@echo off

REM Démarrer le backend FastAPI
start "FastAPI" cmd /k uvicorn backend.main:app --host 0.0.0.0 --port 8000

REM Démarrer le frontend React
cd frontend
start "Frontend" cmd /k npm run dev

REM Facultatif : attendre que l'utilisateur ferme les fenêtres
pause
