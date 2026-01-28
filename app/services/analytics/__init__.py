"""Analytics and metrics tracking."""

from app.services.analytics.tracker import (
    tracker,
    track_document_uploaded,
    track_extraction_started,
    track_extraction_completed,
    track_qbo_sync,
    track_api_request,
    get_analytics_summary,
)

__all__ = [
    "tracker",
    "track_document_uploaded",
    "track_extraction_started",
    "track_extraction_completed",
    "track_qbo_sync",
    "track_api_request",
    "get_analytics_summary",
]
