# Notification and Alert Engine

## Overview

The Notification and Alert Engine provides persistent, user-specific alerts
for fraud detection, investigation workflows, case escalation, and report
generation.

The subsystem supports:

- In-application notifications
- Email notification abstraction
- Domain-event-driven notification creation
- Read and unread state
- Delivery status tracking
- Retry scheduling
- Expiration
- Soft deletion and restoration
- Bulk operations
- Notification statistics
- Role-restricted administrative actions

## Architecture

```text
Fraud / Case / Report Service
            |
            v
      Domain Event Bus
            |
            v
 Notification Event Handler
            |
            v
   Notification Service
            |
            v
 Notification Repository
            |
            v
       PostgreSQL
```

Email delivery follows this flow:

```text
Notification Email Service
            |
            v
       Email Sender
       /          \
Console Sender   SMTP Sender
```

The current event bus is synchronous and runs inside the FastAPI process. Its
interfaces allow migration to a message broker in a future architecture.

## Notification lifecycle

A notification may move through the following delivery states:

```text
pending -> delivered
pending -> failed -> pending -> delivered
pending -> failed
pending -> cancelled
```

A delivery failure records:

- Delivery attempt count
- Failure timestamp
- Failure reason
- Next retry time

## Domain events

Supported domain events include:

- `HighRiskFraudDetected`
- `FraudPredictionCompleted`
- `InvestigationAssigned`
- `FraudCaseEscalated`
- `FraudCaseStatusChanged`
- `ReportGenerationCompleted`
- `ReportGenerationFailed`

## API capabilities

Authenticated users can:

- List and filter their notifications
- Paginate notification results
- Read one notification
- Mark notifications as read or unread
- Retrieve unread counts and statistics
- Soft-delete and restore notifications
- Perform bulk read, delete, and restore operations

Privileged users can:

- Create notifications for another user
- Create and deliver email notifications
- Process the email retry queue
- Clean up expired notifications

## Security

Notification records are scoped to the authenticated recipient. A normal user
cannot read, update, delete, or restore another user's notification.

Administrative actions require a privileged role such as:

- `admin`
- `manager`
- `risk_manager`

## Current email configuration

Local development uses `ConsoleEmailSender`. It records simulated email
delivery through application logging.

`SMTPEmailSender` is available for later production configuration. SMTP
credentials must be loaded from environment variables and must never be
committed to source control.

## Future improvements

Planned refinements include:

- Notification dispatcher pattern
- Asynchronous background jobs
- WebSocket delivery
- Per-user notification preferences
- Provider-specific delivery records
- SMS and Slack delivery channels
- Redis, RabbitMQ, or Kafka event transport
- Dead-letter queues
- Email templates
