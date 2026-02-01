"""
Pytest configuration for RWA-Studio Backend Tests
"""

import os
import sys
import pytest

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Set testing environment
os.environ['FLASK_ENV'] = 'testing'
os.environ['SECRET_KEY'] = 'test-secret-key-for-testing-only-not-production'
os.environ['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-testing-only'

# Strong password for test fixtures that meets complexity requirements
TEST_PASSWORD = 'TestPass123!'


@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    from src.main import app as flask_app
    
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with flask_app.app_context():
        from src.models.user import db
        db.create_all()
        yield flask_app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def auth_headers(client):
    """Get authentication headers for protected routes"""
    # Register a test user with strong password
    client.post('/api/auth/register', json={
        'username': 'testuser',
        'email': 'test@example.com',
        'password': TEST_PASSWORD
    })
    
    # Login to get token
    response = client.post('/api/auth/login', json={
        'email': 'test@example.com',
        'password': TEST_PASSWORD
    })
    
    data = response.get_json()
    token = data.get('data', {}).get('access_token', '')
    
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def admin_headers(client):
    """Get admin authentication headers"""
    # Register an admin user with strong password
    client.post('/api/auth/register', json={
        'username': 'adminuser',
        'email': 'admin@example.com',
        'password': TEST_PASSWORD,
        'role': 'admin'
    })
    
    # Login to get token
    response = client.post('/api/auth/login', json={
        'email': 'admin@example.com',
        'password': TEST_PASSWORD
    })
    
    data = response.get_json()
    token = data.get('data', {}).get('access_token', '')
    
    return {'Authorization': f'Bearer {token}'}
