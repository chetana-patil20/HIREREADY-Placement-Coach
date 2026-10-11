from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import get_current_student_profile
from app.services.ai_service import ai_service
from app.engines.readiness_engine import compute_readiness
from app.engines.matching_engine import match_student_to_all_roles
from app.engines.skill_gap_engine import analyze_skill_gap
from app.engines.resume_engine import analyze_resume_text

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _student_context(student: models.StudentProfile) -> dict:
    return {
        "target_role": student.target_role,
        "cgpa": student.cgpa,
        "backlogs": student.backlogs,
        "graduation_year": student.graduation_year,
        "skills": [{"name": s.skill_name, "proficiency": s.proficiency} for s in student.skills],
        "project_count": len(student.projects),
        "projects": [{"title": p.title, "tech_stack": p.tech_stack} for p in student.projects[:5]],
        "certification_count": len(student.certifications),
        "internship_count": len(student.internships),
    }


@router.post("/chat")
def chat(payload: schemas.ChatRequest, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    readiness = compute_readiness(db, student)
    roles = db.query(models.JobRole).all()
    matches = match_student_to_all_roles(student, roles)
    best_match = matches[0].to_dict() if matches else None

    skill_gap = analyze_skill_gap(db, student, student.target_role).to_dict() if student.target_role else {}
    recent_chat = (
        db.query(models.ChatMessage)
        .filter(models.ChatMessage.student_id == student.id)
        .order_by(models.ChatMessage.id.desc())
        .limit(8)
        .all()
    )
    recent_chat.reverse()

    facts = {
        "readiness": readiness.to_dict(),
        "best_match": best_match,
        "matches": [m.to_dict() for m in matches[:10]],
        "skill_gap": skill_gap,
        "resume": {"score": student.resume_score} if student.resume_score else None,
        "recent_conversation": [{"role": m.role, "content": m.content} for m in recent_chat],
    }

    db.add(models.ChatMessage(student_id=student.id, role="user", content=payload.message))
    reply = ai_service.answer_coach_question(_student_context(student), payload.message, facts)
    db.add(models.ChatMessage(student_id=student.id, role="assistant", content=reply))
    db.commit()

    return {"reply": reply, "mode": "llm" if ai_service.enabled else "local-smart"}


@router.get("/chat/history")
def chat_history(student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    msgs = db.query(models.ChatMessage).filter(models.ChatMessage.student_id == student.id).order_by(models.ChatMessage.created_at).all()
    return [{"role": m.role, "content": m.content, "created_at": m.created_at.isoformat()} for m in msgs]


@router.post("/resume-analysis")
def resume_analysis(payload: schemas.ResumeAnalysisRequest, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    required_skills = []
    if student.target_role:
        gap = analyze_skill_gap(db, student, student.target_role)
        required_skills = [i.skill_name for i in gap.items if i.importance == "required"]

    result = analyze_resume_text(payload.resume_text, student.target_role, required_skills)
    suggestions = ai_service.resume_suggestions(payload.resume_text, student.target_role, result["findings"])

    student.resume_text = payload.resume_text
    student.resume_score = result["score"]
    db.commit()

    return {
        "score": result["score"],
        "problems": result["problems"],
        "suggestions": suggestions,
        "word_count": result["word_count"],
        "has_github": result["has_github"],
        "has_linkedin": result["has_linkedin"],
    }


@router.post("/interview/start")
def start_interview(payload: schemas.InterviewStartRequest, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    role = payload.role or student.target_role or "Software Developer"
    session = models.InterviewSession(student_id=student.id, mode=payload.mode, role=role)
    db.add(session)
    db.commit()
    db.refresh(session)

    skill_names = [s.skill_name for s in student.skills]
    previous_questions = (
        db.query(models.InterviewQuestion.question_text)
        .join(models.InterviewSession, models.InterviewSession.id == models.InterviewQuestion.session_id)
        .filter(
            models.InterviewSession.student_id == student.id,
            models.InterviewSession.mode == payload.mode,
            models.InterviewSession.role == role,
        )
        .order_by(models.InterviewQuestion.id.desc())
        .limit(10)
        .all()
    )
    asked_before = [row[0] for row in previous_questions]
    question_text = ai_service.generate_interview_question(role, payload.mode, 1, skill_names, asked_before)

    question = models.InterviewQuestion(session_id=session.id, question_text=question_text, order_index=1)
    db.add(question)
    db.commit()
    db.refresh(question)

    return {
        "session_id": session.id, "mode": session.mode, "role": session.role,
        "question": {"id": question.id, "text": question.question_text, "order_index": question.order_index},
    }


@router.post("/interview/answer")
def answer_interview(payload: schemas.InterviewAnswerRequest, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    session = db.query(models.InterviewSession).filter(
        models.InterviewSession.id == payload.session_id, models.InterviewSession.student_id == student.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    question = db.query(models.InterviewQuestion).filter(
        models.InterviewQuestion.id == payload.question_id, models.InterviewQuestion.session_id == session.id
    ).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found.")
    if question.student_answer:
        raise HTTPException(status_code=409, detail="This question has already been answered.")

    evaluation = ai_service.evaluate_interview_answer(question.question_text, payload.answer, session.role, session.mode)
    question.student_answer = payload.answer
    question.score = evaluation["score"]
    question.strengths = evaluation["strengths"]
    question.weaknesses = evaluation["weaknesses"]
    question.improved_answer = evaluation["improved_answer"]
    db.commit()

    answered_count = db.query(models.InterviewQuestion).filter(
        models.InterviewQuestion.session_id == session.id, models.InterviewQuestion.student_answer != ""
    ).count()

    next_question = None
    MAX_QUESTIONS = 5
    if answered_count < MAX_QUESTIONS:
        asked = [q.question_text for q in session.questions]
        skill_names = [s.skill_name for s in student.skills]
        q_text = ai_service.generate_interview_question(session.role, session.mode, answered_count + 1, skill_names, asked)
        nq = models.InterviewQuestion(session_id=session.id, question_text=q_text, order_index=answered_count + 1)
        db.add(nq)
        db.commit()
        db.refresh(nq)
        next_question = {"id": nq.id, "text": nq.question_text, "order_index": nq.order_index}
    else:
        scores = [q.score for q in session.questions if q.score is not None]
        session.overall_score = round(sum(scores) / len(scores)) if scores else 0
        db.commit()

    return {
        "evaluation": evaluation,
        "next_question": next_question,
        "session_complete": next_question is None,
        "overall_score": session.overall_score,
    }


@router.get("/interview/sessions")
def list_sessions(student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    sessions = sorted(student.interview_sessions, key=lambda s: s.started_at, reverse=True)
    return [
        {"id": s.id, "mode": s.mode, "role": s.role, "started_at": s.started_at.isoformat(),
         "overall_score": s.overall_score, "question_count": len(s.questions)}
        for s in sessions
    ]


@router.get("/interview/sessions/{session_id}")
def get_session(session_id: int, student: models.StudentProfile = Depends(get_current_student_profile), db: Session = Depends(get_db)):
    session = db.query(models.InterviewSession).filter(
        models.InterviewSession.id == session_id, models.InterviewSession.student_id == student.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Interview session not found.")
    return {
        "id": session.id, "mode": session.mode, "role": session.role, "overall_score": session.overall_score,
        "questions": [
            {"id": q.id, "text": q.question_text, "answer": q.student_answer, "score": q.score,
             "strengths": q.strengths, "weaknesses": q.weaknesses, "improved_answer": q.improved_answer}
            for q in session.questions
        ],
    }
