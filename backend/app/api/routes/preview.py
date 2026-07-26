"""
Preview routes.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.preview import PreviewResponse, PreviewItem, ApproveRequest, EditPreviewRequest
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.preview_service import PreviewService

router = APIRouter(prefix="/preview", tags=["Preview"])


@router.get("/{upload_id}", response_model=PreviewResponse)
def get_preview(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get extraction preview data for approval."""
    service = PreviewService(db)
    return service.get_preview(upload_id)


@router.post("/{upload_id}/approve")
def approve_preview(
    upload_id: int,
    request: ApproveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve preview data and commit to main tables."""
    service = PreviewService(db)
    return service.approve(upload_id, request)


@router.post("/{upload_id}/reject")
def reject_preview(
    upload_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Reject preview data."""
    service = PreviewService(db)
    return service.reject_all(upload_id)


@router.post("/{upload_id}/edit", response_model=PreviewItem)
def edit_preview_row(
    upload_id: int,
    request: EditPreviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Edit a specific row in the preview."""
    service = PreviewService(db)
    return service.edit_item(request)
