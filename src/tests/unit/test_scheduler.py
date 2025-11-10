"""
Unit tests for the News Aggregation Scheduler module.

Tests cover:
- Scheduler initialization with various configurations
- Job scheduling (preview and publish)
- Pipeline execution orchestration
- Error handling and recovery
- Timezone handling
- Graceful shutdown
- Helper functions
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

# Mock the imports that may not be available in test environment
import sys
sys.modules['src.core.fetcher'] = MagicMock()
sys.modules['src.core.summarizer'] = MagicMock()
sys.modules['src.core.composer'] = MagicMock()

from src.core.scheduler import (
    NewsAggregatorScheduler,
    parse_schedule_time,
    get_week_key_for_date,
    SchedulerError,
    JobExecutionError,
)


class TestSchedulerInitialization:
    """Test scheduler initialization with various configurations"""

    def test_scheduler_initialization_with_defaults(self):
        """Should initialize with default configuration"""
        scheduler = NewsAggregatorScheduler()

        assert scheduler.timezone == "Europe/London"
        assert scheduler.preview_time == "18:00"
        assert scheduler.publish_time == "10:00"
        assert scheduler.jobstore_type == "sqlite"
        assert scheduler.scheduler is not None

    def test_scheduler_initialization_with_custom_timezone(self):
        """Should initialize with custom timezone"""
        scheduler = NewsAggregatorScheduler(timezone="America/New_York")

        assert scheduler.timezone == "America/New_York"

    def test_scheduler_initialization_with_custom_times(self):
        """Should initialize with custom schedule times"""
        scheduler = NewsAggregatorScheduler(
            preview_time="17:00",
            publish_time="09:00"
        )

        assert scheduler.preview_time == "17:00"
        assert scheduler.publish_time == "09:00"

    def test_scheduler_initialization_with_memory_jobstore(self):
        """Should initialize with in-memory jobstore for testing"""
        scheduler = NewsAggregatorScheduler(jobstore_type="memory")

        assert scheduler.jobstore_type == "memory"

    def test_scheduler_initialization_with_sqlite_jobstore(self):
        """Should initialize with SQLite jobstore for persistence"""
        scheduler = NewsAggregatorScheduler(jobstore_type="sqlite")

        assert scheduler.jobstore_type == "sqlite"


class TestScheduleJobs:
    """Test job scheduling functionality"""

    def test_schedule_jobs_creates_preview_job(self):
        """Should schedule preview job for Thursday 18:00"""
        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        scheduler.schedule_jobs()

        jobs = scheduler.list_scheduled_jobs()
        preview_jobs = [j for j in jobs if j["id"] == "preview_job"]

        assert len(preview_jobs) == 1
        assert preview_jobs[0]["trigger"] == "cron"

    def test_schedule_jobs_creates_publish_job(self):
        """Should schedule publish job for Friday 10:00"""
        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        scheduler.schedule_jobs()

        jobs = scheduler.list_scheduled_jobs()
        publish_jobs = [j for j in jobs if j["id"] == "publish_job"]

        assert len(publish_jobs) == 1
        assert publish_jobs[0]["trigger"] == "cron"

    def test_schedule_jobs_with_custom_times(self):
        """Should schedule jobs at custom times"""
        scheduler = NewsAggregatorScheduler(
            preview_time="17:30",
            publish_time="11:45",
            jobstore_type="memory"
        )
        scheduler.schedule_jobs()

        jobs = scheduler.list_scheduled_jobs()
        assert len(jobs) == 2


class TestJobExecution:
    """Test job execution and pipeline orchestration"""

    @patch("src.core.scheduler.fetch_news")
    @patch("src.core.scheduler.summarize_article")
    @patch("src.core.scheduler.compose_weekly_post")
    def test_run_preview_job_executes_pipeline(
        self, mock_compose, mock_summarize, mock_fetch
    ):
        """Should execute full pipeline for preview job"""
        # Setup mocks - need at least 3 articles for composer
        mock_fetch.return_value = [
            {"title": f"Article {i}", "link": f"http://example.com/{i}", "source": "example.com"}
            for i in range(5)
        ]
        mock_summarize.return_value = {
            "article_url": "http://example.com/1",
            "summary": "Summary text",
            "source": "example.com",
            "published_at": datetime.now(),
            "tokens_used": 100,
            "provider": "claude"
        }
        mock_compose.return_value = {
            "week_key": "2025.W46",
            "content": "Post content",
            "character_count": 500
        }

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.run_preview_job()

        assert result["status"] == "success"
        assert result["job_type"] == "preview"
        assert mock_fetch.called
        assert mock_summarize.called
        assert mock_compose.called

    @patch("src.core.scheduler.fetch_news")
    @patch("src.core.scheduler.summarize_article")
    @patch("src.core.scheduler.compose_weekly_post")
    def test_run_publish_job_executes_pipeline(
        self, mock_compose, mock_summarize, mock_fetch
    ):
        """Should execute full pipeline for publish job"""
        # Setup mocks - need at least 3 articles for composer
        mock_fetch.return_value = [
            {"title": f"Article {i}", "link": f"http://example.com/{i}", "source": "example.com"}
            for i in range(5)
        ]
        mock_summarize.return_value = {
            "article_url": "http://example.com",
            "summary": "Summary",
            "source": "example.com",
            "published_at": datetime.now(),
            "tokens_used": 100,
            "provider": "claude"
        }
        mock_compose.return_value = {
            "week_key": "2025.W46",
            "content": "Post content"
        }

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.run_publish_job()

        assert result["status"] == "success"
        assert result["job_type"] == "publish"
        assert mock_fetch.called
        assert mock_summarize.called
        assert mock_compose.called

    @patch("src.core.scheduler.fetch_news")
    def test_execute_pipeline_returns_result_dict(self, mock_fetch):
        """Should return complete result dictionary"""
        mock_fetch.return_value = []

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.execute_pipeline("2025.W46", is_preview=True)

        assert "job_id" in result
        assert "job_type" in result
        assert "week_key" in result
        assert "status" in result
        assert "started_at" in result
        assert "completed_at" in result
        assert "duration_seconds" in result
        assert result["week_key"] == "2025.W46"


class TestPipelineOrchestration:
    """Test full pipeline orchestration"""

    @patch("src.core.scheduler.fetch_news")
    @patch("src.core.scheduler.summarize_article")
    @patch("src.core.scheduler.compose_weekly_post")
    def test_execute_pipeline_fetches_articles(
        self, mock_compose, mock_summarize, mock_fetch
    ):
        """Should fetch articles from configured RSS sources"""
        mock_fetch.return_value = [
            {"title": "Article 1", "link": "http://example.com/1"},
            {"title": "Article 2", "link": "http://example.com/2"},
        ]
        mock_summarize.return_value = {
            "article_url": "http://example.com/1",
            "summary": "Summary",
            "source": "example.com",
            "published_at": datetime.now(),
            "tokens_used": 100,
            "provider": "claude"
        }
        mock_compose.return_value = {"week_key": "2025.W46", "content": "Post"}

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.execute_pipeline("2025.W46")

        mock_fetch.assert_called_once()
        assert result["articles_fetched"] == 2

    @patch("src.core.scheduler.fetch_news")
    @patch("src.core.scheduler.summarize_article")
    @patch("src.core.scheduler.compose_weekly_post")
    def test_execute_pipeline_summarizes_articles(
        self, mock_compose, mock_summarize, mock_fetch
    ):
        """Should summarize each fetched article"""
        articles = [
            {"title": f"Article {i}", "link": f"http://example.com/{i}"}
            for i in range(5)
        ]
        mock_fetch.return_value = articles
        mock_summarize.return_value = {
            "article_url": "http://example.com/1",
            "summary": "Summary",
            "source": "example.com",
            "published_at": datetime.now(),
            "tokens_used": 100,
            "provider": "claude"
        }
        mock_compose.return_value = {"week_key": "2025.W46", "content": "Post"}

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.execute_pipeline("2025.W46")

        # Should summarize up to 10 articles (or all if fewer)
        assert mock_summarize.call_count == 5
        assert result["articles_summarized"] == 5

    @patch("src.core.scheduler.fetch_news")
    @patch("src.core.scheduler.summarize_article")
    @patch("src.core.scheduler.compose_weekly_post")
    def test_execute_pipeline_composes_post(
        self, mock_compose, mock_summarize, mock_fetch
    ):
        """Should compose LinkedIn post from summaries"""
        mock_fetch.return_value = [
            {"title": f"Article {i}", "link": f"http://example.com/{i}", "source": "example.com"}
            for i in range(5)
        ]
        mock_summarize.return_value = {
            "article_url": "http://example.com",
            "summary": "Summary",
            "source": "example.com",
            "published_at": datetime.now(),
            "tokens_used": 100,
            "provider": "claude"
        }
        mock_compose.return_value = {
            "week_key": "2025.W46",
            "content": "Post content",
            "character_count": 500
        }

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.execute_pipeline("2025.W46")

        mock_compose.assert_called_once()
        assert result["post_created"] is True


class TestErrorHandling:
    """Test error handling and recovery"""

    @patch("src.core.scheduler.fetch_news")
    def test_execute_pipeline_handles_fetch_failure(self, mock_fetch):
        """Should handle fetcher exceptions gracefully"""
        mock_fetch.side_effect = Exception("Network error")

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.execute_pipeline("2025.W46")

        assert result["status"] == "failed"
        assert "Network error" in result["error"]
        assert result["articles_fetched"] == 0

    @patch("src.core.scheduler.fetch_news")
    @patch("src.core.scheduler.summarize_article")
    @patch("src.core.scheduler.compose_weekly_post")
    def test_execute_pipeline_handles_summarizer_failure(
        self, mock_compose, mock_summarize, mock_fetch
    ):
        """Should continue pipeline when some articles fail to summarize"""
        # Fetch 5 articles so that after 1 failure we still have 4 successful summaries
        mock_fetch.return_value = [
            {"title": f"Article {i}", "link": f"http://example.com/{i}", "source": "example.com"}
            for i in range(1, 6)
        ]
        # First succeeds, second fails, others succeed
        mock_summarize.side_effect = [
            {"article_url": "http://example.com/1", "summary": "Summary 1", "source": "example.com", "published_at": datetime.now(), "tokens_used": 100, "provider": "claude"},
            Exception("API rate limit"),
            {"article_url": "http://example.com/3", "summary": "Summary 3", "source": "example.com", "published_at": datetime.now(), "tokens_used": 100, "provider": "claude"},
            {"article_url": "http://example.com/4", "summary": "Summary 4", "source": "example.com", "published_at": datetime.now(), "tokens_used": 100, "provider": "claude"},
            {"article_url": "http://example.com/5", "summary": "Summary 5", "source": "example.com", "published_at": datetime.now(), "tokens_used": 100, "provider": "claude"},
        ]
        mock_compose.return_value = {"week_key": "2025.W46", "content": "Post"}

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.execute_pipeline("2025.W46")

        # Should continue with successful summaries (4 out of 5)
        assert result["status"] == "success"
        assert result["articles_summarized"] == 4
        assert mock_compose.called

    @patch("src.core.scheduler.fetch_news")
    @patch("src.core.scheduler.summarize_article")
    @patch("src.core.scheduler.compose_weekly_post")
    def test_execute_pipeline_handles_composer_failure(
        self, mock_compose, mock_summarize, mock_fetch
    ):
        """Should handle composer exceptions gracefully"""
        mock_fetch.return_value = [
            {"title": f"Article {i}", "link": f"http://example.com/{i}", "source": "example.com"}
            for i in range(5)
        ]
        mock_summarize.return_value = {
            "article_url": "http://example.com",
            "summary": "Summary",
            "source": "example.com",
            "published_at": datetime.now(),
            "tokens_used": 100,
            "provider": "claude"
        }
        mock_compose.side_effect = Exception("Composer error")

        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        result = scheduler.execute_pipeline("2025.W46")

        assert result["status"] == "failed"
        assert "Composer error" in result["error"]
        assert result["post_created"] is False


class TestSchedulerLifecycle:
    """Test scheduler startup and shutdown"""

    def test_shutdown_stops_scheduler(self):
        """Should gracefully shutdown scheduler"""
        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        scheduler.schedule_jobs()

        # Start in a non-blocking way for testing
        scheduler.scheduler.start(paused=True)
        assert scheduler.scheduler.running

        scheduler.shutdown(wait=False)
        assert not scheduler.scheduler.running

    def test_list_scheduled_jobs_returns_jobs(self):
        """Should return list of all scheduled jobs"""
        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        scheduler.schedule_jobs()

        jobs = scheduler.list_scheduled_jobs()

        assert len(jobs) == 2
        job_ids = [j["id"] for j in jobs]
        assert "preview_job" in job_ids
        assert "publish_job" in job_ids


class TestHelperFunctions:
    """Test helper utility functions"""

    def test_parse_schedule_time_valid_format(self):
        """Should parse valid time string"""
        hour, minute = parse_schedule_time("18:00")

        assert hour == 18
        assert minute == 0

    def test_parse_schedule_time_with_minutes(self):
        """Should parse time with minutes"""
        hour, minute = parse_schedule_time("17:30")

        assert hour == 17
        assert minute == 30

    def test_parse_schedule_time_invalid_format(self):
        """Should raise error for invalid time format"""
        with pytest.raises(SchedulerError) as exc_info:
            parse_schedule_time("invalid")

        assert "Invalid time format" in str(exc_info.value)

    def test_parse_schedule_time_invalid_hour(self):
        """Should raise error for invalid hour"""
        with pytest.raises(SchedulerError) as exc_info:
            parse_schedule_time("25:00")

        assert "Invalid" in str(exc_info.value)

    def test_get_week_key_for_date(self):
        """Should generate correct ISO week key"""
        date = datetime(2025, 11, 14)  # Week 46 of 2025

        week_key = get_week_key_for_date(date)

        assert week_key == "2025.W46"

    def test_get_week_key_for_date_year_boundary(self):
        """Should handle week keys at year boundary"""
        # First week of January might belong to previous year
        date = datetime(2025, 1, 1)

        week_key = get_week_key_for_date(date)

        # ISO week date may assign this to previous year
        assert week_key.startswith("202")  # Either 2024 or 2025

    def test_get_week_key_for_date_december(self):
        """Should handle weeks in December"""
        date = datetime(2025, 12, 15)

        week_key = get_week_key_for_date(date)

        assert week_key.startswith("2025.W")


class TestTimezoneHandling:
    """Test timezone configuration and handling"""

    def test_scheduler_respects_timezone(self):
        """Should use configured timezone for job scheduling"""
        scheduler = NewsAggregatorScheduler(
            timezone="America/New_York",
            jobstore_type="memory"
        )
        scheduler.schedule_jobs()

        # Verify timezone is set correctly
        assert str(scheduler.scheduler.timezone) == "America/New_York"

    def test_scheduler_with_utc_timezone(self):
        """Should support UTC timezone"""
        scheduler = NewsAggregatorScheduler(
            timezone="UTC",
            jobstore_type="memory"
        )
        scheduler.schedule_jobs()

        assert str(scheduler.scheduler.timezone) == "UTC"


class TestJobPersistence:
    """Test job persistence with different jobstores"""

    def test_memory_jobstore_no_persistence(self):
        """Should use in-memory jobstore without file"""
        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        scheduler.schedule_jobs()

        # Memory jobstore should not create files
        jobstore = scheduler.scheduler._jobstores.get("default")
        assert isinstance(jobstore, MemoryJobStore)

    def test_sqlite_jobstore_with_persistence(self):
        """Should use SQLite jobstore for persistence"""
        scheduler = NewsAggregatorScheduler(
            jobstore_type="sqlite",
            jobstore_path=":memory:"  # Use in-memory SQLite for testing
        )

        # Should use SQLite jobstore
        assert scheduler.jobstore_type == "sqlite"
        jobstore = scheduler.scheduler._jobstores.get("default")
        assert isinstance(jobstore, SQLAlchemyJobStore)


class TestJobIsolation:
    """Test job execution isolation and concurrency control"""

    def test_max_instances_prevents_overlapping_jobs(self):
        """Should configure max_instances to prevent overlaps"""
        scheduler = NewsAggregatorScheduler(jobstore_type="memory")
        scheduler.schedule_jobs()

        jobs = scheduler.list_scheduled_jobs()

        # Each job should have max_instances configured
        for job in jobs:
            assert job.get("max_instances") is not None


class TestConfigurationValidation:
    """Test configuration validation"""

    def test_invalid_timezone_raises_error(self):
        """Should raise error for invalid timezone"""
        with pytest.raises(Exception):  # pytz or APScheduler will raise
            scheduler = NewsAggregatorScheduler(timezone="Invalid/Timezone")
            scheduler.schedule_jobs()

    def test_empty_preview_time_raises_error(self):
        """Should raise error for empty preview time"""
        with pytest.raises(SchedulerError):
            scheduler = NewsAggregatorScheduler(preview_time="")
            scheduler.schedule_jobs()

    def test_empty_publish_time_raises_error(self):
        """Should raise error for empty publish time"""
        with pytest.raises(SchedulerError):
            scheduler = NewsAggregatorScheduler(publish_time="")
            scheduler.schedule_jobs()
