import datetime as dt
import hashlib
import hmac
import secrets

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas
from app.auth import hash_password, verify_password, create_access_token, get_current_user
from app.config import settings
from app.services.email_service import send_verification_code

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _code_hash(code: str) -> str:
    return hashlib.sha256(f"{settings.JWT_SECRET}:{code}".encode("utf-8")).hexdigest()


def _issue_verification(user: models.User, db: Session) -> None:
    now = dt.datetime.utcnow()
    recent = db.query(models.EmailVerification).filter(
        models.EmailVerification.user_id == user.id,
        models.EmailVerification.created_at > now - dt.timedelta(seconds=60),
    ).first()
    if recent:
        raise HTTPException(status_code=429, detail="A code was just sent. Please wait one minute before requesting another.")

    code = f"{secrets.randbelow(1_000_000):06d}"
    db.query(models.EmailVerification).filter(models.EmailVerification.user_id == user.id).delete()
    db.add(models.EmailVerification(
        user_id=user.id, code_hash=_code_hash(code),
        expires_at=now + dt.timedelta(minutes=15), created_at=now,
    ))
    try:
        send_verification_code(user.email, code)
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/register", response_model=schemas.AuthMessageResponse)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if user and user.email_verified:
        raise HTTPException(status_code=400, detail="An account with this email already exists. Please log in.")

    if not user:
        user = models.User(
            email=email, hashed_password=hash_password(payload.password), role="student",
            full_name=payload.full_name.strip(), email_verified=False,
        )
        db.add(user)
        db.flush()
        db.add(models.StudentProfile(user_id=user.id))
    else:
        user.full_name = payload.full_name.strip()
        user.hashed_password = hash_password(payload.password)

    _issue_verification(user, db)
    db.commit()
    return schemas.AuthMessageResponse(message="Verification code sent. Enter it to activate your account.", email=email)


@router.post("/verify-email", response_model=schemas.TokenResponse)
def verify_email(payload: schemas.VerifyEmailRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    if user.email_verified:
        raise HTTPException(status_code=400, detail="This email is already verified. Please log in.")

    record = db.query(models.EmailVerification).filter(
        models.EmailVerification.user_id == user.id,
    ).order_by(models.EmailVerification.created_at.desc()).first()
    if not record or record.expires_at < dt.datetime.utcnow() or record.attempts >= 5:
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    if not hmac.compare_digest(record.code_hash, _code_hash(payload.code)):
        record.attempts += 1
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    user.email_verified = True
    db.query(models.EmailVerification).filter(models.EmailVerification.user_id == user.id).delete()
    db.commit()
    token = create_access_token(user.id, user.role, user.token_version)
    return schemas.TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    email = str(payload.email).strip().lower()
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    if not user.email_verified:
        raise HTTPException(status_code=403, detail="Verify your email before logging in. Submit your signup form again to send a new code.")
    token = create_access_token(user.id, user.role, user.token_version)
    return schemas.TokenResponse(access_token=token, role=user.role, full_name=user.full_name)


@router.post("/logout")
def logout(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.token_version += 1
    db.commit()
    return {"message": "Logged out successfully."}
