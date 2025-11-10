"""
Unit tests for LinkedIn Publisher (Slice 05)

Test coverage:
- Publisher initialization
- Local post storage and retrieval
- Post listing and filtering
- Idempotency checks
- OAuth URL generation
- Token exchange and refresh
- LinkedIn API integration (mocked)
- Retry mechanism with backoff
- Error handling
- Dry-run mode
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import httpx
import pytest

from src.core.publisher import (
    LinkedInPublisher,
    OAuthError,
    PublishingError,
    StorageError,
    parse_linkedin_error,
    validate_oauth_credentials,
)


# Fixtures


@pytest.fixture
def temp_posts_dir(tmp_path):
    """Create temporary posts directory"""
    posts_dir = tmp_path / "posts"
    posts_dir.mkdir()
    return posts_dir


@pytest.fixture
def temp_credentials_dir(tmp_path):
    """Create temporary credentials directory"""
    creds_dir = tmp_path / "credentials"
    creds_dir.mkdir()
    return creds_dir


@pytest.fixture
def publisher(temp_posts_dir, temp_credentials_dir):
    """Create publisher instance with temp directories"""
    return LinkedInPublisher(
        client_id="test_client_id_1234567890",
        client_secret="test_client_secret_abcdefghij",
        redirect_uri="http://localhost:8000/callback",
        posts_dir=str(temp_posts_dir),
        credentials_dir=str(temp_credentials_dir),
        dry_run=False,
    )


@pytest.fixture
def dry_run_publisher(temp_posts_dir, temp_credentials_dir):
    """Create publisher in dry-run mode"""
    return LinkedInPublisher(
        client_id="test_client_id",
        client_secret="test_client_secret",
        posts_dir=str(temp_posts_dir),
        credentials_dir=str(temp_credentials_dir),
        dry_run=True,
    )


@pytest.fixture
def sample_post_content():
    """Sample LinkedIn post content"""
    return """🚀 Tech & AI Weekly Digest — Week 45, 2025

This week's top stories in technology and artificial intelligence:

1️⃣ OpenAI releases GPT-5 with breakthrough reasoning capabilities
   🔗 Source: techcrunch.com

2️⃣ Google announces quantum supremacy milestone
   🔗 Source: theverge.com

💡 What caught your attention this week? Drop a comment below!

#TechNews #ArtificialIntelligence #AI #TechWeekly
"""


@pytest.fixture
def sample_metadata():
    """Sample post metadata"""
    return {
        "article_count": 2,
        "char_count": 345,
        "hashtag_count": 4,
        "sources": ["techcrunch.com", "theverge.com"],
    }


@pytest.fixture
def mock_oauth_response():
    """Mock OAuth token response"""
    return {
        "access_token": "AQVdDPdL9pFKxMjE2MDEzNDg",
        "expires_in": 5184000,
        "refresh_token": "AQWxPqNjm8gF7Ys9hK",
        "token_type": "Bearer",
        "scope": "w_member_social r_liteprofile",
    }


@pytest.fixture
def mock_linkedin_post_response():
    """Mock LinkedIn post creation response"""
    return {
        "id": "urn:li:share:1234567890",
        "created": {"time": 1699459200000},
    }


# Test: Publisher Initialization


def test_publisher_initialization_with_explicit_params(temp_posts_dir, temp_credentials_dir):
    """Test publisher initializes with explicit parameters"""
    pub = LinkedInPublisher(
        client_id="test_client",
        client_secret="test_secret",
        redirect_uri="http://localhost:8000/callback",
        posts_dir=str(temp_posts_dir),
        credentials_dir=str(temp_credentials_dir),
        dry_run=True,
        max_retries=5,
    )

    assert pub.client_id == "test_client"
    assert pub.client_secret == "test_secret"
    assert pub.redirect_uri == "http://localhost:8000/callback"
    assert pub.dry_run is True
    assert pub.max_retries == 5
    assert pub.posts_dir.exists()
    assert pub.credentials_dir.exists()


def test_publisher_initialization_from_env(temp_posts_dir, temp_credentials_dir, monkeypatch):
    """Test publisher reads OAuth credentials from environment"""
    monkeypatch.setenv("LINKEDIN_CLIENT_ID", "env_client_id")
    monkeypatch.setenv("LINKEDIN_CLIENT_SECRET", "env_client_secret")
    monkeypatch.setenv("LINKEDIN_REDIRECT_URI", "http://example.com/callback")

    pub = LinkedInPublisher(
        posts_dir=str(temp_posts_dir),
        credentials_dir=str(temp_credentials_dir),
    )

    assert pub.client_id == "env_client_id"
    assert pub.client_secret == "env_client_secret"
    assert pub.redirect_uri == "http://example.com/callback"


def test_publisher_creates_directories_if_missing(tmp_path):
    """Test publisher creates storage directories if they don't exist"""
    posts_dir = tmp_path / "new_posts"
    creds_dir = tmp_path / "new_creds"

    pub = LinkedInPublisher(
        posts_dir=str(posts_dir),
        credentials_dir=str(creds_dir),
    )

    assert posts_dir.exists()
    assert creds_dir.exists()


