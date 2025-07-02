#!/usr/bin/env python3
"""
Hackathon Submission Recovery Tool

This tool helps recover submissions from backup files when the normal submission process fails.
It can be used by administrators to restore lost submissions or by users to resubmit from backups.

Usage:
    python recovery_tool.py --list                              # List all backups
    python recovery_tool.py --restore SUBMISSION_ID             # Restore a specific submission
    python recovery_tool.py --restore-file BACKUP_FILE.json     # Restore from specific backup file
    python recovery_tool.py --validate BACKUP_FILE.json         # Validate a backup file
"""

import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Import schema functions
from hackathon.backend.schema import get_fields

DEFAULT_DB_PATH = "data/hackathon.db"
DEFAULT_BACKUP_DIR = "data/submission_backups"
DEFAULT_TABLE = "hackathon_submissions_v2"


class SubmissionRecoveryTool:
    def __init__(self, db_path: str = DEFAULT_DB_PATH, backup_dir: str = DEFAULT_BACKUP_DIR):
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        
    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backup files."""
        if not self.backup_dir.exists():
            print(f"Backup directory not found: {self.backup_dir}")
            return []
        
        backups = []
        for backup_file in self.backup_dir.glob("*.json"):
            try:
                stat = backup_file.stat()
                with open(backup_file, 'r') as f:
                    data = json.load(f)
                
                # Extract info from backup
                submission_data = data.get("submission_data", {})
                backup_type = "error" if backup_file.name.startswith("ERROR-") else "normal"
                
                backup_info = {
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "submission_id": submission_data.get("submission_id", "unknown"),
                    "project_name": submission_data.get("project_name", "unknown"),
                    "team_name": submission_data.get("team_name", "unknown"),
                    "type": backup_type,
                    "size_bytes": stat.st_size,
                    "created_at": data.get("timestamp", "unknown"),
                    "file_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "has_error": "error" in data
                }
                
                if "error" in data:
                    backup_info["error_message"] = data["error"].get("message", "unknown")
                
                backups.append(backup_info)
                
            except Exception as e:
                print(f"Warning: Failed to process {backup_file}: {e}")
                continue
        
        # Sort by creation time (newest first)
        backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return backups
    
    def validate_backup(self, backup_file: Path) -> Dict[str, Any]:
        """Validate a backup file and return validation results."""
        result = {
            "valid": False,
            "file_exists": False,
            "parseable": False,
            "has_submission_data": False,
            "schema_valid": False,
            "errors": [],
            "warnings": []
        }
        
        # Check if file exists
        if not backup_file.exists():
            result["errors"].append(f"Backup file not found: {backup_file}")
            return result
        result["file_exists"] = True
        
        # Try to parse JSON
        try:
            with open(backup_file, 'r') as f:
                data = json.load(f)
            result["parseable"] = True
        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON: {e}")
            return result
        except Exception as e:
            result["errors"].append(f"Failed to read file: {e}")
            return result
        
        # Check if it has submission data
        submission_data = data.get("submission_data")
        if not submission_data:
            result["errors"].append("No submission_data found in backup")
            return result
        result["has_submission_data"] = True
        
        # Validate required fields
        required_fields = ["submission_id", "project_name", "team_name", "description"]
        missing_fields = [field for field in required_fields if not submission_data.get(field)]
        if missing_fields:
            result["errors"].append(f"Missing required fields: {missing_fields}")
        
        # Check against schema
        try:
            schema_fields = get_fields("v2")
            extra_fields = [field for field in submission_data.keys() 
                          if field not in schema_fields and field not in ["submission_id", "status", "created_at", "updated_at"]]
            if extra_fields:
                result["warnings"].append(f"Extra fields not in schema: {extra_fields}")
            
            result["schema_valid"] = True
        except Exception as e:
            result["warnings"].append(f"Could not validate against schema: {e}")
        
        result["valid"] = len(result["errors"]) == 0
        return result
    
    def restore_submission(self, backup_file: Path, force: bool = False) -> bool:
        """Restore a submission from backup file to the database."""
        print(f"Attempting to restore submission from: {backup_file}")
        
        # Validate backup first
        validation = self.validate_backup(backup_file)
        if not validation["valid"]:
            print("❌ Backup validation failed:")
            for error in validation["errors"]:
                print(f"   • {error}")
            if not force:
                print("Use --force to restore anyway (not recommended)")
                return False
            else:
                print("⚠️  Forcing restore despite validation errors...")
        
        if validation["warnings"]:
            print("⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"   • {warning}")
        
        # Load backup data
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
        except Exception as e:
            print(f"❌ Failed to load backup file: {e}")
            return False
        
        submission_data = backup_data["submission_data"]
        submission_id = submission_data["submission_id"]
        
        # Check if database exists
        if not self.db_path.exists():
            print(f"❌ Database not found: {self.db_path}")
            print("Please create the database first using create_hackathon_db.py")
            return False
        
        # Connect to database
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if submission already exists
            cursor.execute(f"SELECT submission_id FROM {DEFAULT_TABLE} WHERE submission_id = ?", (submission_id,))
            existing = cursor.fetchone()
            
            if existing and not force:
                print(f"❌ Submission {submission_id} already exists in database")
                print("Use --force to overwrite existing submission")
                return False
            elif existing and force:
                print(f"⚠️  Overwriting existing submission {submission_id}")
                cursor.execute(f"DELETE FROM {DEFAULT_TABLE} WHERE submission_id = ?", (submission_id,))
            
            # Prepare data for insertion
            fields = list(submission_data.keys())
            placeholders = ", ".join(["?" for _ in fields])
            columns = ", ".join(fields)
            values = [submission_data[field] for field in fields]
            
            # Insert submission
            cursor.execute(f"INSERT INTO {DEFAULT_TABLE} ({columns}) VALUES ({placeholders})", values)
            conn.commit()
            
            print(f"✅ Successfully restored submission: {submission_id}")
            print(f"   Project: {submission_data.get('project_name', 'Unknown')}")
            print(f"   Team: {submission_data.get('team_name', 'Unknown')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def find_backup_by_id(self, submission_id: str) -> Optional[Path]:
        """Find the most recent backup file for a submission ID."""
        backup_files = list(self.backup_dir.glob(f"{submission_id}-*.json"))
        backup_files.extend(list(self.backup_dir.glob(f"ERROR-{submission_id}-*.json")))
        
        if not backup_files:
            return None
        
        # Return the most recent backup
        return max(backup_files, key=lambda f: f.stat().st_mtime)


def main():
    parser = argparse.ArgumentParser(description="Hackathon Submission Recovery Tool")
    parser.add_argument("--list", action="store_true", help="List all backup files")
    parser.add_argument("--restore", metavar="SUBMISSION_ID", help="Restore submission by ID")
    parser.add_argument("--restore-file", metavar="BACKUP_FILE", help="Restore from specific backup file")
    parser.add_argument("--validate", metavar="BACKUP_FILE", help="Validate a backup file")
    parser.add_argument("--force", action="store_true", help="Force operation even if validation fails")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH, help="Path to database file")
    parser.add_argument("--backup-dir", default=DEFAULT_BACKUP_DIR, help="Path to backup directory")
    
    args = parser.parse_args()
    
    tool = SubmissionRecoveryTool(args.db_path, args.backup_dir)
    
    if args.list:
        print("📂 Available backup files:")
        backups = tool.list_backups()
        
        if not backups:
            print("   No backup files found")
            return
        
        for backup in backups:
            status = "❌ ERROR" if backup["type"] == "error" else "✅ OK"
            print(f"\n   {status} {backup['filename']}")
            print(f"      ID: {backup['submission_id']}")
            print(f"      Project: {backup['project_name']}")
            print(f"      Team: {backup['team_name']}")
            print(f"      Created: {backup['created_at']}")
            print(f"      Size: {backup['size_bytes']} bytes")
            if backup["has_error"]:
                print(f"      Error: {backup.get('error_message', 'Unknown error')}")
    
    elif args.validate:
        backup_file = Path(args.validate)
        print(f"🔍 Validating backup file: {backup_file}")
        
        validation = tool.validate_backup(backup_file)
        
        if validation["valid"]:
            print("✅ Backup file is valid")
        else:
            print("❌ Backup file has errors:")
            for error in validation["errors"]:
                print(f"   • {error}")
        
        if validation["warnings"]:
            print("⚠️  Warnings:")
            for warning in validation["warnings"]:
                print(f"   • {warning}")
    
    elif args.restore:
        submission_id = args.restore
        backup_file = tool.find_backup_by_id(submission_id)
        
        if not backup_file:
            print(f"❌ No backup found for submission ID: {submission_id}")
            return
        
        print(f"📁 Found backup: {backup_file}")
        success = tool.restore_submission(backup_file, args.force)
        
        if success:
            print("\n🎉 Restoration completed successfully!")
        else:
            print("\n💥 Restoration failed!")
    
    elif args.restore_file:
        backup_file = Path(args.restore_file)
        success = tool.restore_submission(backup_file, args.force)
        
        if success:
            print("\n🎉 Restoration completed successfully!")
        else:
            print("\n💥 Restoration failed!")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main() 