"""
KYC Service Base Class
Abstract interface for KYC provider integrations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime


class KYCStatus(Enum):
    """KYC verification status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_REVIEW = "requires_review"
    EXPIRED = "expired"


@dataclass
class KYCResult:
    """KYC verification result"""
    status: KYCStatus
    provider: str
    provider_check_id: str
    applicant_id: Optional[str] = None
    verification_level: Optional[int] = None
    country_code: Optional[str] = None
    rejection_reasons: Optional[list] = None
    completed_at: Optional[datetime] = None
    raw_response: Optional[Dict[str, Any]] = None


@dataclass
class ApplicantData:
    """Data for creating a KYC applicant"""
    first_name: str
    last_name: str
    email: str
    wallet_address: str
    country: Optional[str] = None
    date_of_birth: Optional[str] = None  # YYYY-MM-DD format


class KYCService(ABC):
    """Abstract base class for KYC service providers"""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the KYC provider"""
        pass
    
    @abstractmethod
    def create_applicant(self, applicant_data: ApplicantData) -> Dict[str, Any]:
        """
        Create a new applicant in the KYC system
        
        Returns:
            Dict containing applicant_id and any additional provider data
        """
        pass
    
    @abstractmethod
    def create_check(self, applicant_id: str, check_types: list = None) -> Dict[str, Any]:
        """
        Create a verification check for an applicant
        
        Args:
            applicant_id: The provider's applicant ID
            check_types: List of check types to run (e.g., ['identity', 'document'])
            
        Returns:
            Dict containing check_id and status
        """
        pass
    
    @abstractmethod
    def get_check_status(self, check_id: str) -> KYCResult:
        """
        Get the current status of a verification check
        
        Args:
            check_id: The provider's check ID
            
        Returns:
            KYCResult with current status and details
        """
        pass
    
    @abstractmethod
    def generate_sdk_token(self, applicant_id: str, referrer: str = "*/*") -> str:
        """
        Generate a token for the frontend SDK
        
        Args:
            applicant_id: The provider's applicant ID
            referrer: The referrer URL pattern
            
        Returns:
            SDK token string for frontend initialization
        """
        pass
    
    @abstractmethod
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """
        Verify the authenticity of a webhook payload
        
        Args:
            payload: Raw webhook payload
            signature: Webhook signature from headers
            
        Returns:
            True if signature is valid
        """
        pass
    
    @abstractmethod
    def parse_webhook(self, payload: Dict[str, Any]) -> KYCResult:
        """
        Parse a webhook payload into a KYCResult
        
        Args:
            payload: Parsed webhook payload
            
        Returns:
            KYCResult with status from webhook
        """
        pass
