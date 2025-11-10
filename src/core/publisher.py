"""
LinkedIn Publisher Module

Handles LinkedIn post publishing with OAuth, retries, idempotency, and local storage.
Supports dry-run mode for testing without actual publishing.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode

import httpx
import structlog

logger = structlog.get_logger()


class PublisherError(Exception):
    """Base exception for publisher errors"""
    pass


class OAuthError(PublisherError):
    """OAuth-related errors"""
    pass


class PublishingError(PublisherError):
    """Errors during post publishing"""
    pass


class StorageError(PublisherError):
    """Errors during local storage operations"""
    pass


class LinkedInPublisher:
    """
    Handles LinkedIn post publishing with OAuth, retries, and idempotency.

    Features:
    - OAuth 2.0 authentication with token refresh
    - Local post storage with metadata
    - Idempotency checks (prevent duplicate posts)
    - Retry logic with exponential backoff
    - Dry-run mode for testing
    - Web dashboard support
    """

    # LinkedIn API endpoints
    LINKEDIN_API_BASE = "https://api.linkedin.com/v2"
    LINKEDIN_OAUTH_BASE = "https://www.linkedin.com/oauth/v2"

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        redirect_uri: str | None = None,
        posts_dir: str = "./data/posts",
        credentials_dir: str = "./data/credentials",
        dry_run: bool = False,
        max_retries: int = 3,
        retry_backoff_seconds: int = 2,
    ):
        """
        Initialize LinkedIn publisher.

        Args:
            client_id: LinkedIn OAuth client ID (from env if not provided)
            client_secret: LinkedIn OAuth client secret (from env if not provided)
            redirect_uri: OAuth redirect URI (from env if not provided)
            posts_dir: Directory for storing posts locally
            credentials_dir: Directory for storing OAuth credentials
            dry_run: If True, save posts locally without publishing
            max_retries: Maximum retry attempts for failed requests
            retry_backoff_seconds: Base seconds for exponential backoff
        """
        self.client_id = client_id or os.getenv("LINKEDIN_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("LINKEDIN_CLIENT_SECRET")
        self.redirect_uri = redirect_uri or os.getenv(
            "LINKEDIN_REDIRECT_URI", "http://localhost:8000/v1/oauth/callback"
        )
        self.posts_dir = Path(posts_dir)
        self.credentials_dir = Path(credentials_dir)
        self.dry_run = dry_run
        self.max_retries = max_retries
        self.retry_backoff_seconds = retry_backoff_seconds

        # Ensure directories exist
        self.posts_dir.mkdir(parents=True, exist_ok=True)
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

        # HTTP client
        self.http_client = httpx.Client(timeout=30.0)

        logger.info(
            "publisher_initialized",
            dry_run=self.dry_run,
            posts_dir=str(self.posts_dir),
            has_credentials=bool(self.client_id and self.client_secret),
        )

    def publish_post(
        self, week_key: str, content: str, metadata: dict | None = None
    ) -> dict:
        """
        Publish a post to LinkedIn.

        Args:
            week_key: Unique week identifier (e.g., "2025.W45")
            content: Post content text
            metadata: Optional metadata (article_count, sources, etc.)

        Returns:
            {
                "success": bool,
                "week_key": str,
                "post_id": str | None,
                "post_url": str | None,
                "status": str,  # "draft", "published", "failed"
                "error": str | None
            }
        """
        logger.info("publish_post_started", week_key=week_key, dry_run=self.dry_run)

        # Check if already published
        if self.is_already_published(week_key):
            error_msg = f"Post with week_key '{week_key}' is already published"
            logger.warning("duplicate_post_attempt", week_key=week_key)
            return {
                "success": False,
                "week_key": week_key,
                "post_id": None,
                "post_url": None,
                "status": "failed",
                "error": error_msg,
            }

        # Save locally first
        try:
            self.save_post_locally(
                week_key=week_key,
                content=content,
                status="draft",
                metadata=metadata,
            )
        except StorageError as e:
            logger.error("local_save_failed", week_key=week_key, error=str(e))
            return {
                "success": False,
                "week_key": week_key,
                "post_id": None,
                "post_url": None,
                "status": "failed",
                "error": f"Failed to save locally: {str(e)}",
            }

        # If dry-run, stop here
        if self.dry_run:
            logger.info("dry_run_mode_skipping_publish", week_key=week_key)
            return {
                "success": True,
                "week_key": week_key,
                "post_id": None,
                "post_url": None,
                "status": "draft",
                "error": None,
            }

        # Publish to LinkedIn
        try:
            result = self._retry_with_backoff(
                lambda: self._create_linkedin_post(content)
            )

            # Update post status to published
            post = self.load_post(week_key)
            if post:
                post["status"] = "published"
                post["published_at"] = datetime.now(timezone.utc).isoformat()
                post["linkedin_post_id"] = result.get("id")
                post["linkedin_post_url"] = result.get("url")
                self._save_post_file(week_key, post)

            logger.info(
                "post_published_successfully",
                week_key=week_key,
                post_id=result.get("id"),
            )

            return {
                "success": True,
                "week_key": week_key,
                "post_id": result.get("id"),
                "post_url": result.get("url"),
                "status": "published",
                "error": None,
            }

        except PublishingError as e:
            logger.error("publishing_failed", week_key=week_key, error=str(e))

            # Update post status to failed
            post = self.load_post(week_key)
            if post:
                post["status"] = "failed"
                post["error_message"] = str(e)
                post["retry_count"] = post.get("retry_count", 0) + 1
                self._save_post_file(week_key, post)

            return {
                "success": False,
                "week_key": week_key,
                "post_id": None,
                "post_url": None,
                "status": "failed",
                "error": str(e),
            }

    def save_post_locally(
        self,
        week_key: str,
        content: str,
        status: str = "draft",
        metadata: dict | None = None,
    ) -> str:
        """
        Save post to local storage.

        Args:
            week_key: Unique week identifier
            content: Post content text
            status: Post status (draft, approved, published, failed)
            metadata: Optional metadata

        Returns:
            File path where post was saved
        """
        now = datetime.now(timezone.utc)

        # Load existing post if it exists
        existing_post = self.load_post(week_key)

        post_data = {
            "week_key": week_key,
            "content": content,
            "status": status,
            "created_at": existing_post["created_at"]
            if existing_post
            else now.isoformat(),
            "updated_at": now.isoformat(),
            "approved_at": existing_post.get("approved_at")
            if existing_post
            else None,
            "published_at": existing_post.get("published_at")
            if existing_post
            else None,
            "linkedin_post_id": existing_post.get("linkedin_post_id")
            if existing_post
            else None,
            "linkedin_post_url": existing_post.get("linkedin_post_url")
            if existing_post
            else None,
            "error_message": existing_post.get("error_message")
            if existing_post
            else None,
            "retry_count": existing_post.get("retry_count", 0) if existing_post else 0,
            "metadata": metadata or {},
        }

        file_path = self._save_post_file(week_key, post_data)
        logger.info("post_saved_locally", week_key=week_key, file_path=str(file_path))

        return str(file_path)

    def load_post(self, week_key: str) -> dict | None:
        """
        Load post from local storage.

        Args:
            week_key: Unique week identifier

        Returns:
            Post data dict or None if not found
        """
        file_path = self.posts_dir / f"{week_key}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("failed_to_load_post", week_key=week_key, error=str(e))
            raise StorageError(f"Failed to load post {week_key}: {str(e)}")

    def list_posts(self, status: str | None = None, limit: int = 50) -> list[dict]:
        """
        List all stored posts with optional status filter.

        Args:
            status: Filter by status (draft, approved, published, failed)
            limit: Maximum number of posts to return

        Returns:
            List of post data dicts, sorted by created_at (newest first)
        """
        posts = []

        for file_path in self.posts_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    post = json.load(f)

                # Apply status filter
                if status and post.get("status") != status:
                    continue

                posts.append(post)

            except (json.JSONDecodeError, IOError) as e:
                logger.warning(
                    "skipping_corrupted_post", file=str(file_path), error=str(e)
                )
                continue

        # Sort by created_at (newest first)
        posts.sort(key=lambda p: p.get("created_at", ""), reverse=True)

        return posts[:limit]

    def get_post_status(self, week_key: str) -> str | None:
        """
        Get status of a specific post.

        Args:
            week_key: Unique week identifier

        Returns:
            Status string or None if post not found
        """
        post = self.load_post(week_key)
        return post.get("status") if post else None

    def is_already_published(self, week_key: str) -> bool:
        """
        Check if post with week_key was already published.

        Args:
            week_key: Unique week identifier

        Returns:
            True if post exists and is published
        """
        status = self.get_post_status(week_key)
        return status == "published"

    def approve_post(self, week_key: str) -> bool:
        """
        Approve a draft post for publishing.

        Args:
            week_key: Unique week identifier

        Returns:
            True if approved successfully
        """
        post = self.load_post(week_key)

        if not post:
            logger.warning("post_not_found_for_approval", week_key=week_key)
            return False

        if post["status"] == "published":
            logger.warning("cannot_approve_published_post", week_key=week_key)
            return False

        post["status"] = "approved"
        post["approved_at"] = datetime.now(timezone.utc).isoformat()
        self._save_post_file(week_key, post)

        logger.info("post_approved", week_key=week_key)
        return True

    def generate_oauth_url(self, state: str | None = None) -> str:
        """
        Generate LinkedIn OAuth authorization URL.

        Args:
            state: Optional state parameter for CSRF protection

        Returns:
            Authorization URL
        """
        if not self.client_id or not self.redirect_uri:
            raise OAuthError("Missing client_id or redirect_uri for OAuth")

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "w_member_social r_liteprofile",
        }

        if state:
            params["state"] = state

        return f"{self.LINKEDIN_OAUTH_BASE}/authorization?{urlencode(params)}"

    def authenticate(self, auth_code: str) -> dict:
        """
        Exchange OAuth code for access token.

        Args:
            auth_code: Authorization code from OAuth callback

        Returns:
            Token data dict with access_token, expires_in, etc.
        """
        if not self.client_id or not self.client_secret:
            raise OAuthError("Missing OAuth credentials")

        data = {
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = self.http_client.post(
                f"{self.LINKEDIN_OAUTH_BASE}/accessToken",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

            token_data = response.json()

            # Save credentials
            self._save_credentials(token_data)

            logger.info("oauth_authentication_successful")
            return token_data

        except httpx.HTTPStatusError as e:
            error_msg = parse_linkedin_error(e.response)
            logger.error("oauth_authentication_failed", error=error_msg)
            raise OAuthError(f"Authentication failed: {error_msg}")

    def refresh_access_token(self) -> dict:
        """
        Refresh expired access token.

        Returns:
            New token data dict
        """
        credentials = self._load_credentials()

        if not credentials or "refresh_token" not in credentials:
            raise OAuthError("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": credentials["refresh_token"],
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            response = self.http_client.post(
                f"{self.LINKEDIN_OAUTH_BASE}/accessToken",
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            response.raise_for_status()

            token_data = response.json()

            # Save new credentials
            self._save_credentials(token_data)

            logger.info("access_token_refreshed")
            return token_data

        except httpx.HTTPStatusError as e:
            error_msg = parse_linkedin_error(e.response)
            logger.error("token_refresh_failed", error=error_msg)
            raise OAuthError(f"Token refresh failed: {error_msg}")

    def _create_linkedin_post(self, content: str) -> dict:
        """
        Internal method to create post via LinkedIn API.

        Args:
            content: Post content text

        Returns:
            LinkedIn API response with post ID and URL
        """
        credentials = self._load_credentials()

        if not credentials or "access_token" not in credentials:
            raise PublishingError("No access token available. Please authenticate first.")

        # Prepare post data (LinkedIn UGC API format)
        post_data = {
            "author": "urn:li:person:CURRENT",  # Special value for current user
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": content},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        headers = {
            "Authorization": f"Bearer {credentials['access_token']}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

        try:
            response = self.http_client.post(
                f"{self.LINKEDIN_API_BASE}/ugcPosts",
                json=post_data,
                headers=headers,
            )
            response.raise_for_status()

            result = response.json()

            # Extract post ID and construct URL
            post_id = result.get("id", "")
            post_url = f"https://www.linkedin.com/feed/update/{post_id}" if post_id else None

            return {"id": post_id, "url": post_url, "raw_response": result}

        except httpx.HTTPStatusError as e:
            error_msg = parse_linkedin_error(e.response)
            logger.error("linkedin_api_error", error=error_msg, status=e.response.status_code)
            raise PublishingError(f"LinkedIn API error: {error_msg}")

        except httpx.RequestError as e:
            logger.error("network_error", error=str(e))
            raise PublishingError(f"Network error: {str(e)}")

    def _retry_with_backoff(self, func: Callable, max_retries: int | None = None) -> Any:
        """
        Retry function with exponential backoff.

        Args:
            func: Function to retry
            max_retries: Override default max_retries

        Returns:
            Function return value

        Raises:
            Last exception if all retries fail
        """
        max_retries = max_retries or self.max_retries
        last_exception = None

        for attempt in range(max_retries):
            try:
                return func()
            except PublishingError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = self.retry_backoff_seconds * (2 ** attempt)
                    logger.warning(
                        "retry_attempt",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        wait_seconds=wait_time,
                        error=str(e),
                    )
                    time.sleep(wait_time)
                else:
                    logger.error("max_retries_exceeded", max_retries=max_retries)

        raise last_exception

    def _save_post_file(self, week_key: str, post_data: dict) -> Path:
        """Save post data to JSON file"""
        file_path = self.posts_dir / f"{week_key}.json"

        try:
            with open(file_path, "w") as f:
                json.dump(post_data, f, indent=2)
            return file_path
        except IOError as e:
            raise StorageError(f"Failed to save post file: {str(e)}")

    def _save_credentials(self, token_data: dict) -> None:
        """Save OAuth credentials to file"""
        file_path = self.credentials_dir / "linkedin_oauth.json"

        # Calculate expiry time
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc).timestamp() + expires_in

        credentials = {
            "access_token": token_data.get("access_token"),
            "refresh_token": token_data.get("refresh_token"),
            "expires_at": expires_at,
            "token_type": token_data.get("token_type", "Bearer"),
            "scope": token_data.get("scope", ""),
        }

        try:
            with open(file_path, "w") as f:
                json.dump(credentials, f, indent=2)
        except IOError as e:
            logger.error("failed_to_save_credentials", error=str(e))
            raise StorageError(f"Failed to save credentials: {str(e)}")

    def _load_credentials(self) -> dict | None:
        """Load OAuth credentials from file"""
        file_path = self.credentials_dir / "linkedin_oauth.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error("failed_to_load_credentials", error=str(e))
            return None

    def __del__(self):
        """Cleanup HTTP client on deletion"""
        if hasattr(self, "http_client"):
            self.http_client.close()


# Helper Functions


def validate_oauth_credentials(client_id: str, client_secret: str) -> bool:
    """
    Validate OAuth credentials are properly formatted.

    Args:
        client_id: LinkedIn OAuth client ID
        client_secret: LinkedIn OAuth client secret

    Returns:
        True if credentials appear valid
    """
    if not client_id or not client_secret:
        return False

    # Basic validation: non-empty strings with reasonable length
    if len(client_id) < 10 or len(client_secret) < 10:
        return False

    return True


def parse_linkedin_error(response: httpx.Response) -> str:
    """
    Parse LinkedIn API error responses.

    Args:
        response: HTTP response object

    Returns:
        Human-readable error message
    """
    try:
        error_data = response.json()

        # LinkedIn API error format
        if "message" in error_data:
            return error_data["message"]

        if "error_description" in error_data:
            return error_data["error_description"]

        if "error" in error_data:
            return str(error_data["error"])

        return str(error_data)

    except (json.JSONDecodeError, ValueError):
        return f"HTTP {response.status_code}: {response.text[:200]}"
