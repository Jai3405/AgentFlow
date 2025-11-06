# AgentFlow Project Structure

This document provides a clean overview of the AgentFlow project structure after cleanup and organization.

## Root Directory

```
AgentFlow/
├── Documentation
├── Startup Scripts
├── Backend (Python/FastAPI)
└── Frontend (React/TypeScript)
```

---

## Documentation Files

### Essential Documentation (Keep for Demo)

| File | Size | Purpose |
|------|------|---------|
| **readme.md** | 8KB | Main project overview and quick start |
| **Capstone_Project_Report.md** | 17KB | Complete capstone report (text) |
| **Capstone Project Report.pdf** | 146KB | Complete capstone report (PDF) |
| **CLAUDE.md** | 4KB | Instructions for Claude Code AI assistant |
| **IMPLEMENTATION_STATUS.md** | 16KB | Detailed phase-by-phase completion status |
| **COMPLETION_SUMMARY.md** | 14KB | Project completion summary and statistics |
| **PRE_DEMO_CHECKLIST.md** | 3.5KB | Pre-demo checklist and preparation |
| **DEMO_GUIDE.md** | 14KB | Complete 15-20 min demo walkthrough |
| **DEMO_README.md** | 4.5KB | Quick demo reference guide |
| **API_REFERENCE.md** | 15KB | REST API endpoint documentation |
| **SETUP_AND_USAGE.md** | 17KB | Detailed setup and usage instructions |

### Removed Documentation (Redundant)
- BACKEND_FIXES.md - Historical fixes
- FRONTEND_FIXES.md - Historical fixes
- STATEFUL_WORKFLOW_FIXES.md - Historical fixes
- PHASE_2_SUMMARY.md - Superseded by IMPLEMENTATION_STATUS.md
- PHASE_3_SUMMARY.md - Superseded by IMPLEMENTATION_STATUS.md
- CHANGELOG.md - Too detailed for capstone
- NATURAL_CONVERSATION_FEATURES.md - Covered in other docs

---

## Startup Scripts

| Script | Purpose |
|--------|---------|
| **quick_start_demo.sh** | One-command demo startup (macOS) |
| **scripts/start_dev_gemini.sh** | Manual development server startup (Gemini API) |
| **cleanup_project.sh** | Project cleanup utility (this was just run) |

### Removed Scripts
- complete_setup.sh - Consolidated into quick_start_demo.sh
- scripts/start_dev.sh - OpenAI version (using Gemini now)
- scripts/setup_prject.sh - Typo, duplicate functionality

---

## Backend Structure

```
backend/
├── alembic/                    # Database migrations
├── api/                        # REST API endpoints
│   ├── integrations.py         # Integration management endpoints
│   ├── execution.py            # Workflow execution endpoints
│   └── monitoring.py           # Monitoring and analytics endpoints
├── core/                       # Core application logic
│   ├── conversation_manager_gemini.py    # Gemini AI conversation handler
│   ├── conversation_graph.py             # LangGraph state machine
│   └── workflow_generator.py             # Workflow spec generator
├── database/                   # Database layer
│   ├── base.py                 # SQLAlchemy base setup
│   ├── models.py               # Database models (9 tables)
│   └── repositories/           # Data access layer
├── execution/                  # Workflow execution engine
│   ├── engine.py               # Main execution orchestrator
│   ├── step_processor.py       # Step-by-step executor (11 step types)
│   └── scheduler.py            # Job scheduling system
├── integrations/               # External service integrations
│   ├── base.py                 # Base integration class
│   ├── email_service.py        # Email integration
│   ├── slack_service.py        # Slack integration
│   ├── sms_service.py          # Twilio SMS integration
│   ├── webhook_service.py      # Webhook integration
│   ├── database_service.py     # Database integrations
│   └── file_service.py         # File operations
├── models/                     # Pydantic models
│   └── conversation.py         # Conversation state models
├── services/                   # Business logic services
│   ├── intent_classifier.py    # Intent classification
│   ├── entity_extractor.py     # Entity extraction
│   ├── entity_extractor_gemini.py  # Gemini-enhanced extraction
│   ├── confidence_scorer.py    # Confidence scoring
│   ├── workflow_validator.py   # Workflow validation
│   └── conversation_metrics.py # Conversation analytics
├── scripts/                    # Utility scripts
│   └── init_db.py              # Database initialization
├── tests/                      # Test suite
├── utils/                      # Utility functions
├── main_gemini.py              # FastAPI app entry point (Gemini)
├── requirements_gemini.txt     # Python dependencies
├── .env                        # Environment variables (NOT in git)
├── .env.gemini.example         # Example environment file
└── agentflow-venv/             # Python virtual environment
```

### Key Backend Features
- 13,000+ lines of Python code
- 45+ REST API endpoints
- 11 integration types
- 9 database tables
- Async/await throughout

---

## Frontend Structure

