"""
Public Asset Page API Routes for RWA-Studio
Author: Sowad Al-Mughni
Phase 4: Growth Features

Dynamic asset page serving with social meta tags and referral tracking.
"""

from flask import Blueprint, request, jsonify, Response, render_template_string
from datetime import datetime, date
from sqlalchemy import func
from src.models.token import db, TokenDeployment, VerifiedAddress, ComplianceEvent
from src.models.referral import Referral, ShareEvent, AssetPageView, AssetPageTemplate
import json
import hashlib

assets_bp = Blueprint('assets', __name__)


# ============================================================================
# PUBLIC ASSET PAGE ENDPOINTS
# ============================================================================

@assets_bp.route('/<token_address>', methods=['GET'])
def get_asset_page(token_address):
    """
    Get public asset page data for a token
    Tracks page views and handles referral parameters
    """
    # Track referral if present
    ref_code = request.args.get('ref')
    utm_source = request.args.get('utm_source')
    utm_medium = request.args.get('utm_medium')
    utm_campaign = request.args.get('utm_campaign')
    
    # Look up token
    token = TokenDeployment.query.filter_by(token_address=token_address).first()
    
    if not token:
        return jsonify({'success': False, 'error': 'Token not found'}), 404
    
    # Track page view
    _track_page_view(token, ref_code, utm_source, utm_medium, utm_campaign, request)
    
    # Track referral click if present
    if ref_code:
        _track_referral_click(ref_code)
    
    # Get verification stats
    verified_count = VerifiedAddress.query.filter_by(
        token_deployment_id=token.id,
        is_active=True
    ).count()
    
    # Get recent compliance events count
    recent_events = ComplianceEvent.query.filter_by(
        token_deployment_id=token.id
    ).count()
    
    # Build page data
    page_data = {
        'token': token.to_dict(),
        'stats': {
            'verified_investors': verified_count,
            'compliance_events': recent_events
        },
        'badges': _generate_badges(token),
        'share_urls': _generate_share_urls(token_address, request.host_url),
        'embed_codes': _generate_embed_codes(token, request.host_url)
    }
    
    return jsonify({
        'success': True,
        'data': page_data
    })


@assets_bp.route('/<token_address>/html', methods=['GET'])
def get_asset_page_html(token_address):
    """
    Get rendered HTML asset page (for iframe embedding or SSR)
    """
    template_name = request.args.get('template', 'default')
    
    token = TokenDeployment.query.filter_by(token_address=token_address).first()
    
    if not token:
        return Response("Token not found", status=404, mimetype='text/plain')
    
    # Get template
    template = AssetPageTemplate.query.filter_by(name=template_name, is_active=True).first()
    
    # Generate HTML
    html = _generate_asset_page_html(token, template)
    
    response = Response(html, mimetype='text/html')
    response.headers['Cache-Control'] = 'public, max-age=300'  # 5 min cache
    
    return response


@assets_bp.route('/<token_address>/og-image.png', methods=['GET'])
def get_og_image(token_address):
    """
    Generate Open Graph image for social sharing
    Returns a placeholder for now - would use image generation in production
    """
    token = TokenDeployment.query.filter_by(token_address=token_address).first()
    
    if not token:
        return jsonify({'success': False, 'error': 'Token not found'}), 404
    
    # In production, this would generate an actual image
    # For now, return metadata for frontend to handle
    return jsonify({
        'success': True,
        'data': {
            'token_name': token.token_name,
            'token_symbol': token.token_symbol,
            'asset_type': token.asset_type,
            'framework': token.regulatory_framework,
            'message': 'OG image generation would be handled by image service'
        }
    })


# ============================================================================
# SHARE & REFERRAL ENDPOINTS
# ============================================================================

