import datetime as dt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_student_profile
from app.engines.readiness_engine import compute_readiness
from app.engines.matching_engine import match_student_to_all_roles
from app.engines.skill_gap_engine import analyze_skill_gap
from app.engines.preparation_engine import save_preparation_plan
from app.engines.recommendation_engine import generate_recommendations, generate_notifications_for_student

router = APIRouter(prefix="/api/student", tags=["student"])


def _profile_to_dict(p: models.StudentProfile) -> dict:
    return {
        "id": p.id,
        "full_name": p.user.full_name if p.user else "",
        "email": p.user.email if p.user else "",
        "branch": p.branch,
        "cgpa": p.cgpa,
        "percentage_10": p.percentage_10,
        "percentage_12": p.percentage_12,
        "backlogs": p.backlogs,
        "graduation_year": p.graduation_year,
        "target_role": p.target_role,
        "available_study_hours_per_day": p.available_study_hours_per_day,
        "resume_text": p.resume_text,
        "resume_score": p.resume_score,
        "soft_skills": p.soft_skills,
        "linkedin_url": p.linkedin_url,
        "github_url": p.github_url,
        "phone": p.phone,
        "skills": [{"skill_name": s.skill_name, "proficiency": s.proficiency} for s in p.skills],
        "projects": [{"id": pr.id, "title": pr.title, "description": pr.description,
                       "tech_stack": pr.tech_stack, "link": pr.link} for pr in p.projects],
        "certifications": [{"id": c.id, "title": c.title, "issuer": c.issuer, "year": c.year, "credential_url": c.credential_url or ""} for c in p.certifications],
        "internships": [{"id": i.id, "company_name": i.company_name, "role": i.role,
                          "duration_months": i.duration_months, "description": i.description} for i in p.internships],
    }


@router.get("/profile")
def get_profile(student: models.StudentProfile = Depends(get_current_student_profile)):
    return _profile_to_dict(student)


@router.put("/profile")
def update_profile(payload: schemas.ProfileUpdateRequest,
                    student: models.StudentProfile = Depends(get_current_student_profile),
                    db: Session = Depends(get_db)):
    data = payload.dict(exclude_unset=True)

    simple_fields = ["branch", "cgpa", "percentage_10", "percentage_12", "backlogs", "graduation_year",
                      "target_role", "available_study_hours_per_day", "soft_skills",
                      "linkedin_url", "github_url", "phone"]
    for f in simple_fields:
        if f in data and data[f] is not None:
            setattr(student, f, data[f])

    if "skills" in data and data["skills"] is not None:
        db.query(models.StudentSkill).filter(models.StudentSkill.student_id == student.id).delete()
        for s in data["skills"]:
            db.add(models.StudentSkill(student_id=student.id, skill_name=s["skill_name"], proficiency=s["proficiency"]))

    if "projects" in data and data["projects"] is not None:
        db.query(models.Project).filter(models.Project.student_id == student.id).delete()
        for p in data["projects"]:
            db.add(models.Project(student_id=student.id, title=p["title"], description=p.get("description", ""),
                                   tech_stack=p.get("tech_stack", ""), link=p.get("link", "")))

    if "certifications" in data and data["certifications"] is not None:
        db.query(models.Certification).filter(models.Certification.student_id == student.id).delete()
        for c in data["certifications"]:
            db.add(models.Certification(student_id=student.id, title=c["title"], issuer=c.get("issuer", ""), year=c.get("year"), credential_url=c.get("credential_url", "")))

    if "internships" in data and data["internships"] is not None:
        db.query(models.Internship).filter(models.Internship.student_id == student.id).delete()
        for i in data["internships"]:
            db.add(models.Internship(student_id=student.id, company_name=i["company_name"], role=i.get("role", ""),
                                      duration_months=i.get("duration_months", 1), description=i.get("description", "")))

    db.commit()
    db.refresh(student)
    return _profile_to_dict(student)


