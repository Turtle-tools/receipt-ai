"""
Analytics and metrics tracking.

Tracks:
- Document processing metrics
- API usage
- Extraction accuracy
- QBO sync success rates
- Performance metrics
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import json

from app.core.logging import get_logger

logger = get_logger("analytics")


@dataclass
class Metric:
    """A single metric data point."""
    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class AnalyticsTracker:
    """In-memory analytics tracker (replace with proper service in production)."""
    
    def __init__(self):
        self.metrics: List[Metric] = []
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)
    
    def track_event(
        self,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ):
        """Track an event."""
        logger.info(
            f"Event: {event_name}",
            extra={
                "event": event_name,
                "properties": properties or {},
                "user_id": user_id,
            }
        )
        
        self.counters[event_name] += 1
    
    def track_metric(
        self,
        name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Track a numeric metric."""
        metric = Metric(
            name=name,
            value=value,
            tags=tags or {},
            metadata=metadata or {},
        )
        
        self.metrics.append(metric)
        
        logger.debug(
            f"Metric: {name} = {value}",
            extra={
                "metric_name": name,
                "metric_value": value,
                "tags": tags,
            }
        )
    
    def increment(self, counter_name: str, value: int = 1):
        """Increment a counter."""
        self.counters[counter_name] += value
    
    def timing(self, timer_name: str, duration_ms: float):
        """Record a timing metric."""
        self.timers[timer_name].append(duration_ms)
        
        self.track_metric(
            f"{timer_name}.duration_ms",
            duration_ms,
            tags={"type": "timing"},
        )
    
    def get_stats(self, metric_name: Optional[str] = None) -> Dict[str, Any]:
        """Get statistics for metrics."""
        if metric_name:
            values = [m.value for m in self.metrics if m.name == metric_name]
            if not values:
                return {}
            
            return {
                "count": len(values),
                "sum": sum(values),
                "avg": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
            }
        
        # Return all stats
        stats = {}
        
        # Counters
        stats["counters"] = dict(self.counters)
        
        # Timers
        stats["timers"] = {}
        for timer_name, values in self.timers.items():
            if values:
                stats["timers"][timer_name] = {
                    "count": len(values),
                    "avg_ms": sum(values) / len(values),
                    "min_ms": min(values),
                    "max_ms": max(values),
                    "p50_ms": sorted(values)[len(values) // 2],
                    "p95_ms": sorted(values)[int(len(values) * 0.95)] if len(values) > 20 else max(values),
                }
        
        return stats
    
    def reset(self):
        """Reset all metrics (for testing)."""
        self.metrics.clear()
        self.counters.clear()
        self.timers.clear()


# Global tracker instance
tracker = AnalyticsTracker()


# Helper functions for common events

def track_document_uploaded(
    document_id: int,
    file_type: str,
    file_size_bytes: int,
    source: str = "web",
):
    """Track document upload event."""
    tracker.track_event(
        "document.uploaded",
        properties={
            "document_id": document_id,
            "file_type": file_type,
            "file_size_bytes": file_size_bytes,
            "source": source,
        }
    )
    
    tracker.increment("documents.uploaded")
    tracker.track_metric(
        "document.size_bytes",
        file_size_bytes,
        tags={"file_type": file_type},
    )


def track_extraction_started(document_id: int, document_type: str):
    """Track extraction start."""
    tracker.track_event(
        "extraction.started",
        properties={
            "document_id": document_id,
            "document_type": document_type,
        }
    )
    
    tracker.increment("extractions.started")


def track_extraction_completed(
    document_id: int,
    document_type: str,
    duration_ms: float,
    confidence: float,
    success: bool = True,
):
    """Track extraction completion."""
    tracker.track_event(
        "extraction.completed",
        properties={
            "document_id": document_id,
            "document_type": document_type,
            "duration_ms": duration_ms,
            "confidence": confidence,
            "success": success,
        }
    )
    
    if success:
        tracker.increment("extractions.succeeded")
    else:
        tracker.increment("extractions.failed")
    
    tracker.timing("extraction.duration", duration_ms)
    tracker.track_metric(
        "extraction.confidence",
        confidence,
        tags={"document_type": document_type},
    )


def track_qbo_sync(
    document_id: int,
    qbo_id: Optional[str],
    success: bool,
    duration_ms: float,
):
    """Track QBO sync."""
    tracker.track_event(
        "qbo.sync",
        properties={
            "document_id": document_id,
            "qbo_id": qbo_id,
            "success": success,
            "duration_ms": duration_ms,
        }
    )
    
    if success:
        tracker.increment("qbo.syncs.succeeded")
    else:
        tracker.increment("qbo.syncs.failed")
    
    tracker.timing("qbo.sync.duration", duration_ms)


def track_api_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
):
    """Track API request."""
    tracker.increment(f"api.requests.{method}")
    tracker.increment(f"api.status.{status_code}")
    
    tracker.timing(f"api.request.{method}", duration_ms)
    
    tracker.track_metric(
        "api.response_time_ms",
        duration_ms,
        tags={
            "method": method,
            "path": path,
            "status": str(status_code),
        }
    )


def get_analytics_summary(hours: int = 24) -> Dict[str, Any]:
    """Get analytics summary for the last N hours."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    
    # Filter recent metrics
    recent_metrics = [m for m in tracker.metrics if m.timestamp >= cutoff]
    
    # Calculate stats
    summary = {
        "period_hours": hours,
        "metrics_count": len(recent_metrics),
        "stats": tracker.get_stats(),
    }
    
    # Document stats
    summary["documents"] = {
        "uploaded": tracker.counters.get("documents.uploaded", 0),
        "processed": tracker.counters.get("extractions.succeeded", 0),
        "failed": tracker.counters.get("extractions.failed", 0),
    }
    
    # QBO stats
    summary["qbo"] = {
        "synced": tracker.counters.get("qbo.syncs.succeeded", 0),
        "failed": tracker.counters.get("qbo.syncs.failed", 0),
    }
    
    # API stats
    summary["api"] = {
        "total_requests": sum(v for k, v in tracker.counters.items() if k.startswith("api.requests.")),
        "by_method": {
            k.replace("api.requests.", ""): v
            for k, v in tracker.counters.items()
            if k.startswith("api.requests.")
        },
    }
    
    return summary


# Middleware integration

class AnalyticsMiddleware:
    """Middleware to automatically track API metrics."""
    
    @staticmethod
    def track_request(method: str, path: str, status_code: int, duration_ms: float):
        """Track API request from middleware."""
        track_api_request(method, path, status_code, duration_ms)
