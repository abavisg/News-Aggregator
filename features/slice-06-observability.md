# Slice 06: Observability (Logging, Metrics, and Alerts)

## Goal
Implement comprehensive observability for the News Aggregator system with structured logging, metrics collection, alerting capabilities, and a metrics dashboard to monitor system health and performance.

## Acceptance Criteria

1. **Functional Requirements:**
   - Structured JSON logging with contextual information (week_key, job_type, error_code)
   - Metrics collection for key operations (feeds fetched, posts published, failures)
   - Alert system for critical events (missed deadlines, token expiry, high failure rates)
   - Metrics persistence across application restarts
   - Metrics API endpoints for dashboard integration
   - Health check endpoint with system status
   - Support for multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
   - Log rotation and retention policies
   - Metrics export in Prometheus format

2. **Non-Functional Requirements:**
   - Test coverage: ≥ 80%
   - Performance: Logging overhead < 5ms per operation
   - Metrics update: Real-time (in-memory) with periodic persistence
   - Alert evaluation: Every 60 seconds
   - Log file size: Max 100MB with rotation
   - Metrics retention: 90 days
   - Zero impact on existing functionality

3. **Metrics to Track:**
   ```python
   # Counters (cumulative)
   - feeds_fetched_total: int  # Total RSS feeds fetched
   - feeds_failed_total: int  # Total feed fetch failures
   - articles_fetched_total: int  # Total articles retrieved
   - articles_summarized_total: int  # Total articles summarized
   - summaries_failed_total: int  # Total summarization failures
   - posts_composed_total: int  # Total posts composed
   - posts_published_total: int  # Total posts published to LinkedIn
   - publish_failures_total: int  # Total publishing failures
   - oauth_refreshes_total: int  # Total OAuth token refreshes
   - api_requests_total: int  # Total API requests by endpoint

   # Gauges (point-in-time values)
   - active_sources_count: int  # Number of active RSS sources
   - last_fetch_timestamp: float  # Unix timestamp of last fetch
   - last_publish_timestamp: float  # Unix timestamp of last publish
   - oauth_token_expires_at: float  # Unix timestamp of token expiry
   - system_health_score: float  # Overall health (0.0-1.0)

   # Histograms
   - fetch_duration_seconds: List[float]  # Duration of fetch operations
   - summarize_duration_seconds: List[float]  # Duration of summarization
   - publish_duration_seconds: List[float]  # Duration of publishing
   ```

4. **Alert Conditions:**
   ```python
   # Critical alerts
   - missed_preview_deadline: preview job not completed by Friday 00:00
   - missed_publish_deadline: publish job not completed by Friday 12:00
   - oauth_token_expiring: token expires within 24 hours
   - high_failure_rate: failure rate > 5% in last 100 operations
   - ingestion_stopped: no articles fetched in last 24 hours

   # Warning alerts
   - slow_operation: any operation takes > 30 seconds
   - low_article_count: < 3 articles fetched in a run
   - storage_space_low: < 100MB disk space available
   ```

5. **Log Format:**
   ```json
   {
     "timestamp": "2025-11-10T18:00:00.123Z",
     "level": "INFO",
     "logger": "news_aggregator.fetcher",
     "message": "Fetched articles from RSS source",
     "context": {
       "week_key": "2025.W45",
       "job_type": "preview",
       "source": "techcrunch.com",
       "article_count": 5,
       "duration_ms": 234
     },
     "error_code": null,
     "error_message": null,
     "trace_id": "abc123"
   }
   ```

## Technical Design

### Module: `src/core/observability.py`

**Main Classes:**

