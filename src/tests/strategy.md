# Testing Strategy - Weekly Tech & AI Aggregator

This document defines the TDD/BDD approach for the Weekly Tech & AI Aggregator project.

---

## Principles

1. **Test-First Development (TDD)**
   - Write failing tests BEFORE implementation
   - Follow Red → Green → Refactor cycle
   - No production code without corresponding tests

2. **Behavior-Driven Development (BDD)**
   - Use Given/When/Then semantics in test docstrings
   - Focus on user outcomes, not implementation details
   - Tests should read like specifications

3. **Test Isolation**
   - Each test is independent and can run in any order
   - Use mocks/stubs for external dependencies (network, AI, database)
   - Prefer in-memory SQLite for integration tests

---

## Test Structure

### Directory Layout
```
/src/tests
  /unit          # Fast, isolated tests for single functions
  /integration   # Multi-component tests with real dependencies
  /bdd           # Behavioral scenarios using behave (optional)
  /fixtures      # Shared test data and factory functions
  conftest.py    # pytest fixtures and configuration
```

### Test Markers
Use pytest markers to categorize tests:
```python
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.bdd
@pytest.mark.slow
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

## BDD with Behave (Optional)

For complex user scenarios:

```gherkin
# features/weekly_summary.feature
Feature: Weekly Tech Summary Generation

  Scenario: Generate weekly LinkedIn post from valid articles
    Given the system has fetched 15 tech articles from approved sources
    When the weekly summarization job runs on Thursday at 18:00
    Then a LinkedIn post draft is created
    And the draft contains 3-6 highlighted articles
    And the post length is under 3000 characters
    And the post includes relevant hashtags
```

---

## CI/CD Integration

Tests run automatically on:
- Every push to feature branches
- Pull request creation
- Scheduled weekly runs

GitHub Actions workflow:
```yaml
- name: Run tests
  run: |
    pytest --cov=src --cov-report=xml
    pytest --markers=integration
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

A feature is complete when:
- ✅ All new code has corresponding tests
- ✅ All tests pass locally and in CI
- ✅ Coverage meets target for module
- ✅ No regressions in existing tests
- ✅ Tests follow naming and structure conventions

---

**Last Updated:** 2025-11-10
**Maintained by:** Giorgos Ampavis
