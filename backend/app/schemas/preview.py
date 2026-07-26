"""
Pydantic V2 schemas for the mapping preview workflow.
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class PreviewItem(BaseModel):
    """Single row in the extraction preview."""
    id: Optional[int] = None
    upload_id: int
    department: Optional[str] = None
    semester: Optional[str] = None
    class_name: Optional[str] = None
    day: str
    period: str
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    faculty_name: Optional[str] = None
    room: Optional[str] = None
    validation_status: str = "pending"
    validation_message: Optional[str] = None
    is_approved: int = 0

    class Config:
        from_attributes = True

class PreviewResponse(BaseModel):
    """Full preview response for an upload."""
    upload_id: int
    total_entries: int
    valid_count: int
    warning_count: int
    error_count: int
    items: List[PreviewItem]
    pdf_url: Optional[str] = None
    master_debug_log: Optional[List[Dict[str, Any]]] = None


class ApproveRequest(BaseModel):
    """Request to approve specific preview items."""
    item_ids: Optional[List[int]] = None
    approve_all: bool = False


class EditPreviewRequest(BaseModel):
    """Request to edit a preview row."""
    item_id: int
    subject_code: Optional[str] = None
    subject_name: Optional[str] = None
    faculty_name: Optional[str] = None
    room: Optional[str] = None
    day: Optional[str] = None
    period: Optional[str] = None
