"""
Seeds the database with realistic demo data so the app looks populated
immediately after first run. Safe to call multiple times - it checks
whether data already exists before inserting.
"""
import datetime as dt
from app.database import SessionLocal, engine, Base
from app import models
from app.auth import hash_password

TODAY = dt.date.today()


def seed_skill_requirements(db):
    if db.query(models.SkillRequirement).count() > 0:
        return
    role_requirements = {
        "Python Developer": {
            "required": ["Python", "SQL", "Git", "REST APIs", "Django"],
            "preferred": ["Docker", "AWS", "Pandas"],
        },
        "AI Engineer": {
            "required": ["Python", "SQL", "NumPy", "Pandas", "Machine Learning", "Git"],
            "preferred": ["Deep Learning", "Docker", "Cloud Basics", "APIs"],
        },
        "Data Analyst": {
            "required": ["SQL", "Excel", "Python", "Data Visualization", "Statistics"],
            "preferred": ["Power BI", "Tableau", "Pandas"],
        },
        "Frontend Developer": {
            "required": ["HTML", "CSS", "JavaScript", "React", "Git"],
            "preferred": ["TypeScript", "Tailwind CSS", "Next.js"],
        },
        "Software Developer": {
            "required": ["Data Structures", "Algorithms", "Java", "SQL", "Git"],
            "preferred": ["System Design", "REST APIs", "Docker"],
        },
    }
    for role, groups in role_requirements.items():
        for skill in groups["required"]:
            db.add(models.SkillRequirement(role_name=role, skill_name=skill, importance="required"))
        for skill in groups["preferred"]:
            db.add(models.SkillRequirement(role_name=role, skill_name=skill, importance="preferred"))
    db.commit()


