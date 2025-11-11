# Slice 07: Source Discovery Agent

## Goal
Implement an automated source discovery agent that continuously finds, evaluates, and recommends new RSS feeds for inclusion in the news aggregation system. The agent should score sources based on relevance, uniqueness, and quality, maintain a lifecycle workflow, and provide approval mechanisms.

## Acceptance Criteria

1. **Functional Requirements:**
   - Discover new RSS sources from multiple inputs (RSS directories, Techmeme, Hacker News, outbound links)
   - Score sources using three metrics:
     - `relevance_score`: % of posts matching tech/AI keywords (threshold: ≥70%)
     - `overlap_score`: Jaccard similarity with approved feeds (threshold: <0.4)
     - `quality_score`: Domain authority proxy based on multiple signals
   - Maintain source lifecycle: candidate → approved → deprecated
   - Generate weekly report at `/docs/source-candidates.md`
   - Manual approval workflow with optional auto-approval via feature flag
   - Track discovery metadata (discovered_at, last_evaluated, evaluation_count)
   - Support for batch evaluation of candidate sources
   - Deprecation detection for inactive or low-quality sources

2. **Non-Functional Requirements:**
   - Test coverage: ≥ 80%
   - Performance: Evaluate 100 sources in < 60 seconds
   - Discovery runs: Weekly (configurable via scheduler)
   - Storage: SQLite sources table with proper indexing
   - Rate limiting: Respect robots.txt and implement backoff
   - Zero impact on existing functionality

3. **Scoring Algorithm Details:**
   ```python
   # Relevance Score (0.0-1.0)
   # Count posts matching tech/AI keywords
   tech_keywords = ["AI", "machine learning", "startup", "technology",
                    "software", "developer", "programming", "cloud",
                    "cybersecurity", "blockchain", "SaaS"]
   relevance_score = matching_posts / total_posts

   # Overlap Score (0.0-1.0, lower is better)
   # Jaccard similarity: intersection / union of article titles
   overlap_score = len(common_articles) / len(all_articles)

   # Quality Score (0.0-1.0)
   # Composite score based on:
   # - Domain age (older is better, proxy via DNS lookup)
   # - Post frequency (1-3 posts/day ideal)
   # - Content length (longer articles = higher quality)
   # - HTTPS availability (security indicator)
   # - Valid RSS format (well-formed XML)
   quality_score = weighted_average([
       (domain_age_score, 0.2),
       (frequency_score, 0.3),
       (content_length_score, 0.2),
       (https_score, 0.1),
       (valid_rss_score, 0.2)
   ])

   # Overall Score
   # Source is recommended if ALL conditions met:
   # - relevance_score >= 0.70
   # - overlap_score < 0.40
   # - quality_score >= 0.60
   ```

4. **Discovery Sources:**
   - **RSS Directories:** Feedspot, Feedly, Alltop tech categories
   - **Techmeme:** Parse sidebar for popular tech blogs
   - **Hacker News:** Extract domains from top stories
   - **Outbound Links:** Follow links from current approved sources

5. **Source Lifecycle States:**
   ```python
   class SourceStatus(Enum):
       CANDIDATE = "candidate"      # Newly discovered, pending evaluation
       APPROVED = "approved"        # Manually approved, active in fetcher
       DEPRECATED = "deprecated"    # Inactive or low quality, removed
       REJECTED = "rejected"        # Manually rejected, not suitable
   ```

## Technical Design

### Module: `src/core/source_discovery.py`

**Main Classes:**

