"""
Subject repository - data access layer for Subject model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.subject import Subject


class SubjectRepository:
    """Handles all database operations for the Subject model."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_code(self, upload_id: int, code: str) -> Optional[Subject]:
        """Find a subject by its code for a specific upload."""
        return (
            self.db.query(Subject)
            .filter(Subject.upload_id == upload_id, Subject.subject_code == code)
            .first()
        )

    def get_or_create(
        self,
        upload_id: int,
        subject_code: str,
        subject_name: str,
        department: str = None,
        hours: int = None,
    ) -> Subject:
        """Get existing subject by code for this upload, or create new."""
        existing = self.get_by_code(upload_id, subject_code)
        if existing:
            return existing

        subject = Subject(
            upload_id=upload_id,
            subject_code=subject_code,
            subject_name=subject_name,
            department=department,
            hours=hours,
        )
        self.db.add(subject)
        self.db.flush()
        return subject

    def get_all(self) -> List[Subject]:
        """Get all subjects."""
        return self.db.query(Subject).all()
