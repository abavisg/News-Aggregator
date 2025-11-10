"""
Unit tests for the AI summarizer module.

Tests cover:
- Claude API integration
- Ollama integration
- Provider auto-detection
- Error handling and fallbacks
- Token counting
- Prompt building
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from src.core.summarizer import (
    summarize_article,
    summarize_with_claude,
    summarize_with_ollama,
    detect_provider,
    build_summary_prompt,
    count_tokens,
    SummarizerError,
)


# Sample article fixture
@pytest.fixture
def sample_article():
    """Sample article data from fetcher"""
    return {
        "title": "OpenAI Releases GPT-5 with Revolutionary Reasoning Capabilities",
        "link": "https://techcrunch.com/2025/11/10/openai-gpt5-release",
        "source": "techcrunch.com",
        "date": "2025-11-10T10:00:00Z",
        "published_at": datetime(2025, 11, 10, 10, 0, 0),
    }


@pytest.fixture
def sample_article_with_description():
    """Sample article with additional description field"""
    return {
        "title": "Google Announces Quantum Computing Breakthrough",
        "link": "https://www.theverge.com/2025/11/10/quantum-computing",
        "source": "theverge.com",
        "date": "2025-11-10T14:30:00Z",
        "published_at": datetime(2025, 11, 10, 14, 30, 0),
        "description": "Google claims to have solved a major quantum error correction problem.",
    }


class TestSummarizeArticle:
    """Test the main summarize_article function"""

    @patch("src.core.summarizer.detect_provider")
    @patch("src.core.summarizer.summarize_with_claude")
    def test_summarize_article_with_claude_success(
        self, mock_claude, mock_detect, sample_article
    ):
        """Test successful summarization using Claude API"""
        # Arrange
        mock_detect.return_value = "claude"
        mock_claude.return_value = {
            "article_url": sample_article["link"],
            "summary": "OpenAI has released GPT-5 with advanced reasoning capabilities. The new model shows significant improvements in complex problem-solving tasks.",
            "source": sample_article["source"],
            "published_at": sample_article["published_at"],
            "tokens_used": 150,
            "provider": "claude",
        }

        # Act
        result = summarize_article(sample_article)

        # Assert
        assert result["provider"] == "claude"
        assert "summary" in result
        assert len(result["summary"]) > 0
        assert result["tokens_used"] > 0
        assert result["article_url"] == sample_article["link"]
        mock_claude.assert_called_once_with(sample_article)

    @patch("src.core.summarizer.summarize_with_ollama")
    def test_summarize_article_with_ollama_success(
        self, mock_ollama, sample_article
    ):
        """Test successful summarization using Ollama"""
        # Arrange
        mock_ollama.return_value = {
            "article_url": sample_article["link"],
            "summary": "OpenAI launches GPT-5 featuring enhanced reasoning and problem-solving abilities.",
            "source": sample_article["source"],
            "published_at": sample_article["published_at"],
            "tokens_used": 120,
            "provider": "ollama",
        }

        # Act
        result = summarize_article(sample_article, provider="ollama")

        # Assert
        assert result["provider"] == "ollama"
        assert "summary" in result
        assert result["article_url"] == sample_article["link"]
        mock_ollama.assert_called_once_with(sample_article)

    @patch("src.core.summarizer.detect_provider")
    @patch("src.core.summarizer.summarize_with_claude")
    @patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test123"})
    def test_summarize_article_auto_detects_provider(
        self, mock_claude, mock_detect, sample_article
    ):
        """Test that provider is auto-detected from environment"""
        # Arrange
        mock_detect.return_value = "claude"
        mock_claude.return_value = {
            "article_url": sample_article["link"],
            "summary": "Test summary",
            "source": sample_article["source"],
            "published_at": sample_article["published_at"],
            "tokens_used": 100,
            "provider": "claude",
        }

        # Act
        result = summarize_article(sample_article)

        # Assert
        mock_detect.assert_called_once()
        assert result["provider"] == "claude"

    @patch("src.core.summarizer.summarize_with_claude")
    @patch("src.core.summarizer.summarize_with_ollama")
    def test_summarize_article_handles_missing_description(
        self, mock_ollama, mock_claude, sample_article
    ):
        """Test summarization works with only title (no description)"""
        # Arrange
        mock_ollama.return_value = {
            "article_url": sample_article["link"],
            "summary": "Summary based on title only.",
            "source": sample_article["source"],
            "published_at": sample_article["published_at"],
            "tokens_used": 80,
            "provider": "ollama",
        }

        # Act
        result = summarize_article(sample_article, provider="ollama")

        # Assert
        assert result["summary"] is not None
        assert len(result["summary"]) > 0

    def test_summarize_article_raises_on_unknown_provider(self, sample_article):
        """Test that error is raised for unknown provider"""
        # Act & Assert
        with pytest.raises(SummarizerError, match="Unknown provider"):
            summarize_article(sample_article, provider="invalid_provider")


class TestProviderDetection:
    """Test provider auto-detection logic"""

    @patch.dict(
        "os.environ",
        {
            "ANTHROPIC_API_KEY": "sk-ant-test123",
            "OLLAMA_BASE_URL": "http://localhost:11434",
        },
    )
    def test_detect_provider_prefers_claude_when_both_available(self):
        """Test that Claude is preferred when both providers are available"""
        # Act
        provider = detect_provider()

        # Assert
        assert provider == "claude"

    @patch.dict("os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}, clear=True)
    def test_detect_provider_falls_back_to_ollama(self):
        """Test fallback to Ollama when Claude is not available"""
        # Act
        provider = detect_provider()

        # Assert
        assert provider == "ollama"

    @patch.dict("os.environ", {}, clear=True)
    def test_detect_provider_raises_when_no_provider(self):
        """Test that error is raised when no provider is configured"""
        # Act & Assert
        with pytest.raises(SummarizerError, match="No AI provider configured"):
            detect_provider()


class TestClaudeIntegration:
    """Test Claude API integration"""

    @patch("src.core.summarizer.Anthropic")
    def test_summarize_with_claude_success(self, mock_anthropic_class, sample_article):
        """Test successful Claude API call"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="This is a test summary from Claude.")]
        mock_response.usage = Mock(input_tokens=50, output_tokens=30)
        mock_client.messages.create.return_value = mock_response

        # Act
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
            result = summarize_with_claude(sample_article)

        # Assert
        assert result["provider"] == "claude"
        assert result["summary"] == "This is a test summary from Claude."
        assert result["tokens_used"] == 80  # 50 + 30
        assert result["article_url"] == sample_article["link"]

    @patch("src.core.summarizer.Anthropic")
    def test_summarize_with_claude_handles_rate_limit(
        self, mock_anthropic_class, sample_article
    ):
        """Test handling of Claude API rate limit (429 error)"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        from anthropic import RateLimitError

        mock_client.messages.create.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=Mock(status_code=429),
            body=None,
        )

        # Act & Assert
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
            with pytest.raises(SummarizerError, match="Claude API rate limit"):
                summarize_with_claude(sample_article)

    @patch.dict("os.environ", {}, clear=True)
    def test_summarize_with_claude_raises_when_no_api_key(self, sample_article):
        """Test that error is raised when ANTHROPIC_API_KEY is not set"""
        # Act & Assert
        with pytest.raises(SummarizerError, match="ANTHROPIC_API_KEY not set"):
            summarize_with_claude(sample_article)

    @patch("src.core.summarizer.Anthropic")
    def test_summarize_with_claude_handles_api_error(
        self, mock_anthropic_class, sample_article
    ):
        """Test handling of general Claude API errors"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        from anthropic import APIError

        mock_client.messages.create.side_effect = APIError(
            message="API Error",
            request=Mock(),
            body=None,
        )

        # Act & Assert
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
            with pytest.raises(SummarizerError, match="Claude API error"):
                summarize_with_claude(sample_article)

    @patch("src.core.summarizer.Anthropic")
    def test_summarize_with_claude_handles_unexpected_error(
        self, mock_anthropic_class, sample_article
    ):
        """Test handling of unexpected errors in Claude"""
        # Arrange
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = ValueError("Unexpected error")

        # Act & Assert
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
            with pytest.raises(SummarizerError, match="Unexpected error with Claude"):
                summarize_with_claude(sample_article)


