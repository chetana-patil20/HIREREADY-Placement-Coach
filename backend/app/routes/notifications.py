from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app import models
from app.auth import get_current_student_profile
from app.engines.recommendation_engine import generate_notifications_for_student

router = APIRouter(prefix="/api", tags=["notifications"])


@router.get("/notifications")
def get_notifications(student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    generated = generate_notifications_for_student(db, student)
    persisted = db.query(models.Notification).filter(
        (models.Notification.student_id == student.id) | (models.Notification.student_id.is_(None))
    ).order_by(models.Notification.created_at.desc()).limit(20).all()

    persisted_list = [
        {"id": n.id, "title": n.title, "message": n.message, "category": n.category,
         "is_read": n.is_read, "created_at": n.created_at.isoformat(), "source": "stored"}
        for n in persisted
    ]
    generated_list = [{"id": None, "is_read": False, "source": "live", **g} for g in generated]
    return persisted_list + generated_list


@router.post("/notifications/{notification_id}/read")
def mark_read(notification_id: int, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    notif = db.query(models.Notification).filter(models.Notification.id == notification_id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"id": notification_id, "is_read": True}


@router.get("/events")
def list_events(category: str = None, db: Session = Depends(get_db)):
    query = db.query(models.Event)
    if category:
        query = query.filter(models.Event.category == category)
    events = query.order_by(models.Event.event_date).all()
    return [
        {"id": e.id, "title": e.title, "category": e.category, "description": e.description,
         "event_date": e.event_date.isoformat() if e.event_date else None, "location": e.location}
        for e in events
    ]


@router.get("/announcements")
def list_announcements(db: Session = Depends(get_db)):
    rows = db.query(models.Announcement).order_by(models.Announcement.created_at.desc()).all()
    return [{"id": a.id, "title": a.title, "body": a.body, "created_at": a.created_at.isoformat()} for a in rows]


@router.get("/timetable")
def get_timetable(db: Session = Depends(get_db)):
    rows = db.query(models.TimetableEntry).all()
    return [
        {"id": t.id, "day_of_week": t.day_of_week, "subject": t.subject,
         "start_time": t.start_time, "end_time": t.end_time, "room": t.room}
        for t in rows
    ]


@router.get("/exams")
def get_exams(db: Session = Depends(get_db)):
    rows = db.query(models.Exam).order_by(models.Exam.exam_date).all()
    return [
        {"id": e.id, "subject": e.subject, "exam_date": e.exam_date.isoformat() if e.exam_date else None,
         "exam_type": e.exam_type}
        for e in rows
    ]
