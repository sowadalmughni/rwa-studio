"""
Rate Limiting Middleware for RWA-Studio
Author: Sowad Al-Mughni

Provides configurable rate limiting for API endpoints
to prevent abuse and ensure fair usage.

OWASP: Implements protection against brute force and DoS attacks.
Rate limits are applied per-IP by default, with user-based limits
for authenticated requests.
"""

from flask import jsonify, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import os
import logging

logger = logging.getLogger(__name__)

# ==========================================
# RATE LIMIT KEY FUNCTIONS
# ==========================================

def get_rate_limit_key():
    """
    Get rate limit key combining IP address and user identity.
    
    OWASP: Use both IP and user-based rate limiting to prevent
    abuse from authenticated users while still protecting against
    distributed attacks.
    
    Returns:
        str: Rate limit key in format "ip:X.X.X.X" or "user:ID:ip:X.X.X.X"
    """
    ip_address = get_remote_address()
    
    # Try to get user identity from JWT
    try:
        from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            # Combine user ID and IP for authenticated requests
            return f"user:{user_id}:ip:{ip_address}"
    except Exception:
        pass
    
    # Fall back to IP-only for unauthenticated requests
    return f"ip:{ip_address}"


# Initialize limiter with combined IP + user key function
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[os.environ.get('RATELIMIT_DEFAULT', '1000 per minute')],
    storage_uri=os.environ.get('RATELIMIT_STORAGE_URL', 'memory://'),
    strategy='fixed-window',
    headers_enabled=True
)


def init_rate_limiter(app):
    """
    Initialize rate limiter with Flask app.
    
    Configures:
    - Default rate limits
    - Custom 429 error handler with Retry-After header
    - Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, etc.)
    """
    limiter.init_app(app)
    
    # Log rate limit storage configuration
    storage_url = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    if 'memory://' in storage_url and os.environ.get('FLASK_ENV') == 'production':
        logger.warning(
            "SECURITY WARNING: In-memory rate limiting in production. "
            "Configure RATELIMIT_STORAGE_URL to use Redis for multi-instance deployments."
        )
    
    # Custom error handler for rate limit exceeded (HTTP 429)
    @app.errorhandler(429)
    def rate_limit_exceeded(e):
        """
        Handle rate limit exceeded errors with graceful 429 response.
        
        OWASP: Provide clear feedback about rate limits without
        exposing internal system details.
        """
        # Extract retry_after from the error
        retry_after = None
        if hasattr(e, 'description') and 'retry after' in str(e.description).lower():
            try:
                # Parse retry time from description
                import re
                match = re.search(r'(\d+)\s*second', str(e.description))
                if match:
                    retry_after = int(match.group(1))
            except Exception:
                pass
        
        response = jsonify({
            'success': False,
            'error': {
                'code': 'RATE_LIMIT_EXCEEDED',
                'message': 'Too many requests. Please slow down.',
                'retry_after': retry_after
            }
        })
        
        # Set Retry-After header for client compliance
        if retry_after:
            response.headers['Retry-After'] = str(retry_after)
        
        return response, 429
    
    return limiter


# ==========================================
# RATE LIMIT DECORATORS
# ==========================================

