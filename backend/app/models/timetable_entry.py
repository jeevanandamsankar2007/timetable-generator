"""
TimetableEntry model - one cell in the timetable grid.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class TimetableEntry(Base):
    """
    Single timetable cell: a specific day+period for a class+subject.
    Faculty are linked via the FacultyMapping table (supports multiple faculty).
    """

    __tablename__ = "timetable_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    upload_id = Column(
        Integer, ForeignKey("uploaded_pdfs.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    class_id = Column(
        Integer, ForeignKey("classes.id"), nullable=True, index=True
    )
    subject_id = Column(
        Integer, ForeignKey("subjects.id"), nullable=True, index=True
    )
    day = Column(String(20), nullable=False)
    period = Column(String(50), nullable=False)
    room = Column(String(50), nullable=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    upload = relationship("UploadedPDF", back_populates="timetable_entries")
    subject = relationship("Subject", lazy="selectin")
    class_ref = relationship("Class", lazy="selectin")
    faculty_mappings = relationship(
        "FacultyMapping", back_populates="entry",
        cascade="all, delete-orphan", lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<TimetableEntry(id={self.id}, day='{self.day}', period='{self.period}')>"
