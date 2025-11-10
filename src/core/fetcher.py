"""
RSS Feed Fetcher Module

Fetches and normalizes tech/AI news articles from multiple RSS feeds.
Handles errors gracefully and provides structured logging.
"""

import feedparser
import structlog
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urlparse
from dateutil import parser as date_parser


# Initialize structured logger
logger = structlog.get_logger(__name__)


def fetch_news(sources: List[str], limit_per_source: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch and normalize articles from multiple RSS feeds.

    Args:
        sources: List of RSS feed URLs
        limit_per_source: Maximum articles to fetch per source (default: 5)

    Returns:
        List of normalized article dictionaries with keys:
        - title: Article headline
        - link: Full URL to article
        - source: Feed domain name
        - date: Published date as ISO string
        - published_at: Published date as datetime object

    Raises:
        None (handles errors gracefully and logs them)
    """
    if not sources:
        logger.info("fetch_news_called_with_empty_sources")
        return []

    all_articles = []

    for source_url in sources:
        try:
            logger.info("fetching_feed", source=source_url)

            # Parse the RSS feed
            feed = feedparser.parse(source_url)

            # Check if feed was parsed successfully
            if hasattr(feed, 'bozo_exception'):
                logger.warning(
                    "feed_parse_error",
                    source=source_url,
                    error=str(feed.bozo_exception)
                )
                # Continue with what we got, if anything
                if not feed.entries:
                    continue

            # Process entries (limit to specified number)
            entries = feed.entries[:limit_per_source]

            for entry in entries:
                try:
                    normalized = normalize_entry(entry, source_url)
                    all_articles.append(normalized)
                except Exception as e:
                    logger.error(
                        "entry_normalization_failed",
                        source=source_url,
                        error=str(e)
                    )
                    continue

            logger.info(
                "feed_fetched_successfully",
                source=source_url,
                articles_count=len(entries)
            )

        except Exception as e:
            logger.error(
                "feed_fetch_failed",
                source=source_url,
                error=str(e)
            )
            continue

    logger.info(
        "fetch_news_completed",
        total_sources=len(sources),
        total_articles=len(all_articles)
    )

    return all_articles


def normalize_entry(entry: Dict[str, Any], source_url: str) -> Dict[str, Any]:
    """
    Convert feedparser entry to normalized format.

    Args:
        entry: Raw feedparser entry dictionary
        source_url: Original RSS feed URL

    Returns:
        Normalized article dictionary with required fields
    """
    # Extract title (required)
    title = entry.get("title", "Untitled")

    # Extract link (required)
    link = entry.get("link", "")

    # Extract and parse published date
    date_string = entry.get("published", entry.get("updated", ""))

    if date_string:
        published_at = parse_published_date(date_string)
        date_iso = published_at.isoformat()
    else:
        # Use current time as fallback
        published_at = datetime.now()
        date_iso = published_at.isoformat()
        logger.debug("no_published_date_using_current_time", link=link)

    # Extract source domain
    source = extract_domain(source_url)

    return {
        "title": title,
        "link": link,
        "source": source,
        "date": date_iso,
        "published_at": published_at
    }


def parse_published_date(date_string: str) -> datetime:
    """
    Parse various date formats to datetime object.

    Handles common RSS date formats including:
    - RFC 822: "Mon, 10 Nov 2025 10:00:00 GMT"
    - ISO 8601: "2025-11-10T10:00:00Z"
    - Other common formats

    Args:
        date_string: Date string in various formats

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date string cannot be parsed
    """
    try:
        # dateutil.parser is very flexible and handles most formats
        return date_parser.parse(date_string)
    except (ValueError, TypeError) as e:
        logger.warning(
            "date_parse_failed",
            date_string=date_string,
            error=str(e)
        )
        # Return current time as fallback
        return datetime.now()


def extract_domain(url: str) -> str:
    """
    Extract clean domain name from URL.

    Removes www. prefix and keeps only the domain name.

    Args:
        url: Full URL (e.g., "https://www.example.com/feed/")

    Returns:
        Clean domain name (e.g., "example.com")
    """
    try:
        parsed = urlparse(url)
        domain = parsed.netloc

        # Remove www. prefix if present
        if domain.startswith("www."):
            domain = domain[4:]

        return domain if domain else url

    except Exception as e:
        logger.warning("domain_extraction_failed", url=url, error=str(e))
        return url
