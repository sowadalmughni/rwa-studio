"""
Authentication Middleware for RWA-Studio
Author: Sowad Al-Mughni

Provides decorators for role-based access control.
"""

from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt

def admin_required():
    """
    Decorator that ensures only admin users can access the endpoint.
    Must be used after @jwt_required().
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') != 'admin':
                return jsonify({
                    'success': False, 
                    'error': 'Admin access required'
                }), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def transfer_agent_required():
    """
    Decorator that ensures only transfer_agent or admin users can access the endpoint.
    Must be used after @jwt_required().
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get('role') not in ['admin', 'transfer_agent']:
                return jsonify({
                    'success': False, 
                    'error': 'Transfer agent access required'
                }), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def roles_required(*allowed_roles):
    """
    Decorator that ensures user has one of the specified roles.
    
    Usage:
        @roles_required('admin', 'transfer_agent')
        def my_endpoint():
            ...
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role', 'user')
            if user_role not in allowed_roles:
                return jsonify({
                    'success': False, 
                    'error': f'Access denied. Required roles: {", ".join(allowed_roles)}'
                }), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper


def wallet_verified():
    """
    Decorator that ensures the user has a verified wallet address.
    Useful for blockchain-related operations.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims.get('wallet'):
                return jsonify({
                    'success': False, 
                    'error': 'Wallet verification required'
                }), 403
            return fn(*args, **kwargs)
        return decorator
    return wrapper
