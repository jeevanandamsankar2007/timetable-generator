"""
Faculty routes.
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.faculty import FacultySearchRequest, FacultyProfileResponse, FacultyTimetableResponse
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.faculty_service import FacultyService
from app.generator.timetable_generator import TimetableGenerator

router = APIRouter(prefix="/faculty", tags=["Faculty"])


@router.get("", response_model=Dict[str, Any])
def search_faculty(
    query: str = Query(None),
    department: str = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search for faculty members."""
    service = FacultyService(db)
    req = FacultySearchRequest(query=query, department=department, page=page, per_page=per_page)
    return service.search(current_user.id, req)


@router.get("/{faculty_id}", response_model=FacultyProfileResponse)
def get_faculty_profile(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed faculty profile."""
    service = FacultyService(db)
    return service.get_profile(faculty_id)


@router.get("/{faculty_id}/timetable", response_model=FacultyTimetableResponse)
def get_faculty_timetable(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate timetable for a faculty member."""
    generator = TimetableGenerator(db)
    return generator.generate(faculty_id)
