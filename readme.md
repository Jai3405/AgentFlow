<div align="center">

# AgentFlow

### Build Agents by Talking to One

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18.0-blue.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688.svg)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)](https://www.typescriptlang.org/)

*A revolutionary conversational AI platform that transforms natural language into production-ready workflow automation*

[Demo](#-quick-start) • [Features](#-key-features) • [Architecture](#-architecture) • [Documentation](#-documentation)

---

</div>

## Overview

**AgentFlow** is a next-generation workflow automation platform that eliminates the complexity barrier between business requirements and technical implementation. Instead of drag-and-drop interfaces or complex scripting, users simply describe what they need in natural language, and AgentFlow's AI engine automatically generates, visualizes, and deploys complete automation workflows.

### The Challenge

In today's enterprise landscape, **90% of automation initiatives fail to reach production** due to:
- Technical complexity preventing non-technical users from building solutions
- Steep learning curves for traditional automation platforms
- Disconnect between business domain knowledge and technical implementation
- Time-intensive manual workflow construction and testing

### Our Solution

AgentFlow bridges this gap with a **conversational AI interface** that understands business requirements and automatically generates production-grade workflows with proper error handling, monitoring, and optimization built-in from day one.

---

## Key Features

<table>
<tr>
<td width="50%">

### For Business Users

**Zero Learning Curve**
- Describe workflows in plain English
- No programming or technical knowledge required
- Intelligent follow-up questions to clarify requirements

**Real-Time Visualization**
- Watch your workflow being built as you describe it
- Interactive step-by-step process breakdown
- Immediate feedback and confidence scoring

**Complete Transparency**
- Understand exactly what your workflow will do
- See all integration points and data flows
- Review and approve before deployment

</td>
<td width="50%">

### For Technical Teams

**Production-Ready Output**
- Enterprise-grade code with monitoring built-in
- Comprehensive error handling and recovery
- Security best practices enforced automatically

**Full Observability**
- Real-time execution dashboards
- Detailed analytics and performance metrics
- Step-by-step execution logs and debugging

**Extensible Architecture**
- 11 integration types out of the box
- Easy to add custom integrations
- RESTful API with 45+ endpoints

</td>
</tr>
</table>

---

## How It Works

```mermaid
graph LR
    A[Natural Language Input] --> B[AI Intent Analysis]
    B --> C[Entity Extraction]
    C --> D[Workflow Generation]
    D --> E[Real-Time Visualization]
    E --> F[Validation & Deployment]
    F --> G[Execution & Monitoring]
```

### 1. Conversational Design

```
You: "I need to automate our customer support email system.
      Monitor support@company.com for incoming emails, categorize
      them as technical, billing, or general inquiries."

AgentFlow: "I'll create an email automation workflow for you.
            I understand you want to:
            - Monitor support@company.com
            - Categorize emails into 3 types

            Should I also route these to specific teams or create
            notifications for urgent cases?"
```

### 2. Intelligent Workflow Construction

As you describe your needs, AgentFlow:
- Analyzes intent and extracts business entities
- Maps requirements to technical components
- Constructs workflow graphs with proper dependencies
- Generates production-ready steps with error handling
- Validates completeness and suggests improvements

### 3. Live Execution & Monitoring

- **Real-time execution dashboards** with status tracking
- **Analytics dashboards** with success rates and performance metrics
- **Scheduler interface** for automated workflow runs
- **Detailed logging** for debugging and auditing

---

## Quick Start

### Prerequisites

```bash
Python 3.10+    Node.js 16+    Google Gemini API Key
```

### Installation

**Option 1: Quick Start (Recommended)**

```bash
# Clone the repository
git clone https://github.com/yourusername/AgentFlow.git
cd AgentFlow

# Run automated setup
./quick_start_demo.sh
```

The script will:
- Check system requirements
- Install backend dependencies in virtual environment
- Install frontend dependencies
- Initialize the database
- Start both servers automatically
- Open the application in your browser

**Option 2: Manual Setup**

```bash
# 1. Clone and navigate
git clone https://github.com/yourusername/AgentFlow.git
cd AgentFlow

# 2. Backend Setup
cd backend
python3 -m venv agentflow-venv
source agentflow-venv/bin/activate  # On Windows: agentflow-venv\Scripts\activate
pip install -r requirements_gemini.txt

# 3. Configure environment
cp .env.gemini.example .env
# Edit .env and add your GEMINI_API_KEY

# 4. Initialize database
python scripts/init_db.py

# 5. Start backend (in backend directory)
python3 -m uvicorn main_gemini:app --reload --port 8000

# 6. Frontend Setup (new terminal)
cd frontend
npm install
npm start
```

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Builder    │  │  Executions  │  │  Analytics   │          │
│  │  Interface   │  │  Dashboard   │  │  Dashboard   │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         React 18 + TypeScript + Tailwind CSS                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                         REST API
                              │
┌─────────────────────────────────────────────────────────────────┐
│                         Backend Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Conversation │  │   Workflow   │  │  Execution   │          │
│  │    Engine    │  │  Generator   │  │    Engine    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         FastAPI + LangGraph + Google Gemini AI                  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Integration Layer                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │
│  │ Email  │ │ Slack  │ │  SMS   │ │Database│ │Webhook │       │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

<table>
<tr>
<td width="50%" valign="top">

**Backend Technologies**
- **FastAPI** - Modern async web framework
- **LangGraph** - Stateful conversation management
- **Google Gemini AI** - Natural language understanding
- **SQLAlchemy** - Database ORM with migrations
- **Alembic** - Database version control
- **Pydantic** - Data validation and serialization

</td>
<td width="50%" valign="top">

**Frontend Technologies**
- **React 18** - Component-based UI framework
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client for API calls
- **React Hooks** - Modern state management

</td>
</tr>
</table>

### Project Structure

```
AgentFlow/
├── backend/
│   ├── api/                        # REST API endpoints
│   │   ├── integrations.py         # Integration management (45+ endpoints)
│   │   ├── execution.py            # Workflow execution control
│   │   └── monitoring.py           # Analytics and monitoring
│   ├── core/                       # Core business logic
│   │   ├── conversation_manager_gemini.py  # AI conversation engine
│   │   ├── conversation_graph.py           # LangGraph state machine
│   │   └── workflow_generator.py           # Workflow compilation
│   ├── database/                   # Data persistence layer
│   │   ├── models.py               # SQLAlchemy models (9 tables)
│   │   └── repositories/           # Data access patterns
│   ├── execution/                  # Workflow execution engine
│   │   ├── engine.py               # Orchestration and scheduling
│   │   ├── step_processor.py       # Step execution (11 types)
│   │   └── scheduler.py            # Cron, interval, one-time jobs
│   ├── integrations/               # External service connectors
│   │   ├── email_service.py        # Gmail, Outlook integration
│   │   ├── slack_service.py        # Slack messaging
│   │   ├── sms_service.py          # Twilio SMS
│   │   ├── database_service.py     # PostgreSQL, MySQL, MongoDB
│   │   ├── file_service.py         # CSV, Excel, JSON processing
│   │   └── webhook_service.py      # HTTP webhooks
│   ├── services/                   # Enhanced AI services
│   │   ├── intent_classifier.py    # Intent recognition
│   │   ├── entity_extractor_gemini.py  # Entity extraction
│   │   ├── confidence_scorer.py    # Quality scoring
│   │   ├── workflow_validator.py   # Validation engine
│   │   └── conversation_metrics.py # Analytics tracking
│   └── main_gemini.py              # Application entry point
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatInterface.tsx           # Conversational UI
│   │   │   ├── WorkflowVisualization.tsx   # Real-time graph
│   │   │   ├── ExecutionDashboard.tsx      # Live monitoring
│   │   │   ├── AnalyticsDashboard.tsx      # Metrics & stats
│   │   │   └── SchedulerUI.tsx             # Job management
│   │   ├── types/index.ts          # TypeScript definitions
│   │   └── App.tsx                 # Main application component
│   └── public/
│       └── logo.png                # Application branding
│
└── documentation/
    ├── API_REFERENCE.md            # Complete API documentation
    ├── DEMO_GUIDE.md               # Demo walkthrough (15-20 min)
    ├── SETUP_AND_USAGE.md          # Detailed setup guide
    └── PROJECT_STRUCTURE.md        # Architecture deep-dive
```

---

## Core Components

### 1. Conversational AI Engine

Powered by Google's Gemini 2.0, the conversation engine:
- Understands business requirements in natural language
- Extracts entities (emails, databases, schedules, conditions)
- Maintains conversation context across multiple turns
- Asks intelligent follow-up questions to clarify requirements
- Provides confidence scores for requirement completeness

### 2. Workflow Generator

Automatically compiles conversations into:
- Structured workflow specifications
- Step-by-step execution plans
- Proper error handling and retry logic
- Monitoring and logging instrumentation
- Integration point configurations

### 3. Execution Engine

Production-grade execution system with:
- **11 Step Types**: Email, Slack, SMS, Database, File, Webhook, Condition, Loop, Wait, Transform, API Call
- **Parallel Execution**: Concurrent step processing where possible
- **Error Recovery**: Automatic retry with exponential backoff
- **State Management**: Persistent execution state across restarts
- **Real-time Monitoring**: Live status updates and progress tracking

### 4. Integration Layer

Pre-built connectors for:
- **Communication**: Email (Gmail, Outlook), Slack, SMS (Twilio)
- **Data**: PostgreSQL, MySQL, MongoDB, CSV, Excel, JSON
- **Automation**: Webhooks, HTTP APIs, Scheduled triggers
- **All integrations support both production and simulation modes**

---

## Usage Examples

### Example 1: Customer Support Automation

```plaintext
User: "I need to automate our customer support email system. Monitor
       support@company.com for incoming emails, categorize them as
       technical, billing, or general inquiries, and route technical
       issues to tech@company.com and billing issues to billing@company.com.
       Also send a Slack notification to #support-team for urgent cases."

AgentFlow Response:
✓ Email monitoring configured for support@company.com
✓ AI categorization enabled (technical, billing, general)
✓ Routing rules created:
  - Technical → tech@company.com
  - Billing → billing@company.com
✓ Slack notifications enabled for #support-team (urgent only)
✓ Workflow validation passed (100% confidence)

Your workflow is ready! Would you like to:
1. Test with sample data
2. Schedule for immediate deployment
3. Review the generated workflow steps
```

### Example 2: Daily Report Generation

```plaintext
User: "Generate and email daily sales reports at 9 AM every weekday.
       Pull data from our PostgreSQL database, create an Excel summary,
       and send to managers@company.com"

AgentFlow Response:
✓ Scheduled job created: Weekdays at 9:00 AM
✓ Database connection configured (PostgreSQL)
✓ Report format: Excel with summary sheets
✓ Email recipients: managers@company.com
✓ Estimated execution time: 2-3 minutes

Workflow includes:
- Data extraction from sales_data table
- Aggregation and pivot calculations
- Excel generation with charts
- Email delivery with attachment
- Error notifications if data is missing

Ready to activate?
```

### Example 3: Alert System

```plaintext
User: "Monitor our API health endpoint every 5 minutes. If it returns
       an error or takes longer than 2 seconds, send me a Slack alert
       with the error details"

AgentFlow Response:
✓ Health check interval: Every 5 minutes
✓ Monitoring: API response time and status
✓ Alert threshold: >2 seconds or error status
✓ Notification channel: Slack (your DM)

Your monitoring workflow includes:
- HTTP GET request to health endpoint
- Response time measurement
- Status code validation
- Conditional alerting logic
- Alert deduplication (max 1 per hour)

This workflow will run continuously. Start monitoring now?
```

---

## Project Statistics

<table>
<tr>
<td align="center"><b>13,000+</b><br>Lines of Code</td>
<td align="center"><b>45+</b><br>REST API Endpoints</td>
<td align="center"><b>11</b><br>Integration Types</td>
<td align="center"><b>9</b><br>Database Tables</td>
</tr>
<tr>
<td align="center"><b>4</b><br>Major Dashboards</td>
<td align="center"><b>11</b><br>Step Processors</td>
<td align="center"><b>3</b><br>Scheduler Types</td>
<td align="center"><b>100%</b><br>Async/Await</td>
</tr>
</table>

---

## Development Phases

### Phase 1: Foundation (Completed)
- Conversational interface with AI-powered intent recognition
- Real-time workflow visualization with progress tracking
- Basic entity extraction and workflow generation
- React frontend with TypeScript and Tailwind CSS

### Phase 2: Enhanced Intelligence (Completed)
- Advanced Gemini AI integration for natural conversations
- Confidence scoring and requirement validation
- Multi-turn conversation optimization
- Conversation quality metrics and analytics

### Phase 3: Integration Layer (Completed)
- Email integration (Gmail, Outlook with OAuth)
- Slack messaging integration
- SMS integration via Twilio
- Webhook system for real-time triggers
- Database connectors (PostgreSQL, MySQL, MongoDB)
- File processing (CSV, Excel, JSON)

### Phase 4: Execution Engine (Completed)
- Production-grade workflow execution orchestrator
- 11 step types with parallel execution support
- Comprehensive error handling and retry logic
- Job scheduling system (cron, interval, one-time)
- Real-time monitoring and logging infrastructure

### Phase 5: Monitoring & Analytics (Completed)
- Execution dashboard with live status tracking
- Analytics dashboard with system metrics
- Scheduler UI for job management
- Performance optimization and scaling improvements

---

## API Documentation

AgentFlow provides a comprehensive REST API with 45+ endpoints across multiple domains:

### Core Endpoints

**Conversation Management**
```http
POST   /api/chat                    # Process conversation messages
GET    /api/conversations/{id}      # Retrieve conversation history
DELETE /api/conversations/{id}      # Delete conversation
```

**Workflow Management**
```http
POST   /api/workflows/generate/{conversation_id}  # Generate workflow from conversation
GET    /api/workflows                              # List all workflows
GET    /api/workflows/{id}                         # Get workflow details
PUT    /api/workflows/{id}                         # Update workflow
DELETE /api/workflows/{id}                         # Delete workflow
```

**Execution Control**
```http
POST   /api/execute/{workflow_id}   # Start workflow execution
GET    /api/executions              # List executions
GET    /api/executions/{id}         # Get execution details
POST   /api/executions/{id}/pause   # Pause execution
POST   /api/executions/{id}/resume  # Resume execution
POST   /api/executions/{id}/cancel  # Cancel execution
```

**Monitoring & Analytics**
```http
GET    /api/analytics/metrics       # System-wide metrics
GET    /api/analytics/executions    # Execution statistics
GET    /api/executions/{id}/logs    # Detailed execution logs
```

**Integration Management**
```http
GET    /api/integrations            # List available integrations
POST   /api/integrations            # Configure integration
GET    /api/integrations/{id}       # Get integration details
PUT    /api/integrations/{id}       # Update integration
DELETE /api/integrations/{id}       # Delete integration
POST   /api/integrations/{id}/test  # Test integration
```

**Scheduler**
```http
GET    /api/scheduler/jobs          # List scheduled jobs
POST   /api/scheduler/jobs          # Create scheduled job
GET    /api/scheduler/jobs/{id}     # Get job details
PUT    /api/scheduler/jobs/{id}     # Update job
DELETE /api/scheduler/jobs/{id}     # Delete job
POST   /api/scheduler/jobs/{id}/enable   # Enable job
POST   /api/scheduler/jobs/{id}/disable  # Disable job
```

---

## Database Schema

AgentFlow uses SQLAlchemy ORM with a comprehensive 9-table schema:

```sql
conversations          -- Conversation state and metadata
├── messages          -- Individual conversation messages
└── workflows         -- Generated workflow specifications

workflow_executions   -- Execution instances and status
└── execution_logs    -- Step-by-step execution logs

integration_configs   -- Integration credentials and settings

webhook_registrations -- Registered webhook endpoints

scheduled_jobs        -- Scheduled workflow runs

alembic_version      -- Database migration tracking
```

All tables include:
- Timestamps (created_at, updated_at)
- Soft delete support
- JSON metadata fields for flexibility
- Proper indexing for query performance

---

## Configuration

### Environment Variables

Create a `backend/.env` file with the following configuration:

```bash
# Core Configuration (Required)
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./agentflow.db
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=["http://localhost:3000"]

# Development Settings
DEBUG=True
LOG_LEVEL=INFO

# Optional: Email Integration
# GMAIL_CLIENT_ID=your_client_id
# GMAIL_CLIENT_SECRET=your_client_secret

# Optional: Slack Integration
# SLACK_BOT_TOKEN=xoxb-your-token
# SLACK_SIGNING_SECRET=your_secret

# Optional: SMS Integration
# TWILIO_ACCOUNT_SID=your_account_sid
# TWILIO_AUTH_TOKEN=your_auth_token
# TWILIO_PHONE_NUMBER=+1234567890

# Optional: Database Connections
# POSTGRES_HOST=localhost
# POSTGRES_PORT=5432
# MYSQL_HOST=localhost
# MONGODB_URI=mongodb://localhost:27017
```

**Security Note**: The `.env` file is excluded from git via `.gitignore`. Never commit API keys or secrets to version control.

### Getting API Keys

**Google Gemini API (Required)**
1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)

**Optional Integrations** (for live demonstrations)
- **Slack**: https://api.slack.com/apps
- **Twilio**: https://www.twilio.com/console
- **Gmail**: https://console.cloud.google.com (OAuth2 setup required)

---

## Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/integration/ -v

# E2E tests
npm run test:e2e
```

### Test Coverage

The project includes comprehensive test coverage across:
- Unit tests for core business logic
- Integration tests for API endpoints
- E2E tests for critical user workflows
- Mock services for external integrations

---

## Deployment

### Docker Deployment (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Manual Deployment

**Backend**
```bash
cd backend
gunicorn main_gemini:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Frontend**
```bash
cd frontend
npm run build
# Serve the 'build' directory with your preferred web server
```

### Environment Considerations

- **Development**: SQLite database, debug mode enabled
- **Staging**: PostgreSQL database, reduced logging
- **Production**: PostgreSQL with replication, comprehensive monitoring, rate limiting

---

## Documentation

Comprehensive documentation is available in the repository:

| Document | Description |
|----------|-------------|
| [API_REFERENCE.md](API_REFERENCE.md) | Complete API endpoint documentation |
| [SETUP_AND_USAGE.md](SETUP_AND_USAGE.md) | Detailed setup and configuration guide |
| [DEMO_GUIDE.md](DEMO_GUIDE.md) | 15-20 minute demo walkthrough |
| [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) | Deep-dive into architecture |
| [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) | Phase-by-phase completion tracking |
| [PRE_DEMO_CHECKLIST.md](PRE_DEMO_CHECKLIST.md) | Demo preparation checklist |

---

## Troubleshooting

### Common Issues

**Backend won't start**
```bash
cd backend
pip install -r requirements_gemini.txt
python scripts/init_db.py
```

**Frontend won't start**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Port already in use**
```bash
# Kill backend process
lsof -ti:8000 | xargs kill -9

# Kill frontend process
lsof -ti:3000 | xargs kill -9
```

**Database errors**
```bash
cd backend
rm agentflow.db  # Reset database
python scripts/init_db.py
```

---

## Contributing

We welcome contributions from the community! Here's how you can help:

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
   - Follow existing code style and conventions
   - Add tests for new functionality
   - Update documentation as needed
4. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
5. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**
   - Describe your changes in detail
   - Reference any related issues
   - Wait for review and feedback

### Development Guidelines

- **Code Style**: Follow PEP 8 for Python, ESLint rules for TypeScript
- **Testing**: Maintain or improve test coverage
- **Documentation**: Update docs for any user-facing changes
- **Commits**: Use clear, descriptive commit messages

---

## Roadmap

### Upcoming Features

**Short-term (Next 3 months)**
- Visual workflow editor alongside conversational interface
- Workflow templates library for common use cases
- Enhanced error recovery with automatic rollback
- Multi-language support (Spanish, French, German)

**Medium-term (3-6 months)**
- Workflow marketplace for sharing community templates
- Advanced scheduling with holiday calendars
- Machine learning model integration (custom ML workflows)
- Team collaboration features (shared workflows, permissions)

**Long-term (6-12 months)**
- Self-optimization using genetic algorithms
- Federated learning for privacy-preserving workflows
- Blockchain integration for immutable audit trails
- Mobile application (iOS and Android)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- Commercial use allowed
- Modification allowed
- Distribution allowed
- Private use allowed
- Liability and warranty not provided

---

## Authors

<table>
<tr>
<td align="center">
<img src="https://github.com/Jai3405.png" width="100px;" alt="Jayaditya Reddy"/><br />
<sub><b>Jayaditya Reddy</b></sub><br />
<a href="https://github.com/Jai3405">GitHub</a>
</td>
<td align="center">
<img src="https://github.com/adipkg.png" width="100px;" alt="Adip Krishna"/><br />
<sub><b>Adip Krishna</b></sub><br />
<a href="https://github.com/adipkrishna">GitHub</a>
</td>
</tr>
</table>

**Institution**: Woxsen University, School of Technology
**Department**: Computer Science and Engineering
**Academic Year**: 2025-2026, 7th Semester

---

## Acknowledgments

Special thanks to:
- **Google** for Gemini AI API access
- **FastAPI** and **React** communities for excellent documentation
- **Open source contributors** whose libraries made this project possible

---

## Contact & Support

- **Project Repository**: [https://github.com/Jai3405/AgentFlow](https://github.com/Jai3405/AgentFlow)
- **Issues & Bug Reports**: [GitHub Issues](https://github.com/Jai3405/AgentFlow/issues)
- **Documentation**: [Project Wiki](https://github.com/Jai3405/AgentFlow/wiki)

For academic inquiries or collaboration opportunities, please contact the authors through GitHub.

---

<div align="center">

### Built with passion by students, for the future of automation

**AgentFlow** - Making AI workflow automation as simple as having a conversation

[Back to Top](#agentflow)

</div>
