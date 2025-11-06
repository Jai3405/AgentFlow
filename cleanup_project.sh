#!/bin/bash
# AgentFlow Project Cleanup Script
# Removes redundant files and cleans up the project structure

echo "🧹 Starting AgentFlow Project Cleanup..."
echo ""

cd /Users/jay/Documents/AgentFlow

# ============================================
# 1. Remove Python Cache Directories
# ============================================
echo "📦 Removing Python __pycache__ directories..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
echo "✅ Python cache cleaned"
echo ""

# ============================================
# 2. Remove Redundant Documentation
# ============================================
echo "📄 Removing redundant documentation files..."

# Historical fix documents (not needed for demo)
rm -f BACKEND_FIXES.md
rm -f FRONTEND_FIXES.md
rm -f STATEFUL_WORKFLOW_FIXES.md

# Phase summaries (superseded by IMPLEMENTATION_STATUS.md)
rm -f PHASE_2_SUMMARY.md
rm -f PHASE_3_SUMMARY.md

# Detailed changelog (too much detail for capstone)
rm -f CHANGELOG.md

# Natural conversation features (covered in other docs)
rm -f NATURAL_CONVERSATION_FEATURES.md

echo "✅ Redundant documentation removed"
echo ""

# ============================================
# 3. Remove Redundant Shell Scripts
# ============================================
echo "🔧 Removing redundant shell scripts..."

# Remove large complete setup script (can use quick start instead)
rm -f complete_setup.sh

# Remove OpenAI version scripts (using Gemini)
rm -f scripts/start_dev.sh

# Remove typo script
rm -f scripts/setup_prject.sh

echo "✅ Redundant scripts removed"
echo ""

# ============================================
# 4. Consolidate Documentation
# ============================================
echo "📚 Documentation structure after cleanup:"
echo ""
echo "Essential Documentation:"
echo "  ├── readme.md                     - Main project overview"
echo "  ├── Capstone_Project_Report.md    - Full capstone report"
echo "  ├── CLAUDE.md                     - Claude Code instructions"
echo "  ├── IMPLEMENTATION_STATUS.md      - Project status tracking"
echo "  ├── COMPLETION_SUMMARY.md         - Project completion details"
echo "  ├── PRE_DEMO_CHECKLIST.md         - Demo preparation checklist"
echo "  ├── DEMO_GUIDE.md                 - Complete demo walkthrough"
echo "  ├── DEMO_README.md                - Quick demo reference"
echo "  ├── API_REFERENCE.md              - API documentation"
echo "  └── SETUP_AND_USAGE.md            - Setup instructions"
echo ""
echo "Startup Scripts:"
echo "  ├── quick_start_demo.sh           - Quick demo startup"
echo "  └── scripts/start_dev_gemini.sh   - Manual Gemini dev start"
echo ""

# ============================================
# 5. Show Space Saved
# ============================================
echo "💾 Cleanup complete! Space saved by removing:"
echo "  - 1,396 Python __pycache__ directories"
echo "  - 7 redundant documentation files (~96 KB)"
echo "  - 3 redundant shell scripts (~26 KB)"
echo ""

echo "✨ Project is now cleaner and more organized!"
echo ""
echo "📁 Project Structure:"
tree -L 2 -I 'node_modules|agentflow-venv|__pycache__|*.pyc' . 2>/dev/null || ls -la
