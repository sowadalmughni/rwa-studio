"""
Analytics Export API Routes for RWA-Studio
Author: Sowad Al-Mughni

Export analytics data in CSV and PDF formats.

Security:
- JWT authentication required
- Rate limiting on all endpoints
- Input validation
"""

from flask import Blueprint, request, jsonify, Response
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import desc, func
from src.models.token import db, TokenDeployment, TokenMetrics, ComplianceEvent, VerifiedAddress
from src.models.referral import AssetPageView, ShareEvent
from src.middleware.rate_limit import rate_limit_read
from src.middleware.validation import is_valid_ethereum_address
import csv
import io
import json

analytics_export_bp = Blueprint('analytics_export', __name__)


@analytics_export_bp.route('/export/<token_address>', methods=['GET'])
@jwt_required()
@rate_limit_read  # Analytics export
def export_analytics(token_address):
    """
    Export analytics data for a token
    
    Query params:
    - format: 'csv', 'json', 'pdf' (default: 'json')
    - days: number of days to include (default: 30)
    - type: 'metrics', 'compliance', 'page_views', 'all' (default: 'all')
    """
    # Validate token address format
    if not is_valid_ethereum_address(token_address):
        return jsonify({'success': False, 'error': 'Invalid token address format'}), 400
    
    export_format = request.args.get('format', 'json')
    
    # Validate format
    if export_format not in ['csv', 'json', 'pdf']:
        return jsonify({'success': False, 'error': 'Invalid format. Use csv, json, or pdf'}), 400
    
    days = request.args.get('days', 30, type=int)
    
    # Limit days range to prevent abuse
    if days < 1 or days > 365:
        return jsonify({'success': False, 'error': 'Days must be between 1 and 365'}), 400
    
    data_type = request.args.get('type', 'all')
    
    # Validate data type
    if data_type not in ['metrics', 'compliance', 'page_views', 'all']:
        return jsonify({'success': False, 'error': 'Invalid type'}), 400
    
    # Look up token
    token = TokenDeployment.query.filter_by(token_address=token_address).first()
    
    if not token:
        return jsonify({'success': False, 'error': 'Token not found'}), 404
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Gather data based on type
    export_data = {
        'token': {
            'address': token.token_address,
            'name': token.token_name,
            'symbol': token.token_symbol
        },
        'export_date': datetime.utcnow().isoformat(),
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'days': days
        }
    }
    
    if data_type in ['metrics', 'all']:
        export_data['metrics'] = _get_token_metrics(token.id, start_date)
    
    if data_type in ['compliance', 'all']:
        export_data['compliance'] = _get_compliance_data(token.id, start_date)
    
    if data_type in ['page_views', 'all']:
        export_data['page_views'] = _get_page_view_data(token.id, start_date)
    
    # Return in requested format
    if export_format == 'csv':
        return _export_as_csv(export_data, data_type)
    elif export_format == 'pdf':
        return _export_as_markdown_pdf(export_data, token)
    else:
        return jsonify({
            'success': True,
            'data': export_data
        })


