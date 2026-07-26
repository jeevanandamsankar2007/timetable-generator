"""Models package - imports all models for Alembic discovery."""
from app.models.user import User
from app.models.faculty import Faculty
from app.models.subject import Subject
from app.models.class_model import Class
from app.models.uploaded_pdf import UploadedPDF
from app.models.timetable_entry import TimetableEntry
from app.models.faculty_mapping import FacultyMapping
from app.models.preview_data import PreviewData
from app.models.validation_log import ValidationLog

__all__ = [
    "User",
    "Faculty",
    "Subject",
    "Class",
    "UploadedPDF",
    "TimetableEntry",
    "FacultyMapping",
    "PreviewData",
    "ValidationLog",
]