# Test: Local Post Storage


def test_save_post_locally(publisher, sample_post_content, sample_metadata):
    """Test saving post to local storage"""
    week_key = "2025.W45"

    file_path = publisher.save_post_locally(
        week_key=week_key,
        content=sample_post_content,
        status="draft",
        metadata=sample_metadata,
    )

    assert file_path.endswith(f"{week_key}.json")
    assert Path(file_path).exists()

    # Verify file content
    with open(file_path, "r") as f:
        data = json.load(f)

    assert data["week_key"] == week_key
    assert data["content"] == sample_post_content
    assert data["status"] == "draft"
    assert data["metadata"] == sample_metadata
    assert "created_at" in data
    assert data["published_at"] is None


def test_save_post_preserves_existing_timestamps(publisher, sample_post_content):
    """Test updating post preserves original created_at timestamp"""
    week_key = "2025.W45"

    # Save initial post
    publisher.save_post_locally(week_key, sample_post_content, status="draft")

    # Load and check initial timestamp
    post1 = publisher.load_post(week_key)
    created_at_1 = post1["created_at"]

    # Update post
    time.sleep(0.1)
    publisher.save_post_locally(week_key, sample_post_content, status="approved")

    # Verify created_at unchanged, updated_at changed
    post2 = publisher.load_post(week_key)
    assert post2["created_at"] == created_at_1
    assert post2["status"] == "approved"
    assert post2["updated_at"] != created_at_1


def test_load_post_existing(publisher, sample_post_content):
    """Test loading existing post"""
    week_key = "2025.W45"

    publisher.save_post_locally(week_key, sample_post_content, status="draft")
    post = publisher.load_post(week_key)

    assert post is not None
    assert post["week_key"] == week_key
    assert post["content"] == sample_post_content
    assert post["status"] == "draft"


def test_load_post_nonexistent(publisher):
    """Test loading non-existent post returns None"""
    post = publisher.load_post("2025.W99")
    assert post is None


def test_load_post_corrupted_file(publisher, temp_posts_dir):
    """Test loading corrupted JSON file raises StorageError"""
    week_key = "2025.W45"
    file_path = temp_posts_dir / f"{week_key}.json"

    # Create corrupted file
    with open(file_path, "w") as f:
        f.write("invalid json {{{")

    with pytest.raises(StorageError, match="Failed to load post"):
        publisher.load_post(week_key)


# Test: Post Listing


def test_list_posts_empty(publisher):
    """Test listing posts when none exist"""
    posts = publisher.list_posts()
    assert posts == []


def test_list_posts_all(publisher, sample_post_content):
    """Test listing all posts"""
    # Create multiple posts
    publisher.save_post_locally("2025.W45", sample_post_content, status="draft")
    publisher.save_post_locally("2025.W46", sample_post_content, status="published")
    publisher.save_post_locally("2025.W47", sample_post_content, status="failed")

    posts = publisher.list_posts()

    assert len(posts) == 3
    assert {p["week_key"] for p in posts} == {"2025.W45", "2025.W46", "2025.W47"}


def test_list_posts_filter_by_status(publisher, sample_post_content):
    """Test filtering posts by status"""
    publisher.save_post_locally("2025.W45", sample_post_content, status="draft")
    publisher.save_post_locally("2025.W46", sample_post_content, status="published")
    publisher.save_post_locally("2025.W47", sample_post_content, status="draft")

    drafts = publisher.list_posts(status="draft")
    published = publisher.list_posts(status="published")

    assert len(drafts) == 2
    assert len(published) == 1
    assert all(p["status"] == "draft" for p in drafts)


def test_list_posts_sorted_by_created_at(publisher, sample_post_content):
    """Test posts are sorted by created_at (newest first)"""
    # Create posts with delays
    publisher.save_post_locally("2025.W45", sample_post_content, status="draft")
    time.sleep(0.1)
    publisher.save_post_locally("2025.W46", sample_post_content, status="draft")
    time.sleep(0.1)
    publisher.save_post_locally("2025.W47", sample_post_content, status="draft")

    posts = publisher.list_posts()

    assert posts[0]["week_key"] == "2025.W47"  # Newest
    assert posts[2]["week_key"] == "2025.W45"  # Oldest


