"""
Pydantic V2 schemas for PDF upload.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class UploadBase(BaseModel):
    department: Optional[str] = None
    semester: Optional[str] = None
    academic_year: Optional[str] = None


class UploadResponse(UploadBase):
    """Response after uploading a PDF."""
    id: int
    original_filename: str
    status: str
    processing_stage: Optional[str] = None
    processing_progress: int = 0
    upload_date: datetime

    model_config = ConfigDict(from_attributes=True)


class UploadListItem(UploadResponse):
    """Single item in the uploads list."""
    uploaded_by: Optional[str] = None
    faculty_count: int = 0

class UploadSummaryResponse(BaseModel):
    """Summary of the extraction and validation process."""
    upload_id: int
    total_extracted: int
    saved_records: int
    warning_count: int
    error_count: int
    master_debug_log: Optional[list] = None
    validation_logs: Optional[list] = None
    
    model_config = ConfigDict(from_attributes=True)
