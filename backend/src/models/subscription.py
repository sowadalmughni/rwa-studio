"""
Subscription model for RWA-Studio SaaS billing
Author: Sowad Al-Mughni

Phase 3: Payment Gateway Integration
"""

from src.models.user import db, utc_now
from datetime import datetime


class Subscription(db.Model):
    """Model for tracking user subscriptions"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Stripe identifiers
    stripe_customer_id = db.Column(db.String(50), nullable=True, index=True)
    stripe_subscription_id = db.Column(db.String(50), unique=True, nullable=True, index=True)
    
    # Plan details
    plan = db.Column(db.String(20), nullable=False, default='starter')  # starter, professional, enterprise
    status = db.Column(db.String(20), nullable=False, default='incomplete')  # active, past_due, canceled, incomplete
    
    # Billing period
    current_period_start = db.Column(db.DateTime, nullable=True)
    current_period_end = db.Column(db.DateTime, nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, default=False)
    canceled_at = db.Column(db.DateTime, nullable=True)
    
    # Usage tracking
    tokens_limit = db.Column(db.Integer, default=3)  # Based on plan
    tokens_used = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('subscription', uselist=False))
    
    # Plan token limits
    PLAN_LIMITS = {
        'starter': 3,
        'professional': 10,
        'enterprise': 100,
    }
    
    def __repr__(self):
        return f'<Subscription {self.id} - {self.plan} ({self.status})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'plan': self.plan,
            'status': self.status,
            'current_period_start': self.current_period_start.isoformat() if self.current_period_start else None,
            'current_period_end': self.current_period_end.isoformat() if self.current_period_end else None,
            'cancel_at_period_end': self.cancel_at_period_end,
            'tokens_limit': self.tokens_limit,
            'tokens_used': self.tokens_used,
            'tokens_available': self.tokens_limit - self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def is_active(self) -> bool:
        """Check if subscription is currently active"""
        return self.status in ('active', 'trialing')
    
    def can_create_token(self) -> bool:
        """Check if user can create another token"""
        return self.is_active() and self.tokens_used < self.tokens_limit
    
    def increment_token_usage(self):
        """Increment the token usage counter"""
        self.tokens_used += 1
        self.updated_at = utc_now()
    
    def update_from_stripe(self, subscription_data):
        """Update model from Stripe subscription data"""
        self.stripe_subscription_id = subscription_data.id
        self.status = subscription_data.status
        self.current_period_start = datetime.fromtimestamp(subscription_data.current_period_start)
        self.current_period_end = datetime.fromtimestamp(subscription_data.current_period_end)
        self.cancel_at_period_end = subscription_data.cancel_at_period_end
        if subscription_data.canceled_at:
            self.canceled_at = datetime.fromtimestamp(subscription_data.canceled_at)
        self.updated_at = utc_now()


class BillingHistory(db.Model):
    """Model for tracking billing history and invoices"""
    __tablename__ = 'billing_history'
    
    id = db.Column(db.Integer, primary_key=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id'), nullable=False)
    
    # Stripe identifiers
    stripe_invoice_id = db.Column(db.String(50), unique=True, nullable=True)
    stripe_payment_intent_id = db.Column(db.String(50), nullable=True)
    
    # Invoice details
    amount = db.Column(db.Integer, nullable=False)  # Amount in cents
    currency = db.Column(db.String(3), default='usd')
    status = db.Column(db.String(20), nullable=False)  # paid, open, void, uncollectible
    
    # URLs
    invoice_url = db.Column(db.String(500), nullable=True)
    pdf_url = db.Column(db.String(500), nullable=True)
    
    # Timestamps
    invoice_date = db.Column(db.DateTime, nullable=False)
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    
    # Relationship
    subscription = db.relationship('Subscription', backref=db.backref('billing_history', lazy=True))
    
    def __repr__(self):
        return f'<BillingHistory {self.id} - ${self.amount/100:.2f} ({self.status})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'subscription_id': self.subscription_id,
            'amount': self.amount / 100,  # Convert cents to dollars
            'currency': self.currency,
            'status': self.status,
            'invoice_url': self.invoice_url,
            'pdf_url': self.pdf_url,
            'invoice_date': self.invoice_date.isoformat() if self.invoice_date else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
        }
