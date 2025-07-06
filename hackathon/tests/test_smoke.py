#!/usr/bin/env python3
"""
Minimal smoke test for the hackathon data pipeline.
Verifies that the core pipeline scripts run without error.
"""
import subprocess
import sqlite3
import os
import sys
import uuid

DB_PATH = os.path.join("data", "hackathon.db")
TEST_ID = "SMOKE_TEST_001"
DEFAULT_VERSION = "v2"
DEFAULT_TABLE = f"hackathon_submissions_{DEFAULT_VERSION}"


def run(script_path, *args, check=True):
    if script_path.endswith("create_db.py"):
        cmd = ["python3", "-m", "hackathon.backend.create_db"]
        cmd.extend(args)
    else:
        cmd = ["python3", "-m"]
        module = script_path.replace("/", ".").replace(".py", "")
        cmd.append(module)
        cmd.extend(args)
    result = subprocess.run(cmd, capture_output=True)
    print("STDOUT:\n" + result.stdout.decode())
    print("STDERR:\n" + result.stderr.decode())
    if check and result.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}")
        sys.exit(1)
    return result


def setup_db():
    # Recreate the database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    run("hackathon/backend/create_db.py")
    # Insert a test record
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO {DEFAULT_TABLE} (submission_id, project_name, team_name, description, category, status) VALUES (?, ?, ?, ?, ?, ?)",
                   (TEST_ID, "Smoke Test Project", "Smoke Testers", "A test submission for smoke testing.", "test", "submitted"))
    conn.commit()
    conn.close()
    print(f"Inserted test submission with ID {TEST_ID}")


def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"


def test_smoke_pipeline():
    # ...
    payload = {
        "project_name": unique_name("SMOKE_TEST_001"),
        "team_name": "Smoke Test Team",
        "category": "AI/Agents",
        "description": "Smoke test project description.",
        "discord_handle": "smoke#1234",
        "github_url": "https://github.com/test/smoke",
        "demo_video_url": "https://youtube.com/smoke"
        # Optional fields can be added as needed
    }
    # ...rest of the test remains unchanged, but all POSTs should use this payload and add any missing required fields if needed...


def main():
    setup_db()
    # Run research script
    run("hackathon/backend/research.py", "--submission-id", TEST_ID, "--version", DEFAULT_VERSION)
    # Run scoring script
    run("hackathon/backend/hackathon_manager.py", "--score", "--submission-id", TEST_ID, "--version", DEFAULT_VERSION)
    # Run episode generation
    run("hackathon/scripts/generate_episode.py", "--submission-id", TEST_ID, "--version", DEFAULT_VERSION)
    print("Smoke test completed successfully.")

if __name__ == "__main__":
    main() 