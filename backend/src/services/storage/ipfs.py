"""
Pinata IPFS Storage Service Implementation
https://docs.pinata.cloud/
"""

import json
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime
import httpx

from .service import StorageService, StoredDocument


def get_config():
    """Get configuration - imported here to avoid circular imports"""
    from src.config import Config
    return Config


class PinataStorageService(StorageService):
    """Pinata IPFS storage service implementation"""
    
    API_URL = "https://api.pinata.cloud"
    
    def __init__(self):
        config = get_config()
        self.api_key = config.PINATA_API_KEY
        self.secret_key = config.PINATA_SECRET_KEY
        self.jwt = config.PINATA_JWT
        self._gateway_url = config.IPFS_GATEWAY_URL
        
        # Use JWT if available, otherwise API key/secret
        if self.jwt:
            self.headers = {
                "Authorization": f"Bearer {self.jwt}"
            }
        elif self.api_key and self.secret_key:
            self.headers = {
                "pinata_api_key": self.api_key,
                "pinata_secret_api_key": self.secret_key
            }
        else:
            self.headers = {}
    
    @property
    def provider_name(self) -> str:
        return "pinata"
    
    @property
    def gateway_url(self) -> str:
        return self._gateway_url
    
    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StoredDocument:
        """Upload a file to IPFS via Pinata"""
        url = f"{self.API_URL}/pinning/pinFileToIPFS"
        
        # Prepare metadata
        pinata_metadata = {
            "name": filename
        }
        if metadata:
            pinata_metadata["keyvalues"] = metadata
        
        files = {
            "file": (filename, file)
        }
        
        data = {
            "pinataMetadata": json.dumps(pinata_metadata)
        }
        
        with httpx.Client() as client:
            response = client.post(
                url,
                headers=self.headers,
                files=files,
                data=data,
                timeout=120.0  # 2 minute timeout for large files
            )
            response.raise_for_status()
            result = response.json()
        
        return StoredDocument(
            ipfs_hash=result["IpfsHash"],
            name=filename,
            size=result.get("PinSize", 0),
            gateway_url=self.get_gateway_url(result["IpfsHash"]),
            pin_date=datetime.fromisoformat(result["Timestamp"].replace("Z", "+00:00"))
                if result.get("Timestamp") else datetime.utcnow(),
            metadata=metadata
        )
    
    def upload_json(
        self,
        data: Dict[str, Any],
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StoredDocument:
        """Upload JSON data to IPFS via Pinata"""
        url = f"{self.API_URL}/pinning/pinJSONToIPFS"
        
        payload = {
            "pinataContent": data,
            "pinataMetadata": {
                "name": name
            }
        }
        
        if metadata:
            payload["pinataMetadata"]["keyvalues"] = metadata
        
        headers = {**self.headers, "Content-Type": "application/json"}
        
        with httpx.Client() as client:
            response = client.post(
                url,
                headers=headers,
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
        
        return StoredDocument(
            ipfs_hash=result["IpfsHash"],
            name=name,
            size=result.get("PinSize", 0),
            gateway_url=self.get_gateway_url(result["IpfsHash"]),
            pin_date=datetime.fromisoformat(result["Timestamp"].replace("Z", "+00:00"))
                if result.get("Timestamp") else datetime.utcnow(),
            metadata=metadata
        )
    
    def get_file(self, ipfs_hash: str) -> bytes:
        """Retrieve a file from IPFS via gateway"""
        url = self.get_gateway_url(ipfs_hash)
        
        with httpx.Client() as client:
            response = client.get(url, timeout=60.0)
            response.raise_for_status()
            return response.content
    
    def get_metadata(self, ipfs_hash: str) -> Optional[StoredDocument]:
        """Get metadata for a pinned file"""
        url = f"{self.API_URL}/data/pinList"
        
        params = {
            "hashContains": ipfs_hash,
            "status": "pinned"
        }
        
        with httpx.Client() as client:
            response = client.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
        
        rows = result.get("rows", [])
        if not rows:
            return None
        
        pin = rows[0]
        return StoredDocument(
            ipfs_hash=pin["ipfs_pin_hash"],
            name=pin.get("metadata", {}).get("name", ""),
            size=pin.get("size", 0),
            gateway_url=self.get_gateway_url(pin["ipfs_pin_hash"]),
            pin_date=datetime.fromisoformat(pin["date_pinned"].replace("Z", "+00:00"))
                if pin.get("date_pinned") else None,
            metadata=pin.get("metadata", {}).get("keyvalues")
        )
    
    def unpin(self, ipfs_hash: str) -> bool:
        """Unpin a file from Pinata"""
        url = f"{self.API_URL}/pinning/unpin/{ipfs_hash}"
        
        with httpx.Client() as client:
            response = client.delete(
                url,
                headers=self.headers,
                timeout=30.0
            )
            return response.status_code == 200
    
    def list_pins(self, limit: int = 10, offset: int = 0) -> list:
        """List pinned files"""
        url = f"{self.API_URL}/data/pinList"
        
        params = {
            "status": "pinned",
            "pageLimit": limit,
            "pageOffset": offset
        }
        
        with httpx.Client() as client:
            response = client.get(
                url,
                headers=self.headers,
                params=params,
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
        
        return [
            StoredDocument(
                ipfs_hash=pin["ipfs_pin_hash"],
                name=pin.get("metadata", {}).get("name", ""),
                size=pin.get("size", 0),
                gateway_url=self.get_gateway_url(pin["ipfs_pin_hash"]),
                pin_date=datetime.fromisoformat(pin["date_pinned"].replace("Z", "+00:00"))
                    if pin.get("date_pinned") else None,
                metadata=pin.get("metadata", {}).get("keyvalues")
            )
            for pin in result.get("rows", [])
        ]
