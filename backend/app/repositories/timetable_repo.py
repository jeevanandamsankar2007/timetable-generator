"""
Timetable repository - data access layer for TimetableEntry and FacultyMapping.
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.timetable_entry import TimetableEntry
from app.models.faculty_mapping import FacultyMapping


class TimetableRepository:
    """Handles database operations for timetable entries and faculty mappings."""

    def __init__(self, db: Session):
        self.db = db

    def create_entry(
        self,
        upload_id: int,
        class_id: int,
        subject_id: int,
        day: str,
        period: str,
        room: str = None,
    ) -> TimetableEntry:
        """Create a single timetable entry."""
        entry = TimetableEntry(
            upload_id=upload_id,
            class_id=class_id,
            subject_id=subject_id,
            day=day,
            period=period,
            room=room,
        )
        self.db.add(entry)
        self.db.flush()
        return entry

    def create_faculty_mapping(
        self, entry_id: int, faculty_id: int
    ) -> FacultyMapping:
        """Map a faculty to a timetable entry."""
        mapping = FacultyMapping(entry_id=entry_id, faculty_id=faculty_id)
        self.db.add(mapping)
        self.db.flush()
        return mapping

    def batch_create_entries(
        self, entries: List[dict]
    ) -> List[TimetableEntry]:
        """
        Batch insert timetable entries with their faculty mappings.
        Each entry dict should contain:
            upload_id, class_id, subject_id, day, period, room, faculty_ids
        """
        created = []
        for entry_data in entries:
            faculty_ids = entry_data.pop("faculty_ids", [])
            entry = TimetableEntry(**entry_data)
            self.db.add(entry)
            self.db.flush()

            for fid in faculty_ids:
                mapping = FacultyMapping(entry_id=entry.id, faculty_id=fid)
                self.db.add(mapping)

            created.append(entry)

        self.db.flush()
        return created

    def get_entries_by_upload(self, upload_id: int) -> List[TimetableEntry]:
        """Get all entries for a specific upload."""
        return (
            self.db.query(TimetableEntry)
            .filter(TimetableEntry.upload_id == upload_id)
            .all()
        )

    def get_entries_by_faculty(self, faculty_id: int) -> List[TimetableEntry]:
        """Get all timetable entries assigned to a faculty member."""
        return (
            self.db.query(TimetableEntry)
            .join(FacultyMapping)
            .filter(FacultyMapping.faculty_id == faculty_id)
            .all()
        )

    def count_entries(self) -> int:
        """Count total timetable entries."""
        return self.db.query(func.count(TimetableEntry.id)).scalar() or 0
