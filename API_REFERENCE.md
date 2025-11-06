# AgentFlow API Reference

Complete reference for all 42 API endpoints across 4 phases.

## Table of Contents
- [Conversation API (Phase 1)](#conversation-api)
- [Integration API (Phase 3)](#integration-api)
- [Execution API (Phase 4)](#execution-api)
- [Monitoring API (Phase 4)](#monitoring-api)

---

## Conversation API

### POST /api/chat
Send a message to build workflows conversationally.

**Request**:
```json
{
  "message": "I want to send daily reports via email",
  "conversation_id": null  // or existing ID
}
```

**Response**:
```json
{
  "response": "I'll help you create an email automation workflow...",
  "conversation_id": "conv_123",
  "workflow_progress": 45.5,
  "next_questions": ["Who should receive the emails?"],
  "workflow_preview": {...}
}
```

### GET /api/conversations/{conversation_id}
Get conversation history and state.

### POST /api/workflows/generate/{conversation_id}
Generate final workflow from conversation.

---

## Integration API

### Email Integration

#### POST /api/integrations/email/setup
Setup email integration (Gmail or Outlook).

**Request**:
```json
{
  "integration_type": "gmail",
  "credentials": {
    "token_file": "token.json",
    "credentials_file": "credentials.json"
  }
}
```

#### POST /api/integrations/email/send
Send email via configured provider.

**Request**:
```json
{
  "provider": "gmail",
  "to": ["user@example.com"],
  "subject": "Test Email",
  "body": "Hello from AgentFlow!",
  "cc": [],
  "bcc": [],
  "attachments": []
}
```

#### POST /api/integrations/email/fetch
Fetch emails from configured provider.

**Request**:
```json
{
  "provider": "gmail",
  "folder": "INBOX",
  "limit": 10,
  "filters": {"from": "boss@company.com"}
}
```

### Notification Integration

#### POST /api/integrations/notifications/setup
Setup notification integration (Slack, Email, or SMS).

**Request**:
```json
{
  "integration_type": "slack",
  "credentials": {
    "bot_token": "xoxb-..."
  }
}
```

#### POST /api/integrations/notifications/send
Send notification across channels.

**Request**:
```json
{
  "channels": ["slack", "email", "sms"],
  "message": "Alert message",
  "title": "Important Alert",
  "priority": "high",
  "recipients": {
    "slack": ["#alerts"],
    "email": ["admin@company.com"],
    "sms": ["+1234567890"]
  }
}
```

#### POST /api/integrations/notifications/alert
Send high-priority multi-channel alert.

**Query Params**:
- `message` (string, required)
- `priority` (string, default: "high")
- `channels` (array, optional)
- `recipients` (object, optional)

### Webhook Integration

#### POST /api/integrations/webhooks/setup
Initialize webhook manager.

#### POST /api/integrations/webhooks/register
Register a new webhook.

**Request**:
```json
{
  "url": "https://api.example.com/webhook",
  "events": ["workflow.completed", "workflow.failed"],
  "secret": "my_secret_key",
  "description": "Production webhook"
}
```

**Response**:
```json
{
  "status": "success",
  "webhook_id": "webhook_abc123"
}
```

#### POST /api/integrations/webhooks/trigger
Manually trigger webhook for testing.

**Request**:
```json
{
  "event_type": "workflow.completed",
  "payload": {
    "workflow_id": "wf_123",
    "status": "completed",
    "execution_time": 45.2
  }
}
```

#### GET /api/integrations/webhooks
List all registered webhooks.

#### DELETE /api/integrations/webhooks/{webhook_id}
Unregister a webhook.

### Integration Management

#### GET /api/integrations/status
List all integrations and their status.

**Response**:
```json
{
  "status": "success",
  "count": 5,
  "integrations": [
    {
      "name": "gmail",
      "status": "connected",
      "type": "email",
      "provider": "gmail",
      "connected_at": "2025-11-06T..."
    }
  ]
}
```

#### GET /api/integrations/status/{integration_name}
Get status of specific integration.

#### POST /api/integrations/test/{integration_name}
Test connection for integration.

#### POST /api/integrations/disconnect/{integration_name}
Disconnect specific integration.

#### POST /api/integrations/disconnect-all
Disconnect all integrations.

---

## Execution API

### Workflow Execution

#### POST /api/execution/execute
Execute a workflow immediately.

**Request**:
```json
{
  "workflow_id": "my_workflow",
  "workflow_spec": {
    "steps": [
      {
        "id": "step1",
        "type": "email",
        "config": {
          "action": "send",
          "provider": "gmail",
          "to": ["user@example.com"],
          "subject": "Test",
          "body": "Hello!"
        }
      }
    ]
  },
  "input_data": {"user_name": "John"},
  "async_execution": false
}
```

**Response (Sync)**:
```json
{
  "status": "completed",
  "execution": {
    "execution_id": "exec_123",
    "workflow_id": "my_workflow",
    "status": "completed",
    "progress": 1.0,
    "execution_time": 2.5,
    "started_at": "2025-11-06T...",
    "completed_at": "2025-11-06T...",
    "completed_steps": ["step1"],
    "step_outputs": {...},
    "logs": [...]
  }
}
```

**Response (Async)**:
```json
{
  "status": "started",
  "execution_id": "exec_123",
  "message": "Workflow execution started in background"
}
```

#### GET /api/execution/status/{execution_id}
Get real-time status of running execution.

**Response**:
```json
{
  "execution_id": "exec_123",
  "workflow_id": "my_workflow",
  "status": "running",
  "current_step": "step2",
  "progress": 0.5,
  "execution_time": 5.2,
  "completed_steps_count": 1,
  "failed_steps_count": 0
}
```

#### GET /api/execution/active
List all currently active executions.

#### POST /api/execution/cancel/{execution_id}
Cancel a running execution.

#### POST /api/execution/pause/{execution_id}
Pause a running execution.

#### POST /api/execution/resume/{execution_id}
Resume a paused execution.

#### POST /api/execution/validate
Validate workflow specification before execution.

**Request**:
```json
{
  "steps": [...]
}
```

**Response**:
```json
{
  "status": "success",
  "validation": {
    "valid": true,
    "errors": [],
    "warnings": ["Step 2 has no config field"]
  }
}
```

### Workflow Scheduling

#### POST /api/execution/schedule
Schedule workflow for recurring execution.

**Cron Schedule**:
```json
{
  "workflow_id": "daily_report",
  "workflow_spec": {...},
  "schedule_type": "cron",
  "schedule_config": {
    "expression": "0 9 * * *"  // Daily at 9 AM
  },
  "input_data": {}
}
```

**Interval Schedule**:
```json
{
  "workflow_id": "hourly_check",
  "workflow_spec": {...},
  "schedule_type": "interval",
  "schedule_config": {
    "hours": 1,
    "minutes": 0
  }
}
```

**One-time Schedule**:
```json
{
  "workflow_id": "future_task",
  "workflow_spec": {...},
  "schedule_type": "once",
  "schedule_config": {
    "time": "2025-12-01T10:00:00"
  }
}
```

**Response**:
```json
{
  "status": "success",
  "job": {
    "job_id": "job_abc123",
    "workflow_id": "daily_report",
    "schedule_type": "cron",
    "enabled": true,
    "next_execution": "2025-11-07T09:00:00",
    "last_execution": null,
    "execution_count": 0
  }
}
```

#### GET /api/execution/schedule
List all scheduled jobs.

**Query Params**:
- `workflow_id` (optional) - Filter by workflow

#### GET /api/execution/schedule/{job_id}
Get details of scheduled job.

#### PUT /api/execution/schedule/{job_id}
Update scheduled job.

**Request**:
```json
{
  "enabled": false,
  "schedule_config": {
    "expression": "0 10 * * *"  // Change to 10 AM
  }
}
```

#### DELETE /api/execution/schedule/{job_id}
Remove scheduled job.

#### POST /api/execution/schedule/{job_id}/enable
Enable a disabled job.

#### POST /api/execution/schedule/{job_id}/disable
Disable a job without deleting it.

#### GET /api/execution/schedule/upcoming
Get upcoming scheduled executions.

**Query Params**:
- `limit` (int, default: 10)

**Response**:
```json
{
  "status": "success",
  "count": 5,
  "upcoming": [
    {
      "job_id": "job_123",
      "workflow_id": "daily_report",
      "next_execution": "2025-11-07T09:00:00",
      "schedule_type": "cron"
    }
  ]
}
```

#### GET /api/execution/schedule/history
Get execution history for scheduled jobs.

**Query Params**:
- `job_id` (optional) - Filter by job

### Scheduler Control

#### POST /api/execution/scheduler/start
Start the background scheduler.

#### POST /api/execution/scheduler/stop
Stop the background scheduler.

#### GET /api/execution/scheduler/status
Get scheduler status.

**Response**:
```json
{
  "status": "success",
  "running": true,
  "active_jobs": 12
}
```

---

## Monitoring API

### GET /api/monitoring/metrics/{workflow_id}
Get comprehensive metrics for a workflow.

**Response**:
```json
{
  "status": "success",
  "metrics": {
    "workflow_id": "my_workflow",
    "total_executions": 150,
    "successful_executions": 145,
    "failed_executions": 5,
    "success_rate": 96.67,
    "avg_execution_time_seconds": 3.45,
    "last_execution": "2025-11-06T...",
    "top_errors": {
      "email_send_error": 3,
      "database_timeout": 2
    }
  }
}
```

### GET /api/monitoring/metrics
Get overall system-wide metrics.

**Response**:
```json
{
  "status": "success",
  "metrics": {
    "total_workflows": 25,
    "total_executions": 1523,
    "successful_executions": 1450,
    "failed_executions": 73,
    "success_rate": 95.21,
    "avg_execution_time_seconds": 4.12,
    "most_active_workflows": [
      {"workflow_id": "daily_report", "executions": 365}
    ],
    "error_prone_workflows": [
      {"workflow_id": "api_sync", "error_rate": 12.5}
    ]
  }
}
```

### GET /api/monitoring/trends
Get execution trends over time.

**Query Params**:
- `workflow_id` (optional) - Filter by workflow
- `time_window_hours` (int, default: 24) - Time window

**Response**:
```json
{
  "status": "success",
  "trends": {
    "time_window_hours": 24,
    "total_executions": 48,
    "trends": [
      {
        "timestamp": "2025-11-06T00:00:00",
        "total": 5,
        "successful": 5,
        "failed": 0,
        "avg_duration": 3.2
      }
    ]
  }
}
```

### GET /api/monitoring/performance/{workflow_id}
Get step-level performance analysis.

**Response**:
```json
{
  "status": "success",
  "performance": {
    "workflow_id": "my_workflow",
    "total_executions": 100,
    "step_metrics": {
      "send_email": {
        "total_attempts": 100,
        "completions": 98,
        "failures": 2,
        "completion_rate": 98.0
      }
    }
  }
}
```

### GET /api/monitoring/errors
Get error analysis.

**Query Params**:
- `workflow_id` (optional) - Filter by workflow
- `limit` (int, default: 10) - Max errors to return

**Response**:
```json
{
  "status": "success",
  "analysis": {
    "total_failures": 25,
    "unique_errors": 8,
    "top_errors": [
      {
        "error": "send_email: Connection timeout",
        "frequency": 12,
        "examples": [
          {
            "execution_id": "exec_123",
            "timestamp": "2025-11-06T...",
            "full_error": "..."
          }
        ]
      }
    ]
  }
}
```

### GET /api/monitoring/summary/{workflow_id}
Get comprehensive performance summary.

Combines metrics, step performance, errors, and recent executions.

### DELETE /api/monitoring/history
Clear execution history.

**Query Params**:
- `workflow_id` (optional) - Clear specific workflow only

### GET /api/monitoring/health
Get system health status.

**Response**:
```json
{
  "status": "success",
  "health": {
    "status": "healthy",  // healthy, degraded, unhealthy
    "success_rate": 96.5,
    "total_executions": 1523,
    "failed_executions": 53,
    "active_workflows": 25
  }
}
```

---

## Error Responses

All endpoints return consistent error format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

**HTTP Status Codes**:
- `200` - Success
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (invalid API key)
- `404` - Not Found
- `500` - Internal Server Error

---

## Authentication

Currently, no authentication is required for local development.

For production, implement API key authentication:

```python
# Add to headers
headers = {
    "X-API-Key": "your_api_key_here"
}
```

---

## Rate Limiting

No rate limiting in development.

For production, recommended limits:
- 100 requests/minute for execution endpoints
- 1000 requests/minute for monitoring endpoints

---

## Webhooks

When webhooks are triggered, AgentFlow sends POST requests with:

**Headers**:
```
Content-Type: application/json
X-Webhook-Signature: <HMAC-SHA256 signature>
X-Webhook-Event: <event_type>
```

**Payload**:
```json
{
  "event_type": "workflow.completed",
  "timestamp": "2025-11-06T...",
  "data": {
    "workflow_id": "...",
    "execution_id": "...",
    "status": "completed",
    ...
  }
}
```

**Verify Signature** (if secret provided):
```python
import hmac
import hashlib

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

---

## Step Types Reference

### 1. Email
```json
{
  "type": "email",
  "config": {
    "action": "send",  // or "fetch"
    "provider": "gmail",  // or "outlook"
    "to": ["user@example.com"],
    "subject": "Subject",
    "body": "Body",
    "cc": [],
    "bcc": [],
    "attachments": []
  }
}
```

### 2. Notification
```json
{
  "type": "notification",
  "config": {
    "channels": ["slack", "email", "sms"],
    "message": "Alert message",
    "title": "Title",
    "priority": "normal",  // normal, high, urgent
    "recipients": {
      "slack": ["#channel"],
      "email": ["user@example.com"],
      "sms": ["+1234567890"]
    }
  }
}
```

### 3. Webhook
```json
{
  "type": "webhook",
  "config": {
    "event_type": "custom.event",
    "payload": {"key": "value"}
  }
}
```

### 4. Database Read
```json
{
  "type": "database_read",
  "config": {
    "database_type": "postgresql",  // mysql, mongodb
    "database_name": "mydb",
    "table": "users",  // or "collection" for MongoDB
    "columns": ["id", "name"],
    "limit": 100,
    "where": "active = true",
    "credentials": {...}
  }
}
```

### 5. Database Write
```json
{
  "type": "database_write",
  "config": {
    "database_type": "postgresql",
    "database_name": "mydb",
    "table": "users",
    "action": "insert",  // update, delete
    "data": [...],  // or "$previous_step"
    "credentials": {...}
  }
}
```

### 6. File Process
```json
{
  "type": "file_process",
  "config": {
    "file_type": "csv",  // json, excel
    "action": "read",  // write, transform
    "file_path": "/path/to/file.csv"
  }
}
```

### 7. Transform
```json
{
  "type": "transform",
  "config": {
    "type": "map",  // filter, aggregate
    "input": "$previous_step",
    "mapping": {"new_field": "old_field"}
  }
}
```

### 8. Condition
```json
{
  "type": "condition",
  "config": {
    "condition": {
      "field": "count",
      "operator": "greater_than",
      "value": 10
    }
  },
  "branches": {
    "true": [...],
    "false": [...]
  }
}
```

### 9. Loop
```json
{
  "type": "loop",
  "config": {
    "items": "$previous_step"  // or array
  },
  "loop_steps": [...]
}
```

### 10. Delay
```json
{
  "type": "delay",
  "config": {
    "duration": 5  // seconds
  }
}
```

### 11. Script
```json
{
  "type": "script",
  "config": {
    "script": "context.get_variable('count') * 2"
  }
}
```

---

## Variable Interpolation

Use `{{variable}}` to insert variables:

```json
{
  "body": "Hello {{user_name}}, you have {{count}} new messages"
}
```

Reference previous step outputs with `$step_id`:

```json
{
  "input": "$fetch_users"
}
```

---

For interactive API testing, visit: **http://localhost:8000/docs**
