"""
Transfer Agent Route Tests for RWA-Studio
"""

import pytest


class TestTokenEndpoints:
    """Test token management endpoints"""
    
    def test_get_tokens_empty(self, client, auth_headers):
        """Test getting tokens when none exist"""
        response = client.get('/api/transfer-agent/tokens', headers=auth_headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert 'tokens' in data['data']
        assert isinstance(data['data']['tokens'], list)
    
    def test_get_tokens_pagination(self, client, auth_headers):
        """Test tokens pagination parameters"""
        response = client.get(
            '/api/transfer-agent/tokens?page=1&per_page=10',
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert 'pagination' in data['data']
        assert data['data']['pagination']['page'] == 1
        assert data['data']['pagination']['per_page'] == 10
    
    def test_register_token_unauthorized(self, client, auth_headers):
        """Test registering token without transfer_agent role"""
        response = client.post('/api/transfer-agent/tokens', 
            json={
                'token_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f8dBe0',
                'token_name': 'Test Token',
                'token_symbol': 'TST',
                'asset_type': 'real_estate',
                'regulatory_framework': 'reg_d',
                'jurisdiction': 'US',
                'max_supply': 1000000,
                'deployer_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f8dBe0',
                'compliance_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f8dBe1',
                'identity_registry_address': '0x742d35Cc6634C0532925a3b844Bc9e7595f8dBe2'
            },
            headers=auth_headers
        )
        
        # Should fail due to missing transfer_agent role
        assert response.status_code in [401, 403]
    
    def test_get_token_not_found(self, client, auth_headers):
        """Test getting non-existent token"""
        response = client.get(
            '/api/transfer-agent/tokens/0x0000000000000000000000000000000000000000',
            headers=auth_headers
        )
        
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False


class TestVerificationEndpoints:
    """Test address verification endpoints"""
    
    def test_get_verified_addresses_token_not_found(self, client, auth_headers):
        """Test getting verified addresses for non-existent token"""
        response = client.get(
            '/api/transfer-agent/tokens/0x0000000000000000000000000000000000000000/verified-addresses',
            headers=auth_headers
        )
        
        assert response.status_code == 404


class TestComplianceEndpoints:
    """Test compliance event endpoints"""
    
    def test_compliance_endpoints_protected(self, client):
        """Test that compliance endpoints are protected"""
        endpoints = [
            '/api/transfer-agent/tokens',
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code == 401, f"Endpoint {endpoint} should be protected"
    
    def test_dashboard_overview_accessible(self, client):
        """Test that dashboard overview is accessible without auth (public stats)"""
        response = client.get('/api/transfer-agent/dashboard/overview')
        # Dashboard overview is intentionally public for transparency
        assert response.status_code == 200
