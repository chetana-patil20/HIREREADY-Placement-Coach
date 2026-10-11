"""
Job / Placement Matching Engine
================================
Deterministic scoring of how well a student fits a given job role.
Combines skill match, academic match, and project relevance into an
overall match percentage, plus the eligibility verdict from the
eligibility engine.
"""
from dataclasses import dataclass, field
from typing import List
from app import models
from app.engines.eligibility_engine import check_eligibility


@dataclass
class MatchResult:
    job_role_id: int
    company_name: str
    role_title: str
    eligible: bool
    eligibility_reasons: List[str]
    overall_match: int
    skill_match: int
    academic_match: int
    project_relevance: int
    matched_skills: List[str]
    missing_required_skills: List[str]
    missing_preferred_skills: List[str]
    relevant_project_titles: List[str]
    recommended_action: str

    def to_dict(self):
        return self.__dict__


def _skill_set(csv: str) -> set:
    return {s.strip().lower() for s in (csv or "").split(",") if s.strip()}


def _score_skills(student: models.StudentProfile, role: models.JobRole):
    owned = {s.skill_name.strip().lower(): s.proficiency for s in student.skills}
    required = _skill_set(role.required_skills)
    preferred = _skill_set(role.preferred_skills)

    matched_required = sorted(s for s in required if s in owned)
    matched_preferred = sorted(s for s in preferred if s in owned)
    missing_required = sorted(s for s in required if s not in owned)
    missing_preferred = sorted(s for s in preferred if s not in owned)

    if required:
        # weight by proficiency: a skill counts more if the student is genuinely strong in it
        req_score = sum(owned.get(s, 0) for s in required) / (len(required) * 100)
    else:
        req_score = 1.0
    if preferred:
        pref_score = sum(owned.get(s, 0) for s in preferred) / (len(preferred) * 100)
    else:
        pref_score = 1.0

    # required skills weigh 75%, preferred skills weigh 25%
    skill_score = round((req_score * 0.75 + pref_score * 0.25) * 100)
    matched = sorted(set(matched_required) | set(matched_preferred))
    return skill_score, matched, missing_required, missing_preferred


def _score_academics(student: models.StudentProfile, role: models.JobRole) -> int:
    score = 0
    weight_total = 0

    weight_total += 60
    if role.min_cgpa:
        ratio = min(student.cgpa / role.min_cgpa, 1.3) if role.min_cgpa > 0 else 1
        score += min(ratio, 1.0) * 60
    else:
        score += 60

    weight_total += 20
    backlog_penalty = max(0, student.backlogs - role.max_backlogs) * 10
    score += max(0, 20 - backlog_penalty)

    weight_total += 20
    allowed_years = [y.strip() for y in (role.eligible_graduation_years or "").split(",") if y.strip()]
    if not allowed_years or str(student.graduation_year) in allowed_years:
        score += 20

    return round((score / weight_total) * 100) if weight_total else 100


def _score_projects(student: models.StudentProfile, role: models.JobRole):
    required = _skill_set(role.required_skills) | _skill_set(role.preferred_skills)
    relevant = []
    for p in student.projects:
        stack = _skill_set(p.tech_stack)
        if stack & required:
            relevant.append(p.title)

    if not student.projects:
        return 0, relevant
    if not required:
        # no specific tech requirement: reward having any projects at all
        return min(100, len(student.projects) * 30), [p.title for p in student.projects]

    coverage = len(relevant) / max(1, len(student.projects))
    breadth = min(len(relevant), 3) / 3  # up to 3 relevant projects is "full marks"
    score = round((coverage * 0.4 + breadth * 0.6) * 100)
    return score, relevant


def _recommend_action(missing_required: List[str], missing_preferred: List[str], project_relevance: int) -> str:
    if missing_required:
        top = missing_required[0]
        action = f"Learn {top.title()} next"
        if len(missing_required) > 1:
            action += f" and {missing_required[1].title()}"
        if project_relevance < 40:
            action += f", then build one project that uses it."
        else:
            action += "."
        return action
    if missing_preferred:
        return f"You meet the required skills. Learning {missing_preferred[0].title()} would strengthen your profile further."
    if project_relevance < 50:
        return "Your skills are a strong match. Build one more project directly relevant to this role to stand out."
    return "You're a strong match for this role. Focus on interview preparation next."


def match_student_to_role(student: models.StudentProfile, role: models.JobRole) -> MatchResult:
    eligibility = check_eligibility(student, role)
    skill_score, matched, missing_required, missing_preferred = _score_skills(student, role)
    academic_score = _score_academics(student, role)
    project_score, relevant_projects = _score_projects(student, role)

    # Overall match: skills matter most, then academics, then project proof
    overall = round(skill_score * 0.55 + academic_score * 0.25 + project_score * 0.20)

    return MatchResult(
        job_role_id=role.id,
        company_name=role.company.name if role.company else "",
        role_title=role.title,
        eligible=eligibility.eligible,
        eligibility_reasons=eligibility.failed_reasons,
        overall_match=overall,
        skill_match=skill_score,
        academic_match=academic_score,
        project_relevance=project_score,
        matched_skills=matched,
        missing_required_skills=missing_required,
        missing_preferred_skills=missing_preferred,
        relevant_project_titles=relevant_projects,
        recommended_action=_recommend_action(missing_required, missing_preferred, project_score),
    )


def match_student_to_all_roles(student: models.StudentProfile, roles: List[models.JobRole]) -> List[MatchResult]:
    results = [match_student_to_role(student, r) for r in roles]
    results.sort(key=lambda r: r.overall_match, reverse=True)
    return results