@assets_bp.route('/<token_address>/share', methods=['POST'])
def track_share(token_address):
    """Track a share event for analytics"""
    token = TokenDeployment.query.filter_by(token_address=token_address).first()
    
    if not token:
        return jsonify({'success': False, 'error': 'Token not found'}), 404
    
    data = request.get_json() or {}
    
    # Create share event
    share_event = ShareEvent(
        token_deployment_id=token.id,
        share_type='share_click',
        platform=data.get('platform', 'direct'),
        referral_code=data.get('ref'),
        utm_source=data.get('utm_source'),
        utm_medium=data.get('utm_medium'),
        utm_campaign=data.get('utm_campaign'),
        visitor_id=_hash_visitor_id(request),
        device_type=_detect_device_type(request.user_agent.string if request.user_agent else ''),
        user_agent=str(request.user_agent)[:500] if request.user_agent else None,
        referer=request.referrer[:500] if request.referrer else None
    )
    
    db.session.add(share_event)
    db.session.commit()
    
    # Generate share URLs with UTM parameters
    share_urls = _generate_share_urls(token_address, request.host_url, data.get('ref'))
    
    return jsonify({
        'success': True,
        'data': {
            'share_id': share_event.id,
            'share_urls': share_urls
        }
    })


@assets_bp.route('/referral/create', methods=['POST'])
def create_referral():
    """Create a new referral code for a user"""
    data = request.get_json() or {}
    
    referrer_address = data.get('referrer_address')
    token_deployment_id = data.get('token_deployment_id')
    
    if not referrer_address:
        return jsonify({'success': False, 'error': 'referrer_address is required'}), 400
    
    # Check for existing active referral code
    existing = Referral.query.filter_by(
        referrer_address=referrer_address,
        token_deployment_id=token_deployment_id,
        is_active=True
    ).first()
    
    if existing:
        return jsonify({
            'success': True,
            'data': existing.to_dict()
        })
    
    # Create new referral
    referral = Referral(
        referral_code=Referral.generate_code(),
        referrer_address=referrer_address,
        token_deployment_id=token_deployment_id,
        reward_type='credit',
        reward_amount=100.0  # $100 credit per referral
    )
    
    db.session.add(referral)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': referral.to_dict()
    }), 201


@assets_bp.route('/referral/<code>/stats', methods=['GET'])
def get_referral_stats(code):
    """Get statistics for a referral code"""
    referral = Referral.query.filter_by(referral_code=code).first()
    
    if not referral:
        return jsonify({'success': False, 'error': 'Referral code not found'}), 404
    
    return jsonify({
        'success': True,
        'data': referral.to_dict()
    })


# ============================================================================
# TEMPLATE ENDPOINTS
# ============================================================================

@assets_bp.route('/templates', methods=['GET'])
def get_templates():
    """Get all available asset page templates"""
    asset_type = request.args.get('asset_type')
    include_premium = request.args.get('include_premium', 'true').lower() == 'true'
    
    query = AssetPageTemplate.query.filter_by(is_active=True)
    
    if asset_type:
        query = query.filter(
            (AssetPageTemplate.asset_type == asset_type) | 
            (AssetPageTemplate.asset_type == None)
        )
    
    if not include_premium:
        query = query.filter_by(is_premium=False)
    
    templates = query.all()
    
    return jsonify({
        'success': True,
        'data': {
            'templates': [t.to_dict() for t in templates]
        }
    })


@assets_bp.route('/templates/<name>', methods=['GET'])
def get_template(name):
    """Get a specific template by name"""
    template = AssetPageTemplate.query.filter_by(name=name, is_active=True).first()
    
    if not template:
        return jsonify({'success': False, 'error': 'Template not found'}), 404
    
    return jsonify({
        'success': True,
        'data': template.to_dict()
    })


# ============================================================================
# ANALYTICS ENDPOINTS
# ============================================================================

