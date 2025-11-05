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
