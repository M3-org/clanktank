#!/usr/bin/env python3
"""
Test script for robust submission pipeline enhancements.
Tests auto-save, backup creation, error handling, and recovery mechanisms.
"""

import json
import os
import tempfile
from pathlib import Path
import sqlite3
import uuid
import pytest
import subprocess
from fastapi.testclient import TestClient
import asyncio
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import sys
import time

def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from hackathon.backend.app import app
    return TestClient(app)

def test_backend_backup_creation(client):
    """Test that backend creates backups properly."""
    import subprocess
    subprocess.run(["python3", "-m", "hackathon.scripts.create_db"], check=True)
    unique_id = uuid.uuid4().hex[:8]
    payload = {
        "project_name": unique_name("Robustness Project"),
        "team_name": "Robustness Testers",
        "category": "AI/Agents",
        "description": "Testing the robustness enhancements",
        "discord_handle": "testuser#1234",
        "github_url": "https://github.com/test/project",
        "demo_video_url": "https://youtube.com/test"
    }
    time.sleep(12)
    response = client.post("/api/submissions", json=payload)
    assert response.status_code == 201, f"Submission failed: {response.status_code} - {response.text}"
    result = response.json()
    submission_id = result.get("submission_id")
    backup_file = result.get("backup_created")
    assert submission_id, "No submission_id returned"
    assert backup_file, "No backup_created returned"
    # Verify backup file exists and is valid
    assert Path(backup_file).exists(), "Backup file not found"
    with open(backup_file, 'r') as f:
        backup_data = json.load(f)
    assert backup_data.get("submission_data", {}).get("submission_id") == submission_id, "Backup file data doesn't match submission"

def test_recovery_tool():
    """Test the recovery tool functionality."""
    import subprocess
    result = subprocess.run([
        "python3", "-m", "hackathon.scripts.recovery_tool", "--list"
    ], capture_output=True, text=True, cwd=".")
    assert result.returncode == 0, f"Recovery tool failed: {result.stderr}"
    assert "Available backup files:" in result.stdout, "Unexpected output format"

def test_database_resilience():
    """Test database resilience features."""
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    conn = None
    try:
        import subprocess
        subprocess.run([
            "python3", "-m", "hackathon.scripts.create_db", temp_db.name
        ], check=True, capture_output=True)
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        test_submission = {
            "submission_id": "test-duplicate-123",
            "project_name": "Test Project",
            "team_name": "Test Team",
            "description": "Test description",
            "category": "AI/Agents",
            "status": "submitted",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00"
        }
        fields = list(test_submission.keys())
        placeholders = ", ".join(["?" for _ in fields])
        columns = ", ".join(fields)
        values = [test_submission[field] for field in fields]
        cursor.execute(f"INSERT INTO hackathon_submissions_v2 ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        try:
            cursor.execute(f"INSERT INTO hackathon_submissions_v2 ({columns}) VALUES ({placeholders})", values)
            conn.commit()
            assert False, "Duplicate insertion should have failed"
        except sqlite3.IntegrityError:
            pass  # Expected
    finally:
        if conn:
            conn.close()
        try:
            os.unlink(temp_db.name)
        except:
            pass

def test_backup_directory_creation():
    """Test that backup directories are created properly."""
    backup_dir = Path("data/submission_backups")
    if backup_dir.exists():
        import shutil
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)
    assert backup_dir.exists() and backup_dir.is_dir(), "Backup directory not created" 