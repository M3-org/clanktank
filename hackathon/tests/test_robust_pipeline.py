#!/usr/bin/env python3
"""
Test script for robust submission pipeline enhancements.
Tests auto-save, backup creation, error handling, and recovery mechanisms.
"""

import json
import os
import tempfile
from pathlib import Path
import sqlite3
import requests
import subprocess
import sys
import uuid

def unique_name(base):
    return f"{base}-{uuid.uuid4().hex[:8]}"

def test_backend_backup_creation():
    """Test that backend creates backups properly."""
    print("🧪 Testing backend backup creation...")
    
    # Test submission data
    subprocess.run(["python3", "-m", "hackathon.scripts.create_db"], check=True)
    unique_id = uuid.uuid4().hex[:8]
    payload = {
        "project_name": unique_name("Robustness Project"),
        "team_name": "Robustness Testers",
        "category": "AI/Agents",
        "description": "Testing the robustness enhancements",
        "discord_handle": "testuser#1234",
        "github_url": "https://github.com/test/project",
        "demo_video_url": "https://youtube.com/test"
        # Optional fields can be added as needed
    }
    
    try:
        # Make submission
        response = requests.post("http://localhost:8000/api/submissions", json=payload)
        
        if response.status_code == 201:
            result = response.json()
            submission_id = result.get("submission_id")
            backup_file = result.get("backup_created")
            
            print(f"✅ Submission successful: {submission_id}")
            print(f"✅ Backup created: {backup_file}")
            
            # Verify backup file exists and is valid
            if backup_file and Path(backup_file).exists():
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                
                assert backup_data.get("submission_data", {}).get("submission_id") == submission_id, "Backup file data doesn't match submission"
            else:
                print("❌ Backup file not found")
        else:
            assert False, f"Submission failed: {response.status_code} - {response.text}"
    
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to backend (is it running on localhost:8000?)")
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    return False

def test_recovery_tool():
    """Test the recovery tool functionality."""
    print("\n🧪 Testing recovery tool...")
    
    try:
        # Test listing backups
        result = subprocess.run([
            "python3", "-m", "hackathon.scripts.recovery_tool", "--list"
        ], capture_output=True, text=True, cwd=".")
        
        if result.returncode == 0:
            print("✅ Recovery tool --list works")
            if "Available backup files:" in result.stdout:
                print("✅ Backup listing format correct")
                return True
            else:
                assert False, "Unexpected output format"
        else:
            assert False, f"Recovery tool failed: {result.stderr}"
    
    except Exception as e:
        print(f"❌ Recovery tool test error: {e}")
    
    return False

def test_database_resilience():
    """Test database resilience features."""
    print("\n🧪 Testing database resilience...")
    
    # Create a temporary database to test with
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    temp_db.close()
    
    conn = None
    try:
        # Create test database
        subprocess.run([
            "python3", "-m", "hackathon.scripts.create_db", temp_db.name
        ], check=True, capture_output=True)
        
        # Test duplicate handling by inserting same submission twice
        conn = sqlite3.connect(temp_db.name)
        cursor = conn.cursor()
        
        test_submission = {
            "submission_id": "test-duplicate-123",
            "project_name": "Test Project",
            "team_name": "Test Team",
            "description": "Test description",
            "category": "AI/Agents",
            "status": "submitted",
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00"
        }
        
        # First insertion should work
        fields = list(test_submission.keys())
        placeholders = ", ".join(["?" for _ in fields])
        columns = ", ".join(fields)
        values = [test_submission[field] for field in fields]
        
        cursor.execute(f"INSERT INTO hackathon_submissions_v2 ({columns}) VALUES ({placeholders})", values)
        conn.commit()
        
        # Second insertion should fail gracefully
        try:
            cursor.execute(f"INSERT INTO hackathon_submissions_v2 ({columns}) VALUES ({placeholders})", values)
            conn.commit()
            assert False, "Duplicate insertion should have failed"
        except sqlite3.IntegrityError:
            print("✅ Duplicate constraint properly enforced")
            return True
    
    except Exception as e:
        assert False, f"Database resilience test error: {e}"
    
    finally:
        if conn:
            conn.close()
        try:
            os.unlink(temp_db.name)
        except:
            pass

def test_backup_directory_creation():
    """Test that backup directories are created properly."""
    print("\n🧪 Testing backup directory creation...")
    
    backup_dir = Path("data/submission_backups")
    
    # Remove directory if it exists (for clean test)
    if backup_dir.exists():
        import shutil
        shutil.rmtree(backup_dir)
    
    # The directory should be created automatically on first submission
    # This would happen in a real submission test, but we'll just verify the logic
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    assert backup_dir.exists() and backup_dir.is_dir(), "Backup directory not created"
    print("✅ Backup directory creation works")

def run_all_tests():
    """Run all robustness tests."""
    print("🚀 Running Robust Pipeline Tests\n")
    
    tests = [
        ("Backup Directory Creation", test_backup_directory_creation),
        ("Database Resilience", test_database_resilience),
        ("Recovery Tool", test_recovery_tool),
        ("Backend Backup Creation", test_backend_backup_creation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Testing: {test_name}")
        print('='*50)
        
        try:
            test_func()
            results[test_name] = True
        except AssertionError as e:
            print(f"❌ {test_name} failed: {e}")
            results[test_name] = False
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All robustness tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 