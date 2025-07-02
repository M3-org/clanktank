# Admin Tools

This directory contains administrative and recovery tools that are not part of the main production pipeline but may be useful for maintenance and troubleshooting.

## Tools

### recovery_tool.py
A comprehensive recovery tool for restoring submissions from backup files.

**Usage:**
```bash
# List all backups
python hackathon/admin_tools/recovery_tool.py --list

# Restore by submission ID  
python hackathon/admin_tools/recovery_tool.py --restore SUBMISSION_ID

# Restore from specific backup file
python hackathon/admin_tools/recovery_tool.py --restore-file backup.json

# Validate backup file
python hackathon/admin_tools/recovery_tool.py --validate backup.json
```

**When to use:**
- Database corruption requiring bulk recovery
- User reports lost submission (rare with auto-backup system)
- Audit and validation of backup files
- Emergency restoration scenarios

## Note

These tools are for administrative use and are not part of the regular submission pipeline. The robust auto-backup system handles most recovery scenarios automatically. 