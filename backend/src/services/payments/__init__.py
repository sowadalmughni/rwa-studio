"""
Payment Service Module
Provides payment processing via Stripe
"""

from .service import PaymentService, SubscriptionPlan, SubscriptionStatus
from .stripe import StripePaymentService

_payment_service = None


def get_payment_service() -> PaymentService:
    """Get the configured payment service instance"""
    global _payment_service
    if _payment_service is None:
        _payment_service = StripePaymentService()
    return _payment_service


__all__ = ['PaymentService', 'SubscriptionPlan', 'SubscriptionStatus', 'StripePaymentService', 'get_payment_service']
