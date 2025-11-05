"""
Base classes for integration services
Provides common interfaces and error handling
"""

from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum


class IntegrationStatus(str, Enum):
    """Status of an integration"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    AUTHENTICATING = "authenticating"


class IntegrationType(str, Enum):
    """Type of integration"""
    EMAIL = "email"
    NOTIFICATION = "notification"
    WEBHOOK = "webhook"
    DATABASE = "database"
    STORAGE = "storage"


class IntegrationError(Exception):
    """Base exception for integration errors"""
    def __init__(self, message: str, integration_name: str, details: Dict = None):
        self.message = message
        self.integration_name = integration_name
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(IntegrationError):
    """Authentication failed for integration"""
    pass


class RateLimitError(IntegrationError):
    """Rate limit exceeded for integration"""
    pass


class BaseIntegration(ABC):
    """Base class for all integrations"""

    def __init__(self, name: str, integration_type: IntegrationType):
        self.name = name
        self.integration_type = integration_type
        self.status = IntegrationStatus.DISCONNECTED
        self.last_connected = None
        self.last_error = None
        self.metadata = {}

    @abstractmethod
    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to the integration service

        Args:
            credentials: Authentication credentials

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """
        Disconnect from the integration service

        Returns:
            True if disconnection successful
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test if connection is still valid

        Returns:
            True if connection is valid
        """
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current integration status"""
        return {
            "name": self.name,
            "type": self.integration_type.value,
            "status": self.status.value,
            "last_connected": self.last_connected.isoformat() if self.last_connected else None,
            "last_error": self.last_error,
            "metadata": self.metadata
        }

    def _set_connected(self):
        """Mark integration as connected"""
        self.status = IntegrationStatus.CONNECTED
        self.last_connected = datetime.now()
        self.last_error = None

    def _set_error(self, error: str):
        """Mark integration as error state"""
        self.status = IntegrationStatus.ERROR
        self.last_error = error


class BaseEmailService(BaseIntegration):
    """Base class for email integrations"""

    def __init__(self, name: str):
        super().__init__(name, IntegrationType.EMAIL)

    @abstractmethod
    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Send an email

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body (HTML or plain text)
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of attachment dicts

        Returns:
            Dict with message_id and status
        """
        pass

    @abstractmethod
    async def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from mailbox

        Args:
            folder: Mailbox folder to fetch from
            limit: Maximum number of emails to fetch
            unread_only: Only fetch unread emails
            since: Only fetch emails since this date

        Returns:
            List of email dicts
        """
        pass

    @abstractmethod
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read"""
        pass

    @abstractmethod
    async def mark_as_unread(self, message_id: str) -> bool:
        """Mark email as unread"""
        pass


class BaseNotificationService(BaseIntegration):
    """Base class for notification services"""

    def __init__(self, name: str):
        super().__init__(name, IntegrationType.NOTIFICATION)

    @abstractmethod
    async def send_notification(
        self,
        recipients: List[str],
        message: str,
        title: str = None,
        priority: str = "normal",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send a notification

        Args:
            recipients: List of recipient identifiers
            message: Notification message
            title: Optional notification title
            priority: Priority level (low, normal, high, urgent)
            metadata: Additional metadata

        Returns:
            Dict with notification_id and status
        """
        pass

    @abstractmethod
    async def get_delivery_status(self, notification_id: str) -> Dict[str, Any]:
        """Get delivery status of a notification"""
        pass


class BaseWebhookHandler(ABC):
    """Base class for webhook handlers"""

    @abstractmethod
    async def handle_webhook(
        self,
        event_type: str,
        payload: Dict[str, Any],
        headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Handle incoming webhook

        Args:
            event_type: Type of webhook event
            payload: Webhook payload data
            headers: Request headers

        Returns:
            Response dict
        """
        pass

    @abstractmethod
    def verify_signature(self, payload: bytes, signature: str, secret: str) -> bool:
        """Verify webhook signature"""
        pass
