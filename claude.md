
# 🤖 Claude Code Configuration for Weekly Tech & AI Aggregator

Defines how Claude Code should plan, implement, and test each slice for the **Weekly Tech & AI Aggregator** MVP.

---

## 🎯 Purpose

To ensure Claude Code works incrementally, safely, and consistently across all slices using **TDD** and **BDD** practices, while maintaining alignment with the unified specification (`/docs/unified-weekly-tech-ai-specification.md`).

The goal is to produce a fully automated, observable, and test-driven pipeline that fetches, summarizes, and publishes weekly Tech & AI news to LinkedIn every Friday at 10:00 (Europe/London).

---

## 🧩 Workflow (per slice)

1. **Start in Plan Mode**
   - Read relevant specs and slice definition.  
   - Summarize what will be built.  
   - List Python files, functions, and tests to create.  
   - Wait for explicit confirmation before coding.

2. **On approval, switch to Build Mode**
   - Write **failing tests first** (TDD).  
   - Implement only minimal logic to pass.  
   - Refactor for clarity and performance once green.

3. **After all tests pass**
   - Update `docs/BUILD_LOG.md` with summary and commit message.  
   - Update user-facing docs (`README.md`) only if the slice adds visible capability (e.g., API endpoint, CLI script, config flag).  

---

## 🧭 Context Setup

Before any slice begins, Claude Code must load the following:

1. `/claude.md` → global workflow and engineering rules  
2. `/features/<active_slice>.md` → current feature spec  
3. `/docs/unified-weekly-tech-ai-specification.md` → technical foundation and acceptance criteria  
4. `/tests/strategy.md` → shared TDD/BDD test structure and examples  

**Purpose:**  
To ensure each slice follows the same architectural, testing, and operational patterns defined in the unified spec.

**Session Start Command (for Giorgos to paste in Claude Code):**
```
Read claude.md, features/<active_slice>.md,
docs/unified-weekly-tech-ai-specification.md, and tests/strategy.md.
Summarise the slice goal, dependencies, and required test coverage.
List planned Python modules, functions, and test names.
Do not write code yet — stay in Plan Mode until confirmation.
```

---

### 🧹 Context Reset Policy

After a slice is merged and all tests pass:

1. Update `docs/BUILD_LOG.md` with the summary and commit message.  
2. Commit changes with a conventional commit message (`feat: complete slice XX`).  
3. Reset Claude context to start clean for the next slice.  
4. Reload context using:
   ```
   Read claude.md, features/<next_slice>.md,
   docs/unified-weekly-tech-ai-specification.md, and tests/strategy.md.
   Summarise the slice goal and plan.
   Do not write code yet — stay in Plan Mode until confirmation.
   ```

---

## 🧪 Test-Driven Development Rules

- Always create **failing tests first**.  
- No implementation before red → green cycle.  
- Use **pytest** for structure; follow Given/When/Then semantics in docstrings.  
- Keep test naming explicit and intention-focused, not mechanical.

Example:
```python
def test_generate_weekly_post_compiles_top_articles_successfully():
    """Given fetched articles, when summarized and composed, then output is a valid LinkedIn post."""
```

---

## 🧠 Best Practices

| Rule | Description |
|------|--------------|
| **Ask before major changes** | Confirm schema, API, or design refactors. |
| **Follow TDD strictly** | No code before tests. |
| **Keep atomic PRs** | One slice or micro-feature per PR. |
| **Document success** | Update `docs/BUILD_LOG.md` after completion. |
| **Stay incremental** | Deliver small, tested progress only. |
| **Use lint & formatters** | Run `ruff`, `black`, and `pytest --maxfail=1`. |
| **Keep test isolation** | Use mocks or temp SQLite DB for isolation. |

---

## 🧾 Deliverables per Slice

Each slice must deliver:

- ✅ **Python Code** – minimal, functional, and tested.  
- ✅ **Tests** – green, intentional, covering core logic.  
- ✅ **README.md Update** – only if user-facing.  
- ✅ **Build Log Entry** – concise, timestamped, referencing slice ID.

Example Build Log Entry:
```
✅ Slice 03 – Summarizer complete
- Added LLM-based summarization (Claude API)
- Implemented fallback extractive summarizer
- Tests for token limits and length compliance
- Commit: feat: add summarizer with fallback logic
```

---

## ✅ Definition of Done

A slice is considered **complete** when:

1. All tests pass locally and in CI.  
2. Code follows unified spec conventions.  
3. Documentation updated (`README`, `BUILD_LOG`).  
4. Deployment script unaffected (if applicable).  
5. Next slice spec ready to load.

---

## 🚫 Do Not

- Skip **Plan Mode**.  
- Modify or mix multiple slices.  
- Push untested code.  
- Introduce new dependencies without approval.  
- Commit experimental AI prompts in production scripts.  

---

## 🧭 Author Notes

Created by **Giorgos Ampavis**  
Maintained for the **Weekly Tech & AI Aggregator** MVP (Claude Code + Python web stack).  
This file defines how Claude Code should think, plan, and build each slice safely and consistently using **TDD**, **BDD**, and **incremental delivery** principles.
