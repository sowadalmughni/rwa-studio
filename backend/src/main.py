"""
RWA-Studio Backend Application
Author: Sowad Al-Mughni

Main Flask application with production-ready configuration,
security middleware, rate limiting, and error handling.
"""

import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager

# Import configuration
from src.config import get_config

# Import middleware
from src.middleware.rate_limit import init_rate_limiter
from src.middleware.error_handler import init_error_handlers
from src.middleware.security import init_security_headers

# Import models and routes
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp, check_if_token_revoked
from src.routes.transfer_agent import transfer_agent_bp

# Phase 3: Import new routes
from src.routes.kyc import kyc_bp
from src.routes.documents import documents_bp
from src.routes.billing import billing_bp

# Phase 3: Import new models (for db.create_all())
from src.models.subscription import Subscription, BillingHistory
from src.models.kyc import KYCVerification, KYCDocument

# Phase 3: Import Celery
from src.tasks.celery_app import init_celery

# Get validated configuration
config = get_config()

# Initialize Flask app
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))

# Load configuration from config class
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = config.JWT_REFRESH_TOKEN_EXPIRES
app.config['JWT_TOKEN_LOCATION'] = config.JWT_TOKEN_LOCATION
app.config['JWT_HEADER_NAME'] = config.JWT_HEADER_NAME
app.config['JWT_HEADER_TYPE'] = config.JWT_HEADER_TYPE
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS

# Rate limiting configuration
app.config['RATELIMIT_STORAGE_URL'] = config.RATELIMIT_STORAGE_URL
app.config['RATELIMIT_HEADERS_ENABLED'] = config.RATELIMIT_HEADERS_ENABLED

# Initialize security middleware
init_security_headers(app)

# Initialize error handlers
init_error_handlers(app)

# Initialize rate limiter
limiter = init_rate_limiter(app)

# Initialize JWT
jwt = JWTManager(app)

# Register token revocation callback
jwt.token_in_blocklist_loader(check_if_token_revoked)

# Error handlers for JWT
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return {'success': False, 'error': {'code': 'TOKEN_EXPIRED', 'message': 'Token has expired'}}, 401

@jwt.invalid_token_loader
def invalid_token_callback(error):
    return {'success': False, 'error': {'code': 'INVALID_TOKEN', 'message': 'Invalid token'}}, 401

@jwt.unauthorized_loader
def missing_token_callback(error):
    return {'success': False, 'error': {'code': 'UNAUTHORIZED', 'message': 'Authorization token required'}}, 401

@jwt.revoked_token_loader
def revoked_token_callback(jwt_header, jwt_payload):
    return {'success': False, 'error': {'code': 'TOKEN_REVOKED', 'message': 'Token has been revoked'}}, 401

# Enable CORS for frontend integration
CORS(app, origins=config.CORS_ORIGINS)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(transfer_agent_bp, url_prefix='/api/transfer-agent')

# Phase 3: Register new blueprints
app.register_blueprint(kyc_bp, url_prefix='/api/kyc')
app.register_blueprint(documents_bp, url_prefix='/api/documents')
app.register_blueprint(billing_bp, url_prefix='/api/billing')

# Phase 3: Initialize Celery with Flask app context
celery = init_celery(app)

# Initialize database
db.init_app(app)

with app.app_context():
    db.create_all()

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {
        'status': 'healthy',
        'environment': config.FLASK_ENV,
        'version': '3.0.0',
        'phase': 3,
        'services': {
            'kyc': 'onfido',
            'email': 'sendgrid',
            'payments': 'stripe',
            'storage': 'pinata'
        }
    }

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    print(f"🚀 RWA-Studio Backend starting...")
    print(f"   Environment: {config.FLASK_ENV}")
    print(f"   Debug: {config.DEBUG}")
    print(f"   Host: {config.HOST}:{config.PORT}")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
