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


class UnexpectedFieldsError(ValidationError):
    """Error raised when unexpected fields are present in request"""
    
    def __init__(self, unexpected_fields: List[str]):
        super().__init__(
            message='Unexpected fields in request',
            errors=[{'field': f, 'message': f'Unexpected field: {f}'} for f in unexpected_fields]
        )
        self.unexpected_fields = unexpected_fields


# ==========================================
# VALIDATION HELPERS
# ==========================================

def is_valid_email(email: str) -> bool:
    """
    Validate email format.
    
    OWASP: Email validation should be strict but not overly complex.
    Use regex for format validation, then verify via confirmation email.
    """
    if not email:
        return False
    # RFC 5322 compliant email pattern (simplified)
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        return False
    # Additional checks
    if len(email) > 254:  # Max email length per RFC
        return False
    if '..' in email:  # No consecutive dots
        return False
    return True


def is_valid_ethereum_address(address: str) -> bool:
    """Validate Ethereum address format (0x + 40 hex chars)"""
    if not address:
        return False
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))


def is_valid_tx_hash(tx_hash: str) -> bool:
    """Validate Ethereum transaction hash format (0x + 64 hex chars)"""
    if not tx_hash:
        return False
    pattern = r'^0x[a-fA-F0-9]{64}$'
    return bool(re.match(pattern, tx_hash))


def is_strong_password(password: str) -> bool:
    """
    Validate password complexity.
    
    OWASP Password Requirements (NIST SP 800-63B):
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - Not in common password list (basic check)
    
    Returns:
        bool: True if password meets complexity requirements
    """
    if not password or len(password) < 8:
        return False
    if len(password) > 128:  # Max length to prevent DoS
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~]', password):
        return False
    
    # Check against common weak passwords
    common_passwords = {
        'password', 'password1', '12345678', 'qwerty123',
        'letmein1', 'welcome1', 'admin123', 'passw0rd'
    }
    if password.lower() in common_passwords:
        return False
    
    return True


def get_password_requirements() -> str:
    """Return password requirements message for user feedback"""
    return (
        "Password must be 8-128 characters with at least one uppercase letter, "
        "one lowercase letter, one digit, and one special character (!@#$%^&*)"
    )


def sanitize_string(value: str, max_length: int = 1000) -> str:
    """
    Sanitize string input.
    
    OWASP: Input sanitization is a defense-in-depth measure.
    - Strip leading/trailing whitespace
    - Remove null bytes (injection attack vector)
    - Limit length to prevent buffer overflow / DoS
    """
    if not isinstance(value, str):
        return str(value)[:max_length]
    # Remove null bytes (security)
    value = value.replace('\x00', '')
    # Strip whitespace and limit length
    return value.strip()[:max_length]


