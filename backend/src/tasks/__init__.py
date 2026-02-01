"""
Celery Tasks Module for RWA-Studio
Author: Sowad Al-Mughni

Phase 3: Async Task Processing
"""

from .celery_app import celery_app
from .email_tasks import (
    send_kyc_started_email,
    send_kyc_complete_email,
    send_kyc_failed_email,
    send_transfer_notification_email,
    send_compliance_alert_email,
    send_subscription_email,
)
from .kyc_tasks import (
    process_kyc_webhook,
    sync_kyc_to_registry,
)

__all__ = [
    'celery_app',
    'send_kyc_started_email',
    'send_kyc_complete_email',
    'send_kyc_failed_email',
    'send_transfer_notification_email',
    'send_compliance_alert_email',
    'send_subscription_email',
    'process_kyc_webhook',
    'sync_kyc_to_registry',
]
