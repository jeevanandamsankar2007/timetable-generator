"""
PreviewData model - temporary staging table for extracted data awaiting approval.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, func
from app.database.base import Base


class PreviewData(Base):
    """
    Staging table holding extracted timetable data before user approval.
    Each row represents one extracted mapping that has not yet been committed.
    """

    __tablename__ = "preview_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(
        Integer, ForeignKey("uploaded_pdfs.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    department = Column(String(100), nullable=True)
    semester = Column(String(20), nullable=True)
    class_name = Column(String(50), nullable=True)
    day = Column(String(20), nullable=False)
    period = Column(String(50), nullable=False)
    subject_code = Column(String(50), nullable=True)
    subject_name = Column(String(255), nullable=True)
    faculty_name = Column(String(255), nullable=True)
    room = Column(String(50), nullable=True)
    validation_status = Column(String(50), default="pending")
    # Status values: valid, warning, error, pending
    validation_message = Column(Text, nullable=True)
    is_approved = Column(Integer, default=0)
    # 0=pending, 1=approved, -1=rejected
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return (
            f"<PreviewData(id={self.id}, day='{self.day}', "
            f"period='{self.period}', faculty='{self.faculty_name}')>"
        )