class TestOllamaIntegration:
    """Test Ollama integration"""

    @patch("src.core.summarizer.httpx.post")
    def test_summarize_with_ollama_success(self, mock_post, sample_article):
        """Test successful Ollama API call"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "This is a test summary from Ollama."
        }
        mock_post.return_value = mock_response

        # Act
        with patch.dict(
            "os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}
        ):
            result = summarize_with_ollama(sample_article)

        # Assert
        assert result["provider"] == "ollama"
        assert result["summary"] == "This is a test summary from Ollama."
        assert result["article_url"] == sample_article["link"]
        assert "tokens_used" in result

    @patch("src.core.summarizer.httpx.post")
    def test_summarize_with_ollama_handles_connection_error(
        self, mock_post, sample_article
    ):
        """Test handling of Ollama connection errors"""
        # Arrange
        import httpx

        mock_post.side_effect = httpx.ConnectError("Connection refused")

        # Act & Assert
        with patch.dict(
            "os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}
        ):
            with pytest.raises(SummarizerError, match="Ollama connection failed"):
                summarize_with_ollama(sample_article)

    @patch("src.core.summarizer.httpx.post")
    def test_summarize_with_ollama_handles_timeout(self, mock_post, sample_article):
        """Test handling of Ollama timeout errors"""
        # Arrange
        import httpx

        mock_post.side_effect = httpx.TimeoutException("Request timeout")

        # Act & Assert
        with patch.dict(
            "os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}
        ):
            with pytest.raises(SummarizerError, match="Ollama request timeout"):
                summarize_with_ollama(sample_article)

    @patch("src.core.summarizer.httpx.post")
    def test_summarize_with_ollama_handles_http_error(
        self, mock_post, sample_article
    ):
        """Test handling of Ollama HTTP errors (non-200 status)"""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        # Act & Assert
        with patch.dict(
            "os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}
        ):
            with pytest.raises(SummarizerError, match="Ollama API error: 500"):
                summarize_with_ollama(sample_article)

    @patch("src.core.summarizer.httpx.post")
    def test_summarize_with_ollama_handles_unexpected_error(
        self, mock_post, sample_article
    ):
        """Test handling of unexpected errors in Ollama"""
        # Arrange
        mock_post.side_effect = ValueError("Unexpected error")

        # Act & Assert
        with patch.dict(
            "os.environ", {"OLLAMA_BASE_URL": "http://localhost:11434"}
        ):
            with pytest.raises(SummarizerError, match="Unexpected error with Ollama"):
                summarize_with_ollama(sample_article)


class TestHelperFunctions:
    """Test utility/helper functions"""

    def test_build_summary_prompt_includes_title_and_description(
        self, sample_article_with_description
    ):
        """Test that prompt includes both title and description"""
        # Act
        prompt = build_summary_prompt(
            sample_article_with_description["title"],
            sample_article_with_description["description"],
        )

        # Assert
        assert sample_article_with_description["title"] in prompt
        assert sample_article_with_description["description"] in prompt
        assert "summarize" in prompt.lower()

    def test_build_summary_prompt_works_with_title_only(self):
        """Test that prompt works with only title"""
        # Arrange
        title = "AI Breakthrough Announced"

        # Act
        prompt = build_summary_prompt(title)

        # Assert
        assert title in prompt
        assert "summarize" in prompt.lower()

    def test_count_tokens_estimates_correctly(self):
        """Test token counting for cost estimation"""
        # Arrange
        short_text = "Hello world"
        long_text = "This is a much longer text that should have more tokens. " * 10

        # Act
        short_count = count_tokens(short_text)
        long_count = count_tokens(long_text)

        # Assert
        assert short_count > 0
        assert long_count > short_count
        assert short_count < 10  # "Hello world" should be < 10 tokens
        assert long_count > 50  # Long text should be > 50 tokens

    @patch("src.core.summarizer.detect_provider")
    @patch("src.core.summarizer.summarize_with_claude")
    def test_summarize_article_includes_token_count(
        self, mock_claude, mock_detect, sample_article
    ):
        """Test that result includes token usage tracking"""
        # Arrange
        mock_detect.return_value = "claude"
        mock_claude.return_value = {
            "article_url": sample_article["link"],
            "summary": "Test summary",
            "source": sample_article["source"],
            "published_at": sample_article["published_at"],
            "tokens_used": 123,
            "provider": "claude",
        }

        # Act
        result = summarize_article(sample_article)

        # Assert
        assert "tokens_used" in result
        assert isinstance(result["tokens_used"], int)
        assert result["tokens_used"] > 0
