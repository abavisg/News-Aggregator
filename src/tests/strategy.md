# Testing Strategy - Weekly Tech & AI Aggregator

This document defines the comprehensive TDD/BDD/E2E approach for the Weekly Tech & AI Aggregator project.

**Last Updated:** 2025-11-10 (Amended to include BDD scenarios and Golden Path E2E tests)

---

## Principles

1. **Test-First Development (TDD)**
   - Write failing tests BEFORE implementation
   - Follow Red → Green → Refactor cycle
   - No production code without corresponding tests

2. **Behavior-Driven Development (BDD)**
   - Use Given/When/Then semantics in test docstrings and feature files
   - Focus on user outcomes, not implementation details
   - Tests should read like specifications
   - **NEW:** Gherkin feature files for slice acceptance criteria

3. **Test Isolation**
   - Each test is independent and can run in any order
   - Use mocks/stubs for external dependencies (network, AI, database)
   - Prefer in-memory SQLite for integration tests

4. **Golden Path E2E Testing (NEW)**
   - After each slice completion, run full pipeline E2E tests
   - Verify integration of all completed slices
   - Test the "happy path" from RSS feed to LinkedIn post
   - Ensure no regressions in previously completed slices

---

## Test Structure

### Test Pyramid

```
        /\         E2E Tests (Golden Path)
       /  \        - Full pipeline integration
      /    \       - Real external dependencies (mocked when necessary)
     / E2E  \      - Run after each slice completion
    /________\
    |        |     Integration Tests
    |  INT   |     - Multi-component integration
    |________|     - Mocked external dependencies
    |        |     BDD Scenarios
    |  BDD   |     - Behavioral acceptance tests
    |________|     - Gherkin feature files
    |        |     Unit Tests
    |  UNIT  |     - Fast, isolated functions
    |________|     - Complete coverage of edge cases
```

### Directory Layout
```
/src/tests
  /unit              # Fast, isolated tests for single functions
  /integration       # Multi-component tests with real dependencies
  /e2e               # End-to-end golden path tests (NEW)
  /fixtures          # Shared test data and factory functions
  conftest.py        # pytest fixtures and configuration

/features            # BDD feature files (NEW)
  /steps             # Step definitions for BDD scenarios
  slice-01-fetcher.feature
  slice-02-summarizer.feature
  slice-03-composer.feature
  golden-path.feature
  environment.py     # Behave hooks and setup
```

### Test Markers
Use pytest markers to categorize tests:
```python
@pytest.mark.unit         # Fast unit tests (< 1s each)
@pytest.mark.integration  # Integration tests (< 5s each)
@pytest.mark.e2e          # End-to-end tests (< 30s each)
@pytest.mark.bdd          # BDD scenario tests
@pytest.mark.slow         # Tests that take > 5s
@pytest.mark.golden       # Golden path critical tests
```

---

## Test Patterns

### Unit Test Example
```python
import pytest
from src.core.fetcher import fetch_news

@pytest.mark.unit
def test_fetch_news_returns_normalized_articles():
    """
    Given a list of valid RSS feed URLs
    When fetch_news is called
    Then it returns a list of normalized article dictionaries
    """
    # Arrange
    sources = ["https://techcrunch.com/feed/"]

    # Act
    articles = fetch_news(sources)

    # Assert
    assert len(articles) > 0
    assert "title" in articles[0]
    assert "link" in articles[0]
    assert "source" in articles[0]
    assert "date" in articles[0]


@pytest.mark.unit
def test_fetch_news_handles_invalid_url_gracefully():
    """
    Given an invalid RSS feed URL
    When fetch_news is called
    Then it returns an empty list without raising exceptions
    """
    # Arrange
    sources = ["https://invalid-domain-12345.com/feed/"]

    # Act
    articles = fetch_news(sources)

    # Assert
    assert articles == []
```

### Integration Test Example
```python
import pytest
from src.core.fetcher import fetch_news
from src.core.summarizer import summarize_articles
from src.core.composer import compose_linkedin_post

@pytest.mark.integration
def test_full_pipeline_generates_valid_post(temp_db):
    """
    Given fetched articles
    When the full pipeline runs (fetch → summarize → compose)
    Then a valid LinkedIn post is generated with correct structure
    """
    # Arrange
    sources = ["https://techcrunch.com/feed/"]

    # Act
    articles = fetch_news(sources)
    summaries = summarize_articles(articles[:5])
    post = compose_linkedin_post(summaries)

    # Assert
    assert len(post) > 0
    assert len(post) <= 3000  # LinkedIn character limit
    assert "#AI" in post or "#Tech" in post
```

### Mock Example
```python
import pytest
from unittest.mock import Mock, patch
from src.core.summarizer import summarize_article

@pytest.mark.unit
@patch('src.core.summarizer.anthropic.Client')
def test_summarizer_uses_claude_api(mock_client):
    """
    Given an article
    When summarize_article is called
    Then it calls Claude API with correct prompt
    """
    # Arrange
    mock_response = Mock()
    mock_response.content = [Mock(text="AI breakthrough announced")]
    mock_client.return_value.messages.create.return_value = mock_response

    article = {
        "title": "New AI Model Released",
        "link": "https://example.com/article",
        "content": "Long article content..."
    }

    # Act
    summary = summarize_article(article)

    # Assert
    assert summary == "AI breakthrough announced"
    mock_client.return_value.messages.create.assert_called_once()
```

