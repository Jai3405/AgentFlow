# AgentFlow - Demo Ready! 🚀

## Quick Start (30 seconds)

```bash
cd /Users/jay/Documents/AgentFlow
./quick_start_demo.sh
```

This will automatically:
- ✅ Check all dependencies
- ✅ Initialize database if needed
- ✅ Open two terminals (backend + frontend)
- ✅ Start both servers

**Then open:** http://localhost:3000

---

## Manual Start (If needed)

### Terminal 1 - Backend
```bash
cd backend
python3 -m uvicorn main_gemini:app --reload --port 8000
```

### Terminal 2 - Frontend
```bash
cd frontend
npm start
```

---

## Access Points

- **Frontend UI:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs

---

## Demo Features

### 1. Workflow Builder Tab
- Build workflows conversationally
- Real-time visualization
- Natural language processing

### 2. Executions Tab
- Monitor live workflow execution
- Control running workflows (pause/resume/cancel)
- View execution progress and logs

### 3. Analytics Tab
- System performance metrics
- Success rates and trends
- System health monitoring

### 4. Scheduler Tab
- Manage scheduled workflows
- Cron, interval, and one-time schedules
- Execution history and stats

---

## Demo Scenarios

### Scenario 1: Email Automation
```
Type in chat:
"I need to automate customer support email handling. Monitor support@company.com,
categorize emails as technical or billing, and route to appropriate teams."
```

### Scenario 2: Data Processing
```
Type in chat:
"Process CSV sales data daily at 9 AM. Read from data folder, validate the data,
insert into database, and email summary report to management."
```

### Scenario 3: Notification System
```
Type in chat:
"Create a notification workflow that monitors our database for high-priority alerts
and sends Slack messages to #alerts channel immediately."
```

---

## API Examples (For Demo)

### Execute a Workflow
```bash
curl -X POST "http://localhost:8000/api/execution/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "demo-workflow-001",
    "workflow_spec": {
      "name": "Email Processing Demo",
      "steps": [
        {"id": "step_1", "type": "email", "config": {"action": "fetch"}},
        {"id": "step_2", "type": "notification", "config": {"channel": "slack"}}
      ]
    }
  }'
```

### Get Active Executions
```bash
curl http://localhost:8000/api/execution/active
```

### Get Analytics
```bash
curl http://localhost:8000/api/monitoring/metrics
```

### Schedule a Workflow
```bash
curl -X POST "http://localhost:8000/api/execution/schedule" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "daily-report",
    "schedule_type": "cron",
    "schedule": "0 9 * * *",
    "workflow_spec": {"name": "Daily Report", "steps": []}
  }'
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill backend (port 8000)
lsof -ti:8000 | xargs kill -9

# Kill frontend (port 3000)
lsof -ti:3000 | xargs kill -9
```

### Database Issues
```bash
cd backend
rm agentflow.db
python3 scripts/init_db.py
```

### Backend Won't Start
```bash
cd backend
pip3 install -r requirements_gemini.txt
```

### Frontend Won't Start
```bash
cd frontend
rm -rf node_modules
npm install
```

---

## Project Statistics

- **Lines of Code:** 13,000+
- **API Endpoints:** 45+
- **Database Tables:** 9
- **Integration Types:** 11
- **Frontend Components:** 8
- **Step Types:** 11
- **Completion:** 100% ✅

---

## Key Documents

- **[DEMO_GUIDE.md](DEMO_GUIDE.md)** - Complete demo script (20 min)
- **[COMPLETION_SUMMARY.md](COMPLETION_SUMMARY.md)** - What was built
- **[IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)** - Technical details
- **[README.md](readme.md)** - Project overview

---

## Demo Tips

1. **Start with the problem** - Make it relatable
2. **Show the builder first** - Most impressive feature
3. **Navigate to each tab** - Show completeness
4. **Explain the architecture** - Show technical depth
5. **Open API docs** - Show professionalism
6. **Have backup scenarios** - In case one fails

---

## Presentation Flow (15-20 min)

1. Introduction (2 min)
2. Workflow Builder Demo (5 min)
3. Execution Dashboard (3 min)
4. Analytics Dashboard (3 min)
5. Scheduler (3 min)
6. Architecture Overview (2 min)
7. Q&A (2-5 min)

---

## Success! ✅

Your capstone project is:
- ✅ Fully functional
- ✅ Demo ready
- ✅ Well documented
- ✅ Production quality
- ✅ Impressive in scope

**Good luck with your presentation! 🎓**

---

For detailed demo script, see: **[DEMO_GUIDE.md](DEMO_GUIDE.md)**
