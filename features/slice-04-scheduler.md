# Slice 04: Scheduler

## Goal
Implement an automated scheduler using APScheduler that orchestrates weekly news aggregation, preview generation, and publication workflows. The scheduler will coordinate all previous slices (fetch → summarize → compose) and run them on a reliable weekly schedule.

## Acceptance Criteria

1. **Functional Requirements:**
   - Schedule preview generation every Thursday at 18:00 (Europe/London)
   - Schedule publication every Friday at 10:00 (Europe/London)
   - Support one-time manual job execution (immediate run)
   - Graceful startup and shutdown handling
   - Job persistence across restarts (using APScheduler jobstore)
   - Configurable timezone and schedule times via environment variables
   - Execute full pipeline: fetch → summarize → compose
   - Handle job failures with proper error logging
   - Support dry-run mode for testing without actual execution

2. **Non-Functional Requirements:**
   - Startup time: < 5 seconds
   - Test coverage: ≥ 90%
   - Memory footprint: < 100MB idle
   - Logging: structured logs for all scheduler events
   - Reliability: Jobs must not silently fail
   - Idempotency: Re-running same week_key should be safe

3. **Data Format:**
   ```python
   # Scheduler configuration
   {
       "timezone": "Europe/London",
       "preview_time": "18:00",  # Thursday
       "publish_time": "10:00",  # Friday
       "preview_day": 3,  # Thursday (0=Monday)
       "publish_day": 4,  # Friday
       "jobstore": "sqlite",  # or "memory" for testing
       "max_instances": 1  # Prevent overlapping jobs
   }

   # Job execution result
   {
       "job_id": str,
       "job_type": str,  # "preview" or "publish"
       "week_key": str,
       "status": str,  # "success", "failed", "skipped"
       "started_at": datetime,
       "completed_at": datetime,
       "duration_seconds": float,
       "articles_fetched": int,
       "articles_summarized": int,
       "post_created": bool,
       "error": str | None
   }
   ```

## Technical Design

### Module: `src/core/scheduler.py`

**Main Class:**
```python
class NewsAggregatorScheduler:
    """
    Manages scheduled execution of news aggregation workflows.

    Uses APScheduler to coordinate weekly preview and publish jobs.
    """

    def __init__(
        self,
        timezone: str = "Europe/London",
        preview_time: str = "18:00",
        publish_time: str = "10:00",
        jobstore_type: str = "sqlite"
    ):
        """Initialize scheduler with configuration"""

    def start(self) -> None:
        """Start the scheduler (blocking operation)"""

    def shutdown(self, wait: bool = True) -> None:
        """Gracefully shutdown scheduler"""

    def schedule_jobs(self) -> None:
        """Configure all recurring jobs"""

    def run_preview_job(self) -> dict:
        """Execute preview generation workflow"""

    def run_publish_job(self) -> dict:
        """Execute publish workflow"""

    def execute_pipeline(self, week_key: str, is_preview: bool = True) -> dict:
        """Execute full pipeline: fetch → summarize → compose"""

    def get_job_status(self, job_id: str) -> dict:
        """Get status of a specific job"""

    def list_scheduled_jobs(self) -> list[dict]:
        """List all scheduled jobs"""
```

**Helper Functions:**
```python
def parse_schedule_time(time_str: str) -> tuple[int, int]:
    """Parse time string (HH:MM) into hour and minute"""

def get_week_key_for_date(date: datetime) -> str:
    """Generate week_key (YYYY.Www) for specific date"""

def should_run_job(week_key: str, job_type: str) -> bool:
    """Check if job should run based on existing state"""

def save_job_result(result: dict) -> None:
    """Persist job execution result for observability"""
```

**Custom Exception:**
```python
class SchedulerError(Exception):
    """Raised when scheduler operation fails"""

class JobExecutionError(Exception):
    """Raised when scheduled job execution fails"""
```

### Module: `src/scripts/scheduler.py`

**Entry Point Script:**
```python
"""
Scheduler entry point for production deployment.

Usage:
    python src/scripts/scheduler.py              # Start scheduler
    python src/scripts/scheduler.py --once       # Run once and exit
    python src/scripts/scheduler.py --preview    # Run preview job now
    python src/scripts/scheduler.py --publish    # Run publish job now
"""

def main():
    """Main entry point with CLI argument parsing"""
```

## Test Cases

### Unit Tests (`src/tests/unit/test_scheduler.py`)

1. `test_scheduler_initialization()`
   - Given: Valid configuration parameters
   - When: NewsAggregatorScheduler() is instantiated
   - Then: Scheduler is created with correct settings

2. `test_scheduler_initialization_with_defaults()`
   - Given: No configuration parameters
   - When: NewsAggregatorScheduler() is instantiated
   - Then: Uses default timezone and times

