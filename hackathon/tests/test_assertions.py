"""
Common test assertions for Hackathon test suite
Reusable assertion patterns to avoid duplication
"""

from typing import Dict, Any, List, Optional, Union
from .test_constants import (
    HTTP_OK, HTTP_CREATED, HTTP_BAD_REQUEST, HTTP_NOT_FOUND,
    HTTP_UNPROCESSABLE_ENTITY, VALID_CATEGORIES
)


def assert_successful_response(response, expected_status: int = HTTP_OK) -> None:
    """Assert that a response is successful"""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"


def assert_error_response(response, expected_status: int = HTTP_BAD_REQUEST) -> None:
    """Assert that a response is an error"""
    assert response.status_code == expected_status, f"Expected {expected_status}, got {response.status_code}. Response: {response.text}"


def assert_json_response(response, expected_status: int = HTTP_OK) -> Dict[str, Any]:
    """Assert response is JSON and return the data"""
    assert_successful_response(response, expected_status)
    assert response.headers.get("content-type", "").startswith("application/json")
    return response.json()


def assert_valid_submission_structure(data: Dict[str, Any], version: str = "v2") -> None:
    """Assert that submission data has valid structure"""
    # Common fields for both versions
    required_fields = [
        "submission_id", "project_name", "team_name", "category",
        "description", "discord_handle", "status", "created_at"
    ]
    
    if version == "v2":
        required_fields.extend([
            "how_it_works", "problem_solved", "coolest_tech", "next_steps"
        ])
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
        assert data[field] is not None, f"Field {field} is None"
    
    # Validate specific field types
    assert isinstance(data["submission_id"], str), "submission_id must be string"
    assert isinstance(data["project_name"], str), "project_name must be string"
    assert isinstance(data["team_name"], str), "team_name must be string"
    assert isinstance(data["category"], str), "category must be string"
    assert isinstance(data["description"], str), "description must be string"
    assert isinstance(data["discord_handle"], str), "discord_handle must be string"
    assert isinstance(data["status"], str), "status must be string"
    
    # Validate category
    assert data["category"] in VALID_CATEGORIES, f"Invalid category: {data['category']}"
    
    # Validate URLs if present
    if "github_url" in data and data["github_url"]:
        assert data["github_url"].startswith("http"), "github_url must be valid URL"
    
    if "demo_video_url" in data and data["demo_video_url"]:
        assert data["demo_video_url"].startswith("http"), "demo_video_url must be valid URL"
    
    if version == "v2" and "live_demo_url" in data and data["live_demo_url"]:
        assert data["live_demo_url"].startswith("http"), "live_demo_url must be valid URL"


def assert_valid_leaderboard_structure(data: Dict[str, Any]) -> None:
    """Assert that leaderboard data has valid structure"""
    assert "submissions" in data, "Missing submissions field"
    assert isinstance(data["submissions"], list), "submissions must be a list"
    
    if data["submissions"]:
        submission = data["submissions"][0]
        required_fields = [
            "submission_id", "project_name", "team_name", "category",
            "total_score", "rank"
        ]
        
        for field in required_fields:
            assert field in submission, f"Missing leaderboard field: {field}"
        
        # Validate score and rank types
        assert isinstance(submission["total_score"], (int, float)), "total_score must be numeric"
        assert isinstance(submission["rank"], int), "rank must be integer"
        assert submission["rank"] >= 1, "rank must be positive"


def assert_valid_stats_structure(data: Dict[str, Any]) -> None:
    """Assert that stats data has valid structure"""
    expected_fields = [
        "total_submissions", "submissions_by_status", "submissions_by_category"
    ]
    
    for field in expected_fields:
        assert field in data, f"Missing stats field: {field}"
    
    assert isinstance(data["total_submissions"], int), "total_submissions must be integer"
    assert isinstance(data["submissions_by_status"], dict), "submissions_by_status must be dict"
    assert isinstance(data["submissions_by_category"], dict), "submissions_by_category must be dict"


def assert_valid_scores_structure(data: Dict[str, Any]) -> None:
    """Assert that scores data has valid structure"""
    expected_fields = [
        "aimarc_score", "aishaw_score", "peepo_score", "spartan_score",
        "community_score", "total_score"
    ]
    
    for field in expected_fields:
        if field in data:
            assert isinstance(data[field], (int, float, type(None))), f"{field} must be numeric or None"
            if data[field] is not None:
                assert 0 <= data[field] <= 10, f"{field} must be between 0 and 10"


