# Slice 03: LinkedIn Post Composer

## Goal
Implement a LinkedIn post composer that takes AI-generated article summaries and produces a polished, engaging weekly digest ready for publication.

## Acceptance Criteria

1. **Functional Requirements:**
   - Compose weekly digest from 3-6 article summaries
   - Generate engaging headline/introduction
   - Format article highlights with clear structure
   - Add relevant tech/AI hashtags (5-8 tags)
   - Enforce LinkedIn character limit (≤3000 characters)
   - Include week identifier (ISO week format: YYYY.Www)
   - Support customizable intro templates
   - Handle edge cases (empty summaries, too few articles)

2. **Non-Functional Requirements:**
   - Processing time: < 1 second per post
   - Test coverage: ≥ 90%
   - Character limit compliance: 100% (never exceed 3000 chars)
   - Logging: structured logs for composition operations
   - Readability: proper formatting with line breaks and emojis

3. **Data Format:**
   ```python
   # Input: List of summaries from Slice 02
   [
       {
           "article_url": str,
           "summary": str,
           "source": str,
           "published_at": datetime,
           "tokens_used": int,
           "provider": str
       },
       ...
   ]

   # Output: Composed LinkedIn post
   {
       "week_key": str,              # e.g., "2025.W45"
       "content": str,               # Full LinkedIn post text
       "headline": str,              # Generated headline
       "article_count": int,         # Number of articles included
       "character_count": int,       # Total characters
       "hashtags": list[str],        # List of hashtags used
       "sources": list[str],         # Unique sources featured
       "created_at": datetime        # Composition timestamp
   }
   ```

## Technical Design

### Module: `src/core/composer.py`

**Main Function:**
```python
def compose_weekly_post(summaries: list[dict], week_key: str = None) -> dict:
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
```

**Helper Functions:**
```python
def generate_headline(article_count: int, week_key: str) -> str:
    """Generate engaging headline for the weekly digest"""

def format_article_highlight(summary: dict, index: int) -> str:
    """Format individual article as LinkedIn-friendly highlight"""

def select_hashtags(summaries: list[dict]) -> list[str]:
    """Select relevant hashtags based on article content and sources"""

def get_current_week_key() -> str:
    """Generate ISO week key (YYYY.Www) for current week"""

def truncate_to_limit(content: str, limit: int = 3000) -> str:
    """Safely truncate content to character limit while preserving structure"""

def validate_summaries(summaries: list[dict]) -> None:
    """Validate summaries list meets minimum requirements"""
```

**Custom Exception:**
```python
class ComposerError(Exception):
    """Raised when post composition fails"""
```

## Test Cases

### Unit Tests (`src/tests/unit/test_composer.py`)

1. `test_compose_weekly_post_success()`
   - Given: Valid list of 5 summarized articles
   - When: compose_weekly_post() is called
   - Then: Returns complete post dict with all required fields

2. `test_compose_weekly_post_with_custom_week_key()`
   - Given: Summaries and custom week_key="2025.W45"
   - When: compose_weekly_post() is called
   - Then: Uses provided week_key in output

3. `test_compose_weekly_post_auto_generates_week_key()`
   - Given: Summaries without week_key parameter
   - When: compose_weekly_post() is called
   - Then: Generates current week key automatically

4. `test_compose_weekly_post_with_minimum_articles()`
   - Given: Exactly 3 article summaries
   - When: compose_weekly_post() is called
   - Then: Successfully creates post with 3 highlights

5. `test_compose_weekly_post_with_maximum_articles()`
   - Given: 10 article summaries
   - When: compose_weekly_post() is called
   - Then: Selects best 6 articles for inclusion

6. `test_compose_weekly_post_enforces_character_limit()`
   - Given: Summaries that would exceed 3000 characters
   - When: compose_weekly_post() is called
   - Then: Post content is ≤3000 characters

7. `test_compose_weekly_post_raises_on_empty_summaries()`
   - Given: Empty summaries list
   - When: compose_weekly_post() is called
   - Then: Raises ComposerError

8. `test_compose_weekly_post_raises_on_too_few_articles()`
   - Given: Only 1-2 article summaries
   - When: compose_weekly_post() is called
   - Then: Raises ComposerError with descriptive message

9. `test_generate_headline_includes_week_and_count()`
   - Given: article_count=5, week_key="2025.W45"
   - When: generate_headline() is called
   - Then: Returns engaging headline with week reference

10. `test_format_article_highlight_creates_readable_format()`
    - Given: Valid summary dict and index=1
    - When: format_article_highlight() is called
    - Then: Returns formatted string with emoji, title, and source

