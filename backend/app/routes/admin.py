from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import require_admin
from app.engines.readiness_engine import compute_readiness
from app.engines.matching_engine import match_student_to_all_roles

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def admin_dashboard(admin=Depends(require_admin), db: Session = Depends(get_db)):
    students = db.query(models.StudentProfile).all()
    roles = db.query(models.JobRole).all()

    eligible_count = 0
    ready_count = 0  # overall readiness >= 60
    skill_counter = Counter()
    gap_counter = Counter()

    for s in students:
        readiness = compute_readiness(db, s)
        if readiness.overall >= 60:
            ready_count += 1
        matches = match_student_to_all_roles(s, roles)
        if any(m.eligible for m in matches):
            eligible_count += 1
        for skill in s.skills:
            skill_counter[skill.skill_name.title()] += 1
        for m in matches[:3]:
            for missing in m.missing_required_skills:
                gap_counter[missing.title()] += 1

    total_applications = db.query(models.Application).count()

    from datetime import date
    upcoming_drives = sorted(
        [r for r in roles if r.drive_date and r.drive_date >= date.today()], key=lambda r: r.drive_date
    )[:5]

    return {
        "total_students": len(students),
        "placement_eligible": eligible_count,
        "placement_ready": ready_count,
        "total_applications": total_applications,
        "top_skills": skill_counter.most_common(8),
        "top_skill_gaps": gap_counter.most_common(8),
        "upcoming_drives": [
            {"id": r.id, "company_name": r.company.name, "role": r.title, "drive_date": r.drive_date.isoformat()}
            for r in upcoming_drives
        ],
        "total_companies": db.query(models.Company).count(),
        "total_job_roles": len(roles),
    }


@router.get("/students")
def list_students(admin=Depends(require_admin), db: Session = Depends(get_db)):
    students = db.query(models.StudentProfile).all()
    roles = db.query(models.JobRole).all()
    out = []
    for s in students:
        readiness = compute_readiness(db, s)
        matches = match_student_to_all_roles(s, roles)
        out.append({
            "id": s.id, "full_name": s.user.full_name if s.user else "", "email": s.user.email if s.user else "",
            "target_role": s.target_role, "cgpa": s.cgpa, "backlogs": s.backlogs,
            "readiness": readiness.overall, "eligible_count": sum(1 for m in matches if m.eligible),
        })
    return out


@router.post("/placements")
def create_job_role(payload: schemas.JobRoleCreate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    company = db.query(models.Company).filter(models.Company.name == payload.company_name).first()
    if not company:
        company = models.Company(name=payload.company_name, logo_emoji=payload.company_logo_emoji)
        db.add(company)
        db.commit()
        db.refresh(company)

    role = models.JobRole(
        company_id=company.id, title=payload.title, ctc_lpa=payload.ctc_lpa, location=payload.location,
        work_mode=payload.work_mode, min_cgpa=payload.min_cgpa, min_percentage_10=payload.min_percentage_10,
        min_percentage_12=payload.min_percentage_12, max_backlogs=payload.max_backlogs,
        eligible_graduation_years=payload.eligible_graduation_years, eligible_branches=payload.eligible_branches,
        required_skills=payload.required_skills, preferred_skills=payload.preferred_skills,
        min_experience_months=payload.min_experience_months, application_deadline=payload.application_deadline,
        drive_date=payload.drive_date, description=payload.description,
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return {"id": role.id, "company_name": company.name, "title": role.title}


@router.put("/placements/{role_id}")
def update_job_role(role_id: int, payload: schemas.JobRoleCreate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Placement opportunity not found.")

    company = db.query(models.Company).filter(models.Company.name == payload.company_name).first()
    if not company:
        company = models.Company(name=payload.company_name, logo_emoji=payload.company_logo_emoji)
        db.add(company)
        db.commit()
        db.refresh(company)

    role.company_id = company.id
    for field in ["title", "ctc_lpa", "location", "work_mode", "min_cgpa", "min_percentage_10", "min_percentage_12",
                  "max_backlogs", "eligible_graduation_years", "eligible_branches", "required_skills",
                  "preferred_skills", "min_experience_months", "application_deadline", "drive_date", "description"]:
        setattr(role, field, getattr(payload, field))
    db.commit()
    return {"id": role.id, "message": "Updated."}


@router.delete("/placements/{role_id}")
def delete_job_role(role_id: int, admin=Depends(require_admin), db: Session = Depends(get_db)):
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Placement opportunity not found.")
    db.delete(role)
    db.commit()
    return {"message": "Deleted."}


@router.post("/announcements")
def create_announcement(payload: schemas.AnnouncementCreate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    a = models.Announcement(title=payload.title, body=payload.body)
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"id": a.id}


@router.post("/events")
def create_event(payload: schemas.EventCreate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    e = models.Event(title=payload.title, category=payload.category, description=payload.description,
                      event_date=payload.event_date, location=payload.location)
    db.add(e)
    db.commit()
    db.refresh(e)
    return {"id": e.id}


@router.get("/support-tickets")
def list_all_tickets(admin=Depends(require_admin), db: Session = Depends(get_db)):
    tickets = db.query(models.SupportTicket).order_by(models.SupportTicket.created_at.desc()).all()
    return [
        {"id": t.id, "student_name": t.student.user.full_name if t.student and t.student.user else "",
         "category": t.category, "subject": t.subject, "description": t.description,
         "status": t.status, "created_at": t.created_at.isoformat()}
        for t in tickets
    ]


@router.put("/support-tickets/{ticket_id}")
def update_ticket_status(ticket_id: int, payload: schemas.SupportTicketStatusUpdate, admin=Depends(require_admin), db: Session = Depends(get_db)):
    ticket = db.query(models.SupportTicket).filter(models.SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found.")
    ticket.status = payload.status
    db.commit()
    return {"id": ticket.id, "status": ticket.status}
