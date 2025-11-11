"""
FastAPI Application - News Aggregator Dashboard

Provides REST API endpoints for:
- Viewing posts and post history
- Approving and publishing posts
- OAuth authentication with LinkedIn
- Dashboard UI
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src.core.publisher import LinkedInPublisher, PublisherError

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="News Aggregator API",
    description="Weekly Tech & AI News Aggregator with LinkedIn Publishing",
    version="1.0.0",
)

# Initialize publisher (will use env vars for credentials)
publisher = LinkedInPublisher(
    dry_run=os.getenv("DRY_RUN", "false").lower() == "true"
)

# Templates directory
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True)
templates = Jinja2Templates(directory=str(templates_dir))


# Pydantic Models


class PostResponse(BaseModel):
    """Response model for post data"""

    week_key: str
    content: str
    status: str
    created_at: str
    updated_at: Optional[str] = None
    approved_at: Optional[str] = None
    published_at: Optional[str] = None
    linkedin_post_id: Optional[str] = None
    linkedin_post_url: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    metadata: dict = Field(default_factory=dict)


class PublishRequest(BaseModel):
    """Request model for publishing a post"""

    week_key: str
    content: str
    metadata: Optional[dict] = None


class PublishResponse(BaseModel):
    """Response model for publish operation"""

    success: bool
    week_key: str
    post_id: Optional[str] = None
    post_url: Optional[str] = None
    status: str
    error: Optional[str] = None


class MessageResponse(BaseModel):
    """Generic message response"""

    success: bool
    message: str


# Dashboard Routes


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    Serve the main dashboard HTML page.

    Displays all posts with filtering and management options.
    """
    try:
        posts = publisher.list_posts(limit=100)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "posts": posts,
                "total_posts": len(posts),
                "dry_run": publisher.dry_run,
            },
        )
    except Exception as e:
        logger.error("dashboard_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Dashboard error: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "dry_run": publisher.dry_run,
    }


# Post Management Endpoints


@app.get("/v1/posts", response_model=list[PostResponse])
async def list_posts(
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of posts"),
):
    """
    List all posts with optional filtering.

    Args:
        status: Filter by status (draft, approved, published, failed)
        limit: Maximum number of posts to return (1-500)

    Returns:
        List of posts sorted by created_at (newest first)
    """
    try:
        posts = publisher.list_posts(status=status, limit=limit)
        logger.info("list_posts", count=len(posts), status_filter=status)
        return posts
    except Exception as e:
        logger.error("list_posts_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list posts: {str(e)}")


@app.get("/v1/posts/{week_key}", response_model=PostResponse)
async def get_post(week_key: str):
    """
    Get a specific post by week_key.

    Args:
        week_key: Unique week identifier (e.g., "2025.W45")

    Returns:
        Post data with all metadata
    """
    try:
        post = publisher.load_post(week_key)

        if not post:
            raise HTTPException(status_code=404, detail=f"Post {week_key} not found")

        logger.info("get_post", week_key=week_key, status=post.get("status"))
        return post
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_post_error", week_key=week_key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get post: {str(e)}")


@app.post("/v1/posts", response_model=PublishResponse)
async def create_post(request: PublishRequest):
    """
    Create a new post (save locally, optionally publish).

    Args:
        request: Post data including week_key, content, and metadata

    Returns:
        Publish result with status and LinkedIn post info (if published)
    """
    try:
        result = publisher.publish_post(
            week_key=request.week_key,
            content=request.content,
            metadata=request.metadata,
        )

        logger.info(
            "create_post",
            week_key=request.week_key,
            success=result["success"],
            status=result["status"],
        )

        return result
    except Exception as e:
        logger.error("create_post_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")


@app.post("/v1/posts/{week_key}/approve", response_model=MessageResponse)
async def approve_post(week_key: str):
    """
    Approve a draft post for publishing.

    Args:
        week_key: Unique week identifier

    Returns:
        Success message
    """
    try:
        success = publisher.approve_post(week_key)

        if not success:
            # Check if post exists
            post = publisher.load_post(week_key)
            if not post:
                raise HTTPException(status_code=404, detail=f"Post {week_key} not found")

            if post["status"] == "published":
                raise HTTPException(
                    status_code=400, detail="Cannot approve already published post"
                )

            raise HTTPException(status_code=400, detail="Failed to approve post")

        logger.info("approve_post_success", week_key=week_key)
        return MessageResponse(
            success=True, message=f"Post {week_key} approved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("approve_post_error", week_key=week_key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to approve post: {str(e)}")


