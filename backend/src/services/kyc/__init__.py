"""
KYC Service Module
Provides identity verification via Onfido
"""

from .base import KYCService, KYCStatus, KYCResult
from .onfido import OnfidoKYCService

_kyc_service = None


def get_kyc_service() -> KYCService:
    """Get the configured KYC service instance"""
    global _kyc_service
    if _kyc_service is None:
        _kyc_service = OnfidoKYCService()
    return _kyc_service


__all__ = ['KYCService', 'KYCStatus', 'KYCResult', 'OnfidoKYCService', 'get_kyc_service']
