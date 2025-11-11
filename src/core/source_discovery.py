"""
Source Discovery Agent for RSS Feed Evaluation (Slice 07)

Discovers, evaluates, and recommends new RSS sources for the news aggregator.
Implements scoring algorithms for relevance, overlap, and quality.
"""

import sqlite3
import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional
from urllib.parse import urlparse
import socket
import re
from bs4 import BeautifulSoup


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


class SourceEvaluator:
    """
    Helper class for source evaluation logic.
    """

    TECH_KEYWORDS = [
        "AI", "artificial intelligence", "machine learning", "ML",
        "startup", "technology", "software", "developer", "programming",
        "cloud", "AWS", "Azure", "GCP", "cybersecurity", "blockchain",
        "cryptocurrency", "SaaS", "API", "DevOps", "data science",
        "tech", "digital", "innovation", "coding"
    ]

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return url

    @staticmethod
    def fetch_feed_articles(feed_url: str, limit: int = 20) -> List[Dict]:
        """
        Fetch recent articles from RSS feed using xml.etree.ElementTree

        Args:
            feed_url: URL of RSS feed
            limit: Maximum number of articles to fetch

        Returns:
            List of article dictionaries
        """
        try:
            # Fetch feed with timeout
            response = requests.get(feed_url, timeout=10)
            response.raise_for_status()

            # Parse XML
            root = ET.fromstring(response.content)

            articles = []

            # Try RSS 2.0 format first
            items = root.findall('.//item')
            if not items:
                # Try Atom format
                # Handle namespace for Atom
                items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
                if not items:
                    items = root.findall('.//entry')

            for item in items[:limit]:
                try:
                    # RSS 2.0 format
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    desc_elem = item.find('description')
                    pub_elem = item.find('pubDate')

                    # Atom format fallback
                    if title_elem is None:
                        title_elem = item.find('{http://www.w3.org/2005/Atom}title')
                    if link_elem is None:
                        link_elem = item.find('{http://www.w3.org/2005/Atom}link')
                        if link_elem is not None and 'href' in link_elem.attrib:
                            link_text = link_elem.attrib['href']
                        else:
                            link_text = link_elem.text if link_elem is not None else ""
                    else:
                        link_text = link_elem.text if link_elem is not None else ""

                    if desc_elem is None:
                        desc_elem = item.find('{http://www.w3.org/2005/Atom}summary')
                        if desc_elem is None:
                            desc_elem = item.find('{http://www.w3.org/2005/Atom}content')

                    if pub_elem is None:
                        pub_elem = item.find('{http://www.w3.org/2005/Atom}published')
                        if pub_elem is None:
                            pub_elem = item.find('{http://www.w3.org/2005/Atom}updated')

                    article = {
                        "title": title_elem.text if title_elem is not None and title_elem.text else "",
                        "link": link_text,
                        "description": desc_elem.text if desc_elem is not None and desc_elem.text else "",
                        "published": pub_elem.text if pub_elem is not None and pub_elem.text else ""
                    }

                    if article["title"] or article["link"]:
                        articles.append(article)

                except Exception:
                    continue

            return articles

        except Exception:
            return []

    @staticmethod
    def check_https(url: str) -> bool:
        """Check if URL uses HTTPS"""
        return url.startswith('https://')

    @staticmethod
    def estimate_domain_age(domain: str) -> float:
        """
        Estimate domain age (0.0-1.0 score)

        Simple heuristic: Check if domain resolves (older domains more likely to exist)
        More sophisticated: Use WHOIS (requires whois package)
        """
        try:
            socket.gethostbyname(domain)
            return 0.7  # Domain exists, assume moderate age
        except Exception:
            return 0.0  # Domain doesn't resolve

    @staticmethod
    def calculate_post_frequency(articles: List[Dict]) -> float:
        """
        Calculate posts per day and return score (0.0-1.0)

        Ideal frequency: 1-3 posts/day scores highest
        Too high (>5/day) or too low (<0.5/day) scores lower
        """
        if not articles:
            return 0.0

        try:
            # Parse published dates
            dates = []
            for article in articles:
                pub = article.get("published", "")
                if pub:
                    try:
                        # Try parsing ISO format or similar
                        # Simplified: just check if date exists
                        dates.append(pub)
                    except Exception:
                        continue

            if len(dates) < 2:
                return 0.5  # Not enough data

            # Estimate posts per day (rough heuristic)
            posts_per_day = len(articles) / 7.0  # Assume ~7 day window

            # Score based on ideal range
            if 1.0 <= posts_per_day <= 3.0:
                return 1.0  # Ideal
            elif 0.5 <= posts_per_day <= 5.0:
                return 0.8  # Good
            elif posts_per_day < 0.5:
                return 0.3  # Too infrequent
            else:
                return 0.5  # Too frequent (spam)

        except Exception:
            return 0.5

    @staticmethod
    def calculate_content_quality(articles: List[Dict]) -> float:
        """
        Analyze content length and quality (return score 0.0-1.0)

        Longer descriptions indicate more detailed content
        """
        if not articles:
            return 0.0

        try:
            total_length = 0
            count = 0

            for article in articles:
                desc = article.get("description", "")
                title = article.get("title", "")
                combined = desc + " " + title
                total_length += len(combined)
                count += 1

            if count == 0:
                return 0.0

            avg_length = total_length / count

            # Score based on average content length
            if avg_length >= 500:
                return 1.0  # Very detailed
            elif avg_length >= 200:
                return 0.8  # Good detail
            elif avg_length >= 100:
                return 0.6  # Moderate
            elif avg_length >= 50:
                return 0.4  # Brief
            else:
                return 0.2  # Very short

        except Exception:
            return 0.5


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
        self.db_path = db_path
        self.auto_approve = auto_approve
        self._init_database()

    def _init_database(self):
        """Initialize sources table in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain TEXT NOT NULL,
                feed_url TEXT UNIQUE NOT NULL,
                status TEXT DEFAULT 'candidate',
                discovered_from TEXT,
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
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_feed_url ON sources(feed_url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sources_relevance_score ON sources(relevance_score)")

        conn.commit()
        conn.close()

    def discover_from_techmeme(self, limit: int = 20) -> List[str]:
        """
        Discover sources from Techmeme sidebar.

        Returns:
            List of feed URLs found on Techmeme
        """
        try:
            response = requests.get("https://techmeme.com", timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Find links to tech blogs
            feeds = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                # Look for feed-like URLs or convert blog URLs to feed URLs
                if any(keyword in href.lower() for keyword in ['/feed', '/rss', 'feed.xml', 'rss.xml']):
                    feeds.append(href)
                elif href.startswith('http') and limit > len(feeds):
                    # Try common feed patterns
                    domain = SourceEvaluator.extract_domain(href)
                    potential_feeds = [
                        f"https://{domain}/feed",
                        f"https://{domain}/rss",
                        f"https://{domain}/feed.xml"
                    ]
                    feeds.extend(potential_feeds[:1])  # Add first guess

            return list(set(feeds))[:limit]

        except Exception:
            return []

    def discover_from_hackernews(self, days: int = 7, min_score: int = 100) -> List[str]:
        """
        Discover sources from Hacker News top stories.

        Args:
            days: Look back N days
            min_score: Minimum story score threshold

        Returns:
            List of feed URLs from HN stories
        """
        try:
            # Fetch top stories from HN API
            response = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=10)
            response.raise_for_status()
            story_ids = response.json()[:100]  # Get top 100

            feeds = []
            for story_id in story_ids:
                try:
                    story_response = requests.get(
                        f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                        timeout=5
                    )
                    story = story_response.json()

                    if story.get('score', 0) >= min_score and 'url' in story:
                        url = story['url']
                        # Skip HN internal links
                        if 'news.ycombinator.com' in url:
                            continue

                        domain = SourceEvaluator.extract_domain(url)
                        # Generate potential feed URLs
                        potential_feeds = [
                            f"https://{domain}/feed",
                            f"https://{domain}/rss",
                            f"https://{domain}/feed.xml"
                        ]
                        feeds.extend(potential_feeds[:1])

                except Exception:
                    continue

            return list(set(feeds))

        except Exception:
            return []

    def discover_from_directories(self, categories: List[str] = None) -> List[str]:
        """
        Discover sources from RSS directories.

        Args:
            categories: List of categories to search (e.g., ["tech", "ai"])

        Returns:
            List of feed URLs from directories
        """
        # Simplified implementation - in production, would query actual directories
        # like Feedspot, Feedly, etc.
        feeds = []

        # Default tech feeds as examples
        default_feeds = [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://arstechnica.com/feed/",
            "https://www.wired.com/feed/rss",
            "https://venturebeat.com/feed/"
        ]

        return default_feeds

    def discover_from_outbound_links(self, source_urls: List[str], limit: int = 10) -> List[str]:
        """
        Discover sources by following links from approved sources.

        Args:
            source_urls: List of approved source URLs to crawl
            limit: Max links to follow per source

        Returns:
            List of feed URLs discovered from outbound links
        """
        feeds = []

        for source_url in source_urls[:5]:  # Limit sources to crawl
            try:
                response = requests.get(source_url, timeout=10)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                for link in soup.find_all('a', href=True)[:limit]:
                    href = link['href']
                    if href.startswith('http') and 'feed' not in href.lower():
                        domain = SourceEvaluator.extract_domain(href)
                        potential_feeds = [
                            f"https://{domain}/feed",
                            f"https://{domain}/rss"
                        ]
                        feeds.extend(potential_feeds[:1])

            except Exception:
                continue

        return list(set(feeds))[:limit]

    def calculate_relevance_score(self, articles: List[Dict]) -> float:
        """
        Calculate % of articles matching tech/AI keywords.

        Args:
            articles: List of article dicts with 'title' and 'description'

        Returns:
            Relevance score (0.0-1.0)
        """
        if not articles:
            return 0.0

        matching_count = 0

        for article in articles:
            text = (article.get("title", "") + " " + article.get("description", "")).lower()

            # Check if any tech keyword is in the text
            for keyword in SourceEvaluator.TECH_KEYWORDS:
                if keyword.lower() in text:
                    matching_count += 1
                    break  # Count article only once

        return matching_count / len(articles)

    def calculate_overlap_score(self, feed_url: str, articles: List[Dict]) -> float:
        """
        Calculate Jaccard similarity with approved sources.

        Args:
            feed_url: URL of candidate feed
            articles: Articles from candidate feed

        Returns:
            Overlap score (0.0-1.0, lower is better)
        """
        if not articles:
            return 0.0

        # Get approved sources
        approved_sources = self.get_candidates(status=SourceStatus.APPROVED)

        if not approved_sources:
            return 0.0  # No overlap if no approved sources

        # Extract article titles from candidate
        candidate_titles = set(article.get("title", "").lower() for article in articles if article.get("title"))

        if not candidate_titles:
            return 0.0

        max_overlap = 0.0

        for approved in approved_sources:
            if approved.sample_articles:
                approved_titles = set(
                    article.get("title", "").lower()
                    for article in approved.sample_articles
                    if article.get("title")
                )

                if approved_titles:
                    # Jaccard similarity
                    intersection = len(candidate_titles & approved_titles)
                    union = len(candidate_titles | approved_titles)

                    if union > 0:
                        overlap = intersection / union
                        max_overlap = max(max_overlap, overlap)

        return max_overlap

    def calculate_quality_score(self, feed_url: str, articles: List[Dict]) -> float:
        """
        Calculate composite quality score.

        Args:
            feed_url: URL of candidate feed
            articles: Articles from candidate feed

        Returns:
            Quality score (0.0-1.0)
        """
        # Extract domain
        domain = SourceEvaluator.extract_domain(feed_url)

        # Calculate component scores
        https_score = 1.0 if SourceEvaluator.check_https(feed_url) else 0.0
        domain_age_score = SourceEvaluator.estimate_domain_age(domain)
        frequency_score = SourceEvaluator.calculate_post_frequency(articles)
        content_score = SourceEvaluator.calculate_content_quality(articles)

        # Check if feed is valid (has articles)
        valid_rss_score = 1.0 if articles else 0.0

        # Weighted average
        weights = {
            'domain_age': 0.2,
            'frequency': 0.3,
            'content': 0.2,
            'https': 0.1,
            'valid_rss': 0.2
        }

        quality_score = (
            domain_age_score * weights['domain_age'] +
            frequency_score * weights['frequency'] +
            content_score * weights['content'] +
            https_score * weights['https'] +
            valid_rss_score * weights['valid_rss']
        )

        return quality_score

    def evaluate_source(self, feed_url: str) -> SourceCandidate:
        """
        Evaluate a candidate source and compute all scores.

        Args:
            feed_url: URL of RSS feed to evaluate

        Returns:
            SourceCandidate with computed scores
        """
        # Fetch articles
        articles = SourceEvaluator.fetch_feed_articles(feed_url, limit=20)

        # Calculate scores
        relevance_score = self.calculate_relevance_score(articles)
        overlap_score = self.calculate_overlap_score(feed_url, articles)
        quality_score = self.calculate_quality_score(feed_url, articles)

        # Extract domain
        domain = SourceEvaluator.extract_domain(feed_url)

        return SourceCandidate(
            domain=domain,
            feed_url=feed_url,
            discovered_from="manual",
            discovered_at=datetime.now(),
            relevance_score=relevance_score,
            overlap_score=overlap_score,
            quality_score=quality_score,
            status=SourceStatus.CANDIDATE,
            last_evaluated=datetime.now(),
            evaluation_count=1,
            sample_articles=articles
        )

    def is_source_recommended(self, candidate: SourceCandidate) -> bool:
        """
        Determine if source meets approval thresholds.

        Args:
            candidate: Source candidate to evaluate

        Returns:
            True if all thresholds met
        """
        return (
            candidate.relevance_score >= 0.70 and
            candidate.overlap_score < 0.40 and
            candidate.quality_score >= 0.60
        )

    def save_candidate(self, candidate: SourceCandidate) -> None:
        """
        Save candidate to database.

        Args:
            candidate: Source candidate to persist
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO sources (
                    domain, feed_url, status, discovered_from, discovered_at,
                    last_evaluated, evaluation_count, relevance_score,
                    overlap_score, quality_score, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                candidate.domain,
                candidate.feed_url,
                candidate.status.value,
                candidate.discovered_from,
                candidate.discovered_at.isoformat(),
                candidate.last_evaluated.isoformat() if candidate.last_evaluated else None,
                candidate.evaluation_count,
                candidate.relevance_score,
                candidate.overlap_score,
                candidate.quality_score,
                datetime.now().isoformat()
            ))

            conn.commit()
        finally:
            conn.close()

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
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = "SELECT * FROM sources WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if min_score is not None:
            query += " AND relevance_score >= ?"
            params.append(min_score)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        candidates = []
        for row in rows:
            candidate = SourceCandidate(
                domain=row[1],
                feed_url=row[2],
                discovered_from=row[4],
                discovered_at=datetime.fromisoformat(row[5]) if row[5] else datetime.now(),
                relevance_score=row[8] or 0.0,
                overlap_score=row[9] or 0.0,
                quality_score=row[10] or 0.0,
                status=SourceStatus(row[3]),
                last_evaluated=datetime.fromisoformat(row[6]) if row[6] else None,
                evaluation_count=row[7] or 0
            )
            candidates.append(candidate)

        return candidates

    def approve_source(self, feed_url: str) -> None:
        """
        Manually approve a candidate source.

        Args:
            feed_url: URL of feed to approve
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM sources WHERE feed_url = ?", (feed_url,))
        if not cursor.fetchone():
            conn.close()
            raise ValueError(f"Source {feed_url} not found")

        cursor.execute("""
            UPDATE sources
            SET status = ?, approved_at = ?, updated_at = ?
            WHERE feed_url = ?
        """, (SourceStatus.APPROVED.value, datetime.now().isoformat(), datetime.now().isoformat(), feed_url))

        conn.commit()
        conn.close()

    def reject_source(self, feed_url: str, reason: Optional[str] = None) -> None:
        """
        Manually reject a candidate source.

        Args:
            feed_url: URL of feed to reject
            reason: Optional rejection reason
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE sources
            SET status = ?, rejection_reason = ?, updated_at = ?
            WHERE feed_url = ?
        """, (SourceStatus.REJECTED.value, reason, datetime.now().isoformat(), feed_url))

        conn.commit()
        conn.close()

    def deprecate_inactive_sources(self, days_inactive: int = 30) -> List[str]:
        """
        Mark approved sources as deprecated if no recent articles.

        Args:
            days_inactive: Days without new content before deprecation

        Returns:
            List of deprecated feed URLs
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cutoff_date = (datetime.now() - timedelta(days=days_inactive)).isoformat()

        cursor.execute("""
            SELECT feed_url FROM sources
            WHERE status = ?
            AND (last_evaluated IS NULL OR last_evaluated < ?)
        """, (SourceStatus.APPROVED.value, cutoff_date))

        rows = cursor.fetchall()
        deprecated_urls = [row[0] for row in rows]

        if deprecated_urls:
            placeholders = ','.join('?' * len(deprecated_urls))
            cursor.execute(f"""
                UPDATE sources
                SET status = ?, updated_at = ?
                WHERE feed_url IN ({placeholders})
            """, [SourceStatus.DEPRECATED.value, datetime.now().isoformat()] + deprecated_urls)

            conn.commit()

        conn.close()
        return deprecated_urls

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
        discovered_urls = []

        # Discover from all sources
        discovered_urls.extend(self.discover_from_techmeme(limit=10))
        discovered_urls.extend(self.discover_from_hackernews(days=7, min_score=100))
        discovered_urls.extend(self.discover_from_directories())

        # Get approved sources for outbound link discovery
        approved = self.get_candidates(status=SourceStatus.APPROVED)
        if approved:
            approved_urls = [s.feed_url for s in approved[:3]]
            discovered_urls.extend(self.discover_from_outbound_links(approved_urls, limit=5))

        # Remove duplicates
        discovered_urls = list(set(discovered_urls))

        # Evaluate and save
        evaluated_count = 0
        recommended_count = 0

        for url in discovered_urls:
            try:
                candidate = self.evaluate_source(url)
                candidate.discovered_from = "discovery_cycle"
                self.save_candidate(candidate)
                evaluated_count += 1

                if self.is_source_recommended(candidate):
                    recommended_count += 1

                    # Auto-approve if enabled
                    if self.auto_approve:
                        self.approve_source(url)

            except Exception:
                continue

        # Generate report
        try:
            self.generate_candidates_report()
        except Exception:
            pass

        return {
            "discovered_count": len(discovered_urls),
            "evaluated_count": evaluated_count,
            "recommended_count": recommended_count
        }

    def generate_candidates_report(self, output_path: str = "./docs/source-candidates.md") -> None:
        """
        Generate markdown report of candidate sources.

        Args:
            output_path: Path to output markdown file
        """
        candidates = self.get_candidates(status=SourceStatus.CANDIDATE)
        approved = self.get_candidates(status=SourceStatus.APPROVED)

        # Build report
        report = "# Source Candidates Report\n\n"
        report += f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        report += f"## Summary\n\n"
        report += f"- **Candidate Sources:** {len(candidates)}\n"
        report += f"- **Approved Sources:** {len(approved)}\n"
        report += f"- **Recommended (meeting thresholds):** {sum(1 for c in candidates if self.is_source_recommended(c))}\n\n"

        if candidates:
            report += "## Recommended Candidates\n\n"
            recommended = [c for c in candidates if self.is_source_recommended(c)]

            if recommended:
                report += "| Domain | Feed URL | Relevance | Overlap | Quality | Status |\n"
                report += "|--------|----------|-----------|---------|---------|--------|\n"

                for candidate in recommended:
                    report += f"| {candidate.domain} | {candidate.feed_url} | {candidate.relevance_score:.2f} | {candidate.overlap_score:.2f} | {candidate.quality_score:.2f} | ✅ Recommended |\n"

                report += "\n"
            else:
                report += "*No candidates meet recommendation thresholds.*\n\n"

            report += "## All Candidates\n\n"
            report += "| Domain | Feed URL | Relevance | Overlap | Quality | Recommended |\n"
            report += "|--------|----------|-----------|---------|---------|-------------|\n"

            for candidate in candidates:
                status = "✅" if self.is_source_recommended(candidate) else "❌"
                report += f"| {candidate.domain} | {candidate.feed_url} | {candidate.relevance_score:.2f} | {candidate.overlap_score:.2f} | {candidate.quality_score:.2f} | {status} |\n"

        # Write report
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(report)