@assets_bp.route('/<token_address>/analytics', methods=['GET'])
def get_asset_analytics(token_address):
    """Get analytics for an asset page"""
    token = TokenDeployment.query.filter_by(token_address=token_address).first()
    
    if not token:
        return jsonify({'success': False, 'error': 'Token not found'}), 404
    
    days = request.args.get('days', 30, type=int)
    
    # Get page views for the period
    page_views = AssetPageView.query.filter_by(
        token_deployment_id=token.id
    ).order_by(AssetPageView.view_date.desc()).limit(days).all()
    
    # Get share events
    share_events = ShareEvent.query.filter_by(
        token_deployment_id=token.id
    ).count()
    
    # Calculate totals
    total_views = sum(pv.page_views for pv in page_views)
    total_unique = sum(pv.unique_visitors for pv in page_views)
    total_badge_impressions = sum(pv.badge_impressions for pv in page_views)
    
    return jsonify({
        'success': True,
        'data': {
            'summary': {
                'total_page_views': total_views,
                'unique_visitors': total_unique,
                'badge_impressions': total_badge_impressions,
                'share_events': share_events
            },
            'daily': [pv.to_dict() for pv in page_views]
        }
    })


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _generate_badges(token):
    """Generate badge data for a token"""
    badges = [
        {
            'name': 'ERC-3643 Compliant',
            'icon': '🔒',
            'color': '#22c55e',
            'description': 'Token implements the ERC-3643 standard'
        },
        {
            'name': 'RWA-Studio Verified',
            'icon': '🛡️',
            'color': '#6366f1',
            'description': 'Token created and verified by RWA-Studio'
        }
    ]
    
    # Add regulatory framework badge
    framework = token.regulatory_framework.lower().replace(' ', '-')
    framework_badges = {
        'reg-d': {'name': 'Regulation D', 'icon': '📜', 'color': '#3b82f6'},
        'reg-s': {'name': 'Regulation S', 'icon': '🌍', 'color': '#8b5cf6'},
        'reg-cf': {'name': 'Regulation CF', 'icon': '👥', 'color': '#f59e0b'},
        'reg-a': {'name': 'Regulation A+', 'icon': '📊', 'color': '#10b981'}
    }
    
    if framework in framework_badges:
        badges.insert(1, framework_badges[framework])
    
    return badges


def _generate_share_urls(token_address, host_url, ref_code=None):
    """Generate share URLs for different platforms"""
    base_url = f"{host_url.rstrip('/')}/assets/{token_address}"
    
    if ref_code:
        base_url = f"{base_url}?ref={ref_code}"
    
    return {
        'direct': base_url,
        'twitter': f"https://twitter.com/intent/tweet?url={base_url}&text=Check out this tokenized asset on RWA-Studio",
        'linkedin': f"https://www.linkedin.com/sharing/share-offsite/?url={base_url}",
        'email': f"mailto:?subject=RWA Investment Opportunity&body=Check out this tokenized asset: {base_url}",
        'telegram': f"https://t.me/share/url?url={base_url}&text=Check out this tokenized asset on RWA-Studio"
    }


def _generate_embed_codes(token, host_url):
    """Generate embed codes for asset badges"""
    base_url = host_url.rstrip('/')
    badge_url = f"{base_url}/api/badge/{token.token_address}.svg"
    page_url = f"{base_url}/assets/{token.token_address}"
    
    return {
        'html': f'<a href="{page_url}"><img src="{badge_url}" alt="{token.token_name} - Verified by RWA-Studio" /></a>',
        'markdown': f'[![{token.token_name}]({badge_url})]({page_url})'
    }


def _track_page_view(token, ref_code, utm_source, utm_medium, utm_campaign, request):
    """Track page view in analytics"""
    today = date.today()
    
    # Get or create today's record
    page_view = AssetPageView.query.filter_by(
        token_deployment_id=token.id,
        view_date=today
    ).first()
    
    if not page_view:
        page_view = AssetPageView(
            token_deployment_id=token.id,
            view_date=today,
            source_breakdown='{}'
        )
        db.session.add(page_view)
    
    # Increment view count
    page_view.page_views += 1
    
    # Update source breakdown
    source = utm_source or ('referral' if ref_code else 'direct')
    breakdown = json.loads(page_view.source_breakdown or '{}')
    breakdown[source] = breakdown.get(source, 0) + 1
    page_view.source_breakdown = json.dumps(breakdown)
    
    # Create share event record
    share_event = ShareEvent(
        token_deployment_id=token.id,
        share_type='page_view',
        platform=source,
        referral_code=ref_code,
        utm_source=utm_source,
        utm_medium=utm_medium,
        utm_campaign=utm_campaign,
        visitor_id=_hash_visitor_id(request),
        device_type=_detect_device_type(request.user_agent.string if request.user_agent else ''),
        user_agent=str(request.user_agent)[:500] if request.user_agent else None,
        referer=request.referrer[:500] if request.referrer else None
    )
    db.session.add(share_event)
    
    db.session.commit()


