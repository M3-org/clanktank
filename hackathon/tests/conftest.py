from unittest.mock import patch
import pytest

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