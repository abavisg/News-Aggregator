
# Weekly Tech & AI Aggregator — Unified Specification (Claude Code + Python Implementation)

## 1. Overview

**Project Name:** Weekly Tech & AI Aggregator  
**Goal:** Automatically collect weekly tech and AI news, summarize highlights, and post them to LinkedIn every Friday at 10:00 (Europe/London).  
**Core Objectives:**  
- Fetch and normalize news from multiple feeds  
- Continuously evaluate and refresh the source list  
- Generate short summaries and a LinkedIn-style weekly digest  
- Auto-publish or submit for approval via scheduler  
- Maintain observability, test coverage, and compliance with TDD/BDD practices  

---

## 2. Architecture

### Tech Stack
| Layer | Technology | Purpose |
|-------|-------------|----------|
| **Backend** | Python (FastAPI) | API + worker services |
| **Scheduler** | APScheduler | Weekly jobs (Thu preview, Fri publish) |
| **Database** | SQLite (local), PostgreSQL (prod) | Persistent data store |
| **AI Integration** | Ollama (local) or Claude API | Summarization and classification |
| **Automation (optional)** | MCP or Agent triggers | Continuous discovery & maintenance |
| **Frontend** | React (planned) | Preview & approval UI |

### Repository Structure
```
/src
  /core          # Core logic: fetchers, summarizers, ranking
  /api           # REST API (FastAPI endpoints)
  /agents        # AI or MCP integrations
  /tests         # Unit, integration, and BDD tests
  /scripts       # Scheduler and CLI entry points
/contracts       # OpenAPI specs, event schemas
/features        # Feature slice markdown specs
/docs            # PRD, architecture, metrics, ADRs
```

---

## 3. Core Modules

### 3.1 Fetcher
Fetches RSS feeds or APIs and normalizes article data.

**Inputs:** list of URLs  
**Outputs:** normalized article objects `{title, link, source, date}`  

Example:
```python
import feedparser

def fetch_news(sources: list[str]) -> list[dict]:
    articles = []
    for url in sources:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            articles.append({
                "title": entry.title,
                "link": entry.link,
                "source": url,
                "date": entry.get("published", "")
            })
    return articles
```

### 3.2 Evaluator (Source Discovery Agent)
Continuously discovers new sources and scores them for inclusion.

**Key metrics:**
- `relevance_score`: % of posts matching tech/AI keywords  
- `overlap_score`: Jaccard similarity with approved feeds (<0.4)  
- `quality_score`: domain authority proxy  

Runs weekly, updates `/docs/source-candidates.md`.  
Manual approval default; auto-approval toggle via feature flag.

### 3.3 Summarizer
Uses Claude API or local LLM via Ollama.

Prompt template:
```
Summarize the following week’s Tech & AI news into a concise LinkedIn-style post
with 3 highlights, a headline, and a closing CTA.
```

### 3.4 Composer
Builds a LinkedIn-ready post from 3–6 summaries and hashtags, enforcing length limits.

### 3.5 Scheduler
Schedules jobs for:
- **Preview**: Thursday 18:00
- **Publish**: Friday 10:00  
(Uses APScheduler; timezone: Europe/London)

### 3.6 Publisher
Handles LinkedIn OAuth, post creation, retries, and idempotency (`week_key` based).

---

## 4. Source List (Canonical + Discovery)

Initial feeds (low overlap):
1. techcrunch.com  
2. theverge.com  
3. wired.com  
4. arstechnica.com  
5. venturebeat.com  
6. mittechnologyreview.com  
7. thenewstack.io  
8. semianalysis.com  
9. huggingface.co/blog  
10. openai.com/research

**Discovery inputs:** RSS directories, Techmeme, Hacker News, outbound links from current sources.  
**Lifecycle states:** candidate → approved → deprecated.  

---

## 5. Data Model

