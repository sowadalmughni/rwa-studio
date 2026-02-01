"""
Configuration Management for RWA-Studio Backend
Author: Sowad Al-Mughni

Centralized configuration with environment variable support
and validation for production readiness.
"""

import os
import sys
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class ConfigurationError(Exception):
    """Raised when configuration validation fails"""
    pass


class Config:
    """Base configuration class with validation"""
    
    # ==========================================
    # SECURITY SETTINGS
    # ==========================================
    
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # ==========================================
    # JWT CONFIGURATION
    # ==========================================
    
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        hours=int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES_HOURS', 1))
    )
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(
        days=int(os.environ.get('JWT_REFRESH_TOKEN_EXPIRES_DAYS', 30))
    )
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # ==========================================
    # DATABASE CONFIGURATION
    # ==========================================
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ==========================================
    # CORS CONFIGURATION
    # ==========================================
    
    CORS_ORIGINS = os.environ.get(
        'CORS_ORIGINS', 
        'http://localhost:5173,http://localhost:3000'
    ).split(',')
    
    # ==========================================
    # RATE LIMITING
    # ==========================================
    
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '1000 per minute')
    RATELIMIT_AUTH = os.environ.get('RATELIMIT_AUTH', '100 per minute')
    RATELIMIT_WRITE = os.environ.get('RATELIMIT_WRITE', '50 per minute')
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_STRATEGY = 'fixed-window'
    
    # ==========================================
    # BLOCKCHAIN CONFIGURATION
    # ==========================================
    
    DEFAULT_NETWORK = os.environ.get('DEFAULT_NETWORK', 'sepolia')
    ETHEREUM_RPC_URL = os.environ.get('ETHEREUM_RPC_URL')
    POLYGON_RPC_URL = os.environ.get('POLYGON_RPC_URL')
    
    # ==========================================
    # LOGGING CONFIGURATION
    # ==========================================
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json')
    
    # ==========================================
    # KYC PROVIDER (Onfido)
    # ==========================================
    
    ONFIDO_API_TOKEN = os.environ.get('ONFIDO_API_TOKEN')
    ONFIDO_WEBHOOK_SECRET = os.environ.get('ONFIDO_WEBHOOK_SECRET')
    ONFIDO_API_URL = os.environ.get('ONFIDO_API_URL', 'https://api.onfido.com/v3.6')
    ONFIDO_REGION = os.environ.get('ONFIDO_REGION', 'us')
    
    # ==========================================
    # PAYMENT GATEWAY (Stripe)
    # ==========================================
    
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
    STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    # Subscription Plans
    STRIPE_PRICE_STARTER = os.environ.get('STRIPE_PRICE_STARTER')
    STRIPE_PRICE_PROFESSIONAL = os.environ.get('STRIPE_PRICE_PROFESSIONAL')
    STRIPE_PRICE_ENTERPRISE = os.environ.get('STRIPE_PRICE_ENTERPRISE')
    
    # ==========================================
    # EMAIL SERVICE (SendGrid)
    # ==========================================
    
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    EMAIL_FROM_ADDRESS = os.environ.get('EMAIL_FROM_ADDRESS', 'noreply@rwa-studio.com')
    EMAIL_FROM_NAME = os.environ.get('EMAIL_FROM_NAME', 'RWA-Studio')
    
    # ==========================================
    # IPFS STORAGE (Pinata)
    # ==========================================
    
    PINATA_API_KEY = os.environ.get('PINATA_API_KEY')
    PINATA_SECRET_KEY = os.environ.get('PINATA_SECRET_KEY')
    PINATA_JWT = os.environ.get('PINATA_JWT')
    IPFS_GATEWAY_URL = os.environ.get('IPFS_GATEWAY_URL', 'https://gateway.pinata.cloud/ipfs')
    
    # ==========================================
    # CELERY (Async Tasks)
    # ==========================================
    
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/1')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/2')
    
    # ==========================================
    # ENVIRONMENT
    # ==========================================
    
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 'yes')
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    @classmethod
    def validate(cls):
        """Validate critical configuration settings"""
        errors = []
        
        # Check for required secrets in production
        if cls.FLASK_ENV == 'production':
            if not cls.SECRET_KEY:
                errors.append("SECRET_KEY is required in production")
            elif cls.SECRET_KEY == 'your-super-secret-key-change-in-production':
                errors.append("SECRET_KEY must be changed from default in production")
            
            if not cls.JWT_SECRET_KEY:
                errors.append("JWT_SECRET_KEY is required in production")
            elif cls.JWT_SECRET_KEY == 'your-jwt-secret-key-change-in-production':
                errors.append("JWT_SECRET_KEY must be changed from default in production")
            
            if cls.DEBUG:
                errors.append("DEBUG must be False in production")
        
        # Ensure secrets are set (with fallback for development)
        if not cls.SECRET_KEY:
            if cls.FLASK_ENV == 'development':
                cls.SECRET_KEY = 'dev-secret-key-not-for-production'
                print("WARNING: Using default SECRET_KEY. Set SECRET_KEY in .env for production.", file=sys.stderr)
            else:
                errors.append("SECRET_KEY must be set")
        
        if not cls.JWT_SECRET_KEY:
            cls.JWT_SECRET_KEY = cls.SECRET_KEY
        
        if errors:
            raise ConfigurationError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        
        return True
    
    @classmethod
    def to_dict(cls):
        """Return configuration as dictionary (excluding secrets)"""
        return {
            'environment': cls.FLASK_ENV,
            'debug': cls.DEBUG,
            'database_url': '***' if cls.SQLALCHEMY_DATABASE_URI else None,
            'cors_origins': cls.CORS_ORIGINS,
            'rate_limit_default': cls.RATELIMIT_DEFAULT,
            'default_network': cls.DEFAULT_NETWORK,
            'log_level': cls.LOG_LEVEL,
        }


class DevelopmentConfig(Config):
    """Development configuration"""
    FLASK_ENV = 'development'
    DEBUG = True


class StagingConfig(Config):
    """Staging configuration"""
    FLASK_ENV = 'staging'
    DEBUG = False


class ProductionConfig(Config):
    """Production configuration with strict validation"""
    FLASK_ENV = 'production'
    DEBUG = False
    
    @classmethod
    def validate(cls):
        """Additional production-specific validation"""
        super().validate()
        
        # Ensure we're using a proper database in production
        if 'sqlite' in cls.SQLALCHEMY_DATABASE_URI.lower():
            print("WARNING: SQLite is not recommended for production", file=sys.stderr)
        
        # Ensure Redis is configured for rate limiting in production
        if 'memory://' in cls.RATELIMIT_STORAGE_URL:
            print("WARNING: In-memory rate limiting is not recommended for production", file=sys.stderr)
        
        return True


class TestingConfig(Config):
    """Testing configuration"""
    FLASK_ENV = 'testing'
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


# Configuration mapping
config_map = {
    'development': DevelopmentConfig,
    'staging': StagingConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
}


def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    config_class = config_map.get(env, DevelopmentConfig)
    config_class.validate()
    return config_class
