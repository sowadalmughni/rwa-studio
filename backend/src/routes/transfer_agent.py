"""
Transfer Agent Console API Routes for RWA-Studio
Author: Sowad Al-Mughni

Security Features (OWASP):
- Rate limiting on all endpoints
- Schema-based input validation
- Role-based access control (transfer_agent role required for writes)
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from src.models.token import (
    db, TokenDeployment, VerifiedAddress, ComplianceEvent, 
    TransferAgentUser, TokenMetrics
)
from src.middleware.auth import transfer_agent_required, admin_required
from src.middleware.rate_limit import rate_limit_read, rate_limit_write, rate_limit_public
from src.middleware.validation import (
    validate_request, validate_query_params, PAGINATION_SCHEMA,
    TOKEN_REGISTER_SCHEMA, ADDRESS_VERIFY_SCHEMA, COMPLIANCE_EVENT_SCHEMA,
    is_valid_ethereum_address, sanitize_string, sanitize_html
)
import json

transfer_agent_bp = Blueprint('transfer_agent', __name__)

# Token Management Endpoints

@transfer_agent_bp.route('/tokens', methods=['GET'])
@jwt_required()
@rate_limit_read
@validate_query_params(PAGINATION_SCHEMA)
def get_tokens(validated_params):
    """Get all token deployments with pagination and filtering"""
    try:
        page = validated_params.get('page', 1)
        per_page = validated_params.get('per_page', 20)
        
        # Get optional filters from query params (validated separately)
        asset_type = request.args.get('asset_type')
        regulatory_framework = request.args.get('regulatory_framework')
        is_active = request.args.get('is_active', type=bool)
        
        # Validate filter values if provided
        valid_asset_types = ['real_estate', 'equity', 'debt', 'commodity', 'art', 'other']
        valid_frameworks = ['reg_d', 'reg_s', 'reg_a', 'reg_cf', 'mifid_ii', 'other']
        
        if asset_type and asset_type not in valid_asset_types:
            return jsonify({'success': False, 'error': f'Invalid asset_type. Must be one of: {valid_asset_types}'}), 400
        
        if regulatory_framework and regulatory_framework not in valid_frameworks:
            return jsonify({'success': False, 'error': f'Invalid regulatory_framework. Must be one of: {valid_frameworks}'}), 400
        
        query = TokenDeployment.query
        
        # Apply filters
        if asset_type:
            query = query.filter(TokenDeployment.asset_type == asset_type)
        if regulatory_framework:
            query = query.filter(TokenDeployment.regulatory_framework == regulatory_framework)
        if is_active is not None:
            query = query.filter(TokenDeployment.is_active == is_active)
        
        # Order by deployment date (newest first)
        query = query.order_by(desc(TokenDeployment.deployment_date))
        
        # Paginate
        tokens = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'tokens': [token.to_dict() for token in tokens.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': tokens.total,
                    'pages': tokens.pages,
                    'has_next': tokens.has_next,
                    'has_prev': tokens.has_prev
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch tokens'}), 500

@transfer_agent_bp.route('/tokens/<token_address>', methods=['GET'])
@jwt_required()
@rate_limit_read
def get_token_details(token_address):
    """Get detailed information about a specific token"""
    try:
        # Validate token address format
        if not is_valid_ethereum_address(token_address):
            return jsonify({'success': False, 'error': 'Invalid token address format'}), 400
        
        token = TokenDeployment.query.filter_by(token_address=token_address.lower()).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        # Get recent compliance events
        recent_events = ComplianceEvent.query.filter_by(
            token_deployment_id=token.id
        ).order_by(desc(ComplianceEvent.timestamp)).limit(10).all()
        
        # Get verification statistics
        verification_stats = db.session.query(
            VerifiedAddress.verification_level,
            func.count(VerifiedAddress.id).label('count')
        ).filter_by(
            token_deployment_id=token.id,
            is_active=True
        ).group_by(VerifiedAddress.verification_level).all()
        
        # Get latest metrics
        latest_metrics = TokenMetrics.query.filter_by(
            token_deployment_id=token.id
        ).order_by(desc(TokenMetrics.metric_date)).first()
        
        return jsonify({
            'success': True,
            'data': {
                'token': token.to_dict(),
                'recent_events': [event.to_dict() for event in recent_events],
                'verification_stats': [
                    {'level': stat[0], 'count': stat[1]} for stat in verification_stats
                ],
                'latest_metrics': latest_metrics.to_dict() if latest_metrics else None
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch token details'}), 500

@transfer_agent_bp.route('/tokens', methods=['POST'])
@jwt_required()
@transfer_agent_required()
@rate_limit_write
@validate_request(TOKEN_REGISTER_SCHEMA)
def register_token(validated_data):
    """
    Register a new token deployment.
    
    Requires: transfer_agent role
    Rate limit: 30 requests/minute
    """
    try:
        token_address = validated_data['token_address'].lower()
        
        # Check if token already exists
        existing_token = TokenDeployment.query.filter_by(
            token_address=token_address
        ).first()
        
        if existing_token:
            return jsonify({'success': False, 'error': 'Token already registered'}), 409
        
        # Create new token deployment record
        token = TokenDeployment(
            token_address=token_address,
            token_name=validated_data['token_name'],
            token_symbol=validated_data['token_symbol'].upper(),
            asset_type=validated_data['asset_type'],
            regulatory_framework=validated_data['regulatory_framework'],
            jurisdiction=validated_data['jurisdiction'],
            max_supply=validated_data['max_supply'],
            deployer_address=validated_data['deployer_address'].lower(),
            compliance_address=validated_data['compliance_address'].lower(),
            identity_registry_address=validated_data['identity_registry_address'].lower(),
            deployment_tx_hash=validated_data.get('deployment_tx_hash'),
            description=validated_data.get('description'),  # Already sanitized by schema
            document_hash=validated_data.get('document_hash')
        )
        
        db.session.add(token)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'token': token.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to register token'}), 500

# Identity Verification Endpoints

@transfer_agent_bp.route('/tokens/<token_address>/verified-addresses', methods=['GET'])
@jwt_required()
@rate_limit_read
@validate_query_params(PAGINATION_SCHEMA)
def get_verified_addresses(token_address, validated_params):
    """Get verified addresses for a token"""
    try:
        # Validate token address
        if not is_valid_ethereum_address(token_address):
            return jsonify({'success': False, 'error': 'Invalid token address format'}), 400
        
        token = TokenDeployment.query.filter_by(token_address=token_address.lower()).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        page = validated_params.get('page', 1)
        per_page = min(validated_params.get('per_page', 50), 100)  # Cap at 100
        
        # Get optional filters
        verification_level = request.args.get('verification_level')
        is_active = request.args.get('is_active', type=bool)
        
        # Validate verification_level
        valid_levels = ['basic', 'accredited', 'institutional']
        if verification_level and verification_level not in valid_levels:
            return jsonify({'success': False, 'error': f'Invalid verification_level. Must be one of: {valid_levels}'}), 400
        
        query = VerifiedAddress.query.filter_by(token_deployment_id=token.id)
        
        # Apply filters
        if verification_level:
            query = query.filter(VerifiedAddress.verification_level == verification_level)
        if is_active is not None:
            query = query.filter(VerifiedAddress.is_active == is_active)
        
        # Order by verification date (newest first)
        query = query.order_by(desc(VerifiedAddress.verification_date))
        
        # Paginate
        addresses = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'addresses': [addr.to_dict() for addr in addresses.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': addresses.total,
                    'pages': addresses.pages,
                    'has_next': addresses.has_next,
                    'has_prev': addresses.has_prev
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch verified addresses'}), 500

@transfer_agent_bp.route('/tokens/<token_address>/verified-addresses', methods=['POST'])
@jwt_required()
@transfer_agent_required()
@rate_limit_write
@validate_request(ADDRESS_VERIFY_SCHEMA)
def add_verified_address(token_address, validated_data):
    """
    Add a verified address to a token.
    
    Requires: transfer_agent role
    Rate limit: 30 requests/minute
    """
    try:
        # Validate token address
        if not is_valid_ethereum_address(token_address):
            return jsonify({'success': False, 'error': 'Invalid token address format'}), 400
        
        token = TokenDeployment.query.filter_by(token_address=token_address.lower()).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        investor_address = validated_data['address'].lower()
        
        # Check if address already verified for this token
        existing_address = VerifiedAddress.query.filter_by(
            token_deployment_id=token.id,
            address=investor_address
        ).first()
        
        if existing_address:
            return jsonify({'success': False, 'error': 'Address already verified for this token'}), 409
        
        # Parse expiration date
        try:
            expiration_date = datetime.fromisoformat(
                validated_data['expiration_date'].replace('Z', '+00:00')
            )
        except (ValueError, AttributeError):
            return jsonify({'success': False, 'error': 'Invalid expiration_date format. Use ISO 8601.'}), 400
        
        # Create verified address record
        verified_address = VerifiedAddress(
            token_deployment_id=token.id,
            address=investor_address,
            verification_level=validated_data['verification_level'],
            jurisdiction=validated_data['jurisdiction'],
            expiration_date=expiration_date,
            identity_hash=validated_data['identity_hash'],
            kyc_provider=validated_data.get('kyc_provider'),
            notes=validated_data.get('notes')  # Already sanitized by schema
        )
        
        db.session.add(verified_address)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'verified_address': verified_address.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to add verified address'}), 500

@transfer_agent_bp.route('/verified-addresses/<int:address_id>', methods=['PUT'])
@jwt_required()
@transfer_agent_required()
@rate_limit_write
def update_verified_address(address_id):
    """
    Update a verified address.
    
    Requires: transfer_agent role
    Rate limit: 30 requests/minute
    """
    try:
        verified_address = VerifiedAddress.query.get(address_id)
        if not verified_address:
            return jsonify({'success': False, 'error': 'Verified address not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        # Validate and update allowed fields
        valid_levels = ['basic', 'accredited', 'institutional']
        
        if 'verification_level' in data:
            if data['verification_level'] not in valid_levels:
                return jsonify({'success': False, 'error': f'Invalid verification_level. Must be one of: {valid_levels}'}), 400
            verified_address.verification_level = data['verification_level']
        
        if 'jurisdiction' in data:
            verified_address.jurisdiction = sanitize_string(data['jurisdiction'], max_length=100)
        
        if 'expiration_date' in data:
            try:
                verified_address.expiration_date = datetime.fromisoformat(
                    data['expiration_date'].replace('Z', '+00:00')
                )
            except (ValueError, AttributeError):
                return jsonify({'success': False, 'error': 'Invalid expiration_date format'}), 400
        
        if 'kyc_provider' in data:
            verified_address.kyc_provider = sanitize_string(data['kyc_provider'], max_length=100)
        
        if 'is_active' in data:
            verified_address.is_active = bool(data['is_active'])
        
        if 'notes' in data:
            verified_address.notes = sanitize_html(sanitize_string(data['notes'], max_length=2000))
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'verified_address': verified_address.to_dict()}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to update verified address'}), 500

# Compliance Monitoring Endpoints

@transfer_agent_bp.route('/tokens/<token_address>/compliance-events', methods=['GET'])
@rate_limit_public
@validate_query_params(PAGINATION_SCHEMA)
def get_compliance_events(token_address, validated_params):
    """Get compliance events for a token (public endpoint)"""
    try:
        # Validate token address
        if not is_valid_ethereum_address(token_address):
            return jsonify({'success': False, 'error': 'Invalid token address format'}), 400
        
        token = TokenDeployment.query.filter_by(token_address=token_address.lower()).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        page = validated_params.get('page', 1)
        per_page = min(validated_params.get('per_page', 50), 100)
        
        # Get optional filters
        event_type = request.args.get('event_type')
        severity = request.args.get('severity')
        resolved = request.args.get('resolved', type=bool)
        
        # Validate filter values
        valid_event_types = ['transfer_blocked', 'compliance_check', 'verification_expired', 'limit_exceeded', 'jurisdiction_violation']
        valid_severities = ['info', 'warning', 'critical']
        
        if event_type and event_type not in valid_event_types:
            return jsonify({'success': False, 'error': f'Invalid event_type. Must be one of: {valid_event_types}'}), 400
        
        if severity and severity not in valid_severities:
            return jsonify({'success': False, 'error': f'Invalid severity. Must be one of: {valid_severities}'}), 400
        
        query = ComplianceEvent.query.filter_by(token_deployment_id=token.id)
        
        # Apply filters
        if event_type:
            query = query.filter(ComplianceEvent.event_type == event_type)
        if severity:
            query = query.filter(ComplianceEvent.severity == severity)
        if resolved is not None:
            query = query.filter(ComplianceEvent.resolved == resolved)
        
        # Order by timestamp (newest first)
        query = query.order_by(desc(ComplianceEvent.timestamp))
        
        # Paginate
        events = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'data': {
                'events': [event.to_dict() for event in events.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': events.total,
                    'pages': events.pages,
                    'has_next': events.has_next,
                    'has_prev': events.has_prev
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch compliance events'}), 500

@transfer_agent_bp.route('/compliance-events', methods=['POST'])
@jwt_required()
@transfer_agent_required()
@rate_limit_write
@validate_request(COMPLIANCE_EVENT_SCHEMA)
def log_compliance_event(validated_data):
    """
    Log a new compliance event.
    
    Requires: transfer_agent role
    Rate limit: 30 requests/minute
    """
    try:
        # Find token
        token = TokenDeployment.query.filter_by(
            token_address=validated_data['token_address'].lower()
        ).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        # Create compliance event
        event = ComplianceEvent(
            token_deployment_id=token.id,
            event_type=validated_data['event_type'],
            from_address=validated_data.get('from_address', '').lower() if validated_data.get('from_address') else None,
            to_address=validated_data.get('to_address', '').lower() if validated_data.get('to_address') else None,
            amount=validated_data.get('amount'),
            reason=validated_data['reason'],
            transaction_hash=validated_data.get('transaction_hash'),
            block_number=validated_data.get('block_number'),
            severity=validated_data.get('severity', 'info'),
            event_metadata=json.dumps(validated_data.get('metadata')) if validated_data.get('metadata') else None
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'event': event.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to log compliance event'}), 500

@transfer_agent_bp.route('/compliance-events/<int:event_id>/resolve', methods=['PUT'])
@jwt_required()
@transfer_agent_required()
@rate_limit_write
def resolve_compliance_event(event_id):
    """
    Mark a compliance event as resolved.
    
    Requires: transfer_agent role
    Rate limit: 30 requests/minute
    """
    try:
        event = ComplianceEvent.query.get(event_id)
        if not event:
            return jsonify({'success': False, 'error': 'Compliance event not found'}), 404
        
        data = request.get_json() or {}
        
        event.resolved = True
        event.resolved_by = sanitize_string(data.get('resolved_by', ''), max_length=100) or None
        event.resolved_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'event': event.to_dict()}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': 'Failed to resolve compliance event'}), 500

# Analytics and Reporting Endpoints

@transfer_agent_bp.route('/tokens/<token_address>/metrics', methods=['GET'])
@rate_limit_public
def get_token_metrics(token_address):
    """Get metrics and analytics for a token (public endpoint)"""
    try:
        # Validate token address
        if not is_valid_ethereum_address(token_address):
            return jsonify({'success': False, 'error': 'Invalid token address format'}), 400
        
        token = TokenDeployment.query.filter_by(token_address=token_address.lower()).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        # Validate and constrain days parameter
        days = request.args.get('days', 30, type=int)
        days = max(1, min(days, 365))  # Constrain to 1-365 days
        
        start_date = datetime.utcnow().date() - timedelta(days=days)
        
        # Get metrics for the specified period
        metrics = TokenMetrics.query.filter(
            TokenMetrics.token_deployment_id == token.id,
            TokenMetrics.metric_date >= start_date
        ).order_by(TokenMetrics.metric_date).all()
        
        # Get summary statistics
        total_verified = VerifiedAddress.query.filter_by(
            token_deployment_id=token.id,
            is_active=True
        ).count()
        
        total_events = ComplianceEvent.query.filter_by(
            token_deployment_id=token.id
        ).count()
        
        unresolved_events = ComplianceEvent.query.filter_by(
            token_deployment_id=token.id,
            resolved=False
        ).count()
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': [metric.to_dict() for metric in metrics],
                'summary': {
                    'total_verified_addresses': total_verified,
                    'total_compliance_events': total_events,
                    'unresolved_events': unresolved_events,
                    'compliance_rate': (1 - (unresolved_events / max(total_events, 1))) * 100
                }
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch token metrics'}), 500

@transfer_agent_bp.route('/dashboard/overview', methods=['GET'])
@rate_limit_public
def get_dashboard_overview():
    """Get overview data for the transfer agent dashboard (public endpoint)"""
    try:
        # Get total counts
        total_tokens = TokenDeployment.query.filter_by(is_active=True).count()
        total_verified_addresses = VerifiedAddress.query.filter_by(is_active=True).count()
        total_compliance_events = ComplianceEvent.query.count()
        unresolved_events = ComplianceEvent.query.filter_by(resolved=False).count()
        
        # Get recent activity
        recent_tokens = TokenDeployment.query.order_by(
            desc(TokenDeployment.deployment_date)
        ).limit(5).all()
        
        recent_events = ComplianceEvent.query.order_by(
            desc(ComplianceEvent.timestamp)
        ).limit(10).all()
        
        # Get asset type distribution
        asset_distribution = db.session.query(
            TokenDeployment.asset_type,
            func.count(TokenDeployment.id).label('count')
        ).filter_by(is_active=True).group_by(TokenDeployment.asset_type).all()
        
        # Get regulatory framework distribution
        regulatory_distribution = db.session.query(
            TokenDeployment.regulatory_framework,
            func.count(TokenDeployment.id).label('count')
        ).filter_by(is_active=True).group_by(TokenDeployment.regulatory_framework).all()
        
        return jsonify({
            'success': True,
            'data': {
                'summary': {
                    'total_tokens': total_tokens,
                    'total_verified_addresses': total_verified_addresses,
                    'total_compliance_events': total_compliance_events,
                    'unresolved_events': unresolved_events,
                    'compliance_rate': (1 - (unresolved_events / max(total_compliance_events, 1))) * 100
                },
                'recent_tokens': [token.to_dict() for token in recent_tokens],
                'recent_events': [event.to_dict() for event in recent_events],
                'asset_distribution': [
                    {'asset_type': dist[0], 'count': dist[1]} for dist in asset_distribution
                ],
                'regulatory_distribution': [
                    {'framework': dist[0], 'count': dist[1]} for dist in regulatory_distribution
                ]
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': 'Failed to fetch dashboard overview'}), 500

# Health check endpoint
@transfer_agent_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the transfer agent console"""
    return jsonify({
        'success': True,
        'message': 'Transfer Agent Console API is running',
        'timestamp': datetime.utcnow().isoformat()
    })

