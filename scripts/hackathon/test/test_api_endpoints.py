import os
import subprocess
import time
import pytest
import httpx
import sqlite3
from pathlib import Path

DB_PATH = "data/hackathon.db"
API_HOST = "127.0.0.1"
API_PORT = 8001
API_URL = f"http://{API_HOST}:{API_PORT}"

@pytest.fixture(scope="session", autouse=True)
def reset_db():
    # Remove and recreate the test DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    subprocess.run(["python3", "scripts/hackathon/create_hackathon_db.py"], check=True)
    yield
    # Cleanup if needed

@pytest.fixture(scope="session")
def api_server():
    # Start FastAPI app in a subprocess
    proc = subprocess.Popen([
        "uvicorn", "scripts.hackathon.dashboard.app:app",
        "--host", API_HOST, "--port", str(API_PORT)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Wait for server to start
    for _ in range(30):
        try:
            httpx.get(f"{API_URL}/")
            break
        except Exception:
            time.sleep(0.5)
    else:
        proc.terminate()
        raise RuntimeError("FastAPI server did not start in time")
    yield
    proc.terminate()
    proc.wait()

@pytest.fixture
def client(api_server):
    with httpx.Client(base_url=API_URL) as c:
        yield c

# Example valid v1 and v2 submissions
v1_submission = {
    "project_name": "Test V1 Project",
    "team_name": "Team V1",
    "description": "Testing v1 schema",
    "category": "ai",
    "discord_handle": "test#0001",
    "twitter_handle": "@testv1",
    "github_url": "https://github.com/test/v1",
    "demo_video_url": "https://youtu.be/testv1",
    "live_demo_url": "https://testv1.live",
    "logo_url": "https://testv1.live/logo.png",
    "tech_stack": "Python, FastAPI",
    "how_it_works": "It just works.",
    "problem_solved": "Testing migration.",
    "coolest_tech": "The hybrid workflow!",
    "next_steps": "Ship it!"
}
v2_submission = {
    "project_name": "Test V2 Project",
    "team_name": "Team V2",
    "summary": "Testing v2 schema",
    "category": "ai",
    "discord_handle": "test#0002",
    "twitter_handle": "@testv2",
    "github_url": "https://github.com/test/v2",
    "demo_video_url": "https://youtu.be/testv2",
    "live_demo_url": "https://testv2.live",
    "image_url": "https://testv2.live/image.png",
    "tech_stack": "Python, FastAPI",
    "how_it_works": "It just works.",
    "problem_solved": "Testing migration.",
    "favorite_part": "The hybrid workflow!"
}

def test_post_v1_submission(client):
    resp = client.post("/api/v1/submissions", json=v1_submission)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert "submission_id" in data

def test_post_v2_submission(client):
    resp = client.post("/api/v2/submissions", json=v2_submission)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert "submission_id" in data

def test_get_v1_submissions(client):
    resp = client.get("/api/v1/submissions")
    assert resp.status_code == 200
    submissions = resp.json()
    assert isinstance(submissions, list)
    assert any(s["project_name"] == v1_submission["project_name"] for s in submissions)

def test_get_v2_submissions(client):
    resp = client.get("/api/v2/submissions")
    assert resp.status_code == 200
    submissions = resp.json()
    assert isinstance(submissions, list)
    assert any(s["project_name"] == v2_submission["project_name"] for s in submissions)

def test_get_v1_submission_detail(client):
    # Get the first v1 submission
    resp = client.get("/api/v1/submissions")
    sub_id = resp.json()[0]["submission_id"]
    detail = client.get(f"/api/v1/submissions/{sub_id}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["submission_id"] == sub_id
    assert data["project_name"] == v1_submission["project_name"]

def test_get_v2_submission_detail(client):
    resp = client.get("/api/v2/submissions")
    sub_id = resp.json()[0]["submission_id"]
    detail = client.get(f"/api/v2/submissions/{sub_id}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["submission_id"] == sub_id
    assert data["project_name"] == v2_submission["project_name"]

def test_v1_stats(client):
    resp = client.get("/api/v1/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_submissions" in data
    assert "by_status" in data
    assert "by_category" in data
    assert data["total_submissions"] >= 0

def test_v2_stats(client):
    resp = client.get("/api/v2/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_submissions" in data
    assert "by_status" in data
    assert "by_category" in data
    assert data["total_submissions"] >= 0

def test_v1_leaderboard(client):
    resp = client.get("/api/v1/leaderboard")
    assert resp.status_code == 200
    leaderboard = resp.json()
    assert isinstance(leaderboard, list)

def test_v2_leaderboard(client):
    resp = client.get("/api/v2/leaderboard")
    assert resp.status_code == 200
    leaderboard = resp.json()
    assert isinstance(leaderboard, list)

def test_feedback_no_data(client):
    # Use a random submission_id that does not exist
    resp = client.get("/api/submission/NO_SUCH_ID/feedback")
    assert resp.status_code == 200
    data = resp.json()
    assert data["submission_id"] == "NO_SUCH_ID"
    assert data["total_votes"] == 0
    assert data["feedback"] == []

def test_feedback_with_data(client):
    # Insert feedback for a v1 submission
    resp = client.get("/api/v1/submissions")
    sub_id = resp.json()[0]["submission_id"]
    # Insert feedback directly into DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO community_feedback (submission_id, discord_user_id, discord_user_nickname, reaction_type, score_adjustment)
        VALUES (?, ?, ?, ?, ?)
    """, (sub_id, "12345", "TestUser", "hype", 1.0))
    conn.commit()
    conn.close()
    # Now check feedback endpoint
    resp2 = client.get(f"/api/submission/{sub_id}/feedback")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["submission_id"] == sub_id
    assert data["total_votes"] == 1
    assert data["feedback"][0]["reaction_type"] == "hype"
    assert "TestUser" in data["feedback"][0]["voters"]

def insert_sample_feedback(submission_id):
    feedback_data = [
        ("user1", "Alice", "hype", 1.0),
        ("user2", "Bob", "innovation_creativity", 1.0),
        ("user3", "Charlie", "technical_execution", 1.0),
        ("user4", "Dana", "market_potential", 1.0),
        ("user5", "Eve", "user_experience", 1.0),
    ]
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for user_id, nickname, reaction, score in feedback_data:
        cursor.execute("""
            INSERT INTO community_feedback (submission_id, discord_user_id, discord_user_nickname, reaction_type, score_adjustment)
            VALUES (?, ?, ?, ?, ?)
        """, (submission_id, user_id, nickname, reaction, score))
    conn.commit()
    conn.close()

def test_feedback_all_categories(client):
    # Create a new v1 submission for this test
    new_submission = v1_submission.copy()
    new_submission["project_name"] = "Feedback Test Project"
    resp_post = client.post("/api/v1/submissions", json=new_submission)
    sub_id = resp_post.json()["submission_id"]
    insert_sample_feedback(sub_id)
    resp2 = client.get(f"/api/submission/{sub_id}/feedback")
    assert resp2.status_code == 200
    data = resp2.json()
    assert data["submission_id"] == sub_id
    assert data["total_votes"] == 5
    categories = {f["reaction_type"] for f in data["feedback"]}
    assert categories == {"hype", "innovation_creativity", "technical_execution", "market_potential", "user_experience"}
    voters = set()
    for f in data["feedback"]:
        voters.update(f["voters"])
    assert voters == {"Alice", "Bob", "Charlie", "Dana", "Eve"} 