```sql
sources(id PK, domain, feed_url, status ENUM('candidate','approved','deprecated'),
  relevance_score, overlap_score, quality_score, last_seen TIMESTAMPTZ)

items(id PK, source_id FK, url UNIQUE, title, excerpt, published_at, content_hash)

weekly_selection(week_key CHAR(8), position INT, item_id FK, summary TEXT, included BOOLEAN)

posts(week_key CHAR(8) PK, content TEXT, status ENUM('draft','approved','published','failed'),
  posted_url, posted_at, error_code, error_message)

feature_flags(key PK, value JSONB, updated_by TEXT, updated_at TIMESTAMPTZ)
```

---

## 6. API Contracts

Minimal REST interface under `/v1`:

```
GET /v1/preview/{week_key}
POST /v1/approve/{week_key}
GET /v1/sources/approved
POST /v1/sources/candidates
GET /v1/metrics/weekly
```

OpenAPI spec stored at `/contracts/openapi.yaml`.  
Webhooks (optional): `/internal/webhooks/publish_result`.

---

## 7. Testing Strategy

### Unit Tests
- Independent per module (`fetcher`, `summarizer`, etc.)
- Mock external calls (network, AI)

Example:
```python
def test_fetch_news_returns_articles():
    articles = fetch_news(["https://techcrunch.com/feed/"])
    assert len(articles) > 0
    assert "title" in articles[0]
```

### Integration Tests
- Run full pipeline: fetch → summarize → compose → save post  
- Use deterministic feeds to avoid drift.

### BDD Example
```gherkin
Feature: Weekly summary generation
  Scenario: Valid news items are summarized and posted
    Given 5 valid tech articles
    When the summarizer runs
    Then a LinkedIn-ready post is generated
```

Coverage goal: ≥80% critical paths.

---

## 8. Slicing Plan (Incremental Delivery)

| Slice | Description | Output |
|-------|--------------|--------|
| 01 | Implement `fetch_news()` | Fetcher + tests |
| 02 | Add summarizer (Claude API) | Summary text + tests |
| 03 | Compose weekly summary | End-to-end function |
| 04 | Add scheduler | Weekly automation |
| 05 | Implement publisher | Post to LinkedIn |
| 06 | Observability (logs, metrics) | Dashboard |
| 07 | Source Discovery Agent | Auto-updating feed list |

Each slice = 1–2 functions, with tests and docs committed before merging.

---

## 9. Developer Workflow

**Claude Code Principles**
- Always update specs before code.
- One slice per PR.
- Prompt Claude Code to:
  - generate tests first,
  - propose OpenAPI updates,
  - create or update migration scripts.

**Example Prompts**
- “Generate tests for deduplication ensuring ≥95% precision.”
- “Propose OpenAPI spec for /preview and /approve endpoints.”
- “Draft SQL migration for tables in section 5.”

---

## 10. CI/CD and Deployment

**GitHub Actions**
```yaml
name: Weekly Tech Digest
on:
  schedule:
    - cron: "0 10 * * FRI"
jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest
      - run: python src/scripts/run_summary.py
```

**Local**
```bash
python src/scripts/run_summary.py
```

**Container**
```dockerfile
FROM python:3.11-slim
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "src/scripts/run_summary.py"]
```

---

## 11. Observability & Alerts

- **Metrics:** `feeds_fetched_total`, `posts_published_total`, `publish_failures_total`  
- **Alerts:** missed preview/publish deadlines, token expiry, ingestion failure rate >5%  
- **Logs:** JSON structured, include week_key, job_type, and error_code  

---

## 12. Success Criteria

- Post generated & published automatically each Friday  
- Source list auto-refreshes weekly  
- All tests pass in CI and local runs  
- No policy violations or failed posts  
- Engagement rate improves over time  

---

## 13. Glossary

- **TDD**: Test Driven Development  
- **BDD**: Behavior Driven Development  
- **MLP**: Minimal Lovable Product  
- **ADR**: Architecture Decision Record  
- **SLO**: Service Level Objective  
- **Week Key**: ISO format `YYYY.Www`
