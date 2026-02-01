"""
Referral and Share Tracking Models for RWA-Studio
Author: Sowad Al-Mughni
Phase 4: Growth Features

Models for tracking referrals, shares, and viral growth metrics.
"""

from src.models.user import db
from datetime import datetime
import json
import uuid


class Referral(db.Model):
    """Model for tracking referral relationships and rewards"""
    __tablename__ = 'referrals'
    
    id = db.Column(db.Integer, primary_key=True)
    referral_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    referrer_address = db.Column(db.String(42), nullable=False, index=True)
    referred_address = db.Column(db.String(42), nullable=True, index=True)  # Filled when someone converts
    token_deployment_id = db.Column(db.Integer, db.ForeignKey('token_deployments.id'), nullable=True)
    
    # Tracking
    clicks = db.Column(db.Integer, default=0)
    conversions = db.Column(db.Integer, default=0)
    
    # Rewards
    reward_type = db.Column(db.String(20), default='credit')  # credit, percentage, fixed
    reward_amount = db.Column(db.Float, default=0.0)
    reward_claimed = db.Column(db.Boolean, default=False)
    reward_claimed_date = db.Column(db.DateTime, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'referral_code': self.referral_code,
            'referrer_address': self.referrer_address,
            'referred_address': self.referred_address,
            'token_deployment_id': self.token_deployment_id,
            'clicks': self.clicks,
            'conversions': self.conversions,
            'reward_type': self.reward_type,
            'reward_amount': self.reward_amount,
            'reward_claimed': self.reward_claimed,
            'reward_claimed_date': self.reward_claimed_date.isoformat() if self.reward_claimed_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'conversion_rate': (self.conversions / self.clicks * 100) if self.clicks > 0 else 0
        }
    
    @staticmethod
    def generate_code():
        """Generate a unique referral code"""
        return uuid.uuid4().hex[:8].upper()


class ShareEvent(db.Model):
    """Model for tracking share events and engagement"""
    __tablename__ = 'share_events'
    
    id = db.Column(db.Integer, primary_key=True)
    token_deployment_id = db.Column(db.Integer, db.ForeignKey('token_deployments.id'), nullable=False)
    
    # Share details
    share_type = db.Column(db.String(20), nullable=False)  # page_view, share_click, embed_view, badge_view
    platform = db.Column(db.String(30), nullable=True)  # twitter, linkedin, email, embed, direct
    referral_code = db.Column(db.String(20), nullable=True)
    
    # UTM tracking
    utm_source = db.Column(db.String(50), nullable=True)
    utm_medium = db.Column(db.String(50), nullable=True)
    utm_campaign = db.Column(db.String(50), nullable=True)
    utm_content = db.Column(db.String(50), nullable=True)
    
    # Visitor info (anonymized)
    visitor_id = db.Column(db.String(64), nullable=True)  # Hashed identifier
    country_code = db.Column(db.String(2), nullable=True)
    device_type = db.Column(db.String(20), nullable=True)  # desktop, mobile, tablet
    
    # Metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_agent = db.Column(db.String(500), nullable=True)
    referer = db.Column(db.String(500), nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'token_deployment_id': self.token_deployment_id,
            'share_type': self.share_type,
            'platform': self.platform,
            'referral_code': self.referral_code,
            'utm_source': self.utm_source,
            'utm_medium': self.utm_medium,
            'utm_campaign': self.utm_campaign,
            'country_code': self.country_code,
            'device_type': self.device_type,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class AssetPageView(db.Model):
    """Model for tracking asset page analytics"""
    __tablename__ = 'asset_page_views'
    
    id = db.Column(db.Integer, primary_key=True)
    token_deployment_id = db.Column(db.Integer, db.ForeignKey('token_deployments.id'), nullable=False)
    
    # Daily aggregation
    view_date = db.Column(db.Date, nullable=False)
    
    # Metrics
    page_views = db.Column(db.Integer, default=0)
    unique_visitors = db.Column(db.Integer, default=0)
    badge_impressions = db.Column(db.Integer, default=0)
    share_clicks = db.Column(db.Integer, default=0)
    contact_clicks = db.Column(db.Integer, default=0)
    
    # Source breakdown (JSON)
    source_breakdown = db.Column(db.Text, nullable=True)  # {"direct": 10, "twitter": 5, ...}
    
    # Unique constraint for one record per token per day
    __table_args__ = (db.UniqueConstraint('token_deployment_id', 'view_date', name='unique_page_view_date'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'token_deployment_id': self.token_deployment_id,
            'view_date': self.view_date.isoformat() if self.view_date else None,
            'page_views': self.page_views,
            'unique_visitors': self.unique_visitors,
            'badge_impressions': self.badge_impressions,
            'share_clicks': self.share_clicks,
            'contact_clicks': self.contact_clicks,
            'source_breakdown': json.loads(self.source_breakdown) if self.source_breakdown else {}
        }


class AssetPageTemplate(db.Model):
    """Model for storing custom asset page templates"""
    __tablename__ = 'asset_page_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Template category
    asset_type = db.Column(db.String(50), nullable=True)  # null = universal
    
    # Template configuration (JSON)
    config = db.Column(db.Text, nullable=False)  # Sections, colors, layout
    
    # Styling
    primary_color = db.Column(db.String(7), default='#3b82f6')
    secondary_color = db.Column(db.String(7), default='#6366f1')
    background_type = db.Column(db.String(20), default='gradient')  # solid, gradient, image
    
    # Features
    show_badges = db.Column(db.Boolean, default=True)
    show_compliance = db.Column(db.Boolean, default=True)
    show_cta = db.Column(db.Boolean, default=True)
    show_documents = db.Column(db.Boolean, default=False)
    
    # Metadata
    is_premium = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'asset_type': self.asset_type,
            'config': json.loads(self.config) if self.config else {},
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'background_type': self.background_type,
            'show_badges': self.show_badges,
            'show_compliance': self.show_compliance,
            'show_cta': self.show_cta,
            'show_documents': self.show_documents,
            'is_premium': self.is_premium,
            'is_active': self.is_active
        }
