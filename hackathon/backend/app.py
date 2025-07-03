#!/usr/bin/env python3
"""
FastAPI backend for the Hackathon Admin Dashboard and Public Leaderboard.
Serves data from hackathon.db via REST API endpoints.
"""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import random

from fastapi import FastAPI, HTTPException, Request, status, UploadFile, File as FastAPIFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, create_model
import uvicorn
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Add path for importing schema module
import sys
sys.path.append(str(Path(__file__).parent.parent))
from hackathon.backend.schema import get_fields, get_schema, reload_schema

from PIL import Image
from io import BytesIO

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)

# Load environment variables
load_dotenv()

# Configuration
# Get the repository root directory (3 levels up from hackathon/dashboard/app.py)
REPO_ROOT = Path(__file__).parent.parent.parent
HACKATHON_DB_PATH = os.getenv('HACKATHON_DB_PATH', str(REPO_ROOT / 'data' / 'hackathon.db'))
STATIC_DATA_DIR = os.getenv('STATIC_DATA_DIR', str(Path(__file__).parent / 'frontend' / 'public' / 'data'))
LOG_FILE_PATH = REPO_ROOT / 'logs' / 'hackathon_api.log'

# Setup logging
LOG_FILE_PATH.parent.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE_PATH),
        logging.StreamHandler()
    ]
)

# Create FastAPI app
app = FastAPI(
    title="Clank Tank Hackathon API",
    description="API for hackathon admin dashboard and public leaderboard",
    version="1.0.0"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Debug middleware to see raw request data
@app.middleware("http")
async def debug_request_middleware(request: Request, call_next):
    if request.url.path == "/api/submissions" and request.method == "POST":
        # Read the request body for debugging
        body = await request.body()
        logging.info("--- DEBUG MIDDLEWARE ---")
        logging.info(f"Content-Type: {request.headers.get('content-type')}")
        logging.info(f"Raw body length: {len(body)}")
        logging.info(f"Raw body (first 1000 chars): {body[:1000]}")
        
        # Try to parse as different formats
        try:
            decoded_body = body.decode('utf-8')
            logging.info(f"Decoded body: {decoded_body[:1000]}")
        except Exception as e:
            logging.info(f"Could not decode body as UTF-8: {e}")
        
        try:
            json_body = json.loads(body)
            logging.info(f"Parsed JSON keys: {list(json_body.keys()) if isinstance(json_body, dict) else 'not a dict'}")
        except Exception as e:
            logging.info(f"Could not parse body as JSON: {e}")
            
        # Check if it might be form data
        try:
            from urllib.parse import parse_qs
            form_data = parse_qs(decoded_body)
            logging.info(f"Parsed as form data: {form_data}")
        except Exception as e:
            logging.info(f"Could not parse as form data: {e}")
        
        # Create a new request with the consumed body
        async def receive():
            return {"type": "http.request", "body": body}
        
        # Rebuild the request
        scope = request.scope
        request._body = body
        
        # Custom request class to handle body re-reading
        class RequestWithBody(Request):
            def __init__(self, scope, receive=None):
                super().__init__(scope, receive)
                self._body = body
                
            async def body(self):
                return self._body
        
        request = RequestWithBody(scope, receive)
        
    response = await call_next(request)
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Engine
engine = create_engine(f"sqlite:///{HACKATHON_DB_PATH}")

# Pydantic models
class SubmissionSummary(BaseModel):
    submission_id: str
    project_name: str
    team_name: str
    category: str
    status: str
    created_at: str
    avg_score: Optional[float] = None
    judge_count: Optional[int] = None
    project_image: Optional[str] = None
    description: Optional[str] = None

class SubmissionDetail(BaseModel):
    submission_id: str
    project_name: str
    team_name: str
    category: str
    description: str
    status: str
    created_at: str
    updated_at: str
    github_url: Optional[str] = None
    demo_video_url: Optional[str] = None
    live_demo_url: Optional[str] = None
    project_image: Optional[str] = None
    tech_stack: Optional[str] = None
    how_it_works: Optional[str] = None
    problem_solved: Optional[str] = None
    coolest_tech: Optional[str] = None
    next_steps: Optional[str] = None
    scores: Optional[List[Dict[str, Any]]] = None
    research: Optional[Dict[str, Any]] = None
    avg_score: Optional[float] = None
    solana_address: Optional[str] = None

# Dynamically create the SubmissionCreate models from versioned manifests
submission_fields_v1 = {field: (Optional[str], None) for field in get_fields("v1")}
SubmissionCreateV1 = create_model('SubmissionCreateV1', **submission_fields_v1)

submission_fields_v2 = {field: (Optional[str], None) for field in get_fields("v2")}
# project_image field is used for file upload, but we store the URL in the database
SubmissionCreateV2 = create_model('SubmissionCreateV2', **submission_fields_v2)

class LeaderboardEntry(BaseModel):
    rank: int
    project_name: str
    team_name: str
    category: str
    final_score: float
    youtube_url: Optional[str] = None
    status: str

# Helper to get available columns in hackathon_scores
from sqlalchemy.engine import Connection

def get_score_columns(conn: 'Connection', required_fields):
    """
    Return only the columns from required_fields that exist in the hackathon_scores table.
    This allows robust queries even if some fields (e.g., community_bonus, final_verdict) are not present yet.
    """
    pragma_result = conn.execute(text("PRAGMA table_info(hackathon_scores)"))
    columns = {row[1] for row in pragma_result.fetchall()}
    return [f for f in required_fields if f in columns]

# Define a model for the submission schema field
class SubmissionFieldSchema(BaseModel):
    name: str
    label: str
    type: str
    required: bool
    placeholder: str = None
    maxLength: int = None
    options: List[str] = None
    pattern: str = None
    helperText: str = None

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
    voters: List[str]

class FeedbackSummary(BaseModel):
    submission_id: str
    total_votes: int
    feedback: List[FeedbackItem]

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
            "judging": {
                "GET /api/submission/{submission_id}/feedback": "Get community feedback for a submission"
            },
            "public": {
                "GET /api/leaderboard": "Get public leaderboard (latest)",
                "GET /api/stats": "Get overall hackathon stats (latest)",
                "GET /api/{version}/leaderboard": "Get public leaderboard (versioned)",
                "GET /api/{version}/stats": "Get overall hackathon stats (versioned)",
                "GET /api/uploads/{filename}": "Serve uploaded project images"
            }
        }
    }

