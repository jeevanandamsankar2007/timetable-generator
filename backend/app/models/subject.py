"""
Subject model - stores subject code, name, department, hours.
"""
from sqlalchemy import Column, Integer, String, DateTime, func, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from app.database.base import Base

class Subject(Base):
    """Academic subject extracted from timetable PDFs."""

    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(Integer, ForeignKey("uploaded_pdfs.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_code = Column(String(50), nullable=False)
    subject_name = Column(String(255), nullable=False)
    department = Column(String(100), nullable=True)
    hours = Column(Integer, nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('upload_id', 'subject_code', name='uix_upload_subject_code'),
    )

    # Relationships
    upload = relationship("UploadedPDF", backref=backref("subjects", cascade="all, delete-orphan"))

    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, code='{self.subject_code}', upload={self.upload_id})>"