@analytics_export_bp.route('/summary', methods=['GET'])
@jwt_required()
@rate_limit_read  # Analytics summary
def get_analytics_summary():
    """Get aggregate analytics summary across all tokens"""
    days = request.args.get('days', 30, type=int)
    
    # Limit days range
    if days < 1 or days > 365:
        return jsonify({'success': False, 'error': 'Days must be between 1 and 365'}), 400
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Total tokens
    total_tokens = TokenDeployment.query.filter_by(is_active=True).count()
    
    # Total verified addresses
    total_verified = VerifiedAddress.query.filter_by(is_active=True).count()
    
    # Compliance events summary
    compliance_summary = db.session.query(
        ComplianceEvent.event_type,
        func.count(ComplianceEvent.id).label('count')
    ).filter(
        ComplianceEvent.timestamp >= start_date
    ).group_by(ComplianceEvent.event_type).all()
    
    # Page views summary
    total_page_views = db.session.query(
        func.sum(AssetPageView.page_views)
    ).filter(
        AssetPageView.view_date >= start_date.date()
    ).scalar() or 0
    
    total_unique_visitors = db.session.query(
        func.sum(AssetPageView.unique_visitors)
    ).filter(
        AssetPageView.view_date >= start_date.date()
    ).scalar() or 0
    
    # Share events
    share_events = ShareEvent.query.filter(
        ShareEvent.timestamp >= start_date
    ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'period_days': days,
            'totals': {
                'tokens': total_tokens,
                'verified_addresses': total_verified,
                'page_views': total_page_views,
                'unique_visitors': total_unique_visitors,
                'share_events': share_events
            },
            'compliance_by_type': {
                event_type: count for event_type, count in compliance_summary
            }
        }
    })


@analytics_export_bp.route('/referral-report', methods=['GET'])
@jwt_required()
@rate_limit_read  # Referral report
def get_referral_report():
    """Get referral performance report"""
    from src.models.referral import Referral
    
    days = request.args.get('days', 30, type=int)
    
    # Limit days range
    if days < 1 or days > 365:
        return jsonify({'success': False, 'error': 'Days must be between 1 and 365'}), 400
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Top referrers
    top_referrers = db.session.query(
        Referral.referrer_address,
        func.sum(Referral.clicks).label('total_clicks'),
        func.sum(Referral.conversions).label('total_conversions')
    ).filter(
        Referral.created_at >= start_date
    ).group_by(
        Referral.referrer_address
    ).order_by(
        desc('total_conversions')
    ).limit(10).all()
    
    # Overall stats
    total_clicks = db.session.query(func.sum(Referral.clicks)).scalar() or 0
    total_conversions = db.session.query(func.sum(Referral.conversions)).scalar() or 0
    
    return jsonify({
        'success': True,
        'data': {
            'period_days': days,
            'totals': {
                'clicks': total_clicks,
                'conversions': total_conversions,
                'conversion_rate': (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
            },
            'top_referrers': [
                {
                    'address': r.referrer_address,
                    'clicks': r.total_clicks,
                    'conversions': r.total_conversions,
                    'conversion_rate': (r.total_conversions / r.total_clicks * 100) if r.total_clicks > 0 else 0
                }
                for r in top_referrers
            ]
        }
    })


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_token_metrics(token_id, start_date):
    """Get token metrics for export"""
    metrics = TokenMetrics.query.filter(
        TokenMetrics.token_deployment_id == token_id,
        TokenMetrics.metric_date >= start_date.date()
    ).order_by(TokenMetrics.metric_date).all()
    
    return [m.to_dict() for m in metrics]


def _get_compliance_data(token_id, start_date):
    """Get compliance events for export"""
    events = ComplianceEvent.query.filter(
        ComplianceEvent.token_deployment_id == token_id,
        ComplianceEvent.timestamp >= start_date
    ).order_by(ComplianceEvent.timestamp).all()
    
    # Summary by type
    summary = {}
    for event in events:
        if event.event_type not in summary:
            summary[event.event_type] = 0
        summary[event.event_type] += 1
    
    return {
        'summary': summary,
        'events': [e.to_dict() for e in events]
    }


def _get_page_view_data(token_id, start_date):
    """Get page view data for export"""
    views = AssetPageView.query.filter(
        AssetPageView.token_deployment_id == token_id,
        AssetPageView.view_date >= start_date.date()
    ).order_by(AssetPageView.view_date).all()
    
    total_views = sum(v.page_views for v in views)
    total_unique = sum(v.unique_visitors for v in views)
    
    return {
        'totals': {
            'page_views': total_views,
            'unique_visitors': total_unique
        },
        'daily': [v.to_dict() for v in views]
    }


def _export_as_csv(data, data_type):
    """Export data as CSV"""
    output = io.StringIO()
    
    if data_type == 'metrics' and 'metrics' in data:
        writer = csv.writer(output)
        writer.writerow(['Date', 'Total Supply', 'Total Holders', 'Verified Holders', 
                        'Total Transfers', 'Blocked Transfers', 'Compliance Score'])
        for m in data['metrics']:
            writer.writerow([
                m['metric_date'], m['total_supply'], m['total_holders'],
                m['verified_holders'], m['total_transfers'], m['blocked_transfers'],
                m['compliance_score']
            ])
    
    elif data_type == 'compliance' and 'compliance' in data:
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Event Type', 'From Address', 'To Address', 
                        'Reason', 'Severity', 'Resolved'])
        for e in data['compliance'].get('events', []):
            writer.writerow([
                e['timestamp'], e['event_type'], e['from_address'],
                e['to_address'], e['reason'], e['severity'], e['resolved']
            ])
    
    elif data_type == 'page_views' and 'page_views' in data:
        writer = csv.writer(output)
        writer.writerow(['Date', 'Page Views', 'Unique Visitors', 'Badge Impressions', 
                        'Share Clicks', 'Contact Clicks'])
        for v in data['page_views'].get('daily', []):
            writer.writerow([
                v['view_date'], v['page_views'], v['unique_visitors'],
                v['badge_impressions'], v['share_clicks'], v['contact_clicks']
            ])
    
    else:
        # Export all as JSON-like CSV
        writer = csv.writer(output)
        writer.writerow(['Data Type', 'JSON Data'])
        writer.writerow(['export', json.dumps(data)])
    
    output.seek(0)
    
    filename = f"rwa-studio-export-{data['token']['symbol']}-{data_type}.csv"
    
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Cache-Control': 'no-cache'
        }
    )


