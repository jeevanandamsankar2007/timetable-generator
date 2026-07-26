"""
Pydantic V2 schemas for dashboard statistics.
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class RecentUpload(BaseModel):
    filename: str
    upload_date: datetime
    status: str

class RecentFaculty(BaseModel):
    name: str
    department: Optional[str]

class RecentError(BaseModel):
    message: str
    timestamp: datetime
    status: str

class DashboardStats(BaseModel):
    """Aggregated statistics for the dashboard."""
    total_pdfs: int = 0
    total_faculty: int = 0
    total_classes: int = 0
    total_subjects: int = 0
    total_timetables: int = 0
    last_upload: Optional[datetime] = None
    recent_uploads: List[RecentUpload] = []
    recent_faculty: List[RecentFaculty] = []
    recent_errors: List[RecentError] = []
