"""
Preview service - handles staging data, validation, and final DB commit.
"""
import logging
from typing import List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.schemas.preview import PreviewResponse, PreviewItem, ApproveRequest, EditPreviewRequest
from app.repositories.preview_repo import PreviewRepository
from app.repositories.upload_repo import UploadRepository
from app.repositories.class_repo import ClassRepository
from app.repositories.subject_repo import SubjectRepository
from app.repositories.faculty_repo import FacultyRepository
from app.repositories.timetable_repo import TimetableRepository
from app.validators.validator import DataValidator
from app.mapping_engine.normalizer import normalize_faculty_name

logger = logging.getLogger(__name__)


class PreviewService:
    def __init__(self, db: Session):
        self.db = db
        self.preview_repo = PreviewRepository(db)
        self.upload_repo = UploadRepository(db)
        self.class_repo = ClassRepository(db)
        self.subject_repo = SubjectRepository(db)
        self.faculty_repo = FacultyRepository(db)
        self.timetable_repo = TimetableRepository(db)

    def get_preview(self, upload_id: int) -> PreviewResponse:
        """Get the current preview state, triggering re-validation."""
        items = self.preview_repo.get_by_upload(upload_id)
        if not items:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No preview data found for this upload"
            )

        # Run validation engine
        DataValidator.validate_preview_items(items)
        self.db.commit() # Save validation results

        # Count stats
        stats = self.preview_repo.count_by_status(upload_id)
        total = sum(stats.values())
        
        # Get master debug log from upload
        upload = self.upload_repo.get_by_id(upload_id)
        master_debug_log = upload.master_debug_log if upload else None
        
        import os
        pdf_url = None
        if upload and upload.stored_filename and os.path.exists(upload.stored_filename):
            filename = os.path.basename(upload.stored_filename)
            pdf_url = f"/uploads/{filename}"

        return PreviewResponse(
            upload_id=upload_id,
            total_entries=total,
            valid_count=stats.get("valid", 0),
            warning_count=stats.get("warning", 0),
            error_count=stats.get("error", 0),
            items=[PreviewItem.model_validate(item) for item in items],
            pdf_url=pdf_url,
            master_debug_log=master_debug_log
        )

    def approve(self, upload_id: int, request: ApproveRequest) -> Dict[str, Any]:
        """Approve preview items and trigger DB commit."""
        if request.approve_all:
            self.preview_repo.approve_all(upload_id)
        elif request.item_ids:
            self.preview_repo.approve_selected(request.item_ids)
        else:
            raise HTTPException(status_code=400, detail="No items selected")

        self.db.commit()
        return self.commit_approved(upload_id)

    def reject_all(self, upload_id: int) -> Dict[str, str]:
        """Reject all and mark upload as failed/rejected."""
        self.preview_repo.reject_all(upload_id)
        self.upload_repo.update_status(upload_id, "error")
        return {"status": "rejected"}

    def edit_item(self, request: EditPreviewRequest) -> PreviewItem:
        """Edit a staging row before approval."""
        updates = request.model_dump(exclude_unset=True, exclude={"item_id"})
        item = self.preview_repo.update_item(request.item_id, updates)
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # Re-validate the specific item (and others if conflict)
        upload_items = self.preview_repo.get_by_upload(item.upload_id)
        DataValidator.validate_preview_items(upload_items)
        self.db.commit()

        self.db.refresh(item)
        return PreviewItem.model_validate(item)

    def commit_approved(self, upload_id: int) -> Dict[str, Any]:
        """
        Move all approved items from PreviewData to production tables.
        This handles Faculty deduplication, Class/Subject creation,
        and TimetableEntry/FacultyMapping inserts inside a transaction.
        """
        approved_items = self.preview_repo.get_approved(upload_id)
        if not approved_items:
            return {"status": "success", "message": "No approved items to commit"}

        try:
            # We group by (class, subject, day, period, room) to reconstruct multi-faculty
            # entries that were split into separate preview rows.
            entry_map = {}

            for item in approved_items:
                if item.validation_status == "error":
                    continue # Safety check, don't commit errors

                # 1. Resolve Class
                cls = self.class_repo.get_or_create(
                    upload_id=upload_id,
                    class_name=item.class_name or "",
                    department=item.department,
                    semester=item.semester
                )

                # 2. Resolve Subject
                subj = self.subject_repo.get_or_create(
                    upload_id=upload_id,
                    subject_code=item.subject_code or "",
                    subject_name=item.subject_name or ""
                )

                # 3. Resolve Faculty
                fac = None
                if item.faculty_name:
                    norm_name = normalize_faculty_name(item.faculty_name)
                    fac = self.faculty_repo.get_or_create(
                        upload_id=upload_id,
                        faculty_name=item.faculty_name,
                        normalized_name=norm_name
                    )

                # 4. Group identical grid cells
                key = (cls.id, subj.id, item.day, item.period, item.room)
                if key not in entry_map:
                    entry_map[key] = {
                        "upload_id": upload_id,
                        "class_id": cls.id,
                        "subject_id": subj.id,
                        "day": item.day,
                        "period": item.period,
                        "room": item.room,
                        "faculty_ids": set()
                    }

                if fac:
                    entry_map[key]["faculty_ids"].add(fac.id)

            # 5. Batch insert Timetable entries
            entries_to_create = []
            for e in entry_map.values():
                e["faculty_ids"] = list(e["faculty_ids"])
                entries_to_create.append(e)

            self.timetable_repo.batch_create_entries(entries_to_create)

            # 6. Save Validation Logs for auditing
            from app.models.validation_log import ValidationLog
            
            error_logs = []
            for item in approved_items:
                if item.validation_status in ("error", "warning") and item.validation_message:
                    error_logs.append(ValidationLog(
                        upload_id=upload_id,
                        status=item.validation_status,
                        message=item.validation_message,
                        cell_reference=f"Day: {item.day}, Period: {item.period}, Subj: {item.subject_code}"
                    ))
            
            if error_logs:
                self.db.bulk_save_objects(error_logs)

            # 7. Cleanup and Update Status
            self.preview_repo.delete_by_upload(upload_id)
            self.upload_repo.update_status(upload_id, "approved")
            self.db.commit()

            return {
                "status": "success",
                "committed_entries": len(entries_to_create)
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"Commit failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to commit data")

    def commit_in_memory_records(self, upload_id: int, items: List[PreviewItem]) -> Dict[str, Any]:
        """
        Commit valid in-memory PreviewItem objects directly to production tables.
        This skips the database-backed staging table (PreviewData).
        """
        if not items:
            return {"status": "success", "committed_entries": 0}

        try:
            entry_map = {}

            for item in items:
                if item.validation_status == "error":
                    continue 

                # 1. Resolve Class
                cls = self.class_repo.get_or_create(
                    upload_id=upload_id,
                    class_name=item.class_name or "",
                    department=item.department,
                    semester=item.semester
                )

                # 2. Resolve Subject
                subj = self.subject_repo.get_or_create(
                    upload_id=upload_id,
                    subject_code=item.subject_code or "",
                    subject_name=item.subject_name or ""
                )

                # 3. Resolve Faculty
                fac = None
                if item.faculty_name:
                    norm_name = normalize_faculty_name(item.faculty_name)
                    fac = self.faculty_repo.get_or_create(
                        upload_id=upload_id,
                        faculty_name=item.faculty_name,
                        normalized_name=norm_name
                    )

                # 4. Group identical grid cells
                key = (cls.id, subj.id, item.day, item.period, item.room)
                if key not in entry_map:
                    entry_map[key] = {
                        "upload_id": upload_id,
                        "class_id": cls.id,
                        "subject_id": subj.id,
                        "day": item.day,
                        "period": item.period,
                        "room": item.room,
                        "faculty_ids": set()
                    }

                if fac:
                    entry_map[key]["faculty_ids"].add(fac.id)

            # 5. Batch insert Timetable entries
            entries_to_create = []
            for e in entry_map.values():
                e["faculty_ids"] = list(e["faculty_ids"])
                entries_to_create.append(e)

            self.timetable_repo.batch_create_entries(entries_to_create)
            
            # Flush changes to ensure they are written
            self.db.flush()

            return {
                "status": "success",
                "committed_entries": len(entries_to_create)
            }

        except Exception as e:
            self.db.rollback()
            logger.error(f"In-memory commit failed: {e}")
            raise RuntimeError(f"Failed to commit valid records: {e}")