@router.get("/readiness")
def get_readiness(student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    return compute_readiness(db, student).to_dict()


@router.get("/matches")
def get_matches(student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    roles = db.query(models.JobRole).all()
    results = match_student_to_all_roles(student, roles)
    return [r.to_dict() for r in results]


@router.get("/matches/{role_id}")
def get_match_detail(role_id: int, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Placement opportunity not found.")
    from app.engines.matching_engine import match_student_to_role
    return match_student_to_role(student, role).to_dict()


@router.get("/skill-gap")
def get_skill_gap(role: str = None, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    role_name = role or student.target_role
    if not role_name:
        raise HTTPException(status_code=400, detail="Set a target role on your profile, or pass ?role=")
    return analyze_skill_gap(db, student, role_name).to_dict()


@router.get("/skill-requirements/roles")
def list_available_roles(db: Session = Depends(get_db)):
    rows = db.query(models.SkillRequirement.role_name).distinct().all()
    return sorted({r[0] for r in rows})


@router.get("/preparation-plan")
def get_prep_plan(student: models.StudentProfile = Depends(get_current_student_profile)):
    tasks = sorted(student.tasks, key=lambda t: (t.week, t.day))
    return [
        {"id": t.id, "week": t.week, "day": t.day, "category": t.category, "title": t.title,
         "description": t.description, "estimated_minutes": t.estimated_minutes,
         "difficulty": t.difficulty, "completed": t.completed, "plan_role": t.plan_role}
        for t in tasks
    ]


@router.post("/preparation-plan/generate")
def generate_prep_plan(role: str = None, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    tasks = save_preparation_plan(db, student, role_name=role or student.target_role)
    return [
        {"id": t.id, "week": t.week, "day": t.day, "category": t.category, "title": t.title,
         "description": t.description, "estimated_minutes": t.estimated_minutes,
         "difficulty": t.difficulty, "completed": t.completed, "plan_role": t.plan_role}
        for t in tasks
    ]


@router.post("/preparation-task/{task_id}/complete")
def complete_task(task_id: int, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    task = db.query(models.PreparationTask).filter(
        models.PreparationTask.id == task_id, models.PreparationTask.student_id == student.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    task.completed = not task.completed
    db.commit()
    return {"id": task.id, "completed": task.completed}


@router.get("/recommendations")
def get_recommendations(student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    return {"recommendations": generate_recommendations(db, student)}


@router.get("/dashboard")
def get_dashboard(student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    readiness = compute_readiness(db, student)
    roles = db.query(models.JobRole).all()
    matches = match_student_to_all_roles(student, roles)
    eligible = [m for m in matches if m.eligible]
    top_matches = matches[:5]

    today = dt.date.today()
    upcoming_drives = sorted(
        [r for r in roles if r.drive_date and r.drive_date >= today], key=lambda r: r.drive_date
    )[:5]
    upcoming_deadlines = sorted(
        [r for r in roles if r.application_deadline and r.application_deadline >= today],
        key=lambda r: r.application_deadline
    )[:5]

    pending_tasks = [t for t in student.tasks if not t.completed]
    today_tasks = sorted(student.tasks, key=lambda t: (t.week, t.day))[:3]

    skill_gap = None
    if student.target_role:
        skill_gap = analyze_skill_gap(db, student, student.target_role).to_dict()

    recs = generate_recommendations(db, student)

    return {
        "full_name": student.user.full_name if student.user else "",
        "readiness": readiness.to_dict(),
        "target_role": student.target_role,
        "eligible_count": len(eligible),
        "top_matches": [m.to_dict() for m in top_matches],
        "skill_gap": skill_gap,
        "today_tasks": [
            {"id": t.id, "title": t.title, "category": t.category, "completed": t.completed}
            for t in today_tasks
        ],
        "pending_task_count": len(pending_tasks),
        "upcoming_drives": [
            {"id": r.id, "company_name": r.company.name, "role": r.title, "drive_date": r.drive_date.isoformat()}
            for r in upcoming_drives
        ],
        "upcoming_deadlines": [
            {"id": r.id, "company_name": r.company.name, "role": r.title,
             "application_deadline": r.application_deadline.isoformat()}
            for r in upcoming_deadlines
        ],
        "resume_score": student.resume_score,
        "recommendations": recs,
    }


@router.post("/apply/{role_id}")
def apply_to_role(role_id: int, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    role = db.query(models.JobRole).filter(models.JobRole.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Placement opportunity not found.")
    from app.engines.eligibility_engine import check_eligibility
    result = check_eligibility(student, role)
    if not result.eligible:
        raise HTTPException(status_code=400, detail="You are not eligible for this role: " + "; ".join(result.failed_reasons))

    existing = db.query(models.Application).filter(
        models.Application.student_id == student.id, models.Application.job_role_id == role_id
    ).first()
    if existing:
        return {"id": existing.id, "status": existing.status, "message": "Already applied."}

    app_row = models.Application(student_id=student.id, job_role_id=role_id, status="Applied")
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    return {"id": app_row.id, "status": app_row.status, "message": "Application submitted."}


@router.get("/applications")
def list_applications(student: models.StudentProfile = Depends(get_current_student_profile)):
    return [
        {"id": a.id, "company_name": a.job_role.company.name, "role": a.job_role.title,
         "status": a.status, "applied_at": a.applied_at.isoformat()}
        for a in student.applications
    ]


@router.post("/support-tickets")
def create_ticket(payload: schemas.SupportTicketCreate, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    ticket = models.SupportTicket(student_id=student.id, category=payload.category,
                                   subject=payload.subject, description=payload.description)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return {"id": ticket.id, "status": ticket.status}


@router.get("/support-tickets")
def list_my_tickets(student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    tickets = db.query(models.SupportTicket).filter(models.SupportTicket.student_id == student.id).order_by(models.SupportTicket.created_at.desc()).all()
    return [
        {"id": t.id, "category": t.category, "subject": t.subject, "description": t.description,
         "status": t.status, "created_at": t.created_at.isoformat()}
        for t in tickets
    ]
