from fastapi import APIRouter, Depends, Path
from fastapi.responses import Response
from sqlalchemy.orm import Session
from app.api.dependencies import get_db, get_current_user
from app.services.export_service import ExportService
from app.models.user import User

router = APIRouter(prefix="/export", tags=["export"])

@router.get("/{upload_id}/excel")
def export_excel(
    upload_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and return an Excel file for the given upload ID."""
    service = ExportService(db)
    file_bytes = service.generate_excel(upload_id)
    
    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=timetable_{upload_id}.xlsx"
        }
    )


@router.get("/{upload_id}/pdf")
def export_pdf(
    upload_id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and return a PDF file for the given upload ID."""
    service = ExportService(db)
    file_bytes = service.generate_pdf(upload_id)
    
    return Response(
        content=file_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=timetable_{upload_id}.pdf"
        }
    )
