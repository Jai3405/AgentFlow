"""
Enhanced entity extraction using Gemini AI
Provides intelligent Named Entity Recognition with confidence scores
"""

from typing import Dict, List, Tuple
import re
import os
import json
from google import genai


class EntityExtractorGemini:
    """Enhanced entity extractor using Gemini for NER"""

    def __init__(self):
        # Fallback regex patterns for when LLM is unavailable
        self.regex_patterns = {
            "email_addresses": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "file_types": r'\b(csv|excel|pdf|json|xml|txt|doc|docx|xlsx|xls)\b',
            "time_expressions": r'\b(daily|weekly|monthly|hourly|every \d+|at \d+|monday|tuesday|wednesday|thursday|friday|saturday|sunday|morning|afternoon|evening|night)\b',
            "team_mentions": r'\b(team|department|group|support|sales|technical|billing|engineering|marketing|hr|finance|operations|customer service)\b',
            "urgency_indicators": r'\b(urgent|critical|asap|immediately|priority|emergency|high priority|time sensitive)\b',
            "numbers": r'\b\d+(?:,\d{3})*(?:\.\d+)?\b',
            "currencies": r'\$\s?\d+(?:,\d{3})*(?:\.\d{2})?|\d+(?:,\d{3})*(?:\.\d{2})?\s?(?:USD|EUR|GBP|dollars?)',
        }

        # Initialize Gemini API
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            self.client = genai.Client(api_key=api_key)
            self.model_name = 'gemini-2.5-flash'
            self.llm_enabled = True
        else:
            print("Warning: GEMINI_API_KEY not found. Using regex-only entity extraction.")
            self.client = None
            self.llm_enabled = False

    async def extract(self, text: str, intent: str = None) -> Dict[str, List[Tuple[str, float]]]:
        """
        Extract entities from text with confidence scores

        Args:
            text: Input text to extract entities from
            intent: Optional intent to guide extraction

        Returns:
            Dict mapping entity types to list of (value, confidence) tuples
        """
        if self.llm_enabled:
            return await self._extract_with_llm(text, intent)
        else:
            return self._extract_with_regex(text)

    async def _extract_with_llm(self, text: str, intent: str = None) -> Dict[str, List[Tuple[str, float]]]:
        """Extract entities using Gemini LLM with confidence scores"""
        try:
            # Build intent-specific guidance
            intent_guidance = self._get_intent_guidance(intent) if intent else ""

            prompt = f"""You are an expert entity extraction system for a workflow automation platform.

Extract relevant entities from the following text and provide confidence scores (0.0 to 1.0).

Text: "{text}"

{intent_guidance}

Extract these entity types:
1. email_addresses: Email addresses mentioned
2. file_types: File formats or data types (csv, json, excel, etc.)
3. time_expressions: Time-related phrases (daily, weekly, at 9am, every monday, etc.)
4. team_mentions: Teams, departments, or roles mentioned
5. urgency_indicators: Words indicating urgency or priority
6. numbers: Numeric values mentioned
7. currencies: Money amounts with currency symbols
8. tools_services: External tools/services mentioned (Slack, Gmail, Salesforce, etc.)
9. actions: Key actions or verbs (send, notify, process, approve, etc.)
10. conditions: Conditional phrases (if, when, unless, etc.)

Format your response as JSON:
{{
    "entity_type": [
        {{"value": "extracted_value", "confidence": 0.95, "context": "brief context"}}
    ]
}}

Only include entities you find. Provide confidence based on:
- High (0.9-1.0): Explicitly stated, clear context
- Medium (0.6-0.89): Implied or partial match
- Low (0.3-0.59): Ambiguous or uncertain

Response (JSON only):"""

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )

            # Parse JSON response
            response_text = response.text.strip()

            # Extract JSON from response (handle markdown code blocks)
            if '```json' in response_text:
                json_start = response_text.find('```json') + 7
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()
            elif '```' in response_text:
                json_start = response_text.find('```') + 3
                json_end = response_text.find('```', json_start)
                response_text = response_text[json_start:json_end].strip()

            entities_json = json.loads(response_text)

            # Convert to our format: Dict[str, List[Tuple[str, float]]]
            entities = {}
            for entity_type, values in entities_json.items():
                if isinstance(values, list) and values:
                    entities[entity_type] = [
                        (item['value'], item['confidence'])
                        for item in values
                        if isinstance(item, dict) and 'value' in item and 'confidence' in item
                    ]

            # Enhance with regex for high-confidence patterns
            regex_entities = self._extract_with_regex(text)
            entities = self._merge_entities(entities, regex_entities)

            return entities

        except Exception as e:
            print(f"Error in LLM entity extraction: {e}")
            # Fallback to regex
            return self._extract_with_regex(text)

    def _extract_with_regex(self, text: str) -> Dict[str, List[Tuple[str, float]]]:
        """Fallback regex-based extraction with confidence scores"""
        entities = {}
        text_lower = text.lower()

        for entity_type, pattern in self.regex_patterns.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                # Assign confidence based on pattern strength
                confidence = self._get_regex_confidence(entity_type, matches, text_lower)
                entities[entity_type] = [(match, confidence) for match in set(matches)]

        return entities

    def _get_regex_confidence(self, entity_type: str, matches: List[str], text: str) -> float:
        """Calculate confidence score for regex matches"""
        # High confidence patterns
        if entity_type in ['email_addresses', 'numbers', 'currencies']:
            return 0.95  # Regex is very accurate for these

        # Medium confidence patterns
        if entity_type in ['file_types', 'time_expressions']:
            # Check if mentioned in context
            if any(word in text for word in ['file', 'format', 'data', 'schedule', 'time', 'when']):
                return 0.85
            return 0.7

        # Lower confidence for ambiguous patterns
        if entity_type in ['team_mentions', 'urgency_indicators']:
            return 0.75

        return 0.6

    def _get_intent_guidance(self, intent: str) -> str:
        """Get intent-specific extraction guidance"""
        guidance = {
            "email_automation": """
Focus especially on:
- Email addresses and domains
- Team names for routing
- Urgency keywords for prioritization
- Time expressions for schedules
""",
            "data_processing": """
Focus especially on:
- File types and formats
- Data sources (databases, APIs, files)
- Processing frequency/schedule
- Numeric thresholds or limits
""",
            "approval_workflow": """
Focus especially on:
- Team/department names
- Approval hierarchies or roles
- Time limits for approvals
- Conditions for auto-approval
- Currency amounts if applicable
""",
            "notification_system": """
Focus especially on:
- Communication channels (Slack, email, SMS)
- Team mentions for recipients
- Urgency levels
- Event triggers
- Time-based conditions
"""
        }
        return guidance.get(intent, "")

    def _merge_entities(self, llm_entities: Dict, regex_entities: Dict) -> Dict[str, List[Tuple[str, float]]]:
        """Merge LLM and regex entities, preferring higher confidence"""
        merged = {}
        all_types = set(llm_entities.keys()) | set(regex_entities.keys())

        for entity_type in all_types:
            llm_values = dict(llm_entities.get(entity_type, []))
            regex_values = dict(regex_entities.get(entity_type, []))

            # Combine and keep highest confidence for each value
            all_values = {}
            for value, conf in llm_values.items():
                all_values[value] = conf
            for value, conf in regex_values.items():
                if value in all_values:
                    all_values[value] = max(all_values[value], conf)
                else:
                    all_values[value] = conf

            if all_values:
                merged[entity_type] = [(val, conf) for val, conf in all_values.items()]

        return merged

    def validate_entity(self, entity_type: str, value: str) -> Tuple[bool, float, str]:
        """
        Validate an extracted entity

        Returns:
            (is_valid, confidence, reason)
        """
        validators = {
            "email_addresses": self._validate_email,
            "file_types": self._validate_file_type,
            "time_expressions": self._validate_time_expression,
            "numbers": self._validate_number,
            "currencies": self._validate_currency,
        }

        validator = validators.get(entity_type)
        if validator:
            return validator(value)

        # Default validation
        return True, 0.8, "No specific validator"

    def _validate_email(self, email: str) -> Tuple[bool, float, str]:
        """Validate email address"""
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        if re.match(pattern, email):
            return True, 0.95, "Valid email format"
        return False, 0.0, "Invalid email format"

    def _validate_file_type(self, file_type: str) -> Tuple[bool, float, str]:
        """Validate file type"""
        valid_types = {'csv', 'excel', 'pdf', 'json', 'xml', 'txt', 'doc', 'docx', 'xlsx', 'xls'}
        if file_type.lower() in valid_types:
            return True, 0.9, "Known file type"
        return True, 0.6, "Uncommon file type"

    def _validate_time_expression(self, time_expr: str) -> Tuple[bool, float, str]:
        """Validate time expression"""
        time_keywords = ['daily', 'weekly', 'monthly', 'hourly', 'every', 'at', 'monday', 'tuesday',
                         'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        if any(keyword in time_expr.lower() for keyword in time_keywords):
            return True, 0.85, "Valid time expression"
        return True, 0.5, "Ambiguous time expression"

    def _validate_number(self, number: str) -> Tuple[bool, float, str]:
        """Validate numeric value"""
        try:
            float(number.replace(',', ''))
            return True, 0.95, "Valid number"
        except ValueError:
            return False, 0.0, "Invalid number format"

    def _validate_currency(self, currency: str) -> Tuple[bool, float, str]:
        """Validate currency amount"""
        if re.search(r'[\$€£]', currency) or re.search(r'USD|EUR|GBP', currency):
            return True, 0.9, "Valid currency format"
        return False, 0.3, "Ambiguous currency"

    def get_missing_entities(self, intent: str, extracted_entities: Dict) -> List[str]:
        """Get list of missing required entities for an intent"""
        required_entities = {
            "email_automation": ["email_addresses", "team_mentions", "urgency_indicators"],
            "data_processing": ["file_types", "time_expressions"],
            "approval_workflow": ["team_mentions", "time_expressions"],
            "notification_system": ["team_mentions", "tools_services"]
        }

        required = required_entities.get(intent, [])
        extracted = set(extracted_entities.keys())
        missing = [entity for entity in required if entity not in extracted]

        return missing

    def calculate_completeness(self, intent: str, extracted_entities: Dict) -> float:
        """Calculate how complete the entity extraction is for an intent"""
        required_entities = {
            "email_automation": ["email_addresses", "team_mentions", "urgency_indicators"],
            "data_processing": ["file_types", "time_expressions"],
            "approval_workflow": ["team_mentions", "time_expressions"],
            "notification_system": ["team_mentions", "tools_services"]
        }

        required = set(required_entities.get(intent, []))
        if not required:
            return 1.0

        extracted = set(extracted_entities.keys())
        completeness = len(extracted & required) / len(required)

        return completeness
