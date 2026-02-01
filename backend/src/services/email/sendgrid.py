"""
SendGrid Email Service Implementation
https://docs.sendgrid.com/
"""

from typing import List, Dict, Any, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, Email, Content

from .service import EmailService, EmailTemplate, EmailMessage, EmailRecipient, EmailResult


def get_config():
    """Get configuration - imported here to avoid circular imports"""
    from src.config import Config
    return Config


class SendGridEmailService(EmailService):
    """SendGrid email service implementation"""
    
    def __init__(self):
        config = get_config()
        self.api_key = config.SENDGRID_API_KEY
        self.from_email = config.EMAIL_FROM_ADDRESS
        self.from_name = config.EMAIL_FROM_NAME
        
        if self.api_key:
            self.client = SendGridAPIClient(api_key=self.api_key)
        else:
            self.client = None
    
    @property
    def provider_name(self) -> str:
        return "sendgrid"
    
    def send(self, message: EmailMessage) -> EmailResult:
        """Send an email message via SendGrid"""
        if not self.client:
            return EmailResult(
                success=False,
                error="SendGrid API key not configured"
            )
        
        try:
            from_email = Email(
                message.from_email or self.from_email,
                message.from_name or self.from_name
            )
            
            to_emails = [
                To(r.email, r.name) for r in message.to
            ]
            
            mail = Mail(
                from_email=from_email,
                to_emails=to_emails,
                subject=message.subject,
                html_content=message.html_content,
                plain_text_content=message.text_content
            )
            
            if message.reply_to:
                mail.reply_to = Email(message.reply_to)
            
            response = self.client.send(mail)
            
            return EmailResult(
                success=response.status_code in [200, 201, 202],
                message_id=response.headers.get("X-Message-Id"),
            )
            
        except Exception as e:
            return EmailResult(
                success=False,
                error=str(e)
            )
    
    def send_template(
        self,
        template: EmailTemplate,
        to: List[EmailRecipient],
        template_data: Dict[str, Any],
        subject: Optional[str] = None
    ) -> EmailResult:
        """Send an email using a pre-defined template"""
        
        # Render the template
        html_content = self.render_template(template, template_data)
        
        # Get default subject if not provided
        if not subject:
            subject = self._get_default_subject(template, template_data)
        
        message = EmailMessage(
            to=to,
            subject=subject,
            html_content=html_content,
            text_content=self._html_to_text(html_content),
        )
        
        return self.send(message)
    
    def _get_default_subject(self, template: EmailTemplate, data: Dict[str, Any]) -> str:
        """Get the default subject for a template"""
        subjects = {
            EmailTemplate.KYC_VERIFICATION_STARTED: "Your Identity Verification Has Started",
            EmailTemplate.KYC_VERIFICATION_COMPLETE: "Identity Verification Complete - Welcome to RWA-Studio",
            EmailTemplate.KYC_VERIFICATION_FAILED: "Action Required: Identity Verification Issue",
            EmailTemplate.TRANSFER_NOTIFICATION: f"Token Transfer: {data.get('token_name', 'RWA Token')}",
            EmailTemplate.COMPLIANCE_ALERT: f"[Alert] Compliance Issue: {data.get('alert_type', 'Review Required')}",
            EmailTemplate.SUBSCRIPTION_CREATED: "Welcome to RWA-Studio Pro!",
            EmailTemplate.SUBSCRIPTION_CANCELLED: "Your RWA-Studio Subscription Has Been Cancelled",
            EmailTemplate.PAYMENT_FAILED: "Action Required: Payment Failed",
            EmailTemplate.WELCOME: "Welcome to RWA-Studio!",
        }
        return subjects.get(template, "RWA-Studio Notification")
    
    def _html_to_text(self, html: str) -> str:
        """Convert HTML to plain text (simple implementation)"""
        import re
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
