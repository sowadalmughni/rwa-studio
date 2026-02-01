"""
KYC Routes for RWA-Studio
Author: Sowad Al-Mughni

KYC Provider Integration API Endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import structlog

from src.models.user import db, User
from src.models.kyc import KYCVerification
from src.services.kyc import get_kyc_service, ApplicantData, KYCStatus
from src.tasks.email_tasks import send_kyc_started_email
from src.tasks.kyc_tasks import process_kyc_webhook

logger = structlog.get_logger()

kyc_bp = Blueprint('kyc', __name__, url_prefix='/api/kyc')


@kyc_bp.route('/start', methods=['POST'])
@jwt_required()
def start_verification():
    """
    Start KYC verification process
    
    Request body:
    {
        "wallet_address": "0x...",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "country": "US",
        "date_of_birth": "1990-01-15"  // optional
    }
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['wallet_address', 'first_name', 'last_name', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        wallet_address = data['wallet_address'].lower()
        
        # Check for existing pending or approved verification
        existing = KYCVerification.query.filter(
            KYCVerification.wallet_address == wallet_address,
            KYCVerification.status.in_(['pending', 'in_progress', 'approved'])
        ).first()
        
        if existing:
            if existing.status == 'approved' and existing.is_valid():
                return jsonify({
                    'error': 'This wallet already has a valid verification',
                    'verification': existing.to_public_dict()
                }), 400
            elif existing.status in ['pending', 'in_progress']:
                return jsonify({
                    'error': 'Verification already in progress',
                    'verification': existing.to_public_dict()
                }), 400
        
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id) if current_user_id else None
        
        # Create applicant with KYC provider
        kyc_service = get_kyc_service()
        
        applicant_data = ApplicantData(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            wallet_address=wallet_address,
            country=data.get('country'),
            date_of_birth=data.get('date_of_birth')
        )
        
        try:
            applicant_result = kyc_service.create_applicant(applicant_data)
        except Exception as e:
            logger.error("kyc_create_applicant_failed", error=str(e), wallet=wallet_address)
            return jsonify({'error': 'Failed to create verification applicant'}), 500
        
        # Create verification record
        verification = KYCVerification(
            wallet_address=wallet_address,
            user_id=user.id if user else None,
            provider=kyc_service.provider_name,
            applicant_id=applicant_result['applicant_id'],
            status='pending',
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            country_code=data.get('country')
        )
        
        db.session.add(verification)
        db.session.commit()
        
        # Generate SDK token for frontend
        try:
            sdk_token = kyc_service.generate_sdk_token(
                applicant_result['applicant_id'],
                referrer="*/*"  # Allow all referrers - should be restricted in production
            )
        except Exception as e:
            logger.error("kyc_generate_sdk_token_failed", error=str(e))
            sdk_token = None
        
        # Send email notification (async)
        send_kyc_started_email.delay(
            data['email'],
            f"{data['first_name']} {data['last_name']}",
            {'wallet_address': wallet_address}
        )
        
        logger.info(
            "kyc_verification_started",
            wallet_address=wallet_address,
            verification_id=verification.id
        )
        
        return jsonify({
            'success': True,
            'verification_id': verification.id,
            'applicant_id': applicant_result['applicant_id'],
            'sdk_token': sdk_token,
            'status': 'pending'
        }), 201
        
    except Exception as e:
        logger.error("kyc_start_error", error=str(e))
        return jsonify({'error': 'Failed to start verification'}), 500


