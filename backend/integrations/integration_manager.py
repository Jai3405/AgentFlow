"""
Integration Manager for AgentFlow
Coordinates all integration services (email, notifications, webhooks)
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio

from integrations.email.gmail_service import GmailService
from integrations.email.outlook_service import OutlookService
from integrations.notifications.slack_service import SlackService
from integrations.notifications.email_service import EmailNotificationService
from integrations.notifications.sms_service import SMSService
from integrations.webhooks.webhook_manager import WebhookManager
from integrations.webhooks.webhook_handlers import WorkflowWebhookHandler
from integrations.base import (
    BaseIntegration,
    IntegrationStatus,
    IntegrationError,
    AuthenticationError
)


class IntegrationManager:
    """
    Central manager for all integrations
    Provides unified interface for managing email, notifications, and webhooks
    """

    def __init__(self):
        # Email services
        self._gmail_service: Optional[GmailService] = None
        self._outlook_service: Optional[OutlookService] = None

        # Notification services
        self._slack_service: Optional[SlackService] = None
        self._email_notification_service: Optional[EmailNotificationService] = None
        self._sms_service: Optional[SMSService] = None

        # Webhook manager
        self._webhook_manager: Optional[WebhookManager] = None

        # Integration registry
        self.integrations: Dict[str, BaseIntegration] = {}
        self.integration_configs: Dict[str, Dict[str, Any]] = {}

    # Email Service Management

    async def setup_gmail(self, credentials: Dict[str, Any]) -> bool:
        """
        Setup Gmail integration

        Args:
            credentials: Gmail OAuth credentials

        Returns:
            True if setup successful
        """
        try:
            self._gmail_service = GmailService()
            success = await self._gmail_service.connect(credentials)

            if success:
                self.integrations['gmail'] = self._gmail_service
                self.integration_configs['gmail'] = {
                    'type': 'email',
                    'provider': 'gmail',
                    'connected_at': datetime.now().isoformat()
                }

            return success

        except Exception as e:
            raise IntegrationError(f"Failed to setup Gmail: {str(e)}", "Gmail")

    async def setup_outlook(self, credentials: Dict[str, Any]) -> bool:
        """
        Setup Outlook integration

        Args:
            credentials: Outlook OAuth credentials

        Returns:
            True if setup successful
        """
        try:
            self._outlook_service = OutlookService()
            success = await self._outlook_service.connect(credentials)

            if success:
                self.integrations['outlook'] = self._outlook_service
                self.integration_configs['outlook'] = {
                    'type': 'email',
                    'provider': 'outlook',
                    'connected_at': datetime.now().isoformat()
                }

            return success

        except Exception as e:
            raise IntegrationError(f"Failed to setup Outlook: {str(e)}", "Outlook")

    async def send_email(
        self,
        provider: str,
        to: List[str],
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send email using specified provider

        Args:
            provider: 'gmail' or 'outlook'
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (HTML supported)
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of attachments

        Returns:
            Dict with message_id and status
        """
        if provider == 'gmail' and self._gmail_service:
            return await self._gmail_service.send_email(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                attachments=attachments
            )
        elif provider == 'outlook' and self._outlook_service:
            return await self._outlook_service.send_email(
                to=to,
                subject=subject,
                body=body,
                cc=cc,
                bcc=bcc,
                attachments=attachments
            )
        else:
            raise IntegrationError(f"Email provider '{provider}' not configured", provider)

    async def fetch_emails(
        self,
        provider: str,
        folder: str = 'INBOX',
        limit: int = 10,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from specified provider

        Args:
            provider: 'gmail' or 'outlook'
            folder: Email folder/label
            limit: Maximum number of emails to fetch
            filters: Additional filters (from, subject, etc.)

        Returns:
            List of email dictionaries
        """
        if provider == 'gmail' and self._gmail_service:
            return await self._gmail_service.fetch_emails(
                folder=folder,
                limit=limit,
                filters=filters
            )
        elif provider == 'outlook' and self._outlook_service:
            return await self._outlook_service.fetch_emails(
                folder=folder,
                limit=limit,
                filters=filters
            )
        else:
            raise IntegrationError(f"Email provider '{provider}' not configured", provider)

    # Notification Service Management

    async def setup_slack(self, credentials: Dict[str, Any]) -> bool:
        """Setup Slack integration"""
        try:
            self._slack_service = SlackService()
            success = await self._slack_service.connect(credentials)

            if success:
                self.integrations['slack'] = self._slack_service
                self.integration_configs['slack'] = {
                    'type': 'notification',
                    'provider': 'slack',
                    'connected_at': datetime.now().isoformat()
                }

            return success

        except Exception as e:
            raise IntegrationError(f"Failed to setup Slack: {str(e)}", "Slack")

    async def setup_email_notifications(self, credentials: Dict[str, Any]) -> bool:
        """Setup SMTP email notifications"""
        try:
            self._email_notification_service = EmailNotificationService()
            success = await self._email_notification_service.connect(credentials)

            if success:
                self.integrations['email_notifications'] = self._email_notification_service
                self.integration_configs['email_notifications'] = {
                    'type': 'notification',
                    'provider': 'email',
                    'connected_at': datetime.now().isoformat()
                }

            return success

        except Exception as e:
            raise IntegrationError(f"Failed to setup email notifications: {str(e)}", "Email")

    async def setup_sms(self, credentials: Dict[str, Any]) -> bool:
        """Setup SMS (Twilio) notifications"""
        try:
            self._sms_service = SMSService()
            success = await self._sms_service.connect(credentials)

            if success:
                self.integrations['sms'] = self._sms_service
                self.integration_configs['sms'] = {
                    'type': 'notification',
                    'provider': 'twilio',
                    'connected_at': datetime.now().isoformat()
                }

            return success

        except Exception as e:
            raise IntegrationError(f"Failed to setup SMS: {str(e)}", "SMS")

    async def send_notification(
        self,
        channels: List[str],
        message: str,
        title: str = None,
        priority: str = "normal",
        recipients: Dict[str, List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send notification across multiple channels

        Args:
            channels: List of channels ('slack', 'email', 'sms')
            message: Notification message
            title: Optional title
            priority: Priority level (normal, high, urgent)
            recipients: Dict mapping channel to recipient list
                Example: {'slack': ['#general'], 'email': ['user@example.com'], 'sms': ['+1234567890']}

        Returns:
            Dict with results per channel
        """
        results = {}

        for channel in channels:
            channel_recipients = recipients.get(channel, []) if recipients else []

            try:
                if channel == 'slack' and self._slack_service:
                    result = await self._slack_service.send_notification(
                        recipients=channel_recipients,
                        message=message,
                        title=title,
                        priority=priority
                    )
                    results['slack'] = {'status': 'success', 'data': result}

                elif channel == 'email' and self._email_notification_service:
                    result = await self._email_notification_service.send_notification(
                        recipients=channel_recipients,
                        message=message,
                        title=title,
                        priority=priority
                    )
                    results['email'] = {'status': 'success', 'data': result}

                elif channel == 'sms' and self._sms_service:
                    result = await self._sms_service.send_notification(
                        recipients=channel_recipients,
                        message=message,
                        title=title,
                        priority=priority
                    )
                    results['sms'] = {'status': 'success', 'data': result}

                else:
                    results[channel] = {
                        'status': 'error',
                        'error': f'Channel {channel} not configured'
                    }

            except Exception as e:
                results[channel] = {
                    'status': 'error',
                    'error': str(e)
                }

        return {
            'overall_status': 'partial_success' if any(r['status'] == 'error' for r in results.values()) else 'success',
            'results': results
        }

    # Webhook Management

    async def setup_webhooks(self) -> bool:
        """Initialize webhook manager"""
        try:
            self._webhook_manager = WebhookManager()

            # Register default workflow webhook handler
            workflow_handler = WorkflowWebhookHandler()
            self._webhook_manager.register_handler('workflow', workflow_handler)

            self.integrations['webhooks'] = self._webhook_manager
            self.integration_configs['webhooks'] = {
                'type': 'webhook',
                'provider': 'internal',
                'connected_at': datetime.now().isoformat()
            }

            return True

        except Exception as e:
            raise IntegrationError(f"Failed to setup webhooks: {str(e)}", "Webhooks")

    def register_webhook(
        self,
        url: str,
        events: List[str],
        secret: str = None,
        description: str = None
    ) -> str:
        """
        Register a new webhook

        Args:
            url: Webhook URL
            events: List of event types to subscribe to
            secret: Optional secret for HMAC signing
            description: Optional description

        Returns:
            Webhook ID
        """
        if not self._webhook_manager:
            raise IntegrationError("Webhook manager not initialized", "Webhooks")

        return self._webhook_manager.register_webhook(
            url=url,
            events=events,
            secret=secret,
            description=description
        )

    async def trigger_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trigger webhook for an event

        Args:
            event_type: Type of event
            payload: Event payload

        Returns:
            Dict with trigger results
        """
        if not self._webhook_manager:
            raise IntegrationError("Webhook manager not initialized", "Webhooks")

        return await self._webhook_manager.trigger_webhook(event_type, payload)

    def unregister_webhook(self, webhook_id: str) -> bool:
        """Unregister a webhook"""
        if not self._webhook_manager:
            raise IntegrationError("Webhook manager not initialized", "Webhooks")

        return self._webhook_manager.unregister_webhook(webhook_id)

    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List all registered webhooks"""
        if not self._webhook_manager:
            return []

        return self._webhook_manager.list_webhooks()

    # Integration Status and Management

    def get_integration_status(self, integration_name: str) -> Dict[str, Any]:
        """
        Get status of a specific integration

        Args:
            integration_name: Name of integration

        Returns:
            Status dict
        """
        if integration_name not in self.integrations:
            return {
                'name': integration_name,
                'status': 'not_configured',
                'connected': False
            }

        integration = self.integrations[integration_name]
        config = self.integration_configs.get(integration_name, {})

        return {
            'name': integration_name,
            'status': integration.status.value if hasattr(integration, 'status') else 'unknown',
            'connected': integration.status == IntegrationStatus.CONNECTED if hasattr(integration, 'status') else False,
            'type': config.get('type'),
            'provider': config.get('provider'),
            'connected_at': config.get('connected_at'),
            'metadata': integration.metadata if hasattr(integration, 'metadata') else {}
        }

    def list_integrations(self) -> List[Dict[str, Any]]:
        """
        List all integrations and their status

        Returns:
            List of integration status dicts
        """
        return [
            self.get_integration_status(name)
            for name in self.integrations.keys()
        ]

    async def test_integration(self, integration_name: str) -> bool:
        """
        Test connection for a specific integration

        Args:
            integration_name: Name of integration

        Returns:
            True if test successful
        """
        if integration_name not in self.integrations:
            raise IntegrationError(f"Integration '{integration_name}' not found", integration_name)

        integration = self.integrations[integration_name]

        if hasattr(integration, 'test_connection'):
            return await integration.test_connection()

        return False

    async def disconnect_integration(self, integration_name: str) -> bool:
        """
        Disconnect a specific integration

        Args:
            integration_name: Name of integration

        Returns:
            True if disconnected successfully
        """
        if integration_name not in self.integrations:
            return False

        integration = self.integrations[integration_name]

        if hasattr(integration, 'disconnect'):
            success = await integration.disconnect()
            if success:
                del self.integrations[integration_name]
                if integration_name in self.integration_configs:
                    del self.integration_configs[integration_name]
            return success

        return False

    async def disconnect_all(self) -> Dict[str, bool]:
        """
        Disconnect all integrations

        Returns:
            Dict mapping integration name to success status
        """
        results = {}

        for integration_name in list(self.integrations.keys()):
            try:
                results[integration_name] = await self.disconnect_integration(integration_name)
            except Exception as e:
                results[integration_name] = False

        return results

    # Bulk Operations

    async def send_multi_channel_alert(
        self,
        message: str,
        priority: str = "high",
        channels: List[str] = None,
        recipients: Dict[str, List[str]] = None
    ) -> Dict[str, Any]:
        """
        Send alert across all available notification channels

        Args:
            message: Alert message
            priority: Priority level
            channels: Specific channels to use (defaults to all configured)
            recipients: Recipients per channel

        Returns:
            Results dict
        """
        # Determine available channels
        available_channels = []
        if self._slack_service:
            available_channels.append('slack')
        if self._email_notification_service:
            available_channels.append('email')
        if self._sms_service:
            available_channels.append('sms')

        # Use specified channels or all available
        target_channels = channels if channels else available_channels

        return await self.send_notification(
            channels=target_channels,
            message=message,
            title="Alert",
            priority=priority,
            recipients=recipients
        )
