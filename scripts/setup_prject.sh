#!/bin/bash
# AgentFlow Project Setup Script

# Create main project directory
mkdir agentflow
cd agentflow

# Backend structure
mkdir backend
cd backend
mkdir -p {api,core,models,services,utils,tests}
cd ..

# Frontend structure  
mkdir frontend
cd frontend
mkdir -p {src/{components,pages,hooks,utils,types},public}
cd ..

# Documentation and config
mkdir -p {docs,config,scripts}

# Initialize backend (Python)
cd backend
python -m venv agentflow-env
source agentflow-env/bin/activate  # On Windows: agentflow-env\Scripts\activate

# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn==0.24.0
langgraph==0.0.40
langchain==0.1.0
openai==1.3.0
pydantic==2.5.0
sqlalchemy==2.0.23
alembic==1.12.1
python-multipart==0.0.6
python-dotenv==1.0.0
pytest==7.4.3
httpx==0.25.2
EOF

pip install -r requirements.txt

# Initialize frontend (React + TypeScript)
cd ../frontend
npx create-react-app . --template typescript
npm install axios tailwindcss @types/react @types/react-dom

# Initialize git repository
cd ..
git init
echo "node_modules/
__pycache__/
*.pyc
.env
.venv/
agentflow-env/
build/
dist/" > .gitignore