@app.get("/api/submissions", tags=["latest"], response_model=List[SubmissionSummary])
async def list_submissions_latest(
    include: str = "scores,research,community",
    status: str = None,
    category: str = None
):
    return await list_submissions(version="v2", include=include, status=status, category=category)

@app.get("/api/submissions/{submission_id}", tags=["latest"], response_model=SubmissionDetail)
async def get_submission_latest(submission_id: str, include: str = "scores,research,community"):
    return await get_submission(submission_id=submission_id, version="v2", include=include)

@app.post("/api/submissions", status_code=201, tags=["latest"], response_model=dict)
@limiter.limit("5/minute")
async def create_submission_latest(submission: SubmissionCreateV2, request: Request):
    """Create a new submission with v2 schema and basic error handling."""
    print(f"📝 Processing submission: {submission.project_name}")
    
    # Validate project_image field
    data_dict = submission.dict()
    project_image = data_dict.get('project_image')
    if project_image:
        if project_image == '[object File]':
            raise HTTPException(
                status_code=422, 
                detail="Invalid file object detected in project_image. Please upload the image first and submit the URL instead."
            )
        elif isinstance(project_image, str) and not project_image.startswith('/api/uploads/'):
            # Remove invalid URLs that aren't our upload URLs
            print(f"⚠️  Invalid project_image URL detected, removing: {project_image}")
            data_dict['project_image'] = None
    
    # Generate submission ID
    submission_id = submission.project_name.lower().replace(" ", "-")[:50]
    if len(submission_id) < 6:
        submission_id = f"{submission_id}-{random.randint(1000, 9999)}"
    
    # Basic data preparation
    now = datetime.now().isoformat()
    data = submission.dict()
    data["submission_id"] = submission_id
    data["status"] = "submitted"
    data["created_at"] = now
    data["updated_at"] = now
    
    # Database insertion
    table = "hackathon_submissions_v2"
    columns = ", ".join(data.keys())
    placeholders = ", ".join([f":{key}" for key in data.keys()])
    
    try:
        with engine.connect() as conn:
            conn.execute(text(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"), data)
            conn.commit()
        
        print(f"✅ Submission saved: {submission_id}")
        return {
            "success": True, 
            "submission_id": submission_id,
            "message": "Submission received and saved successfully"
        }
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "submission_id": submission_id
            }
        )