def test_list_posts_limit(publisher, sample_post_content):
    """Test limiting number of posts returned"""
    # Create 5 posts
    for i in range(45, 50):
        publisher.save_post_locally(f"2025.W{i}", sample_post_content, status="draft")

    posts = publisher.list_posts(limit=3)

    assert len(posts) == 3


def test_list_posts_skips_corrupted_files(publisher, sample_post_content, temp_posts_dir):
    """Test listing posts skips corrupted files"""
    # Create valid post
    publisher.save_post_locally("2025.W45", sample_post_content, status="draft")

    # Create corrupted file
    with open(temp_posts_dir / "2025.W46.json", "w") as f:
        f.write("invalid json")

    posts = publisher.list_posts()

    assert len(posts) == 1
    assert posts[0]["week_key"] == "2025.W45"


# Test: Post Status


def test_get_post_status_existing(publisher, sample_post_content):
    """Test getting status of existing post"""
    week_key = "2025.W45"
    publisher.save_post_locally(week_key, sample_post_content, status="draft")

    status = publisher.get_post_status(week_key)
    assert status == "draft"


def test_get_post_status_nonexistent(publisher):
    """Test getting status of non-existent post"""
    status = publisher.get_post_status("2025.W99")
    assert status is None


def test_is_already_published_true(publisher, sample_post_content):
    """Test idempotency check for published post"""
    week_key = "2025.W45"
    publisher.save_post_locally(week_key, sample_post_content, status="published")

    assert publisher.is_already_published(week_key) is True


def test_is_already_published_false(publisher, sample_post_content):
    """Test idempotency check for draft post"""
    week_key = "2025.W45"
    publisher.save_post_locally(week_key, sample_post_content, status="draft")

    assert publisher.is_already_published(week_key) is False


def test_is_already_published_nonexistent(publisher):
    """Test idempotency check for non-existent post"""
    assert publisher.is_already_published("2025.W99") is False


# Test: Approve Post


def test_approve_post_success(publisher, sample_post_content):
    """Test approving a draft post"""
    week_key = "2025.W45"
    publisher.save_post_locally(week_key, sample_post_content, status="draft")

    result = publisher.approve_post(week_key)

    assert result is True

    post = publisher.load_post(week_key)
    assert post["status"] == "approved"
    assert post["approved_at"] is not None


def test_approve_post_nonexistent(publisher):
    """Test approving non-existent post fails"""
    result = publisher.approve_post("2025.W99")
    assert result is False


def test_approve_post_already_published(publisher, sample_post_content):
    """Test cannot approve already published post"""
    week_key = "2025.W45"
    publisher.save_post_locally(week_key, sample_post_content, status="published")

    result = publisher.approve_post(week_key)
    assert result is False


# Test: OAuth


def test_generate_oauth_url(publisher):
    """Test generating OAuth authorization URL"""
    url = publisher.generate_oauth_url(state="test_state_123")

    assert "https://www.linkedin.com/oauth/v2/authorization" in url
    assert "client_id=test_client_id" in url
    assert "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fcallback" in url
    assert "scope=w_member_social+r_liteprofile" in url
    assert "state=test_state_123" in url


def test_generate_oauth_url_without_state(publisher):
    """Test generating OAuth URL without state parameter"""
    url = publisher.generate_oauth_url()

    assert "https://www.linkedin.com/oauth/v2/authorization" in url
    assert "state=" not in url


def test_generate_oauth_url_missing_credentials(temp_posts_dir, temp_credentials_dir):
    """Test OAuth URL generation fails without credentials"""
    pub = LinkedInPublisher(
        client_id=None,
        posts_dir=str(temp_posts_dir),
        credentials_dir=str(temp_credentials_dir),
    )

    with pytest.raises(OAuthError, match="Missing client_id or redirect_uri"):
        pub.generate_oauth_url()


def test_authenticate_success(publisher, mock_oauth_response, temp_credentials_dir):
    """Test successful OAuth token exchange"""
    with patch.object(publisher.http_client, "post") as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_oauth_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = publisher.authenticate("auth_code_123")

        assert result["access_token"] == "AQVdDPdL9pFKxMjE2MDEzNDg"
        assert result["refresh_token"] == "AQWxPqNjm8gF7Ys9hK"

        # Verify credentials saved
        creds_file = temp_credentials_dir / "linkedin_oauth.json"
        assert creds_file.exists()

        with open(creds_file, "r") as f:
            creds = json.load(f)
            assert creds["access_token"] == mock_oauth_response["access_token"]


