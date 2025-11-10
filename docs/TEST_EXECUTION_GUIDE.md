# Test Execution Guide

This guide provides comprehensive instructions for running tests in the News Aggregator project, including unit tests, integration tests, BDD scenarios, and E2E golden path tests.

---

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html --cov-report=term

# Run specific test types
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "e2e and golden"  # Golden path E2E tests
pytest -m bdd               # BDD scenario tests

# Run tests for specific slice
pytest -m slice01           # Slice 01 tests
pytest -m slice02           # Slice 02 tests
pytest -m slice03           # Slice 03 tests
```

---

## Test Types and When to Run Them

### 1. Unit Tests (Fast Feedback Loop)

**Purpose**: Test individual functions in isolation with mocked dependencies.

**When to run**:
- During active development (continuously)
- Before committing code
- In CI on every push

**Command**:
```bash
pytest -m unit -v
```

**Expected Duration**: < 10 seconds for all unit tests

---

### 2. Integration Tests

**Purpose**: Test multiple components working together with some mocked external dependencies.

**When to run**:
- After implementing a feature
- Before creating a PR
- In CI on every push

**Command**:
```bash
pytest -m integration -v
```

**Expected Duration**: < 30 seconds

---

### 3. BDD Scenarios (Acceptance Tests)

**Purpose**: Verify that features meet acceptance criteria using Gherkin scenarios.

**When to run**:
- After completing a slice
- Before creating a PR
- In CI on PR creation

**Commands**:
```bash
# Run all BDD scenarios
behave

# Run specific feature
behave features/slice-01-fetcher.feature

# Run specific scenario by name
behave -n "Successfully fetch articles"

# Run scenarios with specific tags
behave --tags=@golden
behave --tags=@slice01
behave --tags=@critical

# Exclude work-in-progress scenarios
behave --tags=~@wip

# Show detailed output
behave -v
```

**Expected Duration**: 1-2 minutes for all scenarios

---

### 4. E2E Golden Path Tests (Critical Path Verification)

**Purpose**: Verify the complete pipeline works end-to-end after each slice completion.

**When to run**:
- **MANDATORY**: After merging each slice to main
- Before deploying to production
- In nightly CI builds

**Commands**:
```bash
# Run all golden path E2E tests
pytest -m "e2e and golden" -v

# Run E2E tests for specific slice
pytest -m "e2e and golden" src/tests/e2e/test_golden_path.py::TestGoldenPathAfterSlice03

# Run with detailed output and timing
pytest -m "e2e and golden" -v -s --durations=10
```

**Expected Duration**: 30-60 seconds

---

## Test Execution Workflow After Each Slice

After completing a slice, run tests in this specific order:

```bash
# 1. Unit tests (fast feedback)
echo "=== Running Unit Tests ==="
pytest -m unit -v

# 2. Integration tests
echo "=== Running Integration Tests ==="
pytest -m integration -v

# 3. BDD scenarios for the new slice
echo "=== Running BDD Scenarios ==="
behave features/slice-0X-*.feature

# 4. Golden path E2E tests
echo "=== Running Golden Path E2E Tests ==="
pytest -m "e2e and golden" -v

# 5. Full test suite with coverage
echo "=== Running Full Test Suite with Coverage ==="
pytest --cov=src --cov-report=html --cov-report=term-missing

# 6. All BDD scenarios (comprehensive)
echo "=== Running All BDD Scenarios ==="
behave

# 7. Review coverage report
echo "=== Opening Coverage Report ==="
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
# start htmlcov/index.html     # Windows
```

**Save this as a script:**
```bash
# Save to: scripts/test-after-slice.sh
chmod +x scripts/test-after-slice.sh
./scripts/test-after-slice.sh
```

---

## Test Categories by Marker

### Unit Tests
```bash
# All unit tests
pytest -m unit

# Unit tests for specific module
pytest src/tests/unit/test_fetcher.py
pytest src/tests/unit/test_summarizer.py
pytest src/tests/unit/test_composer.py
```

### Integration Tests
```bash
# All integration tests
pytest -m integration

# Run integration demo
python src/tests/integration_demo.py
```

### E2E Tests
```bash
# All E2E tests
pytest -m e2e

# Only golden path tests
pytest -m golden

# E2E tests excluding slow tests
pytest -m "e2e and not slow"
```

### Slice-Specific Tests
```bash
# Slice 01 (Fetcher)
pytest -m slice01

# Slice 02 (Summarizer)
pytest -m slice02

# Slice 03 (Composer)
pytest -m slice03
```

---

## Test Coverage

### Generate Coverage Report

```bash
# HTML report (most detailed)
pytest --cov=src --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=src --cov-report=term-missing

# XML report (for CI)
pytest --cov=src --cov-report=xml

# All formats
pytest --cov=src --cov-report=html --cov-report=term-missing --cov-report=xml
```

### Coverage Targets

| Module | Target | Current Status |
|--------|--------|----------------|
| src/core/fetcher.py | ≥90% | ✅ 90% |
| src/core/summarizer.py | ≥85% | ✅ 100% |
| src/core/composer.py | ≥90% | ✅ 90% |
| **Overall** | **≥80%** | **✅ 93%** |

---

## BDD Scenarios Guide

### Feature Files Location

```
features/
├── slice-01-fetcher.feature
├── slice-02-summarizer.feature
├── slice-03-composer.feature
├── golden-path.feature
├── environment.py
└── steps/
    ├── fetcher_steps.py
    ├── summarizer_steps.py
    ├── composer_steps.py
    └── golden_path_steps.py