@kyc_bp.route('/check', methods=['POST'])
@jwt_required()
def create_check():
    """
    Create verification check after user completes SDK flow
    
    Request body:
    {
        "verification_id": 123
    }
    """
    try:
        data = request.get_json()
        verification_id = data.get('verification_id')
        
        if not verification_id:
            return jsonify({'error': 'verification_id is required'}), 400
        
        verification = KYCVerification.query.get(verification_id)
        if not verification:
            return jsonify({'error': 'Verification not found'}), 404
        
        if verification.status not in ['pending']:
            return jsonify({'error': 'Verification already in progress or completed'}), 400
        
        kyc_service = get_kyc_service()
        
        try:
            check_result = kyc_service.create_check(
                verification.applicant_id,
                check_types=['document', 'facial_similarity_photo']
            )
        except Exception as e:
            logger.error("kyc_create_check_failed", error=str(e), verification_id=verification_id)
            return jsonify({'error': 'Failed to create verification check'}), 500
        
        # Update verification record
        verification.check_id = check_result['check_id']
        verification.status = 'in_progress'
        verification.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(
            "kyc_check_created",
            verification_id=verification_id,
            check_id=check_result['check_id']
        )
        
        return jsonify({
            'success': True,
            'check_id': check_result['check_id'],
            'status': 'in_progress'
        })
        
    except Exception as e:
        logger.error("kyc_create_check_error", error=str(e))
        return jsonify({'error': 'Failed to create check'}), 500


@kyc_bp.route('/status/<wallet_address>', methods=['GET'])
def get_verification_status(wallet_address: str):
    """Get KYC verification status for a wallet address"""
    try:
        wallet_address = wallet_address.lower()
        
        # Get latest verification for this address
        verification = KYCVerification.query.filter_by(
            wallet_address=wallet_address
        ).order_by(KYCVerification.created_at.desc()).first()
        
        if not verification:
            return jsonify({
                'verified': False,
                'status': 'none',
                'message': 'No verification found for this address'
            })
        
        return jsonify({
            'verified': verification.is_valid(),
            'status': verification.status,
            'verification_level': verification.verification_level,
            'verification': verification.to_public_dict()
        })
        
    except Exception as e:
        logger.error("kyc_status_error", error=str(e), wallet=wallet_address)
        return jsonify({'error': 'Failed to get verification status'}), 500


@kyc_bp.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle KYC provider webhooks
    
    This endpoint receives webhooks from Onfido when verification status changes.
    """
    try:
        # Get raw payload for signature verification
        payload = request.get_data()
        signature = request.headers.get('X-SHA2-Signature', '')
        
        kyc_service = get_kyc_service()
        
        # Verify webhook signature
        if not kyc_service.verify_webhook(payload, signature):
            logger.warning("kyc_webhook_invalid_signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse webhook data
        data = request.get_json()
        
        # Process webhook asynchronously
        process_kyc_webhook.delay(data)
        
        logger.info("kyc_webhook_received", event_type=data.get('payload', {}).get('action'))
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error("kyc_webhook_error", error=str(e))
        return jsonify({'error': 'Webhook processing failed'}), 500


@kyc_bp.route('/verifications', methods=['GET'])
@jwt_required()
def list_verifications():
    """List all KYC verifications (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role not in ['admin', 'transfer_agent']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        # Pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status_filter = request.args.get('status')
        
        query = KYCVerification.query
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        query = query.order_by(KYCVerification.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'verifications': [v.to_dict() for v in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        })
        
    except Exception as e:
        logger.error("kyc_list_error", error=str(e))
        return jsonify({'error': 'Failed to list verifications'}), 500


@kyc_bp.route('/sdk-token/<int:verification_id>', methods=['GET'])
@jwt_required()
def get_sdk_token(verification_id: int):
    """Generate a new SDK token for an existing verification"""
    try:
        verification = KYCVerification.query.get(verification_id)
        
        if not verification:
            return jsonify({'error': 'Verification not found'}), 404
        
        if verification.status not in ['pending']:
            return jsonify({'error': 'Verification not in pending state'}), 400
        
        kyc_service = get_kyc_service()
        
        try:
            sdk_token = kyc_service.generate_sdk_token(
                verification.applicant_id,
                referrer="*/*"
            )
        except Exception as e:
            logger.error("kyc_sdk_token_error", error=str(e), verification_id=verification_id)
            return jsonify({'error': 'Failed to generate SDK token'}), 500
        
        return jsonify({
            'sdk_token': sdk_token,
            'applicant_id': verification.applicant_id
        })
        
    except Exception as e:
        logger.error("kyc_sdk_token_error", error=str(e))
        return jsonify({'error': 'Failed to get SDK token'}), 500
