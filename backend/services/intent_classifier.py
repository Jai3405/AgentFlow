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
