#!/usr/bin/env python3
"""
Test script for image upload functionality
"""

import pytest
from fastapi.testclient import TestClient
import io
from PIL import Image
import os
import uuid
import shutil

DB_PATH = "data/hackathon.db"

def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from hackathon.backend.app import app
    return TestClient(app)

def test_image_upload(client):
    """Test the image upload endpoint"""
    img = Image.new('RGB', (400, 300), color='lightblue')
    try:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), "Test Project Image", fill='navy')
    except:
        pass
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    files = {'file': ('test_image.png', img_bytes, 'image/png')}
    response = client.post('/api/upload-image', files=files)
    assert response.status_code == 200, f"Image upload failed: {response.text}"
    assert 'url' in response.json(), "No URL in upload response"
    image_url = response.json()['url']
    assert image_url is not None


def test_schema_endpoint(client):
    """Test the schema endpoint returns file type"""
    response = client.get('/api/submission-schema')
    assert response.status_code == 200, f"Schema test failed: {response.status_code}"
    schema = response.json()
    file_fields = [field for field in schema.get('fields', []) if field.get('type') == 'file' and field.get('name') == 'project_image']
    assert len(file_fields) > 0, "No 'project_image' file field found in schema"
    for field in file_fields:
        assert field['name'] == 'project_image'


def test_submissions_with_images(client):
    """Test that submissions display correctly in dashboard"""
    response = client.get('/api/submissions')
    assert response.status_code == 200, f"Submissions fetch failed: {response.status_code}"
    submissions = response.json()
    with_images = [s for s in submissions if s.get('project_image') and s['project_image'] != '[object File]']
    invalid_images = [s for s in submissions if s.get('project_image') == '[object File]']
    assert len(invalid_images) == 0, f"Found submissions with invalid image data: {invalid_images}"
    has_image = any(sub.get('project_image') for sub in submissions)
    assert has_image, "No submissions with images found" 