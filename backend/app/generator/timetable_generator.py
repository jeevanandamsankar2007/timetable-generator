"""
Timetable generation engine - reconstructs the grid for a specific faculty.
"""
from typing import List, Dict, Any, Set
from collections import defaultdict
from sqlalchemy.orm import Session

from app.schemas.faculty import FacultyTimetableResponse, TimetableCell
from app.repositories.faculty_repo import FacultyRepository
from app.repositories.timetable_repo import TimetableRepository


class TimetableGenerator:
    """Generates an individual faculty timetable matrix."""

    def __init__(self, db: Session):
        self.faculty_repo = FacultyRepository(db)
        self.timetable_repo = TimetableRepository(db)

    def generate(self, faculty_id: int) -> FacultyTimetableResponse:
        """
        Reconstruct the timetable matrix for a faculty member.
        Automatically infers headers and days from the data.
        """
        fac = self.faculty_repo.get_by_id(faculty_id)
        if not fac:
            raise ValueError("Faculty not found")

        entries = self.timetable_repo.get_entries_by_faculty(faculty_id)

        # Infer days and periods from all entries in the associated uploads
        # This prevents missing columns if the faculty is free during certain periods
        upload_ids = list(set(e.upload_id for e in entries if hasattr(e, 'upload_id')))
        
        if upload_ids:
            from app.models.timetable_entry import TimetableEntry
            all_context_entries = self.timetable_repo.db.query(TimetableEntry).filter(TimetableEntry.upload_id.in_(upload_ids)).all()
        else:
            all_context_entries = []
            
        context_to_use = all_context_entries if all_context_entries else entries
        
        days = self._infer_days(context_to_use)
        periods = self._infer_periods(context_to_use)

        # Build mapping: (day, period) -> Entry
        schedule_map = {}
        for e in entries:
            day_key = str(e.day).capitalize() if e.day else ""
            schedule_map[(day_key, str(e.period))] = e

        # Generate matrix
        schedule = []
        for day in days:
            day_row = []
            
            for period in periods:
                is_break = "break" in period.lower() or "lunch" in period.lower()
                
                if (day, period) in schedule_map:
                    e = schedule_map[(day, period)]
                    subject_name = e.subject.subject_name if e.subject else ""
                    subject_code = e.subject.subject_code if e.subject else ""
                    class_name = e.class_ref.class_name if e.class_ref else ""
                    
                    cell = TimetableCell(
                        type="class",
                        subject=subject_name,
                        subject_code=subject_code,
                        class_name=class_name,
                        room=e.room,
                    )
                    day_row.append(cell)
                        
                else:
                    if is_break:
                        day_row.append(TimetableCell(type="break", label=period))
                    else:
                        day_row.append(TimetableCell(type="free"))
            schedule.append(day_row)

        return FacultyTimetableResponse(
            faculty_id=fac.id,
            faculty_name=fac.faculty_name,
            department="", # Could aggregate from subjects
            headers=periods,
            days=days,
            schedule=schedule
        )

    def _infer_days(self, entries: List[Any]) -> List[str]:
        """Extract unique days in logical order."""
        if not entries:
            return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        unique_days = list(dict.fromkeys(str(e.day).capitalize() for e in entries if e.day))
        
        day_map = {"mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6, "sun": 7}
        
        def day_sort_key(d: str):
            prefix = d[:3].lower()
            return day_map.get(prefix, 99)
            
        return sorted(unique_days, key=day_sort_key)

    def _infer_periods(self, entries: List[Any]) -> List[str]:
        """Extract unique periods in logical order."""
        if not entries:
            return ["1", "2", "3", "4", "5", "6", "7", "8"]
        unique_periods = list(dict.fromkeys(e.period for e in entries))
        
        # Only rely on dynamically extracted periods
        import re
        def parse_time(period: str) -> float:
            match = re.search(r'(\d{1,2})[\.:](\d{2})\s*([AP]M)', period, re.IGNORECASE)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2))
                ampm = match.group(3).upper()
                if ampm == 'PM' and hour < 12:
                    hour += 12
                elif ampm == 'AM' and hour == 12:
                    hour = 0
                return hour + minute / 60.0
            
            # Fallback for breaks if they don't contain time
            lower_p = period.lower()
            if "short break" in lower_p:
                return 10.5
            if "lunch" in lower_p:
                return 13.0
            
            return 99.0
            
        return sorted(unique_periods, key=parse_time)
