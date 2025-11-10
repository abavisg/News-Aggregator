"""
News Aggregation Scheduler Module

Manages scheduled execution of weekly news aggregation workflows using APScheduler.
Coordinates the full pipeline: fetch → summarize → compose.
"""

import os
import structlog
from datetime import datetime
from typing import Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
import pytz

# Import pipeline components
from src.core.fetcher import fetch_news
from src.core.summarizer import summarize_article
from src.core.composer import compose_weekly_post

# Setup structured logging
log = structlog.get_logger(__name__)


class SchedulerError(Exception):
    """Raised when scheduler configuration or operation fails"""
    pass


class JobExecutionError(Exception):
    """Raised when scheduled job execution fails"""
    pass


class NewsAggregatorScheduler:
    """
    Manages scheduled execution of news aggregation workflows.

    Uses APScheduler to coordinate weekly preview and publish jobs.
    Executes the full pipeline: fetch → summarize → compose.
    """

    def __init__(
        self,
        timezone: str = "Europe/London",
        preview_time: str = "18:00",
        publish_time: str = "10:00",
        jobstore_type: str = "sqlite",
        jobstore_path: str = "./scheduler.db",
    ):
        """
        Initialize scheduler with configuration.

        Args:
            timezone: Timezone for job scheduling (e.g., "Europe/London")
            preview_time: Time for preview job in HH:MM format (default: 18:00)
            publish_time: Time for publish job in HH:MM format (default: 10:00)
            jobstore_type: Type of jobstore ("memory" or "sqlite")
            jobstore_path: Path to SQLite database for persistence

        Raises:
            SchedulerError: If configuration is invalid
        """
        self.timezone = timezone
        self.preview_time = preview_time
        self.publish_time = publish_time
        self.jobstore_type = jobstore_type
        self.jobstore_path = jobstore_path

        # Validate configuration
        if not preview_time or not preview_time.strip():
            raise SchedulerError("preview_time cannot be empty")
        if not publish_time or not publish_time.strip():
            raise SchedulerError("publish_time cannot be empty")

        # Get RSS sources from environment or use defaults
        self.rss_sources = os.getenv(
            "RSS_SOURCES",
            "https://techcrunch.com/feed/,https://www.theverge.com/rss/index.xml"
        ).split(",")

        # Initialize scheduler
        self.scheduler = self._create_scheduler()

        log.info(
            "Scheduler initialized",
            timezone=timezone,
            preview_time=preview_time,
            publish_time=publish_time,
            jobstore_type=jobstore_type
        )

    def _create_scheduler(self) -> BackgroundScheduler:
        """
        Create and configure APScheduler instance.

        Returns:
            Configured BackgroundScheduler instance
        """
        # Configure jobstore
        if self.jobstore_type == "memory":
            jobstores = {
                "default": MemoryJobStore()
            }
        elif self.jobstore_type == "sqlite":
            jobstores = {
                "default": SQLAlchemyJobStore(url=f"sqlite:///{self.jobstore_path}")
            }
        else:
            raise SchedulerError(f"Invalid jobstore_type: {self.jobstore_type}")

        # Configure executors
        executors = {
            "default": ThreadPoolExecutor(max_workers=2)
        }

        # Job defaults
        job_defaults = {
            "coalesce": True,  # Combine missed runs
            "max_instances": 1,  # Prevent overlapping executions
            "misfire_grace_time": 300,  # 5 minutes grace period
        }

        # Create scheduler with timezone
        tz = pytz.timezone(self.timezone)
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=tz
        )

        return scheduler

    def schedule_jobs(self) -> None:
        """
        Configure all recurring jobs (preview and publish).

        Creates two cron jobs:
        - Preview job: Thursday 18:00 (default)
        - Publish job: Friday 10:00 (default)
        """
        # Parse schedule times
        preview_hour, preview_minute = parse_schedule_time(self.preview_time)
        publish_hour, publish_minute = parse_schedule_time(self.publish_time)

        # Schedule preview job (Thursday)
        self.scheduler.add_job(
            func=self.run_preview_job,
            trigger=CronTrigger(
                day_of_week=3,  # Thursday (0=Monday)
                hour=preview_hour,
                minute=preview_minute,
                timezone=self.timezone
            ),
            id="preview_job",
            name="Weekly Preview Generation",
            replace_existing=True,
            max_instances=1
        )

        log.info(
            "Preview job scheduled",
            day="Thursday",
            time=self.preview_time,
            timezone=self.timezone
        )

        # Schedule publish job (Friday)
        self.scheduler.add_job(
            func=self.run_publish_job,
            trigger=CronTrigger(
                day_of_week=4,  # Friday (0=Monday)
                hour=publish_hour,
                minute=publish_minute,
                timezone=self.timezone
            ),
            id="publish_job",
            name="Weekly Publication",
            replace_existing=True,
            max_instances=1
        )

        log.info(
            "Publish job scheduled",
            day="Friday",
            time=self.publish_time,
            timezone=self.timezone
        )

    def start(self) -> None:
        """
        Start the scheduler (blocking operation).

        This will block until shutdown() is called or the process is interrupted.
        """
        if not self.scheduler.running:
            self.scheduler.start()
            log.info("Scheduler started")

    def shutdown(self, wait: bool = True) -> None:
        """
        Gracefully shutdown scheduler.

        Args:
            wait: If True, wait for running jobs to complete
        """
        if self.scheduler.running:
            self.scheduler.shutdown(wait=wait)
            log.info("Scheduler shutdown", wait=wait)

    def run_preview_job(self) -> Dict:
        """
        Execute preview generation workflow.

        Runs the full pipeline and logs results without publishing.

        Returns:
            Job execution result dictionary
        """
        week_key = get_week_key_for_date(datetime.now())

        log.info(
            "Preview job started",
            week_key=week_key,
            job_type="preview"
        )

        result = self.execute_pipeline(week_key, is_preview=True)

        log.info(
            "Preview job completed",
            week_key=week_key,
            status=result["status"],
            duration_seconds=result["duration_seconds"]
        )

        return result

    def run_publish_job(self) -> Dict:
        """
        Execute publish workflow.

        Runs the full pipeline and prepares post for publication.

        Returns:
            Job execution result dictionary
        """
        week_key = get_week_key_for_date(datetime.now())

        log.info(
            "Publish job started",
            week_key=week_key,
            job_type="publish"
        )

        result = self.execute_pipeline(week_key, is_preview=False)

        log.info(
            "Publish job completed",
            week_key=week_key,
            status=result["status"],
            duration_seconds=result["duration_seconds"]
        )

        return result

    def execute_pipeline(
        self,
        week_key: str,
        is_preview: bool = True
    ) -> Dict:
        """
        Execute full pipeline: fetch → summarize → compose.

        Args:
            week_key: ISO week identifier (e.g., "2025.W46")
            is_preview: Whether this is a preview or publish job

        Returns:
            Dict with execution results and metadata
        """
        import uuid
        start_time = datetime.now()
        job_id = str(uuid.uuid4())[:8]
        job_type = "preview" if is_preview else "publish"

        result = {
            "job_id": job_id,
            "job_type": job_type,
            "week_key": week_key,
            "status": "failed",
            "started_at": start_time,
            "completed_at": None,
            "duration_seconds": 0.0,
            "articles_fetched": 0,
            "articles_summarized": 0,
            "post_created": False,
            "error": None
        }

        try:
            # Step 1: Fetch articles
            log.info("Pipeline step: fetch", week_key=week_key)
            articles = fetch_news(self.rss_sources)
            result["articles_fetched"] = len(articles)

            log.info(
                "Articles fetched",
                count=len(articles),
                week_key=week_key
            )

            # Step 2: Summarize articles (limit to 10 for cost/time)
            log.info("Pipeline step: summarize", week_key=week_key)
            summaries = []
            articles_to_process = articles[:10]

            for article in articles_to_process:
                try:
                    summary = summarize_article(article)
                    summaries.append(summary)
                    log.debug(
                        "Article summarized",
                        article_url=article.get("link"),
                        week_key=week_key
                    )
                except Exception as e:
                    log.warning(
                        "Failed to summarize article",
                        article_url=article.get("link"),
                        error=str(e),
                        week_key=week_key
                    )
                    continue

            result["articles_summarized"] = len(summaries)

            log.info(
                "Articles summarized",
                count=len(summaries),
                week_key=week_key
            )

            # Step 3: Compose post
            if len(summaries) < 3:
                raise JobExecutionError(
                    f"Insufficient summaries for composition: {len(summaries)} (minimum 3)"
                )

            log.info("Pipeline step: compose", week_key=week_key)
            post = compose_weekly_post(summaries, week_key=week_key)
            result["post_created"] = True
            result["post"] = post

            log.info(
                "Post composed",
                week_key=week_key,
                character_count=post.get("character_count", 0)
            )

            # Success!
            result["status"] = "success"

        except Exception as e:
            log.error(
                "Pipeline execution failed",
                error=str(e),
                week_key=week_key,
                job_type=job_type
            )
            result["error"] = str(e)
            result["status"] = "failed"

        finally:
            end_time = datetime.now()
            result["completed_at"] = end_time
            result["duration_seconds"] = (end_time - start_time).total_seconds()

        return result

    def list_scheduled_jobs(self) -> List[Dict]:
        """
        List all scheduled jobs.

        Returns:
            List of job dictionaries with metadata
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger.__class__.__name__).replace("Trigger", "").lower(),
                "next_run": getattr(job, 'next_run_time', None),
                "max_instances": getattr(job, 'max_instances', None)
            })
        return jobs


# Helper Functions

def parse_schedule_time(time_str: str) -> tuple[int, int]:
    """
    Parse time string (HH:MM) into hour and minute.

    Args:
        time_str: Time in HH:MM format

    Returns:
        Tuple of (hour, minute)

    Raises:
        SchedulerError: If time format is invalid
    """
    try:
        parts = time_str.split(":")
        if len(parts) != 2:
            raise SchedulerError(f"Invalid time format: {time_str}. Expected HH:MM")

        hour = int(parts[0])
        minute = int(parts[1])

        if hour < 0 or hour > 23:
            raise SchedulerError(f"Invalid hour: {hour}. Must be 0-23")
        if minute < 0 or minute > 59:
            raise SchedulerError(f"Invalid minute: {minute}. Must be 0-59")

        return hour, minute

    except (ValueError, AttributeError) as e:
        raise SchedulerError(f"Invalid time format: {time_str}. Expected HH:MM") from e


def get_week_key_for_date(date: datetime) -> str:
    """
    Generate ISO week key (YYYY.Www) for specific date.

    Args:
        date: Date to get week key for

    Returns:
        Week key in format "YYYY.Www" (e.g., "2025.W46")
    """
    iso_calendar = date.isocalendar()
    year = iso_calendar[0]
    week = iso_calendar[1]
    return f"{year}.W{week:02d}"
