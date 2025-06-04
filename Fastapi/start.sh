#!/bin/bash

# Start the FastAPI backend
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &

# Save backend PID
BACKEND_PID=$!

# Start the frontend (assuming it's a React app in 'frontend' folder)
cd frontend
npm install
npm run dev &

# Save frontend PID
FRONTEND_PID=$!

# Wait for both processes
wait $BACKEND_PID
wait $FRONTEND_PID