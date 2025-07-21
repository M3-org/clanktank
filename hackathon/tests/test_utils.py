"""
Shared test utilities for Hackathon test suite
Common functions to avoid duplication across test files
"""

import sqlite3
import subprocess
import uuid
import os
from pathlib import Path
from typing import Dict, Any, Optional

from .test_constants import (
    DB_PATH, DEFAULT_VERSION, DEFAULT_TABLE,
    TEST_GITHUB_URL, TEST_DEMO_URL, TEST_LIVE_DEMO_URL,
    TEST_DISCORD_HANDLE, TEST_TWITTER_HANDLE, TEST_CATEGORY,
    TEST_SOLANA_ADDRESS, TEST_TEAM_NAME, TEST_SUBMISSION_ID_START
)


def unique_name(base: str) -> str:
    """Generate unique name for test data"""
    return f"{base}-{uuid.uuid4().hex[:8]}"


def unique_submission_id(start: int = TEST_SUBMISSION_ID_START) -> int:
    """Generate unique submission ID for testing"""
    return start + uuid.uuid4().int % 900  # Generate numbers between start and start+900


def reset_database() -> None:
    """Reset test database by recreating it"""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    subprocess.run(["python3", "-m", "hackathon.backend.create_db"], check=True)


def get_db_connection() -> sqlite3.Connection:
    """Get database connection for testing"""
    return sqlite3.connect(DB_PATH)


def create_test_submission_data(
    version: str = DEFAULT_VERSION,
    submission_id: Optional[int] = None,
    **overrides: Any
) -> Dict[str, Any]:
    """
    Create test submission data with optional overrides
    
    Args:
        version: Schema version ("v1" or "v2")
        submission_id: Custom submission ID (auto-generated if None)
        **overrides: Additional fields to override
    
    Returns:
        Dictionary with test submission data
    """
    base_data = {
        "project_name": unique_name("Test Project"),
        "team_name": TEST_TEAM_NAME,
        "category": TEST_CATEGORY,
        "description": "Test project description for automated testing",
        "discord_handle": TEST_DISCORD_HANDLE,
        "github_url": TEST_GITHUB_URL,
        "demo_video_url": TEST_DEMO_URL
    }
    
    if version == "v2":
        base_data.update({
            "twitter_handle": TEST_TWITTER_HANDLE,
            "live_demo_url": TEST_LIVE_DEMO_URL,
            "problem_solved": "Test problem that this project solves",
            "favorite_part": "Test favorite part of building this project",
            "solana_address": TEST_SOLANA_ADDRESS,
            "how_it_works": "Test explanation of how it works",
            "coolest_tech": "Test coolest technology used",
            "next_steps": "Test next steps for the project"
        })
    
    # Add submission_id if provided
    if submission_id is not None:
        base_data["submission_id"] = submission_id
    
    # Apply any overrides
    base_data.update(overrides)
    return base_data


def create_minimal_submission_data(version: str = DEFAULT_VERSION) -> Dict[str, Any]:
    """Create minimal valid submission data for testing"""
    minimal_data = {
        "project_name": unique_name("Minimal Project"),
        "team_name": TEST_TEAM_NAME,
        "category": TEST_CATEGORY,
        "description": "Minimal test description",
        "discord_handle": TEST_DISCORD_HANDLE,
        "github_url": TEST_GITHUB_URL,
    }
    
    if version == "v2":
        minimal_data.update({
            "how_it_works": "Minimal explanation",
            "problem_solved": "Minimal problem",
            "coolest_tech": "Minimal tech",
            "next_steps": "Minimal next steps"
        })
    
    return minimal_data


def create_invalid_submission_data(version: str = DEFAULT_VERSION) -> Dict[str, Any]:
    """Create invalid submission data for negative testing"""
    return {
        "project_name": "",  # Empty required field
        "team_name": TEST_TEAM_NAME,
        "category": "Invalid Category",  # Invalid category
        "description": "x" * 10000,  # Too long description
        "discord_handle": "invalid_handle",  # Invalid Discord handle format
        "github_url": "not_a_url",  # Invalid URL
    }


def cleanup_test_submissions(submission_ids: list) -> None:
    """Clean up test submissions and related data"""
    if not submission_ids:
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        for submission_id in submission_ids:
            # Clean up in reverse dependency order
            cursor.execute("DELETE FROM hackathon_scores WHERE submission_id = ?", (submission_id,))
            cursor.execute("DELETE FROM hackathon_research WHERE submission_id = ?", (submission_id,))
            cursor.execute("DELETE FROM community_feedback WHERE submission_id = ?", (submission_id,))
            cursor.execute("DELETE FROM hackathon_submissions_v2 WHERE submission_id = ?", (submission_id,))
            cursor.execute("DELETE FROM hackathon_submissions_v1 WHERE submission_id = ?", (submission_id,))
        
        conn.commit()
    finally:
        conn.close()


def get_submission_count(version: str = DEFAULT_VERSION) -> int:
    """Get count of submissions in database"""
    table_name = f"hackathon_submissions_{version}"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    finally:
        conn.close()


def submission_exists(submission_id: int, version: str = DEFAULT_VERSION) -> bool:
    """Check if submission exists in database"""
    table_name = f"hackathon_submissions_{version}"
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"SELECT 1 FROM {table_name} WHERE submission_id = ?", (submission_id,))
        return cursor.fetchone() is not None
    finally:
        conn.close()


def wait_for_async_operation(timeout: int = 30) -> None:
    """Wait for async operations to complete (placeholder for future use)"""
    import time
    time.sleep(1)  # Simple delay, can be enhanced with actual async waiting


def assert_valid_submission_response(response_data: Dict[str, Any], version: str = DEFAULT_VERSION) -> None:
    """Assert that a submission response has valid structure"""
    assert "submission_id" in response_data
    assert "project_name" in response_data
    assert "team_name" in response_data
    assert "category" in response_data
    assert "status" in response_data
    
    if version == "v2":
        assert "how_it_works" in response_data
        assert "problem_solved" in response_data
        assert "coolest_tech" in response_data
        assert "next_steps" in response_data


def assert_valid_leaderboard_response(response_data: Dict[str, Any]) -> None:
    """Assert that a leaderboard response has valid structure"""
    assert "submissions" in response_data
    assert isinstance(response_data["submissions"], list)
    
    if response_data["submissions"]:
        submission = response_data["submissions"][0]
        assert "submission_id" in submission
        assert "project_name" in submission
        assert "total_score" in submission
        assert "rank" in submission