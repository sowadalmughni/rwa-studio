"""
Storage Service Base Class
Abstract interface for decentralized storage integrations
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, Any, BinaryIO
from datetime import datetime


@dataclass
class StoredDocument:
    """Stored document metadata"""
    ipfs_hash: str
    name: str
    size: int  # bytes
    mime_type: Optional[str] = None
    gateway_url: Optional[str] = None
    pin_date: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class StorageService(ABC):
    """Abstract base class for storage service providers"""
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of the storage provider"""
        pass
    
    @property
    @abstractmethod
    def gateway_url(self) -> str:
        """Return the IPFS gateway URL"""
        pass
    
    @abstractmethod
    def upload_file(
        self,
        file: BinaryIO,
        filename: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StoredDocument:
        """
        Upload a file to IPFS
        
        Args:
            file: File-like object to upload
            filename: Name of the file
            metadata: Optional metadata to attach
            
        Returns:
            StoredDocument with IPFS hash and metadata
        """
        pass
    
    @abstractmethod
    def upload_json(
        self,
        data: Dict[str, Any],
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> StoredDocument:
        """
        Upload JSON data to IPFS
        
        Args:
            data: JSON-serializable data
            name: Name for the JSON file
            metadata: Optional metadata to attach
            
        Returns:
            StoredDocument with IPFS hash
        """
        pass
    
    @abstractmethod
    def get_file(self, ipfs_hash: str) -> bytes:
        """
        Retrieve a file from IPFS
        
        Args:
            ipfs_hash: The IPFS CID/hash
            
        Returns:
            File contents as bytes
        """
        pass
    
    @abstractmethod
    def get_metadata(self, ipfs_hash: str) -> Optional[StoredDocument]:
        """
        Get metadata for a pinned file
        
        Args:
            ipfs_hash: The IPFS CID/hash
            
        Returns:
            StoredDocument with metadata, or None if not found
        """
        pass
    
    @abstractmethod
    def unpin(self, ipfs_hash: str) -> bool:
        """
        Unpin a file from IPFS
        
        Args:
            ipfs_hash: The IPFS CID/hash
            
        Returns:
            True if successfully unpinned
        """
        pass
    
    def get_gateway_url(self, ipfs_hash: str) -> str:
        """Get the full gateway URL for an IPFS hash"""
        return f"{self.gateway_url}/{ipfs_hash}"