def test_authenticate_missing_credentials(temp_posts_dir, temp_credentials_dir):
    """Test authentication fails without OAuth credentials"""
    pub = LinkedInPublisher(
        client_id=None,
        client_secret=None,
        posts_dir=str(temp_posts_dir),
        credentials_dir=str(temp_credentials_dir),
    )

    with pytest.raises(OAuthError, match="Missing OAuth credentials"):
        pub.authenticate("auth_code")


def test_authenticate_api_error(publisher):
    """Test authentication handles API errors"""
    with patch.object(publisher.http_client, "post") as mock_post:
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error_description": "Invalid authorization code"}
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Bad request", request=Mock(), response=mock_response
        )
        mock_post.return_value = mock_response

        with pytest.raises(OAuthError, match="Authentication failed"):
            publisher.authenticate("invalid_code")


def test_refresh_access_token_success(publisher, mock_oauth_response, temp_credentials_dir):
    """Test successful token refresh"""
    # Save initial credentials with refresh token
    initial_creds = {
        "access_token": "old_token",
        "refresh_token": "refresh_token_123",
        "expires_at": datetime.now(timezone.utc).timestamp() - 100,
    }
    with open(temp_credentials_dir / "linkedin_oauth.json", "w") as f:
        json.dump(initial_creds, f)

    with patch.object(publisher.http_client, "post") as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_oauth_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = publisher.refresh_access_token()

        assert result["access_token"] == mock_oauth_response["access_token"]


def test_refresh_access_token_no_refresh_token(publisher):
    """Test token refresh fails without refresh token"""
    with pytest.raises(OAuthError, match="No refresh token available"):
        publisher.refresh_access_token()


# Test: Publishing


def test_publish_post_dry_run_mode(
    dry_run_publisher, sample_post_content, sample_metadata
):
    """Test publishing in dry-run mode saves locally without API call"""
    week_key = "2025.W45"

    result = dry_run_publisher.publish_post(
        week_key=week_key,
        content=sample_post_content,
        metadata=sample_metadata,
    )

    assert result["success"] is True
    assert result["week_key"] == week_key
    assert result["status"] == "draft"
    assert result["post_id"] is None

    # Verify saved locally
    post = dry_run_publisher.load_post(week_key)
    assert post is not None
    assert post["status"] == "draft"


def test_publish_post_duplicate_check(publisher, sample_post_content):
    """Test publishing prevents duplicate posts"""
    week_key = "2025.W45"

    # Mark as already published
    publisher.save_post_locally(week_key, sample_post_content, status="published")

    result = publisher.publish_post(week_key, sample_post_content)

    assert result["success"] is False
    assert "already published" in result["error"]


def test_publish_post_success(
    publisher, sample_post_content, mock_linkedin_post_response, temp_credentials_dir
):
    """Test successful post publishing to LinkedIn"""
    week_key = "2025.W45"

    # Save credentials
    creds = {
        "access_token": "valid_token",
        "expires_at": datetime.now(timezone.utc).timestamp() + 3600,
    }
    with open(temp_credentials_dir / "linkedin_oauth.json", "w") as f:
        json.dump(creds, f)

    with patch.object(publisher.http_client, "post") as mock_post:
        mock_response = Mock()
        mock_response.json.return_value = mock_linkedin_post_response
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        result = publisher.publish_post(week_key, sample_post_content)

        assert result["success"] is True
        assert result["status"] == "published"
        assert result["post_id"] == "urn:li:share:1234567890"

        # Verify post updated
        post = publisher.load_post(week_key)
        assert post["status"] == "published"
        assert post["linkedin_post_id"] == "urn:li:share:1234567890"


def test_publish_post_network_error_retries(publisher, sample_post_content, temp_credentials_dir):
    """Test publishing retries on network errors"""
    week_key = "2025.W45"

    # Save credentials
    creds = {"access_token": "valid_token"}
    with open(temp_credentials_dir / "linkedin_oauth.json", "w") as f:
        json.dump(creds, f)

    with patch.object(publisher.http_client, "post") as mock_post:
        mock_post.side_effect = httpx.RequestError("Network error")

        result = publisher.publish_post(week_key, sample_post_content)

        assert result["success"] is False
        assert "Network error" in result["error"]
        assert mock_post.call_count == publisher.max_retries

        # Verify post marked as failed
        post = publisher.load_post(week_key)
        assert post["status"] == "failed"


def test_publish_post_storage_error(publisher, sample_post_content):
    """Test publishing handles storage errors"""
    week_key = "2025.W45"

    with patch.object(publisher, "_save_post_file", side_effect=StorageError("Disk full")):
        result = publisher.publish_post(week_key, sample_post_content)

        assert result["success"] is False
        assert "Failed to save locally" in result["error"]


