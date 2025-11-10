"""
Pytest configuration and shared fixtures for all tests.

This file provides common fixtures, test configuration, and utilities
used across unit, integration, BDD, and E2E tests.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
import logging


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """
    Configure pytest with custom markers and settings.
    """
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "bdd: marks tests as BDD scenario tests"
    )
    config.addinivalue_line(
        "markers", "golden: marks tests as golden path critical tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (> 5s)"
    )


# ============================================================================
# Logging Fixtures
# ============================================================================

@pytest.fixture
def disable_logging():
    """Disable logging during tests to reduce noise."""
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def enable_debug_logging():
    """Enable debug logging for troubleshooting."""
    logging.basicConfig(level=logging.DEBUG)
    yield
    logging.basicConfig(level=logging.WARNING)


# ============================================================================
# Mock API Fixtures
# ============================================================================

@pytest.fixture
def mock_claude_api():
    """
    Mock Claude API responses for summarization tests.

    Returns a patch context that mocks the Anthropic client.
    """
    with patch('src.core.summarizer.anthropic.Anthropic') as mock_anthropic:
        # Create mock client
        mock_client = MagicMock()

        # Create mock response
        mock_response = Mock()
        mock_content = Mock()
        mock_content.text = "AI-powered summary of the article content with key insights."
        mock_response.content = [mock_content]

        # Mock usage tracking
        mock_usage = Mock()
        mock_usage.input_tokens = 150
        mock_usage.output_tokens = 50
        mock_response.usage = mock_usage

        # Setup mock to return response
        mock_client.messages.create.return_value = mock_response
        mock_anthropic.return_value = mock_client

        yield mock_client


@pytest.fixture
def mock_ollama_api():
    """
    Mock Ollama API responses for local summarization tests.

    Returns a patch context that mocks httpx.post for Ollama calls.
    """
    with patch('src.core.summarizer.httpx.post') as mock_post:
        # Create mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'response': 'Summary from local Ollama model',
            'done': True
        }

        mock_post.return_value = mock_response
        yield mock_post


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_article():
    """
    Provide a sample article for testing.

    Returns a normalized article dictionary.
    """
    return {
        'title': 'OpenAI Announces GPT-5 with Advanced Reasoning',
        'link': 'https://techcrunch.com/2025/11/10/openai-gpt5',
        'source': 'techcrunch.com',
        'date': datetime(2025, 11, 10, 14, 30, 0),
        'content': (
            'OpenAI today announced the release of GPT-5, featuring breakthrough '
            'reasoning capabilities and achieving 95% accuracy on complex logic '
            'benchmarks. The model demonstrates significant improvements in '
            'mathematical reasoning and code generation.'
        )
    }


@pytest.fixture
def sample_articles():
    """
    Provide multiple sample articles for testing.

    Returns a list of normalized article dictionaries.
    """
    base_date = datetime(2025, 11, 10, 12, 0, 0)

    return [
        {
            'title': 'OpenAI Releases GPT-5 with New Capabilities',
            'link': 'https://techcrunch.com/2025/11/10/gpt5',
            'source': 'techcrunch.com',
            'date': base_date,
            'content': 'OpenAI announces GPT-5 with 95% accuracy on logic tasks.'
        },
        {
            'title': 'Google Achieves Quantum Computing Breakthrough',
            'link': 'https://theverge.com/2025/11/09/quantum',
            'source': 'theverge.com',
            'date': base_date - timedelta(days=1),
            'content': 'Google announces quantum computing milestone with error correction.'
        },
        {
            'title': 'AI Chip Shortage Intensifies',
            'link': 'https://wired.com/2025/11/08/chips',
            'source': 'wired.com',
            'date': base_date - timedelta(days=2),
            'content': 'Global AI chip shortage with 18-month lead times for H100 GPUs.'
        },
        {
            'title': 'Linux Kernel 6.7 Ships with Rust',
            'link': 'https://arstechnica.com/2025/11/07/linux-rust',
            'source': 'arstechnica.com',
            'date': base_date - timedelta(days=3),
            'content': 'Linux kernel 6.7 includes 15% of drivers written in Rust.'
        },
        {
            'title': 'Microsoft Copilot Hits 1M Customers',
            'link': 'https://venturebeat.com/2025/11/06/copilot',
            'source': 'venturebeat.com',
            'date': base_date - timedelta(days=4),
            'content': 'Microsoft Copilot reaches 1 million enterprise customers.'
        }
    ]


@pytest.fixture
def sample_summary():
    """
    Provide a sample article summary for testing.

    Returns a summary dictionary with metadata.
    """
    return {
        'article_url': 'https://techcrunch.com/2025/11/10/gpt5',
        'summary': 'OpenAI releases GPT-5 with 95% accuracy on complex logic tasks.',
        'source': 'techcrunch.com',
        'published_at': datetime(2025, 11, 10, 14, 30, 0),
        'tokens_used': 150,
        'provider': 'claude'
    }


@pytest.fixture
def sample_summaries():
    """
    Provide multiple sample summaries for testing.

    Returns a list of summary dictionaries.
    """
    base_date = datetime(2025, 11, 10, 12, 0, 0)

    return [
        {
            'article_url': 'https://techcrunch.com/2025/11/10/gpt5',
            'summary': 'OpenAI releases GPT-5 with 95% accuracy on logic tasks.',
            'source': 'techcrunch.com',
            'published_at': base_date,
            'tokens_used': 150,
            'provider': 'claude'
        },
        {
            'article_url': 'https://theverge.com/2025/11/09/quantum',
            'summary': 'Google achieves quantum computing breakthrough with error correction.',
            'source': 'theverge.com',
            'published_at': base_date - timedelta(days=1),
            'tokens_used': 140,
            'provider': 'claude'
        },
        {
            'article_url': 'https://wired.com/2025/11/08/chips',
            'summary': 'AI chip shortage intensifies with 18-month lead times.',
            'source': 'wired.com',
            'published_at': base_date - timedelta(days=2),
            'tokens_used': 135,
            'provider': 'claude'
        },
        {
            'article_url': 'https://arstechnica.com/2025/11/07/linux',
            'summary': 'Linux kernel 6.7 ships with 15% drivers in Rust.',
            'source': 'arstechnica.com',
            'published_at': base_date - timedelta(days=3),
            'tokens_used': 120,
            'provider': 'claude'
        },
        {
            'article_url': 'https://venturebeat.com/2025/11/06/copilot',
            'summary': 'Microsoft Copilot reaches 1 million enterprise customers.',
            'source': 'venturebeat.com',
            'published_at': base_date - timedelta(days=4),
            'tokens_used': 145,
            'provider': 'claude'
        }
    ]


@pytest.fixture
def sample_linkedin_post():
    """
    Provide a sample LinkedIn post for testing.

    Returns a composed post dictionary.
    """
    return {
        'content': (
            '🚀 Tech & AI Weekly Digest - Week 45, 2025\n\n'
            '📌 OpenAI releases GPT-5 with 95% accuracy on logic tasks.\n'
            '🔗 https://techcrunch.com/2025/11/10/gpt5\n\n'
            '📌 Google achieves quantum computing breakthrough.\n'
            '🔗 https://theverge.com/2025/11/09/quantum\n\n'
            '📌 AI chip shortage intensifies with 18-month lead times.\n'
            '🔗 https://wired.com/2025/11/08/chips\n\n'
            '#AI #MachineLearning #TechNews #Innovation #QuantumComputing'
        ),
        'week_key': '2025.W45',
        'article_count': 3,
        'character_count': 450,
        'hashtags': ['#AI', '#MachineLearning', '#TechNews', '#Innovation', '#QuantumComputing'],
        'sources': ['techcrunch.com', 'theverge.com', 'wired.com']
    }


# ============================================================================
# RSS Feed Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_rss_feed():
    """
    Mock RSS feed response for testing fetcher.

    Returns a mock feedparser result.
    """
    mock_feed = Mock()
    mock_feed.entries = [
        Mock(
            title='Test Article 1',
            link='https://example.com/article1',
            summary='Content for article 1',
            published='Mon, 10 Nov 2025 14:30:00 GMT'
        ),
        Mock(
            title='Test Article 2',
            link='https://example.com/article2',
            summary='Content for article 2',
            published='Mon, 10 Nov 2025 13:00:00 GMT'
        )
    ]
    mock_feed.bozo = False  # Indicates valid feed
    return mock_feed


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def freeze_time():
    """
    Freeze time for consistent date testing.

    Returns a datetime object representing the frozen time.
    """
    frozen_time = datetime(2025, 11, 10, 18, 0, 0)
    return frozen_time


@pytest.fixture
def temp_dir(tmp_path):
    """
    Provide a temporary directory for file operations.

    Uses pytest's built-in tmp_path fixture.
    """
    return tmp_path


# ============================================================================
# Test Data Factories
# ============================================================================

class ArticleFactory:
    """Factory for creating test articles."""

    @staticmethod
    def create(
        title='Test Article',
        link='https://example.com/article',
        source='example.com',
        date=None,
        content='Test article content'
    ):
        """Create a test article with optional custom fields."""
        if date is None:
            date = datetime.now()

        return {
            'title': title,
            'link': link,
            'source': source,
            'date': date,
            'content': content
        }

    @staticmethod
    def create_batch(count=5):
        """Create multiple test articles."""
        articles = []
        base_date = datetime.now()

        for i in range(count):
            articles.append(ArticleFactory.create(
                title=f'Test Article {i+1}',
                link=f'https://example.com/article-{i+1}',
                date=base_date - timedelta(days=i)
            ))

        return articles


class SummaryFactory:
    """Factory for creating test summaries."""

    @staticmethod
    def create(
        article_url='https://example.com/article',
        summary='Test summary',
        source='example.com',
        published_at=None,
        tokens_used=150,
        provider='claude'
    ):
        """Create a test summary with optional custom fields."""
        if published_at is None:
            published_at = datetime.now()

        return {
            'article_url': article_url,
            'summary': summary,
            'source': source,
            'published_at': published_at,
            'tokens_used': tokens_used,
            'provider': provider
        }

    @staticmethod
    def create_batch(count=5):
        """Create multiple test summaries."""
        summaries = []
        base_date = datetime.now()

        for i in range(count):
            summaries.append(SummaryFactory.create(
                article_url=f'https://example.com/article-{i+1}',
                summary=f'Summary of article {i+1}',
                published_at=base_date - timedelta(days=i)
            ))

        return summaries


@pytest.fixture
def article_factory():
    """Provide ArticleFactory for tests."""
    return ArticleFactory


@pytest.fixture
def summary_factory():
    """Provide SummaryFactory for tests."""
    return SummaryFactory


# ============================================================================
# Performance Measurement Fixtures
# ============================================================================

@pytest.fixture
def measure_time():
    """
    Measure execution time of test code.

    Usage:
        with measure_time() as timer:
            # code to measure
        assert timer.elapsed < 5.0
    """
    import time

    class Timer:
        def __init__(self):
            self.start = None
            self.end = None
            self.elapsed = None

        def __enter__(self):
            self.start = time.time()
            return self

        def __exit__(self, *args):
            self.end = time.time()
            self.elapsed = self.end - self.start

    return Timer
