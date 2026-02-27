#!/usr/bin/env python3
"""
FastAPI backend for the Hackathon Admin Dashboard and Public Leaderboard.
Serves data from hackathon.db via REST API endpoints.
"""

import argparse
import json
import logging
import os
import re
import shutil
import sqlite3
import time  # Needed for timestamp handling
import urllib.parse  # Needed for Discord OAuth URL generation
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Optional

import aiohttp  # Needed for Enhanced Transactions API
import requests  # Used by HeliusPriceService
import uvicorn
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    Form,
    HTTPException,
    Request,
    UploadFile,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi import (
    File as FastAPIFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, create_model
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import create_engine, text

# Add path for importing schema module
from hackathon.backend.schema import get_fields, get_schema
from hackathon.backend.simple_audit import log_security_event, log_user_action
from hackathon.backend.websocket_service import prize_pool_service

# Setup rate limiter (can be disabled for testing)
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() not in ["false", "0", "no"]
limiter = Limiter(key_func=get_remote_address)


# Conditional rate limiting decorator
def conditional_rate_limit(rate_limit_str):
    """Apply rate limiting only if ENABLE_RATE_LIMITING is True."""
    if ENABLE_RATE_LIMITING:
        return limiter.limit(rate_limit_str)
    else:
        # Return a no-op decorator for testing
        def no_op_decorator(func):
            return func

        return no_op_decorator


# Configuration
# Get the repository root directory (3 levels up from hackathon/dashboard/app.py)
REPO_ROOT = Path(__file__).parent.parent.parent

# Load environment variables from repo root
load_dotenv(REPO_ROOT / ".env")

from hackathon.backend.config import (  # noqa: E402
    HACKATHON_DB_PATH,
    SUBMISSION_DEADLINE,
    calculate_vote_weight,
)

STATIC_DATA_DIR = os.getenv(
    "STATIC_DATA_DIR", str(REPO_ROOT / "hackathon" / "dashboard" / "frontend" / "public" / "data")
)
LOG_FILE_PATH = REPO_ROOT / "logs" / "hackathon_api.log"

# Submission window configuration loaded from config module

# Setup logging first
LOG_FILE_PATH.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE_PATH), logging.StreamHandler()],
)

# Discord OAuth configuration
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5173/auth/discord/callback")

# Discord Guild/Bot configuration
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
# Prefer explicit bot token, else fall back to DISCORD_TOKEN if present
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")
# Debug: Log Discord config status (without exposing secrets)
if DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET:
    logging.info(f"Discord OAuth configured: Client ID starts with {DISCORD_CLIENT_ID[:10]}...")
else:
    logging.warning("Discord OAuth not configured - missing CLIENT_ID or CLIENT_SECRET")

# Log guild/bot role-fetch capability
if DISCORD_GUILD_ID and DISCORD_BOT_TOKEN:
    logging.info("Discord guild role fetch enabled (bot token present)")
elif DISCORD_GUILD_ID and not DISCORD_BOT_TOKEN:
    logging.warning("DISCORD_GUILD_ID set but no bot token; guild roles will not be fetched via bot")

# Create FastAPI app
app = FastAPI(
    title="Clank Tank Hackathon API",
    description="API for hackathon admin dashboard and public leaderboard",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Ensure DB schema at startup (works with uvicorn module import)
@app.on_event("startup")
async def ensure_db_schema_startup():
    try:
        create_users_table()
        logging.info("Users table ensured (including roles column)")

        # Start WebSocket service for real-time prize pool updates
        await prize_pool_service.start()
        logging.info("WebSocket service started for real-time prize pool updates")
    except Exception as e:
        logging.error(f"Startup schema ensure failed: {e}")


@app.on_event("shutdown")
async def shutdown_websocket_service():
    """Clean shutdown of WebSocket service."""
    try:
        await prize_pool_service.stop()
        logging.info("WebSocket service stopped")
    except Exception as e:
        logging.error(f"Error stopping WebSocket service: {e}")


# Configure CORS with environment-specific origins
def get_allowed_origins():
    """Get CORS allowed origins based on environment."""
    # Allow override via environment variable
    cors_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    if cors_origins:
        return cors_origins.split(",")

    # Environment-specific defaults
    environment = os.getenv("ENVIRONMENT", "development").lower()

    if environment == "production":
        # Production: Restrict to actual domain
        return ["https://clanktank.tv"]
    else:
        # Development: Allow local development
        return ["http://localhost:3000", "http://localhost:5173", "http://127.0.0.1:3000", "http://127.0.0.1:5173"]


allowed_origins = get_allowed_origins()
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"

    # XSS protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # HTTPS enforcement for production
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Content Security Policy
    # Note: 'unsafe-inline' for styles only - required for React/Vite CSS-in-JS
    # Scripts use strict-dynamic with CDN allowlist instead of unsafe-eval
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' cdn.jsdelivr.net; "
        "img-src 'self' data: https:; "
        "connect-src 'self' wss: https:; "
        "frame-ancestors 'none';"
    )
    response.headers["Content-Security-Policy"] = csp_policy

    return response


# Database Engine
engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")


# Token Voting Functions — calculate_vote_weight imported from config


class BirdeyePriceService:
    """Service for fetching token prices from Birdeye API."""

    def __init__(self):
        self.base_url = "https://public-api.birdeye.so/defi/multi_price"
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def get_token_prices(self, mint_addresses: list) -> dict[str, float]:
        """Get current USD prices for multiple tokens"""
        cache_key = ",".join(sorted(mint_addresses))
        now = time.time()

        # Check cache
        if cache_key in self.cache and now - self.cache[cache_key]["timestamp"] < self.cache_ttl:
            return self.cache[cache_key]["prices"]

        # Fetch from Birdeye
        params = {"list_address": ",".join(mint_addresses), "ui_amount_mode": "raw"}
        headers = {"accept": "application/json", "x-chain": "solana"}

        try:
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()

            prices = {}
            if data.get("success") and "data" in data:
                for mint, price_data in data["data"].items():
                    prices[mint] = price_data.get("value", 0)

            # Cache results
            self.cache[cache_key] = {"prices": prices, "timestamp": now}

            return prices

        except Exception as e:
            logging.error(f"Birdeye API error: {e}")
            return {mint: 0 for mint in mint_addresses}


# Global price service instance
price_service = BirdeyePriceService()


# Pydantic models
class SubmissionSummary(BaseModel):
    submission_id: int
    project_name: str
    category: str
    status: str
    created_at: str
    avg_score: float | None = None
    judge_count: int | None = None
    project_image: str | None = None
    description: str | None = None
    discord_handle: str | None = None
    # Add Discord user info
    discord_id: str | None = None
    discord_username: str | None = None
    discord_discriminator: str | None = None
    discord_avatar: str | None = None
    twitter_handle: str | None = None


class SubmissionDetail(BaseModel):
    submission_id: int
    project_name: str
    category: str
    description: str
    status: str
    created_at: str
    updated_at: str
    github_url: str | None = None
    demo_video_url: str | None = None
    project_image: str | None = None
    problem_solved: str | None = None
    favorite_part: str | None = None
    scores: list[dict[str, Any]] | None = None
    research: dict[str, Any] | None = None
    avg_score: float | None = None
    solana_address: str | None = None
    discord_handle: str | None = None
    # Add Discord user info for detail view
    discord_id: str | None = None
    discord_username: str | None = None
    discord_avatar: str | None = None
    community_score: float | None = None  # Add community score field
    can_edit: bool | None = None
    is_creator: bool | None = None
    twitter_handle: str | None = None


# Dynamically create the SubmissionCreate models from versioned manifests
submission_fields_v1 = {field: (Optional[str], None) for field in get_fields("v1")}
SubmissionCreateV1 = create_model("SubmissionCreateV1", **submission_fields_v1)

# Update SubmissionCreateV2 model to match new schema
submission_fields_v2 = {
    "project_name": (Optional[str], None),
    "discord_handle": (Optional[str], None),  # owner/creator
    "category": (Optional[str], None),
    "description": (Optional[str], None),
    "twitter_handle": (Optional[str], None),
    "github_url": (Optional[str], None),
    "demo_video_url": (Optional[str], None),
    "project_image": (Optional[str], None),
    "problem_solved": (Optional[str], None),
    "favorite_part": (Optional[str], None),
    "solana_address": (Optional[str], None),  # optional
}
SubmissionCreateV2 = create_model("SubmissionCreateV2", **submission_fields_v2)


class LeaderboardEntry(BaseModel):
    rank: int
    submission_id: int
    project_name: str
    category: str
    final_score: float
    community_score: float | None = None  # Add community score field
    youtube_url: str | None = None
    status: str
    discord_handle: str | None = None
    # Add these fields for avatar and linking
    discord_id: str | None = None
    discord_username: str | None = None
    discord_avatar: str | None = None


# Helper to get available columns in hackathon_scores
from sqlalchemy.engine import Connection  # noqa: E402


def get_score_columns(conn: "Connection", required_fields):
    """
    Return only the columns from required_fields that exist in the hackathon_scores table.
    This allows robust queries even if some fields (e.g., community_bonus, final_verdict) are not present yet.
    """
    pragma_result = conn.execute(text("PRAGMA table_info(hackathon_scores)"))
    columns = {row[1] for row in pragma_result.fetchall()}
    return [f for f in required_fields if f in columns]


# Invite Code Validation Functions


def is_submission_window_open() -> bool:
    """Check if the submission window is currently open."""
    if not SUBMISSION_DEADLINE:
        return True  # No deadline set, submissions always open

    try:
        deadline = datetime.fromisoformat(SUBMISSION_DEADLINE)
        # Ensure both are offset-aware (UTC)
        now = datetime.now(timezone.utc)
        return now < deadline
    except ValueError:
        logging.error(f"Invalid SUBMISSION_DEADLINE format: {SUBMISSION_DEADLINE}")
        return True  # Default to open if deadline is invalid


def get_submission_window_info() -> dict:
    """Get information about the submission window status."""
    window_open = is_submission_window_open()

    return {
        "submission_window_open": window_open,
        "submission_deadline": SUBMISSION_DEADLINE,
        "current_time": datetime.now().isoformat(),
    }


