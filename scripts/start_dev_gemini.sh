#!/bin/bash
echo "Starting AgentFlow development environment with Gemini API..."

# Check if .env exists and has GEMINI_API_KEY
if [ -f backend/.env ]; then
    if grep -q "GEMINI_API_KEY" backend/.env; then
        echo "✓ Found GEMINI_API_KEY in .env file"
    else
        echo "⚠️  Warning: GEMINI_API_KEY not found in .env file"
        echo "Add your Gemini API key to backend/.env:"
        echo "GEMINI_API_KEY=your_api_key_here"
    fi
else
    echo "⚠️  Warning: .env file not found in backend directory"
    echo "Create backend/.env with:"
    echo "GEMINI_API_KEY=your_api_key_here"
fi

# Start backend with Gemini
echo "Starting backend server with Gemini API..."
cd backend
source agentflow-env/bin/activate 2>/dev/null || {
    echo "Virtual environment not found. Creating one..."
    python3 -m venv agentflow-env
    source agentflow-env/bin/activate
    pip install -r requirements_gemini.txt
}

# Check if Gemini requirements are installed
python -c "import google.generativeai" 2>/dev/null || {
    echo "Installing Gemini requirements..."
    pip install -r requirements_gemini.txt
}

uvicorn main_gemini:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
echo "Starting frontend development server..."
cd ../frontend
npm start &
FRONTEND_PID=$!

echo "Backend PID: $BACKEND_PID"
echo "Frontend PID: $FRONTEND_PID"
echo ""
echo "🚀 AgentFlow with Gemini API is running:"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" INT
wait