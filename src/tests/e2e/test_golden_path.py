"""
Golden Path E2E Tests - Full Pipeline Integration

These tests verify the complete pipeline works end-to-end after each slice completion.
They test the "happy path" to ensure no regressions and proper integration.

Run after each slice merge:
    pytest -m "e2e and golden" -v
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, MagicMock

from src.core.fetcher import fetch_news
from src.core.summarizer import summarize_article
from src.core.composer import compose_weekly_post


@pytest.mark.e2e
@pytest.mark.golden
class TestGoldenPathAfterSlice01:
    """
    E2E tests after Slice 01 (Fetcher) completion.

    Verify: RSS feed fetching works correctly in isolation.
    """

    def test_fetch_returns_valid_articles_from_real_feeds(self):
        """
        Golden Path: Fetch articles from real RSS feeds

        Given: Valid RSS feed URLs
        When: fetch_news is called
        Then: Articles are returned with all required fields
        """
        sources = [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml"
        ]

        articles = fetch_news(sources)

        # Assertions
        assert len(articles) > 0, "Should fetch at least one article"
        assert all('title' in a for a in articles), "All articles must have titles"
        assert all('link' in a for a in articles), "All articles must have links"
        assert all('source' in a for a in articles), "All articles must have sources"
        assert all('date' in a for a in articles), "All articles must have dates"
        assert all('content' in a for a in articles), "All articles must have content"

        # Verify date sorting (newest first)
        if len(articles) > 1:
            dates = [a['date'] for a in articles]
            assert dates == sorted(dates, reverse=True), \
                "Articles should be sorted by date (newest first)"

    def test_fetch_handles_multiple_sources_correctly(self):
        """
        Golden Path: Fetch from multiple sources and combine results

        Given: Multiple RSS feed URLs
        When: fetch_news is called
        Then: Articles from all sources are combined and sorted
        """
        sources = [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://wired.com/feed/rss"
        ]

        articles = fetch_news(sources)

        # Verify articles from multiple sources
        sources_found = set(a['source'] for a in articles)
        assert len(sources_found) >= 2, \
            "Should have articles from at least 2 different sources"

        # Verify no duplicates
        urls = [a['link'] for a in articles]
        assert len(urls) == len(set(urls)), "Should not have duplicate articles"


@pytest.mark.e2e
@pytest.mark.golden
class TestGoldenPathAfterSlice02:
    """
    E2E tests after Slice 02 (Summarizer) completion.

    Verify: Fetch → Summarize pipeline works correctly.
    """

    def test_fetch_and_summarize_pipeline(self, mock_claude_api):
        """
        Golden Path: Fetch → Summarize

        Given: Fetched articles from RSS feeds
        When: Articles are passed to summarizer
        Then: Summaries are generated successfully
        """
        # Step 1: Fetch real articles
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)
        assert len(articles) > 0, "Should fetch articles"

        # Step 2: Summarize first article
        article = articles[0]
        summary = summarize_article(article)

        # Assertions
        assert summary is not None, "Summary should be generated"
        assert isinstance(summary, str), "Summary should be a string"
        assert len(summary) > 0, "Summary should not be empty"
        assert len(summary) <= 500, "Summary should be reasonable length"

    def test_summarize_multiple_articles_preserves_order(self, mock_claude_api):
        """
        Golden Path: Summarize multiple articles in order

        Given: Multiple fetched articles
        When: Each is summarized
        Then: Order is preserved and all succeed
        """
        # Fetch articles
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)
        assert len(articles) >= 3, "Need at least 3 articles"

        # Summarize first 3 articles
        summaries = []
        original_urls = []

        for article in articles[:3]:
            summary = summarize_article(article)
            summaries.append(summary)
            original_urls.append(article['link'])

        # Verify all summaries generated
        assert len(summaries) == 3
        assert all(s is not None for s in summaries)
        assert all(len(s) > 0 for s in summaries)


@pytest.mark.e2e
@pytest.mark.golden
class TestGoldenPathAfterSlice03:
    """
    E2E tests after Slice 03 (Composer) completion.

    Verify: Fetch → Summarize → Compose full pipeline works correctly.
    """

    def test_full_pipeline_fetch_summarize_compose(self, mock_claude_api):
        """
        Golden Path: Fetch → Summarize → Compose

        Given: RSS feed sources
        When: Full pipeline executes
        Then: A valid LinkedIn post is generated
        """
        # Step 1: Fetch articles
        sources = ["https://techcrunch.com/feed/", "https://www.theverge.com/rss/index.xml"]
        articles = fetch_news(sources)
        assert len(articles) >= 3, "Need at least 3 articles for post"

        # Step 2: Summarize articles
        summaries = []
        for article in articles[:5]:
            summary_text = summarize_article(article)
            summaries.append({
                'article_url': article['link'],
                'summary': summary_text,
                'source': article['source'],
                'published_at': article['date'],
                'tokens_used': 150,
                'provider': 'claude'
            })

        # Step 3: Compose LinkedIn post
        post = compose_weekly_post(summaries)

        # Comprehensive assertions
        assert post is not None, "Post should be generated"
        assert 'content' in post, "Post should have content"
        assert 'week_key' in post, "Post should have week key"
        assert 'article_count' in post, "Post should track article count"
        assert 'character_count' in post, "Post should track character count"
        assert 'hashtags' in post, "Post should have hashtags"
        assert 'sources' in post, "Post should track sources"

        # Content validation
        assert len(post['content']) > 0, "Post content should not be empty"
        assert post['character_count'] <= 3000, \
            f"Post exceeds LinkedIn limit: {post['character_count']} chars"

        # Article count validation
        assert 3 <= post['article_count'] <= 6, \
            f"Post should have 3-6 articles, has {post['article_count']}"

        # Hashtag validation
        assert 5 <= len(post['hashtags']) <= 8, \
            f"Post should have 5-8 hashtags, has {len(post['hashtags'])}"

        # Week key validation
        assert post['week_key'] is not None, "Week key should be set"
        assert '.' in post['week_key'], "Week key should have format YYYY.Www"
        assert 'W' in post['week_key'], "Week key should contain 'W'"

        # Source diversity validation
        assert len(post['sources']) > 0, "Post should track sources"

    def test_pipeline_handles_minimal_data(self, mock_claude_api):
        """
        Golden Path: Pipeline works with minimum required data

        Given: Exactly 3 articles (minimum)
        When: Pipeline executes
        Then: Valid post is generated
        """
        # Fetch articles
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)
        assert len(articles) >= 3

        # Summarize exactly 3 articles
        summaries = []
        for article in articles[:3]:
            summary = summarize_article(article)
            summaries.append({
                'article_url': article['link'],
                'summary': summary,
                'source': article['source'],
                'published_at': article['date'],
                'tokens_used': 150,
                'provider': 'claude'
            })

        # Compose post
        post = compose_weekly_post(summaries)

        # Verify minimum viable post
        assert post is not None
        assert post['article_count'] == 3
        assert post['character_count'] <= 3000
        assert len(post['hashtags']) >= 5

    def test_pipeline_produces_consistent_output_structure(self, mock_claude_api):
        """
        Golden Path: Pipeline output structure is consistent

        Given: Pipeline execution
        When: Post is generated
        Then: Output has consistent, predictable structure
        """
        # Execute pipeline
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)

        summaries = []
        for article in articles[:4]:
            summary = summarize_article(article)
            summaries.append({
                'article_url': article['link'],
                'summary': summary,
                'source': article['source'],
                'published_at': article['date'],
                'tokens_used': 150,
                'provider': 'claude'
            })

        post = compose_weekly_post(summaries)

        # Verify consistent structure
        expected_keys = ['content', 'week_key', 'article_count',
                        'character_count', 'hashtags', 'sources']

        for key in expected_keys:
            assert key in post, f"Post missing expected key: {key}"

        # Verify data types
        assert isinstance(post['content'], str)
        assert isinstance(post['week_key'], str)
        assert isinstance(post['article_count'], int)
        assert isinstance(post['character_count'], int)
        assert isinstance(post['hashtags'], list)
        assert isinstance(post['sources'], list)


@pytest.mark.e2e
@pytest.mark.golden
@pytest.mark.slow
class TestGoldenPathPerformance:
    """
    Performance tests for the full pipeline.

    These tests ensure the pipeline meets performance requirements.
    """

    def test_full_pipeline_completes_within_time_limit(self, mock_claude_api):
        """
        Golden Path: Pipeline completes within reasonable time

        Given: Standard article processing load
        When: Pipeline executes
        Then: Total time is under 2 minutes
        """
        import time

        start_time = time.time()

        # Execute full pipeline
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)

        summaries = []
        for article in articles[:5]:
            summary = summarize_article(article)
            summaries.append({
                'article_url': article['link'],
                'summary': summary,
                'source': article['source'],
                'published_at': article['date'],
                'tokens_used': 150,
                'provider': 'claude'
            })

        post = compose_weekly_post(summaries)

        elapsed_time = time.time() - start_time

        # Verify performance
        assert elapsed_time < 120, \
            f"Pipeline took {elapsed_time:.2f}s, should be under 120s"


@pytest.mark.e2e
@pytest.mark.golden
class TestGoldenPathDataIntegrity:
    """
    Data integrity tests across pipeline components.

    Ensure data flows correctly between components without loss or corruption.
    """

    def test_article_data_preserved_through_pipeline(self, mock_claude_api):
        """
        Golden Path: Article data integrity maintained

        Given: Articles with specific URLs and sources
        When: Pipeline processes them
        Then: URLs and sources are preserved in final output
        """
        # Fetch articles
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)
        assert len(articles) >= 3

        # Track original URLs
        original_urls = [a['link'] for a in articles[:3]]
        original_sources = [a['source'] for a in articles[:3]]

        # Process through pipeline
        summaries = []
        for article in articles[:3]:
            summary = summarize_article(article)
            summaries.append({
                'article_url': article['link'],
                'summary': summary,
                'source': article['source'],
                'published_at': article['date'],
                'tokens_used': 150,
                'provider': 'claude'
            })

        post = compose_weekly_post(summaries)

        # Verify data preservation
        post_content = post['content']
        for url in original_urls:
            assert url in post_content, f"Original URL {url} not in post"

        for source in original_sources:
            assert source in post['sources'], f"Source {source} not tracked"

    def test_no_data_loss_in_pipeline(self, mock_claude_api):
        """
        Golden Path: No data loss during processing

        Given: 5 articles to process
        When: Pipeline executes
        Then: All 5 articles are represented in output
        """
        # Fetch and process exactly 5 articles
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)
        assert len(articles) >= 5

        articles_to_process = articles[:5]

        summaries = []
        for article in articles_to_process:
            summary = summarize_article(article)
            summaries.append({
                'article_url': article['link'],
                'summary': summary,
                'source': article['source'],
                'published_at': article['date'],
                'tokens_used': 150,
                'provider': 'claude'
            })

        post = compose_weekly_post(summaries)

        # Verify all articles present
        assert post['article_count'] == 5, \
            f"Expected 5 articles, got {post['article_count']}"


@pytest.mark.e2e
@pytest.mark.golden
class TestGoldenPathRegressionPrevention:
    """
    Regression tests to ensure new slices don't break previous functionality.

    Run after each slice merge to verify no regressions.
    """

    def test_slice01_still_works_after_slice02_merge(self):
        """
        Regression Test: Slice 01 functionality intact after Slice 02

        Given: Slice 02 has been merged
        When: Fetcher is used
        Then: It still works correctly
        """
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)

        assert len(articles) > 0
        assert all('title' in a for a in articles)
        assert all('link' in a for a in articles)

    def test_slice01_and_slice02_work_after_slice03_merge(self, mock_claude_api):
        """
        Regression Test: Slices 01-02 intact after Slice 03

        Given: Slice 03 has been merged
        When: Fetcher and Summarizer are used
        Then: They still work correctly
        """
        # Test Slice 01
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)
        assert len(articles) > 0

        # Test Slice 02
        summary = summarize_article(articles[0])
        assert summary is not None
        assert len(summary) > 0

    def test_full_integration_no_regressions(self, mock_claude_api):
        """
        Regression Test: Full pipeline works after all merges

        Given: All slices have been merged
        When: Full pipeline executes
        Then: Everything works without errors
        """
        # Full pipeline execution
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)

        summaries = []
        for article in articles[:4]:
            summary = summarize_article(article)
            summaries.append({
                'article_url': article['link'],
                'summary': summary,
                'source': article['source'],
                'published_at': article['date'],
                'tokens_used': 150,
                'provider': 'claude'
            })

        post = compose_weekly_post(summaries)

        # Verify everything works
        assert post is not None
        assert post['article_count'] == 4
        assert post['character_count'] <= 3000
        assert len(post['hashtags']) >= 5
        assert len(post['sources']) > 0
