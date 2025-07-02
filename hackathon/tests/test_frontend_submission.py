#!/usr/bin/env python3
"""
Test the frontend submission flow exactly as the GUI would do it.
This simulates the browser making requests through the Vite proxy.
"""

import requests
import uuid

def create_test_image():
    """Create a small test PNG file"""
    import io
    from PIL import Image
    
    # Create a simple 10x10 red square
    img = Image.new('RGB', (10, 10), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes

def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"

def test_frontend_submission_flow():
    """Test the complete frontend submission flow"""
    frontend_url = "http://localhost:5173"
    print("🧪 Testing Frontend Submission Flow...")
    print(f"Frontend URL: {frontend_url}")
    print()
    
    # Step 1: Test schema endpoint through frontend proxy
    print("1. Testing schema endpoint through frontend proxy...")
    try:
        response = requests.get(f"{frontend_url}/api/submission-schema")
        print(f"   Schema response: {response.status_code}")
        assert response.status_code == 200, f"Schema test failed with status {response.status_code}"
        schema = response.json()
        file_fields = [field for field in schema if field.get('type') == 'file' and field.get('name') == 'project_image']
        print(f"   File fields found: {len(file_fields)}")
        assert len(file_fields) > 0, "No 'project_image' file field found in schema"
        
        for field in file_fields:
            print(f"     - {field['name']}: {field['label']}")
            print(f"       Accept: {field.get('accept', 'not specified')}")
            print(f"       Max size: {field.get('maxSize', 'not specified')} bytes")
    except Exception as e:
        assert False, f"Schema test failed: {e}"
    
    # Step 2: Test image upload through frontend proxy
    print()
    print("2. Testing image upload through frontend proxy...")
    try:
        img_data = create_test_image()
        
        files = {
            'file': ('test-frontend.png', img_data, 'image/png')
        }
        
        response = requests.post(f"{frontend_url}/api/upload-image", files=files)
        print(f"   Upload response: {response.status_code}")
        assert response.status_code == 200, f"Upload failed: {response.text}"
        upload_result = response.json()
        print(f"   Upload successful: {upload_result['url']}")
        image_url = upload_result['url']
    except Exception as e:
        assert False, f"Upload test failed: {e}"
    
    # Step 3: Test complete submission through frontend proxy
    print()
    print("3. Testing complete submission through frontend proxy...")
    try:
        submission_data = {
            "project_name": unique_name("FRONTEND_GUI_TEST"),
            "team_name": "Frontend Test Team",
            "category": "DeFi",
            "description": "Testing frontend GUI submission flow",
            "discord_handle": "testuser",
            "github_url": "https://github.com/test/repo",
            "demo_video_url": "https://youtube.com/test",
            "project_image": image_url  # Using the uploaded image URL
        }
        
        response = requests.post(
            f"{frontend_url}/api/submissions", 
            json=submission_data,
            headers={'Content-Type': 'application/json'}
        )
        print(f"   Submission response: {response.status_code}")
        assert response.status_code == 201, f"Submission failed: {response.text}"
        result = response.json()
        print("   ✅ Submission successful!")
        print(f"   Submission ID: {result.get('submission_id')}")
        
        # Step 4: Verify the submission was saved with image
        print()
        print("4. Verifying submission was saved with image...")
        verify_response = requests.get(f"{frontend_url}/api/submissions/{result.get('submission_id')}")
        assert verify_response.status_code == 200, f"Verification failed: {verify_response.status_code}"
        saved_submission = verify_response.json()
        print("   ✅ Verification successful!")
        print(f"   Project name: {saved_submission.get('project_name')}")
        print(f"   Project image: {saved_submission.get('project_image')}")
        
        # Test image accessibility
        if saved_submission.get('project_image'):
            img_response = requests.get(f"{frontend_url}{saved_submission['project_image']}")
            print(f"   Image accessibility: {img_response.status_code}")
            assert img_response.status_code == 200, "Image not accessible"
            print("   ✅ Image is accessible!")
        
        return True
    except Exception as e:
        assert False, f"Submission test failed: {e}"

def main():
    try:
        print("🚀 Starting Frontend GUI Submission Flow Test")
        print("=" * 60)
        success = test_frontend_submission_flow()
        print()
        if success:
            print("🎉 All frontend tests passed!")
            print("The GUI submission flow is working correctly.")
        else:
            print("❌ Some frontend tests failed!")
            print("There may be issues with the GUI submission flow.")
    except KeyboardInterrupt:
        print("\n❌ Test interrupted")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main() 