```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional


class SourceStatus(Enum):
    """Source lifecycle states"""
    CANDIDATE = "candidate"
    APPROVED = "approved"
    DEPRECATED = "deprecated"
    REJECTED = "rejected"


@dataclass
class SourceCandidate:
    """Represents a discovered RSS source"""
    domain: str
    feed_url: str
    discovered_from: str  # "techmeme", "hn", "directory", "outbound_link"
    discovered_at: datetime
    relevance_score: float
    overlap_score: float
    quality_score: float
    status: SourceStatus
    last_evaluated: Optional[datetime] = None
    evaluation_count: int = 0
    sample_articles: Optional[List[Dict]] = None


class SourceDiscoveryAgent:
    """
    Discovers and evaluates new RSS sources for the aggregator.
    """

    def __init__(
        self,
        db_path: str = "./news_aggregator.db",
        auto_approve: bool = False
    ):
        """
        Initialize source discovery agent.

        Args:
            db_path: Path to SQLite database
            auto_approve: If True, auto-approve sources meeting thresholds
        """

    def discover_from_techmeme(self, limit: int = 20) -> List[str]:
        """
        Discover sources from Techmeme sidebar.

        Returns:
            List of feed URLs found on Techmeme
        """

    def discover_from_hackernews(self, days: int = 7, min_score: int = 100) -> List[str]:
        """
        Discover sources from Hacker News top stories.

        Args:
            days: Look back N days
            min_score: Minimum story score threshold

        Returns:
            List of feed URLs from HN stories
        """

    def discover_from_directories(self, categories: List[str] = None) -> List[str]:
        """
        Discover sources from RSS directories.

        Args:
            categories: List of categories to search (e.g., ["tech", "ai"])

        Returns:
            List of feed URLs from directories
        """

    def discover_from_outbound_links(self, source_urls: List[str], limit: int = 10) -> List[str]:
        """
        Discover sources by following links from approved sources.

        Args:
            source_urls: List of approved source URLs to crawl
            limit: Max links to follow per source

        Returns:
            List of feed URLs discovered from outbound links
        """

    def evaluate_source(self, feed_url: str) -> SourceCandidate:
        """
        Evaluate a candidate source and compute all scores.

        Args:
            feed_url: URL of RSS feed to evaluate

        Returns:
            SourceCandidate with computed scores
        """

    def calculate_relevance_score(self, articles: List[Dict]) -> float:
        """
        Calculate % of articles matching tech/AI keywords.

        Args:
            articles: List of article dicts with 'title' and 'description'

        Returns:
            Relevance score (0.0-1.0)
        """

    def calculate_overlap_score(self, feed_url: str, articles: List[Dict]) -> float:
        """
        Calculate Jaccard similarity with approved sources.

        Args:
            feed_url: URL of candidate feed
            articles: Articles from candidate feed

        Returns:
            Overlap score (0.0-1.0, lower is better)
        """

    def calculate_quality_score(self, feed_url: str, articles: List[Dict]) -> float:
        """
        Calculate composite quality score.

        Args:
            feed_url: URL of candidate feed
            articles: Articles from candidate feed

        Returns:
            Quality score (0.0-1.0)
        """

    def is_source_recommended(self, candidate: SourceCandidate) -> bool:
        """
        Determine if source meets approval thresholds.

        Args:
            candidate: Source candidate to evaluate

        Returns:
            True if all thresholds met
        """

    def save_candidate(self, candidate: SourceCandidate) -> None:
        """
        Save candidate to database.

        Args:
            candidate: Source candidate to persist
        """

    def get_candidates(
        self,
        status: Optional[SourceStatus] = None,
        min_score: Optional[float] = None
    ) -> List[SourceCandidate]:
        """
        Retrieve source candidates from database.

        Args:
            status: Filter by status
            min_score: Minimum relevance score threshold

        Returns:
            List of matching source candidates
        """

    def approve_source(self, feed_url: str) -> None:
        """
        Manually approve a candidate source.

        Args:
            feed_url: URL of feed to approve
        """

    def reject_source(self, feed_url: str, reason: Optional[str] = None) -> None:
        """
        Manually reject a candidate source.

        Args:
            feed_url: URL of feed to reject
            reason: Optional rejection reason
        """

    def deprecate_inactive_sources(self, days_inactive: int = 30) -> List[str]:
        """
        Mark approved sources as deprecated if no recent articles.

        Args:
            days_inactive: Days without new content before deprecation

        Returns:
            List of deprecated feed URLs
        """

    def run_discovery_cycle(self) -> Dict:
        """
        Run complete discovery cycle:
        1. Discover from all sources
        2. Evaluate candidates
        3. Save to database
        4. Generate report
        5. Auto-approve if enabled

        Returns:
            Summary dict with counts and stats
        """

    def generate_candidates_report(self, output_path: str = "./docs/source-candidates.md") -> None:
        """
        Generate markdown report of candidate sources.

        Args:
            output_path: Path to output markdown file
        """


class SourceEvaluator:
    """
    Helper class for source evaluation logic.
    """

    TECH_KEYWORDS = [
        "AI", "artificial intelligence", "machine learning", "ML",
        "startup", "technology", "software", "developer", "programming",
        "cloud", "AWS", "Azure", "GCP", "cybersecurity", "blockchain",
        "cryptocurrency", "SaaS", "API", "DevOps", "data science"
    ]

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""

    @staticmethod
    def fetch_feed_articles(feed_url: str, limit: int = 20) -> List[Dict]:
        """Fetch recent articles from RSS feed"""

    @staticmethod
    def check_https(url: str) -> bool:
        """Check if URL uses HTTPS"""

    @staticmethod
    def estimate_domain_age(domain: str) -> float:
        """Estimate domain age (0.0-1.0 score)"""

    @staticmethod
    def calculate_post_frequency(articles: List[Dict]) -> float:
        """Calculate posts per day (return score 0.0-1.0)"""

    @staticmethod
    def calculate_content_quality(articles: List[Dict]) -> float:
        """Analyze content length and quality (return score 0.0-1.0)"""
```

