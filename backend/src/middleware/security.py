"""
Security Middleware for RWA-Studio
Author: Sowad Al-Mughni

Provides security headers and request sanitization
for production-ready security posture.

OWASP Security Headers Implementation:
- A05:2021 Security Misconfiguration prevention
- A03:2021 Injection protection via CSP
- Clickjacking protection via X-Frame-Options
"""

from flask import request, g
from functools import wraps
import time
import uuid
import os
import logging

logger = logging.getLogger(__name__)


def init_security_headers(app):
    """
    Initialize security headers middleware.
    
    Implements OWASP recommended security headers for:
    - Clickjacking protection
    - XSS mitigation
    - Content-Type sniffing prevention
    - Referrer policy
    - Content Security Policy
    """
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        
        # ==========================================
        # CLICKJACKING PROTECTION
        # ==========================================
        # OWASP: Prevent framing by malicious sites
        response.headers['X-Frame-Options'] = 'DENY'
        
        # ==========================================
        # CONTENT TYPE PROTECTION
        # ==========================================
        # OWASP: Prevent MIME type sniffing attacks
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # ==========================================
        # XSS PROTECTION
        # ==========================================
        # Legacy XSS filter (for older browsers)
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # ==========================================
        # REFERRER POLICY
        # ==========================================
        # Control referrer information leakage
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # ==========================================
        # CONTENT SECURITY POLICY (CSP)
        # ==========================================
        # OWASP: Primary defense against XSS and injection attacks
        #
        # Note: 'unsafe-inline' for styles is needed for many UI libraries
        # Consider using nonces for production to eliminate 'unsafe-inline'
        
        env = os.environ.get('FLASK_ENV', 'development')
        
        if env == 'production':
            # Stricter CSP for production
            # Remove 'unsafe-eval' in production (breaks some JS libraries)
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "  # No unsafe-inline/eval in production
                "style-src 'self' 'unsafe-inline'; "  # Keep for CSS-in-JS libraries
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "connect-src 'self' https: wss:; "  # Allow HTTPS and WebSocket
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'; "
                "upgrade-insecure-requests; "
            )
        else:
            # More permissive CSP for development
            # Allows hot-reloading and dev tools
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "  # Needed for dev tools
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https: http:; "
                "font-src 'self' data: https:; "
                "connect-src 'self' https: wss: ws: http://localhost:*; "
                "frame-ancestors 'none';"
            )
        
        response.headers['Content-Security-Policy'] = csp
        
        # ==========================================
        # PERMISSIONS POLICY
        # ==========================================
        # Disable unnecessary browser features
        response.headers['Permissions-Policy'] = (
            'geolocation=(), '
            'microphone=(), '
            'camera=(), '
            'payment=(), '
            'usb=(), '
            'magnetometer=(), '
            'gyroscope=(), '
            'accelerometer=()'
        )
        
        # ==========================================
        # STRICT TRANSPORT SECURITY (HSTS)
        # ==========================================
        # Only enable in production with HTTPS
        if env == 'production':
            # max-age=31536000 (1 year), includeSubDomains, preload
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        # ==========================================
        # CACHE CONTROL FOR SECURITY-SENSITIVE RESPONSES
        # ==========================================
        # Prevent caching of authenticated responses
        if request.endpoint and 'auth' in str(request.endpoint):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
            response.headers['Pragma'] = 'no-cache'
        
        # ==========================================
        # REQUEST ID FOR TRACING
        # ==========================================
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    @app.before_request
    def before_request():
        """Pre-request processing"""
        # Generate unique request ID for tracing
        g.request_id = str(uuid.uuid4())
        g.request_start_time = time.time()
        
        # Log request details (without sensitive data)
        logger.debug(
            f"Request: {request.method} {request.path} "
            f"[{g.request_id}] from {request.remote_addr}"
        )
    
    @app.after_request
    def add_timing_header(response):
        """Add server timing header"""
        if hasattr(g, 'request_start_time'):
            elapsed = time.time() - g.request_start_time
            response.headers['Server-Timing'] = f'total;dur={elapsed*1000:.2f}'
        return response
    
    return app


def require_https(f):
    """
    Decorator to require HTTPS in production.
    
    OWASP: Enforce transport layer security
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if os.environ.get('FLASK_ENV') == 'production':
            if not request.is_secure:
                return {'success': False, 'error': 'HTTPS required'}, 403
        return f(*args, **kwargs)
    return decorated_function


def sanitize_request_data():
    """
    Middleware to sanitize all incoming request data.
    
    OWASP: Defense-in-depth input sanitization
    """
    
    def sanitize_value(value, depth=0):
        """Recursively sanitize a value with depth limit"""
        # Prevent infinite recursion
        if depth > 10:
            return None
        
        if isinstance(value, str):
            # Remove null bytes (injection attack vector)
            value = value.replace('\x00', '')
            # Limit string length to prevent DoS
            return value[:10000]
        elif isinstance(value, dict):
            # Limit dict size
            if len(value) > 100:
                return None
            return {k: sanitize_value(v, depth + 1) for k, v in list(value.items())[:100]}
        elif isinstance(value, list):
            # Limit list size
            return [sanitize_value(v, depth + 1) for v in value[:1000]]
        return value
    
    def init_app(app):
        @app.before_request
        def sanitize_request():
            """Sanitize request JSON data"""
            if request.is_json:
                try:
                    data = request.get_json(silent=True)
                    if data:
                        # Store sanitized data
                        g.sanitized_json = sanitize_value(data)
                except Exception:
                    pass
        return app
    
    return init_app


def validate_content_type(allowed_types=['application/json']):
    """
    Decorator to validate Content-Type header.
    
    OWASP: Prevent content-type confusion attacks
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            content_type = request.content_type or ''
            if not any(t in content_type for t in allowed_types):
                return {
                    'success': False, 
                    'error': f'Invalid Content-Type. Expected: {allowed_types}'
                }, 415
            return f(*args, **kwargs)
        return decorated_function
    return decorator
