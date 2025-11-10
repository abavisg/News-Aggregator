# Slice 02: AI Summarizer

## Goal
Implement an AI-powered summarizer that generates concise summaries of tech/AI news articles using Claude API or Ollama (local LLM).

## Acceptance Criteria

1. **Functional Requirements:**
   - Summarize individual articles (1-3 sentences)
   - Support both Claude API and Ollama backends
   - Auto-detect provider from environment variables
   - Handle rate limits and API errors gracefully
   - Extract key insights from article titles and descriptions
   - Return structured summary with metadata

2. **Non-Functional Requirements:**
   - Response time: < 3 seconds per article (Claude API), < 5 seconds (Ollama)
   - Test coverage: ≥ 90%
   - Error handling: graceful degradation with fallback summaries
   - Logging: structured logs for all AI interactions
   - Cost-aware: track token usage for Claude API calls

3. **Data Format:**
   ```python
   # Input
   {
       "title": str,
       "link": str,
       "source": str,
       "date": str,
       "published_at": datetime
   }

   # Output
   {
       "article_url": str,
       "summary": str,           # 1-3 sentence summary
       "source": str,
       "published_at": datetime,
       "tokens_used": int,       # For cost tracking
       "provider": str           # "claude" or "ollama"
   }
   ```

## Technical Design

### Module: `src/core/summarizer.py`

**Main Function:**
```python
def summarize_article(article: dict, provider: str = None) -> dict:
    """
    Generate a concise summary of a news article using AI.

    Args:
        article: Normalized article dict from fetcher
        provider: Optional override ("claude" or "ollama").
                 Auto-detects from env if None.

    Returns:
        Dict with summary and metadata

    Raises:
        SummarizerError: If both providers fail
    """
```

**Helper Functions:**
```python
def summarize_with_claude(article: dict) -> dict:
    """Use Claude API for summarization"""

def summarize_with_ollama(article: dict) -> dict:
    """Use local Ollama for summarization"""

def detect_provider() -> str:
    """Auto-detect available AI provider from environment"""

def build_summary_prompt(title: str, description: str = "") -> str:
    """Build consistent prompt for summarization"""

def count_tokens(text: str) -> int:
    """Estimate token count for cost tracking"""
```

**Custom Exception:**
```python
class SummarizerError(Exception):
    """Raised when summarization fails on all providers"""
```

## Test Cases

### Unit Tests (`src/tests/unit/test_summarizer.py`)

1. `test_summarize_article_with_claude_success()`
   - Given: Valid article dict, Claude API key in env
   - When: summarize_article() is called
   - Then: Returns summary dict with "claude" provider

2. `test_summarize_article_with_ollama_success()`
   - Given: Valid article dict, Ollama running locally
   - When: summarize_article() is called with provider="ollama"
   - Then: Returns summary dict with "ollama" provider

3. `test_summarize_article_auto_detects_provider()`
   - Given: ANTHROPIC_API_KEY set in environment
   - When: summarize_article() called without provider arg
   - Then: Uses Claude API automatically

4. `test_detect_provider_prefers_claude_when_both_available()`
   - Given: Both Claude and Ollama configured
   - When: detect_provider() is called
   - Then: Returns "claude"

5. `test_detect_provider_falls_back_to_ollama()`
   - Given: No Claude API key, Ollama available
   - When: detect_provider() is called
   - Then: Returns "ollama"

6. `test_detect_provider_raises_when_no_provider()`
   - Given: No providers configured
   - When: detect_provider() is called
   - Then: Raises SummarizerError

7. `test_summarize_with_claude_handles_rate_limit()`
   - Given: Claude API returns 429 error
   - When: summarize_with_claude() is called
   - Then: Raises SummarizerError with descriptive message

8. `test_summarize_with_ollama_handles_connection_error()`
   - Given: Ollama service is unreachable
   - When: summarize_with_ollama() is called
   - Then: Raises SummarizerError

9. `test_build_summary_prompt_includes_title_and_description()`
   - Given: Article title and description
   - When: build_summary_prompt() is called
   - Then: Returns formatted prompt string

10. `test_count_tokens_estimates_correctly()`
    - Given: Sample text string
    - When: count_tokens() is called
    - Then: Returns reasonable token estimate

11. `test_summarize_article_includes_token_count()`
    - Given: Valid article
    - When: summarize_article() succeeds
    - Then: Result includes tokens_used field

12. `test_summarize_article_handles_missing_description()`
    - Given: Article with only title (no description/content)
    - When: summarize_article() is called
    - Then: Generates summary from title alone

## Dependencies

- `anthropic==0.40.0` - Claude API client
- `httpx==0.27.0` - HTTP client for Ollama
- `tiktoken==0.8.0` - Token counting (Claude-compatible)
- `python-dotenv==1.0.0` - Environment variable management

## Environment Variables

```env
# Choose one or both providers
ANTHROPIC_API_KEY=sk-ant-...        # For Claude API
OLLAMA_BASE_URL=http://localhost:11434  # For local Ollama

# Model configuration
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Default model
OLLAMA_MODEL=llama3.2:latest            # Default Ollama model
```

## Prompt Template

```
You are a tech news summarizer. Summarize the following article in 1-3 concise sentences, focusing on:
- The main technical development or news
- Why it matters to the tech/AI community
- Key facts or metrics (if any)

Title: {title}
Description: {description}

Provide only the summary, no preamble or explanation.
```

## Success Metrics

- All 12 test cases pass
- Code coverage ≥ 90% for summarizer.py
- Successfully summarizes articles using both Claude and Ollama
- Average response time < 3s for Claude, < 5s for Ollama
- Token usage tracked for cost monitoring

## Integration with Slice 01

The summarizer will consume output from the fetcher:

```python
from src.core.fetcher import fetch_news
from src.core.summarizer import summarize_article

# Fetch articles
articles = fetch_news([
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml"
])

# Summarize each article
summaries = []
for article in articles[:5]:  # Summarize top 5
    try:
        summary = summarize_article(article)
        summaries.append(summary)
    except SummarizerError as e:
        print(f"Failed to summarize {article['link']}: {e}")
```

## Out of Scope (Future Slices)

- Batch summarization for performance
- Content extraction from full article URLs (beyond title/description)
- Multi-language support
- Summary quality scoring
- Caching of summaries
- Weekly digest composition (Slice 03)

## Definition of Done

- ✅ All tests pass locally and in CI
- ✅ Coverage report shows ≥ 90% for summarizer.py
- ✅ Code follows PEP 8 and passes ruff/black
- ✅ Structured logging implemented
- ✅ Both Claude and Ollama tested manually
- ✅ Documentation strings complete
- ✅ BUILD_LOG.md updated
- ✅ Committed with conventional commit message

---

**Created:** 2025-11-10
**Author:** Giorgos Ampavis
**Status:** In Progress
