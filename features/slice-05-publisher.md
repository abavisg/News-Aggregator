# Slice 05: LinkedIn Publisher with Local Logging and Dashboard

## Goal
Implement a LinkedIn publisher that handles OAuth authentication, post creation, retries, and idempotency. Additionally, add local post storage/logging and a web dashboard to preview generated posts before publishing.

## Acceptance Criteria

1. **Functional Requirements:**
   - Authenticate with LinkedIn using OAuth 2.0
   - Publish posts to LinkedIn with retry logic
   - Store all generated posts locally with timestamps
   - Prevent duplicate posts using week_key-based idempotency
   - Support dry-run mode (save locally without publishing)
   - Provide web dashboard to view generated posts
   - Display post history with status (draft, published, failed)
   - Allow manual approval and publishing from dashboard
   - Log all publishing attempts and outcomes
   - Handle rate limits and API errors gracefully

2. **Non-Functional Requirements:**
   - Test coverage: ≥ 90%
   - OAuth token refresh before expiry
   - Retry policy: 3 attempts with exponential backoff
   - Response time: < 3s for post creation
   - Logging: structured logs for all operations
   - Security: Never log access tokens or sensitive data
   - Idempotency: Publishing same week_key twice should fail gracefully

3. **Data Format:**
   ```python
   # Post record (stored locally)
   {
       "week_key": str,  # e.g., "2025.W45"
       "content": str,  # Full LinkedIn post text
       "status": str,  # "draft", "approved", "published", "failed"
       "created_at": datetime,
       "published_at": datetime | None,
       "linkedin_post_id": str | None,
       "linkedin_post_url": str | None,
       "error_message": str | None,
       "retry_count": int,
       "metadata": {
           "article_count": int,
           "char_count": int,
           "hashtag_count": int
       }
   }

   # OAuth credentials
   {
       "access_token": str,
       "refresh_token": str,
       "expires_at": datetime,
       "token_type": str,
       "scope": str
   }
   ```

## Technical Design

### Module: `src/core/publisher.py`

**Main Class:**
```python
class LinkedInPublisher:
    """
    Handles LinkedIn post publishing with OAuth, retries, and idempotency.
    """

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        posts_dir: str = "./data/posts",
        dry_run: bool = False
    ):
        """Initialize publisher with OAuth credentials"""

    def publish_post(
        self,
        week_key: str,
        content: str,
        metadata: dict | None = None
    ) -> dict:
        """
        Publish a post to LinkedIn.

        Returns:
            {
                "success": bool,
                "post_id": str | None,
                "post_url": str | None,
                "error": str | None
            }
        """

    def save_post_locally(
        self,
        week_key: str,
        content: str,
        status: str = "draft",
        metadata: dict | None = None
    ) -> str:
        """Save post to local storage and return file path"""

    def load_post(self, week_key: str) -> dict | None:
        """Load post from local storage"""

    def list_posts(
        self,
        status: str | None = None,
        limit: int = 50
    ) -> list[dict]:
        """List all stored posts with optional status filter"""

    def get_post_status(self, week_key: str) -> str | None:
        """Get status of a specific post"""

    def is_already_published(self, week_key: str) -> bool:
        """Check if post with week_key was already published"""

    def authenticate(self, auth_code: str) -> dict:
        """Exchange OAuth code for access token"""

    def refresh_access_token(self) -> dict:
        """Refresh expired access token"""

    def _create_linkedin_post(self, content: str) -> dict:
        """Internal method to create post via LinkedIn API"""

    def _retry_with_backoff(
        self,
        func: callable,
        max_retries: int = 3
    ) -> Any:
        """Retry function with exponential backoff"""
```

**Helper Functions:**
```python
def validate_oauth_credentials(
    client_id: str,
    client_secret: str
) -> bool:
    """Validate OAuth credentials are properly formatted"""

def generate_oauth_url(
    client_id: str,
    redirect_uri: str,
    state: str
) -> str:
    """Generate LinkedIn OAuth authorization URL"""

def parse_linkedin_error(response: dict) -> str:
    """Parse LinkedIn API error responses"""
```

### Module: `src/api/main.py`

