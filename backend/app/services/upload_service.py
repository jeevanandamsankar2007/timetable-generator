"""
Upload service - handles file saving and PDF extraction orchestration.
"""
import os
import shutil
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings
from app.repositories.upload_repo import UploadRepository
from app.repositories.preview_repo import PreviewRepository
from app.schemas.upload import UploadResponse, UploadListItem
from app.pdf_engine.reader import PDFReader
from app.pdf_engine.table_detector import TableDetector
from app.pdf_engine.grid_extractor import GridExtractor
from app.pdf_engine.subject_master_extractor import SubjectMasterExtractor
from app.mapping_engine.mapper import TimetableMapper
from app.mapping_engine.multi_faculty import expand_multi_faculty
from app.preview_engine.preview_builder import build_preview_records

logger = logging.getLogger(__name__)


class UploadService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_repo = UploadRepository(db)
        self.preview_repo = PreviewRepository(db)

        # Ensure upload directory exists
        Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    def get_uploads(self, user_id: int) -> List[UploadListItem]:
        """Get all uploads for a user."""
        uploads = self.upload_repo.get_by_user(user_id)
        # Note: In a real scenario, we might calculate faculty_count here
        # by joining with TimetableEntry and FacultyMapping.
        return [UploadListItem.model_validate(u) for u in uploads]

    def delete_upload(self, upload_id: int) -> bool:
        """Delete an upload and its file."""
        upload = self.upload_repo.get_by_id(upload_id)
        if not upload:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found"
            )

        # Delete physical file
        file_path = Path(upload.stored_filename)
        try:
            if file_path.exists():
                file_path.unlink()
        except OSError as e:
            logger.warning(f"Could not delete physical file {file_path} (it may be locked by a process): {e}")

        # Explicitly delete all preview data to prevent orphans and ghost cells on ID reuse
        self.preview_repo.delete_by_upload(upload_id)

        return self.upload_repo.delete(upload_id)

    async def process_upload(
        self,
        user_id: int,
        file: UploadFile,
        department: str,
        semester: str,
        academic_year: str,
    ) -> UploadResponse:
        """Process a newly uploaded PDF."""
        # 1. Save file
        import re
        import uuid
        # Remove trailing spaces/newlines and replace unsafe characters with underscore
        clean_filename = re.sub(r'[^\w\-\. ()]', '_', file.filename.strip())
        safe_filename = f"{user_id}_{uuid.uuid4().hex[:8]}_{clean_filename}"
        file_path = Path(settings.UPLOAD_DIR) / safe_filename

        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            logger.error(f"Failed to save file: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save uploaded file"
            )

        # 2. Create DB record
        upload_record = self.upload_repo.create(
            user_id=user_id,
            original_filename=file.filename,
            stored_filename=str(file_path),
            department=department,
            semester=semester,
            academic_year=academic_year,
        )
        
        self.upload_repo.update_progress(upload_record.id, "Uploading", 10)

        # We return the record instantly. BackgroundTask will be attached in the router.
        return UploadResponse.model_validate(upload_record)

    @staticmethod
    async def run_extraction_background(upload_id: int, metadata: dict):
        """Run the extraction pipeline in the background with a 300-second timeout."""
        import asyncio
        from app.database.connection import SessionLocal
        
        # New DB session for background task
        db = SessionLocal()
        try:
            upload_repo = UploadRepository(db)
            upload = upload_repo.get_by_id(upload_id)
            if not upload:
                logger.error(f"Upload {upload_id} not found for background task")
                return
            file_path = upload.stored_filename

            # Enforce 300-second timeout for large PDFs
            await asyncio.wait_for(UploadService._extract_pdf_async(db, upload_id, file_path, metadata), timeout=300.0)
        except asyncio.TimeoutError:
            logger.error(f"Extraction for {upload_id} timed out after 300 seconds.")
            upload_repo = UploadRepository(db)
            upload_repo.update_status(upload_id, "error")
            upload_repo.update_progress(upload_id, "Timed out (>20s)", 100)
        except Exception as e:
            logger.error(f"Extraction failed for {upload_id}: {e}")
            upload_repo = UploadRepository(db)
            upload_repo.update_status(upload_id, "error")
            upload_repo.update_progress(upload_id, f"Failed: {str(e)[:50]}", 100)
        finally:
            db.close()

    @staticmethod
    async def _extract_pdf_async(db: Session, upload_id: int, file_path: str, metadata: dict):
        """Core extraction pipeline."""
        import asyncio
        upload_repo = UploadRepository(db)
        preview_repo = PreviewRepository(db)
        
        # Clear any existing preview data to prevent duplication on retries/ID reuse
        preview_repo.delete_by_upload(upload_id)
        db.commit()
        
        upload_repo.update_status(upload_id, "processing")
        upload_repo.update_progress(upload_id, "Reading PDF", 25)
        await asyncio.sleep(0) # Yield control

        # 1. Read PDF (Fast)
        reader = PDFReader(file_path)
        pdf_data = await asyncio.to_thread(reader.read)

        if not pdf_data.get("tables"):
            raise ValueError("No tables found in PDF")

        upload_repo.update_progress(upload_id, "Extracting Timetable Grid", 50)
        await asyncio.sleep(0)

        # 2. Detect Tables
        classified = TableDetector.classify_tables(pdf_data["tables"])
        if not classified["timetable_grids"]:
            raise ValueError("No timetable grid detected")

        upload_repo.update_progress(upload_id, "Extracting Subject Master", 75)
        await asyncio.sleep(0)

        # 3. Extract Subject Master
        subject_masters_by_page = {}
        full_debug_log = []
        master_extractor = SubjectMasterExtractor()
        for sm_table in classified["subject_master_tables"]:
            table_idx = sm_table["index"]
            page_num = pdf_data["tables_meta"][table_idx]["page"] if "tables_meta" in pdf_data else 1
            
            extracted, debug_log = master_extractor.extract(sm_table["data"])
            if page_num not in subject_masters_by_page:
                subject_masters_by_page[page_num] = []
            subject_masters_by_page[page_num].extend(extracted)
            full_debug_log.extend(debug_log)
            
        upload_repo.update_master_debug_log(upload_id, full_debug_log)
        
        if not subject_masters_by_page:
            raise ValueError("Subject Master could not be extracted from the PDF")


        upload_repo.update_progress(upload_id, "Mapping Faculty", 85)
        await asyncio.sleep(0)

        # 4. Extract Grids & Map (using O(1) dictionary maps in TimetableMapper)
        all_mapped_cells = []
        import re

        for grid in classified["timetable_grids"]:
            table_idx = grid["index"]
            page_num = pdf_data["tables_meta"][table_idx]["page"] if "tables_meta" in pdf_data else 1
            
            page_subject_master = subject_masters_by_page.get(page_num, [])
            if not page_subject_master:
                logger.warning(f"No subject master found for page {page_num}, falling back to all masters")
                page_subject_master = [item for sublist in subject_masters_by_page.values() for item in sublist]

            mapper = TimetableMapper(page_subject_master)

            structure = TableDetector.detect_structure(grid["data"])
            extractor = GridExtractor(grid["data"], structure)
            cells = extractor.extract_cells()

            page_text = pdf_data["text"][page_num - 1] if "text" in pdf_data and page_num - 1 < len(pdf_data["text"]) else ""
            section_match = re.search(r"Sec(?:tion|.)*?:\s*([A-Za-z0-9\s]+)", page_text, re.IGNORECASE)
            section_name = None
            if section_match:
                section_name = section_match.group(1).split('\n')[0].strip()
                section_name = re.split(r'\s{2,}|Semester|Hall', section_name, flags=re.IGNORECASE)[0].strip()
            
            for cell in cells:
                if section_name:
                    cell["class_name"] = section_name

            mapped = mapper.map_cells(cells)
            all_mapped_cells.extend(mapped)

        # 5. Expand multi-faculty labs
        expanded = expand_multi_faculty(all_mapped_cells)

        upload_repo.update_progress(upload_id, "Validating and Committing", 95)
        await asyncio.sleep(0)

        # 6. Validate, Filter, Auto-Commit, and Log
        from app.schemas.preview import PreviewItem
        from app.validators.validator import DataValidator
        from app.services.preview_service import PreviewService
        from app.models.validation_log import ValidationLog

        # Create PreviewItem Pydantic models from the expanded dictionaries
        preview_records = build_preview_records(upload_id, expanded, metadata)
        preview_items = [PreviewItem.model_validate(r) for r in preview_records]

        # Use the DataValidator on the Pydantic models
        DataValidator.validate_preview_items(preview_items)

        # Separate into valid and invalid
        valid_items = []
        invalid_logs = []
        warning_count = 0
        error_count = 0

        for item in preview_items:
            if item.validation_status == "valid":
                valid_items.append(item)
            else:
                # Warnings and Errors
                if item.validation_status == "warning":
                    warning_count += 1
                elif item.validation_status == "error":
                    error_count += 1
                    
                invalid_logs.append(
                    ValidationLog(
                        upload_id=upload_id,
                        status=item.validation_status,
                        message=item.validation_message,
                        cell_reference=f"Day: {item.day}, Period: {item.period}, Subj: {item.subject_code}"
                    )
                )
                
                    # No longer appending to valid_items since we save everything to preview_data

        # We save ALL items to preview_data (including errors) so the admin can edit/review them
        preview_repo.bulk_insert([item.model_dump(exclude={"id"}) for item in preview_items])

        # Do NOT save to ValidationLogs yet. Validation logs are for final audit after approval.
        # Set stats based on the preview items
        upload_repo.update_stats(
            upload_id, 
            extracted=len(preview_items),
            saved=0, # Nothing saved permanently yet
            warnings=warning_count,
            errors=error_count
        )

        # Status goes to pending_approval instead of completed
        final_status = "pending_approval"
        if error_count > 0 or warning_count > 0:
            if len(preview_items) > 0:
                final_status = "pending_approval" # Still pending, UI can show warnings
            else:
                final_status = "error"
                
        upload_repo.update_status(upload_id, final_status)
        upload_repo.update_progress(upload_id, "Completed", 100)
        logger.info(f"Upload {upload_id} processing complete. Awaiting Admin Approval.")
