"""
Error Handling Middleware for RWA-Studio
Author: Sowad Al-Mughni

Provides structured error responses and logging
for production-ready error handling.
"""

from flask import jsonify, request
from functools import wraps
import traceback
import logging
import sys
import os
from datetime import datetime

# Configure structured logging
log_format = os.environ.get('LOG_FORMAT', 'json')
log_level = os.environ.get('LOG_LEVEL', 'INFO')

logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('rwa-studio')


class APIError(Exception):
    """Base API Error class for structured error responses"""
    
    def __init__(self, message, status_code=400, error_code=None, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or f"ERR_{status_code}"
        self.details = details or {}
    
    def to_dict(self):
        return {
            'success': False,
            'error': {
                'code': self.error_code,
                'message': self.message,
                'details': self.details
            }
        }


class ValidationError(APIError):
    """Validation error for invalid input"""
    
    def __init__(self, message, field=None, details=None):
        super().__init__(
            message=message,
            status_code=400,
            error_code='VALIDATION_ERROR',
            details={'field': field, **(details or {})}
        )


class AuthenticationError(APIError):
    """Authentication error"""
    
    def __init__(self, message='Authentication required'):
        super().__init__(
            message=message,
            status_code=401,
            error_code='AUTHENTICATION_ERROR'
        )


class AuthorizationError(APIError):
    """Authorization error"""
    
    def __init__(self, message='Insufficient permissions'):
        super().__init__(
            message=message,
            status_code=403,
            error_code='AUTHORIZATION_ERROR'
        )


class NotFoundError(APIError):
    """Resource not found error"""
    
    def __init__(self, resource='Resource', identifier=None):
        super().__init__(
            message=f'{resource} not found',
            status_code=404,
            error_code='NOT_FOUND',
            details={'resource': resource, 'identifier': identifier}
        )


class ConflictError(APIError):
    """Conflict error for duplicate resources"""
    
    def __init__(self, message='Resource already exists', resource=None):
        super().__init__(
            message=message,
            status_code=409,
            error_code='CONFLICT',
            details={'resource': resource}
        )


class BlockchainError(APIError):
    """Blockchain-related error"""
    
    def __init__(self, message, tx_hash=None, details=None):
        super().__init__(
            message=message,
            status_code=502,
            error_code='BLOCKCHAIN_ERROR',
            details={'tx_hash': tx_hash, **(details or {})}
        )


def log_error(error, request_info=None):
    """Log error with context"""
    error_context = {
        'timestamp': datetime.utcnow().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'request': request_info or {}
    }
    
    if isinstance(error, APIError):
        error_context['error_code'] = error.error_code
        error_context['status_code'] = error.status_code
        logger.warning(f"API Error: {error_context}")
    else:
        error_context['traceback'] = traceback.format_exc()
        logger.error(f"Unhandled Error: {error_context}")
    
    return error_context


def get_request_info():
    """Get request context for logging"""
    return {
        'method': request.method,
        'path': request.path,
        'ip': request.remote_addr,
        'user_agent': request.user_agent.string if request.user_agent else None
    }


def init_error_handlers(app):
    """Initialize error handlers for Flask app"""
    
    @app.errorhandler(APIError)
    def handle_api_error(error):
        """Handle custom API errors"""
        log_error(error, get_request_info())
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(400)
    def handle_bad_request(error):
        """Handle bad request errors"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'BAD_REQUEST',
                'message': str(error.description) if hasattr(error, 'description') else 'Bad request'
            }
        }), 400
    
    @app.errorhandler(401)
    def handle_unauthorized(error):
        """Handle unauthorized errors"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Authentication required'
            }
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(error):
        """Handle forbidden errors"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'FORBIDDEN',
                'message': 'Insufficient permissions'
            }
        }), 403
    
    @app.errorhandler(404)
    def handle_not_found(error):
        """Handle not found errors"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'NOT_FOUND',
                'message': 'Resource not found'
            }
        }), 404
    
    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """Handle method not allowed errors"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'METHOD_NOT_ALLOWED',
                'message': f'Method {request.method} not allowed for this endpoint'
            }
        }), 405
    
    @app.errorhandler(422)
    def handle_unprocessable_entity(error):
        """Handle validation errors"""
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': str(error.description) if hasattr(error, 'description') else 'Validation failed'
            }
        }), 422
    
    @app.errorhandler(500)
    def handle_internal_error(error):
        """Handle internal server errors"""
        log_error(error, get_request_info())
        
        # Don't expose internal errors in production
        is_production = os.environ.get('FLASK_ENV') == 'production'
        message = 'An internal error occurred' if is_production else str(error)
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': message
            }
        }), 500
    
    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle all unhandled exceptions"""
        log_error(error, get_request_info())
        
        # Don't expose internal errors in production
        is_production = os.environ.get('FLASK_ENV') == 'production'
        message = 'An unexpected error occurred' if is_production else str(error)
        
        return jsonify({
            'success': False,
            'error': {
                'code': 'UNEXPECTED_ERROR',
                'message': message
            }
        }), 500
    
    return app


def handle_errors(f):
    """Decorator for consistent error handling in routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except APIError:
            raise  # Let the error handler deal with it
        except Exception as e:
            log_error(e, get_request_info())
            is_production = os.environ.get('FLASK_ENV') == 'production'
            message = 'An unexpected error occurred' if is_production else str(e)
            return jsonify({
                'success': False,
                'error': {
                    'code': 'UNEXPECTED_ERROR',
                    'message': message
                }
            }), 500
    return decorated_function
