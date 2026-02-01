"""
Authentication Routes for RWA-Studio
Author: Sowad Al-Mughni

Provides JWT-based authentication with support for both
traditional login and wallet-based authentication.
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from datetime import datetime, timedelta, timezone
from src.models.user import User, db
import re


def utc_now():
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

auth_bp = Blueprint('auth', __name__)

# Token blocklist for logout functionality
token_blocklist = set()

def is_valid_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def is_valid_ethereum_address(address):
    """Validate Ethereum address format"""
    if not address:
        return True  # Optional field
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return re.match(pattern, address) is not None

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user account"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username'):
            return jsonify({'success': False, 'error': 'Username is required'}), 400
        if not data.get('email'):
            return jsonify({'success': False, 'error': 'Email is required'}), 400
        if not data.get('password'):
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        # Validate email format
        if not is_valid_email(data['email']):
            return jsonify({'success': False, 'error': 'Invalid email format'}), 400
        
        # Validate password strength
        if len(data['password']) < 8:
            return jsonify({'success': False, 'error': 'Password must be at least 8 characters'}), 400
        
        # Validate wallet address if provided
        if data.get('wallet_address') and not is_valid_ethereum_address(data['wallet_address']):
            return jsonify({'success': False, 'error': 'Invalid Ethereum address format'}), 400
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 409
        
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 409
        
        # Check if wallet address already exists (if provided)
        if data.get('wallet_address'):
            if User.query.filter_by(wallet_address=data['wallet_address'].lower()).first():
                return jsonify({'success': False, 'error': 'Wallet address already registered'}), 409
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'].lower(),
            wallet_address=data.get('wallet_address', '').lower() if data.get('wallet_address') else None,
            role=data.get('role', 'user')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'username': user.username}
        )
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user with email/username and password"""
    try:
        data = request.get_json()
        
        if not data.get('email') and not data.get('username'):
            return jsonify({'success': False, 'error': 'Email or username is required'}), 400
        if not data.get('password'):
            return jsonify({'success': False, 'error': 'Password is required'}), 400
        
        # Find user by email or username
        user = None
        if data.get('email'):
            user = User.query.filter_by(email=data['email'].lower()).first()
        elif data.get('username'):
            user = User.query.filter_by(username=data['username']).first()
        
        if not user:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 403
        
        if not user.check_password(data['password']):
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        
        # Update last login
        user.last_login = utc_now()
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'username': user.username}
        )
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/login/wallet', methods=['POST'])
def login_with_wallet():
    """
    Authenticate user with wallet signature (simplified version).
    In production, this should verify a signed message.
    """
    try:
        data = request.get_json()
        
        if not data.get('wallet_address'):
            return jsonify({'success': False, 'error': 'Wallet address is required'}), 400
        
        if not is_valid_ethereum_address(data['wallet_address']):
            return jsonify({'success': False, 'error': 'Invalid Ethereum address format'}), 400
        
        # TODO: In production, verify the signature of a challenge message
        # For now, we just look up the user by wallet address
        
        wallet_address = data['wallet_address'].lower()
        user = User.query.filter_by(wallet_address=wallet_address).first()
        
        if not user:
            # Auto-create user for wallet-based login
            username = f"wallet_{wallet_address[:8]}"
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"wallet_{wallet_address[:8]}_{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=f"{wallet_address}@wallet.rwa-studio.com",
                wallet_address=wallet_address,
                role='user'
            )
            db.session.add(user)
            db.session.commit()
        
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 403
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate tokens
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'username': user.username, 'wallet': wallet_address}
        )
        refresh_token = create_refresh_token(identity=str(user.id))
        
        return jsonify({
            'success': True,
            'message': 'Wallet login successful',
            'data': {
                'user': user.to_dict(),
                'access_token': access_token,
                'refresh_token': refresh_token
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token using refresh token"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 403
        
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={'role': user.role, 'username': user.username}
        )
        
        return jsonify({
            'success': True,
            'data': {
                'access_token': access_token
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout and invalidate the current token"""
    try:
        jti = get_jwt()['jti']
        token_blocklist.add(jti)
        
        return jsonify({
            'success': True,
            'message': 'Successfully logged out'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'data': {
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Update current authenticated user's profile"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if data.get('username'):
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user.id:
                return jsonify({'success': False, 'error': 'Username already exists'}), 409
            user.username = data['username']
        
        if data.get('email'):
            if not is_valid_email(data['email']):
                return jsonify({'success': False, 'error': 'Invalid email format'}), 400
            existing = User.query.filter_by(email=data['email'].lower()).first()
            if existing and existing.id != user.id:
                return jsonify({'success': False, 'error': 'Email already registered'}), 409
            user.email = data['email'].lower()
        
        if data.get('wallet_address'):
            if not is_valid_ethereum_address(data['wallet_address']):
                return jsonify({'success': False, 'error': 'Invalid Ethereum address format'}), 400
            existing = User.query.filter_by(wallet_address=data['wallet_address'].lower()).first()
            if existing and existing.id != user.id:
                return jsonify({'success': False, 'error': 'Wallet address already registered'}), 409
            user.wallet_address = data['wallet_address'].lower()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'data': {
                'user': user.to_dict()
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change current user's password"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        data = request.get_json()
        
        if not data.get('current_password'):
            return jsonify({'success': False, 'error': 'Current password is required'}), 400
        if not data.get('new_password'):
            return jsonify({'success': False, 'error': 'New password is required'}), 400
        
        if len(data['new_password']) < 8:
            return jsonify({'success': False, 'error': 'New password must be at least 8 characters'}), 400
        
        if not user.check_password(data['current_password']):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        user.set_password(data['new_password'])
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# Utility function to check if token is blocklisted
def check_if_token_revoked(jwt_header, jwt_payload):
    """Callback to check if a token has been revoked"""
    jti = jwt_payload['jti']
    return jti in token_blocklist