def create_users_table():
    """Create the users table for Discord authentication."""
    try:
        engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")
        with engine.connect() as conn:
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS users (
                    discord_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    discriminator TEXT,
                    avatar TEXT,
                    roles TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
                )
            )
            # Ensure roles column exists for older DBs
            pragma_result = conn.execute(text("PRAGMA table_info(users)"))
            columns = {row[1] for row in pragma_result.fetchall()}
            if "roles" not in columns:
                conn.execute(text("ALTER TABLE users ADD COLUMN roles TEXT"))

            # Create likes_dislikes table
            conn.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS likes_dislikes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    discord_id TEXT NOT NULL,
                    submission_id TEXT NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('like', 'dislike')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(discord_id, submission_id),
                    FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                )
            """
                )
            )

            conn.commit()
            logging.info("Users and likes_dislikes tables created successfully")
    except Exception as e:
        logging.error(f"Error creating users table: {e}")


def generate_discord_auth_url() -> str:
    """Generate Discord OAuth authorization URL."""
    if not DISCORD_CLIENT_ID:
        raise HTTPException(status_code=500, detail="Discord OAuth not configured")

    params = {
        "client_id": DISCORD_CLIENT_ID,
        "redirect_uri": DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope": "identify",
    }

    base_url = "https://discord.com/api/oauth2/authorize"
    return f"{base_url}?{urllib.parse.urlencode(params)}"


async def exchange_discord_code(code: str) -> dict:
    """Exchange Discord authorization code for access token and user info."""
    if not DISCORD_CLIENT_ID or not DISCORD_CLIENT_SECRET:
        raise HTTPException(status_code=500, detail="Discord OAuth not configured")

    # Exchange code for access token
    token_data = {
        "client_id": DISCORD_CLIENT_ID,
        "client_secret": DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": DISCORD_REDIRECT_URI,
    }

    async with aiohttp.ClientSession() as session:
        # Get access token
        async with session.post(
            "https://discord.com/api/oauth2/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                logging.error(f"Discord token exchange failed: {resp.status} - {error_text}")

                # Provide more specific error messages based on Discord's response
                if resp.status == 400:
                    try:
                        error_data = await resp.json() if resp.content_type == "application/json" else {}
                        if error_data.get("error") == "invalid_grant":
                            from hackathon.backend.simple_audit import log_security_event

                            log_security_event(
                                "oauth_invalid_grant", f"expired or reused authorization code: {error_data}"
                            )
                            raise HTTPException(
                                status_code=400,
                                detail="Authorization code expired or already used",
                            )
                        elif error_data.get("error") == "invalid_client":
                            from hackathon.backend.simple_audit import log_security_event

                            log_security_event("oauth_invalid_client", f"client configuration error: {error_data}")
                            raise HTTPException(
                                status_code=500,
                                detail="Discord OAuth client configuration error",
                            )
                        else:
                            from hackathon.backend.simple_audit import log_security_event

                            log_security_event("oauth_error", f"Discord OAuth error: {error_data}")
                            raise HTTPException(
                                status_code=400,
                                detail=f"Discord OAuth error: {error_data.get('error', 'invalid_request')}",
                            )
                    except Exception:
                        raise HTTPException(status_code=400, detail="Invalid authorization code")
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Discord service error (HTTP {resp.status})",
                    )

            token_response = await resp.json()

        # Get user info
        access_token = token_response["access_token"]
        async with session.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        ) as resp:
            if resp.status != 200:
                error_text = await resp.text()
                logging.error(f"Discord user info fetch failed: {resp.status} - {error_text}")
                raise HTTPException(status_code=400, detail="Failed to get Discord user info")
            user_data = await resp.json()

    return {"access_token": access_token, "user": user_data}


async def fetch_user_guild_roles(discord_user_id: str) -> list[str]:
    """Fetch list of role IDs for a user in the configured guild using the bot token.

    Returns [] if missing configuration or on error.
    """
    try:
        if not (DISCORD_GUILD_ID and DISCORD_BOT_TOKEN and discord_user_id):
            return []
        url = f"https://discord.com/api/guilds/{DISCORD_GUILD_ID}/members/{discord_user_id}"
        headers = {"Authorization": f"Bot {DISCORD_BOT_TOKEN}"}
        async with aiohttp.ClientSession() as session, session.get(url, headers=headers) as resp:
            if resp.status != 200:
                body = await resp.text()
                logging.warning(f"Guild roles fetch failed {resp.status}: {body}")
                return []
            data = await resp.json()
            roles = data.get("roles", [])
            return [str(r) for r in roles] if isinstance(roles, list) else []
    except Exception as e:
        logging.error(f"Error fetching guild roles: {e}")
        return []


# Function will be moved after DiscordUser model definition


# Define a model for the submission schema field
class SubmissionFieldSchema(BaseModel):
    name: str
    label: str
    type: str
    required: bool
    placeholder: str = None
    maxLength: int = None
    options: list[str] = None
    pattern: str = None
    helperText: str = None


# Enhanced submission schema response with window information
class SubmissionSchemaResponse(BaseModel):
    fields: list[SubmissionFieldSchema]
    submission_window_open: bool
    submission_deadline: str | None = None
    current_time: str


# Define a model for stats
class StatsModel(BaseModel):
    total_submissions: int
    by_status: dict
    by_category: dict
    updated_at: str


# Feedback response models
class FeedbackItem(BaseModel):
    reaction_type: str
    emoji: str
    name: str
    vote_count: int
    voters: list[str]


class FeedbackSummary(BaseModel):
    submission_id: int
    total_votes: int
    feedback: list[FeedbackItem]


# Discord OAuth models
class DiscordUser(BaseModel):
    discord_id: str
    username: str
    discriminator: str | None = None
    avatar: str | None = None
    roles: list[str] | None = None


class DiscordAuthResponse(BaseModel):
    user: DiscordUser
    access_token: str


class DiscordCallbackRequest(BaseModel):
    code: str


class LikeDislikeRequest(BaseModel):
    submission_id: int
    action: str  # "like" or "dislike" or "remove"


class LikeDislikeResponse(BaseModel):
    likes: int
    dislikes: int
    user_action: str | None = None  # "like", "dislike", or None


def create_or_update_user(discord_user_data: dict, roles: list[str] | None = None) -> DiscordUser:
    """Create or update user in database."""
    try:
        engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")
        with engine.connect() as conn:
            discord_id = str(discord_user_data["id"])
            username = discord_user_data["username"]
            discriminator = discord_user_data.get("discriminator")
            avatar_hash = discord_user_data.get("avatar")

            # Construct full Discord CDN avatar URL if avatar hash exists
            avatar = None
            if avatar_hash:
                avatar = f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar_hash}.png"

            # Serialize roles for storage
            roles_json = json.dumps(roles) if roles else None

            # Insert or update user
            conn.execute(
                text(
                    """
                INSERT OR REPLACE INTO users (discord_id, username, discriminator, avatar, roles, last_login)
                VALUES (:discord_id, :username, :discriminator, :avatar, :roles, CURRENT_TIMESTAMP)
            """
                ),
                {
                    "discord_id": discord_id,
                    "username": username,
                    "discriminator": discriminator,
                    "avatar": avatar,
                    "roles": roles_json,
                },
            )
            conn.commit()

            return DiscordUser(
                discord_id=discord_id,
                username=username,
                discriminator=discriminator,
                avatar=avatar,
                roles=roles or None,
            )
    except Exception as e:
        logging.error(f"Error creating/updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to create user")


async def validate_discord_token(request: Request) -> DiscordUser | None:
    """Validate Discord access token and return user if valid."""

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    token = auth_header.split(" ")[1]
    # Environment-configurable test token for development/testing ONLY
    # SECURITY: This MUST NOT be used in production environments
    test_token = os.getenv("TEST_AUTH_TOKEN")
    environment = os.getenv("ENVIRONMENT", "development").lower()
    if test_token and token == test_token:
        if environment == "production":
            logging.error("SECURITY: TEST_AUTH_TOKEN bypass attempted in production - denied")
            log_security_event("test_token_blocked_production", {"token_prefix": token[:8] + "..."})
            return None  # Block test token in production
        return DiscordUser(
            discord_id="1234567890",
            username="testuser",
            discriminator="0001",
            avatar=None,
        )
    try:
        async with (
            aiohttp.ClientSession() as session,
            session.get(
                "https://discord.com/api/users/@me",
                headers={"Authorization": f"Bearer {token}"},
            ) as resp,
        ):
            if resp.status != 200:
                from hackathon.backend.simple_audit import log_security_event

                log_security_event("auth_failed")
                return None
            user_data = await resp.json()
            # Fetch roles via bot token (best effort)
            roles = await fetch_user_guild_roles(str(user_data.get("id")))
            # Update user in database including roles
            discord_user = create_or_update_user(user_data, roles)
            from hackathon.backend.simple_audit import log_user_action

            log_user_action("auth_success", discord_user.discord_id)
            return discord_user
    except Exception as e:
        logging.error(f"Error validating Discord token: {e}")
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("auth_error")
        return None


def validate_github_url(url: str) -> bool:
    """Validate GitHub URL format for security."""
    if not url:
        return False
    # Pattern: https://github.com/username/repo (with optional additional paths)
    pattern = r"^https://github\.com/[\w.-]+/[\w.-]+(/.*)?$"
    return bool(re.match(pattern, url))


def validate_submission_github_url(data_dict: dict, action: str = "submission"):
    """Validate GitHub URL in submission data and raise HTTPException if invalid."""
    github_url = data_dict.get("github_url")
    if github_url and not validate_github_url(github_url):
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("invalid_github_url", f"rejected in {action}: {github_url}")
        raise HTTPException(
            status_code=422,
            detail="Invalid GitHub repository URL format. Please use: https://github.com/username/repository",
        )


# Allowed table names for SQL queries (prevents SQL injection via table name interpolation)
ALLOWED_TABLES = frozenset(
    [
        "hackathon_submissions_v1",
        "hackathon_submissions_v2",
        "hackathon_scores",
        "hackathon_research",
        "users",
        "token_votes",
        "token_metadata",
    ]
)


def validate_table_name(table_name: str) -> str:
    """Validate table name against allowlist to prevent SQL injection.

    Raises ValueError if table name is not in the allowlist.
    """
    if table_name not in ALLOWED_TABLES:
        log_security_event("invalid_table_name", {"attempted_table": table_name})
        raise ValueError(f"Invalid table name: {table_name}")
    return table_name


def get_db_connection():
    """Get database connection."""
    return sqlite3.connect(HACKATHON_DB_PATH)


def get_next_submission_id(conn, version: str = "v2") -> int:
    """
    Get the next sequential submission ID for the given version.
    Uses auto-increment behavior by finding the max ID and adding 1.
    Works with both SQLite and SQLAlchemy connections.
    """
    table_name = f"hackathon_submissions_{version}"
    validate_table_name(table_name)  # Prevent SQL injection via version parameter

    try:
        # Check if this is a raw SQLite connection or SQLAlchemy connection
        if hasattr(conn, "cursor"):
            # Raw SQLite connection
            cursor = conn.cursor()
            cursor.execute(f"SELECT MAX(submission_id) FROM {table_name}")
            result = cursor.fetchone()
        else:
            # SQLAlchemy connection
            from sqlalchemy import text

            result = conn.execute(text(f"SELECT MAX(submission_id) FROM {table_name}"))
            result = result.fetchone()

        max_id = result[0] if result and result[0] is not None else 0
        return max_id + 1
    except Exception:
        # Table doesn't exist or is empty
        return 1


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Clank Tank Hackathon API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "endpoints": {
            "submissions": {
                "POST /api/submissions": "Create a new submission (latest schema)",
                "GET /api/submissions": "List all submissions (latest)",
                "GET /api/submissions/{submission_id}": "Get submission details (latest)",
                "POST /api/v1/submissions": "Create a new submission (v1 schema, deprecated)",
                "GET /api/{version}/submissions": "List all submissions (versioned)",
                "GET /api/{version}/submissions/{submission_id}": "Get submission details (versioned)",
                "GET /api/{version}/submission-schema": "Get submission schema (versioned)",
                "POST /api/upload-image": "Upload a project image and get a URL",
            },
            "judging": {"GET /api/submission/{submission_id}/feedback": "Get community feedback for a submission"},
            "public": {
                "GET /api/leaderboard": "Get public leaderboard (latest)",
                "GET /api/stats": "Get overall hackathon stats (latest)",
                "GET /api/{version}/leaderboard": "Get public leaderboard (versioned)",
                "GET /api/{version}/stats": "Get overall hackathon stats (versioned)",
                "GET /api/uploads/{filename}": "Serve uploaded project images",
            },
        },
    }


# Discord OAuth Endpoints
@app.get("/api/auth/discord/login", tags=["auth"])
async def discord_login():
    """Initiate Discord OAuth login flow."""
    auth_url = generate_discord_auth_url()
    return {"auth_url": auth_url}


@app.post("/api/auth/discord/callback", tags=["auth"], response_model=DiscordAuthResponse)
async def discord_callback(callback_data: DiscordCallbackRequest):
    """Handle Discord OAuth callback."""
    try:
        # Exchange code for access token and user info
        oauth_data = await exchange_discord_code(callback_data.code)

        # Fetch roles via bot token (best effort) and create/update user in DB
        roles = await fetch_user_guild_roles(str(oauth_data["user"].get("id")))
        discord_user = create_or_update_user(oauth_data["user"], roles)

        return DiscordAuthResponse(user=discord_user, access_token=oauth_data["access_token"])
    except Exception as e:
        logging.error(f"Discord OAuth callback error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/auth/me", tags=["auth"], response_model=DiscordUser)
async def get_current_user(request: Request):
    """Get current authenticated user info."""
    # Validate Discord token and return user
    discord_user = await validate_discord_token(request)
    if not discord_user:
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("auth_me_failed", "invalid or missing token")
        raise HTTPException(status_code=401, detail="Not authenticated")

    log_user_action("auth_me_success", discord_user.discord_id)
    return discord_user


@app.post("/api/auth/discord/logout", tags=["auth"])
async def discord_logout():
    """Logout user (clear session)."""
    return {"message": "Logged out successfully"}


@app.post("/api/submissions/{submission_id}/like-dislike", tags=["latest"], response_model=LikeDislikeResponse)
async def toggle_like_dislike(submission_id: int, like_request: LikeDislikeRequest, request: Request):
    """Toggle like/dislike for a submission by authenticated Discord user."""
    # Get authenticated Discord user
    discord_user = await validate_discord_token(request)
    if not discord_user:
        raise HTTPException(status_code=401, detail="Discord authentication required")

    discord_id = discord_user.discord_id

    try:
        engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")
        with engine.connect() as conn:
            # Check current user action
            current_action = conn.execute(
                text(
                    "SELECT action FROM likes_dislikes WHERE discord_id = :discord_id AND submission_id = :submission_id"
                ),
                {"discord_id": discord_id, "submission_id": submission_id},
            ).fetchone()

            if like_request.action == "remove":
                # Remove any existing like/dislike
                conn.execute(
                    text(
                        "DELETE FROM likes_dislikes WHERE discord_id = :discord_id AND submission_id = :submission_id"
                    ),
                    {"discord_id": discord_id, "submission_id": submission_id},
                )
            else:
                # Insert or update like/dislike
                if current_action:
                    conn.execute(
                        text(
                            "UPDATE likes_dislikes SET action = :action, created_at = CURRENT_TIMESTAMP WHERE discord_id = :discord_id AND submission_id = :submission_id"
                        ),
                        {"action": like_request.action, "discord_id": discord_id, "submission_id": submission_id},
                    )
                else:
                    conn.execute(
                        text(
                            "INSERT INTO likes_dislikes (discord_id, submission_id, action) VALUES (:discord_id, :submission_id, :action)"
                        ),
                        {"discord_id": discord_id, "submission_id": submission_id, "action": like_request.action},
                    )

            conn.commit()

            # Get updated counts
            result = conn.execute(
                text("""
                    SELECT
                        SUM(CASE WHEN action = 'like' THEN 1 ELSE 0 END) as likes,
                        SUM(CASE WHEN action = 'dislike' THEN 1 ELSE 0 END) as dislikes
                    FROM likes_dislikes
                    WHERE submission_id = :submission_id
                """),
                {"submission_id": submission_id},
            ).fetchone()

            # Get user's current action
            user_action_result = conn.execute(
                text(
                    "SELECT action FROM likes_dislikes WHERE discord_id = :discord_id AND submission_id = :submission_id"
                ),
                {"discord_id": discord_id, "submission_id": submission_id},
            ).fetchone()

            user_action = user_action_result[0] if user_action_result else None

            return LikeDislikeResponse(likes=result[0] or 0, dislikes=result[1] or 0, user_action=user_action)

    except Exception as e:
        logging.error(f"Error toggling like/dislike: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/submissions/{submission_id}/like-dislike", tags=["latest"], response_model=LikeDislikeResponse)
async def get_like_dislike_counts(submission_id: int, request: Request):
    """Get like/dislike counts for a submission."""
    # Get authenticated Discord user (optional for viewing counts)
    discord_user = await validate_discord_token(request)
    discord_id = discord_user.discord_id if discord_user else None

    try:
        engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")
        with engine.connect() as conn:
            # Get counts
            result = conn.execute(
                text("""
                    SELECT
                        SUM(CASE WHEN action = 'like' THEN 1 ELSE 0 END) as likes,
                        SUM(CASE WHEN action = 'dislike' THEN 1 ELSE 0 END) as dislikes
                    FROM likes_dislikes
                    WHERE submission_id = :submission_id
                """),
                {"submission_id": submission_id},
            ).fetchone()

            # Get user's current action
            user_action_result = conn.execute(
                text(
                    "SELECT action FROM likes_dislikes WHERE discord_id = :discord_id AND submission_id = :submission_id"
                ),
                {"discord_id": discord_id, "submission_id": submission_id},
            ).fetchone()

            user_action = user_action_result[0] if user_action_result else None

            return LikeDislikeResponse(likes=result[0] or 0, dislikes=result[1] or 0, user_action=user_action)

    except Exception as e:
        logging.error(f"Error getting like/dislike counts: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/submissions", tags=["latest"], response_model=list[SubmissionSummary])
async def list_submissions_latest(
    include: str = "scores,research,community",
    status: str | None = None,
    category: str | None = None,
):
    return await list_submissions(version="v2", include=include, status=status, category=category, detail=False)


@app.get("/api/submissions/full", tags=["latest"])
async def list_submissions_full(
    include: str = "scores,research,community",
    status: str | None = None,
    category: str | None = None,
):
    data = await list_submissions(version="v2", include=include, status=status, category=category, detail=True)
    return JSONResponse(content=data)


@app.get("/api/submissions/{submission_id}", tags=["latest"], response_model=SubmissionDetail)
async def get_submission_latest(submission_id: int, request: Request, include: str = "scores,research,community"):
    return await get_submission(submission_id=submission_id, version="v2", include=include, request=request)


@conditional_rate_limit("5/minute")
@app.post("/api/submissions", status_code=201, tags=["latest"], response_model=dict)
async def create_submission_latest(submission: SubmissionCreateV2, request: Request):
    """Create a new submission with v2 schema. Requires Discord authentication."""
    print(f"📝 Processing submission: {submission.project_name}")

    # Check if submission window is open
    if not is_submission_window_open():
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("submission_window_closed", "attempted submission outside window")
        raise HTTPException(
            status_code=403,
            detail="Submission window is closed. New submissions are no longer accepted.",
        )

    # Require Discord authentication
    discord_user = await validate_discord_token(request)
    if not discord_user:
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("unauthorized_submission", "attempted submission without auth")
        raise HTTPException(
            status_code=401,
            detail="Discord authentication required. Please log in with Discord to submit.",
        )

    print(f"🔵 Discord auth: {discord_user.username}")
    data_dict = submission.dict()

    # Auto-populate Discord username if not provided or empty
    if not data_dict.get("discord_handle") or data_dict.get("discord_handle").strip() == "":
        data_dict["discord_handle"] = discord_user.username
        print(f"🔄 Auto-populated Discord handle: {discord_user.username}")

    # Validate GitHub URL for security
    validate_submission_github_url(data_dict, "create")

    # Validate project_image field
    project_image = data_dict.get("project_image")
    if project_image:
        if project_image == "[object File]":
            raise HTTPException(
                status_code=422,
                detail="Invalid file object detected in project_image. Please upload the image first and submit the URL instead.",
            )
        elif isinstance(project_image, str) and not project_image.startswith("/api/uploads/"):
            # Remove invalid URLs that aren't our upload URLs
            print(f"⚠️  Invalid project_image URL detected, removing: {project_image}")
            data_dict["project_image"] = None

    # Log Discord submission
    print(f"🔵 Discord submission: {discord_user.username} ({discord_user.discord_id})")

    # Database operations
    try:
        engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")
        with engine.connect() as conn:
            # Generate submission ID
            submission_id = get_next_submission_id(conn, version="v2")

            # Basic data preparation
            now = datetime.now().isoformat()
            data = data_dict.copy()
            data["submission_id"] = submission_id
            data["status"] = "submitted"
            data["created_at"] = now
            data["updated_at"] = now
            # Set owner_discord_id to the Discord user's ID
            data["owner_discord_id"] = discord_user.discord_id

            # Database insertion
            table = validate_table_name("hackathon_submissions_v2")
            columns = ", ".join(data.keys())
            placeholders = ", ".join([f":{key}" for key in data])
            conn.execute(text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"), data)
            conn.commit()

        # Simple audit logging
        from hackathon.backend.simple_audit import log_user_action

        log_user_action("submission_created", discord_user.discord_id, submission_id)

        print(f"✅ Submission saved: {submission_id}")
        # Backup creation logic
        import json

        backup_dir = REPO_ROOT / "data" / "submission_backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / f"{submission_id}.json"
        with open(backup_path, "w") as f:
            json.dump({"submission_data": data}, f, indent=2)
        return {
            "success": True,
            "submission_id": submission_id,
            "message": "Submission received and saved successfully",
        }

    except Exception as e:
        print(f"❌ Database error: {e}")
        # Only include submission_id if it was successfully generated
        error_content = {"success": False, "error": "Internal server error. Please try again later."}
        if "submission_id" in locals():
            error_content["submission_id"] = submission_id
        return JSONResponse(
            status_code=500,
            content=error_content,
        )


@app.put("/api/submissions/{submission_id}", tags=["latest"], response_model=dict)
@conditional_rate_limit("5/minute")
async def edit_submission_latest(submission_id: int, submission: SubmissionCreateV2, request: Request):
    """
    Edit an existing submission. Requires Discord authentication and user must be the original creator.
    Only allowed during the submission window.
    """
    # Check if submission window is open
    if not is_submission_window_open():
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("edit_window_closed", "attempted edit outside window")
        raise HTTPException(
            status_code=403,
            detail="Submission editing is no longer allowed. The submission window has closed.",
        )

    # Require Discord authentication
    discord_user = await validate_discord_token(request)
    if not discord_user:
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("unauthorized_edit", "attempted edit without auth")
        raise HTTPException(
            status_code=401,
            detail="Discord authentication required. Please log in with Discord to edit.",
        )

    print(f"🔵 Discord edit request: {discord_user.username}")

    try:
        engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")
        with engine.connect() as conn:
            # Verify the submission exists and check ownership
            result = conn.execute(
                text("SELECT owner_discord_id FROM hackathon_submissions_v2 WHERE submission_id = :submission_id"),
                {"submission_id": submission_id},
            )
            row = result.mappings().first()
            if not row:
                from hackathon.backend.simple_audit import log_security_event

                log_security_event("edit_nonexistent", f"attempted edit of non-existent submission: {submission_id}")
                raise HTTPException(status_code=404, detail="Submission not found")
            if row["owner_discord_id"] != discord_user.discord_id:
                from hackathon.backend.simple_audit import log_security_event

                log_security_event(
                    "unauthorized_edit_attempt",
                    f"user {discord_user.discord_id} attempted to edit submission {submission_id} owned by {row['owner_discord_id']}",
                )
                raise HTTPException(status_code=403, detail="You can only edit your own submissions")

            # Prepare data for update
            now = datetime.now().isoformat()
            data = submission.dict()
            data["updated_at"] = now

            # Validate GitHub URL for security
            validate_submission_github_url(data, "edit")

            # Auto-populate Discord username if field is empty
            if not data.get("discord_handle") or data.get("discord_handle").strip() == "":
                data["discord_handle"] = discord_user.username
                print(f"🔄 Auto-populated Discord handle during edit: {discord_user.username}")

            # Remove invite_code field before DB update (not a column)
            if "invite_code" in data:
                del data["invite_code"]

            # Build UPDATE statement
            set_clauses = [f"{key} = :{key}" for key in data]
            update_stmt = text(
                f"""
                UPDATE hackathon_submissions_v2
                SET {", ".join(set_clauses)}
                WHERE submission_id = :submission_id
            """
            )

            # Add submission_id to parameters
            data["submission_id"] = submission_id

            # Execute update
            conn.execute(update_stmt, data)
            conn.commit()

            # Simple audit logging
            from hackathon.backend.simple_audit import log_user_action

            log_user_action("submission_edited", discord_user.discord_id, submission_id)

            logging.info(f"Submission {submission_id} edited successfully by {discord_user.username}")
            return {
                "success": True,
                "submission_id": submission_id,
                "message": "Submission updated successfully",
            }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error editing submission {submission_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update submission")


@conditional_rate_limit("5/minute")
@app.post("/api/upload-image", tags=["latest"])
async def upload_image(
    request: Request,
    submission_id: int = Form(...),
    file: UploadFile = FastAPIFile(...),
):
    """Upload project image and return URL."""
    # Check if submission window is open
    if not is_submission_window_open():
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("upload_window_closed", "attempted upload outside window")
        raise HTTPException(
            status_code=403,
            detail="Image upload is no longer allowed. The submission window has closed.",
        )

    # Require Discord authentication
    discord_user = await validate_discord_token(request)
    if not discord_user:
        from hackathon.backend.simple_audit import log_security_event

        log_security_event("unauthorized_upload", "attempted upload without auth")
        raise HTTPException(status_code=401, detail="Discord authentication required.")
    # Check submission ownership
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT owner_discord_id FROM hackathon_submissions_v2 WHERE submission_id = :submission_id"),
            {"submission_id": submission_id},
        )
        row = result.mappings().first()
        if not row:
            from hackathon.backend.simple_audit import log_security_event

            log_security_event("upload_nonexistent", f"attempted upload to non-existent submission: {submission_id}")
            raise HTTPException(status_code=404, detail="Submission not found")
        if row["owner_discord_id"] != discord_user.discord_id:
            from hackathon.backend.simple_audit import log_security_event

            log_security_event(
                "unauthorized_upload_attempt",
                f"user {discord_user.discord_id} attempted to upload to submission {submission_id} owned by {row['owner_discord_id']}",
            )
            raise HTTPException(status_code=403, detail="You do not own this submission.")
    try:
        # Validate filename (basic sanitization)
        if file.filename:
            import string

            safe_chars = string.ascii_letters + string.digits + ".-_"
            if not all(c in safe_chars for c in file.filename):
                from hackathon.backend.simple_audit import log_security_event

                log_security_event("malicious_filename", f"attempted upload with suspicious filename: {file.filename}")
                raise HTTPException(status_code=400, detail="Filename contains invalid characters")

        # Validate file type by content-type
        if not file.content_type or not file.content_type.startswith("image/"):
            from hackathon.backend.simple_audit import log_security_event

            log_security_event(
                "invalid_file_type", f"attempted upload of {file.content_type} to submission {submission_id}"
            )
            raise HTTPException(status_code=400, detail="File must be an image")

        # Validate file size (2MB limit)
        MAX_SIZE = 2 * 1024 * 1024  # 2MB
        content = await file.read()
        if len(content) > MAX_SIZE:
            from hackathon.backend.simple_audit import log_security_event

            log_security_event(
                "file_too_large",
                f"attempted upload of {len(content)} bytes to submission {submission_id} (max: {MAX_SIZE})",
            )
            raise HTTPException(status_code=400, detail="File size must be less than 2MB")

        # Check minimum file size to prevent empty files
        MIN_SIZE = 100  # 100 bytes minimum
        if len(content) < MIN_SIZE:
            from hackathon.backend.simple_audit import log_security_event

            log_security_event(
                "file_too_small",
                f"attempted upload of {len(content)} bytes to submission {submission_id} (min: {MIN_SIZE})",
            )
            raise HTTPException(status_code=400, detail="File is too small to be a valid image")

        # Validate file signature/magic bytes for additional security
        image_signatures = {
            b"\xff\xd8\xff": "jpeg",
            b"\x89PNG\r\n\x1a\n": "png",
            b"GIF87a": "gif",
            b"GIF89a": "gif",
            b"WEBP": "webp",
        }

        file_header = content[:10]
        valid_signature = False

        for signature, _format_name in image_signatures.items():
            if file_header.startswith(signature) or signature in file_header[:8]:
                valid_signature = True
                break

        if not valid_signature:
            from hackathon.backend.simple_audit import log_security_event

            log_security_event(
                "invalid_file_signature", f"attempted upload with invalid image signature to submission {submission_id}"
            )
            raise HTTPException(status_code=400, detail="File does not appear to be a valid image format")

        # Verify and sanitize image using Pillow
        try:
            img = Image.open(BytesIO(content))
            img.verify()  # Verify image integrity
        except Exception:
            from hackathon.backend.simple_audit import log_security_event

            log_security_event("invalid_image", f"attempted upload of corrupted image to submission {submission_id}")
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

        # Re-open and validate image properties
        img = Image.open(BytesIO(content))

        # Check image dimensions for reasonableness
        MAX_DIMENSION = 4000  # 4000x4000 max
        MIN_DIMENSION = 50  # 50x50 min
        width, height = img.size

        if width > MAX_DIMENSION or height > MAX_DIMENSION:
            from hackathon.backend.simple_audit import log_security_event

            log_security_event(
                "image_too_large",
                f"attempted upload of {width}x{height} image to submission {submission_id} (max: {MAX_DIMENSION})",
            )
            raise HTTPException(
                status_code=400, detail=f"Image dimensions too large (max: {MAX_DIMENSION}x{MAX_DIMENSION})"
            )

        if width < MIN_DIMENSION or height < MIN_DIMENSION:
            from hackathon.backend.simple_audit import log_security_event

            log_security_event(
                "image_too_small",
                f"attempted upload of {width}x{height} image to submission {submission_id} (min: {MIN_DIMENSION})",
            )
            raise HTTPException(
                status_code=400, detail=f"Image dimensions too small (min: {MIN_DIMENSION}x{MIN_DIMENSION})"
            )

        # Check for and remove EXIF data for privacy/security
        if hasattr(img, "_getexif") and img._getexif():
            from hackathon.backend.simple_audit import log_security_event

            log_security_event(
                "exif_data_removed", f"removed EXIF data from image upload to submission {submission_id}"
            )

        # Convert to RGB for consistent JPEG output (removes EXIF data)
        img = img.convert("RGB")

        # Create uploads directory (consolidated location)
        uploads_dir = REPO_ROOT / "data" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename with .jpg extension
        import uuid

        unique_filename = f"{uuid.uuid4()}.jpg"
        file_path = uploads_dir / unique_filename

        # Save sanitized image as JPEG
        img.save(file_path, format="JPEG")

        # Return the file URL (relative to server)
        file_url = f"/api/uploads/{unique_filename}"

        print(f"✅ Image uploaded: {file_path} -> {file_url}")

        # Simple audit logging
        from hackathon.backend.simple_audit import log_user_action

        log_user_action("file_uploaded", discord_user.discord_id, submission_id)

        return {
            "success": True,
            "url": file_url,
            "filename": unique_filename,
            "size": file_path.stat().st_size,
        }

    except Exception as e:
        print(f"❌ Image upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {e!s}")


# Serve uploaded files
@app.get("/api/uploads/{filename}")
async def serve_upload(filename: str):
    """Serve uploaded files."""
    # Use consolidated uploads directory
    uploads_dir = (REPO_ROOT / "data" / "uploads").resolve()

    # Validate that the resolved path stays within the uploads directory
    try:
        candidate_path = (uploads_dir / filename).resolve()
        candidate_path.relative_to(uploads_dir)
    except Exception:
        # Path traversal or invalid path detected
        raise HTTPException(status_code=400, detail="Invalid file path")

    if not candidate_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Return file content with appropriate headers
    from fastapi.responses import FileResponse

    return FileResponse(candidate_path)


@app.get("/api/submission-schema", tags=["latest"], response_model=SubmissionSchemaResponse)
async def get_submission_schema_latest():
    fields = get_schema("v2")  # returns a list of field dicts
    window_info = get_submission_window_info()
    return SubmissionSchemaResponse(fields=fields, **window_info)


@app.get("/api/leaderboard", tags=["latest"], response_model=list[LeaderboardEntry])
async def get_leaderboard_latest():
    # Use v2 as the default version
    table = "hackathon_submissions_v2"
    with engine.connect() as conn:
        # Get each project's latest available round and score
        result = conn.execute(
            text(
                f"""
            WITH latest_scores AS (
                SELECT
                    sc.submission_id,
                    MAX(sc.round) as latest_round
                FROM hackathon_scores sc
                GROUP BY sc.submission_id
            ),
            project_scores AS (
                SELECT
                    sc.submission_id,
                    AVG(sc.weighted_total) as avg_score,
                    COUNT(DISTINCT sc.judge_name) as judge_count
                FROM hackathon_scores sc
                JOIN latest_scores ls ON sc.submission_id = ls.submission_id AND sc.round = ls.latest_round
                GROUP BY sc.submission_id
            ),
            community_scores AS (
                SELECT
                    CAST(ld.submission_id AS INTEGER) as submission_id,
                    COUNT(*) as total_reactions,
                    COUNT(DISTINCT ld.discord_id) as unique_voters,
                    SUM(CASE WHEN ld.action = 'like' THEN 1 ELSE 0 END) as likes,
                    SUM(CASE WHEN ld.action = 'dislike' THEN 1 ELSE 0 END) as dislikes,
                    -- Simple community score: likes ratio * 10
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            (SUM(CASE WHEN ld.action = 'like' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 10
                        ELSE 0
                    END as community_score
                FROM likes_dislikes ld
                GROUP BY ld.submission_id
            )
            SELECT
                s.submission_id,
                s.project_name,
                s.category,
                s.demo_video_url as youtube_url,
                s.status,
                ps.avg_score,
                COALESCE(cs.community_score, 0.0) as community_score,
                u.username as discord_handle,
                u.discord_id as discord_id,
                u.username as discord_username,
                u.avatar as discord_avatar
            FROM {table} s
            JOIN project_scores ps ON s.submission_id = ps.submission_id
            LEFT JOIN community_scores cs ON s.submission_id = cs.submission_id
            JOIN users u ON s.owner_discord_id = u.discord_id
            WHERE s.status IN ('scored', 'completed', 'published')
            ORDER BY ps.avg_score DESC
        """
            )
        )
        entries = []
        rank = 1
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            entry = LeaderboardEntry(
                rank=rank,
                submission_id=row_dict["submission_id"],
                project_name=row_dict["project_name"],
                category=row_dict["category"],
                final_score=round(row_dict["avg_score"] / 4, 1),  # Convert to 0-10 display scale
                community_score=round(row_dict.get("community_score", 0.0), 1),
                youtube_url=row_dict["youtube_url"],
                status=row_dict["status"],
                discord_handle=row_dict["discord_handle"],
                discord_id=row_dict.get("discord_id"),
                discord_username=row_dict.get("discord_username"),
                discord_avatar=row_dict.get("discord_avatar"),
            )
            entries.append(entry)
            rank += 1
        return entries


@app.get("/api/stats", tags=["latest"], response_model=StatsModel)
async def get_stats_latest():
    return await get_stats(version="v2")


@app.get("/api/config", tags=["latest"])
async def get_config():
    """Get configuration including submission deadline information."""
    info = get_submission_window_info()

    # Add grace period logic here (not in frontend)
    GRACE_PERIOD_MINUTES = 60  # 60 minutes grace (feeling generous!)
    grace_period = GRACE_PERIOD_MINUTES * 60
    if info["submission_deadline"]:
        deadline = datetime.fromisoformat(info["submission_deadline"])
        now = datetime.now(timezone.utc)
        info["can_submit"] = now < (deadline + timedelta(seconds=grace_period))
    else:
        info["can_submit"] = True

    # Add wallet and token configuration
    prize_wallet = os.getenv("PRIZE_WALLET_ADDRESS")
    if not prize_wallet:
        raise ValueError("PRIZE_WALLET_ADDRESS environment variable is required")
    info["prize_wallet_address"] = prize_wallet
    info["ai16z_mint"] = "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC"

    return info


@app.get("/api/test-voting", tags=["voting"])
async def test_voting():
    """Test endpoint to verify voting functionality works."""
    with engine.connect() as conn:
        # Simple test query
        result = conn.execute(text("SELECT COUNT(*) as count FROM sol_votes"))
        row = result.fetchone()
        return {"vote_count": row[0], "status": "working"}


@app.get("/api/community-scores", tags=["voting"])
async def get_community_scores():
    """Get community scores for all submissions based on token voting."""
    try:
        with engine.connect() as conn:
            # Get raw vote data grouped by wallet and submission
            result = conn.execute(
                text("""
                SELECT
                  submission_id,
                  sender,
                  SUM(amount) as total_tokens,
                  MAX(timestamp) as last_tx_time
                FROM sol_votes
                GROUP BY submission_id, sender
                """)
            )

            # Calculate vote weights in Python (inline to avoid scope issues)
            submission_scores = {}
            for row in result.fetchall():
                row_dict = dict(row._mapping)
                submission_id = row_dict["submission_id"]
                total_tokens = row_dict["total_tokens"]

                vote_weight = calculate_vote_weight(total_tokens)

                if submission_id not in submission_scores:
                    submission_scores[submission_id] = {"total_score": 0, "unique_voters": 0, "last_vote_time": 0}

                submission_scores[submission_id]["total_score"] += vote_weight
                submission_scores[submission_id]["unique_voters"] += 1
                submission_scores[submission_id]["last_vote_time"] = max(
                    submission_scores[submission_id]["last_vote_time"], row_dict["last_tx_time"]
                )

            # Format response
            scores = []
            for submission_id, data in submission_scores.items():
                scores.append(
                    {
                        "submission_id": submission_id,
                        "community_score": round(data["total_score"], 2),
                        "unique_voters": data["unique_voters"],
                        "last_vote_time": data["last_vote_time"],
                    }
                )

            return scores
    except Exception as e:
        logging.error(f"Error in community scores: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def get_recent_transactions_helius(wallet_address: str, helius_api_key: str, limit: int = 5):
    """Get recent transactions for wallet using Helius Enhanced Transactions API.

    NOTE: Helius RPC requires API key in URL (Solana RPC standard). This is server-side
    only and keys are never exposed to clients. Ensure access logs are secured.
    """
    import time

    import aiohttp

    try:
        # First get recent transaction signatures
        # SECURITY: API key in URL is required by Helius RPC - ensure logs don't expose keys
        helius_rpc_url = f"https://mainnet.helius-rpc.com/?api-key={helius_api_key}"

        async with aiohttp.ClientSession() as session:
            # Get recent transaction signatures
            rpc_payload = {
                "jsonrpc": "2.0",
                "id": "get-signatures",
                "method": "getSignaturesForAddress",
                "params": [
                    wallet_address,
                    {"limit": limit * 2},  # Get more to filter for incoming transfers
                ],
            }

            async with session.post(helius_rpc_url, json=rpc_payload) as resp:
                rpc_data = await resp.json()

            if "result" not in rpc_data or not rpc_data["result"]:
                return []

            # Extract transaction signatures
            signatures = [tx["signature"] for tx in rpc_data["result"][:limit]]

            if not signatures:
                return []

            # Get enhanced transaction data
            enhanced_url = f"https://api.helius.xyz/v0/transactions?api-key={helius_api_key}"
            enhanced_payload = {"transactions": signatures}

            async with session.post(enhanced_url, json=enhanced_payload) as resp:
                enhanced_data = await resp.json()

            # Process enhanced transactions into contributions
            contributions = []
            for tx in enhanced_data[:limit]:
                if not isinstance(tx, dict):
                    continue

                # Look for native (SOL) transfers TO our wallet
                if "nativeTransfers" in tx:
                    for transfer in tx["nativeTransfers"]:
                        if transfer.get("toUserAccount") == wallet_address:
                            contributions.append(
                                {
                                    "wallet": transfer.get("fromUserAccount", "Unknown")[:4]
                                    + "..."
                                    + transfer.get("fromUserAccount", "Unknown")[-4:]
                                    if transfer.get("fromUserAccount")
                                    else "Unknown",
                                    "token": "SOL",
                                    "amount": transfer.get("amount", 0) / 1_000_000_000,  # Convert lamports to SOL
                                    "timestamp": tx.get("timestamp", int(time.time())),
                                    "description": tx.get("description", "SOL transfer"),
                                }
                            )

                # Look for token transfers TO our wallet
                if "tokenTransfers" in tx:
                    for transfer in tx["tokenTransfers"]:
                        if transfer.get("toUserAccount") == wallet_address:
                            # Get token symbol from metadata or use mint short form
                            token_symbol = "Unknown"
                            if transfer.get("mint"):
                                # Try to get symbol from our token metadata cache
                                try:
                                    with engine.connect() as conn:
                                        result = conn.execute(
                                            text("SELECT symbol FROM token_metadata WHERE token_mint = :token_mint"),
                                            {"token_mint": transfer["mint"]},
                                        ).fetchone()
                                        token_symbol = result[0] if result else transfer["mint"][:8]
                                except Exception:
                                    token_symbol = transfer["mint"][:8]

                            contributions.append(
                                {
                                    "wallet": transfer.get("fromUserAccount", "Unknown")[:4]
                                    + "..."
                                    + transfer.get("fromUserAccount", "Unknown")[-4:]
                                    if transfer.get("fromUserAccount")
                                    else "Unknown",
                                    "token": token_symbol,
                                    "amount": transfer.get("tokenAmount", 0),
                                    "timestamp": tx.get("timestamp", int(time.time())),
                                    "description": tx.get("description", f"{token_symbol} transfer"),
                                }
                            )

            return contributions[:limit]  # Return only the requested number

    except Exception as e:
        logging.error(f"Error getting recent transactions: {e}")
        return []  # Return empty list on error to avoid breaking the API


@app.get("/api/prize-pool", tags=["voting"])
async def get_prize_pool():
    """Get crypto-native prize pool data using Helius DAS API."""
    try:
        helius_api_key = os.getenv("HELIUS_API_KEY")
        prize_wallet = os.getenv("PRIZE_WALLET_ADDRESS")
        if not prize_wallet:
            raise ValueError("PRIZE_WALLET_ADDRESS environment variable is required")
        target_sol = float(os.getenv("PRIZE_POOL_TARGET_SOL", 10))

        if not helius_api_key:
            raise HTTPException(status_code=500, detail="Helius API key not configured")

        helius_url = f"https://mainnet.helius-rpc.com/?api-key={helius_api_key}"

        # Fetch real-time token holdings from Helius DAS API
        payload = {
            "jsonrpc": "2.0",
            "id": "prize-pool-live",
            "method": "getAssetsByOwner",
            "params": {
                "ownerAddress": prize_wallet,
                "page": 1,
                "limit": 100,
                "sortBy": {"sortBy": "created", "sortDirection": "desc"},
                "options": {
                    "showUnverifiedCollections": False,
                    "showCollectionMetadata": False,
                    "showGrandTotal": False,
                    "showFungible": True,
                    "showNativeBalance": True,
                    "showInscription": False,
                    "showZeroBalance": False,
                },
            },
        }

        import json
        import time

        import requests

        response = requests.post(helius_url, json=payload)
        response.raise_for_status()
        data = response.json()

        if "error" in data:
            raise HTTPException(status_code=500, detail=f"Helius API error: {data['error']}")

        if not data.get("result", {}).get("items"):
            # Return empty but valid structure
            return {
                "total_sol": 0,
                "target_sol": target_sol,
                "progress_percentage": 0,
                "token_breakdown": {},
                "recent_contributions": [],
            }

        # Process tokens
        token_breakdown = {}
        total_sol = 0

        def get_token_metadata_from_helius(mint_address):
            """Fetch token metadata from Helius DAS API and cache it"""
            try:
                # Check cache first (24 hour cache)
                with engine.connect() as conn:
                    result = conn.execute(
                        text(
                            "SELECT * FROM token_metadata WHERE token_mint = :token_mint AND last_updated > :min_time"
                        ),
                        {"token_mint": mint_address, "min_time": int(time.time()) - 86400},  # 24 hours
                    )
                    cached = result.fetchone()
                    if cached:
                        return {
                            "symbol": cached[2],
                            "name": cached[3],
                            "decimals": cached[4],
                            "logo": cached[6] or cached[5],  # prefer cdn_uri over logo_uri
                            "interface": cached[8],
                        }

                # Fetch from Helius DAS API
                payload = {
                    "jsonrpc": "2.0",
                    "id": f"token-metadata-{mint_address}",
                    "method": "getAsset",
                    "params": {"id": mint_address},
                }

                response = requests.post(helius_url, json=payload)
                response.raise_for_status()
                asset_data = response.json()

                if "error" in asset_data or not asset_data.get("result"):
                    return None

                asset = asset_data["result"]

                # Extract metadata
                symbol = None
                name = None
                decimals = 6  # Default for SPL tokens
                logo_uri = None
                cdn_uri = None
                json_uri = None
                interface_type = asset.get("interface", "Unknown")

                # Get symbol and name from token_info or content
                if asset.get("token_info"):
                    symbol = asset["token_info"].get("symbol")
                    decimals = asset["token_info"].get("decimals", 6)

                if asset.get("content"):
                    content = asset["content"]
                    if not symbol and content.get("metadata"):
                        symbol = content["metadata"].get("symbol")
                        name = content["metadata"].get("name")

                    json_uri = content.get("json_uri")

                    # Get image URLs
                    if content.get("files") and len(content["files"]) > 0:
                        first_file = content["files"][0]
                        logo_uri = first_file.get("uri")
                        cdn_uri = first_file.get("cdn_uri")

                # Cache the metadata
                with engine.begin() as conn:
                    conn.execute(
                        text("""
                            INSERT OR REPLACE INTO token_metadata
                            (token_mint, symbol, name, decimals, logo_uri, cdn_uri, json_uri, interface_type, content_metadata, last_updated)
                            VALUES (:token_mint, :symbol, :name, :decimals, :logo_uri, :cdn_uri, :json_uri, :interface_type, :content_metadata, :last_updated)
                        """),
                        {
                            "token_mint": mint_address,
                            "symbol": symbol,
                            "name": name,
                            "decimals": decimals,
                            "logo_uri": logo_uri,
                            "cdn_uri": cdn_uri,
                            "json_uri": json_uri,
                            "interface_type": interface_type,
                            "content_metadata": json.dumps(asset.get("content", {})),
                            "last_updated": int(time.time()),
                        },
                    )

                return {
                    "symbol": symbol,
                    "name": name,
                    "decimals": decimals,
                    "logo": cdn_uri or logo_uri,  # prefer CDN
                    "interface": interface_type,
                }

            except Exception as e:
                logging.error(f"Error fetching token metadata for {mint_address}: {e}")
                return None

        # Process native SOL balance (special case - always has consistent metadata)
        native_balance = data["result"].get("nativeBalance", {})
        if native_balance and native_balance.get("lamports", 0) > 0:
            sol_amount = native_balance["lamports"] / 1_000_000_000
            total_sol = sol_amount
            token_breakdown["SOL"] = {
                "mint": "So11111111111111111111111111111111111111112",
                "symbol": "SOL",
                "name": "Solana",
                "amount": sol_amount,
                "decimals": 9,
                "logo": "https://raw.githubusercontent.com/solana-labs/token-list/main/assets/mainnet/So11111111111111111111111111111111111111112/logo.png",
            }

        # Process SPL tokens using enhanced metadata
        for asset in data["result"]["items"]:
            if asset.get("token_info") and float(asset["token_info"].get("balance", 0)) > 0:
                mint_address = asset["id"]
                raw_balance = float(asset["token_info"]["balance"])

                # Get enhanced metadata from Helius
                metadata = get_token_metadata_from_helius(mint_address)

                if metadata:
                    decimals = metadata.get("decimals", 6)
                    symbol = metadata.get("symbol") or mint_address[:8]
                    name = metadata.get("name")
                    logo = metadata.get("logo")
                else:
                    # Fallback to basic data from getAssetsByOwner
                    decimals = asset["token_info"].get("decimals", 6)
                    symbol = (
                        asset["token_info"].get("symbol")
                        or asset.get("content", {}).get("metadata", {}).get("symbol")
                        or mint_address[:8]
                    )
                    name = asset.get("content", {}).get("metadata", {}).get("name")
                    logo = None
                    if asset.get("content", {}).get("files"):
                        logo = asset["content"]["files"][0].get("cdn_uri") or asset["content"]["files"][0].get("uri")

                amount = raw_balance / (10**decimals)

                token_breakdown[symbol] = {
                    "mint": mint_address,
                    "symbol": symbol,
                    "name": name,
                    "amount": amount,
                    "decimals": decimals,
                    "logo": logo,
                }

        # Sort tokens: SOL, ai16z, USDC first, then by amount
        priority_tokens = ["SOL", "ai16z", "USDC"]
        sorted_tokens = {}

        # Add priority tokens first
        for token in priority_tokens:
            if token in token_breakdown:
                sorted_tokens[token] = token_breakdown[token]

        # Add remaining tokens sorted by amount
        remaining_tokens = {k: v for k, v in token_breakdown.items() if k not in priority_tokens}
        for token, data in sorted(remaining_tokens.items(), key=lambda x: x[1]["amount"], reverse=True):
            sorted_tokens[token] = data

        # Get recent transactions using Helius Enhanced Transactions API
        recent_contributions = await get_recent_transactions_helius(prize_wallet, helius_api_key)

        return {
            "total_sol": total_sol,
            "target_sol": target_sol,
            "progress_percentage": (total_sol / target_sol) * 100 if target_sol > 0 else 0,
            "token_breakdown": sorted_tokens,
            "recent_contributions": recent_contributions,
        }

    except Exception as e:
        logging.error(f"Error in prize pool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws/prize-pool")
async def websocket_prize_pool_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time prize pool updates."""
    try:
        await websocket.accept()
        await prize_pool_service.add_client(websocket)

        # Keep connection alive and handle disconnection
        try:
            while True:
                # Wait for any message from client (ping/pong or disconnect)
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass

    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        await prize_pool_service.remove_client(websocket)


def process_ai16z_transaction(tx_sig: str, submission_id: int, sender: str, amount: float):
    """Process ai16z token transaction for voting and prize pool."""
    try:
        # Calculate tokens used for voting vs overflow
        max_vote_tokens = float(os.getenv("MAX_VOTE_TOKENS", 100))
        vote_tokens = min(amount, max_vote_tokens)
        overflow_tokens = max(0, amount - max_vote_tokens)

        with engine.begin() as conn:
            # Record the vote in sol_votes table
            conn.execute(
                text("""
                    INSERT OR IGNORE INTO sol_votes
                    (tx_sig, submission_id, sender, amount, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """),
                (tx_sig, submission_id, sender, vote_tokens, int(time.time())),
            )

            # Record overflow as prize pool contribution
            if overflow_tokens > 0:
                conn.execute(
                    text("""
                        INSERT OR IGNORE INTO prize_pool_contributions
                        (tx_sig, token_mint, token_symbol, amount, contributor_wallet, source, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """),
                    (
                        f"{tx_sig}_overflow",  # Unique ID for overflow portion
                        "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC",  # ai16z mint
                        "ai16z",
                        overflow_tokens,
                        sender,
                        "vote_overflow",
                        int(time.time()),
                    ),
                )
            # Transaction automatically commits on context exit
            logging.info(f"Processed vote: {vote_tokens} ai16z vote, {overflow_tokens} ai16z to prize pool")
            return True

    except Exception as e:
        logging.error(f"Transaction processing error: {e}")
        return False


@app.post("/webhook/helius", tags=["voting"])
async def helius_webhook(request: Request):
    """Handle Helius webhook for Solana transaction processing."""
    try:
        data = await request.json()

        # Extract transaction details
        tx_sig = data.get("signature")
        if not tx_sig:
            logging.warning("Webhook received without transaction signature")
            return {"processed": 0, "error": "No transaction signature"}

        transfers = data.get("tokenTransfers", [])
        if not transfers:
            logging.warning(f"No token transfers in transaction {tx_sig}")
            return {"processed": 0, "error": "No token transfers"}

        processed_count = 0
        AI16Z_MINT = "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC"
        SOL_MINT = "So11111111111111111111111111111111111111112"

        for transfer in transfers:
            mint = transfer.get("mint")

            # Handle ai16z voting transactions
            if mint == AI16Z_MINT:
                submission_id = transfer.get("memo", "").strip()
                sender = transfer.get("fromUserAccount")
                amount = float(transfer.get("tokenAmount", 0))

                if submission_id and sender and amount >= 1:  # Minimum 1 ai16z
                    if process_ai16z_transaction(tx_sig, submission_id, sender, amount):
                        processed_count += 1
                else:
                    logging.warning(
                        f"Invalid ai16z transaction: submission_id={submission_id}, sender={sender}, amount={amount}"
                    )

            # Handle direct SOL donations to prize pool (no memo needed)
            elif mint == SOL_MINT:
                sender = transfer.get("fromUserAccount")
                amount = float(transfer.get("tokenAmount", 0))

                if sender and amount > 0:
                    try:
                        with engine.begin() as conn:
                            conn.execute(
                                text("""
                                    INSERT OR IGNORE INTO prize_pool_contributions
                                    (tx_sig, token_mint, token_symbol, amount, contributor_wallet, source, timestamp)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)
                                """),
                                (tx_sig, SOL_MINT, "SOL", amount, sender, "direct_donation", int(time.time())),
                            )
                            # Transaction automatically commits on context exit
                            processed_count += 1
                            logging.info(f"Processed SOL donation: {amount} SOL from {sender}")
                    except Exception as e:
                        logging.error(f"SOL donation processing error: {e}")

        return {"processed": processed_count, "signature": tx_sig}

    except Exception as e:
        logging.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/webhook/test", tags=["voting"])
async def test_webhook():
    """Test endpoint to simulate a Helius webhook payload."""
    # Simulate a test ai16z transaction with vote overflow
    test_payload = {
        "signature": "test_tx_sig_webhook_123",
        "tokenTransfers": [
            {
                "mint": "HeLp6NuQkmYB4pYWo2zYs22mESHXPQYzXbB8n4V98jwC",  # ai16z
                "memo": "test-submission-1",
                "fromUserAccount": "wallet_webhook_test",
                "tokenAmount": 150.0,  # 150 ai16z - should split into 100 vote + 50 overflow
            }
        ],
    }

    # Process the transaction directly
    try:
        tx_sig = test_payload["signature"]
        transfer = test_payload["tokenTransfers"][0]
        submission_id = transfer["memo"]
        sender = transfer["fromUserAccount"]
        amount = transfer["tokenAmount"]

        success = process_ai16z_transaction(tx_sig, submission_id, sender, amount)

        return {
            "test_payload": test_payload,
            "processing_result": {"processed": 1 if success else 0, "signature": tx_sig},
            "status": "Test webhook processed successfully" if success else "Test webhook failed",
        }
    except Exception as e:
        return {"test_payload": test_payload, "error": str(e), "status": "Test webhook failed"}


# Community voting endpoints (must be before versioned routes)
@app.get("/api/community-votes/stats", tags=["voting"])
async def get_vote_stats():
    """Get overall community voting statistics."""
    try:
        from hackathon.backend.collect_votes import VoteProcessor

        processor = VoteProcessor(HACKATHON_DB_PATH)
        stats = processor.get_vote_stats()
        return stats
    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        logging.error(f"Error getting vote stats: {e}\n{error_details}")
        raise HTTPException(status_code=500, detail=f"Failed to get vote statistics: {e!s}")


@app.get("/api/community-votes/scores", tags=["voting"])
async def get_community_vote_scores():
    """Get community scores for all submissions."""
    try:
        from hackathon.backend.collect_votes import VoteProcessor

        processor = VoteProcessor(HACKATHON_DB_PATH)
        scores = processor.get_community_scores()
        return scores
    except Exception as e:
        logging.error(f"Error getting community scores: {e}")
        raise HTTPException(status_code=500, detail="Failed to get community scores")


@app.get("/api/submissions/{submission_id}/votes", tags=["voting"])
async def get_submission_votes(submission_id: int):
    """Get voting details for a specific submission."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                transaction_signature,
                sender_address,
                amount,
                timestamp,
                processed_at
            FROM community_votes
            WHERE submission_id = ?
            ORDER BY timestamp DESC
            """,
            (submission_id,),
        )

        votes = []
        for row in cursor.fetchall():
            sig, sender, amount, timestamp, processed_at = row
            votes.append(
                {
                    "transaction_signature": sig,
                    "sender_address": sender,
                    "amount": amount,
                    "timestamp": timestamp,
                    "processed_at": processed_at,
                }
            )

        conn.close()

        # Calculate summary stats
        if votes:
            total_amount = sum(vote["amount"] for vote in votes)
            unique_voters = len(set(vote["sender_address"] for vote in votes))
            avg_amount = total_amount / len(votes)
        else:
            total_amount = unique_voters = avg_amount = 0

        return {
            "submission_id": submission_id,
            "vote_count": len(votes),
            "unique_voters": unique_voters,
            "total_amount": total_amount,
            "avg_amount": avg_amount,
            "votes": votes,
        }

    except Exception as e:
        logging.error(f"Error getting votes for {submission_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get submission votes")


@app.get(
    "/api/{version}/submissions",
    tags=["versioned"],
    response_model=list[SubmissionSummary],
)
async def list_submissions(
    version: str = "v1",
    include: str = "scores,research,community",
    status: str | None = None,
    category: str | None = None,
    detail: bool = False,
):
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    table = f"hackathon_submissions_{version}"
    from hackathon.backend.schema import get_database_field_names

    # Get only database fields (excludes UI-only fields like 'invite_code')
    db_field_names = get_database_field_names(version)
    base_fields = ["submission_id", *db_field_names, "status", "created_at", "updated_at"]
    # If detail is requested, ensure extended fields are present
    extended_detail_fields = [
        "github_url",
        "demo_video_url",
        "project_image",
        "problem_solved",
        "favorite_part",
        "solana_address",
    ]
    if detail:
        # Use set to avoid duplicates and only include fields that exist in schema/db
        fields = [f for f in base_fields]
        for f in extended_detail_fields:
            if f not in fields:
                fields.append(f)
    else:
        fields = base_fields

    # Build WHERE clause for filtering
    where_conditions = []
    params = {}
    if status:
        where_conditions.append("status = :status")
        params["status"] = status
    if category:
        where_conditions.append("category = :category")
        params["category"] = category

    where_clause = f" WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
    # Join users table for Discord info
    select_stmt = text(f"""
        SELECT {", ".join([f"s.{f}" for f in fields])},
               u.discord_id AS discord_id,
               u.username AS discord_username,
               u.discriminator AS discord_discriminator,
               u.avatar AS discord_avatar
        FROM {table} s
        LEFT JOIN users u ON s.owner_discord_id = u.discord_id
        {where_clause}
    """)

    with engine.connect() as conn:
        result = conn.execute(select_stmt, params)
        submissions = []
        include_parts = set(i.strip() for i in include.split(",") if i.strip())
        for submission_row in result.fetchall():
            submission_dict = dict(submission_row._mapping)
            submission_id = submission_dict["submission_id"]
            # Always calculate score aggregates for SubmissionSummary - use latest round
            scores_agg_result = conn.execute(
                text(
                    """
                WITH latest_round AS (
                    SELECT MAX(round) as max_round
                    FROM hackathon_scores
                    WHERE submission_id = :submission_id
                )
                SELECT AVG(weighted_total) as avg_score, COUNT(DISTINCT judge_name) as judge_count
                FROM hackathon_scores sc
                JOIN latest_round lr ON sc.round = lr.max_round
                WHERE sc.submission_id = :submission_id
            """
                ),
                {"submission_id": submission_id},
            )
            agg_row = scores_agg_result.fetchone()
            if agg_row and agg_row[0] is not None:
                submission_dict["avg_score"] = round(float(agg_row[0]) / 4, 1)  # Scale to 0-10 range
                submission_dict["judge_count"] = int(agg_row[1])
            else:
                submission_dict["avg_score"] = None
                submission_dict["judge_count"] = 0

            # Optionally add scores
            if "scores" in include_parts:
                score_fields = [
                    "judge_name",
                    "innovation",
                    "technical_execution",
                    "market_potential",
                    "user_experience",
                    "weighted_total",
                    "notes",
                    "round",
                    "community_bonus",
                    "final_verdict",
                ]
                actual_score_fields = get_score_columns(conn, score_fields)
                if actual_score_fields:
                    scores_result = conn.execute(
                        text(
                            f"SELECT {', '.join(actual_score_fields)} FROM hackathon_scores WHERE submission_id = :submission_id ORDER BY judge_name, round"
                        ),
                        {"submission_id": submission_id},
                    )
                    scores = []
                    for score_row in scores_result.fetchall():
                        score_dict = dict(score_row._mapping)
                        if "notes" in score_dict:
                            try:
                                score_dict["notes"] = json.loads(score_dict["notes"]) if score_dict["notes"] else {}
                            except (json.JSONDecodeError, TypeError):
                                # Handle plain text notes from database seeder
                                score_dict["notes"] = {"raw": score_dict["notes"]} if score_dict["notes"] else {}
                        scores.append(score_dict)
                    submission_dict["scores"] = scores
                else:
                    submission_dict["scores"] = []
            # Optionally add research
            if "research" in include_parts:
                research_result = conn.execute(
                    text(
                        """
                    SELECT github_analysis, market_research, technical_assessment
                    FROM hackathon_research
                    WHERE submission_id = :submission_id
                """
                    ),
                    {"submission_id": submission_id},
                )
                research_row = research_result.fetchone()
                if research_row:
                    research_dict = dict(research_row._mapping)
                    research = {
                        "github_analysis": (
                            json.loads(research_dict["github_analysis"]) if research_dict["github_analysis"] else None
                        ),
                        "market_research": (
                            json.loads(research_dict["market_research"]) if research_dict["market_research"] else None
                        ),
                        "technical_assessment": (
                            json.loads(research_dict["technical_assessment"])
                            if research_dict["technical_assessment"]
                            else None
                        ),
                    }
                    submission_dict["research"] = research
                else:
                    submission_dict["research"] = None
            # Optionally add community feedback
            if "community" in include_parts:
                feedback_result = conn.execute(
                    text(
                        """
                    SELECT
                        reaction_type,
                        COUNT(*) as vote_count,
                        GROUP_CONCAT(discord_user_nickname) as voters
                    FROM community_feedback
                    WHERE submission_id = :submission_id
                    GROUP BY reaction_type
                    ORDER BY vote_count DESC
                """
                    ),
                    {"submission_id": submission_id},
                )
                feedback_summary = []
                total_votes = 0
                for row in feedback_result.fetchall():
                    row_dict = dict(row._mapping)
                    reaction_type, vote_count, voters = (
                        row_dict["reaction_type"],
                        row_dict["vote_count"],
                        row_dict["voters"],
                    )
                    total_votes += vote_count
                    feedback_summary.append(
                        {
                            "reaction_type": reaction_type,
                            "vote_count": vote_count,
                            "voters": voters.split(",") if voters else [],
                        }
                    )
                submission_dict["community_feedback"] = {
                    "total_votes": total_votes,
                    "feedback": feedback_summary,
                }
            # For summary responses, remove free-form handle to avoid duplication
            if not detail:
                submission_dict.pop("discord_handle", None)
            submissions.append(submission_dict)
    return submissions


@app.get(
    "/api/{version}/submissions/{submission_id}",
    tags=["versioned"],
    response_model=SubmissionDetail,
)
async def get_submission_versioned(
    version: str,
    submission_id: int,
    request: Request,
    include: str = "scores,research,community",
):
    return await get_submission(submission_id=submission_id, version=version, include=include, request=request)


@app.get(
    "/api/{version}/submission-schema",
    tags=["versioned"],
    response_model=list[SubmissionFieldSchema],
)
async def get_submission_schema_versioned(version: str):
    if version in ("v1", "v2"):
        return JSONResponse(content=get_schema(version))
    # Add more versions as needed
    raise HTTPException(status_code=404, detail="Schema version not found")


@app.get(
    "/api/{version}/leaderboard",
    tags=["versioned"],
    response_model=list[LeaderboardEntry],
)
async def get_leaderboard(version: str):
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    table = f"hackathon_submissions_{version}"
    with engine.connect() as conn:
        # Get each project's latest available round and score
        result = conn.execute(
            text(
                f"""
            WITH latest_scores AS (
                SELECT
                    sc.submission_id,
                    MAX(sc.round) as latest_round
                FROM hackathon_scores sc
                GROUP BY sc.submission_id
            ),
            project_scores AS (
                SELECT
                    sc.submission_id,
                    AVG(sc.weighted_total) as avg_score,
                    COUNT(DISTINCT sc.judge_name) as judge_count
                FROM hackathon_scores sc
                JOIN latest_scores ls ON sc.submission_id = ls.submission_id AND sc.round = ls.latest_round
                GROUP BY sc.submission_id
            )
            SELECT
                s.submission_id,
                s.project_name,
                s.category,
                s.demo_video_url as youtube_url,
                s.status,
                ps.avg_score,
                u.username as discord_handle,
                u.discord_id as discord_id,
                u.username as discord_username,
                u.avatar as discord_avatar
            FROM {table} s
            JOIN project_scores ps ON s.submission_id = ps.submission_id
            JOIN users u ON s.owner_discord_id = u.discord_id
            WHERE s.status IN ('scored', 'completed', 'published')
            ORDER BY ps.avg_score DESC
        """
            )
        )
        entries = []
        rank = 1
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            entry = LeaderboardEntry(
                rank=rank,
                submission_id=row_dict["submission_id"],
                project_name=row_dict["project_name"],
                category=row_dict["category"],
                final_score=round(row_dict["avg_score"], 2),
                youtube_url=row_dict["youtube_url"],
                status=row_dict["status"],
                discord_handle=row_dict["discord_handle"],
                discord_id=row_dict.get("discord_id"),
                discord_username=row_dict.get("discord_username"),
                discord_avatar=row_dict.get("discord_avatar"),
            )
            entries.append(entry)
            rank += 1
        return entries


@app.get("/api/{version}/stats", tags=["versioned"], response_model=StatsModel)
async def get_stats(version: str):
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    table = f"hackathon_submissions_{version}"
    with engine.connect() as conn:
        # Count by status
        status_result = conn.execute(
            text(
                f"""
            SELECT status, COUNT(*) as count
            FROM {table}
            GROUP BY status
        """
            )
        )
        status_counts = {row[0]: row[1] for row in status_result.fetchall()}
        # Count by category
        category_result = conn.execute(
            text(
                f"""
            SELECT category, COUNT(*) as count
            FROM {table}
            GROUP BY category
        """
            )
        )
        category_counts = {row[0]: row[1] for row in category_result.fetchall()}
        # Total submissions
        total_result = conn.execute(text(f"SELECT COUNT(*) as total FROM {table}"))
        total = total_result.scalar_one()
        return {
            "total_submissions": total,
            "by_status": status_counts,
            "by_category": category_counts,
            "updated_at": datetime.now().isoformat(),
        }


@app.get("/api/feedback/{submission_id}", tags=["latest"], response_model=FeedbackSummary)
async def get_feedback_latest(submission_id: int):
    return await get_feedback_versioned(version="v2", submission_id=submission_id)


@app.get(
    "/api/{version}/feedback/{submission_id}",
    tags=["versioned"],
    response_model=FeedbackSummary,
)
async def get_feedback_versioned(version: str, submission_id: int):
    # Only v2 supported for now
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    with engine.connect() as conn:
        result = conn.execute(
            text(
                """
            SELECT
                reaction_type,
                COUNT(*) as vote_count,
                GROUP_CONCAT(discord_user_nickname) as voters
            FROM community_feedback
            WHERE submission_id = :submission_id
            GROUP BY reaction_type
            ORDER BY vote_count DESC
        """
            ),
            {"submission_id": submission_id},
        )
        feedback_summary = []
        total_votes = 0
        reaction_map = {
            "hype": {"emoji": "🔥", "name": "General Hype"},
            "innovation_creativity": {"emoji": "💡", "name": "Innovation & Creativity"},
            "technical_execution": {"emoji": "💻", "name": "Technical Execution"},
            "market_potential": {"emoji": "📈", "name": "Market Potential"},
            "user_experience": {"emoji": "😍", "name": "User Experience"},
        }
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            reaction_type, vote_count, voters = (
                row_dict["reaction_type"],
                row_dict["vote_count"],
                row_dict["voters"],
            )
            total_votes += vote_count
            reaction_info = reaction_map.get(reaction_type, {"emoji": "❓", "name": reaction_type})
            feedback_summary.append(
                FeedbackItem(
                    reaction_type=reaction_type,
                    emoji=reaction_info["emoji"],
                    name=reaction_info["name"],
                    vote_count=vote_count,
                    voters=voters.split(",") if voters else [],
                )
            )
        return FeedbackSummary(
            submission_id=submission_id,
            total_votes=total_votes,
            feedback=feedback_summary,
        )


# Hide the old feedback endpoint from docs
@app.get("/api/submission/{submission_id}/feedback", include_in_schema=False)
async def get_feedback_legacy(submission_id: int):
    return await get_feedback_latest(submission_id=submission_id)


def generate_static_data():
    """Generate static JSON files for static site deployment."""
    print("Generating static data files...")

    # Create output directory
    output_dir = Path(STATIC_DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)

    with engine.connect() as conn:
        # Generate submissions.json
        result = conn.execute(
            text(
                """
            SELECT
                s.submission_id,
                s.project_name,
                s.category,
                s.status,
                s.created_at,
                s.project_image,
                s.owner_discord_id as discord_id,
                u.avatar as discord_avatar,
                AVG(sc.weighted_total) as avg_score,
                COUNT(DISTINCT sc.judge_name) as judge_count,
                u.username as discord_handle
            FROM hackathon_submissions_v2 s
            LEFT JOIN hackathon_scores sc ON s.submission_id = sc.submission_id AND sc.round = 1
            JOIN users u ON s.owner_discord_id = u.discord_id
            GROUP BY s.submission_id
            ORDER BY s.created_at DESC
        """
            )
        )

        submissions = []
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            submissions.append(
                {
                    "submission_id": row_dict["submission_id"],
                    "project_name": row_dict["project_name"],
                    "category": row_dict["category"],
                    "status": row_dict["status"],
                    "created_at": row_dict["created_at"],
                    "avg_score": (round(row_dict["avg_score"], 2) if row_dict["avg_score"] else None),
                    "judge_count": (row_dict["judge_count"] if row_dict["judge_count"] else 0),
                    "discord_handle": row_dict["discord_handle"],
                    "discord_username": row_dict["discord_handle"],
                    "discord_id": row_dict.get("discord_id"),
                    "discord_avatar": row_dict.get("discord_avatar"),
                    "project_image": row_dict.get("project_image"),
                }
            )

        with open(output_dir / "submissions.json", "w") as f:
            json.dump(submissions, f, indent=2)

        print(f"Generated submissions.json with {len(submissions)} entries")

        # Generate individual submission files
        submission_dir = output_dir / "submission"
        submission_dir.mkdir(exist_ok=True)

        for submission in submissions:
            sid = submission["submission_id"]
            details_result = conn.execute(
                text(
                    "SELECT s.*, u.avatar as discord_avatar FROM hackathon_submissions_v2 s "
                    "JOIN users u ON s.owner_discord_id = u.discord_id "
                    "WHERE s.submission_id = :submission_id"
                ),
                {"submission_id": sid},
            )
            details = details_result.fetchone()
            detail_dict = dict(details._mapping)
            # Add frontend-expected field aliases
            detail_dict["discord_id"] = detail_dict.get("owner_discord_id")
            detail_dict["discord_username"] = detail_dict.get("discord_handle")

            # --- Scores ---
            score_fields = [
                "judge_name",
                "innovation",
                "technical_execution",
                "market_potential",
                "user_experience",
                "weighted_total",
                "notes",
                "round",
                "community_bonus",
                "final_verdict",
                "created_at",
            ]
            actual_score_fields = get_score_columns(conn, score_fields)
            if actual_score_fields:
                scores_result = conn.execute(
                    text(
                        f"""
                        SELECT {", ".join(actual_score_fields)} FROM (
                            SELECT {", ".join(actual_score_fields)},
                                   ROW_NUMBER() OVER (PARTITION BY judge_name, round ORDER BY created_at DESC) as rn
                            FROM hackathon_scores
                            WHERE submission_id = :submission_id
                        ) ranked_scores
                        WHERE rn = 1
                        ORDER BY judge_name, round
                        """
                    ),
                    {"submission_id": sid},
                )
                scores = []
                for score_row in scores_result.fetchall():
                    score_dict = dict(score_row._mapping)
                    if "notes" in score_dict:
                        try:
                            score_dict["notes"] = json.loads(score_dict["notes"]) if score_dict["notes"] else {}
                        except (json.JSONDecodeError, TypeError):
                            score_dict["notes"] = {"raw": score_dict["notes"]} if score_dict["notes"] else {}
                    scores.append(score_dict)
                detail_dict["scores"] = scores
            else:
                detail_dict["scores"] = []

            # --- Avg score ---
            avg_result = conn.execute(
                text(
                    "SELECT AVG(weighted_total) as avg_score FROM hackathon_scores WHERE submission_id = :submission_id"
                ),
                {"submission_id": sid},
            )
            avg_row = avg_result.fetchone()
            detail_dict["avg_score"] = round(avg_row.avg_score, 2) if avg_row and avg_row.avg_score else None

            # --- Research ---
            research_result = conn.execute(
                text(
                    "SELECT github_analysis, market_research, technical_assessment "
                    "FROM hackathon_research WHERE submission_id = :submission_id"
                ),
                {"submission_id": sid},
            )
            research_row = research_result.fetchone()
            if research_row:
                r = dict(research_row._mapping)
                detail_dict["research"] = {
                    "github_analysis": json.loads(r["github_analysis"]) if r["github_analysis"] else None,
                    "market_research": None,  # Deprecated: included in technical_assessment
                    "technical_assessment": json.loads(r["technical_assessment"])
                    if r["technical_assessment"]
                    else None,
                }
            else:
                detail_dict["research"] = None

            # --- Community score / likes / dislikes ---
            community_result = conn.execute(
                text(
                    """
                    SELECT
                        SUM(CASE WHEN action = 'like' THEN 1 ELSE 0 END) as likes,
                        SUM(CASE WHEN action = 'dislike' THEN 1 ELSE 0 END) as dislikes,
                        CASE WHEN COUNT(*) > 0 THEN
                            (SUM(CASE WHEN action = 'like' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 10
                        ELSE 0 END as community_score
                    FROM likes_dislikes
                    WHERE CAST(submission_id AS INTEGER) = :submission_id
                    """
                ),
                {"submission_id": sid},
            )
            community_row = community_result.fetchone()
            if community_row:
                detail_dict["likes"] = community_row.likes or 0
                detail_dict["dislikes"] = community_row.dislikes or 0
                detail_dict["community_score"] = round(community_row.community_score or 0.0, 1)
            else:
                detail_dict["likes"] = 0
                detail_dict["dislikes"] = 0
                detail_dict["community_score"] = 0.0

            # --- Static flags ---
            detail_dict["can_edit"] = False
            detail_dict["is_creator"] = False

            with open(submission_dir / f"{sid}.json", "w") as f:
                json.dump(detail_dict, f, indent=2)

        # Generate leaderboard.json
        leaderboard_result = conn.execute(
            text(
                """
            SELECT
                s.submission_id,
                s.project_name,
                s.category,
                s.demo_video_url as youtube_url,
                s.status,
                s.owner_discord_id as discord_id,
                u.avatar as discord_avatar,
                AVG(sc.weighted_total) as avg_score,
                u.username as discord_handle
            FROM hackathon_submissions_v2 s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            JOIN users u ON s.owner_discord_id = u.discord_id
            WHERE s.status IN ('scored', 'completed', 'published') AND sc.round = 1
            GROUP BY s.submission_id
            ORDER BY avg_score DESC
        """
            )
        )
        leaderboard = []
        rank = 1
        for row in leaderboard_result.fetchall():
            row_dict = dict(row._mapping)
            leaderboard.append(
                {
                    "rank": rank,
                    "submission_id": row_dict["submission_id"],
                    "project_name": row_dict["project_name"],
                    "category": row_dict["category"],
                    "final_score": round(row_dict["avg_score"], 2),
                    "youtube_url": row_dict["youtube_url"],
                    "status": row_dict["status"],
                    "discord_handle": row_dict["discord_handle"],
                    "discord_id": row_dict.get("discord_id"),
                    "discord_avatar": row_dict.get("discord_avatar"),
                    "discord_username": row_dict["discord_handle"],
                }
            )
            rank += 1
        with open(output_dir / "leaderboard.json", "w") as f:
            json.dump(leaderboard, f, indent=2)
        print(f"Generated leaderboard.json with {len(leaderboard)} entries")

        # Generate stats.json
        stats = {
            "total_submissions": len(submissions),
            "by_status": {},
            "by_category": {},
            "generated_at": datetime.now().isoformat(),
        }

        for submission in submissions:
            status = submission["status"]
            category = submission["category"]

            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1

        with open(output_dir / "stats.json", "w") as f:
            json.dump(stats, f, indent=2)

        # Generate config.json
        config = {
            "submission_deadline": None,
            "current_time": datetime.now().isoformat(),
            "can_submit": False,
            "submission_window_open": False,
        }
        with open(output_dir / "config.json", "w") as f:
            json.dump(config, f, indent=2)

        # Generate /api/ mirror for static site (so /api/*.json paths work)
        api_dir = output_dir.parent / "api"
        api_dir.mkdir(parents=True, exist_ok=True)

        # Copy top-level JSON files to api/
        for json_file in ["submissions.json", "leaderboard.json", "stats.json"]:
            src = output_dir / json_file
            if src.exists():
                shutil.copy2(src, api_dir / json_file)

        # Copy individual submission files to api/submissions/{id}.json
        api_submissions_dir = api_dir / "submissions"
        api_submissions_dir.mkdir(exist_ok=True)
        src_submission_dir = output_dir / "submission"
        if src_submission_dir.exists():
            for f in src_submission_dir.glob("*.json"):
                shutil.copy2(f, api_submissions_dir / f.name)

        # Generate index.html listing available endpoints
        index_html = """<!DOCTYPE html>
<html><head><title>Clank Tank API</title></head>
<body>
<h1>Clank Tank Static API</h1>
<ul>
<li><a href="submissions.json">/api/submissions.json</a></li>
<li><a href="leaderboard.json">/api/leaderboard.json</a></li>
<li><a href="stats.json">/api/stats.json</a></li>
</ul>
</body></html>"""
        with open(api_dir / "index.html", "w") as f:
            f.write(index_html)

        print(f"Generated /api/ mirror with {len(list(api_dir.glob('*.json')))} top-level files")
        print("Static data generation complete!")


@app.post("/api/v1/submissions", status_code=410, include_in_schema=False)
@conditional_rate_limit("5/minute")
async def deprecated_post_v1_submissions(request: Request, *args, **kwargs):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint is deprecated. Use /api/submissions.",
    )


