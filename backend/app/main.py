from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from app.database import engine

from app.config import settings
from app.seed import run_seed
from app.routes import auth, student, placements, ai, notifications, admin

app = FastAPI(
    title="HireReady - Intelligent Placement Coach API",
    description="Deterministic placement engines + AI coaching for college placements.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Create tables first, then apply tiny backwards-compatible SQLite migrations.
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    if engine.url.get_backend_name() == "sqlite":
        columns = {c["name"] for c in inspector.get_columns("certifications")}
        if "credential_url" not in columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE certifications ADD COLUMN credential_url VARCHAR DEFAULT ''"))
        user_columns = {c["name"] for c in inspector.get_columns("users")}
        with engine.begin() as conn:
            if "email_verified" not in user_columns:
                # Preserve accounts created before email verification was added.
                conn.execute(text("ALTER TABLE users ADD COLUMN email_verified BOOLEAN NOT NULL DEFAULT 1"))
            if "token_version" not in user_columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN token_version INTEGER NOT NULL DEFAULT 0"))
    run_seed()


@app.get("/api/health")
def health():
    return {"status": "ok", "ai_enabled": settings.ai_enabled}


app.include_router(auth.router)
app.include_router(student.router)
app.include_router(placements.router)
app.include_router(ai.router)
app.include_router(notifications.router)
app.include_router(admin.router)
