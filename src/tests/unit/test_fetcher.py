"""
Unit tests for RSS feed fetcher module.

Following TDD principles - tests written before implementation.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from src.core.fetcher import (
    fetch_news,
    normalize_entry,
    parse_published_date,
    extract_domain
)


@pytest.mark.unit
@patch('src.core.fetcher.feedparser.parse')
def test_fetch_news_returns_normalized_articles(mock_parse):
    """
    Given a valid RSS feed URL
    When fetch_news() is called
    Then it returns a list of normalized article dictionaries
    """
    # Arrange
    sources = ["https://techcrunch.com/feed/"]

    # Mock feedparser response
    mock_feed = Mock()
    mock_feed.entries = [
        {
            "title": "AI Breakthrough Announced",
            "link": "https://techcrunch.com/2025/11/10/ai-breakthrough/",
            "published": "Mon, 10 Nov 2025 10:00:00 GMT"
        },
        {
            "title": "New Python Framework Released",
            "link": "https://techcrunch.com/2025/11/09/python-framework/",
            "published": "Sun, 09 Nov 2025 15:00:00 GMT"
        }
    ]
    mock_parse.return_value = mock_feed

    # Act
    articles = fetch_news(sources)

    # Assert
    assert isinstance(articles, list)
    assert len(articles) > 0

    # Check normalized structure
    article = articles[0]
    assert "title" in article
    assert "link" in article
    assert "source" in article
    assert "date" in article
    assert "published_at" in article

    assert isinstance(article["title"], str)
    assert isinstance(article["link"], str)
    assert isinstance(article["source"], str)
    assert isinstance(article["date"], str)
    assert isinstance(article["published_at"], datetime)


@pytest.mark.unit
@patch('src.core.fetcher.feedparser.parse')
def test_fetch_news_limits_articles_per_source(mock_parse):
    """
    Given a feed with many articles
    When fetch_news() is called with limit=5
    Then it returns exactly 5 articles per source
    """
    # Arrange
    sources = ["https://techcrunch.com/feed/"]
    limit = 3

    # Mock feedparser response with more articles than limit
    mock_feed = Mock()
    mock_feed.entries = [
        {"title": f"Article {i}", "link": f"https://example.com/{i}", "published": "Mon, 10 Nov 2025 10:00:00 GMT"}
        for i in range(10)  # 10 articles available
    ]
    mock_parse.return_value = mock_feed

    # Act
    articles = fetch_news(sources, limit_per_source=limit)

    # Assert
    assert len(articles) == limit  # Should return exactly limit number


@pytest.mark.unit
def test_fetch_news_handles_invalid_url_gracefully():
    """
    Given an invalid/unreachable URL
    When fetch_news() is called
    Then it returns an empty list without raising exceptions
    """
    # Arrange
    sources = ["https://this-domain-definitely-does-not-exist-12345.com/feed/"]

    # Act & Assert - should not raise exception
    articles = fetch_news(sources)

    assert isinstance(articles, list)
    assert len(articles) == 0


@pytest.mark.unit
@patch('src.core.fetcher.feedparser.parse')
def test_fetch_news_handles_multiple_sources(mock_parse):
    """
    Given a list of 3 valid RSS feeds
    When fetch_news() is called
    Then it returns combined articles from all sources
    """
    # Arrange
    sources = [
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/index.xml",
        "https://www.wired.com/feed/rss"
    ]

    # Mock feedparser to return different articles for each source
    def mock_parse_side_effect(url):
        mock_feed = Mock()
        if "techcrunch" in url:
            mock_feed.entries = [{"title": "TC Article", "link": "https://tc.com/1", "published": "Mon, 10 Nov 2025 10:00:00 GMT"}]
        elif "theverge" in url:
            mock_feed.entries = [{"title": "Verge Article", "link": "https://verge.com/1", "published": "Mon, 10 Nov 2025 11:00:00 GMT"}]
        else:
            mock_feed.entries = [{"title": "Wired Article", "link": "https://wired.com/1", "published": "Mon, 10 Nov 2025 12:00:00 GMT"}]
        return mock_feed

    mock_parse.side_effect = mock_parse_side_effect

    # Act
    articles = fetch_news(sources, limit_per_source=3)

    # Assert
    assert isinstance(articles, list)
    assert len(articles) == 3  # One from each source

    # Should have articles from multiple sources
    unique_sources = set(article["source"] for article in articles)
    assert len(unique_sources) == 3


@pytest.mark.unit
def test_normalize_entry_creates_correct_format():
    """
    Given a raw feedparser entry
    When normalize_entry() is called
    Then it returns a dict with all required keys
    """
    # Arrange
    mock_entry = {
        "title": "AI Breakthrough Announced",
        "link": "https://example.com/article",
        "published": "Mon, 10 Nov 2025 10:00:00 GMT"
    }
    source_url = "https://example.com/feed/"

    # Act
    normalized = normalize_entry(mock_entry, source_url)

    # Assert
    assert "title" in normalized
    assert "link" in normalized
    assert "source" in normalized
    assert "date" in normalized
    assert "published_at" in normalized

    assert normalized["title"] == "AI Breakthrough Announced"
    assert normalized["link"] == "https://example.com/article"
    assert isinstance(normalized["published_at"], datetime)


@pytest.mark.unit
def test_parse_published_date_handles_various_formats():
    """
    Given different date string formats
    When parse_published_date() is called
    Then it returns a valid datetime object
    """
    # Arrange
    date_formats = [
        "Mon, 10 Nov 2025 10:00:00 GMT",
        "2025-11-10T10:00:00Z",
        "2025-11-10 10:00:00",
        "Mon, 10 Nov 2025 10:00:00 +0000"
    ]

    # Act & Assert
    for date_string in date_formats:
        result = parse_published_date(date_string)
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 10


@pytest.mark.unit
def test_extract_domain_returns_clean_name():
    """
    Given a full RSS feed URL
    When extract_domain() is called
    Then it returns a clean domain name
    """
    # Arrange
    test_cases = [
        ("https://techcrunch.com/feed/", "techcrunch.com"),
        ("https://www.theverge.com/rss/index.xml", "theverge.com"),
        ("https://feeds.arstechnica.com/arstechnica/index", "arstechnica.com"),
    ]

    # Act & Assert
    for url, expected_domain in test_cases:
        result = extract_domain(url)
        assert expected_domain in result or result == expected_domain


@pytest.mark.unit
def test_fetch_news_with_empty_source_list():
    """
    Given an empty list of sources
    When fetch_news() is called
    Then it returns an empty list
    """
    # Arrange
    sources = []

    # Act
    articles = fetch_news(sources)

    # Assert
    assert isinstance(articles, list)
    assert len(articles) == 0


@pytest.mark.unit
@patch('src.core.fetcher.feedparser.parse')
def test_fetch_news_handles_malformed_feed(mock_parse):
    """
    Given a URL that returns non-RSS content
    When fetch_news() is called
    Then it handles the error gracefully and returns empty list
    """
    # Arrange
    sources = ["https://www.google.com"]  # Not an RSS feed

    # Mock feedparser to simulate a malformed feed
    mock_feed = Mock()
    mock_feed.entries = []  # No entries
    mock_feed.bozo_exception = Exception("Not a valid RSS feed")
    mock_parse.return_value = mock_feed

    # Act
    articles = fetch_news(sources)

    # Assert
    assert isinstance(articles, list)
    assert len(articles) == 0  # Should return empty list


@pytest.mark.unit
def test_normalize_entry_handles_missing_fields():
    """
    Given a feedparser entry with missing optional fields
    When normalize_entry() is called
    Then it provides sensible defaults
    """
    # Arrange
    mock_entry = {
        "title": "Article without date",
        "link": "https://example.com/no-date"
        # Note: 'published' field is missing
    }
    source_url = "https://example.com/feed/"

    # Act
    normalized = normalize_entry(mock_entry, source_url)

    # Assert
    assert "title" in normalized
    assert "link" in normalized
    assert "source" in normalized
    assert "date" in normalized  # Should provide default
    assert "published_at" in normalized  # Should provide default (e.g., current time)


@pytest.mark.unit
def test_parse_published_date_handles_invalid_format():
    """
    Given an unparseable date string
    When parse_published_date() is called
    Then it returns current datetime as fallback
    """
    # Arrange
    invalid_date = "not-a-valid-date-at-all"

    # Act
    result = parse_published_date(invalid_date)

    # Assert
    assert isinstance(result, datetime)
    # Should be close to current time (within last minute)
    now = datetime.now()
    time_diff = abs((now - result).total_seconds())
    assert time_diff < 60  # Within 60 seconds


@pytest.mark.unit
def test_extract_domain_handles_invalid_url():
    """
    Given a malformed URL
    When extract_domain() is called
    Then it returns the original URL as fallback
    """
    # Arrange
    invalid_url = "not-a-url"

    # Act
    result = extract_domain(invalid_url)

    # Assert
    assert result == invalid_url  # Returns original as fallback


@pytest.mark.unit
@patch('src.core.fetcher.feedparser.parse')
def test_fetch_news_handles_exception_during_normalization(mock_parse):
    """
    Given an entry that causes normalization to fail
    When fetch_news() is called
    Then it skips that entry and continues with others
    """
    # Arrange
    sources = ["https://example.com/feed/"]

    # Mock feedparser with entries, one will fail normalization
    mock_feed = Mock()
    mock_feed.entries = [
        {"title": "Good Article", "link": "https://example.com/1", "published": "Mon, 10 Nov 2025 10:00:00 GMT"},
        {"title": None, "link": None},  # This might cause issues
        {"title": "Another Good Article", "link": "https://example.com/2", "published": "Mon, 10 Nov 2025 11:00:00 GMT"}
    ]
    mock_parse.return_value = mock_feed

    # Act
    articles = fetch_news(sources)

    # Assert
    # Should get at least the valid articles
    assert isinstance(articles, list)
    assert len(articles) >= 2


@pytest.mark.unit
@patch('src.core.fetcher.feedparser.parse')
def test_fetch_news_handles_feedparser_exception(mock_parse):
    """
    Given feedparser.parse raises an exception
    When fetch_news() is called
    Then it logs the error and continues with other sources
    """
    # Arrange
    sources = [
        "https://will-fail.com/feed/",
        "https://will-succeed.com/feed/"
    ]

    # Mock feedparser to raise exception for first source, succeed for second
    def mock_parse_side_effect(url):
        if "will-fail" in url:
            raise Exception("Network error")
        else:
            mock_feed = Mock()
            mock_feed.entries = [
                {"title": "Success Article", "link": "https://success.com/1", "published": "Mon, 10 Nov 2025 10:00:00 GMT"}
            ]
            return mock_feed

    mock_parse.side_effect = mock_parse_side_effect

    # Act
    articles = fetch_news(sources)

    # Assert
    assert isinstance(articles, list)
    assert len(articles) == 1  # Only from the successful source
    assert articles[0]["title"] == "Success Article"
