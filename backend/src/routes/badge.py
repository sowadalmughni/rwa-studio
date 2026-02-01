"""
Embeddable Badge API Routes for RWA-Studio
Author: Sowad Al-Mughni

SVG badge generation with aggressive caching for viral growth.

Security:
- Rate limiting on all endpoints
- Input sanitization for badge parameters
"""

from flask import Blueprint, Response, request, jsonify
from datetime import datetime
from src.models.token import db, TokenDeployment
from src.middleware.rate_limit import rate_limit_public
from src.middleware.validation import is_valid_ethereum_address, sanitize_string

badge_bp = Blueprint('badge', __name__)

# Badge configurations
BADGE_CONFIGS = {
    'erc3643': {
        'name': 'ERC-3643 Compliant',
        'icon': '🔒',
        'color': '#22c55e',
        'bg_color': '#f0fdf4'
    },
    'reg-d': {
        'name': 'Regulation D',
        'icon': '📜',
        'color': '#3b82f6',
        'bg_color': '#eff6ff'
    },
    'reg-s': {
        'name': 'Regulation S',
        'icon': '🌍',
        'color': '#8b5cf6',
        'bg_color': '#f5f3ff'
    },
    'reg-cf': {
        'name': 'Regulation CF',
        'icon': '👥',
        'color': '#f59e0b',
        'bg_color': '#fffbeb'
    },
    'reg-a': {
        'name': 'Regulation A+',
        'icon': '📊',
        'color': '#10b981',
        'bg_color': '#ecfdf5'
    },
    'verified': {
        'name': 'RWA-Studio Verified',
        'icon': '🛡️',
        'color': '#6366f1',
        'bg_color': '#eef2ff'
    },
    'compliant': {
        'name': 'Active Compliance',
        'icon': '✅',
        'color': '#06b6d4',
        'bg_color': '#ecfeff'
    }
}

BADGE_STYLES = {
    'flat': 'flat',
    'flat-square': 'flat-square',
    'plastic': 'plastic',
    'for-the-badge': 'for-the-badge'
}


def generate_svg_badge(label, message, color, bg_color, style='flat'):
    """Generate an SVG badge similar to shields.io style"""
    
    # Calculate text widths (approximate)
    label_width = len(label) * 7 + 10
    message_width = len(message) * 7 + 10
    total_width = label_width + message_width
    
    if style == 'for-the-badge':
        height = 28
        font_size = 11
        text_y = 17
        radius = 4
        label = label.upper()
        message = message.upper()
    else:
        height = 20
        font_size = 11
        text_y = 14
        radius = 3 if style == 'flat' else 0
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="{height}">
  <linearGradient id="smooth" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="round">
    <rect width="{total_width}" height="{height}" rx="{radius}" fill="#fff"/>
  </clipPath>
  <g clip-path="url(#round)">
    <rect width="{label_width}" height="{height}" fill="#555"/>
    <rect x="{label_width}" width="{message_width}" height="{height}" fill="{color}"/>
    <rect width="{total_width}" height="{height}" fill="url(#smooth)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="{font_size}">
    <text x="{label_width/2}" y="{text_y}" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width/2}" y="{text_y - 1}" fill="#fff">{label}</text>
    <text x="{label_width + message_width/2}" y="{text_y}" fill="#010101" fill-opacity=".3">{message}</text>
    <text x="{label_width + message_width/2}" y="{text_y - 1}" fill="#fff">{message}</text>
  </g>
