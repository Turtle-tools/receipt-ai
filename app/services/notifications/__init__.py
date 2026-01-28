"""Email notification service."""

from app.services.notifications.email import (
    EmailService,
    send_extraction_complete,
    send_qbo_sync_complete,
    send_error_notification,
)

__all__ = [
    "EmailService",
    "send_extraction_complete",
    "send_qbo_sync_complete",
    "send_error_notification",
]
