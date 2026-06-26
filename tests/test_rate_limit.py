import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.security.rate_limit import rate_limiter


@pytest.fixture(autouse=True)
def clean_rate_limiter():
    rate_limiter.reset_all()
    yield
    rate_limiter.reset_all()


def test_rate_limiter_basic() -> None:
    ident = "127.0.0.1"
    
    # Check initial hits (limit=3)
    for i in range(3):
        is_limited, info = rate_limiter.check(ident, limit=3, window_seconds=60)
        assert not is_limited
        assert info.remaining == 2 - i
        
    # 4th hit should be limited
    is_limited, info = rate_limiter.check(ident, limit=3, window_seconds=60)
    assert is_limited
    assert info.remaining == 0


def test_rate_limiter_reset() -> None:
    ident = "test-user"
    is_limited, info = rate_limiter.check(ident, limit=1, window_seconds=10)
    assert not is_limited
    
    # 2nd hit limited
    is_limited, info = rate_limiter.check(ident, limit=1, window_seconds=10)
    assert is_limited
    
    # Reset
    rate_limiter.reset(ident)
    is_limited, info = rate_limiter.check(ident, limit=1, window_seconds=10)
    assert not is_limited


def test_rate_limiting_middleware() -> None:
    client = TestClient(app)
    
    # We will check rate limit hits on health check endpoint.
    # Set default rate limit low (e.g. limit=2)
    with patch("app.security.rate_limit.RateLimiter.DEFAULT_LIMIT", 2):
        with patch("app.security.rate_limit.RateLimiter.DEFAULT_WINDOW", 10.0):
            # First request
            res1 = client.get("/health")
            assert res1.status_code == 200
            
            # Second request
            res2 = client.get("/health")
            assert res2.status_code == 200
            
            # Third request (should be rate-limited)
            res3 = client.get("/health")
            assert res3.status_code == 429
            assert "Rate limit exceeded" in res3.json()["detail"]
            assert "Retry-After" in res3.headers
