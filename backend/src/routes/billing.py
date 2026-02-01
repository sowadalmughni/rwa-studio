"""
Billing Routes for RWA-Studio
Author: Sowad Al-Mughni

Stripe Payment Gateway API Endpoints

Security:
- Rate limiting on all endpoints
- Sensitive operations (payment) have strict limits
- Webhook signature verification
"""

from flask import Blueprint, request, jsonify, redirect
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import structlog

from src.models.user import db, User
from src.models.subscription import Subscription, BillingHistory
from src.services.payments import get_payment_service, SubscriptionPlan, SubscriptionStatus
from src.tasks.email_tasks import send_subscription_email
from src.middleware.rate_limit import rate_limit_read, rate_limit_write, rate_limit_sensitive, rate_limit_public

logger = structlog.get_logger()

billing_bp = Blueprint('billing', __name__, url_prefix='/api/billing')


@billing_bp.route('/plans', methods=['GET'])
@rate_limit_public  # Public endpoint to view plans
def get_plans():
    """Get available subscription plans"""
    plans = [
        {
            'id': 'starter',
            'name': 'Starter',
            'price': 99,
            'currency': 'usd',
            'interval': 'month',
            'tokens_limit': 3,
            'features': [
                'Up to 3 tokenized assets',
                'Basic compliance rules',
                'Email support',
                'Standard analytics'
            ]
        },
        {
            'id': 'professional',
            'name': 'Professional',
            'price': 299,
            'currency': 'usd',
            'interval': 'month',
            'tokens_limit': 10,
            'features': [
                'Up to 10 tokenized assets',
                'All compliance rules',
                'Priority support',
                'Advanced analytics',
                'Custom branding',
                'API access'
            ],
            'recommended': True
        },
        {
            'id': 'enterprise',
            'name': 'Enterprise',
            'price': None,  # Custom pricing
            'currency': 'usd',
            'interval': 'month',
            'tokens_limit': 100,
            'features': [
                'Unlimited tokenized assets',
                'Custom compliance rules',
                '24/7 dedicated support',
                'White-label solution',
                'SLA guarantees',
                'On-premise deployment option'
            ],
            'contact_sales': True
        }
    ]
    
    return jsonify({'plans': plans})


