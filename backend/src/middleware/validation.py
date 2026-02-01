"""
Input Validation Middleware for RWA-Studio
Author: Sowad Al-Mughni

Provides request validation using Pydantic-like schemas
for type safety and input sanitization.
"""

from flask import request, jsonify
from functools import wraps
import re
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field


class ValidationError(Exception):
    """Validation error with field information"""
    
    def __init__(self, message: str, field: str = None, errors: List[Dict] = None):
        super().__init__(message)
        self.message = message
        self.field = field
        self.errors = errors or []
    
    def to_dict(self):
        return {
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': self.message,
                'field': self.field,
                'errors': self.errors
            }
        }


# ==========================================
# VALIDATION HELPERS
# ==========================================

def is_valid_email(email: str) -> bool:
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_ethereum_address(address: str) -> bool:
    """Validate Ethereum address format"""
    if not address:
        return False
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def is_valid_tx_hash(tx_hash: str) -> bool:
    """Validate Ethereum transaction hash format"""
    if not tx_hash:
        return False
    pattern = r'^0x[a-fA-F0-9]{64}$'
    return bool(re.match(pattern, tx_hash))


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """Sanitize string input"""
    if not isinstance(value, str):
        return str(value)
    # Strip whitespace and limit length
    return value.strip()[:max_length]


def sanitize_html(value: str) -> str:
    """Remove potentially dangerous HTML/script content"""
    if not isinstance(value, str):
        return str(value)
    # Remove script tags and event handlers
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r'on\w+\s*=', '', value, flags=re.IGNORECASE)
    return value


# ==========================================
# SCHEMA DEFINITIONS
# ==========================================

@dataclass
class FieldSchema:
    """Schema definition for a single field"""
    name: str
    required: bool = True
    field_type: type = str
    min_length: int = None
    max_length: int = None
    min_value: int = None
    max_value: int = None
    pattern: str = None
    validator: callable = None
    sanitizer: callable = None
    default: Any = None
    choices: List[Any] = None


@dataclass
class RequestSchema:
    """Schema definition for request validation"""
    fields: List[FieldSchema] = field(default_factory=list)
    
    def validate(self, data: Dict) -> Dict:
        """Validate data against schema"""
        errors = []
        validated_data = {}
        
        for field_schema in self.fields:
            field_name = field_schema.name
            value = data.get(field_name)
            
            # Check required
            if field_schema.required and value is None:
                if field_schema.default is not None:
                    value = field_schema.default
                else:
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} is required'
                    })
                    continue
            
            # Skip if not required and not provided
            if value is None:
                if field_schema.default is not None:
                    validated_data[field_name] = field_schema.default
                continue
            
            # Type validation
            if field_schema.field_type == str:
                if not isinstance(value, str):
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} must be a string'
                    })
                    continue
                
                # Apply sanitizer if provided
                if field_schema.sanitizer:
                    value = field_schema.sanitizer(value)
                else:
                    value = sanitize_string(value)
                
                # Length validation
                if field_schema.min_length and len(value) < field_schema.min_length:
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} must be at least {field_schema.min_length} characters'
                    })
                    continue
                
                if field_schema.max_length and len(value) > field_schema.max_length:
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} must be at most {field_schema.max_length} characters'
                    })
                    continue
                
                # Pattern validation
                if field_schema.pattern and not re.match(field_schema.pattern, value):
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} has invalid format'
                    })
                    continue
            
            elif field_schema.field_type == int:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} must be an integer'
                    })
                    continue
                
                if field_schema.min_value is not None and value < field_schema.min_value:
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} must be at least {field_schema.min_value}'
                    })
                    continue
                
                if field_schema.max_value is not None and value > field_schema.max_value:
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} must be at most {field_schema.max_value}'
                    })
                    continue
            
            elif field_schema.field_type == bool:
                if isinstance(value, bool):
                    pass
                elif isinstance(value, str):
                    value = value.lower() in ('true', '1', 'yes')
                else:
                    value = bool(value)
            
            elif field_schema.field_type == list:
                if not isinstance(value, list):
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} must be a list'
                    })
                    continue
            
            # Choices validation
            if field_schema.choices and value not in field_schema.choices:
                errors.append({
                    'field': field_name,
                    'message': f'{field_name} must be one of: {", ".join(map(str, field_schema.choices))}'
                })
                continue
            
            # Custom validator
            if field_schema.validator:
                try:
                    if not field_schema.validator(value):
                        errors.append({
                            'field': field_name,
                            'message': f'{field_name} failed validation'
                        })
                        continue
                except Exception as e:
                    errors.append({
                        'field': field_name,
                        'message': f'{field_name} validation error: {str(e)}'
                    })
                    continue
            
            validated_data[field_name] = value
        
        if errors:
            raise ValidationError(
                message='Validation failed',
                errors=errors
            )
        
        return validated_data


