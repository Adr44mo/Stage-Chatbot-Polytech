#!/bin/bash

# Kill any existing uvicorn or vite processes
pkill -f uvicorn
pkill -f vite

# Attendre que les processus soient bien terminés
sleep 1

# Libérer explicitement les ports si besoin
if lsof -i :8000 >/dev/null; then
  echo "Port 8000 encore occupé, on kill le process..."
  fuser -k 8000/tcp
  sleep 1
fi
if lsof -i :5173 >/dev/null; then
  echo "Port 5173 encore occupé, on kill le process..."
  fuser -k 5173/tcp
  sleep 1
fi

# Path to the project root and virtual environment
PROJECT_ROOT="/srv/partage/Stage-Chatbot-Polytech"
VENV_PATH="$PROJECT_ROOT/.venv/bin/activate"

# Activate the virtual environment
if [ -f "$VENV_PATH" ]; then
  source "$VENV_PATH"
else
  echo "Environnement virtuel introuvable à $VENV_PATH"
  exit 1
fi

echo "🔁 Reloading Nginx..."
sudo ./Fastapi/nginx -t && sudo systemctl reload nginx

# Start the FastAPI backend
uvicorn Fastapi.backend.main:app --host 0.0.0.0 --port 8000 --reload &

# Save backend PID
BACKEND_PID=$!

# Start the frontend (assuming it's a React app in 'frontend' folder)
cd Fastapi/frontend
npm install
npm run dev -- --host &

# Save frontend PID
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID
wait $FRONTEND_PID

