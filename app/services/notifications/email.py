"""
Email notification service.

Supports multiple providers:
- SMTP (basic)
- SendGrid
- Resend
- Postmark
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("email")


class EmailService:
    """Email notification service."""
    
    def __init__(self):
        self.provider = getattr(settings, "email_provider", "smtp")
    
    def send(
        self,
        to: str | List[str],
        subject: str,
        html: Optional[str] = None,
        text: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send an email.
        
        Args:
            to: Recipient email(s)
            subject: Email subject
            html: HTML body
            text: Plain text body
            from_email: Sender email (defaults to settings)
            reply_to: Reply-to address
            
        Returns:
            True if sent successfully
        """
        if isinstance(to, str):
            to = [to]
        
        from_email = from_email or getattr(settings, "from_email", "noreply@ironcladcas.com")
        
        try:
            if self.provider == "sendgrid":
                return self._send_sendgrid(to, subject, html, text, from_email, reply_to)
            elif self.provider == "resend":
                return self._send_resend(to, subject, html, text, from_email, reply_to)
            elif self.provider == "postmark":
                return self._send_postmark(to, subject, html, text, from_email, reply_to)
            else:
                return self._send_smtp(to, subject, html, text, from_email, reply_to)
        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False
    
    def _send_smtp(
        self,
        to: List[str],
        subject: str,
        html: Optional[str],
        text: Optional[str],
        from_email: str,
        reply_to: Optional[str],
    ) -> bool:
        """Send via SMTP."""
        smtp_host = getattr(settings, "smtp_host", "localhost")
        smtp_port = getattr(settings, "smtp_port", 587)
        smtp_user = getattr(settings, "smtp_user", None)
        smtp_password = getattr(settings, "smtp_password", None)
        
        # Create message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = from_email
        msg["To"] = ", ".join(to)
        
        if reply_to:
            msg["Reply-To"] = reply_to
        
        # Add bodies
        if text:
            msg.attach(MIMEText(text, "plain"))
        if html:
            msg.attach(MIMEText(html, "html"))
        
        # Send
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent via SMTP to {to}")
        return True
    
    def _send_sendgrid(
        self,
        to: List[str],
        subject: str,
        html: Optional[str],
        text: Optional[str],
        from_email: str,
        reply_to: Optional[str],
    ) -> bool:
        """Send via SendGrid API."""
        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail
        except ImportError:
            raise ImportError("SendGrid not installed. pip install sendgrid")
        
        api_key = getattr(settings, "sendgrid_api_key", None)
        if not api_key:
            raise ValueError("SendGrid API key not configured")
        
        message = Mail(
            from_email=from_email,
            to_emails=to,
            subject=subject,
            html_content=html or text,
        )
        
        if reply_to:
            message.reply_to = reply_to
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        logger.info(f"Email sent via SendGrid to {to}")
        return response.status_code in [200, 201, 202]
    
    def _send_resend(
        self,
        to: List[str],
        subject: str,
        html: Optional[str],
        text: Optional[str],
        from_email: str,
        reply_to: Optional[str],
    ) -> bool:
        """Send via Resend API."""
        import httpx
        
        api_key = getattr(settings, "resend_api_key", None)
        if not api_key:
            raise ValueError("Resend API key not configured")
        
        payload = {
            "from": from_email,
            "to": to,
            "subject": subject,
        }
        
        if html:
            payload["html"] = html
        if text:
            payload["text"] = text
        if reply_to:
            payload["reply_to"] = reply_to
        
        response = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )
        
        response.raise_for_status()
        logger.info(f"Email sent via Resend to {to}")
        return True
    
    def _send_postmark(
        self,
        to: List[str],
        subject: str,
        html: Optional[str],
        text: Optional[str],
        from_email: str,
        reply_to: Optional[str],
    ) -> bool:
        """Send via Postmark API."""
        import httpx
        
        api_key = getattr(settings, "postmark_api_key", None)
        if not api_key:
            raise ValueError("Postmark API key not configured")
        
        payload = {
            "From": from_email,
            "To": ", ".join(to),
            "Subject": subject,
        }
        
        if html:
            payload["HtmlBody"] = html
        if text:
            payload["TextBody"] = text
        if reply_to:
            payload["ReplyTo"] = reply_to
        
        response = httpx.post(
            "https://api.postmarkapp.com/email",
            headers={
                "X-Postmark-Server-Token": api_key,
                "Content-Type": "application/json",
            },
            json=payload,
        )
        
        response.raise_for_status()
        logger.info(f"Email sent via Postmark to {to}")
        return True


# Template helpers

def render_template(template_name: str, **context) -> str:
    """Render an email template with context."""
    template_path = Path(__file__).parent / "templates" / f"{template_name}.html"
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_name}")
    
    template = template_path.read_text()
    
    # Simple template rendering (replace {{variable}})
    for key, value in context.items():
        template = template.replace(f"{{{{{key}}}}}", str(value))
    
    return template


# Notification functions

def send_extraction_complete(
    to: str,
    document_id: int,
    filename: str,
    vendor: str,
    amount: float,
) -> bool:
    """Send extraction complete notification."""
    html = render_template(
        "extraction_complete",
        filename=filename,
        vendor=vendor,
        amount=f"${amount:.2f}",
        document_id=document_id,
        app_url=settings.app_url or "http://localhost:8000",
    )
    
    return EmailService().send(
        to=to,
        subject=f"✅ Receipt extracted: {vendor} - ${amount:.2f}",
        html=html,
    )


def send_qbo_sync_complete(
    to: str,
    document_id: int,
    qbo_id: str,
    company_name: str,
) -> bool:
    """Send QBO sync complete notification."""
    html = render_template(
        "qbo_sync_complete",
        document_id=document_id,
        qbo_id=qbo_id,
        company_name=company_name,
        app_url=settings.app_url or "http://localhost:8000",
    )
    
    return EmailService().send(
        to=to,
        subject=f"✅ Synced to QuickBooks: {company_name}",
        html=html,
    )


def send_error_notification(
    to: str,
    document_id: int,
    error: str,
) -> bool:
    """Send error notification."""
    html = render_template(
        "error_notification",
        document_id=document_id,
        error=error,
        app_url=settings.app_url or "http://localhost:8000",
    )
    
    return EmailService().send(
        to=to,
        subject=f"❌ Document processing failed",
        html=html,
    )
