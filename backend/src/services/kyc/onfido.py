"""
Onfido KYC Service Implementation
https://documentation.onfido.com/
"""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from datetime import datetime
import httpx

from .base import KYCService, KYCStatus, KYCResult, ApplicantData


def get_config():
    """Get configuration - imported here to avoid circular imports"""
    from src.config import Config
    return Config


class OnfidoKYCService(KYCService):
    """Onfido KYC provider implementation"""
    
    def __init__(self):
        config = get_config()
        self.api_token = config.ONFIDO_API_TOKEN
        self.webhook_secret = config.ONFIDO_WEBHOOK_SECRET
        self.api_url = config.ONFIDO_API_URL
        self.region = config.ONFIDO_REGION
        
        self.headers = {
            "Authorization": f"Token token={self.api_token}",
            "Content-Type": "application/json",
        }
    
    @property
    def provider_name(self) -> str:
        return "onfido"
    
    def _request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make an HTTP request to the Onfido API"""
        url = f"{self.api_url}/{endpoint}"
        
        with httpx.Client() as client:
            if method == "GET":
                response = client.get(url, headers=self.headers)
            elif method == "POST":
                response = client.post(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
    
    def create_applicant(self, applicant_data: ApplicantData) -> Dict[str, Any]:
        """Create a new applicant in Onfido"""
        payload = {
            "first_name": applicant_data.first_name,
            "last_name": applicant_data.last_name,
            "email": applicant_data.email,
        }
        
        if applicant_data.country:
            payload["location"] = {"country_of_residence": applicant_data.country}
        
        if applicant_data.date_of_birth:
            payload["dob"] = applicant_data.date_of_birth
        
        result = self._request("POST", "applicants", payload)
        
        return {
            "applicant_id": result["id"],
            "wallet_address": applicant_data.wallet_address,
            "href": result.get("href"),
            "sandbox": result.get("sandbox", False),
        }
    
    def create_check(self, applicant_id: str, check_types: list = None) -> Dict[str, Any]:
        """Create a verification check for an applicant"""
        if check_types is None:
            check_types = ["document", "facial_similarity_photo"]
        
        payload = {
            "applicant_id": applicant_id,
            "report_names": check_types,
        }
        
        result = self._request("POST", "checks", payload)
        
        return {
            "check_id": result["id"],
            "status": result["status"],
            "result": result.get("result"),
            "href": result.get("href"),
        }
    
    def get_check_status(self, check_id: str) -> KYCResult:
        """Get the current status of a verification check"""
        result = self._request("GET", f"checks/{check_id}")
        
        status = self._map_status(result["status"], result.get("result"))
        
        rejection_reasons = None
        if status == KYCStatus.REJECTED and "reports" in result:
            rejection_reasons = [
                r.get("sub_result", r.get("result"))
                for r in result["reports"]
                if r.get("result") != "clear"
            ]
        
        return KYCResult(
            status=status,
            provider=self.provider_name,
            provider_check_id=check_id,
            applicant_id=result.get("applicant_id"),
            verification_level=self._determine_verification_level(result),
            country_code=self._extract_country(result),
            rejection_reasons=rejection_reasons,
            completed_at=datetime.fromisoformat(result["completed_at_iso8601"].replace("Z", "+00:00"))
                if result.get("completed_at_iso8601") else None,
            raw_response=result,
        )
    
    def generate_sdk_token(self, applicant_id: str, referrer: str = "*/*") -> str:
        """Generate a token for the Onfido Web SDK"""
        payload = {
            "applicant_id": applicant_id,
            "referrer": referrer,
        }
        
        result = self._request("POST", "sdk_token", payload)
        return result["token"]
    
    def verify_webhook(self, payload: bytes, signature: str) -> bool:
        """Verify the authenticity of an Onfido webhook"""
        if not self.webhook_secret:
            return False
        
        expected = hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected, signature)
    
    def parse_webhook(self, payload: Dict[str, Any]) -> KYCResult:
        """Parse an Onfido webhook payload"""
        event_type = payload.get("payload", {}).get("resource_type")
        action = payload.get("payload", {}).get("action")
        
        if event_type == "check" and action == "check.completed":
            check_data = payload["payload"]["object"]
            return KYCResult(
                status=self._map_status(check_data["status"], check_data.get("result")),
                provider=self.provider_name,
                provider_check_id=check_data["id"],
                applicant_id=check_data.get("applicant_id"),
                verification_level=self._determine_verification_level(check_data),
                completed_at=datetime.fromisoformat(
                    check_data["completed_at_iso8601"].replace("Z", "+00:00")
                ) if check_data.get("completed_at_iso8601") else None,
                raw_response=payload,
            )
        
        # Return pending for other webhook types
        return KYCResult(
            status=KYCStatus.PENDING,
            provider=self.provider_name,
            provider_check_id=payload.get("payload", {}).get("object", {}).get("id", ""),
            raw_response=payload,
        )
    
    def _map_status(self, onfido_status: str, result: Optional[str] = None) -> KYCStatus:
        """Map Onfido status to KYCStatus enum"""
        if onfido_status == "complete":
            if result == "clear":
                return KYCStatus.APPROVED
            elif result == "consider":
                return KYCStatus.REQUIRES_REVIEW
            else:
                return KYCStatus.REJECTED
        elif onfido_status == "in_progress":
            return KYCStatus.IN_PROGRESS
        elif onfido_status == "withdrawn":
            return KYCStatus.EXPIRED
        else:
            return KYCStatus.PENDING
    
    def _determine_verification_level(self, check_data: Dict) -> int:
        """Determine verification level based on completed checks"""
        # Level 1: Basic identity
        # Level 2: Document verified
        # Level 3: Full verification (document + facial)
        
        reports = check_data.get("report_ids", [])
        if len(reports) >= 2 and check_data.get("result") == "clear":
            return 3
        elif len(reports) >= 1:
            return 2
        return 1
    
    def _extract_country(self, check_data: Dict) -> Optional[str]:
        """Extract country code from check data"""
        # This would typically come from document analysis
        return check_data.get("country_residence")