@limiter.limit("5/minute")
@app.post("/api/upload-image", tags=["latest"])
async def upload_image(request: Request, file: UploadFile = FastAPIFile(...)):
    """Upload project image and return URL."""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (2MB limit)
        MAX_SIZE = 2 * 1024 * 1024  # 2MB
        content = await file.read()
        if len(content) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="File size must be less than 2MB")
        
        # Verify and sanitize image using Pillow
        try:
            img = Image.open(BytesIO(content))
            img.verify()  # Verify image integrity
        except Exception:
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")
        # Re-open image for re-encoding (verify() leaves file in unusable state)
        img = Image.open(BytesIO(content))
        img = img.convert("RGB")  # Ensure JPEG compatible
        
        # Create uploads directory (use same path as serve_upload)
        uploads_dir = Path(__file__).parent / "data" / "uploads"
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
        
        return {
            "success": True,
            "url": file_url,
            "filename": unique_filename,
            "size": file_path.stat().st_size
        }
        
    except Exception as e:
        print(f"❌ Image upload error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload image: {str(e)}")

# Serve uploaded files
@app.get("/api/uploads/{filename}")
async def serve_upload(filename: str):
    """Serve uploaded files."""
    # Use absolute path relative to the app.py file location
    uploads_dir = Path(__file__).parent / "data" / "uploads"
    file_path = uploads_dir / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Return file content with appropriate headers
    from fastapi.responses import FileResponse
    return FileResponse(file_path)

@app.get("/api/submission-schema", tags=["latest"], response_model=List[SubmissionFieldSchema])
async def get_submission_schema_latest():
    return await get_submission_schema_versioned(version="v2")

