#!/usr/bin/env python3
"""
Test complete submission flow with image upload
"""

import requests
import io
from PIL import Image
import uuid
import subprocess

def test_complete_submission():
    """Test the complete submission flow including image upload"""
    
    subprocess.run(["python3", "-m", "hackathon.scripts.create_db"], check=True)
    unique_id = uuid.uuid4().hex[:8]
    project_name = f"Test Project Complete {unique_id}"
    
    print("🧪 Testing complete submission flow...")
    
    # Step 1: Create a test image and upload it
    print("1. Creating and uploading test image...")
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
    
    # Upload image
    files = {'file': ('test_logo.png', img_bytes, 'image/png')}
    upload_response = requests.post('http://localhost:8000/api/upload-image', files=files)
    
    assert upload_response.status_code == 200, f"Image upload failed: {upload_response.text}"
    
    image_url = upload_response.json()['url']
    print(f"✅ Image uploaded: {image_url}")
    
    # Step 2: Create a complete submission
    print("2. Creating submission with uploaded image...")
    
    submission_data = {
        "project_name": project_name,
        "team_name": "Team Complete",
        "category": "AI/Agents",
        "description": "Test complete submission",
        "discord_handle": "complete#1234",
        "twitter_handle": "@neuralnetworks",
        "github_url": "https://github.com/test/complete",
        "demo_video_url": "https://youtube.com/complete",
        "live_demo_url": "https://ai-image-gen-pro.com",
        "project_image": image_url,  # Use the uploaded image URL
        "tech_stack": "Python, PyTorch, Diffusers, FastAPI, React, TailwindCSS",
        "how_it_works": "Our system uses a fine-tuned stable diffusion model combined with custom LoRA adapters to generate high-quality images from text descriptions. The backend is built with FastAPI and the frontend uses React with real-time WebSocket updates.",
        "problem_solved": "Current AI image generators are expensive, slow, or produce low-quality results. Our solution provides fast, high-quality image generation at affordable prices with an intuitive interface.",
        "favorite_part": "The real-time generation preview that shows the image being created step-by-step, giving users insight into the AI's creative process.",
        "solana_address": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
    }
    
    submit_response = requests.post(
        'http://localhost:8000/api/submissions',
        json=submission_data,
        headers={'Content-Type': 'application/json'}
    )
    
    assert submit_response.status_code == 201, f"Submission failed: {submit_response.status_code} {submit_response.text}"
    
    submission_result = submit_response.json()
    submission_id = submission_result.get('submission_id')
    print(f"✅ Submission created: {submission_id}")
    
    # Step 3: Verify the submission was stored correctly
    print("3. Verifying submission storage...")
    
    get_response = requests.get(f'http://localhost:8000/api/submissions/{submission_id}')
    assert get_response.status_code == 200, f"Failed to retrieve submission: {get_response.status_code}"
    
    stored_submission = get_response.json()
    
    # Check key fields
    checks = [
        ("project_name", project_name),
        ("team_name", "Team Complete"),
        ("category", "AI/Agents"),
        ("project_image", image_url)
    ]
    
    for field, expected in checks:
        actual = stored_submission.get(field)
        assert actual == expected, f"Field {field} mismatch: expected '{expected}', got '{actual}'"
        print(f"✅ {field}: {actual}")
    
    # Step 4: Check if image is accessible
    print("4. Verifying image accessibility...")
    
    image_response = requests.get(f'http://localhost:8000{image_url}')
    assert image_response.status_code == 200, f"Image not accessible: {image_response.status_code}"
    
    print(f"✅ Image accessible: {len(image_response.content)} bytes")
    
    # Step 5: List submissions and verify it appears
    print("5. Verifying submission appears in listings...")
    
    list_response = requests.get('http://localhost:8000/api/submissions')
    assert list_response.status_code == 200, f"Failed to list submissions: {list_response.status_code}"
    
    submissions = list_response.json()
    found = False
    for sub in submissions:
        if sub['submission_id'] == submission_id:
            found = True
            print(f"✅ Found in listings: {sub['project_name']} by {sub['team_name']}")
            assert sub.get('project_image') == image_url, f"Image URL mismatch in listing: {sub.get('project_image')}"
            print("✅ Image URL correctly stored in listing")
            break
    
    assert found, f"Submission {submission_id} not found in listings"
    
    print("\n🎉 Complete submission flow successful!")
    print(f"📝 Submission ID: {submission_id}")
    print(f"🖼️ Image URL: {image_url}")
    print("🌐 View at: http://localhost:8000/docs#/latest/get_submission_latest")
    
    return True

if __name__ == "__main__":
    success = test_complete_submission()
    if not success:
        print("\n❌ Test failed!")
        exit(1)
    else:
        print("\n✅ All tests passed!") 