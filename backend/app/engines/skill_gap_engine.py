"""
Skill Gap Engine
================
Compares a student's current skills against the skill set required for a
target role (sourced from the skill_requirements table) and classifies
each skill as Strong / Needs Improvement / Missing.
"""
from dataclasses import dataclass, field
from typing import List
from sqlalchemy.orm import Session
from app import models

STRONG_THRESHOLD = 70
IMPROVE_THRESHOLD = 35


@dataclass
class SkillGapItem:
    skill_name: str
    importance: str  # required | preferred
    status: str  # Strong | Needs Improvement | Missing
    proficiency: int


@dataclass
class SkillGapResult:
    role_name: str
    items: List[SkillGapItem] = field(default_factory=list)
    top_skills_to_learn: List[str] = field(default_factory=list)
    strong_count: int = 0
    improve_count: int = 0
    missing_count: int = 0

    def to_dict(self):
        return {
            "role_name": self.role_name,
            "items": [i.__dict__ for i in self.items],
            "top_skills_to_learn": self.top_skills_to_learn,
            "strong_count": self.strong_count,
            "improve_count": self.improve_count,
            "missing_count": self.missing_count,
        }


def analyze_skill_gap(db: Session, student: models.StudentProfile, role_name: str) -> SkillGapResult:
    requirements = (
        db.query(models.SkillRequirement)
        .filter(models.SkillRequirement.role_name.ilike(role_name))
        .all()
    )
    owned = {s.skill_name.strip().lower(): s.proficiency for s in student.skills}

    items: List[SkillGapItem] = []
    for req in requirements:
        key = req.skill_name.strip().lower()
        proficiency = owned.get(key, 0)
        if key not in owned:
            status = "Missing"
        elif proficiency >= STRONG_THRESHOLD:
            status = "Strong"
        elif proficiency >= IMPROVE_THRESHOLD:
            status = "Needs Improvement"
        else:
            status = "Missing"
        items.append(SkillGapItem(
            skill_name=req.skill_name,
            importance=req.importance,
            status=status,
            proficiency=proficiency,
        ))

    # priority: missing required skills first, then needs-improvement required,
    # then missing preferred skills
    def priority(item: SkillGapItem):
        rank = {
            ("Missing", "required"): 0,
            ("Needs Improvement", "required"): 1,
            ("Missing", "preferred"): 2,
            ("Needs Improvement", "preferred"): 3,
        }
        return rank.get((item.status, item.importance), 9)

    gap_items = [i for i in items if i.status != "Strong"]
    gap_items.sort(key=priority)
    top_skills = [i.skill_name for i in gap_items[:3]]

    result = SkillGapResult(
        role_name=role_name,
        items=items,
        top_skills_to_learn=top_skills,
        strong_count=sum(1 for i in items if i.status == "Strong"),
        improve_count=sum(1 for i in items if i.status == "Needs Improvement"),
        missing_count=sum(1 for i in items if i.status == "Missing"),
    )
    return result
