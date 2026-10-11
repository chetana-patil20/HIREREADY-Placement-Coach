"""
Preparation Plan Engine
=======================
Builds a deterministic, trackable multi-week preparation plan from the
student's skill gap, weak readiness areas, and available daily study
hours. AI is only used afterwards to explain the plan in natural
language - the plan's structure and tasks themselves are rule-based.
"""
import datetime as dt
from typing import List
from sqlalchemy.orm import Session
from app import models
from app.engines.skill_gap_engine import analyze_skill_gap
from app.engines.readiness_engine import compute_readiness

PLAN_WEEKS = 4
DAYS_PER_WEEK = 7


def _skill_learning_task(skill: str, day: int, week: int) -> dict:
    return {
        "week": week, "day": day, "category": "Technical",
        "title": f"Learn / strengthen: {skill.title()}",
        "description": f"Study core concepts of {skill.title()} and solve 3-5 practice problems or build a mini exercise.",
        "estimated_minutes": 90, "difficulty": "Medium",
    }


def build_preparation_plan(db: Session, student: models.StudentProfile, role_name: str = None) -> List[dict]:
    role_name = role_name or student.target_role
    tasks: List[dict] = []

    if not role_name:
        # generic plan focused on the weakest readiness areas
        readiness = compute_readiness(db, student)
        gap_skills = []
    else:
        gap = analyze_skill_gap(db, student, role_name)
        gap_skills = gap.top_skills_to_learn + [
            i.skill_name for i in gap.items if i.status == "Needs Improvement" and i.skill_name not in gap.top_skills_to_learn
        ]
        readiness = compute_readiness(db, student)

    # Week 1: fill core skill gaps
    week1_skills = gap_skills[:4] if gap_skills else ["Core fundamentals", "Data structures", "SQL basics", "Git/GitHub"]
    for idx, skill in enumerate(week1_skills):
        tasks.append(_skill_learning_task(skill, day=idx + 1, week=1))
    tasks.append({
        "week": 1, "day": 6, "category": "Project",
        "title": "Review and update one existing project",
        "description": "Add a clear README, list technologies used, and push clean commits to GitHub.",
        "estimated_minutes": 90, "difficulty": "Easy",
    })
    tasks.append({
        "week": 1, "day": 7, "category": "Aptitude",
        "title": "Aptitude practice: Quantitative basics",
        "description": "Practice 20 quantitative aptitude questions (percentages, ratios, time-speed-distance).",
        "estimated_minutes": 60, "difficulty": "Easy",
    })

    # Week 2: deeper skill building + remaining gap skills
    week2_skills = gap_skills[4:7] if len(gap_skills) > 4 else ["Problem solving", "System basics"]
    for idx, skill in enumerate(week2_skills):
        tasks.append(_skill_learning_task(skill, day=idx + 1, week=2))
    tasks.append({
        "week": 2, "day": 4, "category": "Project",
        "title": f"Build one project relevant to {role_name or 'your target role'}",
        "description": "Plan and start a project that directly uses your target role's core required skills.",
        "estimated_minutes": 150, "difficulty": "Hard",
    })
    tasks.append({
        "week": 2, "day": 6, "category": "Aptitude",
        "title": "Aptitude practice: Logical reasoning",
        "description": "Practice 20 logical reasoning questions (puzzles, seating arrangement, blood relations).",
        "estimated_minutes": 60, "difficulty": "Medium",
    })
    tasks.append({
        "week": 2, "day": 7, "category": "Technical",
        "title": "Coding practice: Arrays & Strings",
        "description": "Solve 5 easy-medium coding problems on arrays and strings.",
        "estimated_minutes": 90, "difficulty": "Medium",
    })

    # Week 3: aptitude + coding intensive
    for day, topic in zip(range(1, 5), ["Data Structures: Linked Lists", "Data Structures: Trees",
                                          "SQL Joins & Queries", "Time & Space Complexity"]):
        tasks.append({
            "week": 3, "day": day, "category": "Technical",
            "title": f"Coding practice: {topic}",
            "description": f"Solve 4-5 problems focused on {topic.lower()}.",
            "estimated_minutes": 90, "difficulty": "Medium",
        })
    tasks.append({
        "week": 3, "day": 5, "category": "Aptitude",
        "title": "Full-length aptitude mock test",
        "description": "Take a timed 40-question mixed aptitude mock test and review mistakes.",
        "estimated_minutes": 75, "difficulty": "Medium",
    })
    tasks.append({
        "week": 3, "day": 6, "category": "Project",
        "title": "Finish and deploy your project",
        "description": "Complete the project started in week 2 and deploy it or host the code with a clean README.",
        "estimated_minutes": 120, "difficulty": "Hard",
    })
    tasks.append({
        "week": 3, "day": 7, "category": "Interview",
        "title": "Review common HR interview questions",
        "description": "Prepare structured answers for 'Tell me about yourself', strengths/weaknesses, and 'why this role'.",
        "estimated_minutes": 60, "difficulty": "Easy",
    })

    # Week 4: resume + mock interviews
    tasks.append({
        "week": 4, "day": 1, "category": "Resume",
        "title": "Rewrite resume project descriptions",
        "description": "Rewrite each project bullet to start with an action verb and include a measurable outcome.",
        "estimated_minutes": 60, "difficulty": "Easy",
    })
    tasks.append({
        "week": 4, "day": 2, "category": "Resume",
        "title": "Run resume through the Resume Analyzer",
        "description": "Use the Resume Analyzer, fix flagged issues, and re-check the score.",
        "estimated_minutes": 45, "difficulty": "Easy",
    })
    tasks.append({
        "week": 4, "day": 3, "category": "Interview",
        "title": "Take a Technical mock interview",
        "description": f"Complete a Technical mock interview for {role_name or 'your target role'} in the AI Coach.",
        "estimated_minutes": 45, "difficulty": "Medium",
    })
    tasks.append({
        "week": 4, "day": 4, "category": "Interview",
        "title": "Take an HR mock interview",
        "description": "Complete an HR mock interview and review the feedback on your weakest answers.",
        "estimated_minutes": 30, "difficulty": "Medium",
    })
    tasks.append({
        "week": 4, "day": 5, "category": "Technical",
        "title": "Revise weakest technical topic",
        "description": f"Revisit your lowest-scoring area: {readiness.weakest_area}.",
        "estimated_minutes": 90, "difficulty": "Medium",
    })
    tasks.append({
        "week": 4, "day": 6, "category": "Aptitude",
        "title": "Final aptitude revision",
        "description": "Review incorrect answers from earlier mock tests and redo similar questions.",
        "estimated_minutes": 60, "difficulty": "Easy",
    })
    tasks.append({
        "week": 4, "day": 7, "category": "Interview",
        "title": "Full mock placement drive simulation",
        "description": "Simulate a full drive: aptitude round, technical interview, then HR interview back-to-back.",
        "estimated_minutes": 120, "difficulty": "Hard",
    })

    for t in tasks:
        t["plan_role"] = role_name or ""
    return tasks


def save_preparation_plan(db: Session, student: models.StudentProfile, role_name: str = None,
                           replace_existing: bool = True) -> List[models.PreparationTask]:
    if replace_existing:
        db.query(models.PreparationTask).filter(
            models.PreparationTask.student_id == student.id
        ).delete()
        db.commit()

    plan = build_preparation_plan(db, student, role_name)
    saved = []
    for t in plan:
        task = models.PreparationTask(student_id=student.id, **t)
        db.add(task)
        saved.append(task)
    db.commit()
    for t in saved:
        db.refresh(t)
    return saved