def sanitize_html(value: str) -> str:
    """
    Remove potentially dangerous HTML/script content.
    
    OWASP: XSS Prevention - remove script tags, event handlers,
    and other potentially dangerous HTML elements.
    """
    if not isinstance(value, str):
        return str(value)
    # Remove script tags
    value = re.sub(r'<script[^>]*>.*?</script>', '', value, flags=re.IGNORECASE | re.DOTALL)
    # Remove event handlers (onclick, onerror, etc.)
    value = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', value, flags=re.IGNORECASE)
    value = re.sub(r'\s*on\w+\s*=\s*\S+', '', value, flags=re.IGNORECASE)
    # Remove javascript: URLs
    value = re.sub(r'javascript\s*:', '', value, flags=re.IGNORECASE)
    # Remove data: URLs (can contain scripts)
    value = re.sub(r'data\s*:[^,]*,', 'data:removed,', value, flags=re.IGNORECASE)
    # Remove iframe tags
    value = re.sub(r'<iframe[^>]*>.*?</iframe>', '', value, flags=re.IGNORECASE | re.DOTALL)
    # Remove object/embed tags
    value = re.sub(r'<(object|embed)[^>]*>.*?</(object|embed)>', '', value, flags=re.IGNORECASE | re.DOTALL)
    return value


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.
    
    OWASP: Path traversal prevention
    """
    if not filename:
        return ''
    # Remove path separators
    filename = filename.replace('/', '').replace('\\', '')
    # Remove null bytes
    filename = filename.replace('\x00', '')
    # Remove parent directory references
    filename = filename.replace('..', '')
    # Limit length
    return filename[:255]


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
    error_message: str = None  # Custom error message for this field
    choices: List[Any] = None


@dataclass
class RequestSchema:
    """
    Schema definition for request validation.
    
    OWASP: Implements strict input validation with:
    - Type checking
    - Length limits
    - Pattern matching
    - Rejection of unexpected fields (when strict=True)
    """
    fields: List[FieldSchema] = field(default_factory=list)
    strict: bool = True  # Reject unexpected fields by default
    
    def validate(self, data: Dict, reject_extra_fields: bool = None) -> Dict:
        """
        Validate data against schema.
        
        Args:
            data: Input data dictionary
            reject_extra_fields: Override schema's strict setting
        
        Returns:
            Dict of validated and sanitized data
        
        Raises:
            ValidationError: If validation fails
            UnexpectedFieldsError: If unexpected fields present (when strict)
        """
        errors = []
        validated_data = {}
        
        # Check for unexpected fields (OWASP: reject unknown inputs)
        should_reject_extra = reject_extra_fields if reject_extra_fields is not None else self.strict
        if should_reject_extra:
            expected_fields = {f.name for f in self.fields}
            unexpected = set(data.keys()) - expected_fields
            if unexpected:
                raise UnexpectedFieldsError(list(unexpected))
        
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
                        # Use custom error message if provided
                        error_msg = field_schema.error_message or f'{field_name} failed validation'
                        errors.append({
                            'field': field_name,
                            'message': error_msg
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

# User registration schema with strong password validation
REGISTER_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(
            name='username', 
            min_length=3, 
            max_length=50, 
            pattern=r'^[a-zA-Z0-9_]+$',
            error_message='Username must be 3-50 characters, alphanumeric and underscores only'
        ),
        FieldSchema(
            name='email', 
            max_length=254,
            validator=is_valid_email,
            error_message='Please provide a valid email address'
        ),
        FieldSchema(
            name='password', 
            min_length=8, 
            max_length=128,
            validator=is_strong_password,
            error_message=get_password_requirements()
        ),
        FieldSchema(
            name='wallet_address', 
            required=False, 
            validator=is_valid_ethereum_address,
            error_message='Invalid Ethereum address format (must be 0x followed by 40 hex characters)'
        ),
    ],
    strict=True  # Reject unexpected fields
)

# Login schema
LOGIN_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(name='email', required=False, max_length=254),
        FieldSchema(name='username', required=False, max_length=50),
        FieldSchema(name='password', max_length=128),
    ],
    strict=True
)

# Wallet login schema (with signature verification)
WALLET_LOGIN_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(
            name='wallet_address', 
            validator=is_valid_ethereum_address,
            error_message='Invalid Ethereum address format'
        ),
        FieldSchema(
            name='signature', 
            min_length=130,  # Ethereum signatures are 65 bytes = 130 hex chars + 0x
            max_length=150,
            pattern=r'^0x[a-fA-F0-9]+$',
            error_message='Invalid signature format'
        ),
        FieldSchema(
            name='message', 
            min_length=1,
            max_length=1000,
            error_message='Message is required for signature verification'
        ),
    ],
    strict=True
)

# Password change schema
PASSWORD_CHANGE_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(name='current_password', max_length=128),
        FieldSchema(
            name='new_password', 
            min_length=8, 
            max_length=128,
            validator=is_strong_password,
            error_message=get_password_requirements()
        ),
    ],
    strict=True
)

# Profile update schema
PROFILE_UPDATE_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(
            name='username', 
            required=False,
            min_length=3, 
            max_length=50, 
            pattern=r'^[a-zA-Z0-9_]+$'
        ),
        FieldSchema(
            name='email', 
            required=False,
            max_length=254,
            validator=is_valid_email
        ),
        FieldSchema(
            name='wallet_address', 
            required=False, 
            validator=is_valid_ethereum_address
        ),
    ],
    strict=True
)

# Token registration schema
TOKEN_REGISTER_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(name='token_address', validator=is_valid_ethereum_address),
        FieldSchema(name='token_name', min_length=1, max_length=100),
        FieldSchema(name='token_symbol', min_length=1, max_length=10, pattern=r'^[A-Z0-9]+$'),
        FieldSchema(name='asset_type', choices=['real_estate', 'equity', 'debt', 'commodity', 'art', 'other']),
        FieldSchema(name='regulatory_framework', choices=['reg_d', 'reg_s', 'reg_a', 'reg_cf', 'mifid_ii', 'other']),
        FieldSchema(name='jurisdiction', min_length=2, max_length=100),
        FieldSchema(name='max_supply', field_type=int, min_value=1, max_value=10**18),
        FieldSchema(name='deployer_address', validator=is_valid_ethereum_address),
        FieldSchema(name='compliance_address', validator=is_valid_ethereum_address),
        FieldSchema(name='identity_registry_address', validator=is_valid_ethereum_address),
        FieldSchema(name='deployment_tx_hash', required=False, validator=is_valid_tx_hash),
        FieldSchema(name='description', required=False, max_length=2000, sanitizer=sanitize_html),
        FieldSchema(name='document_hash', required=False, max_length=66, pattern=r'^0x[a-fA-F0-9]{64}$'),
    ],
    strict=True
)

# Address verification schema
ADDRESS_VERIFY_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(name='address', validator=is_valid_ethereum_address),
        FieldSchema(name='verification_level', choices=['basic', 'accredited', 'institutional']),
        FieldSchema(name='jurisdiction', min_length=2, max_length=100),
        FieldSchema(name='expiration_date', required=True),
        FieldSchema(name='identity_hash', min_length=1, max_length=100),
        FieldSchema(name='kyc_provider', required=False, max_length=100),
        FieldSchema(name='notes', required=False, max_length=2000, sanitizer=sanitize_html),
    ],
    strict=True
)

# Compliance event schema
COMPLIANCE_EVENT_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(name='token_address', validator=is_valid_ethereum_address),
        FieldSchema(name='event_type', choices=['transfer_blocked', 'compliance_check', 'verification_expired', 'limit_exceeded', 'jurisdiction_violation']),
        FieldSchema(name='reason', min_length=1, max_length=1000),
        FieldSchema(name='from_address', required=False, validator=is_valid_ethereum_address),
        FieldSchema(name='to_address', required=False, validator=is_valid_ethereum_address),
        FieldSchema(name='amount', required=False, field_type=int, min_value=0),
        FieldSchema(name='transaction_hash', required=False, validator=is_valid_tx_hash),
        FieldSchema(name='block_number', required=False, field_type=int, min_value=0),
        FieldSchema(name='severity', required=False, choices=['info', 'warning', 'critical'], default='info'),
        FieldSchema(name='metadata', required=False, field_type=dict),
    ],
    strict=True
)

# Pagination schema (lenient for query params)
PAGINATION_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(name='page', required=False, field_type=int, min_value=1, default=1),
        FieldSchema(name='per_page', required=False, field_type=int, min_value=1, max_value=100, default=20),
    ],
    strict=False  # Allow other query params
)

# KYC start schema
KYC_START_SCHEMA = RequestSchema(
    fields=[
        FieldSchema(name='wallet_address', validator=is_valid_ethereum_address),
        FieldSchema(name='first_name', min_length=1, max_length=100),
        FieldSchema(name='last_name', min_length=1, max_length=100),
        FieldSchema(name='email', max_length=254, validator=is_valid_email),
        FieldSchema(name='country', required=False, min_length=2, max_length=2),
        FieldSchema(name='date_of_birth', required=False, pattern=r'^\d{4}-\d{2}-\d{2}$'),
    ],
    strict=True
)


# ==========================================
# VALIDATION DECORATORS
# ==========================================

def validate_request(schema: RequestSchema, reject_extra_fields: bool = None):
    """
    Decorator to validate request body against schema.
    
    OWASP: Implements server-side input validation as primary defense.
    
    Args:
        schema: RequestSchema to validate against
        reject_extra_fields: Override schema's strict setting
    
    Usage:
        @validate_request(REGISTER_SCHEMA)
        def register(validated_data):
            # validated_data contains sanitized input
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check Content-Type
            if not request.is_json:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'INVALID_CONTENT_TYPE',
                        'message': 'Content-Type must be application/json'
                    }
                }), 415
            
            try:
                data = request.get_json(silent=True)
                if data is None:
                    return jsonify({
                        'success': False,
                        'error': {
                            'code': 'INVALID_JSON',
                            'message': 'Request body must be valid JSON'
                        }
                    }), 400
                
                validated_data = schema.validate(data, reject_extra_fields)
                # Pass validated data to the route function
                kwargs['validated_data'] = validated_data
                return f(*args, **kwargs)
            except UnexpectedFieldsError as e:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'UNEXPECTED_FIELDS',
                        'message': 'Request contains unexpected fields',
                        'fields': e.unexpected_fields
                    }
                }), 400
            except ValidationError as e:
                return jsonify(e.to_dict()), 400
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': {
                        'code': 'VALIDATION_ERROR',
                        'message': 'An error occurred during validation'
                    }
                }), 400
        return decorated_function
    return decorator


def validate_query_params(schema: RequestSchema):
    """
    Decorator to validate query parameters against schema.
    
    Note: Query params are typically more lenient (strict=False)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                data = dict(request.args)
                validated_data = schema.validate(data, reject_extra_fields=False)
                kwargs['validated_params'] = validated_data
                return f(*args, **kwargs)
            except ValidationError as e:
                return jsonify(e.to_dict()), 400
        return decorated_function
    return decorator


def validate_json_body(schema: RequestSchema):
    """Alias for validate_request for backward compatibility"""
    return validate_request(schema)
