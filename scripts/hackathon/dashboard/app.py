#!/usr/bin/env python3
"""
FastAPI backend for the Hackathon Admin Dashboard and Public Leaderboard.
Serves data from hackathon.db via REST API endpoints.
"""

import os
import json
import sqlite3
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from contextlib import contextmanager
import logging

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from starlette.responses import Response
from starlette.requests import Request as StarletteRequest
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Setup rate limiter
limiter = Limiter(key_func=get_remote_address)

# Load environment variables
load_dotenv()

# Configuration
# Get the repository root directory (3 levels up from dashboard/app.py)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
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
        logging.info(f"--- DEBUG MIDDLEWARE ---")
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
    tech_stack: Optional[str] = None
    how_it_works: Optional[str] = None
    problem_solved: Optional[str] = None
    coolest_tech: Optional[str] = None
    next_steps: Optional[str] = None
    scores: Optional[List[Dict[str, Any]]] = None
    research: Optional[Dict[str, Any]] = None
    avg_score: Optional[float] = None

class SubmissionCreate(BaseModel):
    project_name: str
    team_name: str
    description: str
    category: str
    discord_handle: str
    twitter_handle: Optional[str] = None
    github_url: str
    demo_video_url: str
    live_demo_url: Optional[str] = None
    logo_url: Optional[str] = None
    tech_stack: Optional[str] = None
    how_it_works: Optional[str] = None
    problem_solved: Optional[str] = None
    coolest_tech: Optional[str] = None
    next_steps: Optional[str] = None

class LeaderboardEntry(BaseModel):
    rank: int
    project_name: str
    team_name: str
    category: str
    final_score: float
    youtube_url: Optional[str] = None

# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Clank Tank Hackathon API",
        "version": "1.0.0",
        "endpoints": {
            "admin": {
                "/api/submissions": "List all submissions",
                "/api/submission/{id}": "Get submission details",
                "/api/submission/{id}/feedback": "Get community feedback"
            },
            "public": {
                "/api/leaderboard": "Get public leaderboard"
            }
        }
    }

@app.get("/api/submissions", response_model=List[SubmissionSummary])
async def get_submissions(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category")
):
    """Get all submissions with optional filtering."""
    with engine.connect() as conn:
        # Base query
        query = text("""
            SELECT 
                s.submission_id,
                s.project_name,
                s.team_name,
                s.category,
                s.status,
                s.created_at,
                AVG(sc.weighted_total) as avg_score,
                COUNT(DISTINCT sc.judge_name) as judge_count
            FROM hackathon_submissions s
            LEFT JOIN hackathon_scores sc ON s.submission_id = sc.submission_id AND sc.round = 1
            WHERE 1=1
        """)
        
        query_str = query.text
        params = {}
        
        # Add filters
        if status:
            query_str += " AND s.status = :status"
            params["status"] = status
        
        if category:
            query_str += " AND s.category = :category"
            params["category"] = category
        
        query_str += " GROUP BY s.submission_id ORDER BY s.created_at DESC"
        
        rows = conn.execute(text(query_str), params).fetchall()
        
        submissions = []
        for row in rows:
            submission = SubmissionSummary(
                submission_id=row[0],
                project_name=row[1],
                team_name=row[2],
                category=row[3],
                status=row[4],
                created_at=row[5],
                avg_score=round(row[6], 2) if row[6] else None,
                judge_count=row[7] if row[7] else 0
            )
            submissions.append(submission)
        
        return submissions

