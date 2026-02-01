"""
Authentication Route Tests for RWA-Studio

Note: Tests use strong passwords that meet complexity requirements:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character
"""

import pytest

# Strong password for testing that meets all complexity requirements
STRONG_PASSWORD = 'TestPass123!'


class TestAuthRoutes:
    """Test authentication endpoints"""
    
    def test_register_success(self, client):
        """Test successful user registration"""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': STRONG_PASSWORD
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert 'access_token' in data['data']
        assert 'refresh_token' in data['data']
        assert data['data']['user']['username'] == 'newuser'
    
    def test_register_missing_username(self, client):
        """Test registration with missing username"""
        response = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': STRONG_PASSWORD
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'invalid-email',
            'password': STRONG_PASSWORD
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_register_short_password(self, client):
        """Test registration with short password"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'short'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_register_weak_password(self, client):
        """Test registration with password lacking complexity"""
        response = client.post('/api/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'  # No uppercase or special char
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username"""
        # First registration
        client.post('/api/auth/register', json={
            'username': 'duplicate',
            'email': 'first@example.com',
            'password': STRONG_PASSWORD
        })
        
        # Second registration with same username
        response = client.post('/api/auth/register', json={
            'username': 'duplicate',
            'email': 'second@example.com',
            'password': STRONG_PASSWORD
        })
        
        assert response.status_code == 409
        data = response.get_json()
        assert data['success'] is False
    
    def test_login_success(self, client):
        """Test successful login"""
        # Register first
        client.post('/api/auth/register', json={
            'username': 'logintest',
            'email': 'logintest@example.com',
            'password': STRONG_PASSWORD
        })
        
        # Then login
        response = client.post('/api/auth/login', json={
            'email': 'logintest@example.com',
            'password': STRONG_PASSWORD
        })
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'access_token' in data['data']
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        response = client.post('/api/auth/login', json={
            'email': 'nonexistent@example.com',
            'password': 'wrongpassword'
        })
        
        assert response.status_code == 401
        data = response.get_json()
        assert data['success'] is False
    
    def test_login_missing_password(self, client):
        """Test login with missing password"""
        response = client.post('/api/auth/login', json={
            'email': 'test@example.com'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
    
    def test_register_with_wallet_address(self, client):
        """Test registration with wallet address"""
        response = client.post('/api/auth/register', json={
            'username': 'walletuser',
            'email': 'wallet@example.com',
            'password': STRONG_PASSWORD,
            'wallet_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f8dBe0'
        })
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['user']['wallet_address'] is not None
    
    def test_register_invalid_wallet_address(self, client):
        """Test registration with invalid wallet address"""
        response = client.post('/api/auth/register', json={
            'username': 'badwallet',
            'email': 'badwallet@example.com',
            'password': STRONG_PASSWORD,
            'wallet_address': 'invalid-address'
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False


class TestAuthProtection:
    """Test authentication protection"""
    
    def test_protected_route_without_token(self, client):
        """Test accessing protected route without token"""
        response = client.get('/api/transfer-agent/tokens')
        
        assert response.status_code == 401
    
    def test_protected_route_with_invalid_token(self, client):
        """Test accessing protected route with invalid token"""
        response = client.get('/api/transfer-agent/tokens', headers={
            'Authorization': 'Bearer invalid-token'
        })
        
        assert response.status_code == 401
    
    def test_protected_route_with_valid_token(self, client, auth_headers):
        """Test accessing protected route with valid token"""
        response = client.get('/api/transfer-agent/tokens', headers=auth_headers)
        
        assert response.status_code == 200
