# AgentFlow
**Build Agents by Talking to One**

A revolutionary no-code platform that transforms conversational descriptions into production-ready AI agent workflows. Simply describe what you need in plain English, and AgentFlow builds the automation for you.

## The Problem

90% of AI agent pilots fail to reach production due to:
- **Complexity barriers** preventing business users from translating domain knowledge into functional AI solutions
- **Technical gaps** between proof-of-concept development and production deployment  
- **Manual optimization** requirements creating ongoing maintenance burdens
- **Limited visibility** into AI decision-making processes hindering debugging and trust

Organizations understand their business problems but lack technical resources to implement AI solutions. Technical teams can build AI systems but may miss crucial business context.

## The Solution

AgentFlow eliminates visual programming interfaces in favor of natural language conversation. Users describe what they need, and the system automatically generates complete, production-ready AI agent workflows.

### Core Innovation
- **Conversational Compilation**: Transform plain English into executable workflows
- **Intelligent Auto-Generation**: Create enterprise-grade systems with proper error handling and monitoring
- **Self-Optimization**: Continuous improvement using genetic programming algorithms  
- **Decision Transparency**: Real-time visibility into agent reasoning and actions

## How It Works

### 1. Natural Conversation
```
You: "Monitor customer support emails, identify urgent issues, route to appropriate teams."

AgentFlow: "I'll create a workflow with email monitoring, urgency detection, and intelligent routing. 
Should I add manager notifications for critical issues?"
```

### 2. Real-Time Workflow Building
As you talk, AgentFlow:
- Extracts business entities and requirements
- Maps them to technical components  
- Constructs workflow graphs with proper dependencies
- Generates production-ready code with error handling

### 3. Live Visualization
Watch your workflow being built in real-time with:
- Step-by-step process breakdown
- Visual component connections
- Progress indicators
- Confidence scoring

## Features

### For Business Users
- **Zero Learning Curve** - Describe needs in conversational English
- **Intelligent Questions** - System asks smart follow-ups to understand requirements
- **Real-Time Feedback** - See workflows being built and tested live
- **Complete Transparency** - Understand why agents make specific decisions

### For Technical Teams  
- **Production-Ready Output** - Enterprise-grade code with monitoring and error handling
- **Automatic Optimization** - Continuous performance improvement without manual tuning
- **Full Observability** - Complete visibility into system performance and behavior
- **Standards Compliance** - Built-in security, monitoring, and integration best practices

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+  
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Jai3405/AgentFlow.git
   cd AgentFlow
   ```

2. **Set up the backend**
   ```bash
   cd backend
   python -m venv agentflow-env
   source agentflow-env/bin/activate  # Windows: agentflow-env\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure environment**
   ```bash
   cd backend
   cp .env.example .env
   # Add your OpenAI API key to .env
   ```

5. **Start development servers**
   ```bash
   # Backend (from backend directory)
   uvicorn main:app --reload --port 8000
   
   # Frontend (from frontend directory)  
   npm start
   ```

6. **Open http://localhost:3000**

## Usage Examples

### Email Automation
```
User: "We get hundreds of support emails that need manual sorting"

AgentFlow: "I can automate that! I'll create an Email Processing Workflow that:
- Monitors your support inbox continuously
- Uses AI to categorize emails (technical, billing, general)  
- Routes to appropriate teams automatically
- Sends notifications with context and priority

What email address should I monitor?"
```

### Data Processing Pipeline
```
User: "I need to process CSV files and generate reports weekly"

AgentFlow: "Perfect! I'll build a Data Processing Workflow:
- Monitors for new CSV uploads
- Validates and cleans the data
- Generates summary reports
- Emails results to stakeholders

Where do the CSV files come from - email attachments, file uploads, or cloud storage?"
```

## Architecture

### Backend
- **FastAPI** - Modern Python web framework
- **LangGraph** - Conversation state management and workflow orchestration
- **OpenAI GPT-4** - Natural language understanding and intent classification  
- **SQLAlchemy** - Database ORM for conversation and workflow persistence
- **Pydantic** - Data validation and serialization

### Frontend
- **React 18** - Component-based UI framework
- **TypeScript** - Type safety and enhanced developer experience
- **Tailwind CSS** - Utility-first styling framework
- **Axios** - HTTP client for API communication

### Key Components

```
AgentFlow/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   ├── conversation_manager.py    # Handles multi-turn conversations
│   │   └── workflow_generator.py      # Converts conversations to workflows
│   ├── models/
│   │   └── conversation.py            # Data models for conversations and workflows
│   └── services/
│       ├── intent_classifier.py      # Classifies user intentions
│       └── entity_extractor.py       # Extracts business entities from text
└── frontend/
    └── src/
        ├── components/
        │   ├── ChatInterface.tsx         # Main conversation interface
        │   └── WorkflowVisualization.tsx # Real-time workflow display
        └── types/index.ts                # TypeScript definitions
```

## Development Roadmap

### Phase 1: Foundation (Weeks 1-2)
- [x] Conversational interface with basic intent recognition
- [x] Workflow visualization and progress tracking  
- [ ] Advanced entity extraction and question generation
- [ ] Conversation state persistence

### Phase 2: Intelligence (Weeks 3-4)
- [ ] Enhanced LLM integration for nuanced conversations
- [ ] Dynamic workflow template selection
- [ ] Confidence scoring and validation
- [ ] Multi-turn conversation optimization

### Phase 3: Integration (Weeks 5-6)
- [ ] Email API integration (Gmail, Outlook)
- [ ] Webhook system for real-time triggers
- [ ] Database connectors and data processing
- [ ] Notification systems (Slack, email, SMS)

### Phase 4: Production (Weeks 7-8)
- [ ] Workflow execution engine
- [ ] Monitoring and analytics dashboard
- [ ] Error handling and recovery systems
- [ ] Performance optimization and scaling

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Technical Considerations

### Conversation State Management
The system uses LangGraph to maintain complex conversation states across multiple turns, ensuring context is preserved and conversations feel natural.

### Scalability
Built with cloud-native principles using FastAPI's async capabilities and React's component architecture for handling concurrent users and conversations.

### Security
- API key management through environment variables
- CORS configuration for cross-origin requests
- Input validation and sanitization for all user inputs

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contact

**Jai Patel** - [GitHub](https://github.com/Jai3405)

Project Link: [https://github.com/Jai3405/AgentFlow](https://github.com/Jai3405/AgentFlow)

---

*AgentFlow: Making AI automation as simple as having a conversation.*