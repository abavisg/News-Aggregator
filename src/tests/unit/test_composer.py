"""
Unit tests for the LinkedIn post composer module.

Tests cover:
- Post composition from summaries
- Headline generation
- Article formatting
- Hashtag selection
- Character limit enforcement
- Week key generation
- Input validation
"""

import pytest
from datetime import datetime
from src.core.composer import (
    compose_weekly_post,
    generate_headline,
    format_article_highlight,
    select_hashtags,
    get_current_week_key,
    truncate_to_limit,
    validate_summaries,
    ComposerError,
)


# Sample summaries fixture
@pytest.fixture
def sample_summaries():
    """Sample summarized articles from Slice 02"""
    return [
        {
            "article_url": "https://techcrunch.com/2025/11/10/openai-gpt5",
            "summary": "OpenAI releases GPT-5 with breakthrough reasoning capabilities, achieving 95% accuracy on complex logic tasks and introducing real-time learning features.",
            "source": "techcrunch.com",
            "published_at": datetime(2025, 11, 10, 10, 0, 0),
            "tokens_used": 150,
            "provider": "claude",
        },
        {
            "article_url": "https://www.theverge.com/2025/11/09/quantum-computing",
            "summary": "Google announces major quantum computing breakthrough, demonstrating error correction that could enable practical quantum computers within 2 years.",
            "source": "theverge.com",
            "published_at": datetime(2025, 11, 9, 14, 30, 0),
            "tokens_used": 140,
            "provider": "claude",
        },
        {
            "article_url": "https://www.wired.com/2025/11/08/ai-chip-shortage",
            "summary": "Global AI chip shortage intensifies as demand for training infrastructure outpaces production, with lead times extending to 18 months for H100 GPUs.",
            "source": "wired.com",
            "published_at": datetime(2025, 11, 8, 9, 15, 0),
            "tokens_used": 135,
            "provider": "claude",
        },
        {
            "article_url": "https://arstechnica.com/2025/11/07/rust-linux-kernel",
            "summary": "Linux kernel 6.7 ships with 15% of drivers now written in Rust, marking a significant milestone in the language's adoption for systems programming.",
            "source": "arstechnica.com",
            "published_at": datetime(2025, 11, 7, 16, 45, 0),
            "tokens_used": 120,
            "provider": "claude",
        },
        {
            "article_url": "https://venturebeat.com/2025/11/06/microsoft-copilot",
            "summary": "Microsoft Copilot reaches 1 million enterprise customers, generating $1.5B in annual revenue as AI assistants become mainstream in workplace productivity.",
            "source": "venturebeat.com",
            "published_at": datetime(2025, 11, 6, 11, 20, 0),
            "tokens_used": 145,
            "provider": "claude",
        },
    ]


@pytest.fixture
def minimal_summaries():
    """Minimal valid summaries (exactly 3 articles)"""
    return [
        {
            "article_url": "https://example.com/article1",
            "summary": "First article summary about AI developments.",
            "source": "example.com",
            "published_at": datetime(2025, 11, 10, 10, 0, 0),
            "tokens_used": 100,
            "provider": "claude",
        },
        {
            "article_url": "https://example.com/article2",
            "summary": "Second article summary about cloud computing.",
            "source": "example.com",
            "published_at": datetime(2025, 11, 9, 10, 0, 0),
            "tokens_used": 100,
            "provider": "claude",
        },
        {
            "article_url": "https://example.com/article3",
            "summary": "Third article summary about cybersecurity.",
            "source": "example.com",
            "published_at": datetime(2025, 11, 8, 10, 0, 0),
            "tokens_used": 100,
            "provider": "claude",
        },
    ]


@pytest.fixture
def many_summaries():
    """More than 6 summaries to test selection logic"""
    return [
        {
            "article_url": f"https://example.com/article{i}",
            "summary": f"Article {i} summary about tech topic {i}.",
            "source": "example.com",
            "published_at": datetime(2025, 11, 10 - i, 10, 0, 0),
            "tokens_used": 100,
            "provider": "claude",
        }
        for i in range(10)
    ]


# Test 1: Successful post composition
def test_compose_weekly_post_success(sample_summaries):
    """Test successful composition with valid summaries"""
    result = compose_weekly_post(sample_summaries)

    assert "week_key" in result
    assert "content" in result
    assert "headline" in result
    assert "article_count" in result
    assert "character_count" in result
    assert "hashtags" in result
    assert "sources" in result
    assert "created_at" in result

    assert isinstance(result["content"], str)
    assert len(result["content"]) > 0
    assert result["article_count"] == 5
    assert result["character_count"] <= 3000


