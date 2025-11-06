#!/bin/bash

# AgentFlow Quick Start Script for Demo
# This script helps you start the application quickly

echo "🚀 AgentFlow Demo Quick Start"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
    echo -e "${RED}❌ Error: Please run this script from the AgentFlow root directory${NC}"
    exit 1
fi

echo -e "${BLUE}📋 Pre-flight checks...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

# Check Node
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}✅ Node.js: $NODE_VERSION${NC}"
else
    echo -e "${RED}❌ Node.js not found${NC}"
    exit 1
fi

# Check backend dependencies
if [ -d "backend/.env" ] || [ -f "backend/.env" ]; then
    echo -e "${GREEN}✅ Backend environment configured${NC}"
else
    echo -e "${YELLOW}⚠️  Backend .env not found (will use defaults)${NC}"
fi

# Check database
if [ -f "backend/agentflow.db" ]; then
    echo -e "${GREEN}✅ Database initialized${NC}"
else
    echo -e "${YELLOW}⚠️  Database not found${NC}"
    echo -e "${BLUE}   Initializing database...${NC}"
    cd backend && python3 scripts/init_db.py && cd ..
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Database initialized${NC}"
    else
        echo -e "${RED}❌ Database initialization failed${NC}"
        exit 1
    fi
fi

# Check frontend dependencies
if [ -d "frontend/node_modules" ]; then
    echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend dependencies not installed${NC}"
    echo -e "${BLUE}   Installing dependencies...${NC}"
    cd frontend && npm install && cd ..
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Frontend dependencies installed${NC}"
    else
        echo -e "${RED}❌ Frontend installation failed${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}✅ All checks passed!${NC}"
echo ""
echo -e "${BLUE}🎯 Starting AgentFlow...${NC}"
echo ""
echo -e "${YELLOW}This will open two terminal windows:${NC}"
echo "  1. Backend (FastAPI) on port 8000"
echo "  2. Frontend (React) on port 3000"
echo ""
echo -e "${YELLOW}To stop the servers:${NC}"
echo "  Press Ctrl+C in each terminal window"
echo ""
echo "Press any key to start..."
read -n 1 -s

# Function to start backend
start_backend() {
    echo -e "${BLUE}🔧 Starting Backend...${NC}"
    cd backend
    python3 -m uvicorn main_gemini:app --reload --port 8000
}

# Function to start frontend
start_frontend() {
    echo -e "${BLUE}🎨 Starting Frontend...${NC}"
    sleep 3  # Wait for backend to start
    cd frontend
    npm start
}

# Check OS and open terminals accordingly
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "cd '"$PWD"' && bash quick_start_demo.sh backend"' &
    osascript -e 'tell app "Terminal" to do script "cd '"$PWD"' && bash quick_start_demo.sh frontend"' &

    echo ""
    echo -e "${GREEN}✅ Terminals opened!${NC}"
    echo ""
    echo -e "${BLUE}📍 Access points:${NC}"
    echo "  Frontend:     http://localhost:3000"
    echo "  Backend API:  http://localhost:8000"
    echo "  API Docs:     http://localhost:8000/docs"
    echo ""
    echo -e "${YELLOW}Wait 10-15 seconds for services to start${NC}"
    echo ""
    exit 0
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    gnome-terminal -- bash -c "cd $PWD/backend && python3 -m uvicorn main_gemini:app --reload --port 8000; exec bash" &
    gnome-terminal -- bash -c "cd $PWD/frontend && npm start; exec bash" &
    echo -e "${GREEN}✅ Terminals opened!${NC}"
    exit 0
else
    # Windows or unknown
    echo -e "${YELLOW}⚠️  Please manually open two terminals and run:${NC}"
    echo ""
    echo "Terminal 1 (Backend):"
    echo "  cd backend"
    echo "  python3 -m uvicorn main_gemini:app --reload --port 8000"
    echo ""
    echo "Terminal 2 (Frontend):"
    echo "  cd frontend"
    echo "  npm start"
    exit 0
fi

# Handle backend/frontend sub-commands (for terminal spawning)
if [ "$1" == "backend" ]; then
    start_backend
elif [ "$1" == "frontend" ]; then
    start_frontend
fi
