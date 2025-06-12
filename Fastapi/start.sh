#!/bin/bash

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

# Start the FastAPI backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Save backend PID
BACKEND_PID=$!

# Start the frontend (assuming it's a React app in 'frontend' folder)
cd frontend
npm install
npm run dev -- --host &

# Save frontend PID
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID
wait $FRONTEND_PID
