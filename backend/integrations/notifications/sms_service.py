"""
SMS notification service using Twilio
Send SMS notifications via Twilio API
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    print("Warning: Twilio library not installed. SMS integration disabled.")

from integrations.base import BaseNotificationService, AuthenticationError, IntegrationError


class SMSService(BaseNotificationService):
    """Twilio-based SMS notification service"""

    def __init__(self):
        super().__init__("SMS")
        self.client = None
        self.from_number = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to Twilio API

        Args:
            credentials: Dict with:
                - account_sid: Twilio account SID
                - auth_token: Twilio auth token
                - from_number: Twilio phone number to send from

        Returns:
            True if connection successful
        """
        if not TWILIO_AVAILABLE:
            raise IntegrationError(
                "Twilio library not installed. Install with: pip install twilio",
                "SMS"
            )

        try:
            account_sid = credentials.get('account_sid')
            auth_token = credentials.get('auth_token')
            self.from_number = credentials.get('from_number')

            if not all([account_sid, auth_token, self.from_number]):
                raise AuthenticationError(
                    "account_sid, auth_token, and from_number are required",
                    "SMS"
                )

            # Create Twilio client
            self.client = Client(account_sid, auth_token)

            # Test authentication by fetching account info
            account = self.client.api.accounts(account_sid).fetch()

            self._set_connected()
            self.metadata['account_sid'] = account_sid
            self.metadata['from_number'] = self.from_number
            self.metadata['account_status'] = account.status

            return True

        except TwilioRestException as e:
            self._set_error(f"Twilio error: {e.msg}")
            raise AuthenticationError(f"Twilio authentication failed: {e.msg}", "SMS")
        except Exception as e:
            self._set_error(str(e))
            raise IntegrationError(f"Failed to connect to Twilio: {str(e)}", "SMS")

    async def disconnect(self) -> bool:
        """Disconnect from Twilio"""
        self.client = None
        self.from_number = None
        self.status = IntegrationStatus.DISCONNECTED
        return True

    async def test_connection(self) -> bool:
        """Test Twilio connection"""
        try:
            if not self.client:
                return False

            # Try to fetch account info
            account_sid = self.metadata.get('account_sid')
            self.client.api.accounts(account_sid).fetch()

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
        Send SMS notification

        Args:
            recipients: List of phone numbers (E.164 format: +1234567890)
            message: SMS message text
            title: Optional title (prepended to message)
            priority: Priority level
            metadata: Additional metadata (media_url for MMS)

        Returns:
            Dict with notification_id and status
        """
        try:
            if not self.client:
                raise IntegrationError("Not connected to Twilio", "SMS")

            # Prepend title if provided
            full_message = f"{title}\n\n{message}" if title else message

            # Truncate if too long (SMS limit is 1600 chars for concatenated messages)
            if len(full_message) > 1600:
                full_message = full_message[:1597] + "..."

            # Add priority indicator for high/urgent
            if priority in ["high", "urgent"]:
                priority_indicator = "🚨 URGENT: " if priority == "urgent" else "⚠️ HIGH PRIORITY: "
                full_message = priority_indicator + full_message

            results = []
            media_url = metadata.get('media_url') if metadata else None

            # Send to each recipient
            for phone_number in recipients:
                try:
                    # Validate phone number format
                    if not phone_number.startswith('+'):
                        phone_number = '+' + phone_number.lstrip('0')

                    # Send SMS (or MMS if media_url provided)
                    twilio_message = self.client.messages.create(
                        body=full_message,
                        from_=self.from_number,
                        to=phone_number,
                        media_url=[media_url] if media_url else None
                    )

                    results.append({
                        'phone_number': phone_number,
                        'message_sid': twilio_message.sid,
                        'status': twilio_message.status,
                        'price': twilio_message.price,
                        'error_code': twilio_message.error_code,
                        'error_message': twilio_message.error_message
                    })

                except TwilioRestException as e:
                    results.append({
                        'phone_number': phone_number,
                        'error': e.msg,
                        'error_code': e.code,
                        'status': 'failed'
                    })

            return {
                'notification_id': results[0]['message_sid'] if results and 'message_sid' in results[0] else None,
                'status': 'sent' if any('message_sid' in r for r in results) else 'failed',
                'recipients': results
            }

        except Exception as e:
            raise IntegrationError(f"Failed to send SMS: {str(e)}", "SMS")

    async def get_delivery_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Get delivery status of an SMS

        Args:
            notification_id: Twilio message SID

        Returns:
            Dict with status information
        """
        try:
            if not self.client:
                raise IntegrationError("Not connected to Twilio", "SMS")

            message = self.client.messages(notification_id).fetch()

            return {
                'notification_id': notification_id,
                'status': message.status,
                'to': message.to,
                'from': message.from_,
                'date_sent': message.date_sent.isoformat() if message.date_sent else None,
                'date_updated': message.date_updated.isoformat() if message.date_updated else None,
                'price': message.price,
                'price_unit': message.price_unit,
                'error_code': message.error_code,
                'error_message': message.error_message
            }

        except TwilioRestException as e:
            return {
                'notification_id': notification_id,
                'status': 'error',
                'error': e.msg
            }
        except Exception as e:
            raise IntegrationError(f"Failed to get delivery status: {str(e)}", "SMS")

    async def send_bulk_sms(
        self,
        recipients: List[str],
        message: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Send SMS to multiple recipients in batches

        Args:
            recipients: List of phone numbers
            message: SMS message
            batch_size: Number of messages to send per batch

        Returns:
            Dict with overall status
        """
        try:
            if not self.client:
                raise IntegrationError("Not connected to Twilio", "SMS")

            all_results = []
            total_sent = 0
            total_failed = 0

            # Process in batches
            for i in range(0, len(recipients), batch_size):
                batch = recipients[i:i+batch_size]

                result = await self.send_notification(
                    recipients=batch,
                    message=message
                )

                all_results.extend(result['recipients'])

                # Count successes and failures
                for r in result['recipients']:
                    if 'message_sid' in r:
                        total_sent += 1
                    else:
                        total_failed += 1

            return {
                'total_recipients': len(recipients),
                'total_sent': total_sent,
                'total_failed': total_failed,
                'status': 'completed',
                'details': all_results
            }

        except Exception as e:
            raise IntegrationError(f"Failed to send bulk SMS: {str(e)}", "SMS")

    @classmethod
    def from_env(cls):
        """Create instance from environment variables"""
        service = cls()
        credentials = {
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID'),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN'),
            'from_number': os.getenv('TWILIO_FROM_NUMBER')
        }
        return service, credentials
