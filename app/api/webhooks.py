"""
Webhook endpoints for external integrations.

Supports:
- Email forwarding (parse attachments)
- Zapier / Make.com integrations
- Custom webhook triggers
"""

import hashlib
import hmac
from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Header, Depends
from pydantic import BaseModel, EmailStr, HttpUrl
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.tasks.extraction import extract_document

router = APIRouter()


class WebhookPayload(BaseModel):
    """Generic webhook payload."""
    event: str
    data: dict


class EmailWebhookPayload(BaseModel):
    """Email forwarding webhook."""
    from_email: EmailStr
    subject: str
    body: Optional[str] = None
    attachments: List[dict] = []  # [{filename, url, content_type}]


class ZapierWebhookPayload(BaseModel):
    """Zapier webhook payload."""
    file_url: HttpUrl
    filename: str
    company_id: Optional[str] = None
    metadata: Optional[dict] = None


def verify_webhook_signature(
    payload: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Verify HMAC signature for webhook security."""
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected)


@router.post("/email")
async def email_webhook(
    request: Request,
    payload: EmailWebhookPayload,
    db: Session = Depends(get_db),
    x_signature: Optional[str] = Header(None),
):
    """
    Receive emails with document attachments.
    
    Setup:
    1. Configure email forwarding rule to this endpoint
    2. Set webhook secret in settings
    3. Email service sends POST with attachments
    
    Example providers:
    - SendGrid Inbound Parse
    - Mailgun Routes
    - Postmark Inbound
    """
    # Verify signature if configured
    if settings.webhook_secret and x_signature:
        body = await request.body()
        if not verify_webhook_signature(body, x_signature, settings.webhook_secret):
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Process attachments
    from app.services.storage.storage import StorageService
    import httpx
    
    storage = StorageService()
    document_ids = []
    
    for attachment in payload.attachments:
        # Download attachment
        async with httpx.AsyncClient() as client:
            response = await client.get(attachment["url"])
            file_data = response.content
        
        # Store file
        storage_path = storage.store_file(
            file_data=file_data,
            filename=attachment["filename"],
        )
        
        # Create document record
        from app.models.database import Document
        doc = Document(
            filename=attachment["filename"],
            file_type=attachment.get("content_type", "application/octet-stream"),
            storage_path=storage_path,
            status="uploaded",
            source="email",
            metadata={
                "from_email": payload.from_email,
                "subject": payload.subject,
            },
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # Trigger extraction
        extract_document.delay(doc.id)
        
        document_ids.append(doc.id)
    
    return {
        "status": "success",
        "message": f"Processed {len(document_ids)} attachments",
        "document_ids": document_ids,
    }


@router.post("/zapier")
async def zapier_webhook(
    payload: ZapierWebhookPayload,
    db: Session = Depends(get_db),
):
    """
    Zapier integration webhook.
    
    Zapier Action: Send Document to Receipt AI
    - User uploads file to Dropbox/Google Drive/etc.
    - Zapier detects new file
    - Sends file URL to this endpoint
    - We download, process, and extract
    """
    import httpx
    from app.services.storage.storage import StorageService
    from app.models.database import Document
    
    # Download file
    async with httpx.AsyncClient() as client:
        response = await client.get(str(payload.file_url))
        file_data = response.content
    
    # Store
    storage = StorageService()
    storage_path = storage.store_file(
        file_data=file_data,
        filename=payload.filename,
    )
    
    # Create document
    doc = Document(
        filename=payload.filename,
        file_type=response.headers.get("content-type", "application/octet-stream"),
        storage_path=storage_path,
        status="uploaded",
        source="zapier",
        metadata=payload.metadata or {},
    )
    
    if payload.company_id:
        doc.company_id = payload.company_id
    
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Extract
    task = extract_document.delay(doc.id)
    
    return {
        "status": "success",
        "document_id": doc.id,
        "task_id": task.id,
        "message": "Document uploaded and queued for extraction",
    }


@router.post("/generic")
async def generic_webhook(
    request: Request,
    payload: WebhookPayload,
    x_signature: Optional[str] = Header(None),
):
    """
    Generic webhook receiver for custom integrations.
    
    Supports any event type. Processes based on event name.
    """
    # Verify signature
    if settings.webhook_secret and x_signature:
        body = await request.body()
        if not verify_webhook_signature(body, x_signature, settings.webhook_secret):
            raise HTTPException(status_code=403, detail="Invalid signature")
    
    # Route based on event type
    handlers = {
        "document.uploaded": handle_document_uploaded,
        "extraction.completed": handle_extraction_completed,
        "qbo.synced": handle_qbo_synced,
    }
    
    handler = handlers.get(payload.event)
    
    if not handler:
        return {
            "status": "ignored",
            "message": f"No handler for event: {payload.event}",
        }
    
    result = await handler(payload.data)
    
    return {
        "status": "success",
        "event": payload.event,
        "result": result,
    }


# Event handlers

async def handle_document_uploaded(data: dict) -> dict:
    """Handle document.uploaded event."""
    # Custom logic
    return {"handled": True}


async def handle_extraction_completed(data: dict) -> dict:
    """Handle extraction.completed event."""
    # Could trigger notifications, analytics, etc.
    return {"handled": True}


async def handle_qbo_synced(data: dict) -> dict:
    """Handle qbo.synced event."""
    # Could update dashboards, send confirmations, etc.
    return {"handled": True}


@router.get("/test")
async def test_webhook():
    """Test endpoint to verify webhook is reachable."""
    return {
        "status": "ok",
        "message": "Webhook endpoint is live",
        "timestamp": "2026-01-28T03:45:00Z",
    }
