# AgentFlow - Complete Setup and Usage Guide

## Table of Contents
1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Detailed Installation](#detailed-installation)
4. [Configuration](#configuration)
5. [API Documentation](#api-documentation)
6. [Workflow Examples](#workflow-examples)
7. [Troubleshooting](#troubleshooting)

---

## Overview

**AgentFlow** is a conversational AI platform that transforms natural language descriptions into production-ready AI agent workflows. It provides a complete end-to-end solution from conversation to execution.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AgentFlow System                         │
├─────────────────────────────────────────────────────────────┤
│  Phase 1: Foundation                                         │
│  ├─ Conversational Interface (Gemini AI)                    │
│  ├─ LangGraph State Machine                                 │
│  └─ Database Persistence (SQLite/PostgreSQL)                │
├─────────────────────────────────────────────────────────────┤
│  Phase 2: Intelligence                                       │
│  ├─ Gemini-Powered Entity Extraction                        │
│  ├─ Multi-Dimensional Confidence Scoring                    │
│  ├─ Workflow Validation                                     │
│  └─ Conversation Quality Metrics                            │
├─────────────────────────────────────────────────────────────┤
│  Phase 3: Integration                                        │
│  ├─ Email (Gmail, Outlook)                                  │
│  ├─ Notifications (Slack, Email, SMS)                       │
│  ├─ Webhooks (Event-driven triggers)                        │
│  ├─ File Processing (CSV, JSON, Excel)                      │
│  └─ Database Connectors (PostgreSQL, MySQL, MongoDB)        │
├─────────────────────────────────────────────────────────────┤
│  Phase 4: Production                                         │
│  ├─ Workflow Execution Engine                               │
│  ├─ Scheduling System (Cron, Interval, One-time)           │
│  ├─ Monitoring & Analytics                                  │
│  └─ Error Tracking & Health Checks                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

- **Natural Language Workflow Building**: Describe workflows in plain English
- **Multi-turn Conversation**: Intelligent conversation management with context
- **11 Step Types**: Email, Notifications, Webhooks, Database, File Processing, and more
- **Flexible Scheduling**: Cron expressions, intervals, or one-time execution
- **Real-time Monitoring**: Track execution progress, metrics, and errors
- **Production-Ready**: Full error handling, retry logic, and persistence

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 16+ (for frontend)
- Git

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/Jai3405/AgentFlow.git
cd AgentFlow

# Run complete setup script
./complete_setup.sh
```

### 2. Configure Environment

```bash
# Copy environment template
cp backend/.env.example backend/.env

# Edit .env and add your Gemini API key
nano backend/.env
```

**Required**: Add your `GEMINI_API_KEY` (get from [Google AI Studio](https://makersuite.google.com/app/apikey))

### 3. Start Backend

```bash
# Option 1: Using startup script
./scripts/start_dev_gemini.sh

# Option 2: Manual start
cd backend
uvicorn main_gemini:app --reload --port 8000
```

### 4. Start Frontend

```bash
cd frontend
npm start
```

### 5. Access Application

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Base**: http://localhost:8000

---

## Detailed Installation

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv agentflow-env
source agentflow-env/bin/activate  # On Windows: agentflow-env\Scripts\activate

# Install dependencies
pip install -r requirements_gemini.txt

# Initialize database
python scripts/init_db.py

# Run migrations
alembic upgrade head
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Build for production (optional)
npm run build
```

### Database Options

**Development** (Default):
```bash
DATABASE_URL=sqlite:///./agentflow.db
```

**Production** (PostgreSQL):
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/agentflow
```

**Production** (MySQL):
```bash
DATABASE_URL=mysql://user:password@localhost:3306/agentflow
```

---

## Configuration

### Required API Keys

#### 1. Gemini API (Required)

Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

```env
GEMINI_API_KEY=your_actual_gemini_api_key_here
```

### Optional Integrations

#### 2. Gmail Integration

**Setup**:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Download credentials as `credentials.json`

```env
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

#### 3. Outlook Integration

**Setup**:
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register an application
3. Add Mail.Read and Mail.Send permissions
4. Create a client secret

```env
OUTLOOK_CLIENT_ID=your_client_id
OUTLOOK_CLIENT_SECRET=your_client_secret
OUTLOOK_TENANT_ID=your_tenant_id
```

#### 4. Slack Integration

**Setup**:
1. Go to [Slack API](https://api.slack.com/apps)
2. Create a new app
3. Add Bot Token Scopes: `chat:write`, `channels:read`, `files:write`
4. Install app to workspace

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token
```

#### 5. Twilio SMS

**Setup**:
1. Sign up at [Twilio](https://www.twilio.com/)
2. Get Account SID and Auth Token
3. Get a Twilio phone number

```env
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890
```

#### 6. SMTP Email Notifications

**Gmail Example**:
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_specific_password
SMTP_FROM_ADDRESS=your_email@gmail.com
```

---

## API Documentation

### Base URL
```
http://localhost:8000
```

### Interactive Documentation
```
http://localhost:8000/docs
```

### API Endpoints Summary

#### Conversation API (Phase 1)
- `POST /api/chat` - Send message and build workflow
- `GET /api/conversations/{id}` - Get conversation history
- `POST /api/workflows/generate/{id}` - Generate workflow from conversation

#### Integration API (Phase 3) - 17 Endpoints

**Email**:
- `POST /api/integrations/email/setup` - Setup Gmail/Outlook
- `POST /api/integrations/email/send` - Send email
- `POST /api/integrations/email/fetch` - Fetch emails

**Notifications**:
- `POST /api/integrations/notifications/setup` - Setup Slack/Email/SMS
- `POST /api/integrations/notifications/send` - Send notification
- `POST /api/integrations/notifications/alert` - Multi-channel alert

**Webhooks**:
- `POST /api/integrations/webhooks/setup` - Initialize webhook manager
- `POST /api/integrations/webhooks/register` - Register webhook
- `POST /api/integrations/webhooks/trigger` - Trigger webhook
- `GET /api/integrations/webhooks` - List webhooks
- `DELETE /api/integrations/webhooks/{id}` - Unregister webhook

**Management**:
- `GET /api/integrations/status` - List all integrations
- `GET /api/integrations/status/{name}` - Get integration status
- `POST /api/integrations/test/{name}` - Test connection
- `POST /api/integrations/disconnect/{name}` - Disconnect integration
- `POST /api/integrations/disconnect-all` - Disconnect all

#### Execution API (Phase 4) - 17 Endpoints

**Execution**:
- `POST /api/execution/execute` - Execute workflow
- `GET /api/execution/status/{id}` - Get execution status
- `GET /api/execution/active` - List active executions
- `POST /api/execution/cancel/{id}` - Cancel execution
- `POST /api/execution/pause/{id}` - Pause execution
- `POST /api/execution/resume/{id}` - Resume execution
- `POST /api/execution/validate` - Validate workflow spec

**Scheduling**:
- `POST /api/execution/schedule` - Schedule workflow
- `GET /api/execution/schedule` - List scheduled jobs
- `GET /api/execution/schedule/{id}` - Get job details
- `PUT /api/execution/schedule/{id}` - Update schedule
- `DELETE /api/execution/schedule/{id}` - Unschedule workflow
- `POST /api/execution/schedule/{id}/enable` - Enable job
- `POST /api/execution/schedule/{id}/disable` - Disable job
- `GET /api/execution/schedule/upcoming` - Upcoming executions
- `GET /api/execution/schedule/history` - Execution history
- `POST /api/execution/scheduler/start` - Start scheduler
- `POST /api/execution/scheduler/stop` - Stop scheduler

#### Monitoring API (Phase 4) - 8 Endpoints

- `GET /api/monitoring/metrics/{workflow_id}` - Workflow metrics
- `GET /api/monitoring/metrics` - Overall metrics
- `GET /api/monitoring/trends` - Execution trends
- `GET /api/monitoring/performance/{id}` - Step performance
- `GET /api/monitoring/errors` - Error analysis
- `GET /api/monitoring/summary/{id}` - Performance summary
- `DELETE /api/monitoring/history` - Clear history
- `GET /api/monitoring/health` - System health

**Total: 42 API Endpoints**

---

## Workflow Examples

### Example 1: Simple Email Workflow

```json
{
  "workflow_id": "email-demo",
  "workflow_spec": {
    "steps": [
      {
        "id": "send_email",
        "type": "email",
        "config": {
          "action": "send",
          "provider": "gmail",
          "to": ["recipient@example.com"],
          "subject": "Hello from AgentFlow",
          "body": "This is an automated email!"
        }
      }
    ]
  }
}
```

**Execute**:
```bash
curl -X POST http://localhost:8000/api/execution/execute \
  -H "Content-Type: application/json" \
  -d @workflow.json
```

### Example 2: Database to Email Workflow

```json
{
  "workflow_id": "db-to-email",
  "workflow_spec": {
    "steps": [
      {
        "id": "fetch_users",
        "type": "database_read",
        "config": {
          "database_type": "postgresql",
          "database_name": "mydb",
          "table": "users",
          "columns": ["name", "email"],
          "where": "active = true",
          "credentials": {
            "host": "localhost",
            "port": 5432,
            "database": "mydb",
            "user": "postgres",
            "password": "password"
          }
        }
      },
      {
        "id": "send_notification",
        "type": "notification",
        "config": {
          "channels": ["slack"],
          "message": "Found {{user_count}} active users",
          "recipients": {
            "slack": ["#general"]
          }
        }
      }
    ]
  }
}
```

### Example 3: Scheduled Report Workflow

```json
{
  "workflow_id": "daily-report",
  "workflow_spec": {
    "steps": [
      {
        "id": "read_csv",
        "type": "file_process",
        "config": {
          "file_type": "csv",
          "action": "read",
          "file_path": "/data/sales.csv"
        }
      },
      {
        "id": "transform",
        "type": "transform",
        "config": {
          "type": "aggregate",
          "input": "$read_csv",
          "operation": "sum",
          "field": "amount"
        }
      },
      {
        "id": "send_report",
        "type": "email",
        "config": {
          "action": "send",
          "provider": "gmail",
          "to": ["manager@company.com"],
          "subject": "Daily Sales Report",
          "body": "Total sales: ${{total_amount}}"
        }
      }
    ]
  },
  "schedule_type": "cron",
  "schedule_config": {
    "expression": "0 9 * * *"  // Every day at 9 AM
  }
}
```

**Schedule**:
```bash
curl -X POST http://localhost:8000/api/execution/schedule \
  -H "Content-Type: application/json" \
  -d @scheduled-workflow.json
```

### Example 4: Conditional Workflow

```json
{
  "workflow_id": "conditional-example",
  "workflow_spec": {
    "steps": [
      {
        "id": "fetch_data",
        "type": "database_read",
        "config": {
          "database_type": "mongodb",
          "collection": "orders",
          "query": {"status": "pending"}
        }
      },
      {
        "id": "check_count",
        "type": "condition",
        "config": {
          "condition": {
            "field": "count",
            "operator": "greater_than",
            "value": 10
          }
        },
        "branches": {
          "true": [
            {
              "id": "alert_high",
              "type": "notification",
              "config": {
                "channels": ["slack", "sms"],
                "message": "High pending orders: {{count}}",
                "priority": "urgent"
              }
            }
          ],
          "false": [
            {
              "id": "alert_normal",
              "type": "notification",
              "config": {
                "channels": ["email"],
                "message": "Normal pending orders: {{count}}"
              }
            }
          ]
        }
      }
    ]
  }
}
```

---

## Troubleshooting

### Common Issues

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'google.generativeai'`

**Solution**:
```bash
pip install -r requirements_gemini.txt
```

#### 2. Database Errors

**Problem**: `Table doesn't exist`

**Solution**:
```bash
python scripts/init_db.py
alembic upgrade head
```

#### 3. Gemini API Errors

**Problem**: `API key not valid`

**Solution**:
- Check your `.env` file has the correct `GEMINI_API_KEY`
- Verify key is valid at [Google AI Studio](https://makersuite.google.com/)

#### 4. Integration Errors

**Problem**: `Integration not configured`

**Solution**:
```bash
# Setup integration first
curl -X POST http://localhost:8000/api/integrations/email/setup \
  -H "Content-Type: application/json" \
  -d '{
    "integration_type": "gmail",
    "credentials": {
      "token_file": "token.json",
      "credentials_file": "credentials.json"
    }
  }'
```

#### 5. Port Already in Use

**Problem**: `Address already in use`

**Solution**:
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn main_gemini:app --reload --port 8001
```

### Debug Mode

Enable detailed logging:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

View logs:
```bash
tail -f agentflow.log
```

---

## Testing

### Run Tests

```bash
cd backend
pytest

cd frontend
npm test
```

### Manual API Testing

Use the interactive docs at http://localhost:8000/docs

Or use curl:

```bash
# Test conversation
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to automate email responses", "conversation_id": null}'

# Test workflow execution
curl -X POST http://localhost:8000/api/execution/execute \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "test", "workflow_spec": {...}}'

# Test monitoring
curl http://localhost:8000/api/monitoring/health
```

---

## Production Deployment

### 1. Update Environment

```env
DEBUG=False
DATABASE_URL=postgresql://user:pass@prod-db:5432/agentflow
SECRET_KEY=<generate-strong-key>
```

### 2. Use Production Server

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn main_gemini:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### 3. Setup Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Enable HTTPS

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com
```

---

## Support

- **Documentation**: See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) and [PHASE_3_SUMMARY.md](PHASE_3_SUMMARY.md)
- **Issues**: https://github.com/Jai3405/AgentFlow/issues
- **API Docs**: http://localhost:8000/docs

---

## License

MIT License - See LICENSE file for details
