"""
Confidence scoring system for workflow specifications
Evaluates conversation quality and workflow completeness
"""

from typing import Dict, List, Tuple
from models.conversation import ConversationState, Message, MessageRole
from datetime import datetime


class ConfidenceScorer:
    """Calculate confidence scores for workflow specifications"""

    def __init__(self):
        # Weight factors for different scoring dimensions
        self.weights = {
            "entity_coverage": 0.30,      # 30% - How many required entities gathered
            "entity_confidence": 0.20,    # 20% - Average confidence of entities
            "conversation_depth": 0.15,   # 15% - Number of clarifying exchanges
            "workflow_completeness": 0.25,# 25% - Workflow specification quality
            "validation_passed": 0.10     # 10% - Explicit validations passed
        }

    def calculate_overall_confidence(
        self,
        conversation_state: ConversationState,
        intent: str,
        entities: Dict[str, List[Tuple[str, float]]],
        workflow: Dict = None
    ) -> Dict[str, float]:
        """
        Calculate overall confidence score with breakdown

        Returns:
            Dict with overall score and component scores
        """
        scores = {}

        # 1. Entity coverage score
        scores['entity_coverage'] = self._score_entity_coverage(intent, entities)

        # 2. Entity confidence score (average confidence of all entities)
        scores['entity_confidence'] = self._score_entity_confidence(entities)

        # 3. Conversation depth score
        scores['conversation_depth'] = self._score_conversation_depth(conversation_state)

        # 4. Workflow completeness score
        scores['workflow_completeness'] = self._score_workflow_completeness(workflow, intent)

        # 5. Validation passed score
        scores['validation_passed'] = self._score_validation_passed(
            conversation_state, entities
        )

        # Calculate weighted overall score
        overall = sum(
            scores[key] * self.weights[key]
            for key in scores.keys()
        )

        return {
            "overall": round(overall, 3),
            **{k: round(v, 3) for k, v in scores.items()}
        }

    def _score_entity_coverage(self, intent: str, entities: Dict) -> float:
        """Score based on coverage of required entities"""
        required_entities = self._get_required_entities(intent)

        if not required_entities:
            return 1.0

        extracted_types = set(entities.keys())
        coverage = len(extracted_types & required_entities) / len(required_entities)

        return coverage

    def _score_entity_confidence(self, entities: Dict[str, List[Tuple[str, float]]]) -> float:
        """Score based on average confidence of extracted entities"""
        if not entities:
            return 0.0

        all_confidences = []
        for entity_list in entities.values():
            for _, confidence in entity_list:
                all_confidences.append(confidence)

        if not all_confidences:
            return 0.0

        return sum(all_confidences) / len(all_confidences)

    def _score_conversation_depth(self, conversation_state: ConversationState) -> float:
        """Score based on conversation quality and depth"""
        user_messages = conversation_state.get_user_messages()
        message_count = len(user_messages)

        if message_count == 0:
            return 0.0

        # Optimal conversation depth is 3-5 messages
        if message_count == 1:
            return 0.2
        elif message_count == 2:
            return 0.5
        elif message_count == 3:
            return 0.8
        elif message_count in [4, 5]:
            return 1.0
        else:
            # Too many messages might indicate confusion
            return max(0.7, 1.0 - (message_count - 5) * 0.1)

    def _score_workflow_completeness(self, workflow: Dict, intent: str) -> float:
        """Score based on workflow specification completeness"""
        if not workflow:
            return 0.0

        score = 0.0
        max_score = 1.0

        # Check if workflow has steps
        steps = workflow.get('steps', [])
        if not steps:
            return 0.0

        # Base score for having steps
        score += 0.3

        # Score based on number of steps (3-5 is optimal for most workflows)
        expected_steps = self._get_expected_steps(intent)
        step_count = len(steps)

        if step_count >= expected_steps:
            score += 0.3
        else:
            score += 0.3 * (step_count / expected_steps)

        # Check if steps have required fields
        steps_complete = all(
            'id' in step and 'type' in step and 'name' in step and 'description' in step
            for step in steps
        )
        if steps_complete:
            score += 0.2

        # Check if workflow has metadata
        if workflow.get('metadata'):
            score += 0.1

        # Check if workflow has connections (for multi-step workflows)
        if step_count > 1 and workflow.get('connections'):
            score += 0.1

        return min(score, max_score)

    def _score_validation_passed(
        self,
        conversation_state: ConversationState,
        entities: Dict
    ) -> float:
        """Score based on validation checks passed"""
        score = 0.0

        # Check if user confirmed/validated information
        messages = conversation_state.messages
        confirmation_keywords = ['yes', 'correct', 'right', 'confirm', 'approve', 'looks good']

        user_confirmations = sum(
            1 for msg in messages
            if msg.role == MessageRole.USER and
            any(keyword in msg.content.lower() for keyword in confirmation_keywords)
        )

        if user_confirmations > 0:
            score += 0.5

        # Check if entities have high confidence
        high_confidence_entities = sum(
            1 for entity_list in entities.values()
            for _, conf in entity_list
            if conf >= 0.8
        )

        total_entities = sum(len(entity_list) for entity_list in entities.values())
        if total_entities > 0:
            score += 0.5 * (high_confidence_entities / total_entities)

        return min(score, 1.0)

    def _get_required_entities(self, intent: str) -> set:
        """Get required entity types for an intent"""
        requirements = {
            "email_automation": {"email_addresses", "team_mentions", "urgency_indicators"},
            "data_processing": {"file_types", "time_expressions"},
            "approval_workflow": {"team_mentions", "time_expressions"},
            "notification_system": {"team_mentions", "tools_services", "urgency_indicators"}
        }
        return requirements.get(intent, set())

    def _get_expected_steps(self, intent: str) -> int:
        """Get expected number of workflow steps for an intent"""
        expected = {
            "email_automation": 4,  # monitor, classify, route, notify
            "data_processing": 4,   # input, validate, transform, output
            "approval_workflow": 4, # submit, review, approve, notify
            "notification_system": 3 # monitor, filter, send
        }
        return expected.get(intent, 3)

    def get_confidence_level(self, score: float) -> str:
        """Convert numeric score to confidence level"""
        if score >= 0.9:
            return "very_high"
        elif score >= 0.75:
            return "high"
        elif score >= 0.6:
            return "medium"
        elif score >= 0.4:
            return "low"
        else:
            return "very_low"

    def get_recommendations(
        self,
        confidence_scores: Dict[str, float],
        intent: str,
        entities: Dict
    ) -> List[str]:
        """Get recommendations to improve confidence score"""
        recommendations = []
        overall = confidence_scores.get('overall', 0)

        # Entity coverage recommendations
        entity_coverage = confidence_scores.get('entity_coverage', 0)
        if entity_coverage < 0.7:
            missing = self._get_required_entities(intent) - set(entities.keys())
            if missing:
                recommendations.append(
                    f"Gather more information about: {', '.join(missing)}"
                )

        # Entity confidence recommendations
        entity_confidence = confidence_scores.get('entity_confidence', 0)
        if entity_confidence < 0.7:
            recommendations.append(
                "Clarify ambiguous information to increase confidence"
            )

        # Conversation depth recommendations
        conversation_depth = confidence_scores.get('conversation_depth', 0)
        if conversation_depth < 0.5:
            recommendations.append(
                "Ask follow-up questions to better understand requirements"
            )

        # Workflow completeness recommendations
        workflow_completeness = confidence_scores.get('workflow_completeness', 0)
        if workflow_completeness < 0.7:
            recommendations.append(
                "Add more detailed steps to the workflow"
            )

        # Validation recommendations
        validation_passed = confidence_scores.get('validation_passed', 0)
        if validation_passed < 0.5:
            recommendations.append(
                "Confirm workflow details with the user"
            )

        return recommendations

    def should_request_confirmation(self, confidence_scores: Dict[str, float]) -> bool:
        """Determine if we should ask user to confirm before proceeding"""
        overall = confidence_scores.get('overall', 0)

        # Request confirmation if overall confidence is medium or below
        if overall < 0.75:
            return True

        # Also request if any component is very low
        for key, value in confidence_scores.items():
            if key != 'overall' and value < 0.5:
                return True

        return False

    def generate_confidence_summary(
        self,
        confidence_scores: Dict[str, float],
        intent: str
    ) -> str:
        """Generate human-readable confidence summary"""
        overall = confidence_scores.get('overall', 0)
        level = self.get_confidence_level(overall)

        level_descriptions = {
            "very_high": "I'm very confident about this workflow",
            "high": "I'm quite confident about this workflow",
            "medium": "I have a moderate understanding of this workflow",
            "low": "I need more information to build this workflow properly",
            "very_low": "I need significantly more information"
        }

        summary = level_descriptions.get(level, "Processing...")

        # Add specific weak points
        weak_points = []
        for key, value in confidence_scores.items():
            if key != 'overall' and value < 0.6:
                weak_points.append(key.replace('_', ' '))

        if weak_points:
            summary += f". I could use more clarity on: {', '.join(weak_points)}."

        return summary
