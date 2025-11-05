"""Email integration services"""

from integrations.email.gmail_service import GmailService
from integrations.email.outlook_service import OutlookService

__all__ = ["GmailService", "OutlookService"]