@app.post("/v1/posts/{week_key}/publish", response_model=PublishResponse)
async def publish_post_endpoint(week_key: str):
    """
    Manually trigger publishing of a post to LinkedIn.

    Args:
        week_key: Unique week identifier

    Returns:
        Publish result with LinkedIn post info
    """
    try:
        # Load existing post
        post = publisher.load_post(week_key)

        if not post:
            raise HTTPException(status_code=404, detail=f"Post {week_key} not found")

        # Publish the post
        result = publisher.publish_post(
            week_key=week_key,
            content=post["content"],
            metadata=post.get("metadata"),
        )

        logger.info(
            "publish_post_manual",
            week_key=week_key,
            success=result["success"],
            status=result["status"],
        )

        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("publish_post_error", week_key=week_key, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to publish post: {str(e)}"
        )


@app.delete("/v1/posts/{week_key}", response_model=MessageResponse)
async def delete_post(week_key: str):
    """
    Delete a post from local storage.

    Args:
        week_key: Unique week identifier

    Returns:
        Success message
    """
    try:
        file_path = publisher.posts_dir / f"{week_key}.json"

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Post {week_key} not found")

        # Don't allow deleting published posts
        post = publisher.load_post(week_key)
        if post and post.get("status") == "published":
            raise HTTPException(
                status_code=400, detail="Cannot delete published posts"
            )

        file_path.unlink()

        logger.info("delete_post", week_key=week_key)
        return MessageResponse(
            success=True, message=f"Post {week_key} deleted successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_post_error", week_key=week_key, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete post: {str(e)}")


# OAuth Endpoints


@app.get("/v1/oauth/login")
async def oauth_login(state: Optional[str] = None):
    """
    Initiate LinkedIn OAuth flow.

    Args:
        state: Optional state parameter for CSRF protection

    Returns:
        Redirect to LinkedIn authorization page
    """
    try:
        state = state or "login_" + datetime.utcnow().isoformat()
        auth_url = publisher.generate_oauth_url(state=state)

        logger.info("oauth_login_initiated", state=state)
        return RedirectResponse(url=auth_url)
    except PublisherError as e:
        logger.error("oauth_login_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("oauth_login_unexpected_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to initiate OAuth: {str(e)}"
        )


@app.get("/v1/oauth/callback")
async def oauth_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
):
    """
    Handle LinkedIn OAuth callback.

    Args:
        code: Authorization code from LinkedIn
        state: State parameter (for CSRF verification)
        error: Error code if OAuth failed
        error_description: Error description if OAuth failed

    Returns:
        Success message or error
    """
    if error:
        logger.error(
            "oauth_callback_error", error=error, description=error_description
        )
        raise HTTPException(
            status_code=400,
            detail=f"OAuth error: {error} - {error_description or 'Unknown error'}",
        )

    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")

    try:
        # Exchange code for token
        token_data = publisher.authenticate(code)

        logger.info("oauth_callback_success", state=state)

        return {
            "success": True,
            "message": "Authentication successful",
            "expires_in": token_data.get("expires_in"),
        }
    except PublisherError as e:
        logger.error("oauth_authentication_failed", error=str(e))
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")
    except Exception as e:
        logger.error("oauth_callback_unexpected_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"OAuth callback failed: {str(e)}"
        )


# Statistics Endpoints


@app.get("/v1/stats")
async def get_statistics():
    """
    Get publishing statistics.

    Returns:
        Statistics about posts by status
    """
    try:
        all_posts = publisher.list_posts(limit=1000)

        stats = {
            "total": len(all_posts),
            "by_status": {
                "draft": 0,
                "approved": 0,
                "published": 0,
                "failed": 0,
            },
            "recent_posts": all_posts[:10],
        }

        for post in all_posts:
            status = post.get("status", "unknown")
            if status in stats["by_status"]:
                stats["by_status"][status] += 1

        logger.info("get_statistics", total_posts=stats["total"])
        return stats
    except Exception as e:
        logger.error("get_statistics_error", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get statistics: {str(e)}"
        )


# Error Handlers


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return {"error": "Not found", "detail": exc.detail, "path": str(request.url)}


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    return {
        "error": "Internal server error",
        "detail": exc.detail,
        "path": str(request.url),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
