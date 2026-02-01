"""
Transfer Agent Console API Routes for RWA-Studio
Author: Sowad Al-Mughni
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
import json

transfer_agent_bp = Blueprint('transfer_agent', __name__)

# Token Management Endpoints

@transfer_agent_bp.route('/tokens', methods=['GET'])
@jwt_required()
def get_tokens():
    """Get all token deployments with pagination and filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        asset_type = request.args.get('asset_type')
        regulatory_framework = request.args.get('regulatory_framework')
        is_active = request.args.get('is_active', type=bool)
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_agent_bp.route('/tokens/<token_address>', methods=['GET'])
@jwt_required()
def get_token_details(token_address):
    """Get detailed information about a specific token"""
    try:
        token = TokenDeployment.query.filter_by(token_address=token_address).first()
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
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_agent_bp.route('/tokens', methods=['POST'])
@jwt_required()
@transfer_agent_required()
def register_token():
    """Register a new token deployment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'token_address', 'token_name', 'token_symbol', 'asset_type',
            'regulatory_framework', 'jurisdiction', 'max_supply', 'deployer_address',
            'compliance_address', 'identity_registry_address'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Check if token already exists
        existing_token = TokenDeployment.query.filter_by(
            token_address=data['token_address']
        ).first()
        
        if existing_token:
            return jsonify({'success': False, 'error': 'Token already registered'}), 409
        
        # Create new token deployment record
        token = TokenDeployment(
            token_address=data['token_address'],
            token_name=data['token_name'],
            token_symbol=data['token_symbol'],
            asset_type=data['asset_type'],
            regulatory_framework=data['regulatory_framework'],
            jurisdiction=data['jurisdiction'],
            max_supply=data['max_supply'],
            deployer_address=data['deployer_address'],
            compliance_address=data['compliance_address'],
            identity_registry_address=data['identity_registry_address'],
            deployment_tx_hash=data.get('deployment_tx_hash'),
            description=data.get('description'),
            document_hash=data.get('document_hash')
        )
        
        db.session.add(token)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'token': token.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Identity Verification Endpoints

@transfer_agent_bp.route('/tokens/<token_address>/verified-addresses', methods=['GET'])
@jwt_required()
def get_verified_addresses(token_address):
    """Get verified addresses for a token"""
    try:
        token = TokenDeployment.query.filter_by(token_address=token_address).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        verification_level = request.args.get('verification_level')
        is_active = request.args.get('is_active', type=bool)
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_agent_bp.route('/tokens/<token_address>/verified-addresses', methods=['POST'])
@jwt_required()
@transfer_agent_required()
def add_verified_address(token_address):
    """Add a verified address to a token"""
    try:
        token = TokenDeployment.query.filter_by(token_address=token_address).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = [
            'address', 'verification_level', 'jurisdiction', 
            'expiration_date', 'identity_hash'
        ]
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Check if address already verified for this token
        existing_address = VerifiedAddress.query.filter_by(
            token_deployment_id=token.id,
            address=data['address']
        ).first()
        
        if existing_address:
            return jsonify({'success': False, 'error': 'Address already verified for this token'}), 409
        
        # Parse expiration date
        try:
            expiration_date = datetime.fromisoformat(data['expiration_date'].replace('Z', '+00:00'))
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid expiration_date format'}), 400
        
        # Create verified address record
        verified_address = VerifiedAddress(
            token_deployment_id=token.id,
            address=data['address'],
            verification_level=data['verification_level'],
            jurisdiction=data['jurisdiction'],
            expiration_date=expiration_date,
            identity_hash=data['identity_hash'],
            kyc_provider=data.get('kyc_provider'),
            notes=data.get('notes')
        )
        
        db.session.add(verified_address)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'verified_address': verified_address.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_agent_bp.route('/verified-addresses/<int:address_id>', methods=['PUT'])
@jwt_required()
@transfer_agent_required()
def update_verified_address(address_id):
    """Update a verified address"""
    try:
        verified_address = VerifiedAddress.query.get(address_id)
        if not verified_address:
            return jsonify({'success': False, 'error': 'Verified address not found'}), 404
        
        data = request.get_json()
        
        # Update allowed fields
        if 'verification_level' in data:
            verified_address.verification_level = data['verification_level']
        if 'jurisdiction' in data:
            verified_address.jurisdiction = data['jurisdiction']
        if 'expiration_date' in data:
            try:
                verified_address.expiration_date = datetime.fromisoformat(
                    data['expiration_date'].replace('Z', '+00:00')
                )
            except ValueError:
                return jsonify({'success': False, 'error': 'Invalid expiration_date format'}), 400
        if 'kyc_provider' in data:
            verified_address.kyc_provider = data['kyc_provider']
        if 'is_active' in data:
            verified_address.is_active = data['is_active']
        if 'notes' in data:
            verified_address.notes = data['notes']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'verified_address': verified_address.to_dict()}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Compliance Monitoring Endpoints

@transfer_agent_bp.route('/tokens/<token_address>/compliance-events', methods=['GET'])
def get_compliance_events(token_address):
    """Get compliance events for a token"""
    try:
        token = TokenDeployment.query.filter_by(token_address=token_address).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        event_type = request.args.get('event_type')
        severity = request.args.get('severity')
        resolved = request.args.get('resolved', type=bool)
        
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
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_agent_bp.route('/compliance-events', methods=['POST'])
@jwt_required()
@transfer_agent_required()
def log_compliance_event():
    """Log a new compliance event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['token_address', 'event_type', 'reason']
        
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing required field: {field}'}), 400
        
        # Find token
        token = TokenDeployment.query.filter_by(token_address=data['token_address']).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        # Create compliance event
        event = ComplianceEvent(
            token_deployment_id=token.id,
            event_type=data['event_type'],
            from_address=data.get('from_address'),
            to_address=data.get('to_address'),
            amount=data.get('amount'),
            reason=data['reason'],
            transaction_hash=data.get('transaction_hash'),
            block_number=data.get('block_number'),
            severity=data.get('severity', 'info'),
            event_metadata=json.dumps(data.get('metadata')) if data.get('metadata') else None
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'event': event.to_dict()}
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_agent_bp.route('/compliance-events/<int:event_id>/resolve', methods=['PUT'])
@jwt_required()
@transfer_agent_required()
def resolve_compliance_event(event_id):
    """Mark a compliance event as resolved"""
    try:
        event = ComplianceEvent.query.get(event_id)
        if not event:
            return jsonify({'success': False, 'error': 'Compliance event not found'}), 404
        
        data = request.get_json()
        
        event.resolved = True
        event.resolved_by = data.get('resolved_by')
        event.resolved_date = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {'event': event.to_dict()}
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Analytics and Reporting Endpoints

@transfer_agent_bp.route('/tokens/<token_address>/metrics', methods=['GET'])
def get_token_metrics(token_address):
    """Get metrics and analytics for a token"""
    try:
        token = TokenDeployment.query.filter_by(token_address=token_address).first()
        if not token:
            return jsonify({'success': False, 'error': 'Token not found'}), 404
        
        days = request.args.get('days', 30, type=int)
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
        return jsonify({'success': False, 'error': str(e)}), 500

@transfer_agent_bp.route('/dashboard/overview', methods=['GET'])
def get_dashboard_overview():
    """Get overview data for the transfer agent dashboard"""
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
        return jsonify({'success': False, 'error': str(e)}), 500

# Health check endpoint
@transfer_agent_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the transfer agent console"""
    return jsonify({
        'success': True,
        'message': 'Transfer Agent Console API is running',
        'timestamp': datetime.utcnow().isoformat()
    })