3. `test_scheduler_initialization_with_custom_timezone()`
   - Given: Custom timezone "America/New_York"
   - When: NewsAggregatorScheduler() is instantiated
   - Then: Scheduler uses specified timezone

4. `test_schedule_jobs_creates_preview_job()`
   - Given: Initialized scheduler
   - When: schedule_jobs() is called
   - Then: Preview job is scheduled for Thursday 18:00

5. `test_schedule_jobs_creates_publish_job()`
   - Given: Initialized scheduler
   - When: schedule_jobs() is called
   - Then: Publish job is scheduled for Friday 10:00

6. `test_run_preview_job_executes_pipeline()`
   - Given: Mocked pipeline components
   - When: run_preview_job() is called
   - Then: Executes fetch → summarize → compose

7. `test_run_preview_job_returns_result()`
   - Given: Successful pipeline execution
   - When: run_preview_job() is called
   - Then: Returns result dict with status "success"

8. `test_run_publish_job_executes_pipeline()`
   - Given: Mocked pipeline components
   - When: run_publish_job() is called
   - Then: Executes fetch → summarize → compose

9. `test_execute_pipeline_fetches_articles()`
   - Given: Valid week_key
   - When: execute_pipeline() is called
   - Then: Calls fetcher.fetch_news() with configured sources

10. `test_execute_pipeline_summarizes_articles()`
    - Given: Fetched articles
    - When: execute_pipeline() is called
    - Then: Calls summarizer.summarize_article() for each article

11. `test_execute_pipeline_composes_post()`
    - Given: Summarized articles
    - When: execute_pipeline() is called
    - Then: Calls composer.compose_weekly_post()

12. `test_execute_pipeline_handles_fetch_failure()`
    - Given: Fetcher raises exception
    - When: execute_pipeline() is called
    - Then: Returns result with status "failed" and error details

13. `test_execute_pipeline_handles_summarizer_failure()`
    - Given: Summarizer raises exception for some articles
    - When: execute_pipeline() is called
    - Then: Continues with successfully summarized articles

14. `test_execute_pipeline_handles_composer_failure()`
    - Given: Composer raises exception
    - When: execute_pipeline() is called
    - Then: Returns result with status "failed" and error details

15. `test_shutdown_stops_scheduler()`
    - Given: Running scheduler
    - When: shutdown() is called
    - Then: Scheduler stops gracefully

16. `test_parse_schedule_time_valid_format()`
    - Given: time_str = "18:00"
    - When: parse_schedule_time() is called
    - Then: Returns (18, 0)

17. `test_parse_schedule_time_invalid_format()`
    - Given: time_str = "invalid"
    - When: parse_schedule_time() is called
    - Then: Raises SchedulerError

18. `test_get_week_key_for_date()`
    - Given: date = datetime(2025, 11, 14)  # Week 46
    - When: get_week_key_for_date() is called
    - Then: Returns "2025.W46"

19. `test_list_scheduled_jobs_returns_jobs()`
    - Given: Scheduler with jobs configured
    - When: list_scheduled_jobs() is called
    - Then: Returns list with preview and publish jobs

20. `test_scheduler_prevents_overlapping_jobs()`
    - Given: Scheduler with max_instances=1
    - When: Same job triggered while running
    - Then: Second instance is skipped

21. `test_scheduler_with_memory_jobstore()`
    - Given: jobstore_type="memory"
    - When: Scheduler is initialized
    - Then: Uses in-memory jobstore (no persistence)

22. `test_scheduler_with_sqlite_jobstore()`
    - Given: jobstore_type="sqlite"
    - When: Scheduler is initialized
    - Then: Uses SQLite jobstore for persistence

## Dependencies

APScheduler is already in requirements.txt:
- `apscheduler==3.10.4` - Job scheduling
- `pytz==2023.3` - Timezone handling
- `python-dotenv==1.0.0` - Environment configuration

## Configuration

### Environment Variables

```env
# Scheduler Configuration
TIMEZONE=Europe/London
PREVIEW_DAY=3                    # Thursday (0=Monday)
PREVIEW_TIME=18:00
PUBLISH_DAY=4                    # Friday
PUBLISH_TIME=10:00
JOBSTORE_TYPE=sqlite             # or "memory" for testing
JOBSTORE_PATH=./scheduler.db     # SQLite database path

# RSS Sources (from Slice 01)
RSS_SOURCES=https://techcrunch.com/feed/,https://www.theverge.com/rss/index.xml

# AI Provider (from Slice 02)
ANTHROPIC_API_KEY=...
OLLAMA_BASE_URL=http://localhost:11434
```

## Scheduler Architecture

