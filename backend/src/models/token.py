"""
Token model for RWA-Studio Transfer Agent Console
Author: Sowad Al-Mughni
"""

from src.models.user import db
from datetime import datetime
import json

class TokenDeployment(db.Model):
    """Model for tracking deployed RWA tokens"""
    __tablename__ = 'token_deployments'
    
    id = db.Column(db.Integer, primary_key=True)
    token_address = db.Column(db.String(42), unique=True, nullable=False, index=True)
    token_name = db.Column(db.String(100), nullable=False)
    token_symbol = db.Column(db.String(10), nullable=False)
    asset_type = db.Column(db.String(50), nullable=False)
    regulatory_framework = db.Column(db.String(20), nullable=False)
    jurisdiction = db.Column(db.String(10), nullable=False)
    max_supply = db.Column(db.String(50), nullable=False)  # Store as string to handle large numbers
    deployer_address = db.Column(db.String(42), nullable=False)
    compliance_address = db.Column(db.String(42), nullable=False)
    identity_registry_address = db.Column(db.String(42), nullable=False)
    deployment_tx_hash = db.Column(db.String(66), nullable=True)
    deployment_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    document_hash = db.Column(db.String(100), nullable=True)  # IPFS hash
    
    # Relationships
    verified_addresses = db.relationship('VerifiedAddress', backref='token_deployment', lazy=True, cascade='all, delete-orphan')
    compliance_events = db.relationship('ComplianceEvent', backref='token_deployment', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'token_address': self.token_address,
            'token_name': self.token_name,
            'token_symbol': self.token_symbol,
            'asset_type': self.asset_type,
            'regulatory_framework': self.regulatory_framework,
            'jurisdiction': self.jurisdiction,
            'max_supply': self.max_supply,
            'deployer_address': self.deployer_address,
            'compliance_address': self.compliance_address,
            'identity_registry_address': self.identity_registry_address,
            'deployment_tx_hash': self.deployment_tx_hash,
            'deployment_date': self.deployment_date.isoformat() if self.deployment_date else None,
            'is_active': self.is_active,
            'description': self.description,
            'document_hash': self.document_hash,
            'verified_addresses_count': len(self.verified_addresses),
            'compliance_events_count': len(self.compliance_events)
        }

class VerifiedAddress(db.Model):
    """Model for tracking verified addresses for each token"""
    __tablename__ = 'verified_addresses'
    
    id = db.Column(db.Integer, primary_key=True)
    token_deployment_id = db.Column(db.Integer, db.ForeignKey('token_deployments.id'), nullable=False)
    address = db.Column(db.String(42), nullable=False, index=True)
    verification_level = db.Column(db.String(20), nullable=False)  # basic, accredited, institutional
    jurisdiction = db.Column(db.String(10), nullable=False)
    verification_date = db.Column(db.DateTime, default=datetime.utcnow)
    expiration_date = db.Column(db.DateTime, nullable=False)
    identity_hash = db.Column(db.String(66), nullable=False)
    kyc_provider = db.Column(db.String(50), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Unique constraint to prevent duplicate addresses per token
    __table_args__ = (db.UniqueConstraint('token_deployment_id', 'address', name='unique_token_address'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'token_deployment_id': self.token_deployment_id,
            'address': self.address,
            'verification_level': self.verification_level,
            'jurisdiction': self.jurisdiction,
            'verification_date': self.verification_date.isoformat() if self.verification_date else None,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None,
            'identity_hash': self.identity_hash,
            'kyc_provider': self.kyc_provider,
            'is_active': self.is_active,
            'notes': self.notes,
            'is_expired': datetime.utcnow() > self.expiration_date if self.expiration_date else False
        }

class ComplianceEvent(db.Model):
    """Model for tracking compliance events and violations"""
    __tablename__ = 'compliance_events'
    
    id = db.Column(db.Integer, primary_key=True)
    token_deployment_id = db.Column(db.Integer, db.ForeignKey('token_deployments.id'), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # transfer_blocked, verification_expired, etc.
    from_address = db.Column(db.String(42), nullable=True)
    to_address = db.Column(db.String(42), nullable=True)
    amount = db.Column(db.String(50), nullable=True)  # Store as string for large numbers
    reason = db.Column(db.String(200), nullable=False)
    transaction_hash = db.Column(db.String(66), nullable=True)
    block_number = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    severity = db.Column(db.String(20), default='info')  # info, warning, error, critical
    resolved = db.Column(db.Boolean, default=False)
    resolved_by = db.Column(db.String(42), nullable=True)
    resolved_date = db.Column(db.DateTime, nullable=True)
    event_metadata = db.Column(db.Text, nullable=True)  # JSON string for additional data
    
    def to_dict(self):
        return {
            'id': self.id,
            'token_deployment_id': self.token_deployment_id,
            'event_type': self.event_type,
            'from_address': self.from_address,
            'to_address': self.to_address,
            'amount': self.amount,
            'reason': self.reason,
            'transaction_hash': self.transaction_hash,
            'block_number': self.block_number,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'severity': self.severity,
            'resolved': self.resolved,
            'resolved_by': self.resolved_by,
            'resolved_date': self.resolved_date.isoformat() if self.resolved_date else None,
            'metadata': json.loads(self.event_metadata) if self.event_metadata else None
        }

class TransferAgentUser(db.Model):
    """Model for transfer agent console users"""
    __tablename__ = 'transfer_agent_users'
    
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(42), unique=True, nullable=False, index=True)
    role = db.Column(db.String(20), nullable=False)  # admin, agent, viewer
    name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    organization = db.Column(db.String(100), nullable=True)
    permissions = db.Column(db.Text, nullable=True)  # JSON string for granular permissions
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'address': self.address,
            'role': self.role,
            'name': self.name,
            'email': self.email,
            'organization': self.organization,
            'permissions': json.loads(self.permissions) if self.permissions else None,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class TokenMetrics(db.Model):
    """Model for storing token metrics and analytics"""
    __tablename__ = 'token_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    token_deployment_id = db.Column(db.Integer, db.ForeignKey('token_deployments.id'), nullable=False)
    metric_date = db.Column(db.Date, nullable=False)
    total_supply = db.Column(db.String(50), nullable=False)
    total_holders = db.Column(db.Integer, default=0)
    verified_holders = db.Column(db.Integer, default=0)
    total_transfers = db.Column(db.Integer, default=0)
    blocked_transfers = db.Column(db.Integer, default=0)
    compliance_score = db.Column(db.Float, default=100.0)  # 0-100 compliance score
    
    # Unique constraint for one record per token per day
    __table_args__ = (db.UniqueConstraint('token_deployment_id', 'metric_date', name='unique_token_date'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'token_deployment_id': self.token_deployment_id,
            'metric_date': self.metric_date.isoformat() if self.metric_date else None,
            'total_supply': self.total_supply,
            'total_holders': self.total_holders,
            'verified_holders': self.verified_holders,
            'total_transfers': self.total_transfers,
            'blocked_transfers': self.blocked_transfers,
            'compliance_score': self.compliance_score
        }

