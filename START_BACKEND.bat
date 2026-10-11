@echo off
cd /d "%~dp0backend"
if not exist ".venv\Scripts\python.exe" py -m venv .venv
call .venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
