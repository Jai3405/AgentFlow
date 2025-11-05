"""
Conversation quality metrics and analytics
Tracks and analyzes conversation efficiency and effectiveness
"""

from typing import Dict, List, Optional
from models.conversation import ConversationState, Message, MessageRole
from datetime import datetime, timedelta


class ConversationMetrics:
    """Track and analyze conversation quality metrics"""

    def __init__(self):
        self.metrics_history = []

    def analyze_conversation(self, conversation_state: ConversationState) -> Dict:
        """
        Analyze conversation and return quality metrics

        Returns comprehensive metrics about conversation quality
        """
        metrics = {}

        # Basic metrics
        metrics['message_count'] = len(conversation_state.messages)
        metrics['user_messages'] = len(conversation_state.get_user_messages())
        metrics['assistant_messages'] = metrics['message_count'] - metrics['user_messages']

        # Timing metrics
        metrics.update(self._calculate_timing_metrics(conversation_state))

        # Efficiency metrics
        metrics.update(self._calculate_efficiency_metrics(conversation_state))

        # Clarity metrics
        metrics.update(self._calculate_clarity_metrics(conversation_state))

        # Progress metrics
        metrics.update(self._calculate_progress_metrics(conversation_state))

        # Overall quality score
        metrics['quality_score'] = self._calculate_quality_score(metrics)
        metrics['quality_level'] = self._get_quality_level(metrics['quality_score'])

        return metrics

    def _calculate_timing_metrics(self, conversation_state: ConversationState) -> Dict:
        """Calculate timing-related metrics"""
        metrics = {}

        messages = conversation_state.messages
        if len(messages) < 2:
            return {
                'duration_seconds': 0,
                'avg_response_time': 0,
                'response_times': []
            }

        # Calculate conversation duration
        start_time = messages[0].timestamp
        end_time = messages[-1].timestamp
        duration = (end_time - start_time).total_seconds()
        metrics['duration_seconds'] = round(duration, 2)
        metrics['duration_minutes'] = round(duration / 60, 2)

        # Calculate response times (assistant response time after user message)
        response_times = []
        for i in range(len(messages) - 1):
            if messages[i].role == MessageRole.USER and messages[i+1].role == MessageRole.ASSISTANT:
                response_time = (messages[i+1].timestamp - messages[i].timestamp).total_seconds()
                response_times.append(response_time)

        if response_times:
            metrics['avg_response_time'] = round(sum(response_times) / len(response_times), 2)
            metrics['max_response_time'] = round(max(response_times), 2)
            metrics['min_response_time'] = round(min(response_times), 2)
        else:
            metrics['avg_response_time'] = 0
            metrics['max_response_time'] = 0
            metrics['min_response_time'] = 0

        metrics['response_times'] = response_times

        return metrics

    def _calculate_efficiency_metrics(self, conversation_state: ConversationState) -> Dict:
        """Calculate efficiency metrics"""
        metrics = {}

        user_messages = conversation_state.get_user_messages()
        total_messages = len(conversation_state.messages)

        if total_messages == 0:
            return {
                'messages_per_minute': 0,
                'clarification_ratio': 0,
                'information_density': 0
            }

        # Messages per minute
        if conversation_state.messages:
            duration = (conversation_state.messages[-1].timestamp -
                       conversation_state.messages[0].timestamp).total_seconds() / 60
            if duration > 0:
                metrics['messages_per_minute'] = round(total_messages / duration, 2)
            else:
                metrics['messages_per_minute'] = 0
        else:
            metrics['messages_per_minute'] = 0

        # Clarification ratio (how many times assistant asks for clarification)
        clarification_keywords = ['what', 'which', 'how', 'when', 'where', 'clarify', 'confirm', '?']
        assistant_messages = [msg for msg in conversation_state.messages
                            if msg.role == MessageRole.ASSISTANT]

        clarifications = sum(
            1 for msg in assistant_messages
            if any(keyword in msg.content.lower() for keyword in clarification_keywords)
        )

        if assistant_messages:
            metrics['clarification_ratio'] = round(clarifications / len(assistant_messages), 2)
        else:
            metrics['clarification_ratio'] = 0

        # Information density (entities per message)
        total_entities = sum(len(values) for values in conversation_state.entities.values())
        if user_messages:
            metrics['information_density'] = round(total_entities / len(user_messages), 2)
        else:
            metrics['information_density'] = 0

        metrics['total_entities_extracted'] = total_entities
        metrics['unique_entity_types'] = len(conversation_state.entities)

        return metrics

    def _calculate_clarity_metrics(self, conversation_state: ConversationState) -> Dict:
        """Calculate clarity and understanding metrics"""
        metrics = {}

        user_messages = conversation_state.get_user_messages()

        if not user_messages:
            return {
                'avg_message_length': 0,
                'clarity_score': 0,
                'confusion_indicators': 0
            }

        # Average message length
        total_length = sum(len(msg.content) for msg in user_messages)
        metrics['avg_message_length'] = round(total_length / len(user_messages), 1)

        # Confusion indicators (user says they don't understand or asks for clarification)
        confusion_keywords = [
            "i don't understand", "what do you mean", "confused", "not sure",
            "can you explain", "what?", "huh", "unclear"
        ]

        confusion_count = sum(
            1 for msg in user_messages
            if any(keyword in msg.content.lower() for keyword in confusion_keywords)
        )

        metrics['confusion_indicators'] = confusion_count

        # Clarity score (inverse of confusion, normalized)
        if len(user_messages) > 0:
            confusion_ratio = confusion_count / len(user_messages)
            metrics['clarity_score'] = round(max(0, 1 - confusion_ratio), 2)
        else:
            metrics['clarity_score'] = 1.0

        return metrics

    def _calculate_progress_metrics(self, conversation_state: ConversationState) -> Dict:
        """Calculate progress and momentum metrics"""
        metrics = {}

        user_messages = conversation_state.get_user_messages()

        # Progress velocity (how fast entities are being gathered)
        if len(user_messages) > 1:
            entities_per_message = []
            cumulative_entities = 0

            for i, msg in enumerate(user_messages, 1):
                # This is simplified - in real implementation, we'd track entities per message
                current_entities = sum(len(values) for values in conversation_state.entities.values())
                entities_gained = current_entities - cumulative_entities
                entities_per_message.append(entities_gained)
                cumulative_entities = current_entities

            if entities_per_message:
                metrics['avg_entities_per_message'] = round(
                    sum(entities_per_message) / len(entities_per_message), 2
                )
                # Check if gathering is accelerating or decelerating
                if len(entities_per_message) >= 2:
                    recent_avg = sum(entities_per_message[-2:]) / 2
                    earlier_avg = sum(entities_per_message[:-2]) / max(1, len(entities_per_message) - 2)
                    metrics['gathering_momentum'] = 'accelerating' if recent_avg > earlier_avg else 'decelerating'
                else:
                    metrics['gathering_momentum'] = 'steady'
            else:
                metrics['avg_entities_per_message'] = 0
                metrics['gathering_momentum'] = 'none'
        else:
            metrics['avg_entities_per_message'] = 0
            metrics['gathering_momentum'] = 'initial'

        # Progress consistency (are we making steady progress?)
        metrics['progress_score'] = conversation_state.progress
        metrics['confidence_score'] = conversation_state.confidence_score

        return metrics

    def _calculate_quality_score(self, metrics: Dict) -> float:
        """Calculate overall conversation quality score"""
        score = 0.0

        # Efficiency component (30%)
        # Good: 2-5 messages, moderate pace
        message_count = metrics.get('user_messages', 0)
        if 2 <= message_count <= 5:
            efficiency = 1.0
        elif message_count == 1:
            efficiency = 0.3
        else:
            efficiency = max(0.5, 1.0 - (message_count - 5) * 0.1)

        score += efficiency * 0.3

        # Clarity component (25%)
        clarity = metrics.get('clarity_score', 0)
        score += clarity * 0.25

        # Information density component (20%)
        density = metrics.get('information_density', 0)
        density_normalized = min(1.0, density / 3.0)  # 3+ entities per message is excellent
        score += density_normalized * 0.20

        # Progress component (25%)
        progress = metrics.get('progress_score', 0)
        score += progress * 0.25

        return round(score, 3)

    def _get_quality_level(self, score: float) -> str:
        """Convert quality score to quality level"""
        if score >= 0.85:
            return "excellent"
        elif score >= 0.70:
            return "good"
        elif score >= 0.55:
            return "fair"
        elif score >= 0.40:
            return "needs_improvement"
        else:
            return "poor"

    def get_insights(self, metrics: Dict) -> List[str]:
        """Generate human-readable insights from metrics"""
        insights = []

        # Duration insight
        duration_min = metrics.get('duration_minutes', 0)
        if duration_min < 2:
            insights.append("Quick conversation - efficient information gathering")
        elif duration_min > 10:
            insights.append("Extended conversation - may indicate complexity or confusion")

        # Efficiency insight
        message_count = metrics.get('user_messages', 0)
        if message_count <= 3:
            insights.append("Concise conversation with focused information exchange")
        elif message_count > 6:
            insights.append("Multiple exchanges - consider streamlining question flow")

        # Clarity insight
        clarity = metrics.get('clarity_score', 0)
        if clarity >= 0.9:
            insights.append("Excellent clarity - user understood prompts well")
        elif clarity < 0.6:
            insights.append("Some confusion detected - improve question clarity")

        # Information density insight
        density = metrics.get('information_density', 0)
        if density >= 2.5:
            insights.append("High information density - user provided rich details")
        elif density < 1.0:
            insights.append("Low information density - may need more targeted questions")

        # Progress insight
        progress = metrics.get('progress_score', 0)
        if progress >= 0.8:
            insights.append("Strong progress - close to workflow completion")
        elif progress < 0.4:
            insights.append("Early stage - continue gathering requirements")

        # Momentum insight
        momentum = metrics.get('gathering_momentum', 'none')
        if momentum == 'accelerating':
            insights.append("Positive momentum - information gathering is accelerating")
        elif momentum == 'decelerating':
            insights.append("Slowing momentum - may be approaching completion or hitting obstacles")

        return insights

    def get_recommendations(self, metrics: Dict) -> List[str]:
        """Generate actionable recommendations based on metrics"""
        recommendations = []

        quality_level = metrics.get('quality_level', 'fair')

        if quality_level in ['poor', 'needs_improvement']:
            # Specific recommendations for low quality

            clarity = metrics.get('clarity_score', 0)
            if clarity < 0.6:
                recommendations.append("Ask clearer, more specific questions")

            density = metrics.get('information_density', 0)
            if density < 1.0:
                recommendations.append("Request more detailed information in each exchange")

            message_count = metrics.get('user_messages', 0)
            if message_count > 7:
                recommendations.append("Reduce the number of questions - combine related asks")

        elif quality_level == 'fair':
            # Recommendations for moderate quality
            recommendations.append("Continue current approach - making steady progress")

            clarification_ratio = metrics.get('clarification_ratio', 0)
            if clarification_ratio > 0.5:
                recommendations.append("Reduce clarification questions by being more specific initially")

        else:
            # Recommendations for good/excellent quality
            recommendations.append("Excellent conversation flow - maintain this approach")

        # Progress-based recommendations
        progress = metrics.get('progress_score', 0)
        if progress > 0.7:
            recommendations.append("Near completion - validate gathered information and generate workflow")

        return recommendations

    def compare_conversations(
        self,
        conversation1: ConversationState,
        conversation2: ConversationState
    ) -> Dict:
        """Compare two conversations and return comparative analysis"""
        metrics1 = self.analyze_conversation(conversation1)
        metrics2 = self.analyze_conversation(conversation2)

        comparison = {
            "conversation1": {
                "quality_score": metrics1.get('quality_score', 0),
                "quality_level": metrics1.get('quality_level', 'unknown'),
                "message_count": metrics1.get('message_count', 0),
                "duration_minutes": metrics1.get('duration_minutes', 0),
            },
            "conversation2": {
                "quality_score": metrics2.get('quality_score', 0),
                "quality_level": metrics2.get('quality_level', 'unknown'),
                "message_count": metrics2.get('message_count', 0),
                "duration_minutes": metrics2.get('duration_minutes', 0),
            },
            "better_conversation": None,
            "key_differences": []
        }

        # Determine which is better
        if metrics1['quality_score'] > metrics2['quality_score']:
            comparison['better_conversation'] = 1
        elif metrics2['quality_score'] > metrics1['quality_score']:
            comparison['better_conversation'] = 2
        else:
            comparison['better_conversation'] = 'tie'

        # Key differences
        if abs(metrics1['message_count'] - metrics2['message_count']) > 3:
            comparison['key_differences'].append(
                f"Message count differs significantly ({metrics1['message_count']} vs {metrics2['message_count']})"
            )

        if abs(metrics1['information_density'] - metrics2['information_density']) > 1.0:
            comparison['key_differences'].append(
                f"Information density varies ({metrics1['information_density']:.1f} vs {metrics2['information_density']:.1f})"
            )

        return comparison
