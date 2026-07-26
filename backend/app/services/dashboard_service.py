"""
Dashboard service - provides high-level statistics.
"""
from sqlalchemy.orm import Session
from app.schemas.dashboard import DashboardStats
from app.repositories.upload_repo import UploadRepository
from app.repositories.faculty_repo import FacultyRepository
from app.repositories.class_repo import ClassRepository
from app.repositories.timetable_repo import TimetableRepository


class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.upload_repo = UploadRepository(db)
        self.faculty_repo = FacultyRepository(db)
        self.class_repo = ClassRepository(db)
        self.timetable_repo = TimetableRepository(db)

    def get_statistics(self, user_id: int) -> DashboardStats:
        """Get aggregate system statistics for a specific user."""
        from app.models.subject import Subject
        from app.models.faculty import Faculty
        from app.models.uploaded_pdf import UploadedPDF
        from app.models.validation_log import ValidationLog
        from app.models.class_model import Class
        from app.models.timetable_entry import TimetableEntry

        total_pdfs = self.db.query(UploadedPDF).filter(UploadedPDF.user_id == user_id).count()
        latest_upload = self.db.query(UploadedPDF).filter(UploadedPDF.user_id == user_id).order_by(UploadedPDF.upload_date.desc()).first()

        recent_uploads = self.db.query(UploadedPDF).filter(UploadedPDF.user_id == user_id).order_by(UploadedPDF.upload_date.desc()).limit(5).all()
        ru_list = [{"filename": u.original_filename, "upload_date": u.upload_date, "status": u.status} for u in recent_uploads]

        total_faculty = self.db.query(Faculty).join(UploadedPDF).filter(UploadedPDF.user_id == user_id).count()
        recent_facs = self.db.query(Faculty).join(UploadedPDF).filter(UploadedPDF.user_id == user_id).order_by(Faculty.id.desc()).limit(5).all()
        rf_list = [{"name": f.faculty_name, "department": "General"} for f in recent_facs]

        total_classes = self.db.query(Class).join(UploadedPDF).filter(UploadedPDF.user_id == user_id).count()
        
        total_subjects = self.db.query(Subject).join(UploadedPDF).filter(UploadedPDF.user_id == user_id).count()
        
        total_timetables = self.db.query(TimetableEntry).join(Class).join(UploadedPDF).filter(UploadedPDF.user_id == user_id).count()

        recent_errs = self.db.query(ValidationLog).join(UploadedPDF).filter(UploadedPDF.user_id == user_id).order_by(ValidationLog.created_at.desc()).limit(5).all()
        re_list = [{"message": e.message, "timestamp": e.created_at, "status": e.status} for e in recent_errs]

        return DashboardStats(
            total_pdfs=total_pdfs,
            total_faculty=total_faculty,
            total_classes=total_classes,
            total_subjects=total_subjects,
            total_timetables=total_timetables,
            last_upload=latest_upload.upload_date if latest_upload else None,
            recent_uploads=ru_list,
            recent_faculty=rf_list,
            recent_errors=re_list
        )
