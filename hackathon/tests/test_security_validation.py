"""
Security validation tests for the 4 main security implementations:
1. Database Schema Consistency (null constraint enforcement)
2. Audit Logging (security event capture)
3. Database Constraints (NOT NULL enforcement)
4. File Validation (comprehensive upload security)
"""

import pytest
import sqlite3
import tempfile
import io
from pathlib import Path
import requests
from hackathon.backend.simple_audit import get_audit

# Use actual localhost server for testing
BASE_URL = "http://localhost:8000"


class TestDatabaseConstraints:
    """Test database-level constraint enforcement"""
    
    def test_null_constraint_enforcement(self):
        """Test that required fields cannot be null at database level"""
        # This tests our database constraint implementation
        with pytest.raises(sqlite3.IntegrityError) as exc_info:
            conn = sqlite3.connect("data/hackathon.db")
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO hackathon_submissions_v2 
                (submission_id, project_name, category, description, github_url, demo_video_url)
                VALUES ('test-null-constraint', 'Test Project', NULL, 'Test Description', 'https://github.com/test', 'https://youtube.com/test')
            """)
            conn.commit()
            conn.close()
        
        assert "NOT NULL constraint failed" in str(exc_info.value)
    
    def test_valid_submission_with_constraints(self):
        """Test that valid submissions work with constraints in place"""
        conn = sqlite3.connect("data/hackathon.db")
        cursor = conn.cursor()
        
        # This should succeed
        cursor.execute("""
            INSERT INTO hackathon_submissions_v2 
            (submission_id, project_name, discord_handle, category, description, github_url, demo_video_url)
            VALUES ('test-valid-constraint', 'Valid Project', 'testuser', 'AI/Agents', 'Valid Description', 'https://github.com/valid', 'https://youtube.com/valid')
        """)
        conn.commit()
        
        # Verify it was inserted
        cursor.execute("SELECT project_name FROM hackathon_submissions_v2 WHERE submission_id = 'test-valid-constraint'")
        result = cursor.fetchone()
        assert result[0] == 'Valid Project'
        
        # Clean up
        cursor.execute("DELETE FROM hackathon_submissions_v2 WHERE submission_id = 'test-valid-constraint'")
        conn.commit()
        conn.close()


class TestAuditLogging:
    """Test security event audit logging"""
    
    def test_audit_table_exists(self):
        """Test that audit table is properly created"""
        conn = sqlite3.connect("data/hackathon.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='simple_audit'")
        result = cursor.fetchone()
        assert result is not None
        conn.close()
    
    def test_security_event_logging(self):
        """Test that security events are properly logged"""
        from hackathon.backend.simple_audit import log_security_event
        
        # Log a test security event
        test_event = "test_security_validation"
        test_details = "Unit test security event"
        test_user = "test_user_123"
        
        log_security_event(test_event, test_details, test_user)
        
        # Verify it was logged
        conn = sqlite3.connect("data/hackathon.db")
        cursor = conn.cursor()
        cursor.execute("""
            SELECT action, user_id, details FROM simple_audit 
            WHERE action = ? AND user_id = ? 
            ORDER BY timestamp DESC LIMIT 1
        """, (f"security_{test_event}", test_user))
        
        result = cursor.fetchone()
        assert result is not None
        assert result[0] == f"security_{test_event}"
        assert result[1] == test_user
        assert result[2] == test_details
        
        # Clean up
        cursor.execute("DELETE FROM simple_audit WHERE action = ? AND user_id = ?", (f"security_{test_event}", test_user))
        conn.commit()
        conn.close()


class TestUnauthorizedAccess:
    """Test unauthorized access attempts are properly blocked and logged"""
    
    def test_unauthorized_submission_blocked(self):
        """Test that submissions without auth are blocked"""
        # Test without Discord token - should fail
        response = requests.post(f"{BASE_URL}/api/submissions", json={
            "project_name": "Unauthorized Test",
            "category": "AI/Agents",
            "description": "This should fail",
            "github_url": "https://github.com/test",
            "demo_video_url": "https://youtube.com/test"
        })
        
        assert response.status_code == 401
        assert "Discord authentication required" in response.json()["detail"]
    
    def test_unauthorized_edit_blocked(self):
        """Test that editing others' submissions is blocked"""
        # Test without Discord token - should fail
        response = requests.put(f"{BASE_URL}/api/submissions/non-existent-submission", json={
            "project_name": "Unauthorized Edit",
            "category": "AI/Agents", 
            "description": "This should fail",
            "github_url": "https://github.com/test",
            "demo_video_url": "https://youtube.com/test"
        })
        
        # Should fail because no authentication
        assert response.status_code == 401