### Database Schema Updates: `src/core/database.py`

Ensure sources table exists with proper fields:

```python
CREATE TABLE IF NOT EXISTS sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT NOT NULL,
    feed_url TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'candidate',  -- candidate|approved|deprecated|rejected
    discovered_from TEXT,  -- techmeme|hn|directory|outbound_link
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_evaluated TIMESTAMP,
    evaluation_count INTEGER DEFAULT 0,
    relevance_score REAL,
    overlap_score REAL,
    quality_score REAL,
    rejection_reason TEXT,
    approved_by TEXT,
    approved_at TIMESTAMP,
    last_fetch_at TIMESTAMP,
    total_articles_fetched INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
CREATE INDEX IF NOT EXISTS idx_sources_feed_url ON sources(feed_url);
CREATE INDEX IF NOT EXISTS idx_sources_relevance_score ON sources(relevance_score);
```

### API Endpoints: `src/api/main.py` (additions)

```python
from src.core.source_discovery import SourceDiscoveryAgent, SourceStatus

discovery_agent = SourceDiscoveryAgent()


@app.get("/v1/sources/candidates")
async def get_source_candidates(
    status: Optional[str] = None,
    min_score: Optional[float] = None
):
    """
    Get source candidates with optional filters.

    Query params:
        status: candidate|approved|deprecated|rejected
        min_score: Minimum relevance score (0.0-1.0)
    """
    status_enum = SourceStatus(status) if status else None
    candidates = discovery_agent.get_candidates(
        status=status_enum,
        min_score=min_score
    )
    return {"candidates": [c.__dict__ for c in candidates]}


@app.post("/v1/sources/discover")
async def run_discovery():
    """
    Manually trigger source discovery cycle.

    Returns summary of discovered and evaluated sources.
    """
    result = discovery_agent.run_discovery_cycle()
    return result


@app.post("/v1/sources/{feed_url:path}/approve")
async def approve_source(feed_url: str):
    """
    Approve a candidate source for use in fetcher.
    """
    discovery_agent.approve_source(feed_url)
    return {"status": "approved", "feed_url": feed_url}


@app.post("/v1/sources/{feed_url:path}/reject")
async def reject_source(feed_url: str, reason: Optional[str] = None):
    """
    Reject a candidate source.
    """
    discovery_agent.reject_source(feed_url, reason)
    return {"status": "rejected", "feed_url": feed_url}


@app.get("/v1/sources/approved")
async def get_approved_sources():
    """
    Get list of approved sources for fetcher.
    """
    sources = discovery_agent.get_candidates(status=SourceStatus.APPROVED)
    return {
        "sources": [
            {"domain": s.domain, "feed_url": s.feed_url, "quality_score": s.quality_score}
            for s in sources
        ]
    }


@app.post("/v1/sources/deprecate-inactive")
async def deprecate_inactive_sources(days: int = 30):
    """
    Mark inactive sources as deprecated.

    Query params:
        days: Days without new content before deprecation (default: 30)
    """
    deprecated = discovery_agent.deprecate_inactive_sources(days_inactive=days)
    return {"deprecated_count": len(deprecated), "deprecated_urls": deprecated}
```

