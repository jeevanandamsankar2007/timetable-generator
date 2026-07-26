"""
Pydantic V2 schemas for download endpoints.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DownloadItem(BaseModel):
    """Row in the downloads listing."""
    id: int
    faculty_name: str
    file_type: str
    generated_date: datetime
    file_size: Optional[str] = None