@app.get("/api/leaderboard", tags=["latest"], response_model=List[LeaderboardEntry])
async def get_leaderboard_latest():
    # Use v2 as the default version
    table = "hackathon_submissions_v2"
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT 
                s.project_name,
                s.team_name,
                s.category,
                s.demo_video_url as youtube_url,
                s.status,
                AVG(sc.weighted_total) as avg_score
            FROM {table} s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            WHERE s.status IN ('scored', 'completed', 'published') AND sc.round = 1
            GROUP BY s.submission_id
            ORDER BY avg_score DESC
        """))
        entries = []
        rank = 1
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            entry = LeaderboardEntry(
                rank=rank,
                project_name=row_dict['project_name'],
                team_name=row_dict['team_name'],
                category=row_dict['category'],
                final_score=round(row_dict['avg_score'], 2),
                youtube_url=row_dict['youtube_url'],
                status=row_dict['status']
            )
            entries.append(entry)
            rank += 1
        return entries

@app.get("/api/stats", tags=["latest"], response_model=StatsModel)
async def get_stats_latest():
    return await get_stats(version="v2")

@app.get("/api/{version}/submissions", tags=["versioned"], response_model=List[SubmissionSummary])
async def list_submissions(
    version: str = "v1",
    include: str = "scores,research,community",
    status: str = None,
    category: str = None
):
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    table = f"hackathon_submissions_{version}"
    manifest = get_fields(version)
    fields = ["submission_id"] + list(manifest) + ["status", "created_at", "updated_at"]
    
    # project_image field is handled properly via schema
    
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
    select_stmt = text(f"SELECT {', '.join(fields)} FROM {table}{where_clause}")
    
    with engine.connect() as conn:
        result = conn.execute(select_stmt, params)
        submissions = []
        include_parts = set(i.strip() for i in include.split(",") if i.strip())
        for submission_row in result.fetchall():
            submission_dict = dict(submission_row._mapping)
            submission_id = submission_dict["submission_id"]
            # Always calculate score aggregates for SubmissionSummary
            scores_agg_result = conn.execute(text("""
                SELECT AVG(weighted_total) as avg_score, COUNT(DISTINCT judge_name) as judge_count
                FROM hackathon_scores 
                WHERE submission_id = :submission_id AND round = 1
            """), {"submission_id": submission_id})
            agg_row = scores_agg_result.fetchone()
            if agg_row and agg_row[0] is not None:
                submission_dict["avg_score"] = round(float(agg_row[0]), 2)
                submission_dict["judge_count"] = int(agg_row[1])
            else:
                submission_dict["avg_score"] = None
                submission_dict["judge_count"] = 0
            
            # Optionally add scores
            if "scores" in include_parts:
                score_fields = [
                    "judge_name", "innovation", "technical_execution", "market_potential",
                    "user_experience", "weighted_total", "notes", "round",
                    "community_bonus", "final_verdict"
                ]
                actual_score_fields = get_score_columns(conn, score_fields)
                if actual_score_fields:
                    scores_result = conn.execute(
                        text(f"SELECT {', '.join(actual_score_fields)} FROM hackathon_scores WHERE submission_id = :submission_id ORDER BY judge_name, round"),
                        {"submission_id": submission_id}
                    )
                    scores = []
                    for score_row in scores_result.fetchall():
                        score_dict = dict(score_row._mapping)
                        if "notes" in score_dict:
                            score_dict["notes"] = json.loads(score_dict["notes"]) if score_dict["notes"] else {}
                        scores.append(score_dict)
                    submission_dict["scores"] = scores
                else:
                    submission_dict["scores"] = []
            # Optionally add research
            if "research" in include_parts:
                research_result = conn.execute(text("""
                    SELECT github_analysis, market_research, technical_assessment
                    FROM hackathon_research
                    WHERE submission_id = :submission_id
                """), {"submission_id": submission_id})
                research_row = research_result.fetchone()
                if research_row:
                    research_dict = dict(research_row._mapping)
                    research = {
                        'github_analysis': json.loads(research_dict['github_analysis']) if research_dict['github_analysis'] else None,
                        'market_research': json.loads(research_dict['market_research']) if research_dict['market_research'] else None,
                        'technical_assessment': json.loads(research_dict['technical_assessment']) if research_dict['technical_assessment'] else None
                    }
                    submission_dict["research"] = research
                else:
                    submission_dict["research"] = None
            # Optionally add community feedback
            if "community" in include_parts:
                feedback_result = conn.execute(text("""
                    SELECT 
                        reaction_type,
                        COUNT(*) as vote_count,
                        GROUP_CONCAT(discord_user_nickname) as voters
                    FROM community_feedback 
                    WHERE submission_id = :submission_id
                    GROUP BY reaction_type
                    ORDER BY vote_count DESC
                """), {"submission_id": submission_id})
                feedback_summary = []
                total_votes = 0
                for row in feedback_result.fetchall():
                    row_dict = dict(row._mapping)
                    reaction_type, vote_count, voters = row_dict['reaction_type'], row_dict['vote_count'], row_dict['voters']
                    total_votes += vote_count
                    feedback_summary.append({
                        'reaction_type': reaction_type,
                        'vote_count': vote_count,
                        'voters': voters.split(',') if voters else []
                    })
                submission_dict["community_feedback"] = {
                    'total_votes': total_votes,
                    'feedback': feedback_summary
                }
            submissions.append(submission_dict)
    return submissions

@app.get("/api/{version}/submissions/{submission_id}", tags=["versioned"], response_model=SubmissionDetail)
async def get_submission_versioned(
    version: str,
    submission_id: str,
    include: str = "scores,research,community"
):
    return await get_submission(submission_id=submission_id, version=version, include=include)

@app.get("/api/{version}/submission-schema", tags=["versioned"], response_model=List[SubmissionFieldSchema])
async def get_submission_schema_versioned(version: str):
    if version in ("v1", "v2"):
        return JSONResponse(content=get_schema(version))
    # Add more versions as needed
    raise HTTPException(status_code=404, detail="Schema version not found")

@app.get("/api/{version}/leaderboard", tags=["versioned"], response_model=List[LeaderboardEntry])
async def get_leaderboard(version: str):
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    table = f"hackathon_submissions_{version}"
    with engine.connect() as conn:
        result = conn.execute(text(f"""
            SELECT 
                s.project_name,
                s.team_name,
                s.category,
                s.demo_video_url as youtube_url,
                s.status,
                AVG(sc.weighted_total) as avg_score
            FROM {table} s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            WHERE s.status IN ('scored', 'completed', 'published') AND sc.round = 1
            GROUP BY s.submission_id
            ORDER BY avg_score DESC
        """))
        entries = []
        rank = 1
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            entry = LeaderboardEntry(
                rank=rank,
                project_name=row_dict['project_name'],
                team_name=row_dict['team_name'],
                category=row_dict['category'],
                final_score=round(row_dict['avg_score'], 2),
                youtube_url=row_dict['youtube_url'],
                status=row_dict['status']
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
        status_result = conn.execute(text(f"""
            SELECT status, COUNT(*) as count
            FROM {table}
            GROUP BY status
        """))
        status_counts = {row[0]: row[1] for row in status_result.fetchall()}
        # Count by category
        category_result = conn.execute(text(f"""
            SELECT category, COUNT(*) as count
            FROM {table}
            GROUP BY category
        """))
        category_counts = {row[0]: row[1] for row in category_result.fetchall()}
        # Total submissions
        total_result = conn.execute(text(f"SELECT COUNT(*) as total FROM {table}"))
        total = total_result.scalar_one()
        return {
            'total_submissions': total,
            'by_status': status_counts,
            'by_category': category_counts,
            'updated_at': datetime.now().isoformat()
        }

@app.get("/api/feedback/{submission_id}", tags=["latest"], response_model=FeedbackSummary)
async def get_feedback_latest(submission_id: str):
    return await get_feedback_versioned(version="v2", submission_id=submission_id)

@app.get("/api/{version}/feedback/{submission_id}", tags=["versioned"], response_model=FeedbackSummary)
async def get_feedback_versioned(version: str, submission_id: str):
    # Only v2 supported for now
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                reaction_type,
                COUNT(*) as vote_count,
                GROUP_CONCAT(discord_user_nickname) as voters
            FROM community_feedback 
            WHERE submission_id = :submission_id
            GROUP BY reaction_type
            ORDER BY vote_count DESC
        """), {"submission_id": submission_id})
        feedback_summary = []
        total_votes = 0
        reaction_map = {
            'hype': {'emoji': '🔥', 'name': 'General Hype'},
            'innovation_creativity': {'emoji': '💡', 'name': 'Innovation & Creativity'},
            'technical_execution': {'emoji': '💻', 'name': 'Technical Execution'},
            'market_potential': {'emoji': '📈', 'name': 'Market Potential'},
            'user_experience': {'emoji': '😍', 'name': 'User Experience'}
        }
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            reaction_type, vote_count, voters = row_dict['reaction_type'], row_dict['vote_count'], row_dict['voters']
            total_votes += vote_count
            reaction_info = reaction_map.get(reaction_type, {'emoji': '❓', 'name': reaction_type})
            feedback_summary.append(FeedbackItem(
                reaction_type=reaction_type,
                emoji=reaction_info['emoji'],
                name=reaction_info['name'],
                vote_count=vote_count,
                voters=voters.split(',') if voters else []
            ))
        return FeedbackSummary(
            submission_id=submission_id,
            total_votes=total_votes,
            feedback=feedback_summary
        )

