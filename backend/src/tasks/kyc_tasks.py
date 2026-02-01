"""
KYC Tasks for Celery
Author: Sowad Al-Mughni

Phase 3: Async KYC Processing
"""

from .celery_app import celery_app
from typing import Dict, Any
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def process_kyc_webhook(self, webhook_data: Dict[str, Any]):
    """Process KYC webhook from provider"""
    try:
        from src.models.user import db
        from src.models.kyc import KYCVerification
        from src.services.kyc import get_kyc_service, KYCStatus
        from .email_tasks import send_kyc_complete_email, send_kyc_failed_email
        
        kyc_service = get_kyc_service()
        result = kyc_service.parse_webhook(webhook_data)
        
        if not result.provider_check_id:
            logger.warning("kyc_webhook_no_check_id", data=webhook_data)
            return False
        
        # Find the verification record
        verification = KYCVerification.query.filter_by(
            check_id=result.provider_check_id
        ).first()
        
        if not verification:
            logger.warning("kyc_verification_not_found", check_id=result.provider_check_id)
            return False
        
        # Update verification status
        verification.status = result.status.value
        verification.verification_level = result.verification_level or 1
        verification.country_code = result.country_code
        
        if result.rejection_reasons:
            verification.set_rejection_reasons(result.rejection_reasons)
        
        if result.raw_response:
            verification.set_result_data(result.raw_response)
        
        if result.completed_at:
            verification.completed_at = result.completed_at
        
        # Set expiration for approved verifications (1 year)
        if result.status == KYCStatus.APPROVED:
            verification.expires_at = datetime.utcnow() + timedelta(days=365)
        
        verification.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(
            "kyc_webhook_processed",
            check_id=result.provider_check_id,
            status=result.status.value,
            wallet_address=verification.wallet_address
        )
        
        # Send email notification
        if verification.email:
            name = f"{verification.first_name or ''} {verification.last_name or ''}".strip() or "there"
            
            if result.status == KYCStatus.APPROVED:
                send_kyc_complete_email.delay(
                    verification.email,
                    name,
                    {
                        'wallet_address': verification.wallet_address,
                        'verification_level': verification.verification_level,
                    }
                )
                
                # Trigger on-chain registration
                sync_kyc_to_registry.delay(verification.id)
                
            elif result.status == KYCStatus.REJECTED:
                send_kyc_failed_email.delay(
                    verification.email,
                    name,
                    {
                        'wallet_address': verification.wallet_address,
                        'rejection_reasons': verification.get_rejection_reasons(),
                    }
                )
        
        return True
        
    except Exception as exc:
        logger.error("kyc_webhook_error", error=str(exc), data=webhook_data)
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=5)
def sync_kyc_to_registry(self, verification_id: int):
    """
    Sync approved KYC verification to on-chain IdentityRegistry
    
    This task registers the verified address in the IdentityRegistry
    smart contract after KYC approval.
    """
    try:
        from src.models.user import db
        from src.models.kyc import KYCVerification
        
        verification = KYCVerification.query.get(verification_id)
        
        if not verification:
            logger.error("sync_kyc_verification_not_found", verification_id=verification_id)
            return False
        
        if verification.status != 'approved':
            logger.warning("sync_kyc_not_approved", verification_id=verification_id, status=verification.status)
            return False
        
        # TODO: Implement on-chain registration
        # This would call the IdentityRegistry contract's registerIdentity function
        # 
        # Example implementation:
        # from web3 import Web3
        # w3 = Web3(Web3.HTTPProvider(os.environ.get('ETHEREUM_RPC_URL')))
        # registry_contract = w3.eth.contract(address=registry_address, abi=registry_abi)
        # tx = registry_contract.functions.registerIdentity(
        #     verification.wallet_address,
        #     verification.country_code or 'US',
        #     verification.verification_level
        # ).transact({'from': operator_address})
        # receipt = w3.eth.wait_for_transaction_receipt(tx)
        
        logger.info(
            "kyc_registry_sync_pending",
            verification_id=verification_id,
            wallet_address=verification.wallet_address,
            message="On-chain sync not yet implemented - pending contract integration"
        )
        
        return True
        
    except Exception as exc:
        logger.error("sync_kyc_registry_error", error=str(exc), verification_id=verification_id)
        raise self.retry(exc=exc, countdown=120 * (self.request.retries + 1))


@celery_app.task
def check_expired_verifications():
    """
    Periodic task to check and update expired verifications
    
    This should be scheduled to run daily via Celery Beat.
    """
    try:
        from src.models.user import db
        from src.models.kyc import KYCVerification
        
        # Find expired verifications
        expired = KYCVerification.query.filter(
            KYCVerification.status == 'approved',
            KYCVerification.expires_at < datetime.utcnow()
        ).all()
        
        count = 0
        for verification in expired:
            verification.status = 'expired'
            verification.updated_at = datetime.utcnow()
            count += 1
            
            # TODO: Optionally revoke on-chain verification
            # TODO: Send expiration notification email
        
        if count > 0:
            db.session.commit()
            logger.info("expired_verifications_updated", count=count)
        
        return count
        
    except Exception as exc:
        logger.error("check_expired_verifications_error", error=str(exc))
        raise


@celery_app.task(bind=True, max_retries=3)
def poll_kyc_status(self, check_id: str, wallet_address: str):
    """
    Poll KYC provider for status update
    
    Used when webhooks fail or for verification confirmation.
    """
    try:
        from src.models.user import db
        from src.models.kyc import KYCVerification
        from src.services.kyc import get_kyc_service, KYCStatus
        
        kyc_service = get_kyc_service()
        result = kyc_service.get_check_status(check_id)
        
        verification = KYCVerification.query.filter_by(check_id=check_id).first()
        
        if not verification:
            logger.warning("poll_kyc_verification_not_found", check_id=check_id)
            return False
        
        # Update if status changed
        if verification.status != result.status.value:
            verification.status = result.status.value
            verification.verification_level = result.verification_level or 1
            verification.country_code = result.country_code
            
            if result.rejection_reasons:
                verification.set_rejection_reasons(result.rejection_reasons)
            
            if result.completed_at:
                verification.completed_at = result.completed_at
            
            if result.status == KYCStatus.APPROVED:
                verification.expires_at = datetime.utcnow() + timedelta(days=365)
            
            verification.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(
                "kyc_status_polled",
                check_id=check_id,
                new_status=result.status.value
            )
            
            # Trigger follow-up actions
            if result.status == KYCStatus.APPROVED:
                sync_kyc_to_registry.delay(verification.id)
        
        return True
        
    except Exception as exc:
        logger.error("poll_kyc_status_error", error=str(exc), check_id=check_id)
        raise self.retry(exc=exc, countdown=300 * (self.request.retries + 1))