**Dashboard Endpoints:**
```python
@app.get("/")
async def dashboard():
    """Serve HTML dashboard"""

@app.get("/v1/posts")
async def list_posts(
    status: str | None = None,
    limit: int = 50
):
    """List all posts with optional filtering"""

@app.get("/v1/posts/{week_key}")
async def get_post(week_key: str):
    """Get specific post by week_key"""

@app.post("/v1/posts/{week_key}/approve")
async def approve_post(week_key: str):
    """Approve draft post for publishing"""

@app.post("/v1/posts/{week_key}/publish")
async def publish_post(week_key: str):
    """Manually trigger post publishing"""

@app.get("/v1/oauth/login")
async def oauth_login():
    """Initiate OAuth flow"""

@app.get("/v1/oauth/callback")
async def oauth_callback(code: str, state: str):
    """Handle OAuth callback"""
```

### Module: `src/api/templates/dashboard.html`

**Simple Dashboard UI:**
- Display list of posts with status badges
- Show post content preview
- Approve/Publish buttons for each post
- Filter by status (all, draft, published, failed)
- Search by week key
- Display metadata (article count, char count, timestamps)

## Local Storage Structure

```
/data
  /posts
    2025.W45.json        # Individual post files
    2025.W46.json
    ...
  /credentials
    linkedin_oauth.json  # OAuth tokens (gitignored)
```

**Post File Format (JSON):**
```json
{
  "week_key": "2025.W45",
  "content": "🚀 Tech & AI Weekly Digest — Week 45, 2025\n\n...",
  "status": "published",
  "created_at": "2025-11-07T18:00:00Z",
  "approved_at": "2025-11-07T19:30:00Z",
  "published_at": "2025-11-08T10:00:00Z",
  "linkedin_post_id": "urn:li:share:1234567890",
  "linkedin_post_url": "https://www.linkedin.com/feed/update/urn:li:share:1234567890",
  "error_message": null,
  "retry_count": 0,
  "metadata": {
    "article_count": 5,
    "char_count": 2847,
    "hashtag_count": 7,
    "sources": ["techcrunch.com", "theverge.com"]
  }
}
```

## Environment Variables

```env
# LinkedIn OAuth (required for publishing)
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/v1/oauth/callback

# Publisher settings
POSTS_STORAGE_DIR=./data/posts
DRY_RUN=false  # Set to true to save locally without publishing
MAX_RETRIES=3
RETRY_BACKOFF_SECONDS=2
```

## LinkedIn API Integration

**Endpoints Used:**
- `POST /v2/ugcPosts` - Create a post
- `GET /v2/me` - Get current user profile
- `POST /oauth/v2/accessToken` - Exchange code for token
- `POST /oauth/v2/accessToken` - Refresh access token

**Required Scopes:**
- `w_member_social` - Post on behalf of user
- `r_liteprofile` - Read basic profile info

**Rate Limits:**
- 100 posts per day per user
- 1 post per minute per user

## Error Handling

**Error Categories:**
1. **Authentication Errors:**
   - Invalid/expired tokens → Trigger refresh
   - Missing credentials → Fail with clear message
   - OAuth flow errors → Log and return to login

2. **Publishing Errors:**
   - Rate limit exceeded → Retry with exponential backoff
   - Network errors → Retry up to 3 times
   - Invalid content → Log error and mark as failed
   - Duplicate post → Check idempotency, skip if already published

3. **Storage Errors:**
   - Disk full → Alert and fail gracefully
   - Permission errors → Log and raise
   - Corrupted files → Skip and log warning

## Testing Strategy

### Unit Tests (`src/tests/unit/test_publisher.py`)

Test coverage must include:
1. ✅ Publisher initialization with various configs
2. ✅ Local post saving and loading
3. ✅ Post listing with status filters
4. ✅ Idempotency checks
5. ✅ OAuth URL generation
6. ✅ Token refresh logic
7. ✅ Error parsing
8. ✅ Retry mechanism with backoff
9. ✅ Dry-run mode
10. ✅ Validation functions

**Mocking Strategy:**
- Mock `httpx` for LinkedIn API calls
- Mock file system operations for storage tests
- Use fixtures for OAuth credentials and responses

### Integration Tests

1. **End-to-End Workflow:**
   - Fetch → Summarize → Compose → Save Locally
   - Load from storage → Approve → Publish (mocked)

2. **Dashboard Workflow:**
   - Create drafts via API
   - List and filter posts
   - Approve and publish