def rate_limit_auth(f):
    """
    Rate limit for authentication endpoints.
    
    Stricter limits to prevent brute force attacks:
    - 20 requests per minute for login/register
    - 5 requests per minute for sensitive operations like password reset
    
    OWASP: Mitigates A07:2021 - Identification and Authentication Failures
    """
    @wraps(f)
    @limiter.limit(os.environ.get('RATELIMIT_AUTH', '20 per minute'))
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def rate_limit_sensitive(f):
    """
    Rate limit for sensitive operations.
    
    Very strict limits for operations like:
    - Password changes
    - Wallet linking
    - Admin operations
    
    5 requests per minute to prevent abuse.
    """
    @wraps(f)
    @limiter.limit(os.environ.get('RATELIMIT_SENSITIVE', '5 per minute'))
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def rate_limit_write(f):
    """
    Rate limit for write operations (POST/PUT/DELETE).
    
    Moderate limits to prevent spam and abuse:
    - 30 requests per minute for data mutations
    
    OWASP: Helps prevent resource exhaustion attacks
    """
    @wraps(f)
    @limiter.limit(os.environ.get('RATELIMIT_WRITE', '30 per minute'))
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def rate_limit_read(f):
    """
    Rate limit for read operations (GET).
    
    Generous limits for normal usage:
    - 200 requests per minute for data reads
    """
    @wraps(f)
    @limiter.limit(os.environ.get('RATELIMIT_READ', '200 per minute'))
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def rate_limit_public(f):
    """
    Rate limit for public endpoints (no auth required).
    
    Moderate limits to prevent scraping:
    - 60 requests per minute for public data
    """
    @wraps(f)
    @limiter.limit(os.environ.get('RATELIMIT_PUBLIC', '60 per minute'))
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function


def custom_rate_limit(limit_string):
    """
    Custom rate limit decorator.
    
    Args:
        limit_string: Rate limit in format "X per Y" (e.g., "10 per minute")
    
    Example:
        @custom_rate_limit("5 per hour")
        def expensive_operation():
            pass
    """
    def decorator(f):
        @wraps(f)
        @limiter.limit(limit_string)
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function
    return decorator


# ==========================================
# ACCOUNT LOCKOUT FOR FAILED LOGINS
# ==========================================

# In-memory failed login tracker (use Redis in production)
_failed_login_attempts = {}


def get_failed_attempts(identifier):
    """
    Get failed login attempts for an identifier (IP or username).
    
    Returns:
        tuple: (attempt_count, lockout_until_timestamp or None)
    """
    import time
    current_time = time.time()
    
    if identifier not in _failed_login_attempts:
        return 0, None
    
    attempts, lockout_until = _failed_login_attempts[identifier]
    
    # Check if lockout has expired
    if lockout_until and current_time > lockout_until:
        # Clear expired lockout
        del _failed_login_attempts[identifier]
        return 0, None
    
    return attempts, lockout_until


def record_failed_login(identifier, max_attempts=5, lockout_duration=900):
    """
    Record a failed login attempt and apply lockout if threshold reached.
    
    Args:
        identifier: IP address or username
        max_attempts: Number of attempts before lockout (default: 5)
        lockout_duration: Lockout duration in seconds (default: 15 minutes)
    
    Returns:
        tuple: (is_locked_out, remaining_attempts, lockout_seconds)
    
    OWASP: Implements account lockout to prevent brute force attacks
    """
    import time
    current_time = time.time()
    
    attempts, lockout_until = get_failed_attempts(identifier)
    
    # Already locked out
    if lockout_until and current_time < lockout_until:
        return True, 0, int(lockout_until - current_time)
    
    # Increment attempts
    attempts += 1
    
    if attempts >= max_attempts:
        # Apply lockout
        lockout_until = current_time + lockout_duration
        _failed_login_attempts[identifier] = (attempts, lockout_until)
        logger.warning(f"Account locked out: {identifier} after {attempts} failed attempts")
        return True, 0, lockout_duration
    
    # Store attempt without lockout
    _failed_login_attempts[identifier] = (attempts, None)
    return False, max_attempts - attempts, 0


def clear_failed_attempts(identifier):
    """
    Clear failed login attempts after successful login.
    
    Args:
        identifier: IP address or username
    """
    if identifier in _failed_login_attempts:
        del _failed_login_attempts[identifier]


def check_account_lockout(identifier):
    """
    Check if an account/IP is currently locked out.
    
    Args:
        identifier: IP address or username
    
    Returns:
        tuple: (is_locked_out, lockout_remaining_seconds)
    """
    import time
    attempts, lockout_until = get_failed_attempts(identifier)
    
    if lockout_until:
        remaining = int(lockout_until - time.time())
        if remaining > 0:
            return True, remaining
    
    return False, 0
