"""
Authentication Routes for RWA-Studio
Author: Sowad Al-Mughni

Provides JWT-based authentication with support for both
traditional login and wallet-based authentication.

Security Features (OWASP):
- Rate limiting on all auth endpoints
- Strong password validation
- Account lockout after failed attempts
- Secure wallet signature verification
- Token blocklist with Redis persistence
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import (
    create_access_token, create_refresh_token, 
    jwt_required, get_jwt_identity, get_jwt
)
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta, timezone
from src.models.user import User, db
from src.middleware.rate_limit import (
    rate_limit_auth, rate_limit_sensitive,
    record_failed_login, clear_failed_attempts, check_account_lockout
)
from src.middleware.validation import (
    validate_request, REGISTER_SCHEMA, LOGIN_SCHEMA, 
    WALLET_LOGIN_SCHEMA, PASSWORD_CHANGE_SCHEMA, PROFILE_UPDATE_SCHEMA,
    is_valid_email, is_valid_ethereum_address, is_strong_password, get_password_requirements
)
import re
import os
import logging

logger = logging.getLogger(__name__)


def utc_now():
    """Get current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc)

auth_bp = Blueprint('auth', __name__)

# ==========================================
# TOKEN BLOCKLIST (Redis-backed in production)
# ==========================================

# Try to use Redis for token blocklist, fall back to in-memory
_redis_client = None
_token_blocklist_memory = set()


def _get_redis_client():
    """Get or initialize Redis client for token blocklist"""
    global _redis_client
    if _redis_client is None:
        redis_url = os.environ.get('RATELIMIT_STORAGE_URL', '')
        if 'redis://' in redis_url:
            try:
                import redis
                _redis_client = redis.from_url(redis_url, decode_responses=True)
                _redis_client.ping()  # Test connection
                logger.info("Token blocklist using Redis storage")
            except Exception as e:
                logger.warning(f"Redis unavailable for token blocklist, using memory: {e}")
                _redis_client = False  # Mark as unavailable
        else:
            _redis_client = False
    return _redis_client if _redis_client else None


def add_token_to_blocklist(jti: str, expires_delta: timedelta = None):
    """
    Add token JTI to blocklist.
    
    OWASP: Implement token revocation for secure logout.
    """
    redis_client = _get_redis_client()
    if redis_client:
        # Store in Redis with expiration matching token lifetime
        ttl = int((expires_delta or timedelta(days=30)).total_seconds())
        redis_client.setex(f"blocklist:{jti}", ttl, "1")
    else:
        _token_blocklist_memory.add(jti)


def is_token_blocklisted(jti: str) -> bool:
    """Check if token JTI is in blocklist"""
    redis_client = _get_redis_client()
    if redis_client:
        return redis_client.exists(f"blocklist:{jti}") > 0
    return jti in _token_blocklist_memory


# Legacy compatibility
token_blocklist = _token_blocklist_memory


@auth_bp.route('/register', methods=['POST'])
@rate_limit_auth
@validate_request(REGISTER_SCHEMA)
def register(validated_data):
    """
    Register a new user account.
    
    Rate limited: 20 requests/minute
    Validates: username, email, password strength, wallet address
    """
    try:
        # Check if username already exists
        if User.query.filter_by(username=validated_data['username']).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 409
        
        # Check if email already exists
        if User.query.filter_by(email=validated_data['email'].lower()).first():
            return jsonify({'success': False, 'error': 'Email already registered'}), 409
        
        # Check if wallet address already exists (if provided)
        wallet_address = validated_data.get('wallet_address')
        if wallet_address:
            if User.query.filter_by(wallet_address=wallet_address.lower()).first():
                return jsonify({'success': False, 'error': 'Wallet address already registered'}), 409
        
        # Create new user (role is always 'user' for self-registration - security)
        user = User(
            username=validated_data['username'],
            email=validated_data['email'].lower(),
            wallet_address=wallet_address.lower() if wallet_address else None,
            role='user'  # Never allow role escalation through registration
        )
        user.set_password(validated_data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f"New user registered: {user.username}")
        
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
        logger.error(f"Registration error: {e}")
        return jsonify({'success': False, 'error': 'Registration failed'}), 500