# Test: Retry Mechanism


def test_retry_with_backoff_success_first_try(publisher):
    """Test retry succeeds on first attempt"""
    mock_func = Mock(return_value="success")

    result = publisher._retry_with_backoff(mock_func)

    assert result == "success"
    assert mock_func.call_count == 1


def test_retry_with_backoff_success_after_failures(publisher):
    """Test retry succeeds after initial failures"""
    mock_func = Mock(side_effect=[
        PublishingError("Error 1"),
        PublishingError("Error 2"),
        "success"
    ])

    result = publisher._retry_with_backoff(mock_func)

    assert result == "success"
    assert mock_func.call_count == 3


def test_retry_with_backoff_all_fail(publisher):
    """Test retry raises exception after all attempts fail"""
    mock_func = Mock(side_effect=PublishingError("Always fails"))

    with pytest.raises(PublishingError, match="Always fails"):
        publisher._retry_with_backoff(mock_func, max_retries=3)

    assert mock_func.call_count == 3


def test_retry_with_backoff_exponential_delay(publisher):
    """Test retry uses exponential backoff"""
    mock_func = Mock(side_effect=PublishingError("Error"))
    start_time = time.time()

    with pytest.raises(PublishingError):
        publisher._retry_with_backoff(mock_func, max_retries=3)

    elapsed = time.time() - start_time

    # Should wait: 2s + 4s = 6s total (backoff_seconds=2, attempts=2)
    assert elapsed >= 6.0
    assert elapsed < 8.0


# Test: Helper Functions


def test_validate_oauth_credentials_valid():
    """Test validating valid OAuth credentials"""
    assert validate_oauth_credentials(
        "client_id_1234567890",
        "client_secret_abcdefghij"
    ) is True


def test_validate_oauth_credentials_empty():
    """Test validation fails for empty credentials"""
    assert validate_oauth_credentials("", "") is False
    assert validate_oauth_credentials(None, None) is False


def test_validate_oauth_credentials_too_short():
    """Test validation fails for too short credentials"""
    assert validate_oauth_credentials("short", "secret") is False


def test_parse_linkedin_error_with_message():
    """Test parsing LinkedIn error with message field"""
    response = Mock()
    response.json.return_value = {"message": "Invalid request"}
    response.status_code = 400

    error = parse_linkedin_error(response)
    assert error == "Invalid request"


def test_parse_linkedin_error_with_error_description():
    """Test parsing LinkedIn error with error_description"""
    response = Mock()
    response.json.return_value = {"error_description": "Token expired"}
    response.status_code = 401

    error = parse_linkedin_error(response)
    assert error == "Token expired"


def test_parse_linkedin_error_with_error():
    """Test parsing LinkedIn error with error field"""
    response = Mock()
    response.json.return_value = {"error": "invalid_grant"}
    response.status_code = 400

    error = parse_linkedin_error(response)
    assert error == "invalid_grant"


def test_parse_linkedin_error_invalid_json():
    """Test parsing error when response is not JSON"""
    response = Mock()
    response.json.side_effect = json.JSONDecodeError("Invalid", "", 0)
    response.status_code = 500
    response.text = "Internal server error"

    error = parse_linkedin_error(response)
    assert "HTTP 500" in error
    assert "Internal server error" in error


# Test: Edge Cases


def test_publisher_handles_special_characters_in_content(publisher):
    """Test publisher handles special characters in post content"""
    week_key = "2025.W45"
    content = "Test with émojis 🚀, quotes \"test\", and newlines\n\nSecond paragraph"

    publisher.save_post_locally(week_key, content)
    post = publisher.load_post(week_key)

    assert post["content"] == content


def test_publisher_handles_very_long_content(publisher):
    """Test publisher handles very long post content"""
    week_key = "2025.W45"
    content = "A" * 10000  # 10k characters

    publisher.save_post_locally(week_key, content)
    post = publisher.load_post(week_key)

    assert len(post["content"]) == 10000


def test_publisher_thread_safe_file_operations(publisher, sample_post_content):
    """Test concurrent post saves don't corrupt files"""
    import threading

    week_keys = [f"2025.W{i}" for i in range(45, 50)]
    threads = []

    def save_post(wk):
        publisher.save_post_locally(wk, sample_post_content)

    for wk in week_keys:
        t = threading.Thread(target=save_post, args=(wk,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify all posts saved correctly
    posts = publisher.list_posts()
    assert len(posts) == 5
    assert all(p["content"] == sample_post_content for p in posts)
