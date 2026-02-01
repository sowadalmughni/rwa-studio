"""
Security Middleware for RWA-Studio
Author: Sowad Al-Mughni

Provides security headers and request sanitization
for production-ready security posture.
"""

from flask import request, g
from functools import wraps
import time
import uuid


def init_security_headers(app):
    """Initialize security headers middleware"""
    
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS filter
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none';"
        )
        
        # Permissions Policy (formerly Feature Policy)
        response.headers['Permissions-Policy'] = (
            'geolocation=(), microphone=(), camera=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
        )
        
        # Strict Transport Security (HTTPS)
        # Only enable in production with HTTPS
        import os
        if os.environ.get('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Add request ID for tracing
        if hasattr(g, 'request_id'):
            response.headers['X-Request-ID'] = g.request_id
        
        return response
    
    @app.before_request
    def before_request():
        """Pre-request processing"""
        # Generate unique request ID for tracing
        g.request_id = str(uuid.uuid4())
        g.request_start_time = time.time()
    
    @app.after_request
    def add_timing_header(response):
        """Add server timing header"""
        if hasattr(g, 'request_start_time'):
            elapsed = time.time() - g.request_start_time
            response.headers['Server-Timing'] = f'total;dur={elapsed*1000:.2f}'
        return response
    
    return app


def require_https(f):
    """Decorator to require HTTPS in production"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        import os
        if os.environ.get('FLASK_ENV') == 'production':
            if not request.is_secure:
                return {'success': False, 'error': 'HTTPS required'}, 403
        return f(*args, **kwargs)
    return decorated_function


def sanitize_request_data():
    """Middleware to sanitize all incoming request data"""
    
    def sanitize_value(value):
        """Recursively sanitize a value"""
        if isinstance(value, str):
            # Remove null bytes
            value = value.replace('\x00', '')
            # Limit string length
            return value[:10000]
        elif isinstance(value, dict):
            return {k: sanitize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [sanitize_value(v) for v in value[:1000]]  # Limit array size
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
