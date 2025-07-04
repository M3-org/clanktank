# Central manifest for all hackathon submission fields and schemas (versioned)
# Updated to use shared JSON schema from submission_schema.json

import json
import os
from typing import Dict, List, Any, Optional

# Get the path to the shared schema file
SCHEMA_FILE_PATH = os.path.join(
    os.path.dirname(__file__), 
    'submission_schema.json'
)

# Cache for loaded schema
_cached_schema: Optional[Dict[str, Any]] = None

def load_shared_schema() -> Dict[str, Any]:
    """Load the shared schema from JSON file with caching."""
    global _cached_schema
    
    if _cached_schema is not None:
        return _cached_schema
    
    try:
        with open(SCHEMA_FILE_PATH, 'r') as f:
            _cached_schema = json.load(f)
        return _cached_schema
    except FileNotFoundError:
        raise FileNotFoundError(f"Shared schema file not found at: {SCHEMA_FILE_PATH}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema file: {e}")

# Load schema data
try:
    schema_data = load_shared_schema()
    SUBMISSION_VERSIONS = schema_data["versions"]
    LATEST_SUBMISSION_VERSION = schema_data["latest"]
    
    # Extract field lists from the detailed schemas
    SUBMISSION_FIELDS = {}
    for version in SUBMISSION_VERSIONS:
        SUBMISSION_FIELDS[version] = [
            field["name"] for field in schema_data["schemas"][version]
        ]
    
    # Use the detailed schemas directly
    SUBMISSION_SCHEMA = schema_data["schemas"]
    
except Exception as e:
    # Fallback to hardcoded values for backward compatibility during transition
    print(f"Warning: Could not load shared schema, using fallback: {e}")
    
    # Fallback definitions (original hardcoded values)
    SUBMISSION_VERSIONS = ["v1", "v2"]
    LATEST_SUBMISSION_VERSION = "v2"
    
    SUBMISSION_FIELDS = {
        "v1": [
            "project_name",
            "team_name",
            "description",
            "category",
            "discord_handle",
            "twitter_handle",
            "github_url",
            "demo_video_url",
            "live_demo_url",
            "logo_url",
            "tech_stack",
            "how_it_works",
            "problem_solved",
            "coolest_tech",
            "next_steps",
        ],
        "v2": [
            "project_name",
            "team_name",
            "description",
            "category",
            "discord_handle",
            "twitter_handle",
            "github_url",
            "demo_video_url",
            "live_demo_url",
            "project_image",
            "tech_stack",
            "how_it_works",
            "problem_solved",
            "favorite_part",
            "solana_address",
        ],
    }
    
    SUBMISSION_SCHEMA = {
        "v1": [],  # Empty for now, can be populated if needed
        "v2": []   # Empty for now, can be populated if needed
    }

# Helper functions

def get_latest_version():
    """Get the latest submission version."""
    return LATEST_SUBMISSION_VERSION

def get_fields(version):
    """Get field list for a specific version."""
    if version == "latest":
        version = get_latest_version()
    return SUBMISSION_FIELDS[version]

def get_schema(version):
    """Get detailed schema for a specific version."""
    if version == "latest":
        version = get_latest_version()
    return SUBMISSION_SCHEMA[version]

def reload_schema():
    """Reload the schema from file (useful for development/testing)."""
    global _cached_schema
    _cached_schema = None
    return load_shared_schema()

def get_field_names_by_version() -> Dict[str, List[str]]:
    """Get all field names organized by version."""
    return SUBMISSION_FIELDS.copy()

def get_supported_versions() -> List[str]:
    """Get list of supported schema versions."""
    return SUBMISSION_VERSIONS.copy() 

def get_database_fields(version="v2"):
    """
    Get database column names for the specified schema version.
    This excludes UI-only fields that don't exist as database columns.
    """
    all_fields = get_schema(version)
    
    # UI-only fields that should not be included in database operations
    ui_only_fields = {'invite_code'}  # Add more UI-only fields here as needed
    
    # Return only fields that exist as database columns
    return [field for field in all_fields if field.get('name') not in ui_only_fields]

def get_database_field_names(version="v2"):
    """
    Get just the field names for database operations.
    """
    return [field['name'] for field in get_database_fields(version)] 