"""
Email Service Base Class
Abstract interface for email service integrations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any


class EmailTemplate(Enum):
    """Pre-defined email templates"""
    KYC_VERIFICATION_STARTED = "kyc_verification_started"
    KYC_VERIFICATION_COMPLETE = "kyc_verification_complete"
    KYC_VERIFICATION_FAILED = "kyc_verification_failed"
    TRANSFER_NOTIFICATION = "transfer_notification"
    COMPLIANCE_ALERT = "compliance_alert"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"
    PAYMENT_FAILED = "payment_failed"
    WELCOME = "welcome"


@dataclass
class EmailRecipient:
    """Email recipient"""
    email: str
    name: Optional[str] = None


@dataclass
class EmailMessage:
    """Email message structure"""
    to: List[EmailRecipient]
    subject: str
    html_content: str
    text_content: Optional[str] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None
    reply_to: Optional[str] = None
    template_id: Optional[str] = None
    template_data: Optional[Dict[str, Any]] = None


@dataclass
class EmailResult:
    """Result of sending an email"""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class EmailService(ABC):
    """Abstract base class for email service providers"""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the email provider"""
        pass
    
    @abstractmethod
    def send(self, message: EmailMessage) -> EmailResult:
        """
        Send an email message
        
        Args:
            message: The email message to send
            
        Returns:
            EmailResult with status and message ID
        """
        pass
    
    @abstractmethod
    def send_template(
        self,
        template: EmailTemplate,
        to: List[EmailRecipient],
        template_data: Dict[str, Any],
        subject: Optional[str] = None
    ) -> EmailResult:
        """
        Send an email using a pre-defined template
        
        Args:
            template: The template to use
            to: List of recipients
            template_data: Data to populate the template
            subject: Optional subject override
            
        Returns:
            EmailResult with status and message ID
        """
        pass
    
    def render_template(self, template: EmailTemplate, data: Dict[str, Any]) -> str:
        """
        Render an HTML template with data
        
        Args:
            template: The template to render
            data: Data to populate the template
            
        Returns:
            Rendered HTML string
        """
        from .templates import get_template_html
        return get_template_html(template, data)
