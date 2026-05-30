@echo off
echo Starting Sentinel AI...

start "Sentinel Backend" cmd /k "cd /d C:\College\BE CSE\Downloads\sentinel-ai\backend && venv\Scripts\activate && uvicorn main:app --reload --port 3001"

timeout /t 3 /nobreak >nul

start "Sentinel Frontend" cmd /k "cd /d C:\College\BE CSE\Downloads\sentinel-ai\frontend && npm run dev"

echo Both servers starting...
echo Backend:  http://localhost:3001
echo Frontend: http://localhost:3000
pause