---

## Test Coverage Goals

| Module | Target | Priority |
|--------|--------|----------|
| `core/fetcher.py` | ≥90% | Critical |
| `core/summarizer.py` | ≥85% | Critical |
| `core/composer.py` | ≥90% | Critical |
| `api/*` | ≥80% | High |
| `agents/*` | ≥70% | Medium |
| `scripts/*` | ≥60% | Medium |

Run coverage report:
```bash
pytest --cov=src --cov-report=html
```

---

## Fixture Strategy

### conftest.py Example
```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def temp_db():
    """Provides an in-memory SQLite database for tests"""
    engine = create_engine("sqlite:///:memory:")
    # Create tables
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture
def sample_articles():
    """Returns a list of sample article objects for testing"""
    return [
        {
            "title": "AI Model Breakthrough",
            "link": "https://example.com/ai-news",
            "source": "TechCrunch",
            "date": "2025-11-10"
        },
        {
            "title": "New Python Framework Released",
            "link": "https://example.com/python-news",
            "source": "The Verge",
            "date": "2025-11-09"
        }
    ]
```

---

## BDD with Behave (MANDATORY)

### Overview
All slices MUST have BDD feature files that define acceptance criteria using Gherkin syntax. These serve as:
- **Living documentation** of feature behavior
- **Acceptance tests** for stakeholder approval
- **Regression tests** to prevent breaking changes

### Feature File Structure

```gherkin
# features/slice-01-fetcher.feature
Feature: RSS Feed Fetcher
  As a news aggregator system
  I want to fetch and normalize articles from RSS feeds
  So that I can process consistent article data

  Scenario: Successfully fetch articles from multiple RSS feeds
    Given the following RSS feed URLs:
      | url                                    |
      | https://techcrunch.com/feed/           |
      | https://www.theverge.com/rss/index.xml |
    When I fetch news from these sources
    Then I should receive a list of articles
    And each article should have required fields:
      | field      |
      | title      |
      | link       |
      | source     |
      | date       |
      | content    |
    And the articles should be sorted by publication date

  Scenario: Handle invalid RSS feed gracefully
    Given an invalid RSS feed URL "https://invalid-domain.com/feed"
    When I attempt to fetch news from this source
    Then the system should not raise an exception
    And the result should be an empty list
    And an error should be logged

  Scenario: Parse various date formats
    Given articles with different date formats:
      | format           | example                    |
      | RFC 822          | Mon, 10 Nov 2025 14:30:00  |
      | ISO 8601         | 2025-11-10T14:30:00Z       |
      | Custom           | November 10, 2025          |
    When I normalize these articles
    Then all dates should be converted to datetime objects
    And dates should be timezone-aware
```

### Running BDD Tests

```bash
# Run all BDD scenarios
behave

# Run specific feature
behave features/slice-01-fetcher.feature

# Run specific scenario by name
behave -n "Successfully fetch articles"

# Run with specific tags
behave --tags=@slice01 --tags=@critical
```

---

## Golden Path E2E Testing (CRITICAL)

### Purpose
After each slice is completed and merged, **MANDATORY** E2E tests verify that:
1. The new slice integrates correctly with previous slices
2. The full pipeline works end-to-end
3. No regressions were introduced
4. The "golden path" (happy flow) produces expected results

### E2E Test Structure

```python
# src/tests/e2e/test_golden_path.py
import pytest
from datetime import datetime
from src.core.fetcher import fetch_news
from src.core.summarizer import summarize_article
from src.core.composer import compose_weekly_post

@pytest.mark.e2e
@pytest.mark.golden
class TestGoldenPathAfterSlice01:
    """E2E tests after Slice 01 (Fetcher) completion"""

    def test_fetch_returns_valid_articles(self):
        """
        Golden Path: Fetch articles from real RSS feeds

        Given: Valid RSS feed URLs
        When: fetch_news is called
        Then: Articles are returned with all required fields
        """
        sources = [
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml"
        ]

        articles = fetch_news(sources)

        assert len(articles) > 0, "Should fetch at least one article"
        assert all('title' in a for a in articles), "All articles must have titles"
        assert all('link' in a for a in articles), "All articles must have links"
        assert all('source' in a for a in articles), "All articles must have sources"


@pytest.mark.e2e
@pytest.mark.golden
class TestGoldenPathAfterSlice02:
    """E2E tests after Slice 02 (Summarizer) completion"""

    def test_fetch_and_summarize_pipeline(self, mock_claude_api):
        """
        Golden Path: Fetch → Summarize

        Given: Fetched articles from RSS feeds
        When: Articles are passed to summarizer
        Then: Summaries are generated successfully
        """
        # Fetch real articles
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)
        assert len(articles) > 0

        # Summarize first article
        summary = summarize_article(articles[0])

        assert summary is not None
        assert len(summary) > 0
        assert len(summary) <= 500  # Reasonable summary length


@pytest.mark.e2e
@pytest.mark.golden
class TestGoldenPathAfterSlice03:
    """E2E tests after Slice 03 (Composer) completion"""

    def test_full_pipeline_fetch_summarize_compose(self, mock_claude_api):
        """
        Golden Path: Fetch → Summarize → Compose

        Given: RSS feed sources
        When: Full pipeline executes
        Then: A valid LinkedIn post is generated
        """
        # Step 1: Fetch articles
        sources = ["https://techcrunch.com/feed/"]
        articles = fetch_news(sources)
        assert len(articles) >= 3, "Need at least 3 articles"

        # Step 2: Summarize articles
        summaries = []
        for article in articles[:5]:
            summary = summarize_article(article)
            summaries.append({
                'article_url': article['link'],
                'summary': summary,
                'source': article['source'],
                'published_at': article['date'],
                'tokens_used': 150,
                'provider': 'claude'
            })

        # Step 3: Compose LinkedIn post
        post = compose_weekly_post(summaries)

        # Assertions
        assert post['content'] is not None
        assert len(post['content']) > 0
        assert post['character_count'] <= 3000
        assert post['article_count'] >= 3
        assert post['article_count'] <= 6
        assert len(post['hashtags']) >= 5
        assert len(post['hashtags']) <= 8
        assert post['week_key'] is not None
```

