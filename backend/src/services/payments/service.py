"""
Payment Service Base Class
Abstract interface for payment service integrations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime


class SubscriptionPlan(Enum):
    """Available subscription plans"""
    STARTER = "starter"          # $99/month - 3 tokens
    PROFESSIONAL = "professional"  # $299/month - 10 tokens
    ENTERPRISE = "enterprise"      # Custom pricing


class SubscriptionStatus(Enum):
    """Subscription status"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    TRIALING = "trialing"
    PAUSED = "paused"


@dataclass
class Customer:
    """Customer data"""
    id: str
    email: str
    name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class Subscription:
    """Subscription data"""
    id: str
    customer_id: str
    plan: SubscriptionPlan
    status: SubscriptionStatus
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False
    canceled_at: Optional[datetime] = None
    tokens_limit: int = 3
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class CheckoutSession:
    """Checkout session for payment"""
    id: str
    url: str
    customer_id: Optional[str] = None
    subscription_id: Optional[str] = None


@dataclass
class Invoice:
    """Invoice data"""
    id: str
    customer_id: str
    subscription_id: Optional[str]
    amount_due: int  # in cents
    amount_paid: int
    currency: str
    status: str
    created: datetime
    hosted_invoice_url: Optional[str] = None
    pdf_url: Optional[str] = None


class PaymentService(ABC):
    """Abstract base class for payment service providers"""
    
    # Token limits per plan
    PLAN_LIMITS = {
        SubscriptionPlan.STARTER: 3,
        SubscriptionPlan.PROFESSIONAL: 10,
        SubscriptionPlan.ENTERPRISE: 100,
    }
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the payment provider"""
        pass
    
    @abstractmethod
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Dict = None) -> Customer:
        """
        Create a new customer
        
        Args:
            email: Customer email
            name: Optional customer name
            metadata: Optional metadata (e.g., wallet_address)
            
        Returns:
            Customer object with provider ID
        """
        pass
    
    @abstractmethod
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        pass
    
    @abstractmethod
    def create_checkout_session(
        self,
        customer_id: str,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str
    ) -> CheckoutSession:
        """
        Create a checkout session for subscription
        
        Args:
            customer_id: The customer ID
            plan: The subscription plan
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            
        Returns:
            CheckoutSession with URL to redirect user
        """
        pass
    
    @abstractmethod
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        pass
    
    @abstractmethod
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Subscription:
        """
        Cancel a subscription
        
        Args:
            subscription_id: The subscription ID
            at_period_end: If True, cancel at end of current period
            
        Returns:
            Updated Subscription object
        """
        pass
    
    @abstractmethod
    def get_invoices(self, customer_id: str, limit: int = 10) -> List[Invoice]:
        """Get customer invoices"""
        pass
    
    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature"""
        pass
    
    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse webhook payload into structured data"""
        pass
    
    def get_tokens_limit(self, plan: SubscriptionPlan) -> int:
        """Get the token limit for a plan"""
        return self.PLAN_LIMITS.get(plan, 3)
