"""
Recommendation Engine
======================
Generates concrete, data-driven recommendations and notifications - e.g.
upcoming deadlines, weak readiness areas, newly-eligible drives. This
does not call the AI; the AI service (ai_service.py) is used separately
to *explain* these facts in natural language when the student asks.
"""
import datetime as dt
from typing import List
from sqlalchemy.orm import Session
from app import models
from app.engines.matching_engine import match_student_to_all_roles
from app.engines.readiness_engine import compute_readiness

DEADLINE_SOON_DAYS = 5


def generate_recommendations(db: Session, student: models.StudentProfile) -> List[str]:
    recs: List[str] = []
    readiness = compute_readiness(db, student)
    recs.append(f"Your biggest weakness is {readiness.weakest_area}. Focus there first.")

    roles = db.query(models.JobRole).all()
    matches = match_student_to_all_roles(student, roles)
    eligible_matches = [m for m in matches if m.eligible]
    if eligible_matches:
        best = eligible_matches[0]
        recs.append(f"You're eligible for {best.role_title} at {best.company_name} with a {best.overall_match}% match.")
    else:
        recs.append("You're not currently eligible for any listed roles yet — check the Skill Gap page for what's blocking you.")

    if not student.resume_text:
        recs.append("You haven't added a resume yet. Add one to unlock resume scoring and suggestions.")

    upcoming = [
        r for r in roles
        if r.application_deadline and 0 <= (r.application_deadline - dt.date.today()).days <= DEADLINE_SOON_DAYS
    ]
    for r in upcoming:
        days_left = (r.application_deadline - dt.date.today()).days
        recs.append(f"{r.company.name} ({r.title}) application closes in {days_left} day(s).")

    return recs


def generate_notifications_for_student(db: Session, student: models.StudentProfile) -> List[dict]:
    """Returns notification dicts derived from real data (not persisted)."""
    notifications: List[dict] = []
    roles = db.query(models.JobRole).all()

    for r in roles:
        if r.application_deadline:
            days_left = (r.application_deadline - dt.date.today()).days
            if 0 <= days_left <= DEADLINE_SOON_DAYS:
                notifications.append({
                    "title": f"{r.company.name} registration closes soon",
                    "message": f"{r.company.name} ({r.title}) application closes in {days_left} day(s).",
                    "category": "deadline",
                })
        if r.drive_date:
            days_left = (r.drive_date - dt.date.today()).days
            if 0 <= days_left <= DEADLINE_SOON_DAYS:
                notifications.append({
                    "title": f"Upcoming drive: {r.company.name}",
                    "message": f"{r.company.name} ({r.title}) drive is on {r.drive_date.isoformat()}.",
                    "category": "drive",
                })

    pending_tasks = [t for t in student.tasks if not t.completed]
    if pending_tasks:
        notifications.append({
            "title": "Preparation tasks pending",
            "message": f"You have {len(pending_tasks)} preparation task(s) left this cycle.",
            "category": "task",
        })

    return notifications
