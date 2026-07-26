"""
Class repository - data access layer for Class model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.class_model import Class


class ClassRepository:
    """Handles all database operations for the Class model."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_name(self, upload_id: int, class_name: str) -> Optional[Class]:
        """Find a class by its name for a specific upload."""
        return (
            self.db.query(Class)
            .filter(Class.upload_id == upload_id, Class.class_name == class_name)
            .first()
        )

    def get_or_create(
        self,
        upload_id: int,
        class_name: str,
        department: str = None,
        semester: str = None,
        academic_year: str = None,
    ) -> Class:
        """Get existing class for this upload or create new."""
        existing = self.get_by_name(upload_id, class_name)
        if existing:
            return existing

        cls = Class(
            upload_id=upload_id,
            class_name=class_name,
            department=department or "",
            semester=semester or "",
            academic_year=academic_year,
        )
        self.db.add(cls)
        self.db.flush()
        return cls

    def count(self) -> int:
        """Count total classes."""
        return self.db.query(func.count(Class.id)).scalar() or 0