# ==========================================
# COMMON SCHEMAS
# ==========================================

# User registration schema
REGISTER_SCHEMA = RequestSchema(fields=[
    FieldSchema(name='username', min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$'),
    FieldSchema(name='email', validator=is_valid_email),
    FieldSchema(name='password', min_length=8, max_length=128),
    FieldSchema(name='wallet_address', required=False, validator=is_valid_ethereum_address),
    FieldSchema(name='role', required=False, choices=['user', 'admin', 'transfer_agent'], default='user'),
])

# Login schema
LOGIN_SCHEMA = RequestSchema(fields=[
    FieldSchema(name='email', required=False),
    FieldSchema(name='username', required=False),
    FieldSchema(name='password'),
])

# Wallet login schema
WALLET_LOGIN_SCHEMA = RequestSchema(fields=[
    FieldSchema(name='wallet_address', validator=is_valid_ethereum_address),
    FieldSchema(name='signature'),
    FieldSchema(name='message'),
])

# Token registration schema
TOKEN_REGISTER_SCHEMA = RequestSchema(fields=[
    FieldSchema(name='token_address', validator=is_valid_ethereum_address),
    FieldSchema(name='token_name', min_length=1, max_length=100),
    FieldSchema(name='token_symbol', min_length=1, max_length=10),
    FieldSchema(name='asset_type', choices=['real_estate', 'equity', 'debt', 'commodity', 'art', 'other']),
    FieldSchema(name='regulatory_framework', choices=['reg_d', 'reg_s', 'reg_a', 'reg_cf', 'mifid_ii', 'other']),
    FieldSchema(name='jurisdiction', min_length=2, max_length=100),
    FieldSchema(name='max_supply', field_type=int, min_value=1),
    FieldSchema(name='deployer_address', validator=is_valid_ethereum_address),
    FieldSchema(name='compliance_address', validator=is_valid_ethereum_address),
    FieldSchema(name='identity_registry_address', validator=is_valid_ethereum_address),
    FieldSchema(name='deployment_tx_hash', required=False, validator=is_valid_tx_hash),
    FieldSchema(name='description', required=False, max_length=2000, sanitizer=sanitize_html),
    FieldSchema(name='document_hash', required=False, max_length=66),
])

# Address verification schema
ADDRESS_VERIFY_SCHEMA = RequestSchema(fields=[
    FieldSchema(name='investor_address', validator=is_valid_ethereum_address),
    FieldSchema(name='verification_level', choices=['basic', 'accredited', 'institutional']),
    FieldSchema(name='country_code', min_length=2, max_length=2),
    FieldSchema(name='expiration_days', required=False, field_type=int, min_value=1, max_value=3650, default=365),
])

# Pagination schema
PAGINATION_SCHEMA = RequestSchema(fields=[
    FieldSchema(name='page', required=False, field_type=int, min_value=1, default=1),
    FieldSchema(name='per_page', required=False, field_type=int, min_value=1, max_value=100, default=20),
])


# ==========================================
# VALIDATION DECORATOR
# ==========================================

def validate_request(schema: RequestSchema):
    """Decorator to validate request body against schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = request.get_json() or {}
                validated_data = schema.validate(data)
                # Pass validated data to the route function
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify(e.to_dict()), 400
        return decorated_function
    return decorator


def validate_query_params(schema: RequestSchema):
    """Decorator to validate query parameters against schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = dict(request.args)
                validated_data = schema.validate(data)
                kwargs['validated_params'] = validated_data
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify(e.to_dict()), 400
        return decorated_function
    return decorator
