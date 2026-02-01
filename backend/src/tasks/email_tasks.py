"""
Email Tasks for Celery
Author: Sowad Al-Mughni

Async Email Sending
"""

from .celery_app import celery_app
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True, max_retries=3)
def send_kyc_started_email(self, recipient_email: str, recipient_name: str, data: Dict[str, Any]):
    """Send KYC verification started email"""
    try:
        from src.services.email import get_email_service, EmailTemplate, EmailRecipient
        
        email_service = get_email_service()
        result = email_service.send_template(
            template=EmailTemplate.KYC_VERIFICATION_STARTED,
            to=[EmailRecipient(email=recipient_email, name=recipient_name)],
            template_data={
                'name': recipient_name,
                'wallet_address': data.get('wallet_address', ''),
            }
        )
        
        if result.success:
            logger.info("kyc_started_email_sent", email=recipient_email, message_id=result.message_id)
        else:
            logger.error("kyc_started_email_failed", email=recipient_email, error=result.error)
            raise Exception(result.error)
        
        return result.success
        
    except Exception as exc:
        logger.error("kyc_started_email_error", email=recipient_email, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def send_kyc_complete_email(self, recipient_email: str, recipient_name: str, data: Dict[str, Any]):
    """Send KYC verification complete email"""
    try:
        from src.services.email import get_email_service, EmailTemplate, EmailRecipient
        
        email_service = get_email_service()
        result = email_service.send_template(
            template=EmailTemplate.KYC_VERIFICATION_COMPLETE,
            to=[EmailRecipient(email=recipient_email, name=recipient_name)],
            template_data={
                'name': recipient_name,
                'wallet_address': data.get('wallet_address', ''),
                'verification_level': data.get('verification_level', 1),
                'dashboard_url': data.get('dashboard_url', 'https://app.rwa-studio.com/dashboard'),
            }
        )
        
        if result.success:
            logger.info("kyc_complete_email_sent", email=recipient_email, message_id=result.message_id)
        else:
            logger.error("kyc_complete_email_failed", email=recipient_email, error=result.error)
            raise Exception(result.error)
        
        return result.success
        
    except Exception as exc:
        logger.error("kyc_complete_email_error", email=recipient_email, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def send_kyc_failed_email(self, recipient_email: str, recipient_name: str, data: Dict[str, Any]):
    """Send KYC verification failed email"""
    try:
        from src.services.email import get_email_service, EmailTemplate, EmailRecipient
        
        email_service = get_email_service()
        result = email_service.send_template(
            template=EmailTemplate.KYC_VERIFICATION_FAILED,
            to=[EmailRecipient(email=recipient_email, name=recipient_name)],
            template_data={
                'name': recipient_name,
                'wallet_address': data.get('wallet_address', ''),
                'rejection_reasons': data.get('rejection_reasons', ['Unable to verify identity']),
                'retry_url': data.get('retry_url', 'https://app.rwa-studio.com/kyc/retry'),
            }
        )
        
        if result.success:
            logger.info("kyc_failed_email_sent", email=recipient_email, message_id=result.message_id)
        else:
            logger.error("kyc_failed_email_failed", email=recipient_email, error=result.error)
            raise Exception(result.error)
        
        return result.success
        
    except Exception as exc:
        logger.error("kyc_failed_email_error", email=recipient_email, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def send_transfer_notification_email(self, recipient_email: str, recipient_name: str, data: Dict[str, Any]):
    """Send token transfer notification email"""
    try:
        from src.services.email import get_email_service, EmailTemplate, EmailRecipient
        
        email_service = get_email_service()
        result = email_service.send_template(
            template=EmailTemplate.TRANSFER_NOTIFICATION,
            to=[EmailRecipient(email=recipient_email, name=recipient_name)],
            template_data={
                'name': recipient_name,
                'token_name': data.get('token_name', 'RWA Token'),
                'symbol': data.get('symbol', 'RWA'),
                'amount': data.get('amount', '0'),
                'from_address': data.get('from_address', ''),
                'to_address': data.get('to_address', ''),
                'tx_hash': data.get('tx_hash', ''),
                'explorer_url': data.get('explorer_url', ''),
            }
        )
        
        if result.success:
            logger.info("transfer_email_sent", email=recipient_email, message_id=result.message_id)
        else:
            logger.error("transfer_email_failed", email=recipient_email, error=result.error)
            raise Exception(result.error)
        
        return result.success
        
    except Exception as exc:
        logger.error("transfer_email_error", email=recipient_email, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def send_compliance_alert_email(self, recipient_emails: List[str], data: Dict[str, Any]):
    """Send compliance alert email to multiple recipients"""
    try:
        from src.services.email import get_email_service, EmailTemplate, EmailRecipient
        
        email_service = get_email_service()
        recipients = [EmailRecipient(email=email) for email in recipient_emails]
        
        result = email_service.send_template(
            template=EmailTemplate.COMPLIANCE_ALERT,
            to=recipients,
            template_data={
                'alert_type': data.get('alert_type', 'Review Required'),
                'token_name': data.get('token_name', 'RWA Token'),
                'event_type': data.get('event_type', 'Compliance Violation'),
                'severity': data.get('severity', 'Medium'),
                'address': data.get('address', ''),
                'details': data.get('details', 'Please review this compliance event in the dashboard.'),
                'review_url': data.get('review_url', 'https://app.rwa-studio.com/compliance'),
            }
        )
        
        if result.success:
            logger.info("compliance_alert_email_sent", recipients=len(recipient_emails), message_id=result.message_id)
        else:
            logger.error("compliance_alert_email_failed", recipients=len(recipient_emails), error=result.error)
            raise Exception(result.error)
        
        return result.success
        
    except Exception as exc:
        logger.error("compliance_alert_email_error", recipients=len(recipient_emails), error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))


@celery_app.task(bind=True, max_retries=3)
def send_subscription_email(self, recipient_email: str, recipient_name: str, template_type: str, data: Dict[str, Any]):
    """Send subscription-related emails"""
    try:
        from src.services.email import get_email_service, EmailTemplate, EmailRecipient
        
        # Map template type to enum
        template_map = {
            'created': EmailTemplate.SUBSCRIPTION_CREATED,
            'cancelled': EmailTemplate.SUBSCRIPTION_CANCELLED,
            'payment_failed': EmailTemplate.PAYMENT_FAILED,
        }
        
        template = template_map.get(template_type, EmailTemplate.SUBSCRIPTION_CREATED)
        
        email_service = get_email_service()
        result = email_service.send_template(
            template=template,
            to=[EmailRecipient(email=recipient_email, name=recipient_name)],
            template_data={
                'name': recipient_name,
                'plan': data.get('plan', 'Pro'),
                'tokens_limit': data.get('tokens_limit', '10'),
                'next_billing_date': data.get('next_billing_date', 'N/A'),
                'access_until': data.get('access_until', 'N/A'),
                'amount': data.get('amount', '0.00'),
                'dashboard_url': data.get('dashboard_url', 'https://app.rwa-studio.com/dashboard'),
                'resubscribe_url': data.get('resubscribe_url', 'https://app.rwa-studio.com/billing'),
                'update_payment_url': data.get('update_payment_url', 'https://app.rwa-studio.com/billing/payment'),
            }
        )
        
        if result.success:
            logger.info("subscription_email_sent", email=recipient_email, template=template_type, message_id=result.message_id)
        else:
            logger.error("subscription_email_failed", email=recipient_email, template=template_type, error=result.error)
            raise Exception(result.error)
        
        return result.success
        
    except Exception as exc:
        logger.error("subscription_email_error", email=recipient_email, template=template_type, error=str(exc))
        raise self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
