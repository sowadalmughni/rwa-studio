"""
Email Service Module
Provides email delivery via SendGrid
"""

from .service import EmailService, EmailTemplate
from .sendgrid import SendGridEmailService

_email_service = None


def get_email_service() -> EmailService:
    """Get the configured email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = SendGridEmailService()
    return _email_service


__all__ = ['EmailService', 'EmailTemplate', 'SendGridEmailService', 'get_email_service']