def assert_valid_research_structure(data: Dict[str, Any]) -> None:
    """Assert that research data has valid structure"""
    expected_fields = ["github_analysis", "market_research", "technical_analysis"]
    
    for field in expected_fields:
        if field in data:
            assert data[field] is not None, f"{field} cannot be None"


def assert_valid_feedback_structure(data: Dict[str, Any]) -> None:
    """Assert that feedback data has valid structure"""
    required_fields = [
        "discord_user_id", "discord_user_nickname", "reaction_type", "score_adjustment"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing feedback field: {field}"
    
    assert isinstance(data["score_adjustment"], (int, float)), "score_adjustment must be numeric"


def assert_valid_image_upload_response(data: Dict[str, Any]) -> None:
    """Assert that image upload response has valid structure"""
    assert "image_url" in data, "Missing image_url field"
    assert isinstance(data["image_url"], str), "image_url must be string"
    assert data["image_url"].startswith("http"), "image_url must be valid URL"


def assert_valid_schema_response(data: Dict[str, Any], version: str = "v2") -> None:
    """Assert that schema response has valid structure"""
    assert "properties" in data, "Missing properties field"
    assert "required" in data, "Missing required field"
    assert isinstance(data["properties"], dict), "properties must be dict"
    assert isinstance(data["required"], list), "required must be list"
    
    # Check for common required fields
    common_required = ["project_name", "team_name", "category", "description"]
    for field in common_required:
        assert field in data["required"], f"Missing required field in schema: {field}"
    
    if version == "v2":
        v2_required = ["how_it_works", "problem_solved", "coolest_tech", "next_steps"]
        for field in v2_required:
            assert field in data["required"], f"Missing v2 required field in schema: {field}"


def assert_pagination_structure(data: Dict[str, Any]) -> None:
    """Assert that paginated response has valid structure"""
    assert "items" in data, "Missing items field"
    assert "total" in data, "Missing total field"
    assert "page" in data, "Missing page field"
    assert "per_page" in data, "Missing per_page field"
    assert "pages" in data, "Missing pages field"
    
    assert isinstance(data["items"], list), "items must be list"
    assert isinstance(data["total"], int), "total must be integer"
    assert isinstance(data["page"], int), "page must be integer"
    assert isinstance(data["per_page"], int), "per_page must be integer"
    assert isinstance(data["pages"], int), "pages must be integer"


def assert_database_state(
    submission_id: int,
    expected_status: Optional[str] = None,
    should_exist: bool = True
) -> None:
    """Assert database state for a submission"""
    from .test_db_helpers import get_submission_status, get_submission_with_scores
    
    if should_exist:
        status = get_submission_status(submission_id)
        assert status is not None, f"Submission {submission_id} not found in database"
        
        if expected_status:
            assert status == expected_status, f"Expected status {expected_status}, got {status}"
    else:
        status = get_submission_status(submission_id)
        assert status is None, f"Submission {submission_id} should not exist in database"


def assert_submission_progression(
    submission_id: int,
    expected_stages: List[str]
) -> None:
    """Assert that submission has progressed through expected stages"""
    from .test_db_helpers import get_submission_with_scores
    
    submission = get_submission_with_scores(submission_id)
    assert submission is not None, f"Submission {submission_id} not found"
    
    current_status = submission["status"]
    assert current_status in expected_stages, f"Unexpected status: {current_status}"
    
    # Check that appropriate data exists for each stage
    if current_status in ["researched", "scored", "completed"]:
        # Should have research data
        pass  # Add research data checks here
    
    if current_status in ["scored", "completed"]:
        # Should have scores
        assert submission["total_score"] is not None, "Missing total_score for scored submission"


def assert_no_duplicate_submissions(project_name: str, team_name: str) -> None:
    """Assert that no duplicate submissions exist"""
    from .test_db_helpers import get_all_submissions
    
    submissions = get_all_submissions()
    matches = [
        s for s in submissions 
        if s["project_name"] == project_name and s["team_name"] == team_name
    ]
    
    assert len(matches) <= 1, f"Found {len(matches)} duplicate submissions for {project_name}/{team_name}"


def assert_valid_rate_limit_response(response) -> None:
    """Assert that rate limit response is valid"""
    assert response.status_code == 429, f"Expected 429, got {response.status_code}"
    data = response.json()
    assert "error" in data, "Missing error field in rate limit response"
    assert "rate limit" in data["error"].lower(), "Error message should mention rate limit"


def assert_file_upload_constraints(file_size_mb: float, max_size_mb: float = 5.0) -> None:
    """Assert file upload size constraints"""
    assert file_size_mb <= max_size_mb, f"File size {file_size_mb}MB exceeds limit {max_size_mb}MB"