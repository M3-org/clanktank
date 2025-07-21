"""
Database helpers for Hackathon test suite
Common database operations to avoid duplication
"""

import sqlite3
from typing import List, Tuple, Optional, Dict, Any

from .test_utils import get_db_connection
from .test_constants import DEFAULT_VERSION


def insert_test_feedback(
    submission_id: str,
    feedback_data: Optional[List[Tuple[str, str, str, float]]] = None
) -> None:
    """
    Insert test feedback data for a submission
    
    Args:
        submission_id: Target submission ID
        feedback_data: List of (user_id, nickname, reaction_type, score) tuples
    """
    if feedback_data is None:
        feedback_data = [
            ("user1", "Alice", "hype", 1.0),
            ("user2", "Bob", "innovation_creativity", 1.0),
            ("user3", "Charlie", "technical_execution", 1.0),
        ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for user_id, nickname, reaction, score in feedback_data:
            cursor.execute("""
                INSERT INTO community_feedback 
                (submission_id, discord_user_id, discord_user_nickname, reaction_type, score_adjustment)
                VALUES (?, ?, ?, ?, ?)
            """, (submission_id, user_id, nickname, reaction, score))
        conn.commit()
    finally:
        conn.close()


def insert_test_research(
    submission_id: int,
    research_data: Optional[Dict[str, Any]] = None,
    version: str = DEFAULT_VERSION
) -> None:
    """
    Insert test research data for a submission
    
    Args:
        submission_id: Target submission ID
        research_data: Research data dictionary
        version: Schema version
    """
    if research_data is None:
        research_data = {
            "github_analysis": {
                "repo_exists": True,
                "commit_count": 25,
                "contributors": 2,
                "languages": ["Python", "TypeScript"],
                "has_readme": True,
                "last_commit_days_ago": 1
            },
            "market_research": {
                "market_size": "Large",
                "competitors": ["Competitor A", "Competitor B"],
                "differentiation": "Novel approach to problem solving"
            },
            "technical_analysis": {
                "complexity_score": 8.5,
                "innovation_score": 9.0,
                "feasibility_score": 7.5
            }
        }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO hackathon_research 
            (submission_id, github_analysis, market_research, technical_analysis, version)
            VALUES (?, ?, ?, ?, ?)
        """, (
            submission_id,
            str(research_data.get("github_analysis", {})),
            str(research_data.get("market_research", {})),
            str(research_data.get("technical_analysis", {})),
            version
        ))
        conn.commit()
    finally:
        conn.close()


def insert_test_scores(
    submission_id: int,
    scores_data: Optional[Dict[str, float]] = None,
    version: str = DEFAULT_VERSION
) -> None:
    """
    Insert test scores for a submission
    
    Args:
        submission_id: Target submission ID
        scores_data: Dictionary of judge scores
        version: Schema version
    """
    if scores_data is None:
        scores_data = {
            "aimarc_score": 8.5,
            "aishaw_score": 7.8,
            "peepo_score": 9.2,
            "spartan_score": 8.0,
            "community_score": 2.5,
            "total_score": 8.4
        }
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO hackathon_scores 
            (submission_id, aimarc_score, aishaw_score, peepo_score, spartan_score, 
             community_score, total_score, version)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            submission_id,
            scores_data.get("aimarc_score"),
            scores_data.get("aishaw_score"),
            scores_data.get("peepo_score"),
            scores_data.get("spartan_score"),
            scores_data.get("community_score"),
            scores_data.get("total_score"),
            version
        ))
        conn.commit()
    finally:
        conn.close()


def get_submission_status(submission_id: int, version: str = DEFAULT_VERSION) -> Optional[str]:
    """
    Get the status of a submission
    
    Args:
        submission_id: Target submission ID
        version: Schema version
    
    Returns:
        Submission status or None if not found
    """
    table_name = f"hackathon_submissions_{version}"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT status FROM {table_name} WHERE submission_id = ?", (submission_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        conn.close()


def update_submission_status(
    submission_id: int,
    new_status: str,
    version: str = DEFAULT_VERSION
) -> bool:
    """
    Update the status of a submission
    
    Args:
        submission_id: Target submission ID
        new_status: New status value
        version: Schema version
    
    Returns:
        True if update succeeded, False otherwise
    """
    table_name = f"hackathon_submissions_{version}"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            f"UPDATE {table_name} SET status = ? WHERE submission_id = ?",
            (new_status, submission_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_all_submissions(version: str = DEFAULT_VERSION) -> List[Dict[str, Any]]:
    """
    Get all submissions from database
    
    Args:
        version: Schema version
    
    Returns:
        List of submission dictionaries
    """
    table_name = f"hackathon_submissions_{version}"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()
        
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def get_submission_with_scores(submission_id: int, version: str = DEFAULT_VERSION) -> Optional[Dict[str, Any]]:
    """
    Get submission with scores data
    
    Args:
        submission_id: Target submission ID
        version: Schema version
    
    Returns:
        Combined submission and scores data or None if not found
    """
    table_name = f"hackathon_submissions_{version}"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"""
            SELECT s.*, sc.aimarc_score, sc.aishaw_score, sc.peepo_score, 
                   sc.spartan_score, sc.community_score, sc.total_score
            FROM {table_name} s
            LEFT JOIN hackathon_scores sc ON s.submission_id = sc.submission_id
            WHERE s.submission_id = ?
        """, (submission_id,))
        
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        
        return dict(zip(columns, row)) if row else None
    finally:
        conn.close()


def cleanup_all_test_data() -> None:
    """Clean up all test data from database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Delete test submissions (assuming they have test ID range >= 1000)
        cursor.execute("DELETE FROM hackathon_scores WHERE submission_id >= 1000")
        cursor.execute("DELETE FROM hackathon_research WHERE submission_id >= 1000")
        cursor.execute("DELETE FROM community_feedback WHERE submission_id >= 1000")
        cursor.execute("DELETE FROM hackathon_submissions_v2 WHERE submission_id >= 1000")
        cursor.execute("DELETE FROM hackathon_submissions_v1 WHERE submission_id >= 1000")
        
        conn.commit()
    finally:
        conn.close()


def get_table_counts() -> Dict[str, int]:
    """
    Get counts of all main tables for debugging
    
    Returns:
        Dictionary with table names and counts
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    tables = [
        "hackathon_submissions_v1",
        "hackathon_submissions_v2",
        "hackathon_scores",
        "hackathon_research",
        "community_feedback"
    ]
    
    counts = {}
    
    try:
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                counts[table] = cursor.fetchone()[0]
            except sqlite3.OperationalError:
                counts[table] = 0  # Table doesn't exist
    finally:
        conn.close()
    
    return counts


def verify_database_integrity() -> Dict[str, bool]:
    """
    Verify database integrity for testing
    
    Returns:
        Dictionary with integrity check results
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    checks = {}
    
    try:
        # Check if main tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = [
            "hackathon_submissions_v1",
            "hackathon_submissions_v2",
            "hackathon_scores",
            "hackathon_research",
            "community_feedback"
        ]
        
        for table in required_tables:
            checks[f"table_{table}_exists"] = table in existing_tables
        
        # Check for foreign key constraints
        cursor.execute("PRAGMA foreign_keys")
        checks["foreign_keys_enabled"] = cursor.fetchone()[0] == 1
        
    finally:
        conn.close()
    
    return checks