### BDD Scenarios (`features/slice-05-publisher.feature`)

```gherkin
Feature: LinkedIn Post Publishing with Local Storage

  Scenario: Save post locally without publishing (dry-run mode)
    Given the publisher is in dry-run mode
    When I publish a post with week_key "2025.W45"
    Then the post should be saved to "./data/posts/2025.W45.json"
    And the post status should be "draft"
    And no LinkedIn API calls should be made

  Scenario: Prevent duplicate post publishing
    Given a post with week_key "2025.W45" is already published
    When I attempt to publish the same week_key again
    Then the publisher should return an error
    And the error message should contain "already published"

  Scenario: Publish post to LinkedIn with retry on failure
    Given valid LinkedIn OAuth credentials
    And a draft post with week_key "2025.W45"
    When the LinkedIn API fails with a network error
    Then the publisher should retry up to 3 times
    And use exponential backoff between retries

  Scenario: View posts in dashboard
    Given 5 posts exist with various statuses
    When I navigate to the dashboard at "/"
    Then I should see a list of all posts
    And each post should show its status, week_key, and creation date

  Scenario: Approve and publish post from dashboard
    Given a draft post with week_key "2025.W45" exists
    When I click the "Approve" button
    Then the post status should change to "approved"
    When I click the "Publish" button
    Then the post should be sent to LinkedIn
    And the status should change to "published"
```

## Dependencies

Add to `requirements.txt`:
```
httpx==0.27.0           # Already installed
fastapi==0.104.1        # Web framework
uvicorn==0.24.0         # ASGI server
jinja2==3.1.2           # Template rendering
python-multipart==0.0.6 # Form parsing
```

## Integration with Scheduler (Slice 04)

Update `src/core/scheduler.py` to use publisher:

```python
from src.core.publisher import LinkedInPublisher

class NewsAggregatorScheduler:
    def __init__(self, ...):
        self.publisher = LinkedInPublisher(
            dry_run=os.getenv("DRY_RUN", "false").lower() == "true"
        )

    def run_publish_job(self) -> dict:
        """Execute publish workflow"""
        week_key = self.get_week_key_for_date(datetime.now())

        # Execute pipeline
        result = self.execute_pipeline(week_key, is_preview=False)

        if result["success"]:
            # Publish to LinkedIn
            post_result = self.publisher.publish_post(
                week_key=week_key,
                content=result["post_content"],
                metadata=result.get("metadata", {})
            )
            result["published"] = post_result["success"]
            result["post_url"] = post_result.get("post_url")

        return result
```

## Success Metrics

1. **Functionality:**
   - ✅ Posts can be saved locally with all metadata
   - ✅ Dashboard displays posts correctly
   - ✅ OAuth flow works end-to-end
   - ✅ Publishing to LinkedIn succeeds (or fails gracefully)
   - ✅ Idempotency prevents duplicate posts
   - ✅ Retries work on transient failures

2. **Quality:**
   - ✅ Test coverage ≥ 90%
   - ✅ All BDD scenarios pass
   - ✅ No sensitive data in logs
   - ✅ Graceful error messages
   - ✅ Code follows project conventions

3. **Documentation:**
   - ✅ API endpoints documented in OpenAPI spec
   - ✅ BUILD_LOG.md updated
   - ✅ README.md updated with new features
   - ✅ Environment variables documented

## Future Enhancements (Out of Scope)

- Post scheduling UI (pick custom publish time)
- Analytics dashboard (views, likes, comments)
- A/B testing different post formats
- Multi-platform support (Twitter, Facebook)
- Image/media attachments
- Post editing after creation
- Bulk operations

---

**Implementation Order:**

1. Create `publisher.py` with local storage functions (TDD)
2. Add OAuth helpers and validation
3. Implement LinkedIn API integration with mocks
4. Add retry logic and error handling
5. Create FastAPI dashboard endpoints
6. Build simple HTML dashboard UI
7. Write comprehensive unit tests
8. Create BDD scenarios
9. Integrate with scheduler
10. Manual testing with real LinkedIn account (optional)
11. Update documentation

**Estimated Effort:** 6-8 hours (including tests and documentation)

**Blockers:** LinkedIn Developer account and OAuth app setup (can use dry-run mode without it)
