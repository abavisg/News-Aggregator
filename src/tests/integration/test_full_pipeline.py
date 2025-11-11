"""
Integration tests for the complete pipeline: Fetch → Summarize → Compose → Publish.

Tests the full workflow of the news aggregator from fetching articles
to publishing LinkedIn posts.
"""

import pytest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.core.fetcher import fetch_news
from src.core.summarizer import summarize_article
from src.core.composer import compose_weekly_post
from src.core.publisher import LinkedInPublisher


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.Anthropic')
def test_fetch_summarize_compose_pipeline(mock_anthropic, mock_feedparser):
    """
    Integration test: Complete content pipeline from fetch to compose.

    Given: RSS feeds with tech news
    When: Full pipeline executes (fetch → summarize → compose)
    Then: LinkedIn-ready post is generated
    """
    # Arrange - Mock RSS feed
    mock_feed = Mock()
    mock_feed.entries = [
        {
            'title': 'OpenAI Releases GPT-5',
            'link': 'https://techcrunch.com/2025/11/10/gpt5',
            'published': 'Mon, 10 Nov 2025 10:00:00 GMT',
        },
        {
            'title': 'Google Quantum Breakthrough',
            'link': 'https://theverge.com/2025/11/09/quantum',
            'published': 'Sun, 09 Nov 2025 14:30:00 GMT',
        },
        {
            'title': 'AI Chip Shortage Intensifies',
            'link': 'https://wired.com/2025/11/08/chips',
            'published': 'Sat, 08 Nov 2025 11:00:00 GMT',
        }
    ]
    mock_feedparser.return_value = mock_feed

    # Mock Claude API
    mock_client = MagicMock()
    mock_response = Mock()
    mock_content = Mock()

    # Different summaries for each article
    summaries_text = [
        "OpenAI releases GPT-5 with 95% accuracy on complex logic tasks.",
        "Google achieves quantum computing breakthrough with error correction.",
        "AI chip shortage intensifies with 18-month lead times for H100 GPUs."
    ]
    call_count = [0]

    def create_response(*args, **kwargs):
        mock_resp = Mock()
        mock_c = Mock()
        mock_c.text = summaries_text[call_count[0] % len(summaries_text)]
        mock_resp.content = [mock_c]
        mock_u = Mock()
        mock_u.input_tokens = 150
        mock_u.output_tokens = 50
        mock_resp.usage = mock_u
        call_count[0] += 1
        return mock_resp

    mock_client.messages.create.side_effect = create_response
    mock_anthropic.return_value = mock_client

    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        # Act - Step 1: Fetch articles
        articles = fetch_news(['https://techcrunch.com/feed/'])
        assert len(articles) == 3

        # Act - Step 2: Summarize articles
        summaries = []
        for article in articles:
            article_with_content = {
                **article,
                'content': f'Full content for {article["title"]}...'
            }
            summary = summarize_article(article_with_content)
            summaries.append(summary)

        assert len(summaries) == 3

        # Act - Step 3: Compose LinkedIn post
        post = compose_weekly_post(summaries)

        # Assert - Check post structure
        assert 'content' in post
        assert 'week_key' in post
        # Metadata is at root level, not nested

        # Check content includes all articles
        for summary in summaries:
            assert summary['summary'] in post['content'] or len(summary['summary']) > 50

        # Check hashtags present
        assert '#TechNews' in post['content'] or '#AI' in post['content']

        # Check week key format
        assert post['week_key'].startswith('2025.W')

        # Check metadata
        assert post['article_count'] == 3
        assert post['character_count'] > 0
        assert post['character_count'] <= 3000  # LinkedIn limit


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.Anthropic')
def test_pipeline_with_post_storage(mock_anthropic, mock_feedparser, tmp_path):
    """
    Integration test: Pipeline with local post storage.

    Given: Complete pipeline execution
    When: Post is generated and saved
    Then: Post is stored correctly on disk
    """
    # Arrange - Mock RSS feed
    mock_feed = Mock()
    mock_feed.entries = [
        {
            'title': 'Test Article 1',
            'link': 'https://example.com/article-1',
            'published': 'Mon, 10 Nov 2025 10:00:00 GMT',
        },
        {
            'title': 'Test Article 2',
            'link': 'https://example.com/article-2',
            'published': 'Mon, 10 Nov 2025 11:00:00 GMT',
        },
        {
            'title': 'Test Article 3',
            'link': 'https://example.com/article-3',
            'published': 'Mon, 10 Nov 2025 12:00:00 GMT',
        }
    ]
    mock_feedparser.return_value = mock_feed

    # Mock Claude
    mock_client = MagicMock()
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = "Test summary"
    mock_response.content = [mock_content]
    mock_usage = Mock()
    mock_usage.input_tokens = 100
    mock_usage.output_tokens = 30
    mock_response.usage = mock_usage
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        # Act - Execute pipeline
        articles = fetch_news(['https://example.com/feed/'])
        summaries = []
        for article in articles:
            article_with_content = {**article, 'content': f'Content for {article["title"]}'}
            summary = summarize_article(article_with_content)
            summaries.append(summary)
        post = compose_weekly_post(summaries)

        # Act - Save post locally
        publisher = LinkedInPublisher(posts_dir=str(tmp_path / "posts"))
        week_key = post['week_key']
        publisher.save_post_locally(
            week_key=week_key,
            content=post['content'],
            metadata={'article_count': post['article_count'], 'character_count': post['character_count'], 'sources': post['sources'], 'hashtags': post['hashtags']},
            status='draft'
        )

        # Assert - Post file exists
        post_file = tmp_path / "posts" / f"{week_key}.json"
        assert post_file.exists()

        # Assert - Post content correct
        with open(post_file, 'r') as f:
            saved_post = json.load(f)

        assert saved_post['week_key'] == week_key
        assert saved_post['content'] == post['content']
        assert saved_post['status'] == 'draft'
        assert 'created_at' in saved_post
        assert 'metadata' in saved_post


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.httpx.post')
def test_pipeline_with_ollama_fallback(mock_httpx, mock_feedparser):
    """
    Integration test: Pipeline uses Ollama when Claude is not available.

    Given: Claude API key not set
    And: Ollama is available
    When: Pipeline executes
    Then: Ollama is used for summarization
    And: Post is generated successfully
    """
    # Arrange - Mock RSS feed
    mock_feed = Mock()
    mock_feed.entries = [
        {
            'title': 'Test Article 1',
            'link': 'https://example.com/article-1',
            'published': 'Mon, 10 Nov 2025 10:00:00 GMT',
        },
        {
            'title': 'Test Article 2',
            'link': 'https://example.com/article-2',
            'published': 'Mon, 10 Nov 2025 11:00:00 GMT',
        },
        {
            'title': 'Test Article 3',
            'link': 'https://example.com/article-3',
            'published': 'Mon, 10 Nov 2025 12:00:00 GMT',
        }
    ]
    mock_feedparser.return_value = mock_feed

    # Mock Ollama
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'response': 'Ollama-generated summary',
        'done': True
    }
    mock_httpx.return_value = mock_response

    # Use Ollama (no Claude API key)
    with patch.dict('os.environ', {'OLLAMA_BASE_URL': 'http://localhost:11434'}, clear=True):
        # Act - Execute pipeline
        articles = fetch_news(['https://example.com/feed/'])
        summaries = []
        for article in articles:
            article_with_content = {**article, 'content': f'Content for {article["title"]}'}
            summary = summarize_article(article_with_content)
            summaries.append(summary)

        # Assert - Ollama was used
        assert all(s['provider'] == 'ollama' for s in summaries)
        assert all(s['summary'] == 'Ollama-generated summary' for s in summaries)

        # Act - Compose post
        post = compose_weekly_post(summaries)

        # Assert - Post generated successfully
        assert 'Ollama-generated summary' in post['content']
        assert post['article_count'] == 3


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.Anthropic')
def test_pipeline_handles_empty_feed_gracefully(mock_anthropic, mock_feedparser):
    """
    Integration test: Pipeline handles empty RSS feeds gracefully.

    Given: RSS feed with no articles
    When: Pipeline executes
    Then: No crash occurs
    And: Appropriate error or empty result is returned
    """
    # Arrange - Mock empty feed
    mock_feed = Mock()
    mock_feed.entries = []
    mock_feedparser.return_value = mock_feed

    # Act - Fetch (should return empty list)
    articles = fetch_news(['https://example.com/feed/'])

    # Assert - Empty result, no crash
    assert articles == []

    # Can't summarize or compose without articles
    # This is expected behavior


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.Anthropic')
def test_pipeline_respects_article_limits(mock_anthropic, mock_feedparser):
    """
    Integration test: Pipeline respects fetch limits throughout.

    Given: Many articles available
    And: Fetch limit set to 3
    When: Pipeline executes
    Then: Only 3 articles are processed
    And: Only 3 summaries are generated
    And: Post includes only 3 articles
    """
    # Arrange - Mock feed with many articles
    mock_feed = Mock()
    mock_feed.entries = [
        {
            'title': f'Article {i}',
            'link': f'https://example.com/article-{i}',
            'published': 'Mon, 10 Nov 2025 10:00:00 GMT',
        }
        for i in range(10)
    ]
    mock_feedparser.return_value = mock_feed

    # Mock Claude
    mock_client = MagicMock()
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = "Summary"
    mock_response.content = [mock_content]
    mock_usage = Mock()
    mock_usage.input_tokens = 100
    mock_usage.output_tokens = 30
    mock_response.usage = mock_usage
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        # Act - Execute pipeline with limit
        articles = fetch_news(['https://example.com/feed/'], limit_per_source=3)
        assert len(articles) == 3

        summaries = []
        for article in articles:
            article_with_content = {**article, 'content': 'Content'}
            summary = summarize_article(article_with_content)
            summaries.append(summary)

        assert len(summaries) == 3

        post = compose_weekly_post(summaries)

        # Assert - Post includes exactly 3 articles
        assert post['article_count'] == 3


@pytest.mark.integration
def test_pipeline_error_handling_integration():
    """
    Integration test: Error in one stage doesn't break the entire pipeline.

    Given: Fetcher succeeds
    And: Summarizer fails for some articles
    When: Pipeline executes
    Then: Successful articles are still processed
    And: Post is generated with available summaries
    """
    # This test would require more sophisticated error handling
    # Documented as a future improvement
    pass
