"""Auth routes — Discord OAuth login/logout/me."""

import logging
import os
import urllib.parse

import aiohttp
from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import create_engine, text

from hackathon.backend.config import HACKATHON_DB_PATH
from hackathon.backend.models import DiscordAuthResponse, DiscordCallbackRequest, DiscordUser
from hackathon.backend.simple_audit import log_security_event, log_user_action

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Discord config (auth-specific, not shared via config.py)
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:5173/auth/discord/callback")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN") or os.getenv("DISCORD_TOKEN")

if DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET:
    logging.info(f"Discord OAuth configured: Client ID starts with {DISCORD_CLIENT_ID[:10]}...")
else:
    logging.warning("Discord OAuth not configured - missing CLIENT_ID or CLIENT_SECRET")

if DISCORD_GUILD_ID and DISCORD_BOT_TOKEN:
    logging.info("Discord Guild/Bot token configured for role fetching")
else:
    logging.warning("Discord Guild/Bot token not fully configured - role fetching disabled")


def create_users_table():
    """Create the users table for Discord authentication."""
    try:
        _engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")
        with _engine.connect() as conn:
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
                            log_security_event(
                                "oauth_invalid_grant", f"expired or reused authorization code: {error_data}"
                            )
                            raise HTTPException(
                                status_code=400,
                                detail="Authorization code expired or already used",
                            )
                        elif error_data.get("error") == "invalid_client":
                            log_security_event("oauth_invalid_client", f"client configuration error: {error_data}")
                            raise HTTPException(
                                status_code=500,
                                detail="Discord OAuth client configuration error",
                            )
                        else:
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


import json  # noqa: E402


def create_or_update_user(discord_user_data: dict, roles: list[str] | None = None) -> DiscordUser:
    """Create or update user in database."""
    try:
        _engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")
        with _engine.connect() as conn:
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
                log_security_event("auth_failed")
                return None
            user_data = await resp.json()
            # Fetch roles via bot token (best effort)
            roles = await fetch_user_guild_roles(str(user_data.get("id")))
            # Update user in database including roles
            discord_user = create_or_update_user(user_data, roles)
            log_user_action("auth_success", discord_user.discord_id)
            return discord_user
    except Exception as e:
        logging.error(f"Error validating Discord token: {e}")
        log_security_event("auth_error")
        return None


# --- Route handlers ---


@router.get("/discord/login")
async def discord_login():
    """Initiate Discord OAuth login flow."""
    auth_url = generate_discord_auth_url()
    return {"auth_url": auth_url}


@router.post("/discord/callback", response_model=DiscordAuthResponse)
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


@router.get("/me", response_model=DiscordUser)
async def get_current_user(request: Request):
    """Get current authenticated user info."""
    discord_user = await validate_discord_token(request)
    if not discord_user:
        log_security_event("auth_me_failed", "invalid or missing token")
        raise HTTPException(status_code=401, detail="Not authenticated")

    log_user_action("auth_me_success", discord_user.discord_id)
    return discord_user


@router.post("/discord/logout")
async def discord_logout():
    """Logout user (clear session)."""
    return {"message": "Logged out successfully"}
