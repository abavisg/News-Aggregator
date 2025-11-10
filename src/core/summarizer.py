"""
AI-powered article summarizer using Claude API or Ollama.

This module provides summarization capabilities for news articles using either:
- Anthropic's Claude API (cloud-based)
- Ollama (local LLM)

Auto-detects the available provider from environment variables.
"""

import os
import httpx
import structlog
from typing import Optional
from anthropic import Anthropic, RateLimitError, APIError

logger = structlog.get_logger()


class SummarizerError(Exception):
    """Raised when summarization fails on all providers"""

    pass


def detect_provider() -> str:
    """
    Auto-detect available AI provider from environment variables.

    Priority: Claude API > Ollama

    Returns:
        str: "claude" or "ollama"

    Raises:
        SummarizerError: If no provider is configured
    """
    if os.getenv("ANTHROPIC_API_KEY"):
        logger.debug("detected_provider", provider="claude")
        return "claude"
    elif os.getenv("OLLAMA_BASE_URL"):
        logger.debug("detected_provider", provider="ollama")
        return "ollama"
    else:
        logger.error("no_provider_configured")
        raise SummarizerError(
            "No AI provider configured. Set ANTHROPIC_API_KEY or OLLAMA_BASE_URL."
        )


def build_summary_prompt(title: str, description: str = "") -> str:
    """
    Build consistent prompt for article summarization.

    Args:
        title: Article headline
        description: Optional article description/excerpt

    Returns:
        str: Formatted prompt for the AI model
    """
    prompt = """You are a tech news summarizer. Summarize the following article in 1-3 concise sentences, focusing on:
- The main technical development or news
- Why it matters to the tech/AI community
- Key facts or metrics (if any)

Title: {title}"""

    if description:
        prompt += "\nDescription: {description}"

    prompt += "\n\nProvide only the summary, no preamble or explanation."

    return prompt.format(title=title, description=description)


def count_tokens(text: str) -> int:
    """
    Estimate token count for cost tracking.

    Uses a simple approximation: ~4 characters per token (common for English).
    For production use, consider using tiktoken for accurate counts.

    Args:
        text: Text to count tokens for

    Returns:
        int: Estimated token count
    """
    # Simple estimation: average 4 characters per token
    return max(1, len(text) // 4)


def summarize_with_claude(article: dict) -> dict:
    """
    Summarize article using Claude API.

    Args:
        article: Normalized article dict with title, link, etc.

    Returns:
        dict: Summary result with metadata

    Raises:
        SummarizerError: If API call fails
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise SummarizerError("ANTHROPIC_API_KEY not set")

    model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

    try:
        client = Anthropic(api_key=api_key)

        # Build prompt
        description = article.get("description", "")
        prompt = build_summary_prompt(article["title"], description)

        logger.info(
            "summarizing_with_claude",
            article_url=article["link"],
            model=model,
        )

        # Call Claude API
        response = client.messages.create(
            model=model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )

        summary_text = response.content[0].text
        tokens_used = response.usage.input_tokens + response.usage.output_tokens

        logger.info(
            "claude_summary_complete",
            article_url=article["link"],
            tokens_used=tokens_used,
        )

        return {
            "article_url": article["link"],
            "summary": summary_text,
            "source": article["source"],
            "published_at": article["published_at"],
            "tokens_used": tokens_used,
            "provider": "claude",
        }

    except RateLimitError as e:
        logger.error("claude_rate_limit", error=str(e))
        raise SummarizerError(f"Claude API rate limit exceeded: {e}")

    except APIError as e:
        logger.error("claude_api_error", error=str(e))
        raise SummarizerError(f"Claude API error: {e}")

    except Exception as e:
        logger.error("claude_unexpected_error", error=str(e))
        raise SummarizerError(f"Unexpected error with Claude: {e}")


def summarize_with_ollama(article: dict) -> dict:
    """
    Summarize article using local Ollama.

    Args:
        article: Normalized article dict with title, link, etc.

    Returns:
        dict: Summary result with metadata

    Raises:
        SummarizerError: If Ollama call fails
    """
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")

    # Build prompt
    description = article.get("description", "")
    prompt = build_summary_prompt(article["title"], description)

    logger.info(
        "summarizing_with_ollama",
        article_url=article["link"],
        model=model,
    )

    try:
        response = httpx.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
            timeout=30.0,
        )

        if response.status_code != 200:
            raise SummarizerError(
                f"Ollama API error: {response.status_code} - {response.text}"
            )

        result = response.json()
        summary_text = result["response"]

        # Estimate tokens for Ollama (no built-in tracking)
        tokens_used = count_tokens(prompt) + count_tokens(summary_text)

        logger.info(
            "ollama_summary_complete",
            article_url=article["link"],
            tokens_estimated=tokens_used,
        )

        return {
            "article_url": article["link"],
            "summary": summary_text,
            "source": article["source"],
            "published_at": article["published_at"],
            "tokens_used": tokens_used,
            "provider": "ollama",
        }

    except httpx.ConnectError as e:
        logger.error("ollama_connection_error", error=str(e))
        raise SummarizerError(f"Ollama connection failed: {e}")

    except httpx.TimeoutException as e:
        logger.error("ollama_timeout", error=str(e))
        raise SummarizerError(f"Ollama request timeout: {e}")

    except Exception as e:
        logger.error("ollama_unexpected_error", error=str(e))
        raise SummarizerError(f"Unexpected error with Ollama: {e}")


def summarize_article(article: dict, provider: Optional[str] = None) -> dict:
    """
    Generate a concise summary of a news article using AI.

    Args:
        article: Normalized article dict from fetcher with keys:
                 {title, link, source, date, published_at}
        provider: Optional override ("claude" or "ollama").
                  Auto-detects from env if None.

    Returns:
        dict: Summary result with keys:
              {article_url, summary, source, published_at, tokens_used, provider}

    Raises:
        SummarizerError: If summarization fails
    """
    # Determine provider
    if provider is None:
        provider = detect_provider()

    logger.info(
        "summarizing_article",
        article_title=article["title"],
        provider=provider,
    )

    # Route to appropriate provider
    if provider == "claude":
        return summarize_with_claude(article)
    elif provider == "ollama":
        return summarize_with_ollama(article)
    else:
        raise SummarizerError(f"Unknown provider: {provider}")
