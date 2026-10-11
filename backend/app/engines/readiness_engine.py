"""
Placement Readiness Engine
==========================
Computes a transparent, weighted "Overall Placement Readiness" score from
six sub-scores, so a student always understands *why* their number is
what it is. Nothing here is random or AI-generated - every sub-score is
derived from concrete profile data.

Overall Readiness =
    0.20 * Academic Readiness
  + 0.25 * Technical Skill Readiness
  + 0.15 * Project Readiness
  + 0.15 * Resume Readiness
  + 0.10 * Aptitude Readiness
  + 0.15 * Interview Readiness
"""
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app import models

WEIGHTS = {
    "academic": 0.20,
    "technical_skills": 0.25,
    "projects": 0.15,
    "resume": 0.15,
    "aptitude": 0.10,
    "interview": 0.15,
}


@dataclass
class ReadinessResult:
    overall: int
    academic: int
    technical_skills: int
    projects: int
    resume: int
    aptitude: int
    interview: int
    weakest_area: str
    strongest_area: str
    score_meaning: str
    next_actions: list
    weights: dict

    def to_dict(self):
        return self.__dict__


LABELS = {
    "academic": "academics",
    "technical_skills": "technical skills",
    "projects": "project experience",
    "resume": "resume",
    "aptitude": "aptitude preparation",
    "interview": "interview preparation",
}


def _academic_score(student: models.StudentProfile) -> int:
    # Use every reported academic measure. Missing school percentages are
    # omitted and the remaining weights are normalized, rather than treated as zero.
    components = [(max(0, min(100, student.cgpa * 10)), 0.70)]
    if student.percentage_10 > 0:
        components.append((max(0, min(100, student.percentage_10)), 0.15))
    if student.percentage_12 > 0:
        components.append((max(0, min(100, student.percentage_12)), 0.15))
    weight_sum = sum(weight for _, weight in components)
    cgpa_component = sum(score * weight for score, weight in components) / weight_sum
    backlog_penalty = min(40, student.backlogs * 15)
    return round(max(0, cgpa_component - backlog_penalty))


def _technical_skill_score(db: Session, student: models.StudentProfile) -> int:
    skills = student.skills
    if not skills:
        return 0
    if student.target_role:
        requirements = db.query(models.SkillRequirement).filter(
            models.SkillRequirement.role_name.ilike(student.target_role)
        ).all()
        owned = {s.skill_name.strip().casefold(): s.proficiency for s in skills}
        required = [r for r in requirements if r.importance == "required"]
        preferred = [r for r in requirements if r.importance != "required"]
        if required:
            req_score = sum(owned.get(r.skill_name.strip().casefold(), 0) for r in required) / len(required)
            pref_score = (sum(owned.get(r.skill_name.strip().casefold(), 0) for r in preferred) / len(preferred)) if preferred else req_score
            return round(req_score * 0.8 + pref_score * 0.2)
    avg_proficiency = sum(s.proficiency for s in skills) / len(skills)
    # average proficiency carries most of the weight; breadth (number of
    # distinct skills, capped at 8) contributes a smaller bonus
    breadth_bonus = min(len(skills), 8) / 8 * 15
    return round(min(100, avg_proficiency * 0.85 + breadth_bonus))


def _project_score(db: Session, student: models.StudentProfile) -> int:
    projects = student.projects
    certs = student.certifications
    interns = student.internships
    if not projects and not certs and not interns:
        return 0
    project_count = len(projects)
    if student.target_role:
        requirements = db.query(models.SkillRequirement).filter(
            models.SkillRequirement.role_name.ilike(student.target_role)
        ).all()
        target_skills = {r.skill_name.strip().casefold() for r in requirements}
        if target_skills:
            project_count = sum(
                1 for project in projects
                if target_skills & {skill.strip().casefold() for skill in (project.tech_stack or "").split(",") if skill.strip()}
            )
    project_component = min(project_count, 4) / 4 * 60
    cert_component = min(len(certs), 3) / 3 * 20
    intern_component = min(len(interns), 2) / 2 * 20
    return round(project_component + cert_component + intern_component)


def _resume_score(student: models.StudentProfile) -> int:
    if student.resume_score and student.resume_score > 0:
        return min(100, student.resume_score)
    return 20 if student.resume_text else 0


def _aptitude_score(db: Session, student: models.StudentProfile) -> int:
    sessions = (
        db.query(models.InterviewSession)
        .filter(
            models.InterviewSession.student_id == student.id,
            models.InterviewSession.mode == "Aptitude",
            models.InterviewSession.overall_score.isnot(None),
        )
        .all()
    )
    if sessions:
        return round(sum(s.overall_score for s in sessions) / len(sessions))
    # fall back to completion rate of aptitude prep tasks
    apt_tasks = [t for t in student.tasks if t.category == "Aptitude"]
    if not apt_tasks:
        return 0
    done = sum(1 for t in apt_tasks if t.completed)
    return round(done / len(apt_tasks) * 100)


def _interview_score(db: Session, student: models.StudentProfile) -> int:
    sessions = (
        db.query(models.InterviewSession)
        .filter(
            models.InterviewSession.student_id == student.id,
            models.InterviewSession.mode.in_(["HR", "Technical", "Role-specific"]),
            models.InterviewSession.overall_score.isnot(None),
        )
        .all()
    )
    if sessions:
        return round(sum(s.overall_score for s in sessions) / len(sessions))
    interview_tasks = [t for t in student.tasks if t.category == "Interview"]
    if not interview_tasks:
        return 0
    done = sum(1 for t in interview_tasks if t.completed)
    return round(done / len(interview_tasks) * 100)


def compute_readiness(db: Session, student: models.StudentProfile) -> ReadinessResult:
    scores = {
        "academic": _academic_score(student),
        "technical_skills": _technical_skill_score(db, student),
        "projects": _project_score(db, student),
        "resume": _resume_score(student),
        "aptitude": _aptitude_score(db, student),
        "interview": _interview_score(db, student),
    }
    overall = round(sum(scores[k] * WEIGHTS[k] for k in WEIGHTS))

    weakest_key = min(scores, key=lambda k: scores[k])
    strongest_key = max(scores, key=lambda k: scores[k])
    action_map = {
        "academic": "Check target-drive CGPA, marks, branch and backlog cutoffs; keep every value accurate in Profile.",
        "technical_skills": "Add role-relevant skills with honest proficiency levels, then practice the weakest required skills in a small project.",
        "projects": "Build or finish a role-relevant project and document your contribution, tests and measurable outcome.",
        "resume": "Run Resume Analyzer and rewrite project bullets to show your action, tools and truthful results.",
        "aptitude": "Complete timed aptitude practice and review the errors before taking another practice set.",
        "interview": "Complete a mock interview, study each answer's feedback and repeat with a fresh set of questions.",
    }
    priorities = sorted(scores, key=lambda key: scores[key])[:3]

    return ReadinessResult(
        overall=overall,
        academic=scores["academic"],
        technical_skills=scores["technical_skills"],
        projects=scores["projects"],
        resume=scores["resume"],
        aptitude=scores["aptitude"],
        interview=scores["interview"],
        weakest_area=LABELS[weakest_key],
        strongest_area=LABELS[strongest_key],
        score_meaning="A profile-based preparation indicator, not a hiring probability. Eligibility is checked separately against each drive's published rules.",
        next_actions=[action_map[key] for key in priorities],
        weights=WEIGHTS,
    )
