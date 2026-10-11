@echo off
setlocal
cd /d "%~dp0"
set "SHELL="
set "npm_config_script_shell="

echo ========================================
echo        HireReady - Intelligent Coach
echo ========================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
  echo Creating backend virtual environment...
  py -m venv backend\.venv
  if errorlevel 1 (
    echo Failed to create Python virtual environment. Install Python 3.11+ and try again.
    pause
    exit /b 1
  )
)

set "INSTALL_BACKEND_DEPS="
if not exist "backend\.venv\.hireready_deps_installed" set "INSTALL_BACKEND_DEPS=1"
"backend\.venv\Scripts\python.exe" -c "import email_validator" >nul 2>&1
if errorlevel 1 set "INSTALL_BACKEND_DEPS=1"

if defined INSTALL_BACKEND_DEPS (
  echo Installing backend dependencies...
  call "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
  call "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
  if errorlevel 1 (
    echo Backend dependency installation failed.
    pause
    exit /b 1
  )
  type nul > "backend\.venv\.hireready_deps_installed"
)

if not exist "frontend\node_modules" (
  echo Installing frontend dependencies...
  cd frontend
  call npm install
  if errorlevel 1 (
    echo Frontend dependency installation failed.
    pause
    exit /b 1
  )
  cd ..
)

echo Starting backend and frontend in separate windows...
start "HireReady Backend" cmd /k "cd /d %~dp0backend && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000"
start "HireReady Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

timeout /t 3 /nobreak >nul
start "" http://localhost:5173/login
endlocal