```python
class MetricsCollector:
    """
    Collects and persists application metrics.
    Supports counters, gauges, and histograms.
    """

    def __init__(self, storage_path: str = "./data/metrics.json"):
        """Initialize metrics collector with persistence"""

    def increment_counter(self, name: str, value: int = 1, labels: dict | None = None) -> None:
        """Increment a counter metric"""

    def set_gauge(self, name: str, value: float, labels: dict | None = None) -> None:
        """Set a gauge metric to a specific value"""

    def observe_histogram(self, name: str, value: float, labels: dict | None = None) -> None:
        """Add an observation to a histogram"""

    def get_metric(self, name: str, labels: dict | None = None) -> dict:
        """Get current value of a metric"""

    def get_all_metrics(self) -> dict:
        """Get all metrics in Prometheus format"""

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus exposition format"""

    def save_to_disk(self) -> None:
        """Persist metrics to disk"""

    def load_from_disk(self) -> None:
        """Load metrics from disk"""


class AlertManager:
    """
    Evaluates alert conditions and triggers notifications.
    """

    def __init__(self, metrics_collector: MetricsCollector):
        """Initialize alert manager with metrics collector"""

    def register_alert(
        self,
        name: str,
        condition: Callable[[], bool],
        severity: str = "warning",
        message: str = ""
    ) -> None:
        """Register a new alert condition"""

    def evaluate_alerts(self) -> List[dict]:
        """
        Evaluate all registered alerts and return active ones.

        Returns:
            [
                {
                    "name": str,
                    "severity": str,  # "critical", "warning"
                    "message": str,
                    "triggered_at": datetime,
                    "resolved": bool
                }
            ]
        """

    def get_active_alerts(self) -> List[dict]:
        """Get currently active alerts"""

    def acknowledge_alert(self, name: str) -> None:
        """Acknowledge an alert (mark as seen)"""


class StructuredLogger:
    """
    Provides structured JSON logging with context propagation.
    """

    def __init__(
        self,
        name: str,
        log_dir: str = "./logs",
        log_level: str = "INFO",
        max_bytes: int = 100 * 1024 * 1024,  # 100MB
        backup_count: int = 5
    ):
        """Initialize structured logger with rotation"""

    def log(
        self,
        level: str,
        message: str,
        context: dict | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        trace_id: str | None = None
    ) -> None:
        """Log a structured message"""

    def debug(self, message: str, **kwargs) -> None:
        """Log DEBUG level message"""

    def info(self, message: str, **kwargs) -> None:
        """Log INFO level message"""

    def warning(self, message: str, **kwargs) -> None:
        """Log WARNING level message"""

    def error(self, message: str, **kwargs) -> None:
        """Log ERROR level message"""

    def critical(self, message: str, **kwargs) -> None:
        """Log CRITICAL level message"""

    def set_context(self, **kwargs) -> None:
        """Set persistent context for subsequent logs"""

    def clear_context(self) -> None:
        """Clear persistent context"""


def get_logger(name: str) -> StructuredLogger:
    """Get or create a structured logger instance"""


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""


def get_alert_manager() -> AlertManager:
    """Get the global alert manager instance"""
```

### API Endpoints: `src/api/main.py` (additions)

```python
@app.get("/v1/metrics")
async def get_metrics():
    """Get all metrics in JSON format"""
    return metrics_collector.get_all_metrics()


@app.get("/v1/metrics/prometheus")
async def get_metrics_prometheus():
    """Get metrics in Prometheus format"""
    return Response(
        content=metrics_collector.export_prometheus(),
        media_type="text/plain"
    )


@app.get("/v1/alerts")
async def get_alerts():
    """Get active alerts"""
    return alert_manager.get_active_alerts()


@app.post("/v1/alerts/{name}/acknowledge")
async def acknowledge_alert(name: str):
    """Acknowledge an alert"""
    alert_manager.acknowledge_alert(name)
    return {"status": "acknowledged"}


@app.get("/v1/health")
async def health_check():
    """
    Comprehensive health check with system status.

    Returns:
        {
            "status": "healthy" | "degraded" | "unhealthy",
            "timestamp": datetime,
            "metrics": {
                "feeds_fetched_total": int,
                "posts_published_total": int,
                ...
            },
            "alerts": [...],
            "system": {
                "disk_space_mb": float,
                "log_size_mb": float,
                "uptime_seconds": float
            }
        }
    """
```

## Integration with Existing Modules

### 1. Fetcher (`src/core/fetcher.py`)

