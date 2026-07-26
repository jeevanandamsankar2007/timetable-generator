"""
Download routes.
"""
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.generator.timetable_generator import TimetableGenerator
from app.export.pdf_exporter import PDFExporter
from app.export.excel_exporter import ExcelExporter

router = APIRouter(prefix="/download", tags=["Download"])


@router.get("/pdf/all")
def download_all_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and download a multi-page PDF timetable for all faculty."""
    from app.models.faculty import Faculty
    from app.models.uploaded_pdf import UploadedPDF
    generator = TimetableGenerator(db)
    
    faculties = (
        db.query(Faculty)
        .join(UploadedPDF, UploadedPDF.id == Faculty.upload_id)
        .filter(UploadedPDF.user_id == current_user.id)
        .order_by(Faculty.faculty_name)
        .all()
    )
    if not faculties:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No faculty found")
        
    timetables = [generator.generate(f.id) for f in faculties]
    buffer = PDFExporter.export_all(timetables)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="All_Faculty_Timetables.pdf"'}
    )


@router.get("/excel/all")
def download_all_excel(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and download a multi-sheet Excel timetable for all faculty."""
    from app.models.faculty import Faculty
    from app.models.uploaded_pdf import UploadedPDF
    generator = TimetableGenerator(db)
    
    faculties = (
        db.query(Faculty)
        .join(UploadedPDF, UploadedPDF.id == Faculty.upload_id)
        .filter(UploadedPDF.user_id == current_user.id)
        .order_by(Faculty.faculty_name)
        .all()
    )
    if not faculties:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No faculty found")
        
    timetables = [generator.generate(f.id) for f in faculties]
    buffer = ExcelExporter.export_all(timetables)
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="All_Faculty_Timetables.xlsx"'}
    )


@router.get("/pdf/{faculty_id}")
def download_pdf(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and download a PDF timetable."""
    generator = TimetableGenerator(db)
    timetable = generator.generate(faculty_id)
    
    buffer = PDFExporter.export(timetable)
    
    filename = f"{timetable.faculty_name.replace(' ', '_')}_Timetable.pdf"
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/excel/{faculty_id}")
def download_excel(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate and download an Excel timetable."""
    generator = TimetableGenerator(db)
    timetable = generator.generate(faculty_id)
    
    buffer = ExcelExporter.export(timetable)
    
    filename = f"{timetable.faculty_name.replace(' ', '_')}_Timetable.xlsx"
    
    return Response(
        content=buffer.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
