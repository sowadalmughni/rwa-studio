"""
Rate Limiting Middleware for RWA-Studio
Author: Sowad Al-Mughni

Provides configurable rate limiting for API endpoints
to prevent abuse and ensure fair usage.
"""

from flask import jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import os

# Initialize limiter with default configuration
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[os.environ.get('RATELIMIT_DEFAULT', '1000 per minute')],
    storage_uri=os.environ.get('RATELIMIT_STORAGE_URL', 'memory://'),
    strategy='fixed-window',
    headers_enabled=True
)


def init_rate_limiter(app):
    """Initialize rate limiter with Flask app"""
    limiter.init_app(app)
    
    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        return jsonify({
            'success': False,
            'error': 'Rate limit exceeded',
            'message': str(e.description),
            'retry_after': e.retry_after if hasattr(e, 'retry_after') else None
        }), 429
    
    return limiter


# Rate limit decorators for different endpoint types
def auth_limit():
    """Rate limit for authentication endpoints (100/min)"""
    return limiter.limit(os.environ.get('RATELIMIT_AUTH', '100 per minute'))


def write_limit():
    """Rate limit for write operations (50/min)"""
    return limiter.limit(os.environ.get('RATELIMIT_WRITE', '50 per minute'))


def read_limit():
    """Rate limit for read operations (1000/min)"""
    return limiter.limit(os.environ.get('RATELIMIT_DEFAULT', '1000 per minute'))


def custom_limit(limit_string):
    """Custom rate limit decorator
    
    Args:
        limit_string: Rate limit in format "X per Y" (e.g., "10 per minute")
    """
    return limiter.limit(limit_string)


# IP-based rate limiting with wallet address consideration
def get_rate_limit_key():
    """Get rate limit key based on IP and optionally wallet address"""
    # Try to get wallet address from JWT or request
    wallet_address = None
    
    # Check if there's a JWT token with wallet info
    try:
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        identity = get_jwt_identity()
        if identity:
            wallet_address = identity
    except Exception:
        pass
    
    # If wallet address available, use it as key
    if wallet_address:
        return f"wallet:{wallet_address}"
    
    # Fall back to IP address
    return get_remote_address()


def wallet_aware_limiter():
    """Limiter that considers wallet address for rate limiting"""
    return Limiter(
        key_func=get_rate_limit_key,
        default_limits=['1000 per minute'],
        storage_uri=os.environ.get('RATELIMIT_STORAGE_URL', 'memory://'),
    )