Add metrics and logging:
```python
from .observability import get_logger, get_metrics_collector

logger = get_logger(__name__)
metrics = get_metrics_collector()

def fetch_news(sources: list[str]) -> list[dict]:
    start_time = time.time()
    logger.info("Starting RSS feed fetch", context={"source_count": len(sources)})

    try:
        # ... existing fetch logic ...

        metrics.increment_counter("feeds_fetched_total", len(sources))
        metrics.increment_counter("articles_fetched_total", len(articles))
        metrics.observe_histogram("fetch_duration_seconds", time.time() - start_time)

        logger.info(
            "Feed fetch completed",
            context={
                "source_count": len(sources),
                "article_count": len(articles),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        )
        return articles

    except Exception as e:
        metrics.increment_counter("feeds_failed_total")
        logger.error(
            "Feed fetch failed",
            context={"source_count": len(sources)},
            error_code="FETCH_ERROR",
            error_message=str(e)
        )
        raise
```

### 2. Summarizer (`src/core/summarizer.py`)

Add metrics and logging:
```python
def summarize_article(article: dict, provider: str = "auto") -> str:
    start_time = time.time()
    logger.info("Starting article summarization", context={"provider": provider})

    try:
        # ... existing summarization logic ...

        metrics.increment_counter("articles_summarized_total")
        metrics.observe_histogram("summarize_duration_seconds", time.time() - start_time)

        logger.info(
            "Summarization completed",
            context={
                "provider": provider,
                "input_length": len(article.get("content", "")),
                "output_length": len(summary),
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        )
        return summary

    except Exception as e:
        metrics.increment_counter("summaries_failed_total")
        logger.error(
            "Summarization failed",
            context={"provider": provider},
            error_code="SUMMARIZE_ERROR",
            error_message=str(e)
        )
        raise
```

### 3. Composer (`src/core/composer.py`)

Add metrics and logging:
```python
def compose_weekly_post(summaries: list[dict], week_key: str | None = None) -> dict:
    logger.info("Starting post composition", context={"summary_count": len(summaries)})

    try:
        # ... existing composition logic ...

        metrics.increment_counter("posts_composed_total")

        logger.info(
            "Post composition completed",
            context={
                "week_key": week_key,
                "article_count": len(summaries),
                "char_count": len(post["content"]),
                "hashtag_count": len(post["hashtags"])
            }
        )
        return post

    except Exception as e:
        logger.error(
            "Post composition failed",
            context={"summary_count": len(summaries)},
            error_code="COMPOSE_ERROR",
            error_message=str(e)
        )
        raise
```

### 4. Publisher (`src/core/publisher.py`)

Add metrics and logging:
```python
def publish_post(self, week_key: str, content: str, metadata: dict | None = None) -> dict:
    start_time = time.time()
    logger.info("Starting post publication", context={"week_key": week_key})

    try:
        # ... existing publish logic ...

        metrics.increment_counter("posts_published_total")
        metrics.observe_histogram("publish_duration_seconds", time.time() - start_time)
        metrics.set_gauge("last_publish_timestamp", time.time())

        logger.info(
            "Post published successfully",
            context={
                "week_key": week_key,
                "post_id": result["post_id"],
                "duration_ms": int((time.time() - start_time) * 1000)
            }
        )
        return result

    except Exception as e:
        metrics.increment_counter("publish_failures_total")
        logger.error(
            "Post publication failed",
            context={"week_key": week_key},
            error_code="PUBLISH_ERROR",
            error_message=str(e)
        )
        raise
```

### 5. Scheduler (`src/core/scheduler.py`)

Add alert registration:
```python
from .observability import get_alert_manager, get_metrics_collector

alert_manager = get_alert_manager()
metrics = get_metrics_collector()

def __init__(self, ...):
    # ... existing init ...

    # Register alerts
    alert_manager.register_alert(
        "missed_preview_deadline",
        condition=lambda: self._check_preview_deadline_missed(),
        severity="critical",
        message="Preview job did not complete by Friday 00:00"
    )

    alert_manager.register_alert(
        "missed_publish_deadline",
        condition=lambda: self._check_publish_deadline_missed(),
        severity="critical",
        message="Publish job did not complete by Friday 12:00"
    )

    alert_manager.register_alert(
        "high_failure_rate",
        condition=lambda: self._check_high_failure_rate(),
        severity="warning",
        message="Failure rate exceeded 5% threshold"
    )
```

