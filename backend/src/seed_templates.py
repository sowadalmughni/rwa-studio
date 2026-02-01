"""
Seed Data Script for RWA-Studio
Author: Sowad Al-Mughni

Seeds the database with default asset page templates.
Run with: flask seed-templates (or import and call directly)
"""

import json
from src.models.user import db
from src.models.referral import AssetPageTemplate


def seed_templates():
    """Seed default asset page templates"""
    
    templates = [
        {
            'name': 'real-estate',
            'display_name': 'Real Estate Fund',
            'description': 'Professional template optimized for real estate investments with property showcase sections',
            'asset_type': 'real-estate',
            'config': json.dumps({
                'sections': ['hero', 'property_gallery', 'financials', 'location', 'compliance', 'cta'],
                'hero_style': 'image_background',
                'show_map': True,
                'show_documents': True,
                'accent_elements': ['property_highlights', 'roi_calculator']
            }),
            'primary_color': '#1e3a5f',
            'secondary_color': '#2563eb',
            'background_type': 'image',
            'show_badges': True,
            'show_compliance': True,
            'show_cta': True,
            'show_documents': True,
            'is_premium': False
        },
        {
            'name': 'private-equity',
            'display_name': 'Private Equity',
            'description': 'Sophisticated template for PE fund shares with financial metrics and team sections',
            'asset_type': 'private-equity',
            'config': json.dumps({
                'sections': ['hero', 'investment_thesis', 'portfolio', 'team', 'financials', 'compliance', 'cta'],
                'hero_style': 'minimal_dark',
                'show_performance': True,
                'show_team': True,
                'accent_elements': ['fund_metrics', 'vintage_chart']
            }),
            'primary_color': '#0f172a',
            'secondary_color': '#6366f1',
            'background_type': 'gradient',
            'show_badges': True,
            'show_compliance': True,
            'show_cta': True,
            'show_documents': True,
            'is_premium': False
        },
        {
            'name': 'debt-instrument',
            'display_name': 'Debt Instrument',
            'description': 'Clean template for bonds and loans with yield visualization and payment schedules',
            'asset_type': 'debt',
            'config': json.dumps({
                'sections': ['hero', 'yield_summary', 'payment_schedule', 'issuer_info', 'compliance', 'cta'],
                'hero_style': 'clean_minimal',
                'show_payment_calendar': True,
                'show_yield_curve': True,
                'accent_elements': ['coupon_rate', 'maturity_countdown']
            }),
            'primary_color': '#065f46',
            'secondary_color': '#10b981',
            'background_type': 'solid',
            'show_badges': True,
            'show_compliance': True,
            'show_cta': True,
            'show_documents': False,
            'is_premium': False
        },
        {
            'name': 'art-collectibles',
            'display_name': 'Art & Collectibles',
            'description': 'Visual-first template for art, collectibles, and luxury assets with provenance tracking',
            'asset_type': 'art',
            'config': json.dumps({
                'sections': ['hero_gallery', 'artwork_details', 'provenance', 'artist_bio', 'valuation', 'compliance', 'cta'],
                'hero_style': 'gallery_fullwidth',
                'show_3d_viewer': False,
                'show_provenance_timeline': True,
                'accent_elements': ['authenticity_badge', 'condition_report']
            }),
            'primary_color': '#7c2d12',
            'secondary_color': '#ea580c',
            'background_type': 'solid',
            'show_badges': True,
            'show_compliance': True,
            'show_cta': True,
            'show_documents': True,
            'is_premium': True
        },
        {
            'name': 'revenue-share',
            'display_name': 'Revenue Share',
            'description': 'Dynamic template for royalties and revenue-sharing tokens with earnings visualization',
            'asset_type': 'revenue-share',
            'config': json.dumps({
                'sections': ['hero', 'earnings_overview', 'revenue_breakdown', 'payout_history', 'projections', 'compliance', 'cta'],
                'hero_style': 'data_focused',
                'show_live_earnings': True,
                'show_distribution_chart': True,
                'accent_elements': ['earnings_ticker', 'next_payout']
            }),
            'primary_color': '#7c3aed',
            'secondary_color': '#a855f7',
            'background_type': 'gradient',
            'show_badges': True,
            'show_compliance': True,
            'show_cta': True,
            'show_documents': False,
            'is_premium': False
        },
        {
            'name': 'default',
            'display_name': 'Default',
            'description': 'Clean, professional template suitable for any asset type',
            'asset_type': None,
            'config': json.dumps({
                'sections': ['hero', 'details', 'compliance', 'cta'],
                'hero_style': 'standard',
                'accent_elements': []
            }),
            'primary_color': '#3b82f6',
            'secondary_color': '#6366f1',
            'background_type': 'gradient',
            'show_badges': True,
            'show_compliance': True,
            'show_cta': True,
            'show_documents': False,
            'is_premium': False
        },
        {
            'name': 'minimal',
            'display_name': 'Minimal',
            'description': 'Simplified template with essential information only',
            'asset_type': None,
            'config': json.dumps({
                'sections': ['hero', 'details', 'cta'],
                'hero_style': 'minimal',
                'accent_elements': []
            }),
            'primary_color': '#374151',
            'secondary_color': '#6b7280',
            'background_type': 'solid',
            'show_badges': True,
            'show_compliance': False,
            'show_cta': True,
            'show_documents': False,
            'is_premium': False
        }
    ]
    
    for template_data in templates:
        # Check if template exists
        existing = AssetPageTemplate.query.filter_by(name=template_data['name']).first()
        
        if existing:
            # Update existing template
            for key, value in template_data.items():
                setattr(existing, key, value)
        else:
            # Create new template
            template = AssetPageTemplate(**template_data)
            db.session.add(template)
    
    db.session.commit()
    print(f"✅ Seeded {len(templates)} asset page templates")
    return templates


if __name__ == '__main__':
    # For running directly
    from src.main import app
    with app.app_context():
        seed_templates()
