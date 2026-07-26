"""
FacultyMapping model - links faculty to timetable entries.
Supports unlimited faculty per single timetable entry (e.g. labs).
"""
from sqlalchemy import Column, Integer, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship
from app.database.base import Base


class FacultyMapping(Base):
    """
    Maps one faculty member to one timetable entry.
    Multiple rows with the same entry_id enable multi-faculty labs.
    """

    __tablename__ = "faculty_mappings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(
        Integer, ForeignKey("timetable_entries.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    faculty_id = Column(
        Integer, ForeignKey("faculty.id"), nullable=False, index=True,
    )
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    entry = relationship("TimetableEntry", back_populates="faculty_mappings")
    faculty = relationship("Faculty", back_populates="mappings")

    def __repr__(self) -> str:
        return f"<FacultyMapping(entry_id={self.entry_id}, faculty_id={self.faculty_id})>"
