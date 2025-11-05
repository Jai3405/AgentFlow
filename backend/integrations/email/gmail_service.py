"""
Gmail API integration service
Provides email monitoring, sending, and management using Gmail API
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GMAIL_AVAILABLE = True
except ImportError:
    GMAIL_AVAILABLE = False
    print("Warning: Google API libraries not installed. Gmail integration disabled.")

from integrations.base import BaseEmailService, AuthenticationError, IntegrationError


class GmailService(BaseEmailService):
    """Gmail API integration for email operations"""

    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',
        'https://www.googleapis.com/auth/gmail.send',
        'https://www.googleapis.com/auth/gmail.modify'
    ]

    def __init__(self):
        super().__init__("Gmail")
        self.service = None
        self.credentials = None
        self.user_email = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to Gmail API

        Args:
            credentials: Dict with either:
                - credentials_file: Path to OAuth credentials JSON
                - token_file: Path to saved token
                - Or pre-authenticated Credentials object

        Returns:
            True if connection successful
        """
        if not GMAIL_AVAILABLE:
            raise IntegrationError(
                "Gmail libraries not installed. Install with: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client",
                "Gmail"
            )

        try:
            creds = None
            token_file = credentials.get('token_file', 'token.json')
            credentials_file = credentials.get('credentials_file', 'credentials.json')

            # Load existing token
            if os.path.exists(token_file):
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)

            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(credentials_file):
                        raise AuthenticationError(
                            f"Credentials file not found: {credentials_file}",
                            "Gmail"
                        )

                    flow = InstalledAppFlow.from_client_secrets_file(
                        credentials_file, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials for next run
                with open(token_file, 'w') as token:
                    token.write(creds.to_json())

            self.credentials = creds
            self.service = build('gmail', 'v1', credentials=creds)

            # Get user's email address
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile.get('emailAddress')

            self._set_connected()
            self.metadata['user_email'] = self.user_email

            return True

        except Exception as e:
            self._set_error(str(e))
            raise IntegrationError(f"Failed to connect to Gmail: {str(e)}", "Gmail")

    async def disconnect(self) -> bool:
        """Disconnect from Gmail API"""
        self.service = None
        self.credentials = None
        self.status = IntegrationStatus.DISCONNECTED
        return True

    async def test_connection(self) -> bool:
        """Test if Gmail connection is still valid"""
        try:
            if not self.service:
                return False

            # Try to get profile
            self.service.users().getProfile(userId='me').execute()
            return True

        except Exception:
            self._set_error("Connection test failed")
            return False

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
        Send an email via Gmail

        Args:
            to: List of recipient email addresses
            subject: Email subject
            body: Email body
            cc: List of CC recipients
            bcc: List of BCC recipients
            attachments: List of dicts with 'filename' and 'content' keys
            is_html: Whether body is HTML

        Returns:
            Dict with message_id and status
        """
        try:
            if not self.service:
                raise IntegrationError("Not connected to Gmail", "Gmail")

            # Create message
            message = MIMEMultipart()
            message['To'] = ', '.join(to)
            message['Subject'] = subject

            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)

            # Add body
            mime_type = 'html' if is_html else 'plain'
            message.attach(MIMEText(body, mime_type))

            # Add attachments
            if attachments:
                for attachment in attachments:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment['content'])
                    encoders.encode_base64(part)
                    part.add_header(
                        'Content-Disposition',
                        f'attachment; filename={attachment["filename"]}'
                    )
                    message.attach(part)

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            # Send message
            sent_message = self.service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()

            return {
                'message_id': sent_message['id'],
                'status': 'sent',
                'thread_id': sent_message.get('threadId'),
                'label_ids': sent_message.get('labelIds', [])
            }

        except HttpError as e:
            raise IntegrationError(f"Gmail API error: {str(e)}", "Gmail", {'error': e.error_details})
        except Exception as e:
            raise IntegrationError(f"Failed to send email: {str(e)}", "Gmail")

    async def fetch_emails(
        self,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        since: datetime = None,
        query: str = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from Gmail

        Args:
            folder: Label to fetch from (INBOX, SENT, etc.)
            limit: Maximum number of emails
            unread_only: Only fetch unread emails
            since: Only fetch emails since this date
            query: Gmail search query

        Returns:
            List of email dicts
        """
        try:
            if not self.service:
                raise IntegrationError("Not connected to Gmail", "Gmail")

            # Build query
            query_parts = []

            if folder:
                query_parts.append(f'label:{folder}')

            if unread_only:
                query_parts.append('is:unread')

            if since:
                date_str = since.strftime('%Y/%m/%d')
                query_parts.append(f'after:{date_str}')

            if query:
                query_parts.append(query)

            search_query = ' '.join(query_parts) if query_parts else None

            # Fetch message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=limit
            ).execute()

            messages = results.get('messages', [])

            # Fetch full message details
            emails = []
            for msg in messages:
                try:
                    message = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()

                    email_data = self._parse_email(message)
                    emails.append(email_data)

                except Exception as e:
                    print(f"Error fetching message {msg['id']}: {e}")
                    continue

            return emails

        except HttpError as e:
            raise IntegrationError(f"Gmail API error: {str(e)}", "Gmail", {'error': e.error_details})
        except Exception as e:
            raise IntegrationError(f"Failed to fetch emails: {str(e)}", "Gmail")

    def _parse_email(self, message: Dict) -> Dict[str, Any]:
        """Parse Gmail API message format to simplified dict"""
        headers = {h['name']: h['value'] for h in message['payload']['headers']}

        # Extract body
        body = self._extract_body(message['payload'])

        # Parse date
        internal_date = int(message.get('internalDate', 0)) / 1000
        date = datetime.fromtimestamp(internal_date) if internal_date else None

        return {
            'id': message['id'],
            'thread_id': message['threadId'],
            'from': headers.get('From', ''),
            'to': headers.get('To', ''),
            'cc': headers.get('Cc', ''),
            'subject': headers.get('Subject', ''),
            'body': body,
            'date': date.isoformat() if date else None,
            'labels': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'is_unread': 'UNREAD' in message.get('labelIds', []),
            'has_attachments': self._has_attachments(message['payload'])
        }

    def _extract_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode()
                elif part['mimeType'] == 'text/html':
                    if 'data' in part['body']:
                        return base64.urlsafe_b64decode(part['body']['data']).decode()
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode()

        return ''

    def _has_attachments(self, payload: Dict) -> bool:
        """Check if message has attachments"""
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('filename'):
                    return True
        return False

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark email as read"""
        try:
            if not self.service:
                raise IntegrationError("Not connected to Gmail", "Gmail")

            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            return True

        except Exception as e:
            raise IntegrationError(f"Failed to mark as read: {str(e)}", "Gmail")

    async def mark_as_unread(self, message_id: str) -> bool:
        """Mark email as unread"""
        try:
            if not self.service:
                raise IntegrationError("Not connected to Gmail", "Gmail")

            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': ['UNREAD']}
            ).execute()

            return True

        except Exception as e:
            raise IntegrationError(f"Failed to mark as unread: {str(e)}", "Gmail")

    async def create_label(self, label_name: str) -> str:
        """Create a new Gmail label"""
        try:
            if not self.service:
                raise IntegrationError("Not connected to Gmail", "Gmail")

            label = {
                'name': label_name,
                'labelListVisibility': 'labelShow',
                'messageListVisibility': 'show'
            }

            created_label = self.service.users().labels().create(
                userId='me',
                body=label
            ).execute()

            return created_label['id']

        except Exception as e:
            raise IntegrationError(f"Failed to create label: {str(e)}", "Gmail")

    async def add_label(self, message_id: str, label_id: str) -> bool:
        """Add label to a message"""
        try:
            if not self.service:
                raise IntegrationError("Not connected to Gmail", "Gmail")

            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'addLabelIds': [label_id]}
            ).execute()

            return True

        except Exception as e:
            raise IntegrationError(f"Failed to add label: {str(e)}", "Gmail")
