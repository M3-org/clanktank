import os
import subprocess
import time
import pytest
import httpx
import sqlite3
import uuid

DB_PATH = "data/hackathon.db"
API_HOST = "127.0.0.1"
API_PORT = 8001
API_URL = f"http://{API_HOST}:{API_PORT}"

@pytest.fixture(scope="session", autouse=True)
def reset_db():
    # Remove and recreate the test DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    subprocess.run(["python3", "-m", "hackathon.scripts.create_db"], check=True)
    yield
    # Cleanup if needed

@pytest.fixture(scope="session")
def api_server():
    # Start FastAPI app in a subprocess
    proc = subprocess.Popen([
                    "uvicorn", "hackathon.backend.app:app",
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

def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"

# v1 required fields
v1_submission = {
    "project_name": unique_name("Test V1 Project"),
    "team_name": "Team V1",
    "category": "AI/Agents",
    "description": "Test V1 project description.",
    "discord_handle": "testv1#1234",
    "twitter_handle": "",
    "github_url": "https://github.com/test/v1",
    "demo_video_url": "https://youtube.com/testv1",
    "live_demo_url": "",
    "logo_url": "",
    "tech_stack": "",
    "how_it_works": "",
    "problem_solved": "",
    "coolest_tech": "",
    "next_steps": ""
}

# v2 required fields + recommended optional fields for full coverage
v2_submission = {
    "project_name": unique_name("Test V2 Project"),
    "team_name": "Team V2",
    "category": "AI/Agents",
    "description": "Test V2 project description.",
    "discord_handle": "testv2#1234",
    "twitter_handle": "@testv2",
    "github_url": "https://github.com/test/v2",
    "demo_video_url": "https://youtube.com/testv2",
    "live_demo_url": "https://testv2.live",
    "project_image": "/api/uploads/testv2-image.png",
    "tech_stack": "Python, FastAPI, React",
    "how_it_works": "Explains how v2 project works.",
    "problem_solved": "Describes the problem solved by v2.",
    "favorite_part": "The best part of v2.",
    "solana_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
}

def test_post_submission_v1():
    subprocess.run(["python3", "-m", "hackathon.scripts.create_db"], check=True)
    payload = {
        "project_name": unique_name("Test Project V1"),
        "team_name": "Team V1",
        "category": "AI/Agents",
        "description": "Test V1 description",
        "discord_handle": "testv1#1234",
        "github_url": "https://github.com/test/v1",
        "demo_video_url": "https://youtube.com/testv1"
    }
    # ... rest of test ...

def test_get_submissions(client):
    # Create a submission first
    resp_post = client.post("/api/submissions", json=v2_submission)
    assert resp_post.status_code == 201
    # Now GET
    resp = client.get("/api/submissions")
    assert resp.status_code == 200
    submissions = resp.json()
    assert isinstance(submissions, list)
    assert any(s["project_name"] == v2_submission["project_name"] for s in submissions)

def test_get_submission_detail(client):
    # Create a submission first
    resp_post = client.post("/api/submissions", json=v2_submission)
    assert resp_post.status_code == 201
    sub_id = resp_post.json().get("submission_id")
    assert sub_id
    detail = client.get(f"/api/submissions/{sub_id}")
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
    resp_post = client.post("/api/submissions", json=new_submission)
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

def test_get_v2_submission_schema(client):
    resp = client.get("/api/v2/submission-schema")
    assert resp.status_code == 200
    schema = resp.json()
    assert isinstance(schema, list)
    assert any(f["name"] == "project_name" for f in schema)
    assert any(f["name"] == "team_name" for f in schema)
    # Check for required field metadata
    for field in schema:
        assert "name" in field
        assert "label" in field
        assert "type" in field
        assert "required" in field

def test_post_latest_submission(client):
    # Use v2_submission but with v2 field names mapped to v2 schema
    latest_submission = v2_submission.copy()
    latest_submission["project_name"] = "Test Latest Project"
    latest_submission["team_name"] = "Team Latest"
    latest_submission["description"] = "Testing latest schema"
    latest_submission["category"] = "AI/Agents"
    latest_submission["discord_handle"] = "test#0003"
    latest_submission["twitter_handle"] = "@testlatest"
    latest_submission["github_url"] = "https://github.com/test/latest"
    latest_submission["demo_video_url"] = "https://youtu.be/testlatest"
    latest_submission["live_demo_url"] = "https://testlatest.live"
    latest_submission["image_url"] = "https://testlatest.live/image.png"
    latest_submission["tech_stack"] = "Python, FastAPI"
    latest_submission["how_it_works"] = "It just works."
    latest_submission["problem_solved"] = "Testing migration."
    latest_submission["favorite_part"] = "The hybrid workflow!"
    latest_submission["test_field"] = "Test value for v2"
    resp = client.post("/api/submissions", json=latest_submission)
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert "submission_id" in data

def test_get_latest_submissions(client):
    resp = client.get("/api/submissions")
    assert resp.status_code == 200
    submissions = resp.json()
    assert isinstance(submissions, list)
    assert any(s["project_name"] == "Test Latest Project" for s in submissions)

def test_get_latest_leaderboard(client):
    resp = client.get("/api/leaderboard")
    assert resp.status_code == 200
    leaderboard = resp.json()
    assert isinstance(leaderboard, list)

def test_get_latest_stats(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_submissions" in data
    assert "by_status" in data
    assert "by_category" in data
    assert data["total_submissions"] >= 0

def test_get_latest_submission_schema(client):
    resp = client.get("/api/submission-schema")
    assert resp.status_code == 200
    schema = resp.json()
    assert isinstance(schema, list)
    assert any(f["name"] == "project_name" for f in schema)
    assert any(f["name"] == "team_name" for f in schema)
    for field in schema:
        assert "name" in field
        assert "label" in field
        assert "type" in field
        assert "required" in field

def test_get_feedback_latest(client):
    # Use a known submission_id with feedback in the test DB
    submission_id = "test-feedback-001"
    resp = client.get(f"/api/feedback/{submission_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "submission_id" in data
    assert "total_votes" in data
    assert "feedback" in data
    assert isinstance(data["feedback"], list)
    if data["feedback"]:
        item = data["feedback"][0]
        assert "reaction_type" in item
        assert "emoji" in item
        assert "name" in item
        assert "vote_count" in item
        assert "voters" in item

def test_get_feedback_versioned(client):
    submission_id = "test-feedback-001"
    resp = client.get(f"/api/v2/feedback/{submission_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["submission_id"] == submission_id

def test_get_feedback_legacy(client):
    submission_id = "test-feedback-001"
    resp = client.get(f"/api/submission/{submission_id}/feedback")
    assert resp.status_code == 200
    data = resp.json()
    assert data["submission_id"] == submission_id

def test_feedback_not_found(client):
    resp = client.get("/api/feedback/doesnotexist123")
    assert resp.status_code == 200  # Returns empty feedback, not 404 