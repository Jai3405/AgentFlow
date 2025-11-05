"""
Outlook/Microsoft Graph API integration service
Provides email operations using Microsoft Graph API
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os

try:
    from msal import ConfidentialClientApplication, PublicClientApplication
    import requests
    OUTLOOK_AVAILABLE = True
except ImportError:
    OUTLOOK_AVAILABLE = False
    print("Warning: MSAL library not installed. Outlook integration disabled.")

from integrations.base import BaseEmailService, AuthenticationError, IntegrationError


class OutlookService(BaseEmailService):
    """Microsoft Graph API integration for Outlook"""

    # Microsoft Graph API endpoints
    GRAPH_API_ENDPOINT = 'https://graph.microsoft.com/v1.0'

    # Required scopes
    SCOPES = [
        'Mail.Read',
        'Mail.Send',
        'Mail.ReadWrite'
    ]

    def __init__(self):
        super().__init__("Outlook")
        self.client_app = None
        self.access_token = None
        self.user_email = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to Microsoft Graph API

        Args:
            credentials: Dict with:
                - client_id: Application (client) ID
                - client_secret: Client secret (for confidential apps)
                - tenant_id: Directory (tenant) ID
                - Or access_token: Pre-obtained access token

        Returns:
            True if connection successful
        """
        if not OUTLOOK_AVAILABLE:
            raise IntegrationError(
                "MSAL library not installed. Install with: pip install msal requests",
                "Outlook"
            )

        try:
            # If access token provided directly
            if 'access_token' in credentials:
                self.access_token = credentials['access_token']
            else:
                # Authenticate using MSAL
                client_id = credentials.get('client_id')
                client_secret = credentials.get('client_secret')
                tenant_id = credentials.get('tenant_id', 'common')

                if not client_id:
                    raise AuthenticationError("client_id is required", "Outlook")

                authority = f"https://login.microsoftonline.com/{tenant_id}"

                if client_secret:
                    # Confidential client (server-side)
                    self.client_app = ConfidentialClientApplication(
                        client_id,
                        authority=authority,
                        client_credential=client_secret
                    )
                else:
                    # Public client (device code flow)
                    self.client_app = PublicClientApplication(
                        client_id,
                        authority=authority
                    )

                # Acquire token
                result = self.client_app.acquire_token_for_client(scopes=self.SCOPES)

                if 'access_token' in result:
                    self.access_token = result['access_token']
                else:
                    error = result.get('error_description', 'Unknown error')
                    raise AuthenticationError(f"Failed to acquire token: {error}", "Outlook")

            # Get user profile
            profile = await self._make_request('GET', '/me')
            self.user_email = profile.get('mail') or profile.get('userPrincipalName')

            self._set_connected()
            self.metadata['user_email'] = self.user_email

            return True

        except Exception as e:
            self._set_error(str(e))
            raise IntegrationError(f"Failed to connect to Outlook: {str(e)}", "Outlook")

    async def disconnect(self) -> bool:
        """Disconnect from Microsoft Graph API"""
        self.client_app = None
        self.access_token = None
        self.status = IntegrationStatus.DISCONNECTED
        return True

    async def test_connection(self) -> bool:
        """Test if Outlook connection is still valid"""
        try:
            if not self.access_token:
                return False

            # Try to get user profile
            await self._make_request('GET', '/me')
            return True

        except Exception:
            self._set_error("Connection test failed")
            return False

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Dict = None,
        params: Dict = None
    ) -> Dict:
        """Make request to Microsoft Graph API"""
        if not self.access_token:
            raise IntegrationError("Not authenticated", "Outlook")

        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

        url = f"{self.GRAPH_API_ENDPOINT}{endpoint}"

        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            json=data,
            params=params
        )

        if response.status_code >= 400:
            raise IntegrationError(
                f"Microsoft Graph API error: {response.status_code}",
                "Outlook",
                {'response': response.text}
            )

        return response.json() if response.text else {}

    async def send_email(
        self,
        to: List[str],
        subject: str,
        body: str,
        cc: List[str] = None,
        bcc: List[str] = None,
        attachments: List[Dict] = None,
        is_html: bool = True
    ) -> Dict[str, Any]:
        """
        Send an email via Outlook

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of attachment dicts
            is_html: Whether body is HTML

        Returns:
            Dict with message_id and status
        """
        try:
            # Build message
            message = {
                'subject': subject,
                'body': {
                    'contentType': 'HTML' if is_html else 'Text',
                    'content': body
                },
                'toRecipients': [{'emailAddress': {'address': addr}} for addr in to]
            }

            if cc:
                message['ccRecipients'] = [{'emailAddress': {'address': addr}} for addr in cc]

            if bcc:
                message['bccRecipients'] = [{'emailAddress': {'address': addr}} for addr in bcc]

            if attachments:
                message['attachments'] = [
                    {
                        '@odata.type': '#microsoft.graph.fileAttachment',
                        'name': att['filename'],
                        'contentBytes': att['content']
                    }
                    for att in attachments
                ]

            # Send message
            result = await self._make_request(
                'POST',
                '/me/sendMail',
                data={'message': message, 'saveToSentItems': True}
            )

            return {
                'message_id': result.get('id', 'sent'),
                'status': 'sent'
            }

        except Exception as e:
            raise IntegrationError(f"Failed to send email: {str(e)}", "Outlook")

    async def fetch_emails(
        self,
        folder: str = "inbox",
        limit: int = 10,
        unread_only: bool = False,
        since: datetime = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from Outlook

        Args:
            folder: Folder name (inbox, sentitems, etc.)
            limit: Maximum number of emails
            unread_only: Only fetch unread emails
            since: Only fetch emails since this date

        Returns:
            List of email dicts
        """
        try:
            # Build query parameters
            params = {
                '$top': limit,
                '$orderby': 'receivedDateTime DESC'
            }

            # Build filter
            filters = []
            if unread_only:
                filters.append('isRead eq false')

            if since:
                date_str = since.strftime('%Y-%m-%dT%H:%M:%SZ')
                filters.append(f'receivedDateTime ge {date_str}')

            if filters:
                params['$filter'] = ' and '.join(filters)

            # Fetch messages
            result = await self._make_request(
                'GET',
                f'/me/mailFolders/{folder}/messages',
                params=params
            )

            messages = result.get('value', [])

            # Parse messages
            emails = [self._parse_email(msg) for msg in messages]

            return emails

        except Exception as e:
            raise IntegrationError(f"Failed to fetch emails: {str(e)}", "Outlook")

    def _parse_email(self, message: Dict) -> Dict[str, Any]:
        """Parse Microsoft Graph API message to simplified dict"""
        return {
            'id': message.get('id'),
            'from': message.get('from', {}).get('emailAddress', {}).get('address', ''),
            'to': ', '.join([
                r.get('emailAddress', {}).get('address', '')
                for r in message.get('toRecipients', [])
            ]),
            'cc': ', '.join([
                r.get('emailAddress', {}).get('address', '')
                for r in message.get('ccRecipients', [])
            ]),
            'subject': message.get('subject', ''),
            'body': message.get('body', {}).get('content', ''),
            'date': message.get('receivedDateTime'),
            'is_unread': not message.get('isRead', True),
            'has_attachments': message.get('hasAttachments', False),
            'importance': message.get('importance', 'normal')
        }

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read"""
        try:
            await self._make_request(
                'PATCH',
                f'/me/messages/{message_id}',
                data={'isRead': True}
            )
            return True

        except Exception as e:
            raise IntegrationError(f"Failed to mark as read: {str(e)}", "Outlook")

    async def mark_as_unread(self, message_id: str) -> bool:
        """Mark email as unread"""
        try:
            await self._make_request(
                'PATCH',
                f'/me/messages/{message_id}',
                data={'isRead': False}
            )
            return True

        except Exception as e:
            raise IntegrationError(f"Failed to mark as unread: {str(e)}", "Outlook")

    async def move_to_folder(self, message_id: str, folder_id: str) -> bool:
        """Move email to a different folder"""
        try:
            await self._make_request(
                'POST',
                f'/me/messages/{message_id}/move',
                data={'destinationId': folder_id}
            )
            return True

        except Exception as e:
            raise IntegrationError(f"Failed to move message: {str(e)}", "Outlook")

    async def create_folder(self, folder_name: str, parent_folder: str = "inbox") -> str:
        """Create a new mail folder"""
        try:
            result = await self._make_request(
                'POST',
                f'/me/mailFolders/{parent_folder}/childFolders',
                data={'displayName': folder_name}
            )

            return result.get('id')

        except Exception as e:
            raise IntegrationError(f"Failed to create folder: {str(e)}", "Outlook")
