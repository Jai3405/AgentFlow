#!/bin/bash
# Complete AgentFlow Setup Script
# Run this in your cloned repository directory

set -e

echo "🚀 Setting up AgentFlow project structure..."

# Create directory structure
echo "📁 Creating directories..."
mkdir -p backend/{api,core,models,services,utils,tests}
mkdir -p frontend/src/{components,pages,hooks,utils,types}
mkdir -p frontend/public
mkdir -p {docs,config,scripts}

# Backend setup
echo "🐍 Setting up backend..."
cd backend

# Create requirements.txt
cat > requirements.txt << 'EOF'
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

# Create .env.example
cat > .env.example << 'EOF'
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=sqlite:///./agentflow.db
SECRET_KEY=your_secret_key_here
CORS_ORIGINS=["http://localhost:3000"]
EOF

# Create Python __init__.py files
touch api/__init__.py core/__init__.py models/__init__.py services/__init__.py utils/__init__.py tests/__init__.py

# Create main.py
cat > main.py << 'EOF'
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from core.conversation_manager import ConversationManager
from core.workflow_generator import WorkflowGenerator
from models.conversation import ConversationState, Message

app = FastAPI(title="AgentFlow API", version="1.0.0")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
conversation_manager = ConversationManager()
workflow_generator = WorkflowGenerator()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    workflow_progress: float
    next_questions: Optional[List[str]] = None
    workflow_preview: Optional[Dict] = None

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main conversation endpoint"""
    try:
        # Get or create conversation
        conv_id = request.conversation_id or str(uuid.uuid4())
        
        # Process the message
        response_data = await conversation_manager.process_message(
            conv_id, request.message
        )
        
        return ChatResponse(
            response=response_data["response"],
            conversation_id=conv_id,
            workflow_progress=response_data["progress"],
            next_questions=response_data.get("next_questions"),
            workflow_preview=response_data.get("workflow_preview")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    try:
        conversation = await conversation_manager.get_conversation(conversation_id)
        return conversation.dict()
    except Exception as e:
        raise HTTPException(status_code=404, detail="Conversation not found")

@app.post("/api/workflows/generate/{conversation_id}")
async def generate_workflow(conversation_id: str):
    """Generate workflow from conversation"""
    try:
        workflow = await workflow_generator.generate_from_conversation(conversation_id)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

# Create models/conversation.py
cat > models/conversation.py << 'EOF'
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

class WorkflowType(str, Enum):
    EMAIL_PROCESSING = "email_processing"
    DATA_PIPELINE = "data_pipeline"
    APPROVAL_WORKFLOW = "approval_workflow"
    NOTIFICATION_SYSTEM = "notification_system"

class ConversationState(BaseModel):
    conversation_id: Optional[str] = None
    messages: List[Message] = []
    workflow_type: Optional[WorkflowType] = None
    entities: Dict[str, Any] = {}
    requirements: Dict[str, Any] = {}
    progress: float = 0.0
    confidence_score: float = 0.0
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    
    def add_message(self, message: Message):
        """Add a message to the conversation"""
        self.messages.append(message)
        self.updated_at = datetime.now()
    
    def get_user_messages(self) -> List[Message]:
        """Get only user messages"""
        return [msg for msg in self.messages if msg.role == MessageRole.USER]
    
    def get_latest_context(self, num_messages: int = 10) -> List[Message]:
        """Get recent conversation context"""
        return self.messages[-num_messages:]
EOF

# Create core/conversation_manager.py
cat > core/conversation_manager.py << 'EOF'
import json
from typing import Dict, List, Optional
from langchain.llms import OpenAI
from langgraph.graph import StateGraph, END
from models.conversation import ConversationState, Message
from services.intent_classifier import IntentClassifier
from services.entity_extractor import EntityExtractor
from datetime import datetime

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, ConversationState] = {}
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()
        # For now, create a simple response without LLM
        # self.llm = OpenAI(temperature=0.7)
    
    async def process_message(self, conversation_id: str, message: str) -> Dict:
        """Process a user message and return response"""
        
        # Get or create conversation state
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = ConversationState()
        
        state = self.conversations[conversation_id]
        
        # Add user message
        from models.conversation import Message, MessageRole
        state.add_message(Message(
            role=MessageRole.USER,
            content=message,
            timestamp=datetime.now()
        ))
        
        # Simple response generation for now
        intent = await self.intent_classifier.classify(message)
        entities = await self.entity_extractor.extract(message)
        
        # Update state
        state.entities.update(entities)
        
        # Calculate progress
        required_info = ["email_addresses", "team_mentions", "urgency_indicators"]
        gathered_info = [key for key in required_info if key in entities]
        progress = len(gathered_info) / len(required_info) if required_info else 0.0
        
        # Generate response based on intent
        if intent == "email_automation":
            response = f"I understand you want to automate email processes. I can see you mentioned: {', '.join(entities.get('email_addresses', []))}. Let me help you build an email processing workflow. What specific actions do you want to take with these emails?"
        elif intent == "data_processing":
            response = "I can help you build a data processing workflow. What kind of data are you working with and what do you want to do with it?"
        else:
            response = "I'd be happy to help you build an automation workflow! Can you tell me more about what business process you'd like to automate?"
        
        return {
            "response": response,
            "progress": progress,
            "next_questions": self._generate_questions(intent),
            "workflow_preview": self._generate_preview(intent) if progress > 0.3 else None
        }
    
    async def get_conversation(self, conversation_id: str):
        """Get conversation by ID"""
        return self.conversations.get(conversation_id)
    
    def _generate_questions(self, intent: str) -> List[str]:
        """Generate follow-up questions based on intent"""
        questions = {
            "email_automation": [
                "What email address should I monitor?",
                "How do you want to categorize the emails?",
                "Which team members should receive different types of emails?"
            ],
            "data_processing": [
                "What format is your data in (CSV, JSON, database)?",
                "What processing steps do you need?",
                "Where should the processed data be sent?"
            ]
        }
        return questions.get(intent, ["What would you like to automate?"])
    
    def _generate_preview(self, intent: str) -> Dict:
        """Generate a simple workflow preview"""
        if intent == "email_automation":
            return {
                "steps": [
                    {"id": "monitor", "type": "email", "name": "Email Monitor", "description": "Monitor incoming emails"},
                    {"id": "classify", "type": "process", "name": "Classify", "description": "Categorize emails by type"},
                    {"id": "route", "type": "decision", "name": "Route", "description": "Send to appropriate team"}
                ]
            }
        return {"steps": []}
EOF

# Create core/workflow_generator.py
cat > core/workflow_generator.py << 'EOF'
from typing import Dict, List
import json

class WorkflowGenerator:
    def __init__(self):
        self.workflow_templates = {
            "email_processing": {
                "steps": [
                    {"id": "email_monitor", "type": "email", "name": "Email Monitor"},
                    {"id": "classifier", "type": "process", "name": "Smart Classifier"},
                    {"id": "router", "type": "decision", "name": "Auto Router"},
                    {"id": "notify", "type": "notification", "name": "Send Notifications"}
                ]
            }
        }
    
    async def generate_from_conversation(self, conversation_id: str) -> Dict:
        """Generate workflow from conversation state"""
        workflow = {
            "id": f"workflow_{conversation_id}",
            "name": "Email Processing Workflow",
            "steps": [
                {
                    "id": "email_monitor",
                    "type": "email",
                    "name": "Email Monitor",
                    "description": "Monitor incoming emails from support@company.com",
                    "config": {
                        "email_source": "support@company.com",
                        "check_interval": "1min"
                    }
                },
                {
                    "id": "classifier",
                    "type": "process",
                    "name": "Smart Classifier",
                    "description": "Analyze email content for urgency and category",
                    "config": {
                        "categories": ["technical", "billing", "general"],
                        "urgency_keywords": ["urgent", "critical", "down", "not working"]
                    }
                }
            ],
            "connections": [
                {"from": "email_monitor", "to": "classifier"}
            ],
            "metadata": {
                "created_from_conversation": conversation_id,
                "estimated_setup_time": "15 minutes",
                "complexity": "medium"
            }
        }
        
        return workflow
EOF

# Create services files
cat > services/intent_classifier.py << 'EOF'
from typing import Dict
import re

class IntentClassifier:
    def __init__(self):
        self.intent_patterns = {
            "email_automation": [
                r"email", r"inbox", r"support", r"customer service",
                r"routing", r"sorting", r"filtering"
            ],
            "data_processing": [
                r"data", r"csv", r"excel", r"database", r"report",
                r"process", r"transform", r"clean"
            ],
            "approval_workflow": [
                r"approval", r"review", r"authorize", r"sign off",
                r"permission", r"request", r"escalate"
            ],
            "notification_system": [
                r"notify", r"alert", r"remind", r"message",
                r"update", r"inform", r"send"
            ]
        }
    
    async def classify(self, text: str) -> str:
        """Classify user intent from text"""
        text_lower = text.lower()
        
        scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = sum(1 for pattern in patterns if re.search(pattern, text_lower))
            scores[intent] = score
        
        # Return intent with highest score, or 'general' if no matches
        if max(scores.values()) > 0:
            return max(scores.keys(), key=scores.get)
        return "general"
EOF

cat > services/entity_extractor.py << 'EOF'
from typing import Dict, List
import re

class EntityExtractor:
    def __init__(self):
        self.entity_patterns = {
            "email_addresses": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "file_types": r'\b(csv|excel|pdf|json|xml)\b',
            "time_expressions": r'\b(daily|weekly|monthly|hourly|every \d+|at \d+)\b',
            "team_mentions": r'\b(team|department|group|support|sales|technical|billing)\b',
            "urgency_indicators": r'\b(urgent|critical|asap|immediately|priority)\b'
        }
    
    async def extract(self, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        entities = {}
        text_lower = text.lower()
        
        for entity_type, pattern in self.entity_patterns.items():
            matches = re.findall(pattern, text_lower)
            if matches:
                entities[entity_type] = matches
        
        return entities
EOF

# Move to frontend directory
cd ../frontend

echo "⚛️ Setting up frontend..."

# Create package.json for React TypeScript
cat > package.json << 'EOF'
{
  "name": "agentflow-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "@types/jest": "^27.5.2",
    "@types/node": "^16.11.47",
    "@types/react": "^18.0.15",
    "@types/react-dom": "^18.0.6",
    "axios": "^1.6.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "tailwindcss": "^3.3.0",
    "typescript": "^4.7.4",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOF

# Create types
cat > src/types/index.ts << 'EOF'
export interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  workflow_progress: number;
  next_questions?: string[];
  workflow_preview?: WorkflowPreview;
}

export interface WorkflowPreview {
  steps: WorkflowStep[];
  connections?: WorkflowConnection[];
}

export interface WorkflowStep {
  id: string;
  type: string;
  name: string;
  description: string;
}

export interface WorkflowConnection {
  from: string;
  to: string;
  condition?: string;
}
EOF

# Create components
cat > src/components/ChatInterface.tsx << 'EOF'
import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Message, ChatResponse } from '../types';

interface ChatInterfaceProps {
  onWorkflowUpdate?: (workflow: any) => void;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ onWorkflowUpdate }) => {
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hi! I'm AgentFlow, your AI workflow builder. I can help you create automation workflows just by talking to me. What business process would you like to automate?",
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [workflowProgress, setWorkflowProgress] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await axios.post<ChatResponse>('http://localhost:8000/api/chat', {
        message: inputValue,
        conversation_id: conversationId
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setConversationId(response.data.conversation_id);
      setWorkflowProgress(response.data.workflow_progress);

      if (response.data.workflow_preview && onWorkflowUpdate) {
        onWorkflowUpdate(response.data.workflow_preview);
      }
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="flex flex-col h-full bg-white rounded-lg shadow-lg">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-600 to-blue-600 text-white p-4 rounded-t-lg">
        <h2 className="text-xl font-bold">AgentFlow Assistant</h2>
        <div className="flex items-center mt-2">
          <div className="bg-white bg-opacity-20 rounded-full px-3 py-1 text-sm">
            Workflow Progress: {Math.round(workflowProgress * 100)}%
          </div>
          {workflowProgress > 0 && (
            <div className="ml-2 bg-white bg-opacity-20 rounded-full h-2 w-32">
              <div 
                className="bg-white h-2 rounded-full transition-all duration-300"
                style={{ width: `${workflowProgress * 100}%` }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-800'
              }`}
            >
              <p className="whitespace-pre-wrap">{message.content}</p>
              <p className="text-xs mt-1 opacity-70">
                {new Date(message.timestamp).toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-800 px-4 py-2 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex space-x-2">
          <textarea
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe the workflow you want to create..."
            className="flex-1 resize-none border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={isLoading || !inputValue.trim()}
            className="bg-blue-600 text-white px-6 py-2 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
EOF

cat > src/components/WorkflowVisualization.tsx << 'EOF'
import React from 'react';
import { WorkflowPreview, WorkflowStep } from '../types';

interface WorkflowVisualizationProps {
  workflow?: WorkflowPreview;
}

const WorkflowVisualization: React.FC<WorkflowVisualizationProps> = ({ workflow }) => {
  if (!workflow || !workflow.steps.length) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6 h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="w-16 h-16 mx-auto mb-4 bg-gray-200 rounded-full flex items-center justify-center">
            <svg className="w-8 h-8" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4 2a2 2 0 00-2 2v11a2 2 0 002 2h12a2 2 0 002-2V4a2 2 0 00-2-2H4zm3 5a1 1 0 000 2h6a1 1 0 100-2H7zm0 4a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
            </svg>
          </div>
          <p>Start describing your workflow to see it built in real-time</p>
        </div>
      </div>
    );
  }

  const getStepIcon = (type: string) => {
    const icons = {
      email: "📧",
      data: "📊",
      process: "⚙️",
      notification: "🔔",
      decision: "🤔",
      action: "▶️"
    };
    return icons[type as keyof typeof icons] || "⚡";
  };

  const getStepColor = (type: string) => {
    const colors = {
      email: "bg-blue-100 border-blue-300",
      data: "bg-green-100 border-green-300",
      process: "bg-yellow-100 border-yellow-300",
      notification: "bg-purple-100 border-purple-300",
      decision: "bg-orange-100 border-orange-300",
      action: "bg-red-100 border-red-300"
    };
    return colors[type as keyof typeof colors] || "bg-gray-100 border-gray-300";
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 h-full">
      <h3 className="text-lg font-semibold mb-4">Workflow Preview</h3>
      
      <div className="space-y-4">
        {workflow.steps.map((step, index) => (
          <div key={step.id} className="flex items-start space-x-4">
            {/* Step Number */}
            <div className="flex-shrink-0 w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
              {index + 1}
            </div>
            
            {/* Step Content */}
            <div className={`flex-1 p-4 rounded-lg border-2 ${getStepColor(step.type)}`}>
              <div className="flex items-center space-x-2 mb-2">
                <span className="text-xl">{getStepIcon(step.type)}</span>
                <h4 className="font-medium text-gray-800">{step.name}</h4>
              </div>
              <p className="text-sm text-gray-600">{step.description}</p>
            </div>
            
            {/* Arrow */}
            {index < workflow.steps.length - 1 && (
              <div className="flex-shrink-0 pt-6">
                <svg className="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10.293 3.293a1 1 0 011.414 0l6 6a1 1 0 010 1.414l-6 6a1 1 0 01-1.414-1.414L14.586 11H3a1 1 0 110-2h11.586l-4.293-4.293a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default WorkflowVisualization;
EOF

# Update src/App.tsx
cat > src/App.tsx << 'EOF'
import React, { useState } from 'react';
import ChatInterface from './components/ChatInterface';
import WorkflowVisualization from './components/WorkflowVisualization';
import { WorkflowPreview } from './types';

function App() {
  const [currentWorkflow, setCurrentWorkflow] = useState<WorkflowPreview | undefined>();

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-600 via-blue-600 to-blue-800 p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">AgentFlow</h1>
          <p className="text-blue-100 text-lg">Build Agents by Talking to One</p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-96 lg:h-[600px]">
          {/* Chat Interface */}
          <div>
            <ChatInterface onWorkflowUpdate={setCurrentWorkflow} />
          </div>

          {/* Workflow Visualization */}
          <div>
            <WorkflowVisualization workflow={currentWorkflow} />
          </div>
        </div>

        {/* Footer */}
        <div className="text-center mt-8 text-blue-100">
          <p>Describe your automation needs and watch your workflow come to life</p>
        </div>
      </div>
    </div>
  );
}

export default App;
EOF

# Create public/index.html
cat > public/index.html << 