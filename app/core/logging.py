"""
Structured logging configuration.

Provides JSON-formatted logs for production with context tracking.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from contextvars import ContextVar
from pathlib import Path

from app.core.config import settings


# Context variables for request tracking
request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add request context if available
        request_id = request_id_var.get()
        if request_id:
            log_data["request_id"] = request_id
        
        user_id = user_id_var.get()
        if user_id:
            log_data["user_id"] = user_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


class ColoredConsoleFormatter(logging.Formatter):
    """Colored console formatter for development."""
    
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Magenta
    }
    RESET = "\033[0m"
    
    def format(self, record: logging.LogRecord) -> str:
        """Format with colors for console."""
        levelname = record.levelname
        color = self.COLORS.get(levelname, "")
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        
        # Build message
        message = (
            f"{color}[{timestamp}] {levelname:8}{self.RESET} "
            f"{record.name:20} {record.getMessage()}"
        )
        
        # Add exception if present
        if record.exc_info:
            message += "\n" + self.formatException(record.exc_info)
        
        return message


def setup_logging():
    """Configure logging for the application."""
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    if settings.is_production:
        # JSON format for production
        console_handler.setFormatter(StructuredFormatter())
    else:
        # Colored format for development
        console_handler.setFormatter(ColoredConsoleFormatter())
    
    root_logger.addHandler(console_handler)
    
    # File handler for production
    if settings.is_production:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        file_handler = logging.FileHandler(log_dir / "app.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Silence noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    
    # App logger
    app_logger = logging.getLogger("app")
    app_logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    
    app_logger.info(
        "Logging configured",
        extra={
            "environment": settings.app_env,
            "debug": settings.debug,
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance."""
    return logging.getLogger(f"app.{name}")


# Custom log functions with context

def log_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    **kwargs
):
    """Log API request with structured data."""
    logger = get_logger("api")
    
    logger.info(
        f"{method} {path} - {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
            **kwargs,
        }
    )


def log_extraction(
    document_id: int,
    document_type: str,
    status: str,
    duration_ms: Optional[float] = None,
    **kwargs
):
    """Log document extraction event."""
    logger = get_logger("extraction")
    
    logger.info(
        f"Extraction {status} for document {document_id}",
        extra={
            "document_id": document_id,
            "document_type": document_type,
            "status": status,
            "duration_ms": duration_ms,
            **kwargs,
        }
    )


def log_qbo_sync(
    document_id: int,
    qbo_id: Optional[str],
    status: str,
    **kwargs
):
    """Log QuickBooks sync event."""
    logger = get_logger("qbo")
    
    logger.info(
        f"QBO sync {status} for document {document_id}",
        extra={
            "document_id": document_id,
            "qbo_id": qbo_id,
            "status": status,
            **kwargs,
        }
    )


def log_error(
    error: Exception,
    context: str,
    **kwargs
):
    """Log error with context."""
    logger = get_logger("error")
    
    logger.error(
        f"{context}: {str(error)}",
        exc_info=True,
        extra={
            "context": context,
            "error_type": type(error).__name__,
            **kwargs,
        }
    )


# Middleware helpers

def set_request_context(request_id: str, user_id: Optional[str] = None):
    """Set context variables for request tracking."""
    request_id_var.set(request_id)
    if user_id:
        user_id_var.set(user_id)


def clear_request_context():
    """Clear request context variables."""
    request_id_var.set(None)
    user_id_var.set(None)
