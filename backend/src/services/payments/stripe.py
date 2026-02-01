"""
Stripe Payment Service Implementation
https://stripe.com/docs/api
"""

import stripe
from typing import Optional, Dict, Any, List
from datetime import datetime

from .service import (
    PaymentService, 
    SubscriptionPlan, 
    SubscriptionStatus,
    Customer, 
    Subscription, 
    CheckoutSession, 
    Invoice
)


def get_config():
    """Get configuration - imported here to avoid circular imports"""
    from src.config import Config
    return Config


class StripePaymentService(PaymentService):
    """Stripe payment service implementation"""
    
    def __init__(self):
        config = get_config()
        self.secret_key = config.STRIPE_SECRET_KEY
        self.publishable_key = config.STRIPE_PUBLISHABLE_KEY
        self.webhook_secret = config.STRIPE_WEBHOOK_SECRET
        
        # Price IDs for subscription plans
        self.price_ids = {
            SubscriptionPlan.STARTER: config.STRIPE_PRICE_STARTER,
            SubscriptionPlan.PROFESSIONAL: config.STRIPE_PRICE_PROFESSIONAL,
            SubscriptionPlan.ENTERPRISE: config.STRIPE_PRICE_ENTERPRISE,
        }
        
        if self.secret_key:
            stripe.api_key = self.secret_key
    
    @property
    def provider_name(self) -> str:
        return "stripe"
    
    def create_customer(self, email: str, name: Optional[str] = None, metadata: Dict = None) -> Customer:
        """Create a new Stripe customer"""
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {}
        )
        
        return Customer(
            id=customer.id,
            email=customer.email,
            name=customer.name,
            metadata=customer.metadata
        )
    
    def get_customer(self, customer_id: str) -> Optional[Customer]:
        """Get customer by ID"""
        try:
            customer = stripe.Customer.retrieve(customer_id)
            return Customer(
                id=customer.id,
                email=customer.email,
                name=customer.name,
                metadata=dict(customer.metadata) if customer.metadata else None
            )
        except stripe.error.InvalidRequestError:
            return None
    
    def create_checkout_session(
        self,
        customer_id: str,
        plan: SubscriptionPlan,
        success_url: str,
        cancel_url: str
    ) -> CheckoutSession:
        """Create a Stripe Checkout session for subscription"""
        price_id = self.price_ids.get(plan)
        if not price_id:
            raise ValueError(f"No price configured for plan: {plan.value}")
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{
                "price": price_id,
                "quantity": 1,
            }],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "plan": plan.value,
            }
        )
        
        return CheckoutSession(
            id=session.id,
            url=session.url,
            customer_id=customer_id,
            subscription_id=session.subscription
        )
    
    def get_subscription(self, subscription_id: str) -> Optional[Subscription]:
        """Get subscription by ID"""
        try:
            sub = stripe.Subscription.retrieve(subscription_id)
            return self._map_subscription(sub)
        except stripe.error.InvalidRequestError:
            return None
    
    def cancel_subscription(self, subscription_id: str, at_period_end: bool = True) -> Subscription:
        """Cancel a subscription"""
        if at_period_end:
            sub = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            sub = stripe.Subscription.delete(subscription_id)
        
        return self._map_subscription(sub)
    
    def get_invoices(self, customer_id: str, limit: int = 10) -> List[Invoice]:
        """Get customer invoices"""
        invoices = stripe.Invoice.list(customer=customer_id, limit=limit)
        
        return [
            Invoice(
                id=inv.id,
                customer_id=inv.customer,
                subscription_id=inv.subscription,
                amount_due=inv.amount_due,
                amount_paid=inv.amount_paid,
                currency=inv.currency,
                status=inv.status,
                created=datetime.fromtimestamp(inv.created),
                hosted_invoice_url=inv.hosted_invoice_url,
                pdf_url=inv.invoice_pdf
            )
            for inv in invoices.data
        ]
    
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        if not self.webhook_secret:
            return False
        
        try:
            stripe.Webhook.construct_event(
                payload,
                signature,
                self.webhook_secret
            )
            return True
        except (stripe.error.SignatureVerificationError, ValueError):
            return False
    
    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Stripe webhook payload"""
        event_type = payload.get("type", "")
        data = payload.get("data", {}).get("object", {})
        
        result = {
            "event_type": event_type,
            "raw_data": data,
        }
        
        # Handle subscription events
        if event_type.startswith("customer.subscription."):
            sub = self._map_subscription_dict(data)
            result["subscription"] = sub
            result["customer_id"] = data.get("customer")
        
        # Handle invoice events
        elif event_type.startswith("invoice."):
            result["invoice_id"] = data.get("id")
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("subscription")
            result["amount"] = data.get("amount_due", 0) / 100  # Convert cents to dollars
            result["status"] = data.get("status")
        
        # Handle checkout.session.completed
        elif event_type == "checkout.session.completed":
            result["session_id"] = data.get("id")
            result["customer_id"] = data.get("customer")
            result["subscription_id"] = data.get("subscription")
            result["plan"] = data.get("metadata", {}).get("plan")
        
        return result
    
    def _map_subscription(self, sub: stripe.Subscription) -> Subscription:
        """Map Stripe subscription to our Subscription model"""
        # Determine plan from price
        plan = SubscriptionPlan.STARTER
        if sub.items and sub.items.data:
            price_id = sub.items.data[0].price.id
            for p, pid in self.price_ids.items():
                if pid == price_id:
                    plan = p
                    break
        
        status = self._map_status(sub.status)
        
        return Subscription(
            id=sub.id,
            customer_id=sub.customer,
            plan=plan,
            status=status,
            current_period_start=datetime.fromtimestamp(sub.current_period_start),
            current_period_end=datetime.fromtimestamp(sub.current_period_end),
            cancel_at_period_end=sub.cancel_at_period_end,
            canceled_at=datetime.fromtimestamp(sub.canceled_at) if sub.canceled_at else None,
            tokens_limit=self.get_tokens_limit(plan),
            metadata=dict(sub.metadata) if sub.metadata else None
        )
    
    def _map_subscription_dict(self, data: Dict) -> Subscription:
        """Map subscription dict from webhook to Subscription model"""
        plan = SubscriptionPlan.STARTER
        items = data.get("items", {}).get("data", [])
        if items:
            price_id = items[0].get("price", {}).get("id")
            for p, pid in self.price_ids.items():
                if pid == price_id:
                    plan = p
                    break
        
        status = self._map_status(data.get("status", "active"))
        
        return Subscription(
            id=data.get("id", ""),
            customer_id=data.get("customer", ""),
            plan=plan,
            status=status,
            current_period_start=datetime.fromtimestamp(data.get("current_period_start", 0)),
            current_period_end=datetime.fromtimestamp(data.get("current_period_end", 0)),
            cancel_at_period_end=data.get("cancel_at_period_end", False),
            canceled_at=datetime.fromtimestamp(data["canceled_at"]) if data.get("canceled_at") else None,
            tokens_limit=self.get_tokens_limit(plan),
            metadata=data.get("metadata")
        )
    
    def _map_status(self, stripe_status: str) -> SubscriptionStatus:
        """Map Stripe status to SubscriptionStatus enum"""
        mapping = {
            "active": SubscriptionStatus.ACTIVE,
            "past_due": SubscriptionStatus.PAST_DUE,
            "canceled": SubscriptionStatus.CANCELED,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "trialing": SubscriptionStatus.TRIALING,
            "paused": SubscriptionStatus.PAUSED,
        }
        return mapping.get(stripe_status, SubscriptionStatus.INCOMPLETE)
