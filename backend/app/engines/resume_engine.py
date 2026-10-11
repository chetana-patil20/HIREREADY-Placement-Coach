"""
Resume Analyzer - deterministic scoring layer.
Parses the resume text for structural completeness and keyword coverage.
The AI service is layered on top only to phrase suggestions - the score
itself and the list of flagged problems are computed here, from the
actual text, never invented.
"""
import re
from typing import Dict, List
from app import models

SECTION_KEYWORDS = {
    "education": ["education", "b.tech", "bachelor", "university", "college", "cgpa"],
    "experience": ["experience", "internship", "worked at"],
    "projects": ["project"],
    "skills": ["skills", "technologies"],
    "certifications": ["certification", "certified", "course"],
}

MEASURABLE_PATTERNS = [r"\d+%", r"\b\d{2,}\+?\s*(users|records|requests|ms|seconds|rows)\b"]


def analyze_resume_text(resume_text: str, target_role: str, required_skills: List[str]) -> Dict:
    text = resume_text or ""
    lower = text.lower()
    word_count = len(text.split())

    sections_found = {name: any(k in lower for k in kws) for name, kws in SECTION_KEYWORDS.items()}
    has_github = bool(re.search(r"github\.com", lower))
    has_linkedin = bool(re.search(r"linkedin\.com", lower))
    has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[a-z]{2,}", lower))
    has_phone = bool(re.search(r"(\+?\d[\d\-\s]{8,}\d)", text))

    measurable_hits = sum(1 for pat in MEASURABLE_PATTERNS if re.search(pat, lower))
    weak_project_descriptions = sections_found["projects"] and measurable_hits == 0

    missing_keywords = [s for s in required_skills if s.lower() not in lower] if required_skills else []

    # ---- scoring (out of 100) ----
    score = 0
    score += 15 if sections_found["education"] else 0
    score += 15 if sections_found["skills"] else 0
    score += 15 if sections_found["projects"] else 0
    score += 10 if sections_found["experience"] or sections_found["certifications"] else 5
    score += 10 if has_github else 0
    score += 5 if has_linkedin else 0
    score += 10 if has_email and has_phone else 5
    score += 10 if measurable_hits > 0 else 0
    if required_skills:
        coverage = 1 - (len(missing_keywords) / len(required_skills))
        score += round(coverage * 10)
    else:
        score += 5
    score = max(0, min(100, score))

    problems = []
    if not sections_found["education"]:
        problems.append("No clear education section detected.")
    if not sections_found["skills"]:
        problems.append("No dedicated skills section detected.")
    if not sections_found["projects"]:
        problems.append("No projects section detected.")
    if weak_project_descriptions:
        problems.append("Project descriptions lack measurable impact (numbers, percentages, scale).")
    if not has_github:
        problems.append("No GitHub link found.")
    if missing_keywords:
        problems.append(f"Missing role-relevant keywords: {', '.join(missing_keywords[:6])}.")
    if word_count < 120:
        problems.append("Resume looks quite short - consider adding more detail.")

    findings = {
        "weak_project_descriptions": weak_project_descriptions,
        "missing_github": not has_github,
        "missing_metrics": measurable_hits == 0,
        "missing_keywords": missing_keywords,
        "short_resume": word_count < 120,
        "sections_found": sections_found,
    }

    return {
        "score": score,
        "problems": problems,
        "findings": findings,
        "word_count": word_count,
        "has_github": has_github,
        "has_linkedin": has_linkedin,
    }
