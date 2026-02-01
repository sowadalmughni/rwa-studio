"""
Storage Service Module
Provides decentralized document storage via IPFS (Pinata)
"""

from .service import StorageService, StoredDocument
from .ipfs import PinataStorageService

_storage_service = None


def get_storage_service() -> StorageService:
    """Get the configured storage service instance"""
    global _storage_service
    if _storage_service is None:
        _storage_service = PinataStorageService()
    return _storage_service


__all__ = ['StorageService', 'StoredDocument', 'PinataStorageService', 'get_storage_service']