class TestFileValidation:
    """Test comprehensive file upload validation"""
    
    def test_malicious_filename_blocked(self):
        """Test that malicious filenames are rejected"""
        # Create a test image file
        test_image = io.BytesIO()
        # Create minimal valid JPEG header
        test_image.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xFF\xDB\x00C\x00')
        test_image.write(b'\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xFF\xC0\x00\x11\x08\x00\x01\x00\x01\x01\x01\x11\x00\x02\x11\x01\x03\x11\x01\xFF\xC4\x00\x14\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x08\xFF\xC4\x00\x14\x10\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xDA\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00\x3f\x00\xAA\xFF\xD9')
        test_image.seek(0)
        
        # Try uploading with malicious filename
        response = requests.post(f"{BASE_URL}/api/upload-image", 
            files={"file": ("../../../etc/passwd.jpg", test_image, "image/jpeg")},
            data={"submission_id": "test-submission"}
        )
        
        assert response.status_code == 400
        assert "Filename contains invalid characters" in response.json()["detail"]
    
    def test_invalid_file_type_blocked(self):
        """Test that non-image files are rejected"""
        # Create a fake executable file
        fake_exe = io.BytesIO(b"MZ\x90\x00")  # PE header
        fake_exe.seek(0)
        
        response = requests.post(f"{BASE_URL}/api/upload-image",
            files={"file": ("malicious.exe", fake_exe, "application/x-executable")},
            data={"submission_id": "test-submission"}
        )
        
        assert response.status_code == 400
        assert "File must be an image" in response.json()["detail"]
    
    def test_oversized_file_blocked(self):
        """Test that oversized files are rejected"""
        # Create a file larger than 2MB limit
        large_file = io.BytesIO(b"x" * (3 * 1024 * 1024))  # 3MB
        large_file.seek(0)
        
        response = requests.post(f"{BASE_URL}/api/upload-image",
            files={"file": ("large.jpg", large_file, "image/jpeg")},
            data={"submission_id": "test-submission"}
        )
        
        assert response.status_code == 400
        assert "File size must be less than 2MB" in response.json()["detail"]
    
    def test_empty_file_blocked(self):
        """Test that empty files are rejected"""
        empty_file = io.BytesIO(b"")
        empty_file.seek(0)
        
        response = requests.post(f"{BASE_URL}/api/upload-image",
            files={"file": ("empty.jpg", empty_file, "image/jpeg")},
            data={"submission_id": "test-submission"}
        )
        
        assert response.status_code == 400
        assert "File is too small to be a valid image" in response.json()["detail"]


class TestGitHubUrlValidation:
    """Test GitHub URL validation for SSRF protection"""
    
    def test_invalid_github_url_blocked(self):
        """Test that non-GitHub URLs are rejected"""
        response = requests.post(f"{BASE_URL}/api/submissions", json={
            "project_name": "SSRF Test",
            "category": "AI/Agents",
            "description": "Testing SSRF protection",
            "github_url": "https://internal.company.com/malicious",
            "demo_video_url": "https://youtube.com/test"
        })
        
        assert response.status_code == 422  # Pydantic validation error
        assert "must be a valid GitHub repository URL" in response.json()["detail"]
    
    def test_valid_github_url_accepted(self):
        """Test that valid GitHub URLs are accepted"""
        response = requests.post(f"{BASE_URL}/api/submissions", json={
            "project_name": "Valid GitHub Test",
            "category": "AI/Agents", 
            "description": "Testing valid GitHub URL",
            "github_url": "https://github.com/user/repo",
            "demo_video_url": "https://youtube.com/test"
        })
        
        # Should succeed (not fail on URL validation) - might fail on auth but not URL
        assert response.status_code in [201, 401, 403]  # 401/403 might be auth issues, but not URL validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])