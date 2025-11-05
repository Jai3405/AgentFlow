from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
import uuid
from datetime import datetime

from core.conversation_manager_gemini import ConversationManagerGemini
from core.workflow_generator import WorkflowGenerator
from models.conversation import ConversationState, Message
from database.base import Base, engine
from api.integrations import router as integrations_router

app = FastAPI(title="AgentFlow API (Gemini)", version="1.0.0")

# Include integration router
app.include_router(integrations_router)

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully")

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
conversation_manager = ConversationManagerGemini()
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
    """Main conversation endpoint using Gemini API"""
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