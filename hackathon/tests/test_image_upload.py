#!/usr/bin/env python3
"""
Test script for image upload functionality
"""

import requests
import io
from PIL import Image
import tempfile

def test_image_upload():
    """Test the image upload endpoint"""
    
    # Create a test image
    img = Image.new('RGB', (400, 300), color='lightblue')
    
    # Add some text to make it recognizable
    try:
        from PIL import ImageDraw, ImageFont
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), "Test Project Image", fill='navy')
    except:
        pass  # Font might not be available
    
    # Save to bytes
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Test upload
    files = {'file': ('test_image.png', img_bytes, 'image/png')}
    
    try:
        response = requests.post('http://localhost:8000/api/upload-image', files=files)
        print(f"Upload response: {response.status_code}")
        print(f"Response body: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Image upload test passed!")
            return response.json()['url']
        else:
            print("❌ Image upload test failed!")
            return None
            
    except Exception as e:
        print(f"❌ Upload test failed with error: {e}")
        return None

def test_schema_endpoint():
    """Test the schema endpoint returns file type"""
    try:
        response = requests.get('http://localhost:8000/api/submission-schema')
        print(f"Schema response: {response.status_code}")
        
        if response.status_code == 200:
            schema = response.json()
            file_fields = [field for field in schema if field.get('type') == 'file']
            print(f"File fields found: {len(file_fields)}")
            
            for field in file_fields:
                print(f"  - {field['name']}: {field['label']}")
                print(f"    Accept: {field.get('accept', 'not specified')}")
                print(f"    Max size: {field.get('maxSize', 'not specified')} bytes")
            
            return len(file_fields) > 0
        else:
            print("❌ Schema test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Schema test failed with error: {e}")
        return False

def test_submissions_with_images():
    """Test that submissions display correctly in dashboard"""
    try:
        response = requests.get('http://localhost:8000/api/submissions')
        print(f"Submissions response: {response.status_code}")
        
        if response.status_code == 200:
            submissions = response.json()
            print(f"Total submissions: {len(submissions)}")
            
            with_images = [s for s in submissions if s.get('project_image') and s['project_image'] != '[object File]']
            invalid_images = [s for s in submissions if s.get('project_image') == '[object File]']
            
            print(f"  - With valid images: {len(with_images)}")
            print(f"  - With invalid images: {len(invalid_images)}")
            
            if invalid_images:
                print("❌ Found submissions with invalid image data:")
                for sub in invalid_images:
                    print(f"    - {sub['submission_id']}: {sub['project_name']}")
            
            return len(invalid_images) == 0
        else:
            print("❌ Submissions test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Submissions test failed with error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing image upload functionality...")
    print("Make sure the server is running on http://localhost:8000")
    print()
    
    print("1. Testing schema endpoint...")
    schema_ok = test_schema_endpoint()
    print()
    
    print("2. Testing image upload...")
    upload_url = test_image_upload()
    print()
    
    print("3. Testing submissions with images...")
    submissions_ok = test_submissions_with_images()
    print()
    
    if schema_ok and upload_url and submissions_ok:
        print("🎉 All tests passed!")
        print(f"Uploaded image available at: {upload_url}")
    else:
        print("❌ Some tests failed. Check server logs.")
        if not submissions_ok:
            print("💡 Tip: Run 'python hackathon/fix_image_data.py' to clean up invalid image data") 