# Test 2: Custom week key
def test_compose_weekly_post_with_custom_week_key(sample_summaries):
    """Test composition with custom week key"""
    custom_week = "2025.W45"
    result = compose_weekly_post(sample_summaries, week_key=custom_week)

    assert result["week_key"] == custom_week
    assert custom_week in result["content"] or "45" in result["content"]


# Test 3: Auto-generate week key
def test_compose_weekly_post_auto_generates_week_key(sample_summaries):
    """Test that week key is auto-generated when not provided"""
    result = compose_weekly_post(sample_summaries)

    assert result["week_key"] is not None
    assert isinstance(result["week_key"], str)
    # Should match YYYY.Www format
    assert "." in result["week_key"]
    assert result["week_key"].startswith("20")


# Test 4: Minimum articles (3)
def test_compose_weekly_post_with_minimum_articles(minimal_summaries):
    """Test composition with exactly 3 articles (minimum)"""
    result = compose_weekly_post(minimal_summaries)

    assert result["article_count"] == 3
    assert len(result["sources"]) >= 1
    assert result["character_count"] <= 3000


# Test 5: Maximum articles (selects 6 from 10)
def test_compose_weekly_post_with_maximum_articles(many_summaries):
    """Test that composer selects best 6 articles from many"""
    result = compose_weekly_post(many_summaries)

    assert result["article_count"] == 6
    assert result["character_count"] <= 3000


# Test 6: Character limit enforcement
def test_compose_weekly_post_enforces_character_limit():
    """Test that post never exceeds 3000 character limit"""
    # Create summaries with very long text
    long_summaries = [
        {
            "article_url": f"https://example.com/article{i}",
            "summary": "This is a very long summary that repeats itself many times. " * 50,
            "source": "example.com",
            "published_at": datetime(2025, 11, 10 - i, 10, 0, 0),
            "tokens_used": 500,
            "provider": "claude",
        }
        for i in range(6)
    ]

    result = compose_weekly_post(long_summaries)

    assert result["character_count"] <= 3000
    assert len(result["content"]) <= 3000


# Test 7: Empty summaries list
def test_compose_weekly_post_raises_on_empty_summaries():
    """Test that empty summaries list raises ComposerError"""
    with pytest.raises(ComposerError, match="empty"):
        compose_weekly_post([])


# Test 8: Too few articles
def test_compose_weekly_post_raises_on_too_few_articles():
    """Test that fewer than 3 articles raises ComposerError"""
    too_few = [
        {
            "article_url": "https://example.com/article1",
            "summary": "Only one article summary.",
            "source": "example.com",
            "published_at": datetime(2025, 11, 10, 10, 0, 0),
            "tokens_used": 100,
            "provider": "claude",
        }
    ]

    with pytest.raises(ComposerError, match="at least 3"):
        compose_weekly_post(too_few)


# Test 9: Generate headline
def test_generate_headline_includes_week_and_count():
    """Test headline generation includes week reference and article count"""
    headline = generate_headline(article_count=5, week_key="2025.W45")

    assert isinstance(headline, str)
    assert len(headline) > 0
    # Should reference the week or article count
    assert "5" in headline or "Week" in headline or "45" in headline


# Test 10: Format article highlight
def test_format_article_highlight_creates_readable_format(sample_summaries):
    """Test article formatting creates readable highlight"""
    formatted = format_article_highlight(sample_summaries[0], index=1)

    assert isinstance(formatted, str)
    assert len(formatted) > 0
    # Should include the summary text
    assert "GPT-5" in formatted or "OpenAI" in formatted
    # Should include source
    assert "techcrunch" in formatted.lower()


# Test 11: Select hashtags
def test_select_hashtags_returns_relevant_tags(sample_summaries):
    """Test hashtag selection returns relevant tags"""
    hashtags = select_hashtags(sample_summaries)

    assert isinstance(hashtags, list)
    assert 5 <= len(hashtags) <= 8
    # All hashtags should start with #
    for tag in hashtags:
        assert tag.startswith("#")
    # Should include core tech tags
    assert any("Tech" in tag for tag in hashtags) or any("AI" in tag for tag in hashtags)


# Test 12: Hashtags are unique
def test_select_hashtags_avoids_duplicates(sample_summaries):
    """Test that hashtags are unique (no duplicates)"""
    hashtags = select_hashtags(sample_summaries)

    # Check for uniqueness
    assert len(hashtags) == len(set(hashtags))


