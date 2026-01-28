"""
Analytics and metrics API endpoints.
"""

from fastapi import APIRouter, Depends, Query
from typing import Optional

from app.core.auth import get_api_key
from app.services.analytics.tracker import get_analytics_summary, tracker

router = APIRouter()


@router.get("/summary")
async def get_summary(
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    api_key: str = Depends(get_api_key),
):
    """
    Get analytics summary for the last N hours.
    
    Requires API key authentication.
    """
    summary = get_analytics_summary(hours=hours)
    
    return {
        "status": "success",
        "data": summary,
    }


@router.get("/stats")
async def get_stats(
    metric: Optional[str] = None,
    api_key: str = Depends(get_api_key),
):
    """
    Get detailed statistics for metrics.
    
    If metric name provided, returns stats for that metric only.
    Otherwise returns all available stats.
    """
    stats = tracker.get_stats(metric_name=metric)
    
    return {
        "status": "success",
        "metric": metric,
        "data": stats,
    }


@router.get("/counters")
async def get_counters(api_key: str = Depends(get_api_key)):
    """Get all counter values."""
    return {
        "status": "success",
        "data": dict(tracker.counters),
    }


@router.get("/timers")
async def get_timers(api_key: str = Depends(get_api_key)):
    """Get timing statistics."""
    stats = tracker.get_stats()
    
    return {
        "status": "success",
        "data": stats.get("timers", {}),
    }


@router.post("/reset")
async def reset_metrics(api_key: str = Depends(get_api_key)):
    """
    Reset all metrics (for testing).
    
    WARNING: This clears all analytics data!
    """
    tracker.reset()
    
    return {
        "status": "success",
        "message": "All metrics reset",
    }
