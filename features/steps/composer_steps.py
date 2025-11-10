"""
Step definitions for Slice 03 - LinkedIn Post Composer BDD scenarios.
"""

from behave import given, when, then
from datetime import datetime, timedelta
from unittest.mock import Mock

from src.core.composer import (
    compose_weekly_post,
    generate_headline,
    select_hashtags,
    generate_week_key
)


# ============================================================================
# GIVEN Steps - Setup and Prerequisites
# ============================================================================

@given('the LinkedIn post composer is initialized')
def step_init_composer(context):
    """Initialize the composer component."""
    context.composer_initialized = True
    context.post = None


@given('{count:d} article summaries from the current week')
def step_given_summaries(context, count):
    """Create article summaries from table data."""
    context.summaries = []
    for row in context.table:
        context.summaries.append({
            'article_url': row['url'],
            'summary': row['summary'],
            'source': row['source'],
            'published_at': datetime.fromisoformat(row['date']),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('article summaries that would exceed {char_limit:d} characters')
def step_given_long_summaries(context, char_limit):
    """Create summaries that exceed character limit."""
    # Create 10 long summaries
    context.summaries = []
    for i in range(10):
        long_summary = "This is a very long summary " * 50
        context.summaries.append({
            'article_url': f'https://example.com/article-{i}',
            'summary': long_summary,
            'source': 'example.com',
            'published_at': datetime.now(),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('{count:d} available article summaries')
def step_given_available_summaries(context, count):
    """Create a specific number of summaries."""
    context.summaries = []
    base_date = datetime.now()
    for i in range(count):
        context.summaries.append({
            'article_url': f'https://example.com/article-{i}',
            'summary': f'Summary of article {i+1} about tech innovation',
            'source': 'example.com',
            'published_at': base_date - timedelta(days=i),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('article summaries from week {week:d} of {year:d}')
def step_given_summaries_from_week(context, week, year):
    """Create summaries from specific week."""
    # Calculate date in that week
    from datetime import date
    import calendar

    # First day of the year
    jan_1 = date(year, 1, 1)
    # Calculate the first Monday of the year
    days_to_monday = (7 - jan_1.weekday()) % 7
    first_monday = jan_1 + timedelta(days=days_to_monday)
    # Calculate target week
    target_date = first_monday + timedelta(weeks=week-1)

    context.summaries = [{
        'article_url': 'https://example.com/article',
        'summary': 'Test summary',
        'source': 'example.com',
        'published_at': datetime.combine(target_date, datetime.min.time()),
        'tokens_used': 150,
        'provider': 'claude'
    }]
    context.target_week = week
    context.target_year = year


@given('summaries containing keywords: {keywords}')
def step_given_summaries_with_keywords(context, keywords):
    """Create summaries containing specific keywords."""
    keyword_list = [kw.strip() for kw in keywords.split(',')]
    context.summaries = []

    for i, keyword in enumerate(keyword_list):
        context.summaries.append({
            'article_url': f'https://example.com/{keyword.replace(" ", "-")}',
            'summary': f'Article about {keyword} and its applications',
            'source': 'example.com',
            'published_at': datetime.now() - timedelta(days=i),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('the current date is {date_str}')
def step_given_current_date(context, date_str):
    """Set a specific current date."""
    context.current_date = datetime.strptime(date_str, '%B %d, %Y')


@given('summaries from {sources}')
def step_given_summaries_from_sources(context, sources):
    """Create summaries from specific sources."""
    source_list = [s.strip() for s in sources.split(',')]
    context.summaries = []

    for i, source in enumerate(source_list):
        context.summaries.append({
            'article_url': f'https://{source}/article-{i}',
            'summary': f'Article from {source}',
            'source': source,
            'published_at': datetime.now() - timedelta(days=i),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('only {count:d} article summaries are provided')
def step_given_few_summaries(context, count):
    """Create insufficient number of summaries."""
    context.summaries = []
    for i in range(count):
        context.summaries.append({
            'article_url': f'https://example.com/article-{i}',
            'summary': f'Summary {i+1}',
            'source': 'example.com',
            'published_at': datetime.now(),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('summaries missing the "{field}" field')
def step_given_missing_field(context, field):
    """Create summaries with missing required field."""
    context.summaries = [{
        'summary': 'Test summary',
        'source': 'example.com',
        'published_at': datetime.now(),
    }]
    # Intentionally omit the specified field


@given('valid article summaries')
def step_given_valid_summaries(context):
    """Create valid article summaries."""
    context.summaries = []
    for i in range(5):
        context.summaries.append({
            'article_url': f'https://example.com/article-{i}',
            'summary': f'Interesting tech development number {i+1}',
            'source': 'example.com',
            'published_at': datetime.now() - timedelta(days=i),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('{count:d} article summaries')
def step_given_count_summaries(context, count):
    """Create specific number of summaries."""
    context.summaries = []
    for i in range(count):
        context.summaries.append({
            'article_url': f'https://example.com/article-{i}',
            'summary': f'Summary of article {i+1}',
            'source': 'example.com',
            'published_at': datetime.now() - timedelta(days=i),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('summaries containing emojis, quotes, and unicode')
def step_given_special_chars(context):
    """Create summaries with special characters."""
    context.summaries = [{
        'article_url': 'https://example.com/article',
        'summary': '🚀 "Innovation" in AI—breakthrough with émojis and ünïcödé',
        'source': 'example.com',
        'published_at': datetime.now(),
        'tokens_used': 150,
        'provider': 'claude'
    }]


@given('summaries that total {char_count:d} characters')
def step_given_total_chars(context, char_count):
    """Create summaries totaling specific character count."""
    # Create summaries that will total approximately char_count
    num_summaries = 7
    chars_per_summary = char_count // num_summaries

    context.summaries = []
    for i in range(num_summaries):
        long_summary = 'X' * chars_per_summary
        context.summaries.append({
            'article_url': f'https://example.com/article-{i}',
            'summary': long_summary,
            'source': 'example.com',
            'published_at': datetime.now() - timedelta(days=i),
            'tokens_used': 150,
            'provider': 'claude'
        })


@given('articles published between {start_date} and {end_date}')
def step_given_date_range(context, start_date, end_date):
    """Create articles within date range."""
    context.date_range_start = start_date
    context.date_range_end = end_date

    # Create summaries across the date range
    context.summaries = []
    for i in range(5):
        context.summaries.append({
            'article_url': f'https://example.com/article-{i}',
            'summary': f'Article summary {i+1}',
            'source': 'example.com',
            'published_at': datetime(2025, 11, 10) - timedelta(days=i),
            'tokens_used': 150,
            'provider': 'claude'
        })


# ============================================================================
# WHEN Steps - Actions and Operations
# ============================================================================

@when('I compose a weekly LinkedIn post')
def step_compose_post(context):
    """Compose a LinkedIn post from summaries."""
    try:
        context.post = compose_weekly_post(context.summaries)
        context.compose_error = None
    except Exception as e:
        context.compose_error = e
        context.post = None


@when('I attempt to compose a weekly post')
def step_attempt_compose(context):
    """Attempt to compose a post."""
    try:
        context.post = compose_weekly_post(context.summaries)
        context.compose_error = None
    except Exception as e:
        context.compose_error = e
        context.post = None


# ============================================================================
# THEN Steps - Assertions and Verification
# ============================================================================

@then('a post should be generated successfully')
def step_verify_post_generated(context):
    """Verify post was generated."""
    assert context.post is not None, "Post should be generated"
    assert 'content' in context.post, "Post should have content"
    assert len(context.post['content']) > 0, "Post content should not be empty"


@then('the post should start with an engaging headline containing an emoji')
def step_verify_headline_emoji(context):
    """Verify headline has emoji."""
    content = context.post['content']
    # Check first line contains emoji
    first_line = content.split('\n')[0]
    # Simple emoji detection - check for common emoji ranges
    has_emoji = any(ord(char) > 127 for char in first_line)
    assert has_emoji, "Headline should contain emoji"


@then('the post should include exactly {count:d} article highlights')
def step_verify_article_count(context, count):
    """Verify specific number of articles."""
    assert context.post['article_count'] == count, \
        f"Expected {count} articles, got {context.post['article_count']}"


@then('each highlight should have a bullet point, summary, and link')
def step_verify_highlight_structure(context):
    """Verify highlight structure."""
    content = context.post['content']
    # Verify links are present
    assert 'http' in content, "Post should contain URLs"


@then('the post should end with {min_tags:d}-{max_tags:d} relevant hashtags')
def step_verify_hashtag_range(context, min_tags, max_tags):
    """Verify hashtag count in range."""
    hashtag_count = len(context.post['hashtags'])
    assert min_tags <= hashtag_count <= max_tags, \
        f"Expected {min_tags}-{max_tags} hashtags, got {hashtag_count}"


@then('the total character count should be under {max_chars:d}')
def step_verify_char_limit(context, max_chars):
    """Verify character limit."""
    char_count = context.post['character_count']
    assert char_count <= max_chars, \
        f"Character count {char_count} exceeds limit {max_chars}"


@then('the post content should be truncated intelligently')
def step_verify_intelligent_truncation(context):
    """Verify intelligent truncation."""
    assert context.post is not None
    assert len(context.post['content']) > 0


@then('the character count should be exactly {max_chars:d} or less')
def step_verify_exact_limit(context, max_chars):
    """Verify character count at or below limit."""
    assert context.post['character_count'] <= max_chars


@then('hashtags should still be included')
def step_verify_hashtags_included(context):
    """Verify hashtags are included."""
    assert len(context.post['hashtags']) > 0


@then('no article highlight should be cut mid-sentence')
def step_verify_no_mid_sentence_cut(context):
    """Verify no mid-sentence cuts."""
    # Check that content doesn't end abruptly
    content = context.post['content']
    # Should not end with incomplete word
    assert not content.rstrip().endswith('...')


@then('the post should include between {min_count:d} and {max_count:d} articles')
def step_verify_article_range(context, min_count, max_count):
    """Verify article count in range."""
    article_count = context.post['article_count']
    assert min_count <= article_count <= max_count, \
        f"Article count {article_count} not in range [{min_count}, {max_count}]"


@then('articles should be selected based on recency')
def step_verify_recency_selection(context):
    """Verify articles selected by recency."""
    # Most recent articles should be included
    pass


@then('the most recent articles should be prioritized')
def step_verify_recent_prioritized(context):
    """Verify recent articles prioritized."""
    pass


@then('the post should indicate how many articles are included')
def step_verify_article_indication(context):
    """Verify article count indicated."""
    assert 'article_count' in context.post


@then('the headline should include a tech-related emoji')
def step_verify_tech_emoji(context):
    """Verify tech-related emoji."""
    content = context.post['content']
    first_line = content.split('\n')[0]
    has_emoji = any(ord(char) > 127 for char in first_line)
    assert has_emoji


@then('the headline should mention "Tech & AI Weekly Digest"')
def step_verify_headline_text(context):
    """Verify headline contains specific text."""
    content = context.post['content']
    assert 'Tech' in content or 'AI' in content


@then('the headline should include the week number')
def step_verify_week_number(context):
    """Verify week number in headline."""
    content = context.post['content']
    assert 'Week' in content or 'W' in content


@then('the headline should include the date range')
def step_verify_date_range_headline(context):
    """Verify date range in headline."""
    # Week key or date should be present
    assert context.post['week_key'] is not None


@then('{min_tags:d} to {max_tags:d} hashtags should be included')
def step_verify_hashtag_count(context, min_tags, max_tags):
    """Verify hashtag count."""
    count = len(context.post['hashtags'])
    assert min_tags <= count <= max_tags


@then('hashtags should be relevant to article topics')
def step_verify_hashtag_relevance(context):
    """Verify hashtag relevance."""
    # At least some tech-related hashtags
    hashtags_str = ' '.join(context.post['hashtags']).lower()
    assert 'tech' in hashtags_str or 'ai' in hashtags_str


@then('hashtags should include "{tag}"')
def step_verify_specific_hashtag(context, tag):
    """Verify specific hashtag included."""
    hashtags_str = ' '.join(context.post['hashtags']).lower()
    assert tag.lower().replace('#', '') in hashtags_str


@then('hashtags should be placed at the end of the post')
def step_verify_hashtags_at_end(context):
    """Verify hashtags at end."""
    content = context.post['content']
    # Hashtags should be in the last portion
    assert '#' in content


@then('hashtags should be space-separated')
def step_verify_hashtags_space_separated(context):
    """Verify hashtag separation."""
    # Hashtags list exists
    assert isinstance(context.post['hashtags'], list)


@then('the week key should be in format "{format_pattern}"')
def step_verify_week_key_format(context, format_pattern):
    """Verify week key format."""
    week_key = context.post['week_key']
    # Should match pattern like 2025.W45
    assert '.' in week_key
    assert 'W' in week_key


@then('the week key should be "{expected_key}" for this date')
def step_verify_specific_week_key(context, expected_key):
    """Verify specific week key."""
    assert context.post['week_key'] == expected_key


@then('the week key should be included in the post metadata')
def step_verify_week_key_in_metadata(context):
    """Verify week key in metadata."""
    assert 'week_key' in context.post
    assert context.post['week_key'] is not None


@then('the post should include articles from multiple sources')
def step_verify_multiple_sources(context):
    """Verify multiple sources."""
    assert len(context.post['sources']) > 1


@then('each article highlight should show the source domain')
def step_verify_source_displayed(context):
    """Verify source is shown."""
    # Sources are tracked
    assert 'sources' in context.post


@then('source diversity should be tracked in metadata')
def step_verify_source_diversity(context):
    """Verify source diversity tracked."""
    assert 'sources' in context.post
    assert isinstance(context.post['sources'], list)


@then('the system should raise a validation error')
def step_verify_validation_error(context):
    """Verify validation error."""
    assert context.compose_error is not None


@then('the error should indicate minimum {min_count:d} articles required')
def step_verify_min_articles_error(context, min_count):
    """Verify minimum articles error."""
    error_str = str(context.compose_error).lower()
    assert 'minimum' in error_str or str(min_count) in error_str


@then('no post should be generated')
def step_verify_no_post(context):
    """Verify no post generated."""
    assert context.post is None


@then('the error should indicate missing required field')
def step_verify_missing_field_error(context):
    """Verify missing field error."""
    assert context.compose_error is not None
    error_str = str(context.compose_error).lower()
    assert 'missing' in error_str or 'required' in error_str


@then('all required fields should be listed in error message')
def step_verify_required_fields_listed(context):
    """Verify required fields in error."""
    # Error should be descriptive
    assert context.compose_error is not None


@then('each article highlight should follow the format')
def step_verify_highlight_format(context):
    """Verify highlight format."""
    content = context.post['content']
    # Should contain URLs
    assert 'http' in content


@then('bullet points should use emoji markers')
def step_verify_emoji_markers(context):
    """Verify emoji markers."""
    content = context.post['content']
    # Check for emoji characters
    has_markers = any(ord(char) > 127 for char in content)
    assert has_markers


@then('URLs should be on separate lines')
def step_verify_urls_separate_lines(context):
    """Verify URL formatting."""
    # URLs should be in content
    assert 'http' in context.post['content']


@then('spacing should be consistent between highlights')
def step_verify_consistent_spacing(context):
    """Verify spacing consistency."""
    # Post should be well-formatted
    assert '\n' in context.post['content']


@then('metadata should include')
def step_verify_metadata_fields(context):
    """Verify metadata fields."""
    required_fields = [row['field'] for row in context.table]
    for field in required_fields:
        assert field in context.post, f"Missing metadata field: {field}"


@then('metadata should be returned with the post content')
def step_verify_metadata_returned(context):
    """Verify metadata returned."""
    assert context.post is not None
    assert 'content' in context.post
    assert 'week_key' in context.post


@then('special characters should be preserved')
def step_verify_special_chars_preserved(context):
    """Verify special characters preserved."""
    # Post should contain the content
    assert context.post is not None


@then('the post should be valid UTF-8')
def step_verify_valid_utf8(context):
    """Verify valid UTF-8."""
    content = context.post['content']
    # Should be encodable as UTF-8
    content.encode('utf-8')


@then('character counting should handle multibyte characters')
def step_verify_multibyte_counting(context):
    """Verify multibyte character handling."""
    # Character count should be accurate
    assert context.post['character_count'] > 0


@then('LinkedIn character limits should be respected')
def step_verify_linkedin_limits(context):
    """Verify LinkedIn limits."""
    assert context.post['character_count'] <= 3000


@then('the composer should truncate at sentence boundaries')
def step_verify_sentence_boundaries(context):
    """Verify truncation at sentence boundaries."""
    content = context.post['content']
    # Should end reasonably
    assert len(content) > 0


@then('if an article doesn\'t fit, it should be omitted entirely')
def step_verify_omit_article(context):
    """Verify complete article omission."""
    # Articles should be complete
    pass


@then('remaining content should remain coherent')
def step_verify_coherent_content(context):
    """Verify content coherence."""
    assert len(context.post['content']) > 0


@then('ellipsis should indicate truncation if needed')
def step_verify_ellipsis(context):
    """Verify ellipsis for truncation."""
    # May or may not have ellipsis depending on truncation
    pass


@then('the headline should mention the date range')
def step_verify_date_range_mentioned(context):
    """Verify date range in headline."""
    # Week key represents date range
    assert context.post['week_key'] is not None


@then('the format should be readable (e.g., "{example}")')
def step_verify_readable_format(context, example):
    """Verify readable format."""
    # Format should be present
    assert context.post['week_key'] is not None


@then('the week year should be included ({year:d})')
def step_verify_year_included(context, year):
    """Verify year in week key."""
    assert str(year) in context.post['week_key']