## Integration with Existing Modules

### 1. Scheduler (`src/core/scheduler.py`)

Add weekly discovery job:

```python
from src.core.source_discovery import SourceDiscoveryAgent
from .observability import get_logger

logger = get_logger(__name__)
discovery_agent = SourceDiscoveryAgent()


def run_source_discovery():
    """Run weekly source discovery cycle"""
    logger.info("Starting weekly source discovery")

    try:
        result = discovery_agent.run_discovery_cycle()
        logger.info(
            "Source discovery completed",
            context={
                "discovered_count": result["discovered_count"],
                "evaluated_count": result["evaluated_count"],
                "recommended_count": result["recommended_count"]
            }
        )
    except Exception as e:
        logger.error(
            "Source discovery failed",
            error_code="DISCOVERY_ERROR",
            error_message=str(e)
        )
        raise


# Add to scheduler jobs
scheduler.add_job(
    run_source_discovery,
    trigger=CronTrigger(
        day_of_week="mon",  # Run every Monday
        hour=9,
        minute=0,
        timezone=pytz.timezone(TIMEZONE)
    ),
    id="source_discovery",
    name="Weekly Source Discovery",
    replace_existing=True
)
```

### 2. Fetcher (`src/core/fetcher.py`)

Update to fetch only approved sources:

```python
from src.core.source_discovery import SourceDiscoveryAgent, SourceStatus

def get_active_sources() -> List[str]:
    """Get list of approved RSS sources"""
    discovery_agent = SourceDiscoveryAgent()
    approved = discovery_agent.get_candidates(status=SourceStatus.APPROVED)
    return [source.feed_url for source in approved]


def fetch_news() -> list[dict]:
    """Fetch news from all approved sources"""
    sources = get_active_sources()
    # ... existing fetch logic ...
```

## Testing Strategy

### Unit Tests: `src/tests/unit/test_source_discovery.py`

