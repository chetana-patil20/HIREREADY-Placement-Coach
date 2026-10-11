import datetime as dt
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    password: str
    role: str = "student"  # student | admin


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    full_name: str


class AuthMessageResponse(BaseModel):
    message: str
    email: EmailStr


class VerifyEmailRequest(BaseModel):
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


# ---------- Student profile ----------
class SkillIn(BaseModel):
    skill_name: str
    proficiency: int = Field(50, ge=0, le=100)


class ProjectIn(BaseModel):
    id: Optional[int] = None
    title: str
    description: str = ""
    tech_stack: str = ""
    link: str = ""


class CertificationIn(BaseModel):
    id: Optional[int] = None
    title: str
    issuer: str = ""
    year: Optional[int] = None
    credential_url: str = ""


class InternshipIn(BaseModel):
    id: Optional[int] = None
    company_name: str
    role: str = ""
    duration_months: int = 1
    description: str = ""


class ProfileUpdateRequest(BaseModel):
    branch: Optional[str] = None
    cgpa: Optional[float] = None
    percentage_10: Optional[float] = None
    percentage_12: Optional[float] = None
    backlogs: Optional[int] = None
    graduation_year: Optional[int] = None
    target_role: Optional[str] = None
    available_study_hours_per_day: Optional[float] = None
    soft_skills: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    phone: Optional[str] = None
    skills: Optional[List[SkillIn]] = None
    projects: Optional[List[ProjectIn]] = None
    certifications: Optional[List[CertificationIn]] = None
    internships: Optional[List[InternshipIn]] = None


# ---------- AI ----------
class ChatRequest(BaseModel):
    message: str


class ResumeAnalysisRequest(BaseModel):
    resume_text: str


class InterviewStartRequest(BaseModel):
    mode: str  # HR | Technical | Aptitude | Role-specific
    role: Optional[str] = None


class InterviewAnswerRequest(BaseModel):
    session_id: int
    question_id: int
    answer: str


# ---------- Admin ----------
class JobRoleCreate(BaseModel):
    company_name: str
    company_logo_emoji: str = "🏢"
    title: str
    ctc_lpa: float
    location: str = ""
    work_mode: str = "On-site"
    min_cgpa: float = 6.0
    min_percentage_10: float = 0.0
    min_percentage_12: float = 0.0
    max_backlogs: int = 0
    eligible_graduation_years: str = ""
    eligible_branches: str = ""
    required_skills: str = ""
    preferred_skills: str = ""
    min_experience_months: int = 0
    application_deadline: Optional[dt.date] = None
    drive_date: Optional[dt.date] = None
    description: str = ""


class AnnouncementCreate(BaseModel):
    title: str
    body: str = ""


class EventCreate(BaseModel):
    title: str
    category: str = "workshop"
    description: str = ""
    event_date: Optional[dt.date] = None
    location: str = ""


class SupportTicketCreate(BaseModel):
    category: str = "other"
    subject: str
    description: str = ""


class SupportTicketStatusUpdate(BaseModel):
    status: str
