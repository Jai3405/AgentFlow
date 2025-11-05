# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AgentFlow is a conversational AI platform that transforms natural language descriptions into production-ready AI agent workflows. This is a full-stack application with a Python FastAPI backend and React TypeScript frontend.

## Development Commands

### Backend (Python FastAPI)
```bash
# From backend directory
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (React TypeScript)
```bash
# From frontend directory
npm install
npm start          # Development server on port 3000
npm build          # Production build
npm test           # Run tests
```

### Full Development Setup
```bash
# Start both backend and frontend concurrently (OpenAI version)
./scripts/start_dev.sh

# Start with Gemini API alternative
./scripts/start_dev_gemini.sh

# Complete initial setup
./complete_setup.sh
```

### Gemini API Alternative
```bash
# From backend directory (Gemini version)
pip install -r requirements_gemini.txt
uvicorn main_gemini:app --reload --port 8000

# Setup environment for Gemini
cp .env.gemini.example .env
# Edit .env and add your GEMINI_API_KEY
```

## Architecture Overview

### Backend Structure (`/backend/`)
- **main.py** - FastAPI application entry point (OpenAI version)
- **main_gemini.py** - FastAPI application entry point (Gemini version)  
- **core/conversation_manager.py** - Multi-turn conversation state management using LangGraph
- **core/conversation_manager_gemini.py** - Gemini API conversation manager
- **core/workflow_generator.py** - Converts conversations into workflow specifications
- **models/conversation.py** - Pydantic models for conversation state and messages
- **services/intent_classifier.py** - Regex-based intent classification
- **services/entity_extractor.py** - Business entity extraction from user input

### Frontend Structure (`/frontend/src/`)
- **App.tsx** - Main React application component
- **components/ChatInterface.tsx** - Primary conversation interface
- **components/WorkflowVisualization.tsx** - Real-time workflow building display
- **types/index.ts** - TypeScript definitions for API communication

### Key API Endpoints
- **POST `/api/chat`** - Main conversation processing endpoint
- **GET `/api/conversations/{conversation_id}`** - Retrieve conversation history
- **POST `/api/workflows/generate/{conversation_id}`** - Generate workflow from conversation

## Technology Stack

### Backend
- FastAPI with async support
- LangGraph for conversation state management
- LangChain for LLM integration framework
- Pydantic v2 for data validation
- Planned SQLAlchemy integration for persistence

### Frontend
- React 18 with TypeScript
- Tailwind CSS for styling
- Axios for API communication
- Create React App tooling

## Development Notes

### Current State
- Uses regex-based intent classification (email_automation, data_processing, approval_workflow, notification_system)
- In-memory conversation storage (SQLAlchemy configured for future database integration)
- Two LLM integration options available:
  - OpenAI version: Uses LangChain/OpenAI (currently rule-based fallback)
  - Gemini version: Uses Google's Gemini API with smart conversation handling
- Environment variables required: 
  - OpenAI version: OPENAI_API_KEY
  - Gemini version: GEMINI_API_KEY

### Architecture Patterns
- Conversational state management with LangGraph state machines
- Progressive workflow building with real-time visualization
- RESTful API design with auto-generated FastAPI documentation
- Component-based React architecture with TypeScript safety

### Testing and Quality
- No specific linting/formatting commands found - check package.json scripts in frontend/ for available commands
- Test structure established in both backend/tests/ and frontend test infrastructure