def seed_companies_and_roles(db):
    if db.query(models.Company).count() > 0:
        return

    companies_data = [
        {
            "name": "Infosys", "logo_emoji": "🟦",
            "roles": [{
                "title": "Software Developer", "ctc_lpa": 6.5, "location": "Bengaluru", "work_mode": "On-site",
                "min_cgpa": 6.5, "min_percentage_10": 60, "min_percentage_12": 60, "max_backlogs": 1,
                "eligible_graduation_years": f"{TODAY.year},{TODAY.year + 1}",
                "eligible_branches": "",
                "required_skills": "Data Structures,Algorithms,Java,SQL",
                "preferred_skills": "Git,REST APIs",
                "min_experience_months": 0,
                "application_deadline": TODAY + dt.timedelta(days=4),
                "drive_date": TODAY + dt.timedelta(days=10),
                "description": "Entry-level software development role covering Java-based enterprise applications.",
            }],
        },
        {
            "name": "TCS Digital", "logo_emoji": "🟪",
            "roles": [{
                "title": "Python Developer", "ctc_lpa": 7.0, "location": "Hyderabad", "work_mode": "Hybrid",
                "min_cgpa": 7.0, "min_percentage_10": 60, "min_percentage_12": 60, "max_backlogs": 0,
                "eligible_graduation_years": f"{TODAY.year},{TODAY.year + 1}",
                "eligible_branches": "",
                "required_skills": "Python,SQL,Git,REST APIs",
                "preferred_skills": "Django,Docker,AWS",
                "min_experience_months": 0,
                "application_deadline": TODAY + dt.timedelta(days=2),
                "drive_date": TODAY + dt.timedelta(days=8),
                "description": "Backend development role focused on Python microservices.",
            }],
        },
        {
            "name": "Deloitte Analytics", "logo_emoji": "🟩",
            "roles": [{
                "title": "Data Analyst", "ctc_lpa": 8.0, "location": "Pune", "work_mode": "On-site",
                "min_cgpa": 7.0, "min_percentage_10": 0, "min_percentage_12": 0, "max_backlogs": 0,
                "eligible_graduation_years": f"{TODAY.year},{TODAY.year + 1}",
                "eligible_branches": "",
                "required_skills": "SQL,Excel,Python,Statistics",
                "preferred_skills": "Power BI,Tableau,Pandas",
                "min_experience_months": 0,
                "application_deadline": TODAY + dt.timedelta(days=12),
                "drive_date": TODAY + dt.timedelta(days=20),
                "description": "Business analytics role interpreting data for client engagements.",
            }],
        },
        {
            "name": "NeuralArc AI", "logo_emoji": "🟧",
            "roles": [{
                "title": "AI/ML Intern", "ctc_lpa": 5.0, "location": "Remote", "work_mode": "Remote",
                "min_cgpa": 7.5, "min_percentage_10": 0, "min_percentage_12": 0, "max_backlogs": 0,
                "eligible_graduation_years": f"{TODAY.year},{TODAY.year + 1},{TODAY.year + 2}",
                "eligible_branches": "",
                "required_skills": "Python,NumPy,Pandas,Machine Learning",
                "preferred_skills": "Deep Learning,Docker,Cloud Basics",
                "min_experience_months": 0,
                "application_deadline": TODAY + dt.timedelta(days=6),
                "drive_date": TODAY + dt.timedelta(days=14),
                "description": "Internship building and evaluating ML models for production pipelines.",
            }],
        },
        {
            "name": "PixelForge Labs", "logo_emoji": "🟥",
            "roles": [{
                "title": "Frontend Developer", "ctc_lpa": 6.0, "location": "Chennai", "work_mode": "Hybrid",
                "min_cgpa": 6.0, "min_percentage_10": 0, "min_percentage_12": 0, "max_backlogs": 1,
                "eligible_graduation_years": f"{TODAY.year},{TODAY.year + 1}",
                "eligible_branches": "",
                "required_skills": "HTML,CSS,JavaScript,React",
                "preferred_skills": "TypeScript,Tailwind CSS,Next.js",
                "min_experience_months": 0,
                "application_deadline": TODAY + dt.timedelta(days=18),
                "drive_date": TODAY + dt.timedelta(days=25),
                "description": "Building customer-facing web interfaces for a design-tools product.",
            }],
        },
        {
            "name": "Quantify Systems", "logo_emoji": "🟨",
            "roles": [{
                "title": "AI Engineer", "ctc_lpa": 11.0, "location": "Bengaluru", "work_mode": "On-site",
                "min_cgpa": 8.0, "min_percentage_10": 0, "min_percentage_12": 0, "max_backlogs": 0,
                "eligible_graduation_years": f"{TODAY.year},{TODAY.year + 1}",
                "eligible_branches": "",
                "required_skills": "Python,SQL,NumPy,Pandas,Machine Learning",
                "preferred_skills": "Deep Learning,Docker,Cloud Basics",
                "min_experience_months": 2,
                "application_deadline": TODAY + dt.timedelta(days=15),
                "drive_date": TODAY + dt.timedelta(days=22),
                "description": "High-CGPA-bar AI engineering role - deliberately harder to qualify for, to demo ineligibility.",
            }],
        },
    ]

    for c in companies_data:
        company = models.Company(name=c["name"], logo_emoji=c["logo_emoji"])
        db.add(company)
        db.commit()
        db.refresh(company)
        for r in c["roles"]:
            db.add(models.JobRole(company_id=company.id, **r))
    db.commit()


def seed_events_and_announcements(db):
    if db.query(models.Event).count() == 0:
        events = [
            {"title": "Resume Building Workshop", "category": "workshop",
             "description": "Hands-on session on writing placement-ready resumes.",
             "event_date": TODAY + dt.timedelta(days=3), "location": "Seminar Hall A"},
            {"title": "CodeSprint Hackathon", "category": "hackathon",
             "description": "24-hour hackathon sponsored by Quantify Systems.",
             "event_date": TODAY + dt.timedelta(days=9), "location": "Innovation Lab"},
            {"title": "Placement Orientation", "category": "placement",
             "description": "Overview of this year's placement process and timelines.",
             "event_date": TODAY + dt.timedelta(days=1), "location": "Main Auditorium"},
            {"title": "Career in AI Seminar", "category": "career",
             "description": "Industry panel discussing careers in applied AI.",
             "event_date": TODAY + dt.timedelta(days=16), "location": "Seminar Hall B"},
        ]
        for e in events:
            db.add(models.Event(**e))
        db.commit()

    if db.query(models.Announcement).count() == 0:
        announcements = [
            {"title": "Placement registrations now open",
             "body": "All final-year students must complete their HireReady profile before applying to any drive."},
            {"title": "Semester exam schedule released",
             "body": "Check the Academics tab for the updated exam timetable."},
        ]
        for a in announcements:
            db.add(models.Announcement(**a))
        db.commit()


