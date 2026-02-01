"""
Middleware Tests for RWA-Studio
"""

import pytest
from src.middleware.validation import (
    is_valid_email, is_valid_ethereum_address, is_valid_tx_hash,
    sanitize_string, REGISTER_SCHEMA, LOGIN_SCHEMA
)
from src.middleware.error_handler import (
    APIError, ValidationError, AuthenticationError, NotFoundError
)


class TestValidationHelpers:
    """Test validation helper functions"""
    
    def test_valid_email(self):
        """Test valid email addresses"""
        valid_emails = [
            'test@example.com',
            'user.name@domain.org',
            'user+tag@example.co.uk',
            'test123@test.io'
        ]
        for email in valid_emails:
            assert is_valid_email(email), f"{email} should be valid"
    
    def test_invalid_email(self):
        """Test invalid email addresses"""
        invalid_emails = [
            'invalid',
            '@example.com',
            'test@',
            'test@.com',
            '',
            None
        ]
        for email in invalid_emails:
            assert not is_valid_email(email), f"{email} should be invalid"
    
    def test_valid_ethereum_address(self):
        """Test valid Ethereum addresses"""
        valid_addresses = [
            '0x742d35Cc6634C0532925a3b844Bc9e7595f8dBe0',
            '0x0000000000000000000000000000000000000000',
            '0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF'
        ]
        for addr in valid_addresses:
            assert is_valid_ethereum_address(addr), f"{addr} should be valid"
    
    def test_invalid_ethereum_address(self):
        """Test invalid Ethereum addresses"""
        invalid_addresses = [
            '0x123',  # Too short
            '742d35Cc6634C0532925a3b844Bc9e7595f8dBe0',  # Missing 0x
            '0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG',  # Invalid chars
            '',
            None
        ]
        for addr in invalid_addresses:
            assert not is_valid_ethereum_address(addr), f"{addr} should be invalid"
    
    def test_valid_tx_hash(self):
        """Test valid transaction hashes"""
        valid_hashes = [
            '0x' + 'a' * 64,
            '0x' + 'F' * 64,
            '0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef'
        ]
        for hash in valid_hashes:
            assert is_valid_tx_hash(hash), f"{hash} should be valid"
    
    def test_invalid_tx_hash(self):
        """Test invalid transaction hashes"""
        invalid_hashes = [
            '0x123',  # Too short
            '0x' + 'g' * 64,  # Invalid chars
            'abcd' * 16,  # Missing 0x
        ]
        for hash in invalid_hashes:
            assert not is_valid_tx_hash(hash), f"{hash} should be invalid"
    
    def test_sanitize_string(self):
        """Test string sanitization"""
        # Test whitespace stripping
        assert sanitize_string('  hello  ') == 'hello'
        
        # Test length limiting
        long_string = 'a' * 2000
        assert len(sanitize_string(long_string)) == 1000
        
        # Test non-string input
        assert sanitize_string(123) == '123'


class TestSchemaValidation:
    """Test request schema validation"""
    
    def test_register_schema_valid(self):
        """Test valid registration data"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        }
        validated = REGISTER_SCHEMA.validate(data)
        assert validated['username'] == 'testuser'
        assert validated['email'] == 'test@example.com'
    
    def test_register_schema_missing_field(self):
        """Test registration with missing required field"""
        data = {
            'username': 'testuser',
            'email': 'test@example.com'
            # missing password
        }
        with pytest.raises(Exception):  # ValidationError
            REGISTER_SCHEMA.validate(data)
    
    def test_register_schema_invalid_email(self):
        """Test registration with invalid email"""
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'password123'
        }
        with pytest.raises(Exception):
            REGISTER_SCHEMA.validate(data)
    
    def test_login_schema_valid(self):
        """Test valid login data"""
        data = {
            'email': 'test@example.com',
            'password': 'password123'
        }
        validated = LOGIN_SCHEMA.validate(data)
        assert validated['email'] == 'test@example.com'


class TestErrorClasses:
    """Test custom error classes"""
    
    def test_api_error(self):
        """Test APIError class"""
        error = APIError('Test error', status_code=400, error_code='TEST_ERROR')
        assert error.message == 'Test error'
        assert error.status_code == 400
        assert error.error_code == 'TEST_ERROR'
        
        error_dict = error.to_dict()
        assert error_dict['success'] is False
        assert error_dict['error']['code'] == 'TEST_ERROR'
    
    def test_validation_error(self):
        """Test ValidationError class"""
        error = ValidationError('Invalid input', field='email')
        assert error.status_code == 400
        assert error.error_code == 'VALIDATION_ERROR'
        assert 'email' in str(error.to_dict())
    
    def test_authentication_error(self):
        """Test AuthenticationError class"""
        error = AuthenticationError()
        assert error.status_code == 401
        assert error.error_code == 'AUTHENTICATION_ERROR'
    
    def test_not_found_error(self):
        """Test NotFoundError class"""
        error = NotFoundError('Token', '0x123')
        assert error.status_code == 404
        assert 'Token not found' in error.message