## Testing Strategy

### Unit Tests: `src/tests/unit/test_observability.py`

```python
import pytest
from src.core.observability import (
    MetricsCollector,
    AlertManager,
    StructuredLogger,
    get_logger,
    get_metrics_collector,
    get_alert_manager
)


class TestMetricsCollector:
    """Test metrics collection functionality"""

    def test_increment_counter(self):
        """Counter increments correctly"""

    def test_set_gauge(self):
        """Gauge sets to correct value"""

    def test_observe_histogram(self):
        """Histogram records observations"""

    def test_get_metric(self):
        """Metric retrieval returns correct value"""

    def test_get_all_metrics(self):
        """All metrics returned in correct format"""

    def test_export_prometheus(self):
        """Prometheus export format is valid"""

    def test_persistence(self, tmp_path):
        """Metrics persist and load correctly"""

    def test_labels(self):
        """Metric labels work correctly"""

    def test_concurrent_updates(self):
        """Thread-safe metric updates"""


class TestAlertManager:
    """Test alert evaluation and management"""

    def test_register_alert(self):
        """Alert registration works"""

    def test_evaluate_alerts_triggered(self):
        """Alert triggers when condition is true"""

    def test_evaluate_alerts_not_triggered(self):
        """Alert doesn't trigger when condition is false"""

    def test_get_active_alerts(self):
        """Active alerts returned correctly"""

    def test_acknowledge_alert(self):
        """Alert acknowledgment works"""

    def test_alert_severity(self):
        """Alert severity levels work correctly"""

    def test_alert_resolution(self):
        """Alerts auto-resolve when condition clears"""


class TestStructuredLogger:
    """Test structured logging functionality"""

    def test_log_with_context(self):
        """Logging with context works"""

    def test_log_levels(self):
        """All log levels work correctly"""

    def test_persistent_context(self):
        """Context persistence works"""

    def test_clear_context(self):
        """Context clearing works"""

    def test_log_rotation(self, tmp_path):
        """Log rotation works at size limit"""

    def test_json_format(self):
        """Log output is valid JSON"""

    def test_trace_id(self):
        """Trace ID propagation works"""


class TestIntegration:
    """Test observability integration"""

    def test_singleton_instances(self):
        """Singleton pattern works for collectors"""

    def test_metrics_in_logs(self):
        """Metrics can be queried from logs"""

    def test_alert_on_metric_threshold(self):
        """Alerts trigger based on metrics"""

    def test_end_to_end_observability(self):
        """Full observability pipeline works"""
```

### Integration Tests

Test observability with actual module execution:
- Run fetcher and verify metrics are recorded
- Trigger alert conditions and verify alerts fire
- Verify logs are written in correct format
- Test metrics persistence across restarts
- Verify Prometheus export format

## Dependencies

All required dependencies are already in `requirements.txt`:
- `structlog` - Already installed (structured logging)
- Standard library: `logging`, `json`, `threading`, `time`

## Success Criteria

- ✅ All metrics tracked correctly for each operation
- ✅ Alerts trigger appropriately for error conditions
- ✅ Logs are structured JSON with full context
- ✅ Metrics persist across application restarts
- ✅ Prometheus format export works
- ✅ Health check endpoint returns comprehensive status
- ✅ Zero performance impact on existing functionality
- ✅ Test coverage ≥ 80%
- ✅ All existing tests still pass
- ✅ Documentation updated

## Deliverables

1. `src/core/observability.py` - Core observability module
2. `src/tests/unit/test_observability.py` - Comprehensive test suite
3. Updated modules: `fetcher.py`, `summarizer.py`, `composer.py`, `publisher.py`, `scheduler.py`
4. Updated `src/api/main.py` with metrics endpoints
5. `logs/` directory for log files
6. `data/metrics.json` for metrics persistence
7. Updated documentation