11. `test_select_hashtags_returns_relevant_tags()`
    - Given: List of tech/AI article summaries
    - When: select_hashtags() is called
    - Then: Returns 5-8 relevant hashtags

12. `test_select_hashtags_avoids_duplicates()`
    - Given: Summaries from similar topics
    - When: select_hashtags() is called
    - Then: Returns unique hashtags only

13. `test_get_current_week_key_returns_iso_format()`
    - Given: Current date
    - When: get_current_week_key() is called
    - Then: Returns string in "YYYY.Www" format

14. `test_truncate_to_limit_preserves_structure()`
    - Given: Content exceeding 3000 characters
    - When: truncate_to_limit() is called
    - Then: Truncates at word boundary, preserves readability

15. `test_validate_summaries_accepts_valid_list()`
    - Given: Valid summaries list with 4 articles
    - When: validate_summaries() is called
    - Then: No exception raised

16. `test_validate_summaries_rejects_invalid_format()`
    - Given: Summaries with missing required fields
    - When: validate_summaries() is called
    - Then: Raises ComposerError

17. `test_compose_includes_unique_sources()`
    - Given: Summaries from 3 different sources
    - When: compose_weekly_post() is called
    - Then: Output includes all unique source names

18. `test_compose_adds_call_to_action()`
    - Given: Valid summaries
    - When: compose_weekly_post() is called
    - Then: Post content includes engagement CTA

## Dependencies

No new dependencies required! Uses only Python standard library:
- `datetime` - Week key generation and timestamps
- `re` - Text processing and validation

## Post Template Structure

```
🚀 Tech & AI Weekly Digest — Week {week_num}, {year}

This week's top stories in technology and artificial intelligence:

1️⃣ {Article 1 Summary}
   🔗 Source: {source1}

2️⃣ {Article 2 Summary}
   🔗 Source: {source2}

3️⃣ {Article 3 Summary}
   🔗 Source: {source3}

... (up to 6 articles)

💡 What caught your attention this week? Drop a comment below!

#{hashtag1} #{hashtag2} #{hashtag3} #{hashtag4} #{hashtag5}
```

## Default Hashtags

Core hashtags (always included):
- `#TechNews`
- `#ArtificialIntelligence`
- `#TechWeekly`

Contextual hashtags (selected based on content):
- `#MachineLearning`
- `#CloudComputing`
- `#Cybersecurity`
- `#DevOps`
- `#SoftwareEngineering`
- `#DataScience`
- `#OpenSource`
- `#Blockchain`
- `#QuantumComputing`
- `#EdgeComputing`

## Success Metrics

- All 18 test cases pass
- Code coverage ≥ 90% for composer.py
- Generated posts always ≤3000 characters
- Readable, professional LinkedIn formatting
- Proper emoji usage for visual appeal
- Unique hashtags selected per post

## Integration with Slice 02

The composer will consume output from the summarizer:

```python
from src.core.fetcher import fetch_news
from src.core.summarizer import summarize_article
from src.core.composer import compose_weekly_post

# Fetch articles (Slice 01)
articles = fetch_news([
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml",
    "https://www.wired.com/feed/rss"
])

# Summarize articles (Slice 02)
summaries = []
for article in articles[:6]:
    try:
        summary = summarize_article(article)
        summaries.append(summary)
    except Exception as e:
        print(f"Failed to summarize: {e}")

# Compose LinkedIn post (Slice 03)
try:
    post = compose_weekly_post(summaries)
    print(post["content"])
    print(f"\nCharacters: {post['character_count']}/3000")
except ComposerError as e:
    print(f"Failed to compose post: {e}")
```

## Out of Scope (Future Slices)

- Database persistence of composed posts
- A/B testing different headline templates
- Multi-language support
- Image/media attachment suggestions
- Sentiment analysis for content curation
- Scheduling and publishing (Slice 04 & 05)
- User feedback integration
- Performance metrics tracking

## Definition of Done

- ✅ All tests pass locally and in CI
- ✅ Coverage report shows ≥ 90% for composer.py
- ✅ Code follows PEP 8 and passes ruff/black
- ✅ Structured logging implemented
- ✅ Manual testing with real summaries from Slice 02
- ✅ Character limit enforcement verified
- ✅ Documentation strings complete
- ✅ BUILD_LOG.md updated
- ✅ Committed with conventional commit message

---

**Created:** 2025-11-10
**Author:** Giorgos Ampavis
**Status:** Completed
