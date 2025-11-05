#!/bin/bash
echo "Starting AgentFlow development environment..."

# Start backend
echo "Starting backend server..."
cd backend
source agentflow-env/bin/activate
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend development server..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" INT
wait