#!/usr/bin/env python3
"""
FastAPI backend for the Hackathon Admin Dashboard and Public Leaderboard.
Serves data from hackathon.db via REST API endpoints.
"""

import argparse
import logging
import os
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import create_engine

from hackathon.backend.config import HACKATHON_DB_PATH
from hackathon.backend.routes.auth import create_users_table, validate_discord_token  # noqa: F401
from hackathon.backend.routes.auth import router as auth_router
from hackathon.backend.routes.submissions import router as submissions_router
from hackathon.backend.routes.voting import router as voting_router
from hackathon.backend.websocket_service import prize_pool_service
from hackathon.scripts.generate_static_data import generate_static_data

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

# Create FastAPI app
app = FastAPI(
    title="Clank Tank Hackathon API",
    description="API for hackathon admin dashboard and public leaderboard",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(auth_router)
app.include_router(submissions_router)
app.include_router(voting_router)


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
        print(f"Discord OAuth configured: {bool(os.getenv('DISCORD_CLIENT_ID'))}")

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


if __name__ == "__main__":
    main()
