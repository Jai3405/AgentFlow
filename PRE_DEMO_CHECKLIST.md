# Pre-Demo Checklist - What YOU Need to Do

## ✅ **Already Done (You're Secure!)**
- ✅ `.env` files are properly ignored by git
- ✅ No secrets will be pushed to GitHub
- ✅ All code is ready and tested

---

## 🔑 **Add API Keys (Choose Your Level)**

### **Level 1: Basic Demo (0 minutes) - Current State ✅**
**You're good to go!** System works as-is with mock responses.

### **Level 2: Smart AI Demo (5 minutes) - Recommended** ⭐

**Get Free Gemini API Key:**
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIza...`)
5. Edit `backend/.env` line 2:
   ```bash
   GEMINI_API_KEY=AIzaSyYourActualKeyHere
   ```
6. Restart backend - Now conversations will be MUCH smarter!

### **Level 3: Live Integrations (Optional - 30+ min)**
Only if you want to demo real Slack/Email:

**Slack Bot Token:**
```bash
# In backend/.env, add:
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_SIGNING_SECRET=your-secret
```

**Gmail (Complex - Skip for demo):**
Requires OAuth2 setup - not recommended unless you have time.

---

## 📝 **Before You Commit & Push**

### **1. Review what you're committing:**
```bash
cd /Users/jay/Documents/AgentFlow
git status
git diff
```

### **2. Make sure .env is NOT in the list:**
```bash
git status | grep .env
# Should show NOTHING (empty output = good!)
```

### **3. Safe to commit these new files:**
```bash
git add .
git commit -m "Phase 5: Add execution dashboards and demo documentation

- Added ExecutionDashboard for real-time workflow monitoring
- Added AnalyticsDashboard for system metrics
- Added SchedulerUI for job management
- Updated App.tsx with navigation system
- Fixed database schema issues
- Added comprehensive demo guides"

git push origin phase-3-integration
```

---

## 🎬 **Demo Day Morning**

### **30 Minutes Before:**
```bash
cd /Users/jay/Documents/AgentFlow

# Option A: Automated start
./quick_start_demo.sh

# Option B: Manual (if script doesn't work)
# Terminal 1:
cd backend && python3 -m uvicorn main_gemini:app --reload --port 8000

# Terminal 2 (new terminal):
cd frontend && npm start
```

### **Verify Everything Works:**
1. Open http://localhost:3000
2. Click through all 4 tabs (Builder, Executions, Analytics, Scheduler)
3. Type test message in Builder tab
4. Check that http://localhost:8000/docs loads

---

## 🎯 **Quick Reference During Demo**

### **URLs:**
- **Frontend:** http://localhost:3000
- **API Docs:** http://localhost:8000/docs

### **Demo Flow:**
1. **Builder** - Type: *"I need to automate customer support emails"*
2. **Executions** - Show real-time monitoring
3. **Analytics** - Show system metrics
4. **Scheduler** - Show scheduling capabilities
5. **API Docs** - Show 45+ endpoints

### **Key Stats to Mention:**
- 13,000+ lines of code
- 45+ REST API endpoints
- 4 complete phases
- 11 integration types
- Full-stack: React + FastAPI + Database

---

## 🚨 **Troubleshooting**

### **If backend won't start:**
```bash
cd backend
pip3 install -r requirements_gemini.txt
python3 scripts/init_db.py
```

### **If frontend won't start:**
```bash
cd frontend
npm install
```

### **If ports are busy:**
```bash
# Kill backend
lsof -ti:8000 | xargs kill -9

# Kill frontend
lsof -ti:3000 | xargs kill -9
```

---

## ✅ **You're Ready When:**
- [ ] Backend starts without errors
- [ ] Frontend opens at localhost:3000
- [ ] All 4 tabs are visible and clickable
- [ ] Chat interface accepts input
- [ ] Git status shows .env is ignored

**Good luck! 🚀**
