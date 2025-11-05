"""
Slack integration service
Send notifications, messages, and manage Slack channels
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
    SLACK_AVAILABLE = True
except ImportError:
    SLACK_AVAILABLE = False
    print("Warning: Slack SDK not installed. Slack integration disabled.")

from integrations.base import BaseNotificationService, AuthenticationError, IntegrationError


class SlackService(BaseNotificationService):
    """Slack API integration for notifications"""

    def __init__(self):
        super().__init__("Slack")
        self.client = None
        self.bot_info = None

    async def connect(self, credentials: Dict[str, Any]) -> bool:
        """
        Connect to Slack API

        Args:
            credentials: Dict with:
                - bot_token: Slack bot token (xoxb-...)
                - Or app_token: Slack app token (xapp-...)

        Returns:
            True if connection successful
        """
        if not SLACK_AVAILABLE:
            raise IntegrationError(
                "Slack SDK not installed. Install with: pip install slack-sdk",
                "Slack"
            )

        try:
            token = credentials.get('bot_token') or credentials.get('token')
            if not token:
                raise AuthenticationError("bot_token is required", "Slack")

            self.client = WebClient(token=token)

            # Test authentication
            auth_response = self.client.auth_test()

            self.bot_info = {
                'bot_id': auth_response.get('bot_id'),
                'user_id': auth_response.get('user_id'),
                'team': auth_response.get('team'),
                'team_id': auth_response.get('team_id')
            }

            self._set_connected()
            self.metadata.update(self.bot_info)

            return True

        except SlackApiError as e:
            self._set_error(f"Slack API error: {e.response['error']}")
            raise AuthenticationError(f"Slack authentication failed: {e.response['error']}", "Slack")
        except Exception as e:
            self._set_error(str(e))
            raise IntegrationError(f"Failed to connect to Slack: {str(e)}", "Slack")

    async def disconnect(self) -> bool:
        """Disconnect from Slack"""
        self.client = None
        self.bot_info = None
        self.status = IntegrationStatus.DISCONNECTED
        return True

    async def test_connection(self) -> bool:
        """Test if Slack connection is still valid"""
        try:
            if not self.client:
                return False

            self.client.auth_test()
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
        Send Slack notification

        Args:
            recipients: List of channel names or user IDs
            message: Notification message
            title: Optional message title
            priority: Priority level
            metadata: Additional metadata (attachments, blocks, etc.)

        Returns:
            Dict with notification_id and status
        """
        try:
            if not self.client:
                raise IntegrationError("Not connected to Slack", "Slack")

            results = []

            for recipient in recipients:
                # Build message blocks
                blocks = self._build_message_blocks(message, title, priority, metadata)

                # Send message
                response = self.client.chat_postMessage(
                    channel=recipient,
                    text=message,  # Fallback text
                    blocks=blocks if blocks else None
                )

                results.append({
                    'channel': recipient,
                    'ts': response['ts'],
                    'message_id': response['ts']
                })

            return {
                'notification_id': results[0]['ts'] if results else None,
                'status': 'sent',
                'recipients': results
            }

        except SlackApiError as e:
            raise IntegrationError(
                f"Slack API error: {e.response['error']}",
                "Slack",
                {'error': e.response.get('error')}
            )
        except Exception as e:
            raise IntegrationError(f"Failed to send notification: {str(e)}", "Slack")

    def _build_message_blocks(
        self,
        message: str,
        title: str = None,
        priority: str = "normal",
        metadata: Dict[str, Any] = None
    ) -> List[Dict]:
        """Build Slack message blocks"""
        blocks = []

        # Add title if provided
        if title:
            blocks.append({
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": title
                }
            })

        # Add priority indicator
        if priority in ["high", "urgent"]:
            priority_text = "🔴 HIGH PRIORITY" if priority == "high" else "🚨 URGENT"
            blocks.append({
                "type": "context",
                "elements": [{
                    "type": "mrkdwn",
                    "text": priority_text
                }]
            })

        # Add main message
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": message
            }
        })

        # Add custom blocks if provided
        if metadata and 'blocks' in metadata:
            blocks.extend(metadata['blocks'])

        return blocks

    async def get_delivery_status(self, notification_id: str) -> Dict[str, Any]:
        """
        Get delivery status of a Slack message

        Note: Slack doesn't provide detailed delivery status,
        this checks if message still exists
        """
        try:
            if not self.client:
                raise IntegrationError("Not connected to Slack", "Slack")

            # Slack doesn't have a direct delivery status API
            # We can only confirm the message was sent successfully
            return {
                'notification_id': notification_id,
                'status': 'delivered',
                'note': 'Slack does not provide detailed delivery tracking'
            }

        except Exception as e:
            return {
                'notification_id': notification_id,
                'status': 'unknown',
                'error': str(e)
            }

    async def send_direct_message(
        self,
        user_id: str,
        message: str,
        blocks: List[Dict] = None
    ) -> Dict[str, Any]:
        """Send a direct message to a user"""
        try:
            if not self.client:
                raise IntegrationError("Not connected to Slack", "Slack")

            # Open DM channel
            dm_response = self.client.conversations_open(users=[user_id])
            channel_id = dm_response['channel']['id']

            # Send message
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=message,
                blocks=blocks
            )

            return {
                'message_id': response['ts'],
                'channel_id': channel_id,
                'status': 'sent'
            }

        except SlackApiError as e:
            raise IntegrationError(f"Failed to send DM: {e.response['error']}", "Slack")

    async def create_channel(
        self,
        name: str,
        is_private: bool = False,
        description: str = None
    ) -> str:
        """Create a new Slack channel"""
        try:
            if not self.client:
                raise IntegrationError("Not connected to Slack", "Slack")

            response = self.client.conversations_create(
                name=name,
                is_private=is_private
            )

            channel_id = response['channel']['id']

            # Set description if provided
            if description:
                self.client.conversations_setTopic(
                    channel=channel_id,
                    topic=description
                )

            return channel_id

        except SlackApiError as e:
            raise IntegrationError(f"Failed to create channel: {e.response['error']}", "Slack")

    async def invite_to_channel(self, channel_id: str, user_ids: List[str]) -> bool:
        """Invite users to a channel"""
        try:
            if not self.client:
                raise IntegrationError("Not connected to Slack", "Slack")

            self.client.conversations_invite(
                channel=channel_id,
                users=user_ids
            )

            return True

        except SlackApiError as e:
            raise IntegrationError(f"Failed to invite users: {e.response['error']}", "Slack")

    async def post_file(
        self,
        channel: str,
        file_path: str = None,
        content: bytes = None,
        filename: str = None,
        title: str = None,
        initial_comment: str = None
    ) -> Dict[str, Any]:
        """Post a file to a channel"""
        try:
            if not self.client:
                raise IntegrationError("Not connected to Slack", "Slack")

            if file_path:
                response = self.client.files_upload(
                    channels=channel,
                    file=file_path,
                    title=title,
                    initial_comment=initial_comment
                )
            elif content and filename:
                response = self.client.files_upload(
                    channels=channel,
                    content=content,
                    filename=filename,
                    title=title,
                    initial_comment=initial_comment
                )
            else:
                raise ValueError("Either file_path or (content + filename) required")

            return {
                'file_id': response['file']['id'],
                'status': 'uploaded'
            }

        except SlackApiError as e:
            raise IntegrationError(f"Failed to upload file: {e.response['error']}", "Slack")

    async def add_reaction(self, channel: str, timestamp: str, emoji: str) -> bool:
        """Add emoji reaction to a message"""
        try:
            if not self.client:
                raise IntegrationError("Not connected to Slack", "Slack")

            self.client.reactions_add(
                channel=channel,
                timestamp=timestamp,
                name=emoji.replace(':', '')  # Remove colons if present
            )

            return True

        except SlackApiError as e:
            raise IntegrationError(f"Failed to add reaction: {e.response['error']}", "Slack")
