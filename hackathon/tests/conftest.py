from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient

from .test_utils import reset_database, create_test_submission_data
from .test_image_factory import create_test_image
from .test_db_helpers import cleanup_all_test_data

def noop(*a, **kw):
    return None

class NoOpLimiter:
    def limit(self, *a, **kw):
        def decorator(f):
            return f
        return decorator
    def __getattr__(self, name):
        return noop

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    # Patch limiter.limit to a no-op before any tests run
    limiter_patch = patch('hackathon.backend.app.limiter.limit', new=lambda *a, **kw: (lambda f: f))
    limiter_patch.start()
    config._limiter_patch = limiter_patch

    # Patch Discord authentication globally for all tests
    async def mock_validate_discord_token(request):
        class User:
            discord_id = '1234567890'
            username = 'testuser'
            discriminator = '0001'
            avatar = None
        return User()
    discord_patch = patch('hackathon.backend.app.validate_discord_token', new=mock_validate_discord_token)
    discord_patch.start()
    config._discord_patch = discord_patch

    # After patching, import the app and patch the limiter object and error handler
    import hackathon.backend.app
    from fastapi.responses import JSONResponse
    from slowapi.errors import RateLimitExceeded
    hackathon.backend.app.limiter = NoOpLimiter()
    hackathon.backend.app.app.state.limiter = NoOpLimiter()
    async def fake_rate_limit_handler(request, exc):
        return JSONResponse(status_code=429, content={"error": "Rate limit exceeded (test mock)"})
    hackathon.backend.app.app.exception_handlers[RateLimitExceeded] = fake_rate_limit_handler


def pytest_sessionfinish(session, exitstatus):
    # Stop all patches
    limiter_patch = getattr(session.config, '_limiter_patch', None)
    if limiter_patch:
        limiter_patch.stop()
    discord_patch = getattr(session.config, '_discord_patch', None)
    if discord_patch:
        discord_patch.stop()


# Shared Fixtures

@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment once per session"""
    reset_database()
    yield
    # Cleanup after all tests
    cleanup_all_test_data()


@pytest.fixture
def client():
    """Shared test client fixture"""
    from fastapi.testclient import TestClient
    from hackathon.backend.app import app
    return TestClient(app)


@pytest.fixture
def test_submission_data():
    """Fixture for v2 test submission data"""
    return create_test_submission_data(version="v2")


@pytest.fixture
def test_submission_data_v1():
    """Fixture for v1 test submission data"""
    return create_test_submission_data(version="v1")


@pytest.fixture
def test_image():
    """Fixture for test image"""
    return create_test_image()


@pytest.fixture
def small_test_image():
    """Fixture for small test image"""
    from .test_image_factory import create_small_test_image
    return create_small_test_image()


@pytest.fixture
def large_test_image():
    """Fixture for large test image"""
    from .test_image_factory import create_large_test_image
    return create_large_test_image()


@pytest.fixture(autouse=True)
def cleanup_test_data():
    """Auto-cleanup fixture to clean up test data after each test"""
    yield
    # This runs after each test
    cleanup_all_test_data() 