def _track_referral_click(ref_code):
    """Track a referral code click"""
    referral = Referral.query.filter_by(referral_code=ref_code, is_active=True).first()
    if referral:
        referral.clicks += 1
        db.session.commit()


def _hash_visitor_id(request):
    """Create an anonymized visitor ID from request data"""
    data = f"{request.remote_addr}-{request.user_agent}"
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def _detect_device_type(user_agent):
    """Detect device type from user agent"""
    user_agent = user_agent.lower()
    if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
        return 'mobile'
    elif 'tablet' in user_agent or 'ipad' in user_agent:
        return 'tablet'
    return 'desktop'


def _generate_asset_page_html(token, template=None):
    """Generate HTML for asset page"""
    # Default colors
    primary_color = template.primary_color if template else '#3b82f6'
    secondary_color = template.secondary_color if template else '#6366f1'
    
    badges = _generate_badges(token)
    badges_html = ''.join([
        f'<span class="badge" style="border-color: {b["color"]}">{b["icon"]} {b["name"]}</span>'
        for b in badges
    ])
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{token.token_name} ({token.token_symbol}) - RWA-Studio</title>
    <meta name="description" content="Tokenized {token.asset_type} - {token.regulatory_framework} compliant security token">
    
    <!-- Open Graph -->
    <meta property="og:type" content="website">
    <meta property="og:title" content="{token.token_name} - Tokenized {token.asset_type}">
    <meta property="og:description" content="ERC-3643 compliant security token verified by RWA-Studio">
    <meta property="og:image" content="/api/assets/{token.token_address}/og-image.png">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{token.token_name} ({token.token_symbol})">
    <meta name="twitter:description" content="Tokenized {token.asset_type} on RWA-Studio">
    
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
               background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); min-height: 100vh; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem; }}
        .hero {{ background: white; border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; 
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }}
        .hero h1 {{ font-size: 2rem; color: #111827; margin-bottom: 0.5rem; }}
        .symbol {{ color: {primary_color}; font-weight: 600; }}
        .badges {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 1rem 0; }}
        .badge {{ display: inline-flex; align-items: center; gap: 0.25rem; 
                 padding: 0.375rem 0.75rem; border-radius: 9999px; border: 2px solid;
                 background: white; font-size: 0.875rem; font-weight: 500; }}
        .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); 
                     gap: 1rem; margin-top: 1.5rem; }}
        .info-item {{ padding: 1rem; background: #f9fafb; border-radius: 0.5rem; }}
        .info-label {{ font-size: 0.75rem; color: #6b7280; text-transform: uppercase; }}
        .info-value {{ font-size: 1rem; font-weight: 600; color: #111827; margin-top: 0.25rem; }}
        footer {{ text-align: center; padding: 2rem; color: #6b7280; font-size: 0.875rem; }}
        footer a {{ color: {primary_color}; text-decoration: none; }}
        
        @media (max-width: 640px) {{
            .container {{ padding: 1rem; }}
            .hero {{ padding: 1.5rem; }}
            .hero h1 {{ font-size: 1.5rem; }}
            .info-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>{token.token_name} <span class="symbol">({token.token_symbol})</span></h1>
            <p style="color: #4b5563;">{token.description or f'Tokenized {token.asset_type} asset'}</p>
            
            <div class="badges">{badges_html}</div>
            
            <div class="info-grid">
                <div class="info-item">
                    <div class="info-label">Asset Type</div>
                    <div class="info-value">{token.asset_type.replace('-', ' ').title()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Framework</div>
                    <div class="info-value">{token.regulatory_framework.upper()}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Jurisdiction</div>
                    <div class="info-value">{token.jurisdiction}</div>
                </div>
                <div class="info-item">
                    <div class="info-label">Max Supply</div>
                    <div class="info-value">{token.max_supply}</div>
                </div>
            </div>
        </div>
        
        <footer>
            <p>🔒 ERC-3643 compliant token verified by <a href="/">RWA-Studio</a></p>
            <p style="margin-top: 0.5rem; font-size: 0.75rem;">
                Contract: {token.token_address[:10]}...{token.token_address[-8:]}
            </p>
        </footer>
    </div>
</body>
</html>'''
    
    return html