# Hide the old feedback endpoint from docs
@app.get("/api/submission/{submission_id}/feedback", include_in_schema=False)
async def get_feedback_legacy(submission_id: str):
    return await get_feedback_latest(submission_id=submission_id)

def generate_static_data():
    """Generate static JSON files for static site deployment."""
    print("Generating static data files...")
    
    # Create output directory
    output_dir = Path(STATIC_DATA_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with engine.connect() as conn:
        # Generate submissions.json
        result = conn.execute(text("""
            SELECT 
                s.submission_id,
                s.project_name,
                s.team_name,
                s.category,
                s.status,
                s.created_at,
                AVG(sc.weighted_total) as avg_score,
                COUNT(DISTINCT sc.judge_name) as judge_count
            FROM hackathon_submissions_v2 s
            LEFT JOIN hackathon_scores sc ON s.submission_id = sc.submission_id AND sc.round = 1
            GROUP BY s.submission_id
            ORDER BY s.created_at DESC
        """))
        
        submissions = []
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            submissions.append({
                'submission_id': row_dict['submission_id'],
                'project_name': row_dict['project_name'],
                'team_name': row_dict['team_name'],
                'category': row_dict['category'],
                'status': row_dict['status'],
                'created_at': row_dict['created_at'],
                'avg_score': round(row_dict['avg_score'], 2) if row_dict['avg_score'] else None,
                'judge_count': row_dict['judge_count'] if row_dict['judge_count'] else 0
            })
        
        with open(output_dir / 'submissions.json', 'w') as f:
            json.dump(submissions, f, indent=2)
        
        print(f"Generated submissions.json with {len(submissions)} entries")
        
        # Generate individual submission files
        submission_dir = output_dir / 'submission'
        submission_dir.mkdir(exist_ok=True)
        
        for submission in submissions:
            # Use the get_submission logic to generate detailed data
            # (This is a simplified version - in production, refactor to share code)
            details_result = conn.execute(text("SELECT * FROM hackathon_submissions_v2 WHERE submission_id = :submission_id"), 
                         {"submission_id": submission['submission_id']})
            details = details_result.fetchone()
            
            with open(submission_dir / f"{submission['submission_id']}.json", 'w') as f:
                json.dump(dict(details._mapping), f, indent=2)
        
        # Generate leaderboard.json
        leaderboard_result = conn.execute(text("""
            SELECT 
                s.project_name,
                s.team_name,
                s.category,
                s.demo_video_url as youtube_url,
                s.status,
                AVG(sc.weighted_total) as avg_score
            FROM hackathon_submissions_v2 s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            WHERE s.status IN ('scored', 'completed', 'published') AND sc.round = 1
            GROUP BY s.submission_id
            ORDER BY avg_score DESC
        """))
        leaderboard = []
        rank = 1
        for row in leaderboard_result.fetchall():
            row_dict = dict(row._mapping)
            leaderboard.append({
                'rank': rank,
                'project_name': row_dict['project_name'],
                'team_name': row_dict['team_name'],
                'category': row_dict['category'],
                'final_score': round(row_dict['avg_score'], 2),
                'youtube_url': row_dict['youtube_url'],
                'status': row_dict['status']
            })
            rank += 1
        with open(output_dir / 'leaderboard.json', 'w') as f:
            json.dump(leaderboard, f, indent=2)
        print(f"Generated leaderboard.json with {len(leaderboard)} entries")
        
        # Generate stats.json
        stats = {
            'total_submissions': len(submissions),
            'by_status': {},
            'by_category': {},
            'generated_at': datetime.now().isoformat()
        }
        
        for submission in submissions:
            status = submission['status']
            category = submission['category']
            
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            stats['by_category'][category] = stats['by_category'].get(category, 0) + 1
        
        with open(output_dir / 'stats.json', 'w') as f:
            json.dump(stats, f, indent=2)
        
        print("Static data generation complete!")

@app.post("/api/v1/submissions", status_code=410, include_in_schema=False)
@limiter.limit("5/minute")
async def deprecated_post_v1_submissions(request: Request, *args, **kwargs):
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="This endpoint is deprecated. Use /api/submissions.")

