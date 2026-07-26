"""
Upload repository - data access layer for UploadedPDF model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models.uploaded_pdf import UploadedPDF


class UploadRepository:
    """Handles all database operations for the UploadedPDF model."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, upload_id: int) -> Optional[UploadedPDF]:
        """Find an upload by ID."""
        return (
            self.db.query(UploadedPDF)
            .filter(UploadedPDF.id == upload_id)
            .first()
        )

    def get_by_user(self, user_id: int) -> List[UploadedPDF]:
        """Get all uploads for a specific user, newest first."""
        return (
            self.db.query(UploadedPDF)
            .filter(UploadedPDF.user_id == user_id)
            .order_by(desc(UploadedPDF.upload_date))
            .all()
        )

    def create(
        self,
        user_id: int,
        original_filename: str,
        stored_filename: str,
        department: str = None,
        semester: str = None,
        academic_year: str = None,
    ) -> UploadedPDF:
        """Create a new upload record."""
        from datetime import datetime, timezone
        upload = UploadedPDF(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            department=department,
            semester=semester,
            academic_year=academic_year,
            status="processing",
            upload_date=datetime.now(timezone.utc),        )
        self.db.add(upload)
        self.db.commit()
        self.db.refresh(upload)
        return upload

    def update_status(self, upload_id: int, status: str) -> Optional[UploadedPDF]:
        """Update the status of an upload."""
        upload = self.get_by_id(upload_id)
        if upload:
            upload.status = status
            self.db.commit()
            self.db.refresh(upload)
        return upload

    def update_stats(self, upload_id: int, extracted: int, saved: int, warnings: int, errors: int) -> Optional[UploadedPDF]:
        """Update summary stats for the upload."""
        upload = self.get_by_id(upload_id)
        if upload:
            upload.extracted_count = extracted
            upload.saved_count = saved
            upload.warning_count = warnings
            upload.error_count = errors
            self.db.commit()
            self.db.refresh(upload)
        return upload

    def update_progress(self, upload_id: int, stage: str, progress: int) -> Optional[UploadedPDF]:
        """Update processing progress and stage."""
        upload = self.get_by_id(upload_id)
        if upload:
            upload.processing_stage = stage
            upload.processing_progress = progress
            self.db.commit()
            self.db.refresh(upload)
        return upload
        
    def update_master_debug_log(self, upload_id: int, debug_log: List[dict]) -> Optional[UploadedPDF]:
        """Save the subject master extraction debug log."""
        upload = self.get_by_id(upload_id)
        if upload:
            upload.master_debug_log = debug_log
            self.db.commit()
            self.db.refresh(upload)
        return upload

    def delete(self, upload_id: int) -> bool:
        """Delete an upload and its cascade dependencies."""
        upload = self.get_by_id(upload_id)
        if not upload:
            return False
        self.db.delete(upload)
        self.db.commit()
        return True

    def count(self) -> int:
        """Count total uploaded PDFs."""
        return self.db.query(func.count(UploadedPDF.id)).scalar() or 0

    def get_latest(self) -> Optional[UploadedPDF]:
        """Get the most recently uploaded PDF."""
        return (
            self.db.query(UploadedPDF)
            .order_by(desc(UploadedPDF.upload_date))
            .first()
        )