def seed_timetable_and_exams(db):
    if db.query(models.TimetableEntry).count() == 0:
        entries = [
            {"day_of_week": "Monday", "subject": "Data Structures", "start_time": "09:00", "end_time": "10:00", "room": "CS-101"},
            {"day_of_week": "Monday", "subject": "Database Systems", "start_time": "10:00", "end_time": "11:00", "room": "CS-102"},
            {"day_of_week": "Tuesday", "subject": "Operating Systems", "start_time": "09:00", "end_time": "10:00", "room": "CS-101"},
            {"day_of_week": "Wednesday", "subject": "Machine Learning", "start_time": "11:00", "end_time": "12:00", "room": "CS-201"},
            {"day_of_week": "Thursday", "subject": "Computer Networks", "start_time": "09:00", "end_time": "10:00", "room": "CS-103"},
            {"day_of_week": "Friday", "subject": "Placement Prep Lab", "start_time": "14:00", "end_time": "16:00", "room": "Lab-3"},
        ]
        for e in entries:
            db.add(models.TimetableEntry(**e))
        db.commit()

    if db.query(models.Exam).count() == 0:
        exams = [
            {"subject": "Database Systems", "exam_date": TODAY + dt.timedelta(days=20), "exam_type": "Semester"},
            {"subject": "Operating Systems", "exam_date": TODAY + dt.timedelta(days=22), "exam_type": "Semester"},
            {"subject": "Machine Learning", "exam_date": TODAY + dt.timedelta(days=24), "exam_type": "Semester"},
        ]
        for e in exams:
            db.add(models.Exam(**e))
        db.commit()


def seed_demo_student(db):
    existing = db.query(models.User).filter(models.User.email == "demo.student@hireready.app").first()
    if existing:
        return

    user = models.User(
        email="demo.student@hireready.app",
        hashed_password=hash_password("Demo@1234"),
        role="student",
        full_name="Ananya Sharma",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    profile = models.StudentProfile(
        user_id=user.id, branch="Computer Science", cgpa=7.8, percentage_10=88, percentage_12=82,
        backlogs=0, graduation_year=TODAY.year + 1, target_role="AI Engineer",
        available_study_hours_per_day=3,
        soft_skills="Communication,Teamwork,Problem Solving",
        linkedin_url="https://linkedin.com/in/ananya-sharma-demo",
        github_url="https://github.com/ananya-demo",
        phone="+91 98765 43210",
        resume_text=(
            "Ananya Sharma\nEducation: B.Tech Computer Science, CGPA 7.8\n"
            "Skills: Python, SQL, Pandas, Machine Learning basics, Git\n"
            "Projects: Built a student attendance predictor using Pandas and scikit-learn. "
            "Built a task tracker web app.\n"
            "Certifications: Python for Data Science (Coursera)\n"
        ),
        resume_score=58,
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)

    skills = [
        ("Python", 78), ("SQL", 70), ("Pandas", 65), ("NumPy", 55),
        ("Machine Learning", 40), ("Git", 60), ("HTML", 50), ("CSS", 45),
    ]
    for name, prof in skills:
        db.add(models.StudentSkill(student_id=profile.id, skill_name=name, proficiency=prof))

    db.add(models.Project(
        student_id=profile.id, title="Student Attendance Predictor",
        description="A machine learning model that predicts at-risk students from attendance patterns.",
        tech_stack="Python,Pandas,Machine Learning", link="https://github.com/ananya-demo/attendance-predictor",
    ))
    db.add(models.Project(
        student_id=profile.id, title="Campus Task Tracker",
        description="A simple full-stack task tracker for student clubs.",
        tech_stack="Python,SQL,HTML,CSS", link="https://github.com/ananya-demo/task-tracker",
    ))

    db.add(models.Certification(student_id=profile.id, title="Python for Data Science", issuer="Coursera", year=TODAY.year - 1))
    db.add(models.Internship(student_id=profile.id, company_name="LocalTech Solutions", role="Data Analyst Intern",
                              duration_months=2, description="Cleaned and analyzed sales data using Pandas and SQL."))
    db.commit()


def seed_demo_admin(db):
    existing = db.query(models.User).filter(models.User.email == "admin@hireready.app").first()
    if existing:
        return
    admin = models.User(
        email="admin@hireready.app",
        hashed_password=hash_password("Admin@1234"),
        role="admin",
        full_name="Placement Cell Admin",
    )
    db.add(admin)
    db.commit()


def run_seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_skill_requirements(db)
        seed_companies_and_roles(db)
        seed_events_and_announcements(db)
        seed_timetable_and_exams(db)
        seed_demo_student(db)
        seed_demo_admin(db)
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
    print("Seed complete.")