@billing_bp.route('/subscription', methods=['GET'])
@jwt_required()
@rate_limit_read  # User's own subscription data
def get_subscription():
    """Get current user's subscription"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription:
            return jsonify({
                'has_subscription': False,
                'subscription': None
            })
        
        return jsonify({
            'has_subscription': True,
            'subscription': subscription.to_dict()
        })
        
    except Exception as e:
        logger.error("get_subscription_error", error=str(e))
        return jsonify({'error': 'Failed to get subscription'}), 500


@billing_bp.route('/checkout', methods=['POST'])
@jwt_required()
@rate_limit_sensitive  # Payment operations are sensitive
def create_checkout():
    """
    Create a Stripe checkout session
    
    Request body:
    {
        "plan": "professional",
        "success_url": "https://app.rwa-studio.com/billing/success",
        "cancel_url": "https://app.rwa-studio.com/billing/cancel"
    }
    """
    try:
        data = request.get_json()
        
        plan_id = data.get('plan', 'professional')
        success_url = data.get('success_url', 'http://localhost:5173/billing/success')
        cancel_url = data.get('cancel_url', 'http://localhost:5173/billing/cancel')
        
        # Map plan ID to enum
        plan_map = {
            'starter': SubscriptionPlan.STARTER,
            'professional': SubscriptionPlan.PROFESSIONAL,
            'enterprise': SubscriptionPlan.ENTERPRISE,
        }
        
        plan = plan_map.get(plan_id)
        if not plan:
            return jsonify({'error': 'Invalid plan'}), 400
        
        if plan == SubscriptionPlan.ENTERPRISE:
            return jsonify({
                'error': 'Enterprise plan requires contacting sales',
                'contact_url': 'https://rwa-studio.com/contact'
            }), 400
        
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        payment_service = get_payment_service()
        
        # Get or create Stripe customer
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if subscription and subscription.stripe_customer_id:
            customer_id = subscription.stripe_customer_id
        else:
            # Create new customer
            customer = payment_service.create_customer(
                email=user.email,
                name=user.username,
                metadata={'wallet_address': user.wallet_address or '', 'user_id': str(user.id)}
            )
            customer_id = customer.id
            
            # Create or update subscription record
            if not subscription:
                subscription = Subscription(
                    user_id=user.id,
                    stripe_customer_id=customer_id,
                    plan=plan_id,
                    status='incomplete',
                    tokens_limit=Subscription.PLAN_LIMITS.get(plan_id, 3)
                )
                db.session.add(subscription)
            else:
                subscription.stripe_customer_id = customer_id
            
            db.session.commit()
        
        # Create checkout session
        try:
            session = payment_service.create_checkout_session(
                customer_id=customer_id,
                plan=plan,
                success_url=success_url + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=cancel_url
            )
        except Exception as e:
            logger.error("checkout_session_failed", error=str(e))
            return jsonify({'error': 'Failed to create checkout session'}), 500
        
        logger.info(
            "checkout_created",
            user_id=user.id,
            plan=plan_id,
            session_id=session.id
        )
        
        return jsonify({
            'checkout_url': session.url,
            'session_id': session.id
        })
        
    except Exception as e:
        logger.error("create_checkout_error", error=str(e))
        return jsonify({'error': 'Failed to create checkout'}), 500


@billing_bp.route('/cancel', methods=['POST'])
@jwt_required()
@rate_limit_sensitive  # Subscription cancellation is sensitive
def cancel_subscription():
    """Cancel current subscription"""
    try:
        data = request.get_json() or {}
        at_period_end = data.get('at_period_end', True)
        
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription or not subscription.stripe_subscription_id:
            return jsonify({'error': 'No active subscription found'}), 404
        
        if subscription.status == 'canceled':
            return jsonify({'error': 'Subscription already canceled'}), 400
        
        payment_service = get_payment_service()
        
        try:
            result = payment_service.cancel_subscription(
                subscription.stripe_subscription_id,
                at_period_end=at_period_end
            )
        except Exception as e:
            logger.error("cancel_subscription_failed", error=str(e))
            return jsonify({'error': 'Failed to cancel subscription'}), 500
        
        # Update local subscription
        subscription.cancel_at_period_end = at_period_end
        if not at_period_end:
            subscription.status = 'canceled'
            subscription.canceled_at = datetime.utcnow()
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Send email notification
        send_subscription_email.delay(
            user.email,
            user.username,
            'cancelled',
            {
                'access_until': subscription.current_period_end.strftime('%B %d, %Y')
                    if subscription.current_period_end else 'N/A'
            }
        )
        
        logger.info(
            "subscription_canceled",
            user_id=user.id,
            at_period_end=at_period_end
        )
        
        return jsonify({
            'success': True,
            'subscription': subscription.to_dict()
        })
        
    except Exception as e:
        logger.error("cancel_subscription_error", error=str(e))
        return jsonify({'error': 'Failed to cancel subscription'}), 500


@billing_bp.route('/invoices', methods=['GET'])
@jwt_required()
@rate_limit_read  # Reading invoices
def get_invoices():
    """Get billing history/invoices"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription or not subscription.stripe_customer_id:
            return jsonify({'invoices': []})
        
        # Get from local database first
        local_invoices = BillingHistory.query.filter_by(
            subscription_id=subscription.id
        ).order_by(BillingHistory.invoice_date.desc()).limit(20).all()
        
        if local_invoices:
            return jsonify({
                'invoices': [inv.to_dict() for inv in local_invoices]
            })
        
        # Fallback to Stripe API
        payment_service = get_payment_service()
        
        try:
            invoices = payment_service.get_invoices(subscription.stripe_customer_id)
            
            return jsonify({
                'invoices': [
                    {
                        'id': inv.id,
                        'amount': inv.amount_due / 100,
                        'currency': inv.currency,
                        'status': inv.status,
                        'invoice_date': inv.created.isoformat(),
                        'invoice_url': inv.hosted_invoice_url,
                        'pdf_url': inv.pdf_url
                    }
                    for inv in invoices
                ]
            })
        except Exception as e:
            logger.error("get_invoices_failed", error=str(e))
            return jsonify({'invoices': []})
        
    except Exception as e:
        logger.error("get_invoices_error", error=str(e))
        return jsonify({'error': 'Failed to get invoices'}), 500


