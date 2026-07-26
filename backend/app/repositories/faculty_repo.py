"""
Faculty repository - data access layer for Faculty model.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.faculty import Faculty
from app.models.faculty_mapping import FacultyMapping
from app.models.timetable_entry import TimetableEntry


class FacultyRepository:
    """Handles all database operations for the Faculty model."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, faculty_id: int) -> Optional[Faculty]:
        """Find faculty by ID."""
        return self.db.query(Faculty).filter(Faculty.id == faculty_id).first()

    def get_by_normalized_name(self, upload_id: int, normalized_name: str) -> Optional[Faculty]:
        """Find faculty by normalized name for a specific upload (for deduplication)."""
        return (
            self.db.query(Faculty)
            .filter(Faculty.upload_id == upload_id, Faculty.normalized_name == normalized_name)
            .first()
        )

    def get_or_create(
        self, upload_id: int, faculty_name: str, normalized_name: str
    ) -> Faculty:
        """
        Get existing faculty by normalized name for this upload, or create a new record.
        Prevents duplicate faculty entries within the same PDF upload.
        """
        existing = self.get_by_normalized_name(upload_id, normalized_name)
        if existing:
            return existing

        faculty = Faculty(
            upload_id=upload_id,
            faculty_name=faculty_name,
            normalized_name=normalized_name,
        )
        self.db.add(faculty)
        self.db.flush()
        return faculty

    def search(
        self, user_id: int, query: str = "", department: str = "", page: int = 1, per_page: int = 20
    ) -> tuple[List[Faculty], int]:
        """
        Search faculty by name with pagination, scoped to user.
        Returns (list of faculty, total count).
        """
        from app.models.uploaded_pdf import UploadedPDF
        
        q = self.db.query(Faculty).join(UploadedPDF).filter(UploadedPDF.user_id == user_id)
        
        if query:
            q = q.filter(Faculty.faculty_name.ilike(f"%{query}%"))
            
        total = q.count()
        results = q.offset((page - 1) * per_page).limit(per_page).all()
        return results, total

    def get_all(self) -> List[Faculty]:
        """Get all faculty records."""
        return self.db.query(Faculty).all()

    def count(self) -> int:
        """Count total faculty."""
        return self.db.query(func.count(Faculty.id)).scalar() or 0

    def get_faculty_entries(self, faculty_id: int) -> List[TimetableEntry]:
        """Get all timetable entries for a faculty member."""
        return (
            self.db.query(TimetableEntry)
            .join(FacultyMapping)
            .filter(FacultyMapping.faculty_id == faculty_id)
            .all()
        )
