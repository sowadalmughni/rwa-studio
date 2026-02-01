"""
Configuration Tests for RWA-Studio
"""

import os
import pytest


class TestConfiguration:
    """Test configuration module"""
    
    def test_config_loads(self):
        """Test that configuration loads without errors"""
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['SECRET_KEY'] = 'test-secret'
        
        from src.config import get_config
        config = get_config()
        
        assert config is not None
        assert config.FLASK_ENV == 'testing'
    
    def test_config_development_defaults(self):
        """Test development configuration defaults"""
        os.environ['FLASK_ENV'] = 'development'
        os.environ.pop('SECRET_KEY', None)
        
        from src.config import DevelopmentConfig
        
        # Should not raise in development even without SECRET_KEY
        assert DevelopmentConfig.FLASK_ENV == 'development'
    
    def test_config_cors_origins_parsing(self):
        """Test CORS origins are parsed correctly"""
        os.environ['CORS_ORIGINS'] = 'http://localhost:3000,http://localhost:5173'
        
        from src.config import Config
        
        assert isinstance(Config.CORS_ORIGINS, list)
        assert 'http://localhost:3000' in Config.CORS_ORIGINS
    
    def test_config_jwt_expiration(self):
        """Test JWT expiration configuration"""
        from src.config import Config
        
        # Should have timedelta objects
        assert Config.JWT_ACCESS_TOKEN_EXPIRES is not None
        assert Config.JWT_REFRESH_TOKEN_EXPIRES is not None


class TestHealthCheck:
    """Test health check endpoint"""
    
    def test_health_check(self, client):
        """Test health check returns healthy status"""
        response = client.get('/health')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert 'environment' in data
        assert 'version' in data
