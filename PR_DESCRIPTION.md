# LinkedIn Publisher with Dashboard (Slice 05)

Implements automated LinkedIn publishing with a web dashboard for managing weekly tech digests.

## What's New

### 📱 LinkedIn Publisher
- OAuth 2.0 authentication with token refresh
- Automatic post publishing with retry logic
- Local storage for all posts (JSON files)
- Prevents duplicate posts (idempotency)
- Dry-run mode for testing

### 🎨 Web Dashboard
- View all posts with status filtering
- Approve and publish with one click
- Real-time statistics
- Mobile-responsive design
- Visit at http://localhost:8000

### 🔄 Scheduler Integration
- **Preview** (Thursday 18:00): Saves drafts locally
- **Publish** (Friday 10:00): Posts to LinkedIn automatically
- Full pipeline: fetch → summarize → compose → publish

### 🔒 Security
- Fixed all credential exposures in tests
- Added pre-commit hooks for secret detection
- Created SECURITY.md with best practices
- Added .env.example template

## Quick Start

```bash
# Configure environment
cp .env.example .env
# Edit .env with your LinkedIn credentials

# Start dashboard
uvicorn src.api.main:app --reload

# Test in dry-run mode
export DRY_RUN=true
python src/scripts/scheduler.py --preview
```

## Testing
- ✅ 83/83 tests passing
- ✅ 49 publisher tests
- ✅ 34 scheduler tests

## API Endpoints
- `GET /` - Dashboard
- `GET /v1/posts` - List posts
- `POST /v1/posts/{week_key}/approve` - Approve post
- `POST /v1/posts/{week_key}/publish` - Publish post
- `GET /v1/oauth/login` - LinkedIn login

## Files Changed
- **New**: publisher.py, main.py, dashboard.html, test_publisher.py, SECURITY.md, .env.example
- **Updated**: scheduler.py, BUILD_LOG.md, README.md, .gitignore

---

**Ready to merge** • 4 commits • 4,386+ insertions
