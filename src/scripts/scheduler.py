#!/usr/bin/env python3
"""
News Aggregator Scheduler Entry Point

Production script for running the automated news aggregation scheduler.

Usage:
    python src/scripts/scheduler.py              # Start scheduler daemon
    python src/scripts/scheduler.py --preview    # Run preview job now
    python src/scripts/scheduler.py --publish    # Run publish job now
    python src/scripts/scheduler.py --once       # Run once and exit

Environment Variables:
    TIMEZONE           - Scheduler timezone (default: Europe/London)
    PREVIEW_TIME       - Preview job time HH:MM (default: 18:00)
    PUBLISH_TIME       - Publish job time HH:MM (default: 10:00)
    JOBSTORE_TYPE      - "memory" or "sqlite" (default: sqlite)
    JOBSTORE_PATH      - SQLite database path (default: ./scheduler.db)
    RSS_SOURCES        - Comma-separated RSS feed URLs
"""

import os
import sys
import argparse
import signal
import structlog
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from src.core.scheduler import NewsAggregatorScheduler, SchedulerError

# Load environment variables
load_dotenv()

# Setup structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)
log = structlog.get_logger(__name__)


def parse_arguments() -> argparse.Namespace:
    """
    Parse command line arguments.

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="News Aggregator Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--preview",
        action="store_true",
        help="Run preview job immediately and exit"
    )

    parser.add_argument(
        "--publish",
        action="store_true",
        help="Run publish job immediately and exit"
    )

    parser.add_argument(
        "--once",
        action="store_true",
        help="Run preview job once and exit (alias for --preview)"
    )

    parser.add_argument(
        "--timezone",
        default=os.getenv("TIMEZONE", "Europe/London"),
        help="Scheduler timezone (default: Europe/London)"
    )

    parser.add_argument(
        "--preview-time",
        default=os.getenv("PREVIEW_TIME", "18:00"),
        help="Preview job time HH:MM (default: 18:00)"
    )

    parser.add_argument(
        "--publish-time",
        default=os.getenv("PUBLISH_TIME", "10:00"),
        help="Publish job time HH:MM (default: 10:00)"
    )

    parser.add_argument(
        "--jobstore",
        default=os.getenv("JOBSTORE_TYPE", "sqlite"),
        choices=["memory", "sqlite"],
        help="Jobstore type (default: sqlite)"
    )

    parser.add_argument(
        "--jobstore-path",
        default=os.getenv("JOBSTORE_PATH", "./scheduler.db"),
        help="SQLite jobstore path (default: ./scheduler.db)"
    )

    return parser.parse_args()


def setup_signal_handlers(scheduler: NewsAggregatorScheduler) -> None:
    """
    Setup signal handlers for graceful shutdown.

    Args:
        scheduler: Scheduler instance to shutdown on signal
    """
    def signal_handler(signum, frame):
        log.info(
            "Shutdown signal received",
            signal=signal.Signals(signum).name
        )
        scheduler.shutdown(wait=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def run_manual_job(
    scheduler: NewsAggregatorScheduler,
    job_type: str
) -> int:
    """
    Run a job manually and exit.

    Args:
        scheduler: Scheduler instance
        job_type: "preview" or "publish"

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    log.info(
        "Manual job execution started",
        job_type=job_type
    )

    try:
        if job_type == "preview":
            result = scheduler.run_preview_job()
        elif job_type == "publish":
            result = scheduler.run_publish_job()
        else:
            log.error("Invalid job type", job_type=job_type)
            return 1

        if result["status"] == "success":
            log.info(
                "Manual job completed successfully",
                job_type=job_type,
                week_key=result["week_key"],
                articles_fetched=result["articles_fetched"],
                articles_summarized=result["articles_summarized"],
                duration_seconds=result["duration_seconds"]
            )
            return 0
        else:
            log.error(
                "Manual job failed",
                job_type=job_type,
                error=result.get("error")
            )
            return 1

    except Exception as e:
        log.error(
            "Manual job execution failed",
            job_type=job_type,
            error=str(e)
        )
        return 1


def run_daemon(scheduler: NewsAggregatorScheduler) -> int:
    """
    Run scheduler as a daemon.

    Args:
        scheduler: Scheduler instance

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Setup signal handlers for graceful shutdown
        setup_signal_handlers(scheduler)

        # Schedule jobs
        scheduler.schedule_jobs()

        # List scheduled jobs
        jobs = scheduler.list_scheduled_jobs()
        log.info(
            "Jobs scheduled",
            job_count=len(jobs),
            jobs=[j["id"] for j in jobs]
        )

        # Start scheduler (blocking)
        log.info("Starting scheduler daemon...")
        scheduler.start()

        # Keep the main thread alive
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log.info("Keyboard interrupt received")
            scheduler.shutdown(wait=True)

        return 0

    except Exception as e:
        log.error(
            "Scheduler daemon failed",
            error=str(e)
        )
        return 1


def main() -> int:
    """
    Main entry point.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    args = parse_arguments()

    log.info(
        "News Aggregator Scheduler starting",
        timezone=args.timezone,
        preview_time=args.preview_time,
        publish_time=args.publish_time,
        jobstore=args.jobstore
    )

    # Initialize scheduler
    try:
        scheduler = NewsAggregatorScheduler(
            timezone=args.timezone,
            preview_time=args.preview_time,
            publish_time=args.publish_time,
            jobstore_type=args.jobstore,
            jobstore_path=args.jobstore_path
        )
    except SchedulerError as e:
        log.error(
            "Failed to initialize scheduler",
            error=str(e)
        )
        return 1

    # Determine execution mode
    if args.preview or args.once:
        return run_manual_job(scheduler, "preview")
    elif args.publish:
        return run_manual_job(scheduler, "publish")
    else:
        return run_daemon(scheduler)


if __name__ == "__main__":
    sys.exit(main())
