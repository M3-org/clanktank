#!/usr/bin/env python3
"""
Tests for the invite code system
"""

import pytest
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
import sys

# Add the project root to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from scripts.generate_invites import InviteCodeGenerator

class TestInviteCodeGenerator:
    """Test the invite code generation functionality"""
    
    def setup_method(self):
        """Set up a temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create the tables
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE invite_codes (
                code TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                campaign TEXT,
                max_uses INTEGER DEFAULT 1,
                current_uses INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE invite_code_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invite_code TEXT REFERENCES invite_codes(code),
                submission_id TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_info JSON
            )
        """)
        
        conn.commit()
        conn.close()
        
        self.generator = InviteCodeGenerator(self.db_path)
    
    def teardown_method(self):
        """Clean up the temporary database"""
        os.unlink(self.db_path)
    
    def test_generate_code(self):
        """Test basic code generation"""
        code = self.generator.generate_code()
        assert len(code) == 8
        assert code.isupper()
        assert all(c.isalnum() for c in code)
        # Check that ambiguous characters are not used
        assert '0' not in code
        assert 'O' not in code
        assert 'I' not in code
        assert '1' not in code
    
    def test_generate_unique_code(self):
        """Test that generated codes are unique"""
        codes = set()
        for _ in range(100):
            code = self.generator.generate_unique_code()
            assert code not in codes
            codes.add(code)
    
    def test_create_codes(self):
        """Test creating and storing codes in database"""
        codes = self.generator.create_codes(
            count=3,
            campaign="test",
            created_by="pytest",
            max_uses=5,
            notes="Test codes"
        )
        
        assert len(codes) == 3
        assert all(code['campaign'] == 'test' for code in codes)
        assert all(code['max_uses'] == 5 for code in codes)
        
        # Verify codes are in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM invite_codes")
        count = cursor.fetchone()[0]
        assert count == 3
        conn.close()
    
    def test_list_codes(self):
        """Test listing codes"""
        # Create some test codes
        self.generator.create_codes(count=2, campaign="test1")
        self.generator.create_codes(count=1, campaign="test2")
        
        # List all codes
        all_codes = self.generator.list_codes(active_only=False)
        assert len(all_codes) == 3
        
        # List by campaign
        test1_codes = self.generator.list_codes(campaign="test1")
        assert len(test1_codes) == 2
        assert all(code['campaign'] == 'test1' for code in test1_codes)
    
    def test_code_exists(self):
        """Test checking if codes exist"""
        codes = self.generator.create_codes(count=1)
        test_code = codes[0]['code']
        
        assert self.generator.code_exists(test_code)
        assert not self.generator.code_exists("NONEXISTENT")

class TestInviteCodeValidation:
    """Test invite code validation logic"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Create the tables and add test data
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE invite_codes (
                code TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                campaign TEXT,
                max_uses INTEGER DEFAULT 1,
                current_uses INTEGER DEFAULT 0,
                expires_at TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                notes TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE invite_code_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invite_code TEXT REFERENCES invite_codes(code),
                submission_id TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_info JSON
            )
        """)
        
        # Add test codes
        future_date = (datetime.now() + timedelta(days=1)).isoformat()
        past_date = (datetime.now() - timedelta(days=1)).isoformat()
        
        test_codes = [
            ('VALID001', 1, 0, None, True),  # Valid, unused
            ('EXPIRED01', 1, 0, past_date, True),  # Expired
            ('USED0001', 1, 1, None, False),  # Used up, deactivated
            ('INACTIVE1', 1, 0, None, False),  # Inactive
            ('MULTI001', 3, 1, None, True),  # Multi-use, partially used
        ]
        
        for code, max_uses, current_uses, expires_at, is_active in test_codes:
            cursor.execute("""
                INSERT INTO invite_codes (code, max_uses, current_uses, expires_at, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (code, max_uses, current_uses, expires_at, is_active))
        
        conn.commit()
        conn.close()
    
    def teardown_method(self):
        """Clean up"""
        os.unlink(self.db_path)
    
    def test_validate_nonexistent_code(self):
        """Test validation of non-existent code"""
        # We would need to import the validation function from the backend
        # For now, this is a placeholder for the test structure
        # In a real implementation, you'd test the validate_invite_code function
        pass
    
    def test_validate_expired_code(self):
        """Test validation of expired code"""
        # Similar placeholder - would test expired code validation
        pass
    
    def test_validate_used_code(self):
        """Test validation of fully used code"""
        # Placeholder for testing used up codes
        pass
    
    def test_validate_valid_code(self):
        """Test validation of valid code"""
        # Placeholder for testing valid codes
        pass

if __name__ == "__main__":
    # Run tests if script is executed directly
    pytest.main([__file__, "-v"])