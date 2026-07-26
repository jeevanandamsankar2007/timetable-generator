"""
Preview builder - converts extracted and mapped timetable cells
into structured database records for the staging table (PreviewData).
"""
from typing import List, Dict, Any


def build_preview_records(
    upload_id: int,
    mapped_cells: List[Dict[str, Any]],
    metadata: Dict[str, str],
) -> List[Dict[str, Any]]:
    """
    Build preview records for batch insertion.

    Args:
        upload_id: The ID of the uploaded PDF.
        mapped_cells: The output from the mapping engine (multi_faculty expanded).
        metadata: Dict containing department, semester, class_name.

    Returns:
        List of dicts matching the PreviewData ORM model.
    """
    records = []
    for cell in mapped_cells:
        # Map fields
        record = {
            "upload_id": upload_id,
            "department": metadata.get("department"),
            "semester": metadata.get("semester"),
            "class_name": cell.get("class_name") or metadata.get("class_name"),
            "day": cell.get("day"),
            "period": cell.get("period"),
            "subject_code": cell.get("subject_code"),
            "subject_name": cell.get("subject_name"),
            "faculty_name": cell.get("faculty_name"),
            "room": cell.get("room"),
            "validation_status": cell.get("validation_status", "pending"),
            "validation_message": cell.get("validation_message"),
            "is_approved": 0,
        }
        records.append(record)

    return records
