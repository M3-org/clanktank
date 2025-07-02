#!/usr/bin/env python3
"""
Full end-to-end test for the hackathon system.
Simulates a real proposal submission and runs the entire pipeline, logging all output to LOGS.txt.
"""
import subprocess
import requests
import sqlite3
import os
import sys
import json
from datetime import datetime

DB_PATH = os.path.join("data", "hackathon.db")
LOG_PATH = "LOGS.txt"
API_URL = "http://127.0.0.1:8000/api/submissions"

# Example submission data
submission_data = {
    "project_name": "Test Project E2E",
    "team_name": "Testers United",
    "description": "A full pipeline test project.",
    "category": "ai",
    "discord_handle": "testuser#1234",
    "twitter_handle": "@testuser",
    "github_url": "https://github.com/testuser/testproject",
    "demo_video_url": "https://youtu.be/testvideo",
    "live_demo_url": "https://testproject.live",
    "logo_url": "https://testproject.live/logo.png",
    "tech_stack": "Python, FastAPI, React",
    "how_it_works": "It works by magic.",
    "problem_solved": "Testing full pipeline reliability.",
    "coolest_tech": "Automated E2E testing.",
    "next_steps": "Deploy to production."
}


def log(msg):
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")
    print(msg)


def run(cmd, input_data=None):
    log(f"\nRunning: {' '.join(cmd)}")
    if input_data:
        result = subprocess.run(cmd, input=input_data.encode(), capture_output=True)
    else:
        result = subprocess.run(cmd, capture_output=True)
    log("STDOUT:\n" + result.stdout.decode())
    log("STDERR:\n" + result.stderr.decode())
    if result.returncode != 0:
        log(f"FAILED: {' '.join(cmd)}")
        sys.exit(1)
    return result


def reset_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    run(["python3", "scripts/hackathon/create_hackathon_db.py"])
    log("Database reset.")


def start_api():
    # Start FastAPI backend in background
    import subprocess
    import time
    log("Starting FastAPI backend...")
            proc = subprocess.Popen(["uvicorn", "hackathon.dashboard.app:app", "--port", "8000"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Wait for server to start
    for _ in range(20):
        try:
            requests.get(API_URL)
            log("FastAPI backend is up.")
            return proc
        except Exception:
            time.sleep(0.5)
    log("ERROR: FastAPI backend did not start in time.")
    proc.terminate()
    sys.exit(1)


def stop_api(proc):
    proc.terminate()
    proc.wait()
    log("FastAPI backend stopped.")


def submit_proposal():
    log("Submitting proposal via API...")
    resp = requests.post(API_URL, json=submission_data)
    log(f"API Response: {resp.status_code}\n{resp.text}")
    if resp.status_code != 201:
        log("Submission failed!")
        sys.exit(1)
    submission_id = resp.json().get("submission_id")
    log(f"Submission ID: {submission_id}")
    return submission_id


def main():
    # Clear log
    with open(LOG_PATH, "w") as f:
        f.write(f"Full Pipeline Test Log - {datetime.now()}\n\n")
    reset_db()
    # Start backend
    api_proc = start_api()
    try:
        # Submit proposal
        submission_id = submit_proposal()
        # Run research
        run(["python3", "scripts/hackathon/hackathon_research.py", "--submission-id", submission_id])
        # Run scoring
        run(["python3", "scripts/hackathon/hackathon_manager.py", "--score", "--submission-id", submission_id])
        # Run episode generation
        run(["python3", "scripts/hackathon/generate_episode.py", "--submission-id", submission_id])
        log("\nFull pipeline test completed successfully.")
    finally:
        stop_api(api_proc)

if __name__ == "__main__":
    main() 