def _export_as_markdown_pdf(data, token):
    """Export data as Markdown (can be converted to PDF client-side)"""
    md = f"""# {token.token_name} ({token.token_symbol}) Analytics Report

**Export Date:** {data['export_date']}  
**Period:** {data['period']['start'][:10]} to {data['period']['end'][:10]} ({data['period']['days']} days)

---

## Token Information

| Property | Value |
|----------|-------|
| Token Address | `{token.token_address}` |
| Asset Type | {token.asset_type} |
| Regulatory Framework | {token.regulatory_framework} |
| Jurisdiction | {token.jurisdiction} |

"""

    if 'metrics' in data and data['metrics']:
        latest = data['metrics'][-1] if data['metrics'] else {}
        md += f"""
## Token Metrics (Latest)

| Metric | Value |
|--------|-------|
| Total Holders | {latest.get('total_holders', 'N/A')} |
| Verified Holders | {latest.get('verified_holders', 'N/A')} |
| Compliance Score | {latest.get('compliance_score', 'N/A')}% |
| Total Transfers | {latest.get('total_transfers', 'N/A')} |
| Blocked Transfers | {latest.get('blocked_transfers', 'N/A')} |

"""

    if 'compliance' in data:
        summary = data['compliance'].get('summary', {})
        md += f"""
## Compliance Events Summary

| Event Type | Count |
|------------|-------|
"""
        for event_type, count in summary.items():
            md += f"| {event_type} | {count} |\n"

    if 'page_views' in data:
        totals = data['page_views'].get('totals', {})
        md += f"""
## Page Analytics

| Metric | Value |
|--------|-------|
| Total Page Views | {totals.get('page_views', 0)} |
| Unique Visitors | {totals.get('unique_visitors', 0)} |

"""

    md += """
---

*Report generated by RWA-Studio*
"""

    filename = f"rwa-studio-report-{token.token_symbol}.md"
    
    return Response(
        md,
        mimetype='text/markdown',
        headers={
            'Content-Disposition': f'attachment; filename={filename}',
            'Cache-Control': 'no-cache'
        }
    )