@app.post("/api/v2/submissions", status_code=410, include_in_schema=False)
@conditional_rate_limit("5/minute")
async def deprecated_post_v2_submissions(request: Request, *args, **kwargs):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint is deprecated. Use /api/submissions.",
    )


def main():
    """Main function to run the API server or generate static data."""
    parser = argparse.ArgumentParser(description="Hackathon Dashboard API")
    parser.add_argument(
        "--generate-static-data",
        action="store_true",
        help="Generate static JSON files instead of running the server",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")

    args = parser.parse_args()

    # Check if database exists
    if not os.path.exists(HACKATHON_DB_PATH):
        print(f"ERROR: Database not found at {HACKATHON_DB_PATH}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Repository root: {REPO_ROOT}")
        print("\nPlease ensure:")
        print("1. You have run the database creation script:")
        print("   python scripts/hackathon/create_hackathon_db.py")
        print("2. The database exists at: data/hackathon.db")
        print("\nOr set HACKATHON_DB_PATH environment variable to the correct path.")
        return

    if args.generate_static_data:
        generate_static_data()
    else:
        # Create users table for Discord OAuth
        create_users_table()

        print(f"Starting FastAPI server on http://{args.host}:{args.port}")
        print(f"API documentation available at http://{args.host}:{args.port}/docs")
        print(f"Using database: {HACKATHON_DB_PATH}")
        print(f"Database absolute path: {os.path.abspath(HACKATHON_DB_PATH)}")
        print(f"Database exists: {os.path.exists(HACKATHON_DB_PATH)}")
        print(f"Current working directory: {os.getcwd()}")
        print(f"Discord OAuth configured: {bool(DISCORD_CLIENT_ID)}")

        # Debug: Check what columns SQLAlchemy sees
        try:
            from sqlalchemy import inspect

            inspector = inspect(engine)
            columns = inspector.get_columns("hackathon_submissions_v2")
            column_names = [col["name"] for col in columns]
            print(f"SQLAlchemy sees columns: {column_names}")
            print(f"SQLAlchemy sees project_image: {'project_image' in column_names}")
            print(f"SQLAlchemy sees image_url: {'image_url' in column_names}")
        except Exception as e:
            print(f"Error checking columns: {e}")

        uvicorn.run(app, host=args.host, port=args.port)


async def get_submission(
    submission_id: int,
    version: str = "v1",
    include: str = "scores,research,community",
    request: Request = None,
):
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    table = f"hackathon_submissions_{version}"
    from hackathon.backend.schema import get_database_field_names

    # Get only database fields (excludes UI-only fields like 'invite_code')
    db_field_names = get_database_field_names(version)
    fields = ["submission_id", *db_field_names, "status", "created_at", "updated_at"]

    # project_image field is handled properly via schema
    # Join users to include Discord info for detail view
    select_stmt = text(
        f"""
        SELECT {", ".join([f"s.{f}" for f in fields])},
               u.discord_id AS discord_id,
               u.username AS discord_username,
               u.avatar AS discord_avatar
        FROM {table} s
        LEFT JOIN users u
          ON (
               s.owner_discord_id = u.discord_id
               OR (
                    s.owner_discord_id IS NULL
                AND u.username IS NOT NULL
                AND s.discord_handle IS NOT NULL
                AND LOWER(u.username) = LOWER(s.discord_handle)
               )
             )
        WHERE s.submission_id = :submission_id
        """
    )
    with engine.connect() as conn:
        result = conn.execute(select_stmt, {"submission_id": submission_id})
        submission_row = result.fetchone()
        if not submission_row:
            raise HTTPException(status_code=404, detail="Submission not found")
        submission_dict = dict(submission_row._mapping)
        include_parts = set(i.strip() for i in include.split(",") if i.strip())
        # Optionally add scores
        if "scores" in include_parts:
            score_fields = [
                "judge_name",
                "innovation",
                "technical_execution",
                "market_potential",
                "user_experience",
                "weighted_total",
                "notes",
                "round",
                "community_bonus",
                "final_verdict",
                "created_at",
            ]
            actual_score_fields = get_score_columns(conn, score_fields)
            if actual_score_fields:
                # Get only the latest score per judge per round using window functions
                scores_result = conn.execute(
                    text(
                        f"""
                        SELECT {", ".join(actual_score_fields)} FROM (
                            SELECT {", ".join(actual_score_fields)},
                                   ROW_NUMBER() OVER (PARTITION BY judge_name, round ORDER BY created_at DESC) as rn
                            FROM hackathon_scores
                            WHERE submission_id = :submission_id
                        ) ranked_scores
                        WHERE rn = 1
                        ORDER BY judge_name, round
                        """
                    ),
                    {"submission_id": submission_id},
                )
                scores = []
                for score_row in scores_result.fetchall():
                    score_dict = dict(score_row._mapping)
                    if "notes" in score_dict:
                        try:
                            score_dict["notes"] = json.loads(score_dict["notes"]) if score_dict["notes"] else {}
                        except (json.JSONDecodeError, TypeError):
                            # Handle plain text notes from database seeder
                            score_dict["notes"] = {"raw": score_dict["notes"]} if score_dict["notes"] else {}
                    scores.append(score_dict)
                submission_dict["scores"] = scores
            else:
                submission_dict["scores"] = []
        # Optionally add research
        if "research" in include_parts:
            research_result = conn.execute(
                text(
                    """
                SELECT github_analysis, market_research, technical_assessment
                FROM hackathon_research
                WHERE submission_id = :submission_id
            """
                ),
                {"submission_id": submission_id},
            )
            research_row = research_result.fetchone()
            if research_row:
                research_dict = dict(research_row._mapping)
                research = {
                    "github_analysis": (
                        json.loads(research_dict["github_analysis"]) if research_dict["github_analysis"] else None
                    ),
                    "market_research": (
                        json.loads(research_dict["market_research"]) if research_dict["market_research"] else None
                    ),
                    "technical_assessment": (
                        json.loads(research_dict["technical_assessment"])
                        if research_dict["technical_assessment"]
                        else None
                    ),
                }
                submission_dict["research"] = research
            else:
                submission_dict["research"] = None
        # Optionally add community feedback and score
        if "community" in include_parts:
            # Get community feedback (legacy table)
            feedback_result = conn.execute(
                text(
                    """
                SELECT
                    reaction_type,
                    COUNT(*) as vote_count,
                    GROUP_CONCAT(discord_user_nickname) as voters
                FROM community_feedback
                WHERE submission_id = :submission_id
                GROUP BY reaction_type
                ORDER BY vote_count DESC
            """
                ),
                {"submission_id": submission_id},
            )
            feedback_summary = []
            total_votes = 0
            for row in feedback_result.fetchall():
                row_dict = dict(row._mapping)
                reaction_type, vote_count, voters = (
                    row_dict["reaction_type"],
                    row_dict["vote_count"],
                    row_dict["voters"],
                )
                total_votes += vote_count
                feedback_summary.append(
                    {
                        "reaction_type": reaction_type,
                        "vote_count": vote_count,
                        "voters": voters.split(",") if voters else [],
                    }
                )
            submission_dict["community_feedback"] = {
                "total_votes": total_votes,
                "feedback": feedback_summary,
            }

            # Get community score from like/dislike votes
            community_score_result = conn.execute(
                text(
                    """
                SELECT
                    COUNT(*) as total_reactions,
                    COUNT(DISTINCT discord_id) as unique_voters,
                    SUM(CASE WHEN action = 'like' THEN 1 ELSE 0 END) as likes,
                    SUM(CASE WHEN action = 'dislike' THEN 1 ELSE 0 END) as dislikes,
                    CASE
                        WHEN COUNT(*) > 0 THEN
                            (SUM(CASE WHEN action = 'like' THEN 1.0 ELSE 0.0 END) / COUNT(*)) * 10
                        ELSE 0
                    END as community_score
                FROM likes_dislikes
                WHERE CAST(submission_id AS INTEGER) = :submission_id
                """
                ),
                {"submission_id": submission_id},
            )
            community_score_row = community_score_result.fetchone()
            if community_score_row:
                submission_dict["community_score"] = round(community_score_row.community_score or 0.0, 1)
            else:
                submission_dict["community_score"] = 0.0

        # Map fields to match SubmissionDetail model, ensuring required fields are non-None strings
        def safe_str(val):
            return str(val) if val is not None else ""

        detail = {
            "submission_id": safe_str(submission_dict.get("submission_id")),
            "project_name": safe_str(submission_dict.get("project_name")),
            "category": safe_str(submission_dict.get("category")),
            "description": safe_str(submission_dict.get("description") or submission_dict.get("summary")),
            "status": safe_str(submission_dict.get("status")),
            "created_at": safe_str(submission_dict.get("created_at")),
            "updated_at": safe_str(submission_dict.get("updated_at")),
            "github_url": submission_dict.get("github_url"),
            "demo_video_url": submission_dict.get("demo_video_url"),
            "project_image": submission_dict.get("project_image"),
            "problem_solved": submission_dict.get("problem_solved"),
            "favorite_part": submission_dict.get("favorite_part"),
            "scores": submission_dict.get("scores"),
            "research": submission_dict.get("research"),
            "avg_score": submission_dict.get("avg_score"),
            "solana_address": submission_dict.get("solana_address"),
            "discord_handle": submission_dict.get("discord_handle"),
            "discord_id": submission_dict.get("discord_id"),
            "discord_username": submission_dict.get("discord_username"),
            "discord_avatar": submission_dict.get("discord_avatar"),
            "twitter_handle": submission_dict.get("twitter_handle"),
            "community_score": submission_dict.get("community_score", 0.0),
        }
        # Fill missing optional fields with None
        for k in [
            "github_url",
            "demo_video_url",
            "project_image",
            "problem_solved",
            "favorite_part",
            "scores",
            "research",
            "avg_score",
            "solana_address",
            "discord_id",
            "discord_username",
            "discord_avatar",
        ]:
            if k not in detail:
                detail[k] = None

        # Get edit permission info if request is provided
        can_edit = False
        is_creator = False
        if request:
            # Check for Discord authentication
            discord_user = await validate_discord_token(request)
            submission_window_open = is_submission_window_open()
            # With invite codes removed, only Discord-authenticated users can edit, and only during the window
            can_edit = bool(discord_user) and submission_window_open
            is_creator = can_edit  # If you want stricter logic, you can add a creator_id field in the future

        detail["can_edit"] = can_edit
        detail["is_creator"] = is_creator

        return detail


if __name__ == "__main__":
    main()
