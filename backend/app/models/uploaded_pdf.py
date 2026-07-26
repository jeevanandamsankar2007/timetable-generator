"""
UploadedPDF model - tracks every uploaded master timetable PDF.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import relationship
from app.database.base import Base


class UploadedPDF(Base):
    """Record of an uploaded master timetable PDF file."""

    __tablename__ = "uploaded_pdfs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_filename = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    semester = Column(String(20), nullable=True)
    academic_year = Column(String(20), nullable=True)
    status = Column(String(50), default="uploaded", nullable=False)
    # Status values: uploaded, processing, extracted, preview_ready,
    #                approved, error
    processing_stage = Column(String(100), nullable=True)
    processing_progress = Column(Integer, default=0)
    master_debug_log = Column(JSON, nullable=True)
    extracted_count = Column(Integer, default=0)
    saved_count = Column(Integer, default=0)
    warning_count = Column(Integer, default=0)
    error_count = Column(Integer, default=0)
    upload_date = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", lazy="selectin")
    timetable_entries = relationship(
        "TimetableEntry", back_populates="upload", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UploadedPDF(id={self.id}, file='{self.original_filename}')>"