# Test 13: Get current week key
def test_get_current_week_key_returns_iso_format():
    """Test week key generation returns ISO format"""
    week_key = get_current_week_key()

    assert isinstance(week_key, str)
    # Should match YYYY.Www format
    assert "." in week_key
    assert week_key[0:4].isdigit()  # Year
    assert week_key.startswith("20")  # 21st century
    assert "W" in week_key


# Test 14: Truncate to limit preserves structure
def test_truncate_to_limit_preserves_structure():
    """Test truncation preserves structure and doesn't cut mid-word"""
    long_content = "This is a test sentence. " * 200  # ~5000 chars

    truncated = truncate_to_limit(long_content, limit=3000)

    assert len(truncated) <= 3000
    # Should not end mid-word (should end with space or punctuation)
    assert truncated[-1] in [" ", ".", "!", "?", "\n"] or truncated.endswith("...")


# Test 15: Validate summaries accepts valid list
def test_validate_summaries_accepts_valid_list(sample_summaries):
    """Test validation passes for valid summaries"""
    # Should not raise any exception
    validate_summaries(sample_summaries)


# Test 16: Validate summaries rejects invalid format
def test_validate_summaries_rejects_invalid_format():
    """Test validation rejects summaries with missing fields"""
    invalid_summaries = [
        {
            "article_url": "https://example.com/article1",
            # Missing summary field
            "source": "example.com",
        }
    ]

    with pytest.raises(ComposerError):
        validate_summaries(invalid_summaries)


# Test 17: Unique sources tracking
def test_compose_includes_unique_sources(sample_summaries):
    """Test that result includes unique source names"""
    result = compose_weekly_post(sample_summaries)

    assert "sources" in result
    assert isinstance(result["sources"], list)
    assert len(result["sources"]) > 0
    # Should have multiple unique sources
    assert len(set(result["sources"])) >= 3


# Test 18: Call to action included
def test_compose_adds_call_to_action(sample_summaries):
    """Test that post includes engagement call-to-action"""
    result = compose_weekly_post(sample_summaries)

    content_lower = result["content"].lower()
    # Should have some form of CTA
    cta_phrases = ["comment", "share", "thoughts", "think", "?", "drop", "let me know"]
    assert any(phrase in content_lower for phrase in cta_phrases)


# Test 19: Content structure validation
def test_compose_post_has_proper_structure(sample_summaries):
    """Test that composed post has proper structure with sections"""
    result = compose_weekly_post(sample_summaries)

    content = result["content"]
    # Should have multiple line breaks for readability
    assert "\n" in content
    # Should include hashtags at the end
    assert "#" in content
    # Should include numbered or bulleted items
    assert any(char in content for char in ["1", "2", "3", "•", "▪"])


# Test 20: Handles missing optional fields gracefully
def test_compose_handles_missing_optional_fields():
    """Test composition works even with minimal summary fields"""
    minimal = [
        {
            "article_url": "https://example.com/1",
            "summary": "Summary 1",
            "source": "example.com",
            "published_at": datetime(2025, 11, 10, 10, 0, 0),
            "provider": "claude",
            # Missing tokens_used (optional)
        },
        {
            "article_url": "https://example.com/2",
            "summary": "Summary 2",
            "source": "example.com",
            "published_at": datetime(2025, 11, 9, 10, 0, 0),
            "provider": "claude",
        },
        {
            "article_url": "https://example.com/3",
            "summary": "Summary 3",
            "source": "example.com",
            "published_at": datetime(2025, 11, 8, 10, 0, 0),
            "provider": "claude",
        },
    ]

    result = compose_weekly_post(minimal)
    assert result["article_count"] == 3


# Test 21: Created timestamp
def test_compose_includes_creation_timestamp(sample_summaries):
    """Test that result includes creation timestamp"""
    result = compose_weekly_post(sample_summaries)

    assert "created_at" in result
    assert isinstance(result["created_at"], datetime)


# Test 22: Hashtags appear at end of content
def test_hashtags_appear_at_end_of_content(sample_summaries):
    """Test that hashtags are placed at the end of the post"""
    result = compose_weekly_post(sample_summaries)

    content = result["content"]
    hashtags = result["hashtags"]

    # Find last hashtag position
    last_hashtag_pos = max([content.rfind(tag) for tag in hashtags])
    # Should be in last 25% of content
    assert last_hashtag_pos > len(content) * 0.75
