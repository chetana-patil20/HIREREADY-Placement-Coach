# HIREREADY — Intelligent Placement Coach

HireReady is a Windows-friendly full-stack placement platform built with React + Vite on the frontend and FastAPI + SQLite on the backend.

## Quick start on Windows

### Easiest option
Double-click **`START_HIREREADY.bat`**.

It will:
1. Create `backend\\.venv` if needed.
2. Install Python dependencies.
3. Install frontend dependencies if `node_modules` is missing.
4. Start FastAPI on `http://localhost:8000`.
5. Start Vite on `http://localhost:5173`.
6. Open the login page automatically.

### Manual option
Backend terminal:
```powershell
cd backend
py -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Frontend terminal:
```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173/login`.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Student | `demo.student@hireready.app` | `Demo@1234` |
| Admin | `admin@hireready.app` | `Admin@1234` |

## Important notes

- SQLite is used by default, so PostgreSQL is **not required** for the demo.
- The backend pins `bcrypt==4.0.1` because the project's Passlib version is not compatible with newer bcrypt releases.
- AI features work without an API key using a profile-aware deterministic fallback. A real LLM is optional.
- Never put an AI API key in the React frontend. Put it only in `backend/.env`.

## AI configuration (optional)

Copy `backend/.env.example` to `backend/.env` and set either:
```env
AI_PROVIDER=openai
AI_API_KEY=your_key_here
AI_MODEL=gpt-4o-mini
```

or:
```env
AI_PROVIDER=anthropic
AI_API_KEY=your_key_here
AI_MODEL=claude-sonnet-4-6
```

or Google Gemini:
```env
AI_PROVIDER=gemini
AI_API_KEY=your_key_here
AI_MODEL=gemini-2.5-flash
```

If these are empty, HireReady automatically uses its local-smart coaching and evaluation logic.

## Email verification setup (required for new accounts)

New registrations send a 6-digit verification code to the entered address. The account cannot log in until that code is confirmed. Existing demo accounts continue to work.

1. Copy `backend/.env.example` to `backend/.env`.
2. Set `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`, and `SMTP_FROM_EMAIL` for your email provider.
3. For Gmail, enable 2-Step Verification and create an App Password. Put the App Password in `SMTP_PASSWORD`; do not use your regular Gmail password.
4. Save `.env`, then restart the backend.

If SMTP is not configured or cannot send, signup will show an error and will not create a usable account. Keep `backend/.env` private and do not upload it in a ZIP.

## Main student flow

1. Login.
2. Complete **My Profile**.
3. Add technical skills with real proficiency values.
4. Add projects with title, description, tech stack and GitHub/project URL.
5. Add certifications with title, issuer, year and optional credential URL.
6. Save the profile.
7. Check Dashboard, Placements and Skill Gap.
8. Generate a Preparation Plan.
9. Run a Mock Interview.
10. Use AI Coach for profile-aware placement questions.

## Functional improvements in this build

- Stable responsive profile form layout.
- Explicit labels for project and certification fields.
- Certification credential URL support.
- Backwards-compatible SQLite migration for the new certification URL column.
- AI Coach connection/error states and animated typing feedback.
- Local-smart AI fallback works without an API key.
- Interview scoring evaluates key idea coverage, correctness, examples, reasoning, relevance, and structure; long vague answers earn no automatic high score.
- Signup verifies ownership of the email with an expiring code; unverified accounts cannot log in.
- Mock interview scoring considers question coverage, answer detail, examples and reasoning; question history is used to avoid repeating recent questions across sessions.
- Dashboard readiness includes the score meaning, category weights and the next three concrete actions.
- Windows startup scripts for one-click local execution.
- Passlib/bcrypt dependency compatibility fix.
