# Weekly Tech & AI Aggregator

Automated weekly tech and AI news aggregator that fetches, summarizes, and publishes curated content to LinkedIn every Friday.

## Overview

This project automatically:
- Fetches tech/AI news from 10+ RSS feeds
- Summarizes articles using AI (Claude API or Ollama)
- Composes a LinkedIn-ready weekly digest
- Publishes every Friday at 10:00 (Europe/London)
- Discovers and evaluates new sources automatically

## Tech Stack

- **Backend:** Python 3.11+ with FastAPI
- **Scheduler:** APScheduler (weekly jobs)
- **Database:** SQLite (local) / PostgreSQL (production)
- **AI Integration:** Claude API or Ollama (local)
- **Testing:** pytest with TDD/BDD practices

## Project Structure

```
/src
  /core          # Core logic: fetchers, summarizers, ranking
  /api           # REST API (FastAPI endpoints)
  /agents        # AI or MCP integrations
  /tests         # Unit, integration, and BDD tests
  /scripts       # Scheduler and CLI entry points
/contracts       # OpenAPI specs, event schemas
/features        # Feature slice markdown specs
/docs            # PRD, architecture, metrics, BUILD_LOG
```

## Setup

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Virtual environment tool (venv or virtualenv)

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd News-Aggregator
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Environment Variables

Create a `.env` file with the following:

```env
# AI Provider (choose one)
ANTHROPIC_API_KEY=your_claude_api_key_here
OLLAMA_BASE_URL=http://localhost:11434  # For local Ollama

# LinkedIn OAuth
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/callback

# Database
DATABASE_URL=sqlite:///./news_aggregator.db

# Scheduler
TIMEZONE=Europe/London
PREVIEW_TIME=18:00  # Thursday preview
PUBLISH_TIME=10:00  # Friday publish
```

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run with coverage report:
```bash
pytest --cov=src --cov-report=html
```

Run specific test types:
```bash
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m bdd          # BDD tests only
```

### Code Quality

Format code:
```bash
black src/
```

Lint code:
```bash
ruff check src/
```

Type checking:
```bash
mypy src/
```

### Development Workflow

This project follows a strict TDD/BDD approach:

1. **Plan Mode:** Understand the feature slice requirements
2. **Write Tests:** Create failing tests first (Red)
3. **Implement:** Write minimal code to pass tests (Green)
4. **Refactor:** Improve code quality while keeping tests green
5. **Document:** Update BUILD_LOG.md with progress

See `/docs/BUILD_LOG.md` for detailed development history.

## Usage

### Manual Run (Development)

Fetch and preview news:
```bash
python src/scripts/run_summary.py --preview
```

Generate and publish post:
```bash
python src/scripts/run_summary.py --publish
```

### Scheduled Execution

Start the scheduler:
```bash
python src/scripts/scheduler.py
```

The scheduler will automatically:
- Generate preview on Thursday at 18:00
- Publish to LinkedIn on Friday at 10:00

### API Server

Start the FastAPI server:
```bash
uvicorn src.api.main:app --reload
```

Access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Preview & Publishing
- `GET /v1/preview/{week_key}` - Get draft post for specific week
- `POST /v1/approve/{week_key}` - Approve draft for publishing

### Source Management
- `GET /v1/sources/approved` - List approved RSS feeds
- `POST /v1/sources/candidates` - Submit new source candidate

### Metrics
- `GET /v1/metrics/weekly` - Get weekly performance metrics

## Testing Strategy

The project maintains ≥80% test coverage with:
- **Unit Tests:** Fast, isolated tests for individual functions
- **Integration Tests:** Multi-component tests with dependencies
- **BDD Tests:** User-focused scenario tests

See `/src/tests/strategy.md` for detailed testing guidelines.

## Documentation

- **Specification:** `SPECIFICATION.md.md` - Complete technical specification
- **Claude Config:** `claude.md` - Development workflow for Claude Code
- **Build Log:** `docs/BUILD_LOG.md` - Incremental delivery tracking
- **Test Strategy:** `src/tests/strategy.md` - TDD/BDD guidelines

## Deployment

### GitHub Actions (Recommended)

The project includes a GitHub Actions workflow for automated weekly runs:

```yaml
# Runs every Friday at 10:00 UTC
on:
  schedule:
    - cron: "0 10 * * FRI"
```

### Docker

Build and run with Docker:
```bash
docker build -t news-aggregator .
docker run -d --env-file .env news-aggregator
```

### Local Production

For always-on local execution:
```bash
# Using systemd or supervisor
python src/scripts/scheduler.py
```

## Development Roadmap

### Completed
- ✅ Phase 1: Project initialization and structure
- ✅ Slice 01: RSS feed fetcher with tests (90% coverage)
- ✅ Slice 02: AI summarizer (Claude/Ollama) (100% coverage)
- ✅ Slice 03: LinkedIn post composer (90% coverage)
- ✅ Slice 04: Scheduler with APScheduler (96% coverage)
- ✅ Slice 05: LinkedIn publisher with dashboard (comprehensive coverage)
- ✅ Slice 06: Observability - metrics, alerts, structured logging (37 tests, all passing)
- ✅ Slice 07: Source discovery agent (48 tests, 89% coverage)
- ✅ Slice 08: Integration testing & E2E pipeline (12 tests, 100% pass rate)

### Upcoming
- 📋 Future enhancements: E2E scheduler automation, performance testing, security hardening

See `docs/BUILD_LOG.md` for detailed progress.

## Contributing

This project follows incremental, test-driven development:

1. Read the specification and current slice definition
2. Write failing tests first (TDD)
3. Implement minimal functionality
4. Ensure all tests pass
5. Update documentation
6. Submit PR with single slice/feature

## License

[Add your license here]

## Author

**Giorgos Ampavis**

Built with Claude Code following TDD/BDD best practices.

---

**Last Updated:** 2025-11-11
**Current Status:** Slice 08 Complete - Integration Testing Implemented (12 comprehensive tests)