@app.post("/api/v2/submissions", status_code=410, include_in_schema=False)
@limiter.limit("5/minute")
async def deprecated_post_v2_submissions(request: Request, *args, **kwargs):
    raise HTTPException(status_code=status.HTTP_410_GONE, detail="This endpoint is deprecated. Use /api/submissions.")

def main():
    """Main function to run the API server or generate static data."""
    parser = argparse.ArgumentParser(description="Hackathon Dashboard API")
    parser.add_argument(
        "--generate-static-data",
        action="store_true",
        help="Generate static JSON files instead of running the server"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind to (default: 8000)"
    )
    
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
        print(f"Starting FastAPI server on http://{args.host}:{args.port}")
        print(f"API documentation available at http://{args.host}:{args.port}/docs")
        print(f"Using database: {HACKATHON_DB_PATH}")
        print(f"Database absolute path: {os.path.abspath(HACKATHON_DB_PATH)}")
        print(f"Database exists: {os.path.exists(HACKATHON_DB_PATH)}")
        print(f"Current working directory: {os.getcwd()}")

        # Debug: Check what columns SQLAlchemy sees
        try:
            from sqlalchemy import inspect
            inspector = inspect(engine)
            columns = inspector.get_columns('hackathon_submissions_v2')
            column_names = [col['name'] for col in columns]
            print(f"SQLAlchemy sees columns: {column_names}")
            print(f"SQLAlchemy sees project_image: {'project_image' in column_names}")
            print(f"SQLAlchemy sees image_url: {'image_url' in column_names}")
        except Exception as e:
            print(f"Error checking columns: {e}")
            
        uvicorn.run(app, host=args.host, port=args.port)

