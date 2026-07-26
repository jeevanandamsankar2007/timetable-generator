"""
Faculty service - handles searching and retrieving faculty profiles.
"""
from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.faculty import FacultySearchRequest, FacultyProfileResponse
from app.repositories.faculty_repo import FacultyRepository
from app.repositories.timetable_repo import TimetableRepository


class FacultyService:
    def __init__(self, db: Session):
        self.faculty_repo = FacultyRepository(db)
        self.timetable_repo = TimetableRepository(db)

    def search(self, user_id: int, request: FacultySearchRequest) -> Dict[str, Any]:
        """Search faculty with pagination and basic stats."""
        results, total = self.faculty_repo.search(
            user_id=user_id,
            query=request.query,
            department=request.department,
            page=request.page,
            per_page=request.per_page,
        )

        items = []
        for fac in results:
            # We would normally optimize this with a single aggregate query
            entries = self.timetable_repo.get_entries_by_faculty(fac.id)
            items.append({
                "id": fac.id,
                "faculty_name": fac.faculty_name,
                "total_classes": len(set(e.class_id for e in entries if e.class_id)),
                "total_subjects": len(set(e.subject_id for e in entries if e.subject_id)),
                "weekly_hours": len(entries),
                "timetable_count": 1 # simplified
            })

        return {
            "items": items,
            "total": total,
            "page": request.page,
            "per_page": request.per_page
        }

    def get_profile(self, faculty_id: int) -> FacultyProfileResponse:
        """Get detailed profile for a single faculty member."""
        fac = self.faculty_repo.get_by_id(faculty_id)
        if not fac:
            raise HTTPException(status_code=404, detail="Faculty not found")

        entries = self.timetable_repo.get_entries_by_faculty(fac.id)

        subjects = set()
        classes = set()
        uploads = set()

        for e in entries:
            if e.subject:
                subjects.add(e.subject.subject_name)
            if e.class_ref:
                classes.add(e.class_ref.class_name)
            uploads.add(e.upload_id)

        return FacultyProfileResponse(
            id=fac.id,
            faculty_name=fac.faculty_name,
            subjects=list(subjects),
            classes=list(classes),
            weekly_hours=len(entries),
            uploads=list(uploads)
        )
