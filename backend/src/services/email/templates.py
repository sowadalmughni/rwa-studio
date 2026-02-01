"""
Email Templates
HTML templates for various email types
"""

from typing import Dict, Any
from .service import EmailTemplate


def get_template_html(template: EmailTemplate, data: Dict[str, Any]) -> str:
    """Get the rendered HTML for a template"""
    templates = {
        EmailTemplate.KYC_VERIFICATION_STARTED: _kyc_started_template,
        EmailTemplate.KYC_VERIFICATION_COMPLETE: _kyc_complete_template,
        EmailTemplate.KYC_VERIFICATION_FAILED: _kyc_failed_template,
        EmailTemplate.TRANSFER_NOTIFICATION: _transfer_notification_template,
        EmailTemplate.COMPLIANCE_ALERT: _compliance_alert_template,
        EmailTemplate.SUBSCRIPTION_CREATED: _subscription_created_template,
        EmailTemplate.SUBSCRIPTION_CANCELLED: _subscription_cancelled_template,
        EmailTemplate.PAYMENT_FAILED: _payment_failed_template,
        EmailTemplate.WELCOME: _welcome_template,
    }
    
    template_func = templates.get(template, _default_template)
    return template_func(data)


def _base_template(content: str) -> str:
    """Base HTML template wrapper"""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>RWA-Studio</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .container {{
                background-color: #ffffff;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .logo {{
                font-size: 24px;
                font-weight: bold;
                color: #6366f1;
            }}
            .button {{
                display: inline-block;
                background-color: #6366f1;
                color: #ffffff;
                padding: 12px 24px;
                border-radius: 6px;
                text-decoration: none;
                font-weight: 600;
                margin: 20px 0;
            }}
            .button:hover {{
                background-color: #5558dd;
            }}
            .alert {{
                background-color: #fef3c7;
                border-left: 4px solid #f59e0b;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .success {{
                background-color: #d1fae5;
                border-left: 4px solid #10b981;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .error {{
                background-color: #fee2e2;
                border-left: 4px solid #ef4444;
                padding: 15px;
                margin: 20px 0;
                border-radius: 4px;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="logo">RWA-Studio</div>
            </div>
            {content}
            <div class="footer">
                <p>&copy; 2026 RWA-Studio. All rights reserved.</p>
                <p>This is an automated message. Please do not reply directly to this email.</p>
            </div>
        </div>
    </body>
    </html>
    """


def _kyc_started_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>Identity Verification Started</h2>
    <p>Hello {data.get('name', 'there')},</p>
    <p>We've begun processing your identity verification for wallet address:</p>
    <p><strong>{data.get('wallet_address', '')}</strong></p>
    <p>This typically takes a few minutes, but may take up to 24 hours in some cases.</p>
    <p>We'll notify you as soon as verification is complete.</p>
    """
    return _base_template(content)


def _kyc_complete_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>Identity Verification Complete</h2>
    <div class="success">
        <strong>✓ Verified</strong> - Your identity has been successfully verified.
    </div>
    <p>Hello {data.get('name', 'there')},</p>
    <p>Great news! Your identity verification for wallet address:</p>
    <p><strong>{data.get('wallet_address', '')}</strong></p>
    <p>has been successfully completed. You now have access to:</p>
    <ul>
        <li>Invest in tokenized real-world assets</li>
        <li>Transfer tokens to other verified addresses</li>
        <li>Full platform features based on your verification level</li>
    </ul>
    <p>Verification Level: <strong>Level {data.get('verification_level', 1)}</strong></p>
    <a href="{data.get('dashboard_url', '#')}" class="button">Go to Dashboard</a>
    """
    return _base_template(content)


def _kyc_failed_template(data: Dict[str, Any]) -> str:
    reasons = data.get('rejection_reasons', ['Unable to verify identity'])
    reasons_html = ''.join([f'<li>{r}</li>' for r in reasons])
    
    content = f"""
    <h2>Identity Verification Issue</h2>
    <div class="error">
        <strong>Action Required</strong> - We couldn't complete your verification.
    </div>
    <p>Hello {data.get('name', 'there')},</p>
    <p>Unfortunately, we were unable to verify your identity for wallet address:</p>
    <p><strong>{data.get('wallet_address', '')}</strong></p>
    <p><strong>Reasons:</strong></p>
    <ul>{reasons_html}</ul>
    <p>Please try again with the following tips:</p>
    <ul>
        <li>Ensure your document is clearly visible and not expired</li>
        <li>Take photos in good lighting</li>
        <li>Make sure all information matches your documents</li>
    </ul>
    <a href="{data.get('retry_url', '#')}" class="button">Try Again</a>
    """
    return _base_template(content)


def _transfer_notification_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>Token Transfer Notification</h2>
    <p>Hello {data.get('name', 'there')},</p>
    <p>A token transfer has been processed:</p>
    <table style="width: 100%; margin: 20px 0;">
        <tr><td><strong>Token:</strong></td><td>{data.get('token_name', 'RWA Token')}</td></tr>
        <tr><td><strong>Amount:</strong></td><td>{data.get('amount', '0')} {data.get('symbol', 'RWA')}</td></tr>
        <tr><td><strong>From:</strong></td><td style="font-family: monospace; font-size: 12px;">{data.get('from_address', '')}</td></tr>
        <tr><td><strong>To:</strong></td><td style="font-family: monospace; font-size: 12px;">{data.get('to_address', '')}</td></tr>
        <tr><td><strong>Transaction:</strong></td><td style="font-family: monospace; font-size: 12px;">{data.get('tx_hash', '')}</td></tr>
    </table>
    <a href="{data.get('explorer_url', '#')}" class="button">View on Explorer</a>
    """
    return _base_template(content)


def _compliance_alert_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>Compliance Alert</h2>
    <div class="alert">
        <strong>⚠ {data.get('alert_type', 'Review Required')}</strong>
    </div>
    <p>A compliance event has been detected:</p>
    <table style="width: 100%; margin: 20px 0;">
        <tr><td><strong>Token:</strong></td><td>{data.get('token_name', 'RWA Token')}</td></tr>
        <tr><td><strong>Event:</strong></td><td>{data.get('event_type', 'Compliance Violation')}</td></tr>
        <tr><td><strong>Severity:</strong></td><td>{data.get('severity', 'Medium')}</td></tr>
        <tr><td><strong>Address:</strong></td><td style="font-family: monospace; font-size: 12px;">{data.get('address', '')}</td></tr>
    </table>
    <p><strong>Details:</strong></p>
    <p>{data.get('details', 'Please review this compliance event in the dashboard.')}</p>
    <a href="{data.get('review_url', '#')}" class="button">Review Event</a>
    """
    return _base_template(content)


def _subscription_created_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>Welcome to RWA-Studio Pro!</h2>
    <div class="success">
        <strong>✓ Subscription Active</strong>
    </div>
    <p>Hello {data.get('name', 'there')},</p>
    <p>Thank you for subscribing to RWA-Studio {data.get('plan', 'Pro')}!</p>
    <p>Your subscription includes:</p>
    <ul>
        <li>Up to {data.get('tokens_limit', '10')} tokenized assets</li>
        <li>Priority support</li>
        <li>Advanced analytics dashboard</li>
        <li>Custom compliance rules</li>
    </ul>
    <p>Next billing date: <strong>{data.get('next_billing_date', 'N/A')}</strong></p>
    <a href="{data.get('dashboard_url', '#')}" class="button">Get Started</a>
    """
    return _base_template(content)


def _subscription_cancelled_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>Subscription Cancelled</h2>
    <p>Hello {data.get('name', 'there')},</p>
    <p>Your RWA-Studio subscription has been cancelled.</p>
    <p>Your access will remain active until: <strong>{data.get('access_until', 'N/A')}</strong></p>
    <p>We're sorry to see you go! If you change your mind, you can resubscribe at any time.</p>
    <a href="{data.get('resubscribe_url', '#')}" class="button">Resubscribe</a>
    """
    return _base_template(content)


def _payment_failed_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>Payment Failed</h2>
    <div class="error">
        <strong>Action Required</strong> - We couldn't process your payment.
    </div>
    <p>Hello {data.get('name', 'there')},</p>
    <p>We were unable to process your payment for RWA-Studio {data.get('plan', 'Pro')}.</p>
    <p>Amount: <strong>${data.get('amount', '0.00')}</strong></p>
    <p>Please update your payment method to avoid service interruption.</p>
    <a href="{data.get('update_payment_url', '#')}" class="button">Update Payment Method</a>
    """
    return _base_template(content)


def _welcome_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>Welcome to RWA-Studio!</h2>
    <p>Hello {data.get('name', 'there')},</p>
    <p>Welcome to RWA-Studio - the platform for tokenizing real-world assets.</p>
    <p>Here's how to get started:</p>
    <ol>
        <li><strong>Verify your identity</strong> - Complete KYC to access all features</li>
        <li><strong>Connect your wallet</strong> - MetaMask, WalletConnect, and more supported</li>
        <li><strong>Create your first token</strong> - Tokenize assets in just 5 clicks</li>
    </ol>
    <a href="{data.get('get_started_url', '#')}" class="button">Get Started</a>
    """
    return _base_template(content)


def _default_template(data: Dict[str, Any]) -> str:
    content = f"""
    <h2>{data.get('title', 'Notification')}</h2>
    <p>{data.get('message', 'You have a new notification from RWA-Studio.')}</p>
    """
    return _base_template(content)