@app.get("/api/submission/{submission_id}", response_model=SubmissionDetail)
async def get_submission(submission_id: str):
    """Get detailed information for a specific submission."""
    with engine.connect() as conn:
        # Get submission details
        result = conn.execute(text("SELECT * FROM hackathon_submissions WHERE submission_id = :submission_id"), {"submission_id": submission_id})
        
        submission_row = result.fetchone()
        if not submission_row:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        submission_dict = dict(submission_row._mapping)

        # Get scores
        scores_result = conn.execute(text("""
            SELECT 
                judge_name, 
                innovation, 
                technical_execution,
                market_potential,
                user_experience,
                weighted_total,
                notes
            FROM hackathon_scores 
            WHERE submission_id = :submission_id AND round = 1
            ORDER BY judge_name
        """), {"submission_id": submission_id})
        
        scores = []
        total_score = 0
        for score_row in scores_result.fetchall():
            score_dict = dict(score_row._mapping)
            score_data = {
                'judge_name': score_dict['judge_name'],
                'innovation': score_dict['innovation'],
                'technical_execution': score_dict['technical_execution'],
                'market_potential': score_dict['market_potential'],
                'user_experience': score_dict['user_experience'],
                'weighted_total': score_dict['weighted_total'],
                'notes': json.loads(score_dict['notes']) if score_dict['notes'] else {}
            }
            scores.append(score_data)
            total_score += score_dict['weighted_total']
        
        avg_score = round(total_score / len(scores), 2) if scores else None
        
        # Get research data
        research_result = conn.execute(text("""
            SELECT github_analysis, market_research, technical_assessment
            FROM hackathon_research
            WHERE submission_id = :submission_id
        """), {"submission_id": submission_id})
        
        research_row = research_result.fetchone()
        research = None
        if research_row:
            research_dict = dict(research_row._mapping)
            research = {
                'github_analysis': json.loads(research_dict['github_analysis']) if research_dict['github_analysis'] else None,
                'market_research': json.loads(research_dict['market_research']) if research_dict['market_research'] else None,
                'technical_assessment': json.loads(research_dict['technical_assessment']) if research_dict['technical_assessment'] else None
            }
        
        # Build response
        submission = SubmissionDetail(
            submission_id=submission_dict['submission_id'],
            project_name=submission_dict['project_name'],
            team_name=submission_dict['team_name'],
            category=submission_dict['category'],
            description=submission_dict['description'],
            status=submission_dict['status'],
            created_at=submission_dict['created_at'],
            updated_at=submission_dict['updated_at'],
            github_url=submission_dict['github_url'],
            demo_video_url=submission_dict['demo_video_url'],
            live_demo_url=submission_dict['live_demo_url'],
            tech_stack=submission_dict['tech_stack'],
            how_it_works=submission_dict['how_it_works'],
            problem_solved=submission_dict['problem_solved'],
            coolest_tech=submission_dict['coolest_tech'],
            next_steps=submission_dict['next_steps'],
            scores=scores,
            research=research,
            avg_score=avg_score
        )
        
        return submission

@app.post("/api/submissions", status_code=201)
@limiter.limit("5/minute")
async def create_submission(submission: SubmissionCreate, request: Request):
    """Create a new hackathon submission."""
    logging.info(f"--- CREATE SUBMISSION START ---")
    logging.info(f"Received data: {submission.dict()}")
    
    submission_id = f"{submission.project_name.lower().replace(' ', '-')}-{int(datetime.now().timestamp())}"
    logging.info(f"Generated submission_id: {submission_id}")

    insert_stmt = text("""
        INSERT INTO hackathon_submissions (
            submission_id, project_name, team_name, description, category,
            discord_handle, twitter_handle, github_url, demo_video_url,
            live_demo_url, logo_url, tech_stack, how_it_works,
            problem_solved, coolest_tech, next_steps, status, created_at, updated_at
        ) VALUES (
            :submission_id, :project_name, :team_name, :description, :category,
            :discord_handle, :twitter_handle, :github_url, :demo_video_url,
            :live_demo_url, :logo_url, :tech_stack, :how_it_works,
            :problem_solved, :coolest_tech, :next_steps, :status, :created_at, :updated_at
        )
    """)

    submission_data = submission.dict()
    submission_data.update({
        "submission_id": submission_id,
        "status": "submitted",
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    })
    logging.info(f"Prepared data for insert: {submission_data}")

    with engine.begin() as conn:
        try:
            logging.info("Executing transaction...")
            result = conn.execute(insert_stmt, submission_data)
            logging.info(f"Transaction executed. Result: {result.rowcount} rows affected.")
            # The conn.commit() is handled by the `engine.begin()` context manager
            logging.info(f"Successfully created submission {submission_id} for project {submission.project_name}")
        except Exception as e:
            logging.error(f"Database insert error for project {submission.project_name}: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Could not save submission due to a database error.")
    
    logging.info("--- CREATE SUBMISSION END ---")
    return {"status": "success", "submission_id": submission_id}

