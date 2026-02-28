"""Submission-related routes: CRUD, leaderboard, stats, feedback, versioned endpoints."""

import json
import logging
import os
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, UploadFile, status
from fastapi import File as FastAPIFile
from fastapi.responses import JSONResponse
from PIL import Image
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy import create_engine, text

from hackathon.backend.config import HACKATHON_DB_PATH, SUBMISSION_DEADLINE
from hackathon.backend.models import (
    FeedbackItem,
    FeedbackSummary,
    LeaderboardEntry,
    LikeDislikeRequest,
    LikeDislikeResponse,
    StatsModel,
    SubmissionCreateV2,
    SubmissionDetail,
    SubmissionFieldSchema,
    SubmissionSchemaResponse,
    SubmissionSummary,
)
from hackathon.backend.routes.auth import validate_discord_token
from hackathon.backend.schema import get_schema
from hackathon.backend.simple_audit import log_security_event

router = APIRouter()

# Database engine (local to this module)
engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")

# Repository root (3 levels up from hackathon/backend/routes/submissions.py)
REPO_ROOT = Path(__file__).parent.parent.parent.parent

# Rate limiting
ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() not in ["false", "0", "no"]
limiter = Limiter(key_func=get_remote_address)


def conditional_rate_limit(rate_limit_str):
    """Apply rate limiting only if ENABLE_RATE_LIMITING is True."""
    if ENABLE_RATE_LIMITING:
        return limiter.limit(rate_limit_str)
    else:
        def no_op_decorator(func):
            return func

        return no_op_decorator


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


def get_score_columns(conn, required_fields):
    """
    Return only the columns from required_fields that exist in the hackathon_scores table.
    This allows robust queries even if some fields (e.g., community_bonus, final_verdict) are not present yet.
    """
    pragma_result = conn.execute(text("PRAGMA table_info(hackathon_scores)"))
    columns = {row[1] for row in pragma_result.fetchall()}
    return [f for f in required_fields if f in columns]


@router.post("/api/submissions/{submission_id}/like-dislike", tags=["latest"], response_model=LikeDislikeResponse)
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


@router.get("/api/submissions/{submission_id}/like-dislike", tags=["latest"], response_model=LikeDislikeResponse)
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


@router.get("/api/submissions", tags=["latest"], response_model=list[SubmissionSummary])
async def list_submissions_latest(
    include: str = "scores,research,community",
    status: str | None = None,
    category: str | None = None,
):
    return await list_submissions(version="v2", include=include, status=status, category=category, detail=False)


@router.get("/api/submissions/full", tags=["latest"])
async def list_submissions_full(
    include: str = "scores,research,community",
    status: str | None = None,
    category: str | None = None,
):
    data = await list_submissions(version="v2", include=include, status=status, category=category, detail=True)
    return JSONResponse(content=data)


@router.get("/api/submissions/{submission_id}", tags=["latest"], response_model=SubmissionDetail)
async def get_submission_latest(submission_id: int, request: Request, include: str = "scores,research,community"):
    return await get_submission(submission_id=submission_id, version="v2", include=include, request=request)


@conditional_rate_limit("5/minute")
@router.post("/api/submissions", status_code=201, tags=["latest"], response_model=dict)
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


@router.put("/api/submissions/{submission_id}", tags=["latest"], response_model=dict)
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
@router.post("/api/upload-image", tags=["latest"])
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
@router.get("/api/uploads/{filename}")
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


@router.get("/api/submission-schema", tags=["latest"], response_model=SubmissionSchemaResponse)
async def get_submission_schema_latest():
    fields = get_schema("v2")  # returns a list of field dicts
    window_info = get_submission_window_info()
    return SubmissionSchemaResponse(fields=fields, **window_info)


@router.get("/api/leaderboard", tags=["latest"], response_model=list[LeaderboardEntry])
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


@router.get("/api/stats", tags=["latest"], response_model=StatsModel)
async def get_stats_latest():
    return await get_stats(version="v2")


@router.get("/api/config", tags=["latest"])
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


@router.get(
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


@router.get(
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


@router.get(
    "/api/{version}/submission-schema",
    tags=["versioned"],
    response_model=list[SubmissionFieldSchema],
)
async def get_submission_schema_versioned(version: str):
    if version in ("v1", "v2"):
        return JSONResponse(content=get_schema(version))
    # Add more versions as needed
    raise HTTPException(status_code=404, detail="Schema version not found")


@router.get(
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


@router.get("/api/{version}/stats", tags=["versioned"], response_model=StatsModel)
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


@router.get("/api/feedback/{submission_id}", tags=["latest"], response_model=FeedbackSummary)
async def get_feedback_latest(submission_id: int):
    return await get_feedback_versioned(version="v2", submission_id=submission_id)


@router.get(
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
@router.get("/api/submission/{submission_id}/feedback", include_in_schema=False)
async def get_feedback_legacy(submission_id: int):
    return await get_feedback_latest(submission_id=submission_id)


@router.post("/api/v1/submissions", status_code=410, include_in_schema=False)
@conditional_rate_limit("5/minute")
async def deprecated_post_v1_submissions(request: Request, *args, **kwargs):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint is deprecated. Use /api/submissions.",
    )


@router.post("/api/v2/submissions", status_code=410, include_in_schema=False)
@conditional_rate_limit("5/minute")
async def deprecated_post_v2_submissions(request: Request, *args, **kwargs):
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail="This endpoint is deprecated. Use /api/submissions.",
    )


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
