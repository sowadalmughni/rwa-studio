"""
KYC Verification model for RWA-Studio
Author: Sowad Al-Mughni

Phase 3: KYC Provider Integration
"""

from src.models.user import db, utc_now
from datetime import datetime
import json


class KYCVerification(db.Model):
    """Model for tracking KYC verification status"""
    __tablename__ = 'kyc_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Wallet address being verified
    wallet_address = db.Column(db.String(42), nullable=False, index=True)
    
    # User association (optional - for registered users)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # Provider information
    provider = db.Column(db.String(20), nullable=False, default='onfido')  # onfido, jumio
    applicant_id = db.Column(db.String(100), nullable=True)  # Provider's applicant ID
    check_id = db.Column(db.String(100), nullable=True, index=True)  # Provider's check ID
    
    # Verification status
    status = db.Column(db.String(20), nullable=False, default='pending')
    # pending, in_progress, approved, rejected, requires_review, expired
    
    # Verification details
    verification_level = db.Column(db.Integer, default=1)  # 1-3
    country_code = db.Column(db.String(3), nullable=True)  # ISO country code
    
    # Personal information (stored securely)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(120), nullable=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    
    # Results
    rejection_reasons = db.Column(db.Text, nullable=True)  # JSON array of reasons
    result_data = db.Column(db.Text, nullable=True)  # Full result JSON
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)
    completed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('kyc_verifications', lazy=True))
    
    def __repr__(self):
        return f'<KYCVerification {self.id} - {self.wallet_address} ({self.status})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'provider': self.provider,
            'status': self.status,
            'verification_level': self.verification_level,
            'country_code': self.country_code,
            'rejection_reasons': self.get_rejection_reasons(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_valid': self.is_valid(),
        }
    
    def to_public_dict(self):
        """Return public-safe information (no PII)"""
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'status': self.status,
            'verification_level': self.verification_level,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'is_valid': self.is_valid(),
        }
    
    def get_rejection_reasons(self):
        """Get rejection reasons as list"""
        if not self.rejection_reasons:
            return []
        try:
            return json.loads(self.rejection_reasons)
        except json.JSONDecodeError:
            return [self.rejection_reasons]
    
    def set_rejection_reasons(self, reasons: list):
        """Set rejection reasons from list"""
        self.rejection_reasons = json.dumps(reasons)
    
    def get_result_data(self):
        """Get full result data as dict"""
        if not self.result_data:
            return {}
        try:
            return json.loads(self.result_data)
        except json.JSONDecodeError:
            return {}
    
    def set_result_data(self, data: dict):
        """Set result data from dict"""
        self.result_data = json.dumps(data)
    
    def is_valid(self) -> bool:
        """Check if verification is currently valid"""
        if self.status != 'approved':
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True
    
    def is_expired(self) -> bool:
        """Check if verification has expired"""
        if not self.expires_at:
            return False
        return self.expires_at < datetime.utcnow()
    
    @classmethod
    def get_valid_for_address(cls, wallet_address: str):
        """Get the latest valid verification for an address"""
        return cls.query.filter(
            cls.wallet_address == wallet_address.lower(),
            cls.status == 'approved',
            db.or_(cls.expires_at.is_(None), cls.expires_at > datetime.utcnow())
        ).order_by(cls.created_at.desc()).first()
    
    @classmethod
    def get_pending_for_address(cls, wallet_address: str):
        """Get pending verification for an address"""
        return cls.query.filter(
            cls.wallet_address == wallet_address.lower(),
            cls.status.in_(['pending', 'in_progress'])
        ).order_by(cls.created_at.desc()).first()


class KYCDocument(db.Model):
    """Model for tracking KYC documents uploaded"""
    __tablename__ = 'kyc_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    kyc_verification_id = db.Column(db.Integer, db.ForeignKey('kyc_verifications.id'), nullable=False)
    
    # Document details
    document_type = db.Column(db.String(50), nullable=False)  # passport, drivers_license, id_card
    provider_document_id = db.Column(db.String(100), nullable=True)
    
    # Storage (optional - for internal document storage)
    ipfs_hash = db.Column(db.String(100), nullable=True)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=utc_now)
    verified_at = db.Column(db.DateTime, nullable=True)
    
    # Relationship
    kyc_verification = db.relationship('KYCVerification', backref=db.backref('documents', lazy=True))
    
    def __repr__(self):
        return f'<KYCDocument {self.id} - {self.document_type} ({self.status})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'kyc_verification_id': self.kyc_verification_id,
            'document_type': self.document_type,
            'status': self.status,
            'rejection_reason': self.rejection_reason,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'verified_at': self.verified_at.isoformat() if self.verified_at else None,
        }