```

### Running Specific Scenarios

```bash
# By feature file
behave features/slice-01-fetcher.feature

# By scenario name
behave -n "Successfully fetch articles from multiple RSS feeds"

# By tag
behave --tags=@golden
behave --tags=@critical
behave --tags=@slice01

# Exclude tags
behave --tags=~@wip  # Exclude work-in-progress
behave --tags=~@slow # Exclude slow tests

# Multiple tags (AND)
behave --tags=@golden --tags=@slice03

# Multiple tags (OR) - use comma
behave --tags=@slice01,@slice02
```

### BDD Output Formats

```bash
# Default output
behave

# Verbose output
behave -v

# Quiet output (only failures)
behave -q

# JSON output (for reporting)
behave --format=json --outfile=report.json

# Pretty formatter
behave --format=pretty

# Show skipped scenarios
behave --show-skipped
```

---

## Continuous Integration

### GitHub Actions Test Workflow

Tests run automatically on:
- **Every push** to feature branches: Unit + Integration
- **Pull request creation**: Unit + Integration + BDD
- **Merge to main**: Unit + Integration + BDD + E2E Golden Path
- **Nightly builds**: Full test suite including slow tests

### CI Test Commands

```yaml
# Fast tests (on every push)
- name: Fast tests
  run: pytest -m "unit or integration" --cov=src --cov-report=xml

# BDD tests (on PRs)
- name: BDD scenarios
  run: behave --tags=~@wip

# E2E Golden Path (after merge to main)
- name: E2E Golden Path
  run: pytest -m "e2e and golden" -v

# Full suite (nightly)
- name: Full test suite
  run: |
    pytest --cov=src --cov-report=xml
    behave
```

---

## Debugging Failed Tests

### Verbose Output

```bash
# Show print statements
pytest -v -s

# Show local variables on failure
pytest --showlocals

# Stop at first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show full traceback
pytest --tb=long
```

### Test-Specific Debugging

```bash
# Run single test
pytest src/tests/unit/test_fetcher.py::test_fetch_news_returns_normalized_articles

# Run single test class
pytest src/tests/e2e/test_golden_path.py::TestGoldenPathAfterSlice03

# Run with keyword matching
pytest -k "fetch_news"
pytest -k "golden_path"
```

### BDD Debugging

```bash
# Show scenario steps
behave -v

# Stop at first failure
behave --stop

# Show timing for each step
behave --format=pretty

# Capture stdout/stderr
behave --no-capture
```

---

## Performance Testing

### Measure Test Duration

```bash
# Show slowest 10 tests
pytest --durations=10

# Show all test durations
pytest --durations=0

# Profile with detailed timing
pytest --durations=0 -v
```

### Parallel Test Execution

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel
pytest -n auto          # Auto-detect CPU count
pytest -n 4             # Use 4 workers

# Only for unit tests (safe)
pytest -m unit -n auto
```

---

## Common Test Scenarios

### Before Creating a PR

```bash
# Full validation
pytest --cov=src --cov-report=term-missing
behave
```

### After Merging a Slice

```bash
# Run golden path tests for the new slice
pytest -m "e2e and golden" -v

# Verify no regressions
pytest -m "e2e" -v
```

### Before Deployment

```bash
# Full comprehensive test suite
pytest --cov=src --cov-report=html
behave
pytest -m slow  # Run slow tests too
```

### Quick Development Iteration

```bash
# Fast feedback loop
pytest -m unit -x  # Stop at first failure
```

---

## Troubleshooting

### Tests Not Found

```bash
# Check pytest discovers tests correctly
pytest --collect-only

# Verify Python path
echo $PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/News-Aggregator"
```

### Import Errors

```bash
# Ensure project root is in Python path
cd /path/to/News-Aggregator
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest
```

### BDD Steps Not Found

```bash
# Check step definitions are loaded
behave --dry-run

# Verify features directory structure
ls -R features/
```

### Fixture Not Found

```bash
# Check conftest.py is present
ls src/tests/conftest.py

# List available fixtures
pytest --fixtures
```

---

## Test Data and Mocking

### Mock External Dependencies

Tests use fixtures from `src/tests/conftest.py`:

- `mock_claude_api`: Mock Claude API responses
- `mock_ollama_api`: Mock Ollama local API
- `sample_article`: Sample article data
- `sample_summaries`: Sample summary data
- `mock_rss_feed`: Mock RSS feed responses

### Using Fixtures in Tests

```python
def test_summarize_with_mock(mock_claude_api, sample_article):
    """Test summarization with mocked API."""
    summary = summarize_article(sample_article)
    assert summary is not None
```

---

## Best Practices

1. **Run unit tests frequently** during development
2. **Run integration tests** before committing
3. **Run BDD scenarios** after completing a feature
4. **Run golden path E2E tests** after merging each slice
5. **Review coverage reports** to ensure ≥80% coverage
6. **Fix failing tests immediately** - don't accumulate technical debt
7. **Use markers** to run specific test subsets efficiently
8. **Keep tests fast** - slow tests won't be run frequently

---

## Test Results Interpretation

### Success Criteria

✅ All tests passing
✅ Coverage ≥ 80% for new code
✅ No regressions in previous slices
✅ All BDD scenarios green
✅ Golden path E2E tests passing

### When Tests Fail

1. Review the failure message and traceback
2. Run the specific failing test with `-v -s` for details
3. Use `--pdb` to drop into debugger
4. Check if mocks are correctly configured
5. Verify test data is appropriate
6. Ensure external dependencies are mocked
7. Fix the test or the code, never skip tests

---

**Last Updated**: 2025-11-10
**Maintained by**: Giorgos Ampavis
