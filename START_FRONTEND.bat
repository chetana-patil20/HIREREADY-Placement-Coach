@echo off
cd /d "%~dp0frontend"
set "SHELL="
set "npm_config_script_shell="
npm config delete script-shell >nul 2>&1
if not exist "node_modules" npm install
npm run dev
