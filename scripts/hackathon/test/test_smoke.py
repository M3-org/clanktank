#!/usr/bin/env python3
"""
Minimal smoke test for the hackathon data pipeline.
Verifies that the core pipeline scripts run without error.
"""
import subprocess
import sqlite3
import os

DB_PATH = os.path.join("data", "hackathon.db")
TEST_ID = "SMOKE_TEST_001"


def run(script_path, *args, check=True):
    cmd = ["python3", script_path] + list(args)
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True)
    print(result.stdout.decode())
    print(result.stderr.decode())
    if check and result.returncode != 0:
        print(f"FAILED: {' '.join(cmd)}")
        exit(1)
    return result


def setup_db():
    # Recreate the database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    run("scripts/hackathon/create_hackathon_db.py")
    # Insert a test record
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO hackathon_submissions (submission_id, project_name, team_name, description, category, status) VALUES (?, ?, ?, ?, ?, ?)",
                   (TEST_ID, "Smoke Test Project", "Smoke Testers", "A test submission for smoke testing.", "test", "submitted"))
    conn.commit()
    conn.close()
    print(f"Inserted test submission with ID {TEST_ID}")


def main():
    setup_db()
    # Run research script
    run("scripts/hackathon/hackathon_research.py", "--submission-id", TEST_ID)
    # Run scoring script
    run("scripts/hackathon/hackathon_manager.py", "--score", "--submission-id", TEST_ID)
    # Run episode generation
    run("scripts/hackathon/generate_episode.py", "--submission-id", TEST_ID)
    print("Smoke test completed successfully.")

if __name__ == "__main__":
    main() 