</svg>'''
    
    return svg


def generate_token_badge_svg(token, badge_type='full', style='flat'):
    """Generate a complete token badge with multiple compliance indicators"""
    
    framework = token.regulatory_framework.lower().replace(' ', '-')
    framework_config = BADGE_CONFIGS.get(framework, BADGE_CONFIGS['verified'])
    
    # For simple badges, just return regulatory framework badge
    if badge_type == 'simple':
        return generate_svg_badge(
            'RWA-Studio',
            framework_config['name'],
            framework_config['color'],
            framework_config['bg_color'],
            style
        )
    
    # Full badge with token info
    if badge_type == 'token':
        return generate_svg_badge(
            token.token_symbol,
            f"✓ {framework_config['name']}",
            framework_config['color'],
            framework_config['bg_color'],
            style
        )
    
    # Compliance-focused badge
    return generate_svg_badge(
        'ERC-3643',
        f'{token.token_symbol} Verified',
        '#22c55e',
        '#f0fdf4',
        style
    )


@badge_bp.route('/<token_address>.svg', methods=['GET'])
@rate_limit_public  # Public badge generation - heavily cached
def get_badge_svg(token_address):
    """
    Generate SVG badge for a token
    
    Query params:
    - type: 'simple', 'token', 'full' (default: 'full')
    - style: 'flat', 'flat-square', 'plastic', 'for-the-badge' (default: 'flat')
    """
    # Validate token address format
    if not is_valid_ethereum_address(token_address):
        return Response("Invalid token address", status=400, mimetype='text/plain')
    
    badge_type = sanitize_string(request.args.get('type', 'full'), max_length=20)
    style = sanitize_string(request.args.get('style', 'flat'), max_length=20)
    
    # Validate style
    if style not in BADGE_STYLES:
        style = 'flat'
    
    # Look up token
    token = TokenDeployment.query.filter_by(token_address=token_address).first()
    
    if not token:
        # Return a "not found" badge
        svg = generate_svg_badge('RWA-Studio', 'Not Found', '#ef4444', '#fef2f2', style)
    else:
        svg = generate_token_badge_svg(token, badge_type, style)
    
    # Return SVG with aggressive caching (24 hours)
    response = Response(svg, mimetype='image/svg+xml')
    response.headers['Cache-Control'] = 'public, max-age=86400'
    response.headers['ETag'] = f'"{token_address}-{badge_type}-{style}"'
    
    return response


@badge_bp.route('/embed/<token_address>', methods=['GET'])
@rate_limit_public  # Public embed code
def get_embed_code(token_address):
    """
    Get embeddable HTML/Markdown code for a token badge
    """
    if not is_valid_ethereum_address(token_address):
        return jsonify({'success': False, 'error': 'Invalid token address'}), 400
    
    token = TokenDeployment.query.filter_by(token_address=token_address).first()
    
    if not token:
        return jsonify({'success': False, 'error': 'Token not found'}), 404
    
    base_url = request.host_url.rstrip('/')
    badge_url = f"{base_url}/api/badge/{token_address}.svg"
    page_url = f"{base_url}/assets/{token_address}"
    
    # Generate embed codes for different platforms
    embed_codes = {
        'html': f'<a href="{page_url}" target="_blank"><img src="{badge_url}" alt="{token.token_name} - Verified by RWA-Studio" /></a>',
        'markdown': f'[![{token.token_name} - Verified by RWA-Studio]({badge_url})]({page_url})',
        'bbcode': f'[url={page_url}][img]{badge_url}[/img][/url]',
        'rst': f'.. image:: {badge_url}\n   :target: {page_url}\n   :alt: {token.token_name} - Verified by RWA-Studio',
        'textile': f'!{badge_url}({token.token_name} - Verified by RWA-Studio)!:{page_url}',
    }
    
    # Badge URL variations
    badge_urls = {
        'default': f"{badge_url}",
        'simple': f"{badge_url}?type=simple",
        'token': f"{badge_url}?type=token",
        'flat_square': f"{badge_url}?style=flat-square",
        'for_the_badge': f"{badge_url}?style=for-the-badge",
    }
    
    return jsonify({
        'success': True,
        'data': {
            'token': {
                'address': token.token_address,
                'name': token.token_name,
                'symbol': token.token_symbol
            },
            'urls': {
                'badge': badge_url,
                'page': page_url,
                'variations': badge_urls
            },
            'embed_codes': embed_codes
        }
    })


@badge_bp.route('/preview', methods=['GET'])
@rate_limit_public  # Public preview
def preview_badges():
    """
    Preview all badge styles (for documentation)
    """
    styles = ['flat', 'flat-square', 'plastic', 'for-the-badge']
    types = ['simple', 'token', 'full']
    
    previews = []
    for style in styles:
        for badge_type in types:
            previews.append({
                'style': style,
                'type': badge_type,
                'example': generate_svg_badge('RWA-Studio', 'Regulation D', '#3b82f6', '#eff6ff', style)
            })
    
    return jsonify({
        'success': True,
        'data': {
            'styles': styles,
            'types': types,
            'previews': previews[:4]  # Just show style variations
        }
    })


@badge_bp.route('/types', methods=['GET'])
@rate_limit_public  # Public badge types
def get_badge_types():
    """Get all available badge types and their configurations"""
    return jsonify({
        'success': True,
        'data': {
            'badges': BADGE_CONFIGS,
            'styles': list(BADGE_STYLES.keys()),
            'types': ['simple', 'token', 'full']
        }
    })
