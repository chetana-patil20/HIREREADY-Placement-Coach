"""
Database models for HireReady.

Covers: users, student_profiles, skills, student_skills, companies,
job_roles, placement_drives, eligibility_rules, applications, projects,
certifications, internships, resumes, skill_requirements,
preparation_tasks, interview_sessions, interview_questions,
notifications, events, announcements, timetable, exams, support_tickets,
chat_history.
"""
import datetime as dt
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from app.database import Base


def now():
    return dt.datetime.utcnow()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="student")  # student | admin
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=now)
    email_verified = Column(Boolean, default=True, nullable=False)
    token_version = Column(Integer, default=0, nullable=False)

    profile = relationship("StudentProfile", back_populates="user", uselist=False)


class EmailVerification(Base):
    __tablename__ = "email_verifications"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    code_hash = Column(String, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)


class StudentProfile(Base):
    __tablename__ = "student_profiles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)

    branch = Column(String, default="")
    cgpa = Column(Float, default=0.0)
    percentage_10 = Column(Float, default=0.0)
    percentage_12 = Column(Float, default=0.0)
    backlogs = Column(Integer, default=0)
    graduation_year = Column(Integer, default=dt.date.today().year + 1)
    target_role = Column(String, default="")
    available_study_hours_per_day = Column(Float, default=2.0)
    resume_text = Column(Text, default="")
    resume_score = Column(Integer, default=0)
    soft_skills = Column(Text, default="")  # comma separated
    linkedin_url = Column(String, default="")
    github_url = Column(String, default="")
    phone = Column(String, default="")

    user = relationship("User", back_populates="profile")
    skills = relationship("StudentSkill", back_populates="student", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="student", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="student", cascade="all, delete-orphan")
    internships = relationship("Internship", back_populates="student", cascade="all, delete-orphan")
    tasks = relationship("PreparationTask", back_populates="student", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="student", cascade="all, delete-orphan")
    interview_sessions = relationship("InterviewSession", back_populates="student", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    category = Column(String, default="technical")  # technical | soft | tool


class StudentSkill(Base):
    __tablename__ = "student_skills"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    skill_name = Column(String, nullable=False)
    proficiency = Column(Integer, default=50)  # 0-100

    student = relationship("StudentProfile", back_populates="skills")


class Company(Base):
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    logo_emoji = Column(String, default="🏢")
    about = Column(Text, default="")

    job_roles = relationship("JobRole", back_populates="company", cascade="all, delete-orphan")


class JobRole(Base):
    __tablename__ = "job_roles"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    title = Column(String, nullable=False)
    ctc_lpa = Column(Float, default=0.0)
    location = Column(String, default="")
    work_mode = Column(String, default="On-site")  # On-site | Remote | Hybrid

    min_cgpa = Column(Float, default=6.0)
    min_percentage_10 = Column(Float, default=0.0)
    min_percentage_12 = Column(Float, default=0.0)
    max_backlogs = Column(Integer, default=0)
    eligible_graduation_years = Column(String, default="")  # comma separated years
    eligible_branches = Column(String, default="")  # comma separated, blank = all

    required_skills = Column(Text, default="")  # comma separated
    preferred_skills = Column(Text, default="")  # comma separated
    min_experience_months = Column(Integer, default=0)

    application_deadline = Column(Date, nullable=True)
    drive_date = Column(Date, nullable=True)
    description = Column(Text, default="")

    company = relationship("Company", back_populates="job_roles")
    applications = relationship("Application", back_populates="job_role", cascade="all, delete-orphan")


class Application(Base):
    __tablename__ = "applications"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    job_role_id = Column(Integer, ForeignKey("job_roles.id"))
    status = Column(String, default="Applied")  # Applied | Shortlisted | Rejected | Selected
    applied_at = Column(DateTime, default=now)

    student = relationship("StudentProfile", back_populates="applications")
    job_role = relationship("JobRole", back_populates="applications")


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    tech_stack = Column(String, default="")  # comma separated
    link = Column(String, default="")

    student = relationship("StudentProfile", back_populates="projects")


class Certification(Base):
    __tablename__ = "certifications"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    title = Column(String, nullable=False)
    issuer = Column(String, default="")
    year = Column(Integer, nullable=True)
    credential_url = Column(String, default="")

    student = relationship("StudentProfile", back_populates="certifications")


class Internship(Base):
    __tablename__ = "internships"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    company_name = Column(String, nullable=False)
    role = Column(String, default="")
    duration_months = Column(Integer, default=1)
    description = Column(Text, default="")

    student = relationship("StudentProfile", back_populates="internships")


class SkillRequirement(Base):
    """Required skill sets per target role, used by the skill-gap engine."""
    __tablename__ = "skill_requirements"
    id = Column(Integer, primary_key=True)
    role_name = Column(String, nullable=False)  # e.g. "AI Engineer"
    skill_name = Column(String, nullable=False)
    importance = Column(String, default="required")  # required | preferred


class PreparationTask(Base):
    __tablename__ = "preparation_tasks"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    week = Column(Integer, default=1)
    day = Column(Integer, default=1)
    category = Column(String, default="")  # Technical | Aptitude | Resume | Interview | Project
    title = Column(String, nullable=False)
    description = Column(Text, default="")
    estimated_minutes = Column(Integer, default=60)
    difficulty = Column(String, default="Medium")  # Easy | Medium | Hard
    completed = Column(Boolean, default=False)
    plan_role = Column(String, default="")
    created_at = Column(DateTime, default=now)

    student = relationship("StudentProfile", back_populates="tasks")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    mode = Column(String, default="Technical")  # HR | Technical | Aptitude | Role-specific
    role = Column(String, default="")
    started_at = Column(DateTime, default=now)
    overall_score = Column(Integer, nullable=True)

    student = relationship("StudentProfile", back_populates="interview_sessions")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id"))
    question_text = Column(Text, nullable=False)
    student_answer = Column(Text, default="")
    score = Column(Integer, nullable=True)
    strengths = Column(Text, default="")
    weaknesses = Column(Text, default="")
    improved_answer = Column(Text, default="")
    order_index = Column(Integer, default=0)

    session = relationship("InterviewSession", back_populates="questions")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"), nullable=True)  # null = broadcast
    title = Column(String, nullable=False)
    message = Column(Text, default="")
    category = Column(String, default="general")  # deadline | drive | eligibility | task | interview | announcement
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=now)


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    category = Column(String, default="workshop")  # hackathon | workshop | seminar | placement | career
    description = Column(Text, default="")
    event_date = Column(Date, nullable=True)
    location = Column(String, default="")


class Announcement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    body = Column(Text, default="")
    created_at = Column(DateTime, default=now)


class TimetableEntry(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True)
    day_of_week = Column(String, default="Monday")
    subject = Column(String, nullable=False)
    start_time = Column(String, default="09:00")
    end_time = Column(String, default="10:00")
    room = Column(String, default="")


class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True)
    subject = Column(String, nullable=False)
    exam_date = Column(Date, nullable=True)
    exam_type = Column(String, default="Semester")


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    category = Column(String, default="other")  # IT | classroom | infrastructure | placement | other
    subject = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="Pending")  # Pending | In Progress | Resolved
    created_at = Column(DateTime, default=now)


class ChatMessage(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id"))
    role = Column(String, default="user")  # user | assistant
    content = Column(Text, default="")
    created_at = Column(DateTime, default=now)
