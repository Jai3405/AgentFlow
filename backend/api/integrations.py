"""
FastAPI endpoints for integration management
Handles email, notification, and webhook integrations
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from integrations.integration_manager import IntegrationManager
from integrations.base import IntegrationError, AuthenticationError
from database.base import get_db

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Global integration manager instance
integration_manager = IntegrationManager()


# Request/Response Models

class IntegrationCredentials(BaseModel):
    """Credentials for integration setup"""
    bot_token: Optional[str] = None  # Slack
    token: Optional[str] = None  # Generic token
    token_file: Optional[str] = None  # Gmail OAuth token file
    credentials_file: Optional[str] = None  # Gmail OAuth credentials
    client_id: Optional[str] = None  # Outlook/MSAL
    client_secret: Optional[str] = None  # Outlook/MSAL
    tenant_id: Optional[str] = None  # Outlook/MSAL
    smtp_server: Optional[str] = None  # Email notifications
    smtp_port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    from_address: Optional[str] = None
    account_sid: Optional[str] = None  # Twilio
    auth_token: Optional[str] = None  # Twilio
    from_number: Optional[str] = None  # Twilio


class SetupIntegrationRequest(BaseModel):
    """Request to setup an integration"""
    integration_type: str = Field(..., description="Type of integration (gmail, outlook, slack, email_notifications, sms)")
    credentials: IntegrationCredentials


class SendEmailRequest(BaseModel):
    """Request to send email"""
    provider: str = Field(..., description="Email provider (gmail or outlook)")
    to: List[str]
    subject: str
    body: str
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    attachments: Optional[List[Dict[str, Any]]] = None


class FetchEmailsRequest(BaseModel):
    """Request to fetch emails"""
    provider: str = Field(..., description="Email provider (gmail or outlook)")
    folder: str = "INBOX"
    limit: int = Field(10, ge=1, le=100)
    filters: Optional[Dict[str, Any]] = None


class SendNotificationRequest(BaseModel):
    """Request to send notification"""
    channels: List[str] = Field(..., description="List of channels (slack, email, sms)")
    message: str
    title: Optional[str] = None
    priority: str = Field("normal", description="Priority level (normal, high, urgent)")
    recipients: Dict[str, List[str]] = Field(..., description="Recipients per channel")


class RegisterWebhookRequest(BaseModel):
    """Request to register webhook"""
    url: str
    events: List[str]
    secret: Optional[str] = None
    description: Optional[str] = None


class TriggerWebhookRequest(BaseModel):
    """Request to trigger webhook"""
    event_type: str
    payload: Dict[str, Any]


# Email Integration Endpoints

@router.post("/email/setup")
async def setup_email_integration(request: SetupIntegrationRequest):
    """
    Setup email integration (Gmail or Outlook)

    **Gmail requires:**
    - token_file: Path to OAuth token file
    - credentials_file: Path to OAuth credentials file

    **Outlook requires:**
    - client_id: Azure AD application client ID
    - client_secret: Azure AD application client secret
    - tenant_id: Azure AD tenant ID
    """
    try:
        credentials = request.credentials.model_dump(exclude_none=True)

        if request.integration_type == "gmail":
            success = await integration_manager.setup_gmail(credentials)
        elif request.integration_type == "outlook":
            success = await integration_manager.setup_outlook(credentials)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown email integration type: {request.integration_type}")

        if success:
            return {
                "status": "success",
                "message": f"{request.integration_type.capitalize()} integration setup successfully",
                "integration": integration_manager.get_integration_status(request.integration_type)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to setup integration")

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/email/send")
async def send_email(request: SendEmailRequest):
    """
    Send email via configured provider

    Requires the email provider to be set up first via /email/setup
    """
    try:
        result = await integration_manager.send_email(
            provider=request.provider,
            to=request.to,
            subject=request.subject,
            body=request.body,
            cc=request.cc,
            bcc=request.bcc,
            attachments=request.attachments
        )

        return {
            "status": "success",
            "message": "Email sent successfully",
            "data": result
        }

    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")


@router.post("/email/fetch")
async def fetch_emails(request: FetchEmailsRequest):
    """
    Fetch emails from configured provider

    Requires the email provider to be set up first via /email/setup
    """
    try:
        emails = await integration_manager.fetch_emails(
            provider=request.provider,
            folder=request.folder,
            limit=request.limit,
            filters=request.filters
        )

        return {
            "status": "success",
            "count": len(emails),
            "emails": emails
        }

    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch emails: {str(e)}")


# Notification Integration Endpoints

@router.post("/notifications/setup")
async def setup_notification_integration(request: SetupIntegrationRequest):
    """
    Setup notification integration (Slack, Email, or SMS)

    **Slack requires:**
    - bot_token: Slack bot token (xoxb-...)

    **Email notifications require:**
    - smtp_server: SMTP server address
    - smtp_port: SMTP port
    - username: SMTP username
    - password: SMTP password
    - from_address: Sender email address

    **SMS requires:**
    - account_sid: Twilio account SID
    - auth_token: Twilio auth token
    - from_number: Twilio phone number
    """
    try:
        credentials = request.credentials.model_dump(exclude_none=True)

        if request.integration_type == "slack":
            success = await integration_manager.setup_slack(credentials)
        elif request.integration_type == "email_notifications":
            success = await integration_manager.setup_email_notifications(credentials)
        elif request.integration_type == "sms":
            success = await integration_manager.setup_sms(credentials)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown notification type: {request.integration_type}")

        if success:
            return {
                "status": "success",
                "message": f"{request.integration_type.capitalize()} integration setup successfully",
                "integration": integration_manager.get_integration_status(request.integration_type)
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to setup integration")

    except AuthenticationError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/notifications/send")
async def send_notification(request: SendNotificationRequest):
    """
    Send notification across multiple channels

    Requires notification integrations to be set up first via /notifications/setup

    **Example recipients:**
    ```json
    {
      "slack": ["#general", "#alerts"],
      "email": ["user@example.com", "admin@example.com"],
      "sms": ["+11234567890"]
    }
    ```
    """
    try:
        result = await integration_manager.send_notification(
            channels=request.channels,
            message=request.message,
            title=request.title,
            priority=request.priority,
            recipients=request.recipients
        )

        return {
            "status": "success",
            "message": "Notification sent",
            "results": result
        }

    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send notification: {str(e)}")


@router.post("/notifications/alert")
async def send_multi_channel_alert(
    message: str,
    priority: str = "high",
    channels: Optional[List[str]] = None,
    recipients: Optional[Dict[str, List[str]]] = None
):
    """
    Send high-priority alert across all configured notification channels

    If channels not specified, uses all available notification integrations
    """
    try:
        result = await integration_manager.send_multi_channel_alert(
            message=message,
            priority=priority,
            channels=channels,
            recipients=recipients or {}
        )

        return {
            "status": "success",
            "message": "Alert sent",
            "results": result
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")


# Webhook Endpoints

@router.post("/webhooks/setup")
async def setup_webhooks():
    """Initialize webhook manager"""
    try:
        success = await integration_manager.setup_webhooks()

        if success:
            return {
                "status": "success",
                "message": "Webhook manager initialized",
                "integration": integration_manager.get_integration_status("webhooks")
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to setup webhooks")

    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/webhooks/register")
async def register_webhook(request: RegisterWebhookRequest):
    """
    Register a new webhook

    **Supported event types:**
    - workflow.created
    - workflow.updated
    - workflow.executed
    - workflow.completed
    - workflow.failed
    - email.received
    - data.updated
    - approval.requested
    - approval.approved
    - approval.rejected
    """
    try:
        webhook_id = integration_manager.register_webhook(
            url=request.url,
            events=request.events,
            secret=request.secret,
            description=request.description
        )

        return {
            "status": "success",
            "message": "Webhook registered successfully",
            "webhook_id": webhook_id
        }

    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to register webhook: {str(e)}")


@router.post("/webhooks/trigger")
async def trigger_webhook(request: TriggerWebhookRequest):
    """
    Manually trigger webhook for testing or workflow automation
    """
    try:
        result = await integration_manager.trigger_webhook(
            event_type=request.event_type,
            payload=request.payload
        )

        return {
            "status": "success",
            "message": "Webhook triggered",
            "results": result
        }

    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger webhook: {str(e)}")


@router.get("/webhooks")
async def list_webhooks():
    """List all registered webhooks"""
    try:
        webhooks = integration_manager.list_webhooks()

        return {
            "status": "success",
            "count": len(webhooks),
            "webhooks": webhooks
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list webhooks: {str(e)}")


@router.delete("/webhooks/{webhook_id}")
async def unregister_webhook(webhook_id: str):
    """Unregister a webhook"""
    try:
        success = integration_manager.unregister_webhook(webhook_id)

        if success:
            return {
                "status": "success",
                "message": f"Webhook {webhook_id} unregistered"
            }
        else:
            raise HTTPException(status_code=404, detail="Webhook not found")

    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unregister webhook: {str(e)}")


# Integration Status and Management Endpoints

@router.get("/status")
async def list_integrations():
    """List all integrations and their status"""
    try:
        integrations = integration_manager.list_integrations()

        return {
            "status": "success",
            "count": len(integrations),
            "integrations": integrations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list integrations: {str(e)}")


@router.get("/status/{integration_name}")
async def get_integration_status(integration_name: str):
    """Get status of a specific integration"""
    try:
        status = integration_manager.get_integration_status(integration_name)

        return {
            "status": "success",
            "integration": status
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get integration status: {str(e)}")


@router.post("/test/{integration_name}")
async def test_integration(integration_name: str):
    """Test connection for a specific integration"""
    try:
        result = await integration_manager.test_integration(integration_name)

        return {
            "status": "success",
            "integration": integration_name,
            "connection_test": "passed" if result else "failed"
        }

    except IntegrationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to test integration: {str(e)}")


@router.post("/disconnect/{integration_name}")
async def disconnect_integration(integration_name: str):
    """Disconnect a specific integration"""
    try:
        success = await integration_manager.disconnect_integration(integration_name)

        if success:
            return {
                "status": "success",
                "message": f"Integration '{integration_name}' disconnected"
            }
        else:
            raise HTTPException(status_code=404, detail="Integration not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect integration: {str(e)}")


@router.post("/disconnect-all")
async def disconnect_all_integrations():
    """Disconnect all integrations"""
    try:
        results = await integration_manager.disconnect_all()

        return {
            "status": "success",
            "message": "All integrations disconnected",
            "results": results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect all integrations: {str(e)}")
