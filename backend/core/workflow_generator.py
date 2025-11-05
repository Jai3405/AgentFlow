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
