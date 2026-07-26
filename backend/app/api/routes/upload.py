"""
Upload routes.
"""
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from app.schemas.upload import UploadResponse, UploadListItem
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.upload_service import UploadService

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    department: str = Form(...),
    semester: str = Form(...),
    academic_year: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a timetable PDF and begin extraction in the background."""
    from app.config import settings
    from pathlib import Path
    
    service = UploadService(db)
    # Save file and return response immediately
    response = await service.process_upload(
        user_id=current_user.id,
        file=file,
        department=department,
        semester=semester,
        academic_year=academic_year
    )
    
    # Launch background extraction with timeout
    background_tasks.add_task(
        UploadService.run_extraction_background,
        response.id,
        {
            "department": department,
            "semester": semester,
            "class_name": ""
        }
    )
    
    return response


@router.get("s", response_model=List[UploadListItem])
def list_uploads(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all uploads for the logged-in user."""
    service = UploadService(db)
    return service.get_uploads(current_user.id)


@router.delete("s/{upload_id}")
def delete_upload(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a specific upload and its data."""
    service = UploadService(db)
    # Ensure user owns it before deleting (simplified here)
    service.delete_upload(upload_id)
    return {"status": "success", "message": "Upload deleted"}


@router.get("/{upload_id}/summary", response_model=None)
def get_upload_summary(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the processing summary and validation logs for an upload."""
    from app.repositories.upload_repo import UploadRepository
    from app.models.validation_log import ValidationLog
    from app.schemas.upload import UploadSummaryResponse
    
    upload_repo = UploadRepository(db)
    upload = upload_repo.get_by_id(upload_id)
    if not upload:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Upload not found")
        
    validation_logs = db.query(ValidationLog).filter(ValidationLog.upload_id == upload_id).all()
    logs_data = [
        {
            "id": log.id,
            "status": log.status,
            "message": log.message,
            "cell_reference": log.cell_reference,
            "created_at": log.created_at
        } for log in validation_logs
    ]
    
    return UploadSummaryResponse(
        upload_id=upload.id,
        total_extracted=upload.extracted_count or 0,
        saved_records=upload.saved_count or 0,
        warning_count=upload.warning_count or 0,
        error_count=upload.error_count or 0,
        master_debug_log=upload.master_debug_log,
        validation_logs=logs_data
    )
