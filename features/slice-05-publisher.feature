Feature: LinkedIn Post Publishing with Local Storage and Dashboard

  As a content creator
  I want to publish weekly tech digests to LinkedIn
  So that I can share curated content automatically

  Background:
    Given the LinkedIn publisher is initialized
    And the local storage directory exists

  Scenario: Save post locally without publishing (dry-run mode)
    Given the publisher is in dry-run mode
    When I publish a post with week_key "2025.W45" and content:
      """
      🚀 Tech & AI Weekly Digest — Week 45, 2025

      This week's top stories in technology and artificial intelligence:

      1️⃣ OpenAI releases GPT-5
         🔗 Source: techcrunch.com

      #TechNews #AI
      """
    Then the post should be saved to local storage
    And the post status should be "draft"
    And no LinkedIn API calls should be made
    And the local file "2025.W45.json" should exist

  Scenario: Prevent duplicate post publishing
    Given a post with week_key "2025.W45" exists with status "published"
    When I attempt to publish the same post again
    Then the publish should fail
    And the error message should contain "already published"
    And no LinkedIn API calls should be made

  Scenario: Publish post to LinkedIn successfully
    Given valid LinkedIn OAuth credentials are configured
    And a draft post with week_key "2025.W45" exists
    And the LinkedIn API is available
    When I publish the post
    Then the post should be sent to LinkedIn API
    And the API response should contain a post ID
    And the local post status should be updated to "published"
    And the post metadata should include the LinkedIn post URL

  Scenario: Retry publishing on network errors
    Given valid LinkedIn OAuth credentials are configured
    And a draft post with week_key "2025.W46" exists
    And the LinkedIn API fails with network errors 2 times
    And the LinkedIn API succeeds on the 3rd attempt
    When I publish the post
    Then the publisher should retry 3 times total
    And exponential backoff should be used between retries
    And the post should eventually be published successfully

  Scenario: Handle API errors gracefully
    Given valid LinkedIn OAuth credentials are configured
    And a draft post with week_key "2025.W47" exists
    And the LinkedIn API returns error 429 "Rate limit exceeded"
    When I publish the post after maximum retries
    Then the post status should be "failed"
    And the error message should be saved locally
    And the retry count should be recorded

  Scenario: List all posts with filtering
    Given the following posts exist in local storage:
      | week_key  | status    | created_at          |
      | 2025.W45  | published | 2025-11-01T10:00:00Z |
      | 2025.W46  | draft     | 2025-11-08T18:00:00Z |
      | 2025.W47  | failed    | 2025-11-15T10:00:00Z |
      | 2025.W48  | approved  | 2025-11-22T18:00:00Z |
    When I list all posts
    Then I should see 4 posts
    And the posts should be sorted by created_at descending

  Scenario: Filter posts by status
    Given the following posts exist in local storage:
      | week_key  | status    |
      | 2025.W45  | published |
      | 2025.W46  | draft     |
      | 2025.W47  | draft     |
      | 2025.W48  | published |
    When I list posts with status filter "draft"
    Then I should see 2 posts
    And all posts should have status "draft"

  Scenario: Approve a draft post
    Given a draft post with week_key "2025.W45" exists
    When I approve the post
    Then the post status should change to "approved"
    And the approved_at timestamp should be set
    And the post should remain in local storage

  Scenario: Cannot approve already published post
    Given a post with week_key "2025.W45" exists with status "published"
    When I attempt to approve the post
    Then the approval should fail
    And the post status should remain "published"

  Scenario: Generate OAuth authorization URL
    Given LinkedIn OAuth credentials are configured
    When I generate an OAuth URL with state "test_state_123"
    Then the URL should contain "linkedin.com/oauth/v2/authorization"
    And the URL should contain the client_id
    And the URL should contain "redirect_uri"
    And the URL should contain "scope=w_member_social+r_liteprofile"
    And the URL should contain "state=test_state_123"

  Scenario: Exchange authorization code for access token
    Given LinkedIn OAuth credentials are configured
    And I have an authorization code "auth_code_123456"
    And the LinkedIn token endpoint is available
    When I authenticate with the authorization code
    Then I should receive an access token
    And the access token should be saved to local credentials file
    And the credentials should include a refresh token

  Scenario: Refresh expired access token
    Given LinkedIn OAuth credentials are configured
    And an expired access token exists in local storage
    And a valid refresh token exists
    And the LinkedIn token refresh endpoint is available
    When I refresh the access token
    Then I should receive a new access token
    And the new token should replace the old one in local storage
    And the expiry time should be updated

  Scenario: View dashboard with posts
    Given the API server is running
    And the following posts exist:
      | week_key  | status    | content          |
      | 2025.W45  | published | Tech news week 45 |
      | 2025.W46  | draft     | Tech news week 46 |
    When I navigate to the dashboard at "/"
    Then I should see an HTML page
    And the page should display 2 posts
    And each post should show its week_key, status, and preview

  Scenario: Approve post via dashboard API
    Given the API server is running
    And a draft post with week_key "2025.W45" exists
    When I POST to "/v1/posts/2025.W45/approve"
    Then the response status should be 200
    And the response should contain success message
    And the post status should be updated to "approved"

  Scenario: Publish post via dashboard API
    Given the API server is running
    And an approved post with week_key "2025.W45" exists
    And valid LinkedIn credentials are configured
    And the LinkedIn API is available
    When I POST to "/v1/posts/2025.W45/publish"
    Then the response status should be 200
    And the post should be published to LinkedIn
    And the response should contain the LinkedIn post URL

  Scenario: Get specific post via API
    Given the API server is running
    And a post with week_key "2025.W45" exists
    When I GET "/v1/posts/2025.W45"
    Then the response status should be 200
    And the response should contain the post data
    And the response should include all metadata

  Scenario: List posts via API with pagination
    Given the API server is running
    And 100 posts exist in local storage
    When I GET "/v1/posts?limit=20"
    Then the response status should be 200
    And I should receive exactly 20 posts
    And the posts should be sorted by created_at descending

  Scenario: Handle missing OAuth credentials gracefully
    Given LinkedIn OAuth credentials are NOT configured
    And a draft post with week_key "2025.W45" exists
    When I attempt to publish the post
    Then the publish should fail
    And the error should indicate missing credentials
    And the post should remain in draft status

  Scenario: Save post metadata with article count and sources
    Given the publisher is in dry-run mode
    When I publish a post with metadata:
      | field         | value                          |
      | article_count | 5                              |
      | char_count    | 2847                           |
      | hashtag_count | 7                              |
      | sources       | techcrunch.com,theverge.com    |
    Then the post should be saved with all metadata
    And the metadata should be retrievable when loading the post

  Scenario: Idempotency check before publishing
    Given a post with week_key "2025.W45" exists with status "published"
    And the post has a LinkedIn post ID
    When the scheduler attempts to publish the same week_key
    Then the publish should be skipped
    And a warning should be logged
    And no duplicate post should be created on LinkedIn

  Scenario: Handle storage errors during save
    Given the local storage directory is read-only
    When I attempt to save a post with week_key "2025.W45"
    Then a StorageError should be raised
    And the error message should indicate permission issues

  Scenario: Load corrupted post file
    Given a corrupted post file exists for week_key "2025.W45"
    When I attempt to load the post
    Then a StorageError should be raised
    And the error should indicate JSON parsing failure

  Scenario: List posts skips corrupted files
    Given the following posts exist:
      | week_key  | status    | valid |
      | 2025.W45  | published | true  |
      | 2025.W46  | draft     | false |
      | 2025.W47  | draft     | true  |
    When I list all posts
    Then I should see 2 posts
    And corrupted files should be skipped with a warning

  Scenario: OAuth callback handling
    Given the API server is running
    And LinkedIn OAuth credentials are configured
    When I GET "/v1/oauth/callback?code=auth123&state=test_state"
    Then the response should redirect or return success
    And the authorization code should be exchanged for tokens
    And the tokens should be saved to local storage

  Scenario: Post content with special characters
    Given the publisher is in dry-run mode
    When I save a post with special characters:
      """
      Test émojis 🚀✨💡
      Quotes: "test" and 'test'
      Newlines and tabs
      """
    Then the post should be saved correctly
    And the content should be preserved exactly as provided
    When I load the post
    Then the content should match the original

  Scenario: Concurrent post saves
    Given the publisher is initialized
    When 5 posts are saved concurrently
    Then all 5 posts should be saved successfully
    And no data corruption should occur
    And each post should have unique content

  Scenario: Integration with scheduler
    Given the scheduler is configured with the publisher
    And a weekly job is scheduled
    When the publish job executes
    Then the pipeline should run (fetch → summarize → compose)
    And the generated post should be saved locally
    And the post should be published to LinkedIn if not in dry-run mode
    And the job result should include publish status

