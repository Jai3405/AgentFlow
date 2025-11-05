"""
Integration services for external platforms
Includes email, notifications, webhooks, and data sources
"""

from integrations.email.gmail_service import GmailService
from integrations.email.outlook_service import OutlookService
from integrations.notifications.slack_service import SlackService
from integrations.notifications.email_service import EmailNotificationService
from integrations.notifications.sms_service import SMSService
from integrations.webhooks.webhook_manager import WebhookManager

__all__ = [
    "GmailService",
    "OutlookService",
    "SlackService",
    "EmailNotificationService",
    "SMSService",
    "WebhookManager"
]