async def get_submission(submission_id: str, version: str = "v1", include: str = "scores,research,community"):
    if version not in ("v1", "v2"):
        raise HTTPException(status_code=400, detail="Invalid version. Use 'v1' or 'v2'.")
    table = f"hackathon_submissions_{version}"
    manifest = get_fields(version)
    fields = ["submission_id"] + list(manifest) + ["status", "created_at", "updated_at"]
    
    # project_image field is handled properly via schema
    select_stmt = text(f"SELECT {', '.join(fields)} FROM {table} WHERE submission_id = :submission_id")
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
                "judge_name", "innovation", "technical_execution", "market_potential",
                "user_experience", "weighted_total", "notes", "round",
                "community_bonus", "final_verdict"
            ]
            actual_score_fields = get_score_columns(conn, score_fields)
            if actual_score_fields:
                scores_result = conn.execute(
                    text(f"SELECT {', '.join(actual_score_fields)} FROM hackathon_scores WHERE submission_id = :submission_id ORDER BY judge_name, round"),
                    {"submission_id": submission_id}
                )
                scores = []
                for score_row in scores_result.fetchall():
                    score_dict = dict(score_row._mapping)
                    if "notes" in score_dict:
                        score_dict["notes"] = json.loads(score_dict["notes"]) if score_dict["notes"] else {}
                    scores.append(score_dict)
                submission_dict["scores"] = scores
            else:
                submission_dict["scores"] = []
        # Optionally add research
        if "research" in include_parts:
            research_result = conn.execute(text("""
                SELECT github_analysis, market_research, technical_assessment
                FROM hackathon_research
                WHERE submission_id = :submission_id
            """), {"submission_id": submission_id})
            research_row = research_result.fetchone()
            if research_row:
                research_dict = dict(research_row._mapping)
                research = {
                    'github_analysis': json.loads(research_dict['github_analysis']) if research_dict['github_analysis'] else None,
                    'market_research': json.loads(research_dict['market_research']) if research_dict['market_research'] else None,
                    'technical_assessment': json.loads(research_dict['technical_assessment']) if research_dict['technical_assessment'] else None
                }
                submission_dict["research"] = research
            else:
                submission_dict["research"] = None
        # Optionally add community feedback
        if "community" in include_parts:
            feedback_result = conn.execute(text("""
                SELECT 
                    reaction_type,
                    COUNT(*) as vote_count,
                    GROUP_CONCAT(discord_user_nickname) as voters
                FROM community_feedback 
                WHERE submission_id = :submission_id
                GROUP BY reaction_type
                ORDER BY vote_count DESC
            """), {"submission_id": submission_id})
            feedback_summary = []
            total_votes = 0
            for row in feedback_result.fetchall():
                row_dict = dict(row._mapping)
                reaction_type, vote_count, voters = row_dict['reaction_type'], row_dict['vote_count'], row_dict['voters']
                total_votes += vote_count
                feedback_summary.append({
                    'reaction_type': reaction_type,
                    'vote_count': vote_count,
                    'voters': voters.split(',') if voters else []
                })
            submission_dict["community_feedback"] = {
                'total_votes': total_votes,
                'feedback': feedback_summary
            }
        # Map fields to match SubmissionDetail model, ensuring required fields are non-None strings
        def safe_str(val):
            return str(val) if val is not None else ''
        detail = {
            'submission_id': safe_str(submission_dict.get('submission_id')),
            'project_name': safe_str(submission_dict.get('project_name')),
            'team_name': safe_str(submission_dict.get('team_name')),
            'category': safe_str(submission_dict.get('category')),
            'description': safe_str(submission_dict.get('description') or submission_dict.get('summary')),
            'status': safe_str(submission_dict.get('status')),
            'created_at': safe_str(submission_dict.get('created_at')),
            'updated_at': safe_str(submission_dict.get('updated_at')),
            'github_url': submission_dict.get('github_url'),
            'demo_video_url': submission_dict.get('demo_video_url'),
            'live_demo_url': submission_dict.get('live_demo_url'),
            'project_image': submission_dict.get('project_image'),
            'tech_stack': submission_dict.get('tech_stack'),
            'how_it_works': submission_dict.get('how_it_works'),
            'problem_solved': submission_dict.get('problem_solved'),
            'coolest_tech': submission_dict.get('coolest_tech') or submission_dict.get('favorite_part'),
            'next_steps': submission_dict.get('next_steps'),
            'scores': submission_dict.get('scores'),
            'research': submission_dict.get('research'),
            'avg_score': submission_dict.get('avg_score'),
            'solana_address': submission_dict.get('solana_address'),
        }
        # Fill missing optional fields with None
        for k in ['github_url','demo_video_url','live_demo_url','project_image','tech_stack','how_it_works','problem_solved','coolest_tech','next_steps','scores','research','avg_score','solana_address']:
            if k not in detail:
                detail[k] = None
        
        return detail

if __name__ == "__main__":
    main()