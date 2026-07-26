"""
Pydantic V2 schemas for faculty search and timetable responses.
"""
from pydantic import BaseModel
from typing import Optional, List


class FacultyListItem(BaseModel):
    """Faculty summary card in search results."""
    id: int
    faculty_name: str
    total_classes: int = 0
    total_subjects: int = 0
    weekly_hours: int = 0
    timetable_count: int = 0

    class Config:
        from_attributes = True


class TimetableCell(BaseModel):
    """Single cell in a generated timetable grid."""
    type: str  # class, break, lunch, free
    subject: Optional[str] = None
    subject_code: Optional[str] = None
    class_name: Optional[str] = None
    room: Optional[str] = None
    label: Optional[str] = None


class FacultyTimetableResponse(BaseModel):
    """Full individual faculty timetable."""
    faculty_id: int
    faculty_name: str
    department: Optional[str] = None
    headers: List[str]
    days: List[str]
    schedule: List[List[TimetableCell]]


class FacultySearchRequest(BaseModel):
    """Search/filter parameters for faculty."""
    query: Optional[str] = None
    department: Optional[str] = None
    page: int = 1
    per_page: int = 20


class FacultyProfileResponse(BaseModel):
    """Detailed faculty profile with aggregated data."""
    id: int
    faculty_name: str
    subjects: List[str] = []
    classes: List[str] = []
    weekly_hours: int = 0
    uploads: List[int] = []