@app.get("/api/submission/{submission_id}/feedback")
async def get_submission_feedback(submission_id: str):
    """Get community feedback for a specific submission."""
    with engine.connect() as conn:
        # Get feedback summary
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
        
        for row in result.fetchall():
            row_dict = dict(row._mapping)
            reaction_type, vote_count, voters = row_dict['reaction_type'], row_dict['vote_count'], row_dict['voters']
            total_votes += vote_count
            
            # Map reaction types to display names and emojis
            reaction_map = {
                'hype': {'emoji': '🔥', 'name': 'General Hype'},
                'innovation_creativity': {'emoji': '💡', 'name': 'Innovation & Creativity'},
                'technical_execution': {'emoji': '💻', 'name': 'Technical Execution'},
                'market_potential': {'emoji': '📈', 'name': 'Market Potential'},
                'user_experience': {'emoji': '😍', 'name': 'User Experience'}
            }
            
            reaction_info = reaction_map.get(reaction_type, {'emoji': '❓', 'name': reaction_type})
            
            feedback_summary.append({
                'reaction_type': reaction_type,
                'emoji': reaction_info['emoji'],
                'name': reaction_info['name'],
                'vote_count': vote_count,
                'voters': voters.split(',') if voters else []
            })
        
        return {
            'submission_id': submission_id,
            'total_votes': total_votes,
            'feedback': feedback_summary
        }

@app.get("/api/leaderboard", response_model=List[LeaderboardEntry])
async def get_leaderboard():
    """Get public leaderboard data for published projects."""
    with engine.connect() as conn:
        # Get published projects with scores
        result = conn.execute(text("""
            SELECT 
                s.project_name,
                s.team_name,
                s.category,
                s.demo_video_url as youtube_url,
                AVG(sc.weighted_total) as avg_score
            FROM hackathon_submissions s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            WHERE s.status = 'published' AND sc.round = 1
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
                youtube_url=row_dict['youtube_url']
            )
            entries.append(entry)
            rank += 1
        
        return entries

@app.get("/api/stats")
async def get_stats():
    """Get overall statistics for the dashboard."""
    with engine.connect() as conn:
        # Count by status
        status_result = conn.execute(text("""
            SELECT status, COUNT(*) as count
            FROM hackathon_submissions
            GROUP BY status
        """))
        
        status_counts = {row[0]: row[1] for row in status_result.fetchall()}
        
        # Count by category
        category_result = conn.execute(text("""
            SELECT category, COUNT(*) as count
            FROM hackathon_submissions
            GROUP BY category
        """))
        
        category_counts = {row[0]: row[1] for row in category_result.fetchall()}
        
        # Total submissions
        total_result = conn.execute(text("SELECT COUNT(*) as total FROM hackathon_submissions"))
        total = total_result.scalar_one()
        
        return {
            'total_submissions': total,
            'by_status': status_counts,
            'by_category': category_counts,
            'updated_at': datetime.now().isoformat()
        }

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
            FROM hackathon_submissions s
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
            details_result = conn.execute(text("SELECT * FROM hackathon_submissions WHERE submission_id = :submission_id"), 
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
                AVG(sc.weighted_total) as avg_score
            FROM hackathon_submissions s
            JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            WHERE s.status = 'published' AND sc.round = 1
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
                'youtube_url': row_dict['youtube_url']
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
        uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()