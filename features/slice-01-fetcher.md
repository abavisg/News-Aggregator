# Slice 01: RSS Feed Fetcher

## Goal
Implement a robust RSS feed fetcher that retrieves and normalizes tech/AI news articles from multiple sources.

## Acceptance Criteria

1. **Functional Requirements:**
   - Fetch articles from a list of RSS feed URLs
   - Normalize article data to consistent format: `{title, link, source, date, published_at}`
   - Limit to 5 articles per source (most recent)
   - Handle invalid/unreachable URLs gracefully (no crashes)
   - Support common RSS/Atom feed formats

2. **Non-Functional Requirements:**
   - Response time: < 5 seconds for 10 feeds
   - Test coverage: ≥ 90%
   - Error handling: return empty list on failures
   - Logging: structured logs for fetch operations

3. **Data Format:**
   ```python
   {
       "title": str,           # Article headline
       "link": str,            # Full URL to article
       "source": str,          # Feed domain or name
       "date": str,            # Published date (ISO 8601)
       "published_at": datetime # Parsed datetime object
   }
   ```

## Technical Design

### Module: `src/core/fetcher.py`

**Main Function:**
```python
def fetch_news(sources: list[str], limit_per_source: int = 5) -> list[dict]:
    """
    Fetch and normalize articles from multiple RSS feeds.

    Args:
        sources: List of RSS feed URLs
        limit_per_source: Maximum articles to fetch per source (default: 5)

    Returns:
        List of normalized article dictionaries

    Raises:
        None (handles errors gracefully and logs them)
    """
```

**Helper Functions:**
```python
def normalize_entry(entry: dict, source_url: str) -> dict:
    """Convert feedparser entry to normalized format"""

def parse_published_date(date_string: str) -> datetime:
    """Parse various date formats to datetime object"""

def extract_domain(url: str) -> str:
    """Extract clean domain name from URL"""
```

## Test Cases

### Unit Tests (`src/tests/unit/test_fetcher.py`)

1. `test_fetch_news_returns_normalized_articles()`
   - Given: Valid RSS feed URL
   - When: fetch_news() is called
   - Then: Returns list of normalized article dicts

2. `test_fetch_news_limits_articles_per_source()`
   - Given: Feed with 20+ articles
   - When: fetch_news() called with limit=5
   - Then: Returns exactly 5 articles

3. `test_fetch_news_handles_invalid_url_gracefully()`
   - Given: Invalid/unreachable URL
   - When: fetch_news() is called
   - Then: Returns empty list, no exception raised

4. `test_fetch_news_handles_multiple_sources()`
   - Given: List of 3 valid RSS feeds
   - When: fetch_news() is called
   - Then: Returns combined articles from all sources

5. `test_normalize_entry_creates_correct_format()`
   - Given: Raw feedparser entry
   - When: normalize_entry() is called
   - Then: Returns dict with required keys

6. `test_parse_published_date_handles_various_formats()`
   - Given: Different date string formats
   - When: parse_published_date() is called
   - Then: Returns valid datetime object

7. `test_extract_domain_returns_clean_name()`
   - Given: Full RSS feed URL
   - When: extract_domain() is called
   - Then: Returns clean domain name

8. `test_fetch_news_with_empty_source_list()`
   - Given: Empty list of sources
   - When: fetch_news() is called
   - Then: Returns empty list

## Dependencies

- `feedparser==6.0.10` - RSS/Atom feed parsing
- `python-dateutil==2.8.2` - Date parsing
- `structlog==23.2.0` - Structured logging

## Initial Sources (for testing)

Use these 5 sources for initial testing:
1. `https://techcrunch.com/feed/`
2. `https://www.theverge.com/rss/index.xml`
3. `https://www.wired.com/feed/rss`
4. `https://feeds.arstechnica.com/arstechnica/index`
5. `https://venturebeat.com/feed/`

## Success Metrics

- All 8 test cases pass
- Code coverage ≥ 90% for fetcher.py
- Successfully fetches from 5 real RSS feeds
- Average fetch time < 5 seconds for all sources

## Out of Scope (Future Slices)

- Content extraction/scraping (full article text)
- Deduplication logic
- Database persistence
- Caching mechanisms
- Async/concurrent fetching

## Definition of Done

- ✅ All tests pass locally and in CI
- ✅ Coverage report shows ≥ 90% for fetcher.py
- ✅ Code follows PEP 8 and passes ruff/black
- ✅ Structured logging implemented
- ✅ Documentation strings complete
- ✅ BUILD_LOG.md updated
- ✅ Committed with conventional commit message

---

**Created:** 2025-11-10
**Author:** Giorgos Ampavis
**Status:** In Progress
