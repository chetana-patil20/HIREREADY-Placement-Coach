"""
Eligibility Engine
==================
Pure, deterministic rule evaluation. No AI is involved anywhere in this
file. Given a student profile and a job role, decides ELIGIBLE /
NOT_ELIGIBLE and returns the exact reasons, so the student always knows
*why*.
"""
from dataclasses import dataclass, field
from typing import List
from app import models


@dataclass
class EligibilityCheck:
    passed: bool
    label: str  # short human label, e.g. "Minimum CGPA"
    detail: str  # e.g. "Your CGPA is 7.8. This company requires 8.0."


@dataclass
class EligibilityResult:
    eligible: bool
    checks: List[EligibilityCheck] = field(default_factory=list)

    @property
    def failed_reasons(self) -> List[str]:
        return [c.detail for c in self.checks if not c.passed]

    def to_dict(self):
        return {
            "eligible": self.eligible,
            "checks": [c.__dict__ for c in self.checks],
            "failed_reasons": self.failed_reasons,
        }


def _student_skill_names(student: models.StudentProfile) -> set:
    return {s.skill_name.strip().lower() for s in student.skills}


def _total_experience_months(student: models.StudentProfile) -> int:
    return sum(i.duration_months or 0 for i in student.internships)


def check_eligibility(student: models.StudentProfile, role: models.JobRole) -> EligibilityResult:
    checks: List[EligibilityCheck] = []

    # 1. CGPA
    cgpa_ok = student.cgpa >= role.min_cgpa
    checks.append(EligibilityCheck(
        passed=cgpa_ok,
        label="Minimum CGPA",
        detail=(
            f"Your CGPA is {student.cgpa:.1f}, which meets the required {role.min_cgpa:.1f}."
            if cgpa_ok else
            f"Your CGPA is {student.cgpa:.1f}. This company requires a minimum CGPA of {role.min_cgpa:.1f}."
        ),
    ))

    # 2. 10th percentage
    if role.min_percentage_10 and role.min_percentage_10 > 0:
        p10_ok = student.percentage_10 >= role.min_percentage_10
        checks.append(EligibilityCheck(
            passed=p10_ok,
            label="10th Percentage",
            detail=(
                f"Your 10th percentage ({student.percentage_10:.1f}%) meets the requirement."
                if p10_ok else
                f"Your 10th percentage is {student.percentage_10:.1f}%. Minimum required is {role.min_percentage_10:.1f}%."
            ),
        ))

    # 3. 12th percentage
    if role.min_percentage_12 and role.min_percentage_12 > 0:
        p12_ok = student.percentage_12 >= role.min_percentage_12
        checks.append(EligibilityCheck(
            passed=p12_ok,
            label="12th Percentage",
            detail=(
                f"Your 12th percentage ({student.percentage_12:.1f}%) meets the requirement."
                if p12_ok else
                f"Your 12th percentage is {student.percentage_12:.1f}%. Minimum required is {role.min_percentage_12:.1f}%."
            ),
        ))

    # 4. Backlogs
    backlog_ok = student.backlogs <= role.max_backlogs
    checks.append(EligibilityCheck(
        passed=backlog_ok,
        label="Active Backlogs",
        detail=(
            f"You have {student.backlogs} active backlog(s), within the allowed {role.max_backlogs}."
            if backlog_ok else
            f"You have {student.backlogs} active backlog(s). This company allows a maximum of {role.max_backlogs}."
        ),
    ))

    # 5. Graduation year
    allowed_years = [y.strip() for y in (role.eligible_graduation_years or "").split(",") if y.strip()]
    if allowed_years:
        year_ok = str(student.graduation_year) in allowed_years
        checks.append(EligibilityCheck(
            passed=year_ok,
            label="Graduation Year",
            detail=(
                f"Your graduation year ({student.graduation_year}) is eligible."
                if year_ok else
                f"Your graduation year is {student.graduation_year}. This drive is open to: {', '.join(allowed_years)}."
            ),
        ))

    # 6. Branch
    allowed_branches = [b.strip().lower() for b in (role.eligible_branches or "").split(",") if b.strip()]
    if allowed_branches:
        branch_ok = (student.branch or "").strip().lower() in allowed_branches
        checks.append(EligibilityCheck(
            passed=branch_ok,
            label="Branch",
            detail=(
                f"Your branch ({student.branch}) is eligible."
                if branch_ok else
                f"Your branch is {student.branch or 'not set'}. Eligible branches: {', '.join(allowed_branches)}."
            ),
        ))

    # 7. Required skills
    required = [s.strip().lower() for s in (role.required_skills or "").split(",") if s.strip()]
    if required:
        owned = _student_skill_names(student)
        missing = [s for s in required if s not in owned]
        skills_ok = len(missing) == 0
        checks.append(EligibilityCheck(
            passed=skills_ok,
            label="Required Skills",
            detail=(
                "You have all the required skills for this role."
                if skills_ok else
                f"You are missing required skill(s): {', '.join(missing)}."
            ),
        ))

    # 8. Experience
    if role.min_experience_months and role.min_experience_months > 0:
        exp_months = _total_experience_months(student)
        exp_ok = exp_months >= role.min_experience_months
        checks.append(EligibilityCheck(
            passed=exp_ok,
            label="Experience",
            detail=(
                f"You have {exp_months} month(s) of internship experience, which meets the requirement."
                if exp_ok else
                f"You have {exp_months} month(s) of internship experience. Minimum required is {role.min_experience_months} month(s)."
            ),
        ))

    eligible = all(c.passed for c in checks)
    return EligibilityResult(eligible=eligible, checks=checks)