### When to Run E2E Tests

1. **After Each Slice Merge**: Immediately run all applicable golden path tests
2. **Before Creating PR**: Run all E2E tests to ensure no regressions
3. **Nightly Builds**: Run full E2E suite including external dependencies
4. **Pre-Production**: Run complete E2E suite before deployment

### E2E Test Execution

```bash
# Run only E2E tests
pytest -m e2e

# Run only golden path tests
pytest -m golden

# Run E2E tests after Slice 03
pytest -m "e2e and golden" src/tests/e2e/test_golden_path.py::TestGoldenPathAfterSlice03

# Run with verbose output
pytest -m e2e -v -s

# Run E2E with coverage
pytest -m e2e --cov=src --cov-report=html
```

### E2E Test Data Strategy

- **Use Real External Dependencies** (when practical):
  - Real RSS feeds (with rate limiting)
  - Mocked AI API calls (to avoid costs)
  - Real date/time processing

- **Fixture-based Test Data**:
  - Known-good article samples for reproducibility
  - Snapshot testing for complex outputs
  - Golden files for expected results

---

## CI/CD Integration

Tests run automatically on:
- Every push to feature branches (Unit + Integration)
- Pull request creation (Unit + Integration + BDD)
- After PR merge to main (Unit + Integration + BDD + E2E)
- Scheduled nightly runs (Full suite including slow E2E)

GitHub Actions workflow:
```yaml
# Unit and Integration tests on every push
- name: Fast tests
  run: |
    pytest -m "unit or integration" --cov=src --cov-report=xml

# BDD tests on PRs
- name: BDD scenarios
  run: |
    behave --tags=~@wip

# E2E Golden Path after merge
- name: E2E Golden Path
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  run: |
    pytest -m "e2e and golden" -v

# Full suite nightly
- name: Full test suite
  if: github.event_name == 'schedule'
  run: |
    pytest --cov=src
    behave
```

---

## Anti-Patterns to Avoid

1. **Don't test implementation details** - test behaviors and outcomes
2. **Don't share state between tests** - use fixtures for setup
3. **Don't skip failing tests** - fix or remove them
4. **Don't write tests after code** - always test-first
5. **Don't mock everything** - balance unit and integration tests

---

## Definition of Done (Testing)

A feature/slice is complete when:
- ✅ All new code has corresponding unit tests (≥80% coverage)
- ✅ BDD feature file created with acceptance scenarios
- ✅ All BDD scenarios pass (green)
- ✅ Golden path E2E test updated and passing
- ✅ All tests pass locally and in CI
- ✅ Coverage meets target for module
- ✅ No regressions in existing tests
- ✅ Tests follow naming and structure conventions
- ✅ Integration with previous slices verified

---

## Summary: Test Execution After Each Slice

After completing a slice, run tests in this order:

```bash
# 1. Unit tests (fast feedback)
pytest -m unit -v

# 2. Integration tests
pytest -m integration -v

# 3. BDD scenarios for the new slice
behave features/slice-0X-*.feature

# 4. Golden path E2E tests
pytest -m "e2e and golden" -v

# 5. Full test suite with coverage
pytest --cov=src --cov-report=html --cov-report=term

# 6. All BDD scenarios
behave

# 7. Review coverage report
open htmlcov/index.html
```

**Expected Results:**
- ✅ All tests passing
- ✅ Coverage ≥ 80% for new code
- ✅ No regressions in previous slices
- ✅ BDD scenarios all green
- ✅ Golden path E2E test passing

---

**Last Updated:** 2025-11-10 (Amended with BDD and E2E Golden Path strategy)
**Maintained by:** Giorgos Ampavis