```
frontend/
├── public/                     # Static assets
│   ├── index.html              # Main HTML template
│   └── logo.png                # AgentFlow logo
├── src/                        # Source code
│   ├── components/             # React components
│   │   ├── ChatInterface.tsx           # Main chat UI
│   │   ├── WorkflowVisualization.tsx   # Workflow graph display
│   │   ├── ExecutionDashboard.tsx      # Execution monitoring
│   │   ├── AnalyticsDashboard.tsx      # System metrics
│   │   └── SchedulerUI.tsx             # Job scheduling UI
│   ├── types/                  # TypeScript definitions
│   │   └── index.ts            # Type definitions
│   ├── App.tsx                 # Main application component
│   ├── App.css                 # Application styles
│   └── index.tsx               # React entry point
├── package.json                # NPM dependencies
├── tsconfig.json               # TypeScript configuration
└── tailwind.config.js          # Tailwind CSS configuration
```

### Key Frontend Features
- React 18 with TypeScript
- 4 main views: Builder, Executions, Analytics, Scheduler
- Real-time workflow visualization
- Tailwind CSS styling
- Responsive design

---

## Database Schema (SQLite)

The AgentFlow database consists of 9 tables:

1. **messages** - Conversation messages
2. **conversations** - Conversation state
3. **workflows** - Workflow definitions
4. **workflow_executions** - Execution instances
5. **execution_logs** - Step-by-step logs
6. **integration_configs** - Integration credentials
7. **webhook_registrations** - Webhook endpoints
8. **scheduled_jobs** - Scheduled workflow runs
9. **alembic_version** - Database migration tracking

---

## Environment Variables

Required variables in `backend/.env`:

```bash
# Core Configuration
GEMINI_API_KEY=your_gemini_key_here
DATABASE_URL=sqlite:///./agentflow.db
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=["http://localhost:3000"]
DEBUG=True
LOG_LEVEL=INFO

# Optional Integrations (commented out by default)
# SLACK_BOT_TOKEN=xoxb-...
# TWILIO_ACCOUNT_SID=...
# GMAIL_CLIENT_ID=...
# POSTGRES_HOST=localhost
# MYSQL_HOST=localhost
# MONGODB_URI=mongodb://...
```

---

## Project Statistics

### Code Metrics
- Total Lines of Code: 13,000+
- Backend Python Files: ~80 files
- Frontend TypeScript Files: ~10 files
- API Endpoints: 45+
- Git Commits: 2

### Development Timeline
- Phase 1: Backend Infrastructure (Weeks 1-4)
- Phase 2: Enhanced Services (Weeks 5-6)
- Phase 3: Integration Layer (Weeks 7-9)
- Phase 4: Execution Engine (Weeks 10-12)
- Phase 5: Frontend Dashboards (Week 13)

---

## Quick Start

### Option 1: Automated Start (Recommended)
```bash
cd /Users/jay/Documents/AgentFlow
./quick_start_demo.sh
```

### Option 2: Manual Start
```bash
# Terminal 1 - Backend
cd backend
source agentflow-venv/bin/activate
python3 -m uvicorn main_gemini:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm start
```

### Access Points
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs
- API Base: http://localhost:8000/api

---

## Project Cleanup

The project has been cleaned up using `cleanup_project.sh`:

### Removed:
- 1,396 Python `__pycache__` directories
- 7 redundant documentation files (~96 KB)
- 3 redundant shell scripts (~26 KB)

### Result:
- Cleaner project structure
- Faster git operations
- Reduced confusion from duplicate docs
- Better organized for capstone presentation

---

## Documentation Roadmap

### For Capstone Demo
1. Start with: readme.md - Project overview
2. Reference: PRE_DEMO_CHECKLIST.md - Demo preparation
3. Follow: DEMO_GUIDE.md - Demo walkthrough
4. Submit: Capstone_Project_Report.pdf - Final report

### For Development
1. Setup: SETUP_AND_USAGE.md
2. API Reference: API_REFERENCE.md
3. Implementation: IMPLEMENTATION_STATUS.md
4. Claude Code: CLAUDE.md

---

## What's Not Included (Intentionally)

These items are properly ignored by `.gitignore`:

- `node_modules/` - NPM packages (frontend)
- `agentflow-venv/` - Python virtual environment
- `__pycache__/` - Python bytecode cache
- `.env` - Environment variables with secrets
- `*.db` - Database files
- `*.log` - Log files
- `.DS_Store` - macOS system files

**Always verify before committing:**
```bash
git status | grep .env  # Should return nothing
```

---

## Project Highlights

1. Conversational AI Interface - Natural language workflow creation
2. Real-time Visualization - Watch workflows build as you chat
3. Production-Ready Execution Engine - Handles 11 step types
4. Comprehensive Monitoring - Real-time dashboards and analytics
5. Flexible Scheduling - Cron, interval, and one-time jobs
6. Extensible Architecture - Easy to add new integrations
7. Full-Stack TypeScript/Python - Modern tech stack
8. Professional Documentation - Complete API docs and guides

---

**Last Updated:** November 7, 2025 (Phase 5 Complete)
