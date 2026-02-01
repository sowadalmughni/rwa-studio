"""
User Management Routes for RWA-Studio
Author: Sowad Al-Mughni

CRUD operations for user management with proper authorization.

Security Features (OWASP):
- Rate limiting on all endpoints
- Input validation and sanitization
- Role-based access control
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, db
from src.middleware.rate_limit import rate_limit_read, rate_limit_write
from src.middleware.validation import (
    validate_request, validate_query_params, PAGINATION_SCHEMA,
    ValidationError, sanitize_string, is_valid_email
)
from src.middleware.auth import admin_required

user_bp = Blueprint('user', __name__)


# User list/create schema
USER_CREATE_SCHEMA_FIELDS = {
    'username': {'required': True, 'min_length': 3, 'max_length': 50},
    'email': {'required': True, 'max_length': 254},
}


@user_bp.route('/users', methods=['GET'])
@jwt_required()
@rate_limit_read
@validate_query_params(PAGINATION_SCHEMA)
def get_users(validated_params):
    """
    Get paginated list of users.
    
    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20, max: 100)
    
    Requires: Authentication
    Rate limit: 200 requests/minute
    """
    page = validated_params.get('page', 1)
    per_page = validated_params.get('per_page', 20)
    
    users = User.query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': {
            'users': [user.to_dict() for user in users.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': users.total,
                'pages': users.pages,
                'has_next': users.has_next,
                'has_prev': users.has_prev
            }
        }
    })


@user_bp.route('/users', methods=['POST'])
@jwt_required()
@admin_required()
@rate_limit_write
def create_user():
    """
    Create a new user (admin only).
    
    Request body:
    {
        "username": "string",
        "email": "string",
        "password": "string" (optional),
        "role": "user" | "admin" | "transfer_agent" (optional)
    }
    
    Requires: Admin role
    Rate limit: 30 requests/minute
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        # Validate required fields
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        
        if not username or len(username) < 3:
            return jsonify({'success': False, 'error': 'Username must be at least 3 characters'}), 400
        
        if not email or not is_valid_email(email):
            return jsonify({'success': False, 'error': 'Valid email is required'}), 400
        
        # Sanitize inputs
        username = sanitize_string(username, max_length=50)
        email = sanitize_string(email, max_length=254).lower()
        
        # Check for duplicates
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 409
        
        # Create user
        user = User(
            username=username,
            email=email,
            role=data.get('role', 'user')
        )
        
        # Set password if provided
        if data.get('password'):
            user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'user': user.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to create user'}), 500


@user_bp.route('/users/<int:user_id>', methods=['GET'])
@jwt_required()
@rate_limit_read
def get_user(user_id):
    """
    Get user by ID.
    
    Requires: Authentication
    Rate limit: 200 requests/minute
    """
    user = User.query.get_or_404(user_id)
    return jsonify({
        'success': True,
        'data': {'user': user.to_dict()}
    })


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required()
@rate_limit_write
def update_user(user_id):
    """
    Update user by ID (admin only).
    
    Request body:
    {
        "username": "string" (optional),
        "email": "string" (optional),
        "role": "string" (optional),
        "is_active": boolean (optional)
    }
    
    Requires: Admin role
    Rate limit: 30 requests/minute
    """
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        # Update username if provided
        if data.get('username'):
            username = sanitize_string(data['username'], max_length=50)
            existing = User.query.filter_by(username=username).first()
            if existing and existing.id != user.id:
                return jsonify({'success': False, 'error': 'Username already exists'}), 409
            user.username = username
        
        # Update email if provided
        if data.get('email'):
            email = sanitize_string(data['email'], max_length=254).lower()
            if not is_valid_email(email):
                return jsonify({'success': False, 'error': 'Invalid email format'}), 400
            existing = User.query.filter_by(email=email).first()
            if existing and existing.id != user.id:
                return jsonify({'success': False, 'error': 'Email already registered'}), 409
            user.email = email
        
        # Update role if provided (admin only operation)
        if 'role' in data:
            if data['role'] in ['user', 'admin', 'transfer_agent']:
                user.role = data['role']
            else:
                return jsonify({'success': False, 'error': 'Invalid role'}), 400
        
        # Update active status if provided
        if 'is_active' in data:
            user.is_active = bool(data['is_active'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'user': user.to_dict()}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update user'}), 500


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required()
@rate_limit_write
def delete_user(user_id):
    """
    Delete user by ID (admin only).
    
    Requires: Admin role
    Rate limit: 30 requests/minute
    """
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent self-deletion
        current_user_id = get_jwt_identity()
        if str(user.id) == current_user_id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return '', 204
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to delete user'}), 500