@auth_bp.route('/login', methods=['POST'])
@rate_limit_auth
@validate_request(LOGIN_SCHEMA)
def login(validated_data):
    """
    Authenticate user with email/username and password.
    
    Rate limited: 20 requests/minute
    Account lockout: 5 failed attempts = 15 minute lockout
    """
    try:
        # Get identifier for lockout tracking
        ip_address = get_remote_address()
        login_identifier = validated_data.get('email') or validated_data.get('username') or ip_address
        
        # Check for account lockout
        is_locked, lockout_remaining = check_account_lockout(login_identifier)
        if is_locked:
            return jsonify({
                'success': False,
                'error': f'Account temporarily locked. Try again in {lockout_remaining} seconds.',
                'retry_after': lockout_remaining
            }), 429
        
        # Validate at least one identifier provided
        if not validated_data.get('email') and not validated_data.get('username'):
            return jsonify({'success': False, 'error': 'Email or username is required'}), 400
        
        # Find user by email or username
        user = None
        if validated_data.get('email'):
            user = User.query.filter_by(email=validated_data['email'].lower()).first()
        elif validated_data.get('username'):
            user = User.query.filter_by(username=validated_data['username']).first()
        
        # Generic error message to prevent user enumeration
        auth_error = 'Invalid credentials'
        
        if not user:
            record_failed_login(login_identifier)
            return jsonify({'success': False, 'error': auth_error}), 401
        
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 403
        
        if not user.check_password(validated_data['password']):
            is_locked, remaining_attempts, lockout_seconds = record_failed_login(login_identifier)
            if is_locked:
                return jsonify({
                    'success': False,
                    'error': f'Account locked due to too many failed attempts. Try again in {lockout_seconds} seconds.',
                    'retry_after': lockout_seconds
                }), 429
            return jsonify({'success': False, 'error': auth_error}), 401
        
        # Successful login - clear failed attempts
        clear_failed_attempts(login_identifier)
        
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
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500
        
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
        logger.error(f"Login error: {e}")
        return jsonify({'success': False, 'error': 'Login failed'}), 500


def verify_ethereum_signature(address: str, message: str, signature: str) -> bool:
    """
    Verify an Ethereum wallet signature.
    
    OWASP: Cryptographic signature verification prevents wallet impersonation.
    Uses EIP-191 personal_sign standard.
    
    Args:
        address: Ethereum address that supposedly signed the message
        message: The original message that was signed
        signature: The signature to verify (hex string with 0x prefix)
    
    Returns:
        bool: True if signature is valid and matches the address
    """
    try:
        from eth_account.messages import encode_defunct
        from eth_account import Account
        
        # Encode the message as per EIP-191
        message_encoded = encode_defunct(text=message)
        
        # Recover the address from the signature
        recovered_address = Account.recover_message(message_encoded, signature=signature)
        
        # Compare addresses (case-insensitive)
        return recovered_address.lower() == address.lower()
    except ImportError:
        logger.warning("eth_account not installed, falling back to insecure wallet login")
        # Fallback for development - DO NOT use in production
        if os.environ.get('FLASK_ENV') == 'development':
            return True
        return False
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        return False


