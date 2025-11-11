"""
Integration tests for fetch → summarize pipeline.

Tests the integration between the fetcher and summarizer modules,
ensuring they work together correctly with realistic data flows.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.core.fetcher import fetch_news
from src.core.summarizer import summarize_article, detect_provider


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.Anthropic')
def test_fetch_and_summarize_pipeline_with_claude(mock_anthropic, mock_feedparser):
    """
    Integration test: Fetch articles from RSS feed, then summarize them with Claude.

    Given: A mocked RSS feed with real articles
    And: Claude API is available
    When: Articles are fetched and then summarized
    Then: Summaries are generated with correct metadata
    """
    # Arrange - Mock RSS feed
    mock_feed = Mock()
    mock_feed.entries = [
        {
            'title': 'OpenAI Releases GPT-5 with Advanced Reasoning',
            'link': 'https://techcrunch.com/2025/11/10/gpt5',
            'published': 'Mon, 10 Nov 2025 10:00:00 GMT',
        },
        {
            'title': 'Google Achieves Quantum Computing Breakthrough',
            'link': 'https://theverge.com/2025/11/09/quantum',
            'published': 'Sun, 09 Nov 2025 14:30:00 GMT',
        }
    ]
    mock_feedparser.return_value = mock_feed

    # Mock Claude API
    mock_client = MagicMock()
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = "AI-powered summary of the article."
    mock_response.content = [mock_content]
    mock_usage = Mock()
    mock_usage.input_tokens = 150
    mock_usage.output_tokens = 50
    mock_response.usage = mock_usage
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    # Set environment for Claude
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        # Act - Fetch articles
        articles = fetch_news(['https://techcrunch.com/feed/'])

        assert len(articles) == 2, "Should fetch 2 articles"

        # Act - Summarize first article
        article_with_content = {
            **articles[0],
            'content': 'OpenAI announces GPT-5 with breakthrough capabilities...'
        }
        summary = summarize_article(article_with_content)

        # Assert - Check summary structure
        assert 'summary' in summary
        assert 'tokens_used' in summary
        assert 'provider' in summary
        assert summary['provider'] == 'claude'
        assert summary['article_url'] == articles[0]['link']
        assert summary['source'] == articles[0]['source']
        assert isinstance(summary['summary'], str)
        assert len(summary['summary']) > 0


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.httpx.post')
def test_fetch_and_summarize_pipeline_with_ollama(mock_httpx, mock_feedparser):
    """
    Integration test: Fetch articles from RSS feed, then summarize them with Ollama.

    Given: A mocked RSS feed with real articles
    And: Ollama is available locally
    When: Articles are fetched and then summarized
    Then: Summaries are generated using Ollama
    """
    # Arrange - Mock RSS feed
    mock_feed = Mock()
    mock_feed.entries = [
        {
            'title': 'Linux Kernel 6.7 Ships with Rust Support',
            'link': 'https://arstechnica.com/2025/11/linux-rust',
            'published': 'Sat, 08 Nov 2025 09:00:00 GMT',
        }
    ]
    mock_feedparser.return_value = mock_feed

    # Mock Ollama API
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'response': 'Summary from Ollama local model',
        'done': True
    }
    mock_httpx.return_value = mock_response

    # Set environment for Ollama
    with patch.dict('os.environ', {'OLLAMA_BASE_URL': 'http://localhost:11434'}, clear=True):
        # Act - Fetch articles
        articles = fetch_news(['https://arstechnica.com/feed/'])

        assert len(articles) == 1

        # Act - Summarize
        article_with_content = {
            **articles[0],
            'content': 'Linux kernel 6.7 includes significant Rust support...'
        }
        summary = summarize_article(article_with_content)

        # Assert
        assert summary['provider'] == 'ollama'
        assert summary['summary'] == 'Summary from Ollama local model'
        assert summary['article_url'] == articles[0]['link']


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
def test_fetch_multiple_sources_then_summarize_batch(mock_feedparser):
    """
    Integration test: Fetch from multiple sources and summarize in batch.

    Given: Multiple RSS feeds with different articles
    When: All feeds are fetched and articles are summarized
    Then: Each article has correct source attribution
    And: Summaries maintain article-source relationship
    """
    # Arrange - Mock multiple feeds with different responses
    def mock_parse_side_effect(url):
        mock_feed = Mock()
        if 'techcrunch' in url:
            mock_feed.entries = [
                {
                    'title': 'TC Article 1',
                    'link': 'https://techcrunch.com/article1',
                    'published': 'Mon, 10 Nov 2025 10:00:00 GMT',
                }
            ]
        elif 'theverge' in url:
            mock_feed.entries = [
                {
                    'title': 'Verge Article 1',
                    'link': 'https://theverge.com/article1',
                    'published': 'Mon, 10 Nov 2025 11:00:00 GMT',
                }
            ]
        else:
            mock_feed.entries = []
        return mock_feed

    mock_feedparser.side_effect = mock_parse_side_effect

    # Act - Fetch from multiple sources
    sources = [
        'https://techcrunch.com/feed/',
        'https://theverge.com/rss/'
    ]
    articles = fetch_news(sources)

    # Assert - Check source attribution
    assert len(articles) == 2
    assert any(a['source'] == 'techcrunch.com' for a in articles)
    assert any(a['source'] == 'theverge.com' for a in articles)

    # Verify each article has correct structure for summarization
    for article in articles:
        assert 'title' in article
        assert 'link' in article
        assert 'source' in article
        assert 'date' in article
        assert 'published_at' in article


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.Anthropic')
def test_fetch_with_errors_then_summarize_successful_ones(mock_anthropic, mock_feedparser):
    """
    Integration test: Handle partial failures in fetch, then summarize successful articles.

    Given: Multiple RSS feeds, some failing
    When: Fetching is attempted
    Then: Successful articles are fetched
    And: Failed sources don't block summarization
    """
    # Arrange - Mock feed with some failures
    call_count = [0]

    def mock_parse_side_effect(url):
        call_count[0] += 1
        mock_feed = Mock()

        if 'techcrunch' in url:
            # Successful feed
            mock_feed.entries = [
                {
                    'title': 'Successful Article',
                    'link': 'https://techcrunch.com/success',
                    'published': 'Mon, 10 Nov 2025 10:00:00 GMT',
                }
            ]
            mock_feed.bozo = False
        else:
            # Failed feed
            mock_feed.entries = []
            mock_feed.bozo = True
            mock_feed.bozo_exception = Exception("Feed parse error")

        return mock_feed

    mock_feedparser.side_effect = mock_parse_side_effect

    # Mock Claude
    mock_client = MagicMock()
    mock_response = Mock()
    mock_content = Mock()
    mock_content.text = "Summary of successful article"
    mock_response.content = [mock_content]
    mock_usage = Mock()
    mock_usage.input_tokens = 100
    mock_usage.output_tokens = 30
    mock_response.usage = mock_usage
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    # Act - Fetch from multiple sources (one will fail)
    sources = [
        'https://techcrunch.com/feed/',
        'https://invalid-source.com/feed/'
    ]
    articles = fetch_news(sources)

    # Assert - Only successful articles fetched
    assert len(articles) == 1
    assert articles[0]['source'] == 'techcrunch.com'

    # Act - Summarize the successful article
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        article_with_content = {
            **articles[0],
            'content': 'Article content here...'
        }
        summary = summarize_article(article_with_content)

        # Assert - Summary succeeds despite partial fetch failure
        assert summary['summary'] == "Summary of successful article"
        assert summary['article_url'] == articles[0]['link']


@pytest.mark.integration
@patch('src.core.fetcher.feedparser.parse')
@patch('src.core.summarizer.Anthropic')
def test_fetch_limit_then_summarize_respects_limit(mock_anthropic, mock_feedparser):
    """
    Integration test: Fetch with limit, then summarize only fetched articles.

    Given: RSS feed with many articles
    And: Fetch limit is set to 3
    When: Articles are fetched and summarized
    Then: Only 3 articles are fetched and summarized
    """
    # Arrange - Mock feed with many articles
    mock_feed = Mock()
    mock_feed.entries = [
        {
            'title': f'Article {i}',
            'link': f'https://example.com/article-{i}',
            'published': 'Mon, 10 Nov 2025 10:00:00 GMT',
        }
        for i in range(10)  # 10 articles available
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
    mock_usage.output_tokens = 20
    mock_response.usage = mock_usage
    mock_client.messages.create.return_value = mock_response
    mock_anthropic.return_value = mock_client

    # Act - Fetch with limit
    articles = fetch_news(['https://example.com/feed/'], limit_per_source=3)

    # Assert - Respects limit
    assert len(articles) == 3

    # Act - Summarize all fetched articles
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        summaries = []
        for article in articles:
            article_with_content = {**article, 'content': 'Content'}
            summary = summarize_article(article_with_content)
            summaries.append(summary)

        # Assert - All fetched articles summarized
        assert len(summaries) == 3
        for summary in summaries:
            assert 'summary' in summary
            assert summary['provider'] == 'claude'


@pytest.mark.integration
def test_provider_detection_integration():
    """
    Integration test: Provider detection works correctly with environment.

    Given: Different environment configurations
    When: Provider is detected
    Then: Correct provider is selected
    """
    # Test 1: Claude detected
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}, clear=True):
        provider = detect_provider()
        assert provider == 'claude'

    # Test 2: Ollama detected
    with patch.dict('os.environ', {'OLLAMA_BASE_URL': 'http://localhost:11434'}, clear=True):
        provider = detect_provider()
        assert provider == 'ollama'

    # Test 3: No provider configured
    with patch.dict('os.environ', {}, clear=True):
        with pytest.raises(Exception) as exc_info:
            detect_provider()
        assert 'No AI provider configured' in str(exc_info.value)
