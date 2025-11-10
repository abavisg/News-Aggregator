"""
LinkedIn Post Composer

Composes weekly tech/AI news digests into LinkedIn-ready posts.
Takes summarized articles and produces formatted, engaging posts
with headlines, highlights, hashtags, and proper character limits.
"""

import re
from datetime import datetime
from typing import Any


class ComposerError(Exception):
    """Raised when post composition fails"""

    pass


def compose_weekly_post(summaries: list[dict[str, Any]], week_key: str | None = None) -> dict[str, Any]:
    """
    Compose a LinkedIn-ready weekly digest from article summaries.

    Args:
        summaries: List of summarized articles (3-6 recommended)
        week_key: Optional week identifier (YYYY.Www format).
                 Auto-generates current week if None.

    Returns:
        Dict with composed post and metadata

    Raises:
        ComposerError: If summaries list is invalid or empty
    """
    # Validate inputs
    validate_summaries(summaries)

    # Generate week key if not provided
    if week_key is None:
        week_key = get_current_week_key()

    # Select top articles (max 6)
    selected_summaries = summaries[:6] if len(summaries) > 6 else summaries

    # Generate components
    headline = generate_headline(len(selected_summaries), week_key)
    hashtags = select_hashtags(selected_summaries)

    # Build post content
    content_parts = [headline, ""]

    # Add intro line
    content_parts.append("This week's top stories in technology and artificial intelligence:")
    content_parts.append("")

    # Add article highlights
    for idx, summary in enumerate(selected_summaries, start=1):
        highlight = format_article_highlight(summary, idx)
        content_parts.append(highlight)
        content_parts.append("")

    # Add call to action
    content_parts.append("💡 What caught your attention this week? Drop a comment below!")
    content_parts.append("")

    # Add hashtags
    hashtag_line = " ".join(hashtags)
    content_parts.append(hashtag_line)

    # Join all parts
    full_content = "\n".join(content_parts)

    # Enforce character limit
    if len(full_content) > 3000:
        full_content = truncate_to_limit(full_content, 3000)

    # Extract unique sources
    sources = list(set(s["source"] for s in selected_summaries))

    return {
        "week_key": week_key,
        "content": full_content,
        "headline": headline,
        "article_count": len(selected_summaries),
        "character_count": len(full_content),
        "hashtags": hashtags,
        "sources": sources,
        "created_at": datetime.now(),
    }


def generate_headline(article_count: int, week_key: str) -> str:
    """
    Generate engaging headline for the weekly digest.

    Args:
        article_count: Number of articles in the digest
        week_key: Week identifier (YYYY.Www)

    Returns:
        Formatted headline string
    """
    # Extract week number and year from week_key
    try:
        year, week_part = week_key.split(".")
        week_num = week_part.replace("W", "")
    except (ValueError, AttributeError):
        # Fallback if week_key format is unexpected
        week_num = week_key
        year = datetime.now().year

    return f"🚀 Tech & AI Weekly Digest — Week {week_num}, {year}"


def format_article_highlight(summary: dict[str, Any], index: int) -> str:
    """
    Format individual article as LinkedIn-friendly highlight.

    Args:
        summary: Summary dict with article data
        index: Position in the list (1-based)

    Returns:
        Formatted highlight string
    """
    # Number emojis for visual appeal
    number_emojis = {
        1: "1️⃣",
        2: "2️⃣",
        3: "3️⃣",
        4: "4️⃣",
        5: "5️⃣",
        6: "6️⃣",
    }

    emoji = number_emojis.get(index, f"{index}.")

    summary_text = summary["summary"]
    source = summary["source"]

    # Format: emoji + summary + source link
    formatted = f"{emoji} {summary_text}\n   🔗 Source: {source}"

    return formatted


def select_hashtags(summaries: list[dict[str, Any]]) -> list[str]:
    """
    Select relevant hashtags based on article content and sources.

    Args:
        summaries: List of article summaries

    Returns:
        List of 5-8 unique hashtags
    """
    # Core hashtags (always included)
    core_tags = ["#TechNews", "#ArtificialIntelligence", "#TechWeekly"]

    # Contextual hashtags based on keywords
    contextual_tags = {
        "machine learning": "#MachineLearning",
        "ml": "#MachineLearning",
        "cloud": "#CloudComputing",
        "security": "#Cybersecurity",
        "cyber": "#Cybersecurity",
        "devops": "#DevOps",
        "software": "#SoftwareEngineering",
        "data": "#DataScience",
        "open source": "#OpenSource",
        "blockchain": "#Blockchain",
        "quantum": "#QuantumComputing",
        "edge": "#EdgeComputing",
        "ai": "#AI",
        "gpt": "#AI",
        "llm": "#AI",
    }

    # Collect all summary text
    all_text = " ".join(s["summary"].lower() for s in summaries)

    # Find matching contextual tags
    matched_tags = set()
    for keyword, tag in contextual_tags.items():
        if keyword in all_text:
            matched_tags.add(tag)

    # Combine core + contextual tags
    all_tags = core_tags + list(matched_tags)

    # Remove duplicates while preserving order
    unique_tags = []
    seen = set()
    for tag in all_tags:
        if tag not in seen:
            unique_tags.append(tag)
            seen.add(tag)

    # Limit to 8 tags
    return unique_tags[:8]


def get_current_week_key() -> str:
    """
    Generate ISO week key (YYYY.Www) for current week.

    Returns:
        Week key string in format "YYYY.Www"
    """
    now = datetime.now()
    # Get ISO week number (returns tuple: year, week, weekday)
    iso_calendar = now.isocalendar()
    year = iso_calendar[0]
    week = iso_calendar[1]

    return f"{year}.W{week:02d}"


def truncate_to_limit(content: str, limit: int = 3000) -> str:
    """
    Safely truncate content to character limit while preserving structure.

    Args:
        content: Content to truncate
        limit: Maximum character count

    Returns:
        Truncated content
    """
    if len(content) <= limit:
        return content

    # Truncate with some buffer for ellipsis
    truncated = content[: limit - 50]

    # Find last complete sentence or paragraph
    last_period = truncated.rfind(".")
    last_newline = truncated.rfind("\n\n")

    # Use whichever comes later
    cut_point = max(last_period, last_newline)

    if cut_point > 0:
        # Cut at sentence/paragraph boundary
        truncated = truncated[: cut_point + 1]
    else:
        # Fallback: cut at last space
        last_space = truncated.rfind(" ")
        if last_space > 0:
            truncated = truncated[:last_space]

    # Add ellipsis if we cut content
    if len(truncated) < len(content):
        truncated += "..."

    return truncated


def validate_summaries(summaries: list[dict[str, Any]]) -> None:
    """
    Validate summaries list meets minimum requirements.

    Args:
        summaries: List of article summaries

    Raises:
        ComposerError: If validation fails
    """
    # Check if list is empty
    if not summaries or len(summaries) == 0:
        raise ComposerError("Summaries list cannot be empty")

    # Check minimum count
    if len(summaries) < 3:
        raise ComposerError(f"Need at least 3 articles to compose a post, got {len(summaries)}")

    # Check required fields in each summary
    required_fields = ["article_url", "summary", "source", "published_at", "provider"]

    for idx, summary in enumerate(summaries):
        for field in required_fields:
            if field not in summary:
                raise ComposerError(
                    f"Summary at index {idx} missing required field: {field}"
                )

        # Validate summary is not empty
        if not summary["summary"] or len(summary["summary"].strip()) == 0:
            raise ComposerError(f"Summary at index {idx} has empty summary text")