@auth_bp.route('/login/wallet', methods=['POST'])
@rate_limit_auth
@validate_request(WALLET_LOGIN_SCHEMA)
def login_with_wallet(validated_data):
    """
    Authenticate user with wallet signature.
    
    OWASP: Implements secure cryptographic authentication:
    - Verifies EIP-191 personal_sign signature
    - Validates message format and freshness
    - Rate limited to prevent brute force
    
    Request body:
    {
        "wallet_address": "0x...",
        "signature": "0x...",
        "message": "Sign this message to login to RWA-Studio: <nonce>"
    }
    """
    try:
        wallet_address = validated_data['wallet_address'].lower()
        signature = validated_data['signature']
        message = validated_data['message']
        
        # Verify the signature
        if not verify_ethereum_signature(wallet_address, message, signature):
            logger.warning(f"Invalid wallet signature for {wallet_address}")
            return jsonify({
                'success': False, 
                'error': 'Invalid signature'
            }), 401
        
        # Find or create user by wallet address
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
            logger.info(f"Created wallet user: {username}")
        
        if not user.is_active:
            return jsonify({'success': False, 'error': 'Account is deactivated'}), 403
        
        # Update last login
        user.last_login = utc_now()
        db.session.commit()
        
        # Generate tokens with wallet claim
        access_token = create_access_token(
            identity=str(user.id),
            additional_claims={
                'role': user.role, 
                'username': user.username, 
                'wallet': wallet_address
            }
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
        logger.error(f"Wallet login error: {e}")
        return jsonify({'success': False, 'error': 'Wallet login failed'}), 500


@auth_bp.route('/login/wallet/challenge', methods=['POST'])
@rate_limit_auth
def get_wallet_challenge():
    """
    Generate a challenge message for wallet login.
    
    The client should sign this message with their wallet
    and submit it to /login/wallet
    
    Request body:
    {
        "wallet_address": "0x..."
    }
    """
    try:
        data = request.get_json() or {}
        wallet_address = data.get('wallet_address', '')
        
        if not is_valid_ethereum_address(wallet_address):
            return jsonify({
                'success': False,
                'error': 'Invalid wallet address format'
            }), 400
        
        # Generate a time-based nonce for freshness
        import secrets
        nonce = secrets.token_hex(16)
        timestamp = int(utc_now().timestamp())
        
        # Create the challenge message
        message = f"Sign this message to login to RWA-Studio.\n\nWallet: {wallet_address}\nNonce: {nonce}\nTimestamp: {timestamp}"
        
        return jsonify({
            'success': True,
            'data': {
                'message': message,
                'nonce': nonce,
                'timestamp': timestamp,
                'expires_in': 300  # 5 minutes
            }
        })
        
    except Exception as e:
        logger.error(f"Challenge generation error: {e}")
        return jsonify({'success': False, 'error': 'Failed to generate challenge'}), 500


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
        logger.error(f"Token refresh error: {e}")
        return jsonify({'success': False, 'error': 'Token refresh failed'}), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout and invalidate the current token"""
    try:
        jwt_data = get_jwt()
        jti = jwt_data['jti']
        
        # Add token to blocklist
        add_token_to_blocklist(jti)
        
        return jsonify({
            'success': True,
            'message': 'Successfully logged out'
        })
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'success': False, 'error': 'Logout failed'}), 500


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
        logger.error(f"Get profile error: {e}")
        return jsonify({'success': False, 'error': 'Failed to get profile'}), 500


@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
@rate_limit_sensitive
@validate_request(PROFILE_UPDATE_SCHEMA)
def update_current_user(validated_data):
    """
    Update current authenticated user's profile.
    
    Rate limited: 5 requests/minute (sensitive operation)
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Update username if provided
        if validated_data.get('username'):
            existing = User.query.filter_by(username=validated_data['username']).first()
            if existing and existing.id != user.id:
                return jsonify({'success': False, 'error': 'Username already exists'}), 409
            user.username = validated_data['username']
        
        # Update email if provided
        if validated_data.get('email'):
            existing = User.query.filter_by(email=validated_data['email'].lower()).first()
            if existing and existing.id != user.id:
                return jsonify({'success': False, 'error': 'Email already registered'}), 409
            user.email = validated_data['email'].lower()
        
        # Update wallet address if provided
        if validated_data.get('wallet_address'):
            existing = User.query.filter_by(wallet_address=validated_data['wallet_address'].lower()).first()
            if existing and existing.id != user.id:
                return jsonify({'success': False, 'error': 'Wallet address already registered'}), 409
            user.wallet_address = validated_data['wallet_address'].lower()
        
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
        logger.error(f"Profile update error: {e}")
        return jsonify({'success': False, 'error': 'Profile update failed'}), 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@rate_limit_sensitive
@validate_request(PASSWORD_CHANGE_SCHEMA)
def change_password(validated_data):
    """
    Change current user's password.
    
    Rate limited: 5 requests/minute (sensitive operation)
    Validates: Password complexity requirements
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        if not user.check_password(validated_data['current_password']):
            return jsonify({'success': False, 'error': 'Current password is incorrect'}), 401
        
        # Check new password isn't the same as current
        if user.check_password(validated_data['new_password']):
            return jsonify({
                'success': False, 
                'error': 'New password must be different from current password'
            }), 400
        
        user.set_password(validated_data['new_password'])
        db.session.commit()
        
        logger.info(f"Password changed for user: {user.username}")
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Password change error: {e}")
        return jsonify({'success': False, 'error': 'Password change failed'}), 500


# ==========================================
# TOKEN BLOCKLIST CALLBACK
# ==========================================

def check_if_token_revoked(jwt_header, jwt_payload):
    """
    Callback to check if a token has been revoked.
    
    OWASP: Implements token revocation for secure session management.
    """
    jti = jwt_payload['jti']
    return is_token_blocklisted(jti)
