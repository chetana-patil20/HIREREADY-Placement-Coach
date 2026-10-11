from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import get_current_student_profile
from app.engines.eligibility_engine import check_eligibility
from app.engines.matching_engine import match_student_to_role

router = APIRouter(prefix="/api/placements", tags=["placements"])


def _role_to_dict(r: models.JobRole) -> dict:
    return {
        "id": r.id,
        "company_name": r.company.name,
        "company_logo_emoji": r.company.logo_emoji,
        "title": r.title,
        "ctc_lpa": r.ctc_lpa,
        "location": r.location,
        "work_mode": r.work_mode,
        "min_cgpa": r.min_cgpa,
        "max_backlogs": r.max_backlogs,
        "eligible_graduation_years": r.eligible_graduation_years,
        "eligible_branches": r.eligible_branches,
        "required_skills": r.required_skills,
        "preferred_skills": r.preferred_skills,
        "min_experience_months": r.min_experience_months,
        "application_deadline": r.application_deadline.isoformat() if r.application_deadline else None,
        "drive_date": r.drive_date.isoformat() if r.drive_date else None,
        "description": r.description,
    }


@router.get("")
def list_placements(
    role: Optional[str] = None,
    location: Optional[str] = None,
    min_ctc: Optional[float] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(models.JobRole)
    if role:
        query = query.filter(models.JobRole.title.ilike(f"%{role}%"))
    if location:
        query = query.filter(models.JobRole.location.ilike(f"%{location}%"))
    if min_ctc is not None:
        query = query.filter(models.JobRole.ctc_lpa >= min_ctc)
    roles = query.all()
    return [_role_to_dict(r) for r in roles]


@router.get("/{role_id}")
def get_placement(role_id: int, db: Session = Depends(get_db)):
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Placement opportunity not found.")
    return _role_to_dict(role)


@router.get("/{role_id}/eligibility")
def get_eligibility(role_id: int, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Placement opportunity not found.")
    return check_eligibility(student, role).to_dict()


@router.get("/{role_id}/match")
def get_match(role_id: int, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Placement opportunity not found.")
    return match_student_to_role(student, role).to_dict()