```
┌─────────────────────────────────────────────────────┐
│           APScheduler (BackgroundScheduler)         │
│                                                     │
│  ┌─────────────────┐      ┌──────────────────┐    │
│  │  Preview Job    │      │  Publish Job     │    │
│  │  Thu 18:00      │      │  Fri 10:00       │    │
│  └────────┬────────┘      └────────┬─────────┘    │
│           │                        │               │
└───────────┼────────────────────────┼───────────────┘
            │                        │
            ▼                        ▼
    ┌───────────────────────────────────────┐
    │    execute_pipeline(week_key)         │
    │                                       │
    │  1. fetch_news() ───► articles        │
    │  2. summarize_article() ───► summaries│
    │  3. compose_weekly_post() ───► post   │
    │  4. save_result() ───► database       │
    └───────────────────────────────────────┘
```

## Usage Examples

### Running the Scheduler (Production)

```bash
# Start scheduler daemon
python src/scripts/scheduler.py

# Logs:
# 2025-11-10 12:00:00 [INFO] Scheduler initialized (timezone: Europe/London)
# 2025-11-10 12:00:00 [INFO] Preview job scheduled: Thu 18:00
# 2025-11-10 12:00:00 [INFO] Publish job scheduled: Fri 10:00
# 2025-11-10 12:00:00 [INFO] Scheduler started
```

### Manual Job Execution

```bash
# Run preview job immediately
python src/scripts/scheduler.py --preview

# Run publish job immediately
python src/scripts/scheduler.py --publish

# Run once (no daemon)
python src/scripts/scheduler.py --once
```

### Programmatic Usage

```python
from src.core.scheduler import NewsAggregatorScheduler

# Initialize scheduler
scheduler = NewsAggregatorScheduler(
    timezone="Europe/London",
    preview_time="18:00",
    publish_time="10:00"
)

# Start scheduler (blocking)
try:
    scheduler.schedule_jobs()
    scheduler.start()
except KeyboardInterrupt:
    scheduler.shutdown()
```

## Success Metrics

- All 22 test cases pass
- Code coverage ≥ 90% for scheduler.py
- Jobs execute reliably on schedule
- Graceful error handling and recovery
- Proper logging for all events
- No memory leaks during long runs

## Integration with Previous Slices

The scheduler orchestrates all previous slices:

```python
# Slice 01: Fetcher
from src.core.fetcher import fetch_news

# Slice 02: Summarizer
from src.core.summarizer import summarize_article

# Slice 03: Composer
from src.core.composer import compose_weekly_post

def execute_pipeline(week_key: str) -> dict:
    """Full pipeline execution"""

    # Step 1: Fetch articles (Slice 01)
    articles = fetch_news(RSS_SOURCES)

    # Step 2: Summarize articles (Slice 02)
    summaries = []
    for article in articles[:10]:
        try:
            summary = summarize_article(article)
            summaries.append(summary)
        except Exception as e:
            log.error("Summarization failed", article=article, error=str(e))

    # Step 3: Compose post (Slice 03)
    post = compose_weekly_post(summaries, week_key=week_key)

    return {
        "week_key": week_key,
        "status": "success",
        "articles_fetched": len(articles),
        "articles_summarized": len(summaries),
        "post_created": True,
        "post": post
    }
```

## Out of Scope (Future Slices)

- LinkedIn publishing (Slice 05)
- Database persistence beyond jobstore (Slice 06)
- Advanced metrics and monitoring (Slice 06)
- Email notifications on job failure
- A/B testing different schedules
- Multi-timezone support
- Retry logic with exponential backoff (basic retry only)
- Job priority and queueing

## Definition of Done

- ✅ All tests pass locally and in CI
- ✅ Coverage report shows ≥ 90% for scheduler.py
- ✅ Code follows PEP 8 and passes ruff/black
- ✅ Structured logging implemented
- ✅ Manual testing with scheduler running for 24 hours
- ✅ Jobs execute at correct times
- ✅ Graceful shutdown verified
- ✅ Documentation strings complete
- ✅ BUILD_LOG.md updated
- ✅ Committed with conventional commit message

## Observability

The scheduler will log:
- Scheduler startup and shutdown events
- Job scheduling confirmations
- Job execution start/completion with duration
- Pipeline step progress (fetch, summarize, compose)
- Errors and exceptions with full context
- Resource usage (articles fetched, summaries created)

Log format:
```json
{
  "timestamp": "2025-11-10T18:00:00Z",
  "level": "INFO",
  "event": "job_started",
  "job_type": "preview",
  "week_key": "2025.W46",
  "scheduled_time": "2025-11-10T18:00:00Z"
}
```

---

**Created:** 2025-11-10
**Author:** Giorgos Ampavis
**Status:** Completed