```python
import pytest
from src.core.source_discovery import (
    SourceDiscoveryAgent,
    SourceCandidate,
    SourceStatus,
    SourceEvaluator
)


class TestSourceEvaluator:
    """Test source evaluation helper functions"""

    def test_extract_domain(self):
        """Domain extraction works correctly"""

    def test_fetch_feed_articles(self):
        """RSS feed parsing works"""

    def test_check_https(self):
        """HTTPS detection works"""

    def test_calculate_post_frequency(self):
        """Post frequency calculation accurate"""

    def test_calculate_content_quality(self):
        """Content quality scoring works"""


class TestSourceDiscoveryAgent:
    """Test source discovery agent functionality"""

    def test_discover_from_techmeme(self, mock_techmeme):
        """Techmeme discovery finds sources"""

    def test_discover_from_hackernews(self, mock_hn_api):
        """HN discovery finds sources"""

    def test_discover_from_directories(self, mock_directory):
        """Directory discovery finds sources"""

    def test_discover_from_outbound_links(self, mock_html):
        """Outbound link discovery works"""

    def test_calculate_relevance_score_high(self):
        """High relevance score for tech content"""

    def test_calculate_relevance_score_low(self):
        """Low relevance score for non-tech content"""

    def test_calculate_overlap_score_high(self):
        """High overlap detected correctly"""

    def test_calculate_overlap_score_low(self):
        """Low overlap detected correctly"""

    def test_calculate_quality_score(self):
        """Quality score composite calculation works"""

    def test_is_source_recommended_all_pass(self):
        """Source recommended when all thresholds met"""

    def test_is_source_recommended_fail_relevance(self):
        """Source not recommended with low relevance"""

    def test_is_source_recommended_fail_overlap(self):
        """Source not recommended with high overlap"""

    def test_is_source_recommended_fail_quality(self):
        """Source not recommended with low quality"""

    def test_save_candidate(self, tmp_db):
        """Candidate saves to database"""

    def test_get_candidates_all(self, tmp_db):
        """Get all candidates works"""

    def test_get_candidates_by_status(self, tmp_db):
        """Filter by status works"""

    def test_get_candidates_by_min_score(self, tmp_db):
        """Filter by min score works"""

    def test_approve_source(self, tmp_db):
        """Source approval works"""

    def test_reject_source(self, tmp_db):
        """Source rejection works"""

    def test_deprecate_inactive_sources(self, tmp_db):
        """Inactive source deprecation works"""

    def test_run_discovery_cycle(self, mock_all_sources):
        """Full discovery cycle works"""

    def test_generate_candidates_report(self, tmp_path):
        """Markdown report generation works"""

    def test_auto_approve_enabled(self, tmp_db):
        """Auto-approval works when enabled"""

    def test_auto_approve_disabled(self, tmp_db):
        """Auto-approval skipped when disabled"""


class TestIntegration:
    """Integration tests with existing modules"""

    def test_fetcher_uses_approved_sources(self, tmp_db):
        """Fetcher only uses approved sources"""

    def test_scheduler_runs_discovery(self):
        """Scheduler triggers discovery job"""

    def test_end_to_end_discovery_workflow(self, tmp_db):
        """Complete discovery workflow works"""
```

### Integration Tests

- Test discovery with real RSS feeds (mocked HTTP)
- Verify database persistence
- Test API endpoints with FastAPI TestClient
- Verify scheduler integration
- Test report generation

## Dependencies

All required dependencies already in `requirements.txt`:
- `feedparser` - RSS feed parsing
- `requests` - HTTP requests for discovery
- `beautifulsoup4` - HTML parsing for link extraction
- `sqlite3` - Standard library (database)

New optional dependencies (add if needed):
```
whois==0.9.27  # Domain age lookup
```

## Success Criteria

- ✅ Discovery from all 4 sources (Techmeme, HN, directories, outbound links)
- ✅ Accurate scoring algorithms for relevance, overlap, and quality
- ✅ Source lifecycle management (candidate → approved/rejected/deprecated)
- ✅ Database persistence with proper schema
- ✅ API endpoints for source management
- ✅ Weekly scheduler integration
- ✅ Markdown report generation
- ✅ Manual approval workflow
- ✅ Optional auto-approval feature flag
- ✅ Test coverage ≥ 80%
- ✅ All existing tests still pass
- ✅ Documentation updated

## Deliverables

1. `src/core/source_discovery.py` - Main discovery agent module
2. `src/tests/unit/test_source_discovery.py` - Comprehensive test suite
3. `src/tests/integration/test_source_discovery_integration.py` - Integration tests
4. Updated `src/core/scheduler.py` - Weekly discovery job
5. Updated `src/core/fetcher.py` - Use approved sources
6. Updated `src/api/main.py` - Source management endpoints
7. Database schema updates in `src/core/database.py`
8. `/docs/source-candidates.md` - Generated report
9. Updated documentation

## Notes

- Start with simple discovery (Techmeme, HN) before implementing complex crawling
- Mock external HTTP calls in unit tests for speed
- Use rate limiting and respect robots.txt
- Log all discovery operations for observability
- Consider adding feature flag for auto-approval in production
- Future enhancement: ML-based source quality prediction
