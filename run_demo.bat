@echo off
title Engineering Knowledge Agent (DevGuard + CodeGuard) - Demo Server
echo =====================================================================
echo  Engineering Knowledge Agent (EKA) - Final Year CSE Review Showcase
echo =====================================================================
echo.
echo Starting FastAPI Backend + React UI on http://127.0.0.1:8000 ...
echo Demo Accounts:
echo   - Developer : dev@acme   / demo123 (Simulates incidents, views traces)
echo   - Manager   : mgr@acme   / demo123 (Approves/rejects partial fixes)
echo   - Viewer    : viewer@acme/ demo123 (Audit trail & metrics read-only)
echo.
echo Launching browser in 2 seconds...
timeout /t 2 /nobreak >nul
start http://127.0.0.1:8000/
echo.
cd /d "%~dp0\ai-service"
python -m uvicorn eka.api:app --host 127.0.0.1 --port 8000
pause