@billing_bp.route('/webhook', methods=['POST'])
@rate_limit_write  # Webhook from payment provider
def webhook():
    """
    Handle Stripe webhooks
    
    This endpoint receives webhooks from Stripe for subscription events.
    """
    try:
        payload = request.get_data()
        signature = request.headers.get('Stripe-Signature', '')
        
        payment_service = get_payment_service()
        
        # Verify webhook signature
        if not payment_service.verify_webhook(payload, signature):
            logger.warning("billing_webhook_invalid_signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        data = request.get_json()
        event_type = data.get('type', '')
        
        logger.info("billing_webhook_received", event_type=event_type)
        
        # Parse the webhook
        parsed = payment_service.parse_webhook(data)
        
        # Handle different event types
        if event_type == 'checkout.session.completed':
            _handle_checkout_completed(parsed)
        
        elif event_type == 'customer.subscription.created':
            _handle_subscription_created(parsed)
        
        elif event_type == 'customer.subscription.updated':
            _handle_subscription_updated(parsed)
        
        elif event_type == 'customer.subscription.deleted':
            _handle_subscription_deleted(parsed)
        
        elif event_type == 'invoice.paid':
            _handle_invoice_paid(parsed)
        
        elif event_type == 'invoice.payment_failed':
            _handle_payment_failed(parsed)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        logger.error("billing_webhook_error", error=str(e))
        return jsonify({'error': 'Webhook processing failed'}), 500


def _handle_checkout_completed(data: dict):
    """Handle checkout.session.completed event"""
    customer_id = data.get('customer_id')
    subscription_id = data.get('subscription_id')
    plan = data.get('plan')
    
    subscription = Subscription.query.filter_by(
        stripe_customer_id=customer_id
    ).first()
    
    if subscription:
        subscription.stripe_subscription_id = subscription_id
        subscription.status = 'active'
        subscription.plan = plan or subscription.plan
        subscription.tokens_limit = Subscription.PLAN_LIMITS.get(plan, 3)
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Send welcome email
        user = User.query.get(subscription.user_id)
        if user:
            send_subscription_email.delay(
                user.email,
                user.username,
                'created',
                {
                    'plan': plan.title() if plan else 'Pro',
                    'tokens_limit': subscription.tokens_limit,
                    'next_billing_date': subscription.current_period_end.strftime('%B %d, %Y')
                        if subscription.current_period_end else 'N/A'
                }
            )
        
        logger.info("checkout_completed", customer_id=customer_id, plan=plan)


def _handle_subscription_created(data: dict):
    """Handle customer.subscription.created event"""
    sub_data = data.get('subscription')
    if not sub_data:
        return
    
    subscription = Subscription.query.filter_by(
        stripe_customer_id=sub_data.customer_id
    ).first()
    
    if subscription:
        subscription.stripe_subscription_id = sub_data.id
        subscription.status = sub_data.status.value
        subscription.current_period_start = sub_data.current_period_start
        subscription.current_period_end = sub_data.current_period_end
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info("subscription_created_webhook", subscription_id=sub_data.id)


def _handle_subscription_updated(data: dict):
    """Handle customer.subscription.updated event"""
    sub_data = data.get('subscription')
    if not sub_data:
        return
    
    subscription = Subscription.query.filter_by(
        stripe_subscription_id=sub_data.id
    ).first()
    
    if subscription:
        subscription.status = sub_data.status.value
        subscription.current_period_start = sub_data.current_period_start
        subscription.current_period_end = sub_data.current_period_end
        subscription.cancel_at_period_end = sub_data.cancel_at_period_end
        subscription.canceled_at = sub_data.canceled_at
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info("subscription_updated_webhook", subscription_id=sub_data.id)


def _handle_subscription_deleted(data: dict):
    """Handle customer.subscription.deleted event"""
    sub_data = data.get('subscription')
    if not sub_data:
        return
    
    subscription = Subscription.query.filter_by(
        stripe_subscription_id=sub_data.id
    ).first()
    
    if subscription:
        subscription.status = 'canceled'
        subscription.canceled_at = datetime.utcnow()
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        logger.info("subscription_deleted_webhook", subscription_id=sub_data.id)


def _handle_invoice_paid(data: dict):
    """Handle invoice.paid event"""
    subscription = Subscription.query.filter_by(
        stripe_customer_id=data.get('customer_id')
    ).first()
    
    if subscription:
        # Record billing history
        billing = BillingHistory(
            subscription_id=subscription.id,
            stripe_invoice_id=data.get('invoice_id'),
            amount=int(data.get('amount', 0) * 100),  # Convert to cents
            currency='usd',
            status='paid',
            invoice_date=datetime.utcnow(),
            paid_at=datetime.utcnow()
        )
        db.session.add(billing)
        db.session.commit()
        
        logger.info("invoice_paid_webhook", invoice_id=data.get('invoice_id'))


def _handle_payment_failed(data: dict):
    """Handle invoice.payment_failed event"""
    subscription = Subscription.query.filter_by(
        stripe_customer_id=data.get('customer_id')
    ).first()
    
    if subscription:
        subscription.status = 'past_due'
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Send payment failed email
        user = User.query.get(subscription.user_id)
        if user:
            send_subscription_email.delay(
                user.email,
                user.username,
                'payment_failed',
                {'amount': f"{data.get('amount', 0):.2f}"}
            )
        
        logger.info("payment_failed_webhook", customer_id=data.get('customer_id'))


@billing_bp.route('/usage', methods=['GET'])
@jwt_required()
@rate_limit_read  # Usage stats
def get_usage():
    """Get current usage statistics"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        subscription = Subscription.query.filter_by(user_id=user.id).first()
        
        if not subscription:
            return jsonify({
                'tokens_used': 0,
                'tokens_limit': 0,
                'tokens_available': 0,
                'has_subscription': False
            })
        
        return jsonify({
            'tokens_used': subscription.tokens_used,
            'tokens_limit': subscription.tokens_limit,
            'tokens_available': subscription.tokens_limit - subscription.tokens_used,
            'has_subscription': subscription.is_active(),
            'plan': subscription.plan
        })
        
    except Exception as e:
        logger.error("get_usage_error", error=str(e))
        return jsonify({'error': 'Failed to get usage'}), 500
