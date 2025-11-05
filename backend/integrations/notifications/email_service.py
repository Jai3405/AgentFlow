"""
Email notification service (SMTP-based)
Send email notifications using SMTP
"""

from typing import Dict, List, Optional, Any
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

from integrations.base import BaseNotificationService, AuthenticationError, IntegrationError


class EmailNotificationService(BaseNotificationService):
    """SMTP-based email notification service"""

    def __init__(self):
        super().__init__("EmailNotification")
        self.smtp_server = None
        self.smtp_port = None
        self.from_address = None
        self.smtp_connection = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to SMTP server

        Args:
            credentials: Dict with:
                - smtp_server: SMTP server address
                - smtp_port: SMTP port (default: 587 for TLS)
                - username: SMTP username
                - password: SMTP password
                - from_address: From email address
                - use_tls: Whether to use TLS (default: True)

        Returns:
            True if connection successful
        """
        try:
            self.smtp_server = credentials.get('smtp_server')
            self.smtp_port = credentials.get('smtp_port', 587)
            self.from_address = credentials.get('from_address')
            username = credentials.get('username')
            password = credentials.get('password')
            use_tls = credentials.get('use_tls', True)

            if not all([self.smtp_server, username, password, self.from_address]):
                raise AuthenticationError(
                    "smtp_server, username, password, and from_address are required",
                    "EmailNotification"
                )

            # Test connection
            if use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)

            server.login(username, password)
            server.quit()

            # Store credentials for later use
            self.metadata['smtp_server'] = self.smtp_server
            self.metadata['smtp_port'] = self.smtp_port
            self.metadata['from_address'] = self.from_address
            self.metadata['username'] = username
            self.metadata['password'] = password
            self.metadata['use_tls'] = use_tls

            self._set_connected()

            return True

        except smtplib.SMTPAuthenticationError as e:
            self._set_error(f"SMTP authentication failed: {str(e)}")
            raise AuthenticationError(f"SMTP authentication failed: {str(e)}", "EmailNotification")
        except Exception as e:
            self._set_error(str(e))
            raise IntegrationError(f"Failed to connect to SMTP: {str(e)}", "EmailNotification")

    async def disconnect(self) -> bool:
        """Disconnect from SMTP"""
        self.smtp_connection = None
        self.status = IntegrationStatus.DISCONNECTED
        return True

    async def test_connection(self) -> bool:
        """Test SMTP connection"""
        try:
            use_tls = self.metadata.get('use_tls', True)
            username = self.metadata.get('username')
            password = self.metadata.get('password')

            if use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)

            server.login(username, password)
            server.quit()

            return True

        except Exception:
            self._set_error("Connection test failed")
            return False

    async def send_notification(
        self,
        recipients: List[str],
        message: str,
        title: str = None,
        priority: str = "normal",
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Send email notification

        Args:
            recipients: List of email addresses
            message: Email body
            title: Email subject
            priority: Priority level
            metadata: Additional metadata (attachments, cc, bcc, is_html)

        Returns:
            Dict with notification_id and status
        """
        try:
            subject = title or "Notification from AgentFlow"
            is_html = metadata.get('is_html', False) if metadata else False
            cc = metadata.get('cc', []) if metadata else []
            bcc = metadata.get('bcc', []) if metadata else []
            attachments = metadata.get('attachments', []) if metadata else []

            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_address
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            if cc:
                msg['Cc'] = ', '.join(cc)

            # Set priority headers
            if priority in ["high", "urgent"]:
                msg['X-Priority'] = '1' if priority == "urgent" else '2'
                msg['Importance'] = 'high'

            # Add body
            mime_type = 'html' if is_html else 'plain'
            msg.attach(MIMEText(message, mime_type))

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
                    msg.attach(part)

            # Send email
            use_tls = self.metadata.get('use_tls', True)
            username = self.metadata.get('username')
            password = self.metadata.get('password')

            if use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)

            server.login(username, password)

            # Send to all recipients (including cc and bcc)
            all_recipients = recipients + cc + bcc
            server.send_message(msg, to_addrs=all_recipients)
            server.quit()

            return {
                'notification_id': f"email_{hash(subject)}",
                'status': 'sent',
                'recipients': recipients,
                'cc': cc,
                'bcc': bcc
            }

        except smtplib.SMTPException as e:
            raise IntegrationError(f"SMTP error: {str(e)}", "EmailNotification")
        except Exception as e:
            raise IntegrationError(f"Failed to send email: {str(e)}", "EmailNotification")

    async def get_delivery_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Get delivery status (SMTP doesn't provide tracking)

        Returns basic sent status
        """
        return {
            'notification_id': notification_id,
            'status': 'sent',
            'note': 'SMTP does not provide delivery tracking'
        }

    @classmethod
    def from_env(cls):
        """Create instance from environment variables"""
        service = cls()
        credentials = {
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'username': os.getenv('SMTP_USERNAME'),
            'password': os.getenv('SMTP_PASSWORD'),
            'from_address': os.getenv('SMTP_FROM_ADDRESS'),
            'use_tls': os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        }
        return service, credentials
