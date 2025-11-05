"""
Webhook Manager
Manages webhook registrations, routing, and security
"""

from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
import hmac
import hashlib
import uuid
import json

from integrations.base import BaseWebhookHandler, IntegrationError


class WebhookRegistration:
    """Represents a registered webhook"""

    def __init__(
        self,
        webhook_id: str,
        url: str,
        events: List[str],
        secret: str = None,
        metadata: Dict = None
    ):
        self.webhook_id = webhook_id
        self.url = url
        self.events = events
        self.secret = secret or self._generate_secret()
        self.metadata = metadata or {}
        self.created_at = datetime.now()
        self.last_triggered = None
        self.trigger_count = 0
        self.enabled = True

    @staticmethod
    def _generate_secret() -> str:
        """Generate a secure webhook secret"""
        return hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'webhook_id': self.webhook_id,
            'url': self.url,
            'events': self.events,
            'secret': self.secret,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'last_triggered': self.last_triggered.isoformat() if self.last_triggered else None,
            'trigger_count': self.trigger_count,
            'enabled': self.enabled
        }


class WebhookManager:
    """Manages webhooks for AgentFlow"""

    def __init__(self):
        self.webhooks: Dict[str, WebhookRegistration] = {}
        self.handlers: Dict[str, Callable] = {}
        self.event_log: List[Dict] = []

    def register_webhook(
        self,
        url: str,
        events: List[str],
        secret: str = None,
        metadata: Dict = None
    ) -> str:
        """
        Register a new webhook

        Args:
            url: Webhook URL to call
            events: List of event types to subscribe to
            secret: Optional webhook secret (generated if not provided)
            metadata: Optional metadata

        Returns:
            webhook_id
        """
        webhook_id = str(uuid.uuid4())

        webhook = WebhookRegistration(
            webhook_id=webhook_id,
            url=url,
            events=events,
            secret=secret,
            metadata=metadata
        )

        self.webhooks[webhook_id] = webhook

        return webhook_id

    def unregister_webhook(self, webhook_id: str) -> bool:
        """
        Unregister a webhook

        Args:
            webhook_id: Webhook ID to remove

        Returns:
            True if removed
        """
        if webhook_id in self.webhooks:
            del self.webhooks[webhook_id]
            return True
        return False

    def get_webhook(self, webhook_id: str) -> Optional[WebhookRegistration]:
        """Get webhook by ID"""
        return self.webhooks.get(webhook_id)

    def list_webhooks(self, event_type: str = None) -> List[Dict]:
        """
        List all registered webhooks

        Args:
            event_type: Optional filter by event type

        Returns:
            List of webhook dicts
        """
        webhooks = list(self.webhooks.values())

        if event_type:
            webhooks = [w for w in webhooks if event_type in w.events]

        return [w.to_dict() for w in webhooks]

    def enable_webhook(self, webhook_id: str) -> bool:
        """Enable a webhook"""
        if webhook_id in self.webhooks:
            self.webhooks[webhook_id].enabled = True
            return True
        return False

    def disable_webhook(self, webhook_id: str) -> bool:
        """Disable a webhook"""
        if webhook_id in self.webhooks:
            self.webhooks[webhook_id].enabled = False
            return True
        return False

    async def trigger_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Trigger webhooks for an event

        Args:
            event_type: Type of event
            payload: Event payload data
            metadata: Optional metadata

        Returns:
            List of delivery results
        """
        import aiohttp
        import asyncio

        results = []

        # Find webhooks subscribed to this event
        subscribed_webhooks = [
            w for w in self.webhooks.values()
            if event_type in w.events and w.enabled
        ]

        if not subscribed_webhooks:
            return []

        # Prepare event data
        event_data = {
            'event_type': event_type,
            'payload': payload,
            'metadata': metadata or {},
            'timestamp': datetime.now().isoformat(),
            'event_id': str(uuid.uuid4())
        }

        # Log event
        self.event_log.append(event_data)

        # Trigger each webhook
        async def call_webhook(webhook: WebhookRegistration):
            try:
                # Create signature
                signature = self._create_signature(json.dumps(event_data), webhook.secret)

                headers = {
                    'Content-Type': 'application/json',
                    'X-AgentFlow-Signature': signature,
                    'X-AgentFlow-Event': event_type,
                    'X-AgentFlow-Webhook-ID': webhook.webhook_id
                }

                # Make request with timeout
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook.url,
                        json=event_data,
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as response:
                        webhook.last_triggered = datetime.now()
                        webhook.trigger_count += 1

                        return {
                            'webhook_id': webhook.webhook_id,
                            'url': webhook.url,
                            'status_code': response.status,
                            'success': 200 <= response.status < 300,
                            'response': await response.text() if response.status < 300 else None,
                            'error': await response.text() if response.status >= 300 else None
                        }

            except asyncio.TimeoutError:
                return {
                    'webhook_id': webhook.webhook_id,
                    'url': webhook.url,
                    'success': False,
                    'error': 'Request timeout'
                }
            except Exception as e:
                return {
                    'webhook_id': webhook.webhook_id,
                    'url': webhook.url,
                    'success': False,
                    'error': str(e)
                }

        # Call all webhooks concurrently
        tasks = [call_webhook(webhook) for webhook in subscribed_webhooks]
        results = await asyncio.gather(*tasks)

        return results

    def _create_signature(self, payload: str, secret: str) -> str:
        """Create HMAC signature for webhook"""
        return hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()

    def verify_signature(self, payload: str, signature: str, secret: str) -> bool:
        """
        Verify webhook signature

        Args:
            payload: Request payload as string
            signature: Signature from X-AgentFlow-Signature header
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        expected_signature = self._create_signature(payload, secret)
        return hmac.compare_digest(expected_signature, signature)

    def register_handler(self, event_type: str, handler: Callable):
        """
        Register an internal event handler

        Args:
            event_type: Event type to handle
            handler: Async function to call when event occurs
        """
        self.handlers[event_type] = handler

    async def handle_event(self, event_type: str, payload: Dict) -> Any:
        """
        Handle event with registered handler

        Args:
            event_type: Event type
            payload: Event payload

        Returns:
            Handler result
        """
        handler = self.handlers.get(event_type)
        if handler:
            return await handler(payload)
        return None

    def get_event_log(
        self,
        event_type: str = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get webhook event log

        Args:
            event_type: Optional filter by event type
            limit: Maximum number of events to return

        Returns:
            List of event dicts
        """
        events = self.event_log

        if event_type:
            events = [e for e in events if e['event_type'] == event_type]

        # Return most recent events
        return events[-limit:]

    def get_webhook_stats(self, webhook_id: str = None) -> Dict:
        """
        Get webhook statistics

        Args:
            webhook_id: Optional specific webhook ID

        Returns:
            Statistics dict
        """
        if webhook_id:
            webhook = self.webhooks.get(webhook_id)
            if not webhook:
                return {}

            return {
                'webhook_id': webhook_id,
                'trigger_count': webhook.trigger_count,
                'last_triggered': webhook.last_triggered.isoformat() if webhook.last_triggered else None,
                'enabled': webhook.enabled
            }

        # Overall stats
        return {
            'total_webhooks': len(self.webhooks),
            'enabled_webhooks': sum(1 for w in self.webhooks.values() if w.enabled),
            'total_events': len(self.event_log),
            'total_triggers': sum(w.trigger_count for w in self.webhooks.values())
        }
