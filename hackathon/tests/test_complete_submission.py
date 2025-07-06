#!/usr/bin/env python3
"""
Test complete submission flow with image upload
"""

import sys
import uuid
import io
import subprocess
import pytest
from PIL import Image
import time

def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from hackathon.backend.app import app
    return TestClient(app)

def test_complete_submission(client):
    """Test the complete submission flow including image upload"""
    subprocess.run(["python3", "-m", "hackathon.backend.create_db"], check=True)
    unique_id = uuid.uuid4().hex[:8]
    project_name = f"Test Project Complete {unique_id}"

    # Use a fake Discord Bearer token for both requests
    headers = {"Authorization": "Bearer test-token-123"}
    # Step 0: Create a valid submission before uploading the image
    submission_payload = {
        "submission_id": unique_id,
        "project_name": project_name,
        "description": "A complete submission test.",
        "category": "AI/Agents",
        "discord_handle": "testuser#1234",
        "github_url": "https://github.com/test/project",
        "demo_video_url": "https://youtube.com/test"
    }
    create_response = client.post('/api/submissions', json=submission_payload, headers=headers)
    assert create_response.status_code == 201, f"Submission creation failed: {create_response.text}"
    submission_id = create_response.json()["submission_id"]
    # Step 1: Create a test image and upload it
    img = Image.new('RGB', (400, 300), color='lightblue')
    try:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), "Test Project Logo", fill='navy')
        draw.text((20, 50), "Hackathon 2025", fill='darkblue')
    except:
        pass
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    files = {'file': ('test_logo.png', img_bytes, 'image/png')}
    data = {'submission_id': submission_id}
    upload_response = client.post('/api/upload-image', files=files, data=data, headers=headers)
    assert upload_response.status_code == 200, f"Image upload failed: {upload_response.text}"
    image_url = upload_response.json()['url']

    # Step 2: Edit the complete submission (PUT)
    submission_data = {
        "project_name": project_name,
        "category": "AI/Agents",
        "description": "Test complete submission",
        "discord_handle": "complete#1234",
        "twitter_handle": "@neuralnetworks",
        "github_url": "https://github.com/test/complete",
        "demo_video_url": "https://youtube.com/complete",
        "live_demo_url": "https://ai-image-gen-pro.com",
        "project_image": image_url,
        "problem_solved": "Current AI image generators are expensive, slow, or produce low-quality results. Our solution provides fast, high-quality image generation at affordable prices with an intuitive interface.",
        "favorite_part": "The real-time generation preview that shows the image being created step-by-step, giving users insight into the AI's creative process.",
        "solana_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
    }
    import time
    time.sleep(1)
    submit_response = client.put(f'/api/submissions/{submission_id}', json=submission_data, headers=headers)
    assert submit_response.status_code == 200, f"Submission update failed: {submit_response.status_code} {submit_response.text}"

    # Step 3: Verify the submission was stored correctly
    get_response = client.get(f'/api/submissions/{submission_id}')
    assert get_response.status_code == 200, f"Failed to retrieve submission: {get_response.status_code}"
    stored_submission = get_response.json()
    checks = [
        ("project_name", project_name),
        ("category", "AI/Agents"),
        ("project_image", image_url)
    ]
    for field, expected in checks:
        actual = stored_submission.get(field)
        assert actual == expected, f"Field {field} mismatch: expected '{expected}', got '{actual}'"

    # Step 4: Check if image is accessible
    image_response = client.get(image_url)
    assert image_response.status_code == 200, f"Image not accessible: {image_response.status_code}"

    # Step 5: List submissions and verify it appears
    list_response = client.get('/api/submissions')
    assert list_response.status_code == 200, f"Failed to list submissions: {list_response.status_code}"
    submissions = list_response.json()
    found = False
    for sub in submissions:
        if sub['submission_id'] == submission_id:
            found = True
            assert sub.get('project_image') == image_url, f"Image URL mismatch in listing: {sub.get('project_image')}"
            break
    assert found, f"Submission {submission_id} not found in listings" 