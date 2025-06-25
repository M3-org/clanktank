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

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
# Get the repository root directory (3 levels up from dashboard/app.py)
REPO_ROOT = Path(__file__).parent.parent.parent.parent
HACKATHON_DB_PATH = os.getenv('HACKATHON_DB_PATH', str(REPO_ROOT / 'data' / 'hackathon.db'))
STATIC_DATA_DIR = os.getenv('STATIC_DATA_DIR', str(Path(__file__).parent / 'frontend' / 'public' / 'data'))

# Create FastAPI app
app = FastAPI(
    title="Clank Tank Hackathon API",
    description="API for hackathon admin dashboard and public leaderboard",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class LeaderboardEntry(BaseModel):
    rank: int
    project_name: str
    team_name: str
    category: str
    final_score: float
    youtube_url: Optional[str] = None

# Database connection context manager
@contextmanager
def get_db():
    conn = sqlite3.connect(HACKATHON_DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

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
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Base query
        query = """
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
        """
        
        params = []
        
        # Add filters
        if status:
            query += " AND s.status = ?"
            params.append(status)
        
        if category:
            query += " AND s.category = ?"
            params.append(category)
        
        query += " GROUP BY s.submission_id ORDER BY s.created_at DESC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        submissions = []
        for row in rows:
            submission = SubmissionSummary(
                submission_id=row['submission_id'],
                project_name=row['project_name'],
                team_name=row['team_name'],
                category=row['category'],
                status=row['status'],
                created_at=row['created_at'],
                avg_score=round(row['avg_score'], 2) if row['avg_score'] else None,
                judge_count=row['judge_count'] if row['judge_count'] else 0
            )
            submissions.append(submission)
        
        return submissions

@app.get("/api/submission/{submission_id}", response_model=SubmissionDetail)
async def get_submission(submission_id: str):
    """Get detailed information for a specific submission."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get submission details
        cursor.execute("""
            SELECT * FROM hackathon_submissions 
            WHERE submission_id = ?
        """, (submission_id,))
        
        submission_row = cursor.fetchone()
        if not submission_row:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Get scores
        cursor.execute("""
            SELECT 
                judge_name, 
                innovation, 
                technical_execution,
                market_potential,
                user_experience,
                weighted_total,
                notes
            FROM hackathon_scores 
            WHERE submission_id = ? AND round = 1
            ORDER BY judge_name
        """, (submission_id,))
        
        scores = []
        total_score = 0
        for score_row in cursor.fetchall():
            score_data = {
                'judge_name': score_row['judge_name'],
                'innovation': score_row['innovation'],
                'technical_execution': score_row['technical_execution'],
                'market_potential': score_row['market_potential'],
                'user_experience': score_row['user_experience'],
                'weighted_total': score_row['weighted_total'],
                'notes': json.loads(score_row['notes']) if score_row['notes'] else {}
            }
            scores.append(score_data)
            total_score += score_row['weighted_total']
        
        avg_score = round(total_score / len(scores), 2) if scores else None
        
        # Get research data
        cursor.execute("""
            SELECT github_analysis, market_research, technical_assessment
            FROM hackathon_research
            WHERE submission_id = ?
        """, (submission_id,))
        
        research_row = cursor.fetchone()
        research = None
        if research_row:
            research = {
                'github_analysis': json.loads(research_row['github_analysis']) if research_row['github_analysis'] else None,
                'market_research': json.loads(research_row['market_research']) if research_row['market_research'] else None,
                'technical_assessment': json.loads(research_row['technical_assessment']) if research_row['technical_assessment'] else None
            }
        
        # Build response
        submission = SubmissionDetail(
            submission_id=submission_row['submission_id'],
            project_name=submission_row['project_name'],
            team_name=submission_row['team_name'],
            category=submission_row['category'],
            description=submission_row['description'],
            status=submission_row['status'],
            created_at=submission_row['created_at'],
            updated_at=submission_row['updated_at'],
            github_url=submission_row['github_url'],
            demo_video_url=submission_row['demo_video_url'],
            live_demo_url=submission_row['live_demo_url'],
            tech_stack=submission_row['tech_stack'],
            how_it_works=submission_row['how_it_works'],
            problem_solved=submission_row['problem_solved'],
            coolest_tech=submission_row['coolest_tech'],
            next_steps=submission_row['next_steps'],
            scores=scores,
            research=research,
            avg_score=avg_score
        )
        
        return submission

@app.get("/api/submission/{submission_id}/feedback")
async def get_submission_feedback(submission_id: str):
    """Get community feedback for a specific submission."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get feedback summary
        cursor.execute("""
            SELECT 
                reaction_type,
                COUNT(*) as vote_count,
                GROUP_CONCAT(discord_user_nickname) as voters
            FROM community_feedback 
            WHERE submission_id = ?
            GROUP BY reaction_type
            ORDER BY vote_count DESC
        """, (submission_id,))
        
        feedback_summary = []
        total_votes = 0
        
        for row in cursor.fetchall():
            reaction_type, vote_count, voters = row
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
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Get published projects with scores
        cursor.execute("""
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
        """)
        
        entries = []
        rank = 1
        
        for row in cursor.fetchall():
            entry = LeaderboardEntry(
                rank=rank,
                project_name=row['project_name'],
                team_name=row['team_name'],
                category=row['category'],
                final_score=round(row['avg_score'], 2),
                youtube_url=row['youtube_url']
            )
            entries.append(entry)
            rank += 1
        
        return entries

@app.get("/api/stats")
async def get_stats():
    """Get overall statistics for the dashboard."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Count by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM hackathon_submissions
            GROUP BY status
        """)
        
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Count by category
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM hackathon_submissions
            GROUP BY category
        """)
        
        category_counts = {row['category']: row['count'] for row in cursor.fetchall()}
        
        # Total submissions
        cursor.execute("SELECT COUNT(*) as total FROM hackathon_submissions")
        total = cursor.fetchone()['total']
        
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
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Generate submissions.json
        cursor.execute("""
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
        """)
        
        submissions = []
        for row in cursor.fetchall():
            submissions.append({
                'submission_id': row['submission_id'],
                'project_name': row['project_name'],
                'team_name': row['team_name'],
                'category': row['category'],
                'status': row['status'],
                'created_at': row['created_at'],
                'avg_score': round(row['avg_score'], 2) if row['avg_score'] else None,
                'judge_count': row['judge_count'] if row['judge_count'] else 0
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
            cursor.execute("SELECT * FROM hackathon_submissions WHERE submission_id = ?", 
                         (submission['submission_id'],))
            details = cursor.fetchone()
            
            with open(submission_dir / f"{submission['submission_id']}.json", 'w') as f:
                json.dump(dict(details), f, indent=2)
        
        # Generate leaderboard.json
        cursor.execute("""
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
        """)
        
        leaderboard = []
        rank = 1
        
        for row in cursor.fetchall():
            leaderboard.append({
                'rank': rank,
                'project_name': row['project_name'],
                'team_name': row['team_name'],
                'category': row['category'],
                'final_score': round(row['avg_score'], 2),
                'youtube_url': row['youtube_url']
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