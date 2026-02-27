"""
Test constants for Hackathon test suite
Centralized constants to avoid duplication across test files
"""

# Database Configuration
DB_PATH = "data/hackathon.db"
DEFAULT_VERSION = "v2"
DEFAULT_TABLE = f"hackathon_submissions_{DEFAULT_VERSION}"

# API Endpoints
API_SUBMISSIONS = "/api/submissions"
API_LEADERBOARD = "/api/leaderboard"
API_STATS = "/api/stats"
API_SCHEMA = "/api/submission-schema"
API_UPLOAD = "/api/upload-image"
API_FEEDBACK = "/api/feedback"

# Versioned API Endpoints
API_V1_SUBMISSIONS = "/api/v1/submissions"
API_V1_LEADERBOARD = "/api/v1/leaderboard"
API_V2_SUBMISSIONS = "/api/v2/submissions"
API_V2_LEADERBOARD = "/api/v2/leaderboard"

# Test Data Constants
TEST_GITHUB_URL = "https://github.com/test/project"
TEST_DEMO_URL = "https://youtube.com/test"
TEST_LIVE_DEMO_URL = "https://test.live"
TEST_DISCORD_HANDLE = "test#1234"
TEST_TWITTER_HANDLE = "@test"
TEST_CATEGORY = "AI/Agents"
TEST_SOLANA_ADDRESS = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
TEST_TEAM_NAME = "Test Team"

# Test IDs and Prefixes
TEST_SUBMISSION_ID_START = 1000  # Start test IDs at 1000 to avoid conflicts
SMOKE_TEST_ID = 1001

# Categories
VALID_CATEGORIES = ["DeFi", "Gaming", "AI/Agents", "Infrastructure", "Social"]

# Expected HTTP Status Codes
HTTP_OK = 200
HTTP_CREATED = 201
HTTP_BAD_REQUEST = 400
HTTP_NOT_FOUND = 404
HTTP_UNPROCESSABLE_ENTITY = 422
HTTP_RATE_LIMITED = 429

# Image Testing Constants
TEST_IMAGE_SIZE = (400, 300)
TEST_IMAGE_COLOR = "lightblue"
TEST_IMAGE_TEXT = "Test Image"
SMALL_IMAGE_SIZE = (10, 10)
MAX_IMAGE_SIZE_MB = 5
