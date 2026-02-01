"""
Document Routes for RWA-Studio
Author: Sowad Al-Mughni

Phase 3: IPFS Document Storage API Endpoints
"""

from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
import io
import structlog

from src.models.user import db, User
from src.models.token import TokenDeployment
from src.services.storage import get_storage_service

logger = structlog.get_logger()

documents_bp = Blueprint('documents', __name__, url_prefix='/api/documents')

# Allowed file types for document upload
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'image/png',
    'image/jpeg',
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document():
    """
    Upload a document to IPFS
    
    Form data:
    - file: The file to upload
    - token_id: Optional token deployment ID to associate with
    - document_type: Type of document (legal, prospectus, compliance, etc.)
    - description: Optional description
    """
    try:
        # Check if file is in request
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'error': 'File type not allowed',
                'allowed_types': list(ALLOWED_EXTENSIONS)
            }), 400
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        size = file.tell()
        file.seek(0)  # Seek back to start
        
        if size > MAX_FILE_SIZE:
            return jsonify({
                'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Get metadata from form
        token_id = request.form.get('token_id', type=int)
        document_type = request.form.get('document_type', 'general')
        description = request.form.get('description', '')
        
        # Get current user
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Prepare metadata
        metadata = {
            'document_type': document_type,
            'description': description,
            'uploaded_by': user.wallet_address if user else 'unknown',
            'uploaded_at': datetime.utcnow().isoformat(),
        }
        
        if token_id:
            token = TokenDeployment.query.get(token_id)
            if token:
                metadata['token_address'] = token.token_address
                metadata['token_name'] = token.token_name
        
        # Upload to IPFS
        storage_service = get_storage_service()
        
        try:
            result = storage_service.upload_file(
                file=file,
                filename=file.filename,
                metadata=metadata
            )
        except Exception as e:
            logger.error("document_upload_failed", error=str(e))
            return jsonify({'error': 'Failed to upload document to IPFS'}), 500
        
        # Update token with document hash if provided
        if token_id and token:
            token.document_hash = result.ipfs_hash
            db.session.commit()
        
        logger.info(
            "document_uploaded",
            ipfs_hash=result.ipfs_hash,
            filename=file.filename,
            size=result.size
        )
        
        return jsonify({
            'success': True,
            'ipfs_hash': result.ipfs_hash,
            'gateway_url': result.gateway_url,
            'filename': result.name,
            'size': result.size,
            'document_type': document_type
        }), 201
        
    except Exception as e:
        logger.error("document_upload_error", error=str(e))
        return jsonify({'error': 'Failed to upload document'}), 500


@documents_bp.route('/upload-json', methods=['POST'])
@jwt_required()
def upload_json():
    """
    Upload JSON metadata to IPFS
    
    Request body:
    {
        "name": "Token Metadata",
        "data": {...},
        "token_id": 123  // optional
    }
    """
    try:
        data = request.get_json()
        
        if not data.get('name') or not data.get('data'):
            return jsonify({'error': 'name and data are required'}), 400
        
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        # Prepare metadata
        metadata = {
            'uploaded_by': user.wallet_address if user else 'unknown',
            'uploaded_at': datetime.utcnow().isoformat(),
        }
        
        token_id = data.get('token_id')
        if token_id:
            token = TokenDeployment.query.get(token_id)
            if token:
                metadata['token_address'] = token.token_address
        
        # Upload to IPFS
        storage_service = get_storage_service()
        
        try:
            result = storage_service.upload_json(
                data=data['data'],
                name=data['name'],
                metadata=metadata
            )
        except Exception as e:
            logger.error("json_upload_failed", error=str(e))
            return jsonify({'error': 'Failed to upload JSON to IPFS'}), 500
        
        logger.info(
            "json_uploaded",
            ipfs_hash=result.ipfs_hash,
            name=data['name']
        )
        
        return jsonify({
            'success': True,
            'ipfs_hash': result.ipfs_hash,
            'gateway_url': result.gateway_url,
            'name': result.name,
            'size': result.size
        }), 201
        
    except Exception as e:
        logger.error("json_upload_error", error=str(e))
        return jsonify({'error': 'Failed to upload JSON'}), 500


@documents_bp.route('/<ipfs_hash>', methods=['GET'])
def get_document(ipfs_hash: str):
    """
    Get document from IPFS
    
    Returns the document file directly.
    """
    try:
        storage_service = get_storage_service()
        
        # Get document metadata first
        doc_metadata = storage_service.get_metadata(ipfs_hash)
        
        # Get document content
        try:
            content = storage_service.get_file(ipfs_hash)
        except Exception as e:
            logger.error("document_fetch_failed", error=str(e), ipfs_hash=ipfs_hash)
            return jsonify({'error': 'Failed to fetch document from IPFS'}), 404
        
        # Determine content type
        content_type = 'application/octet-stream'
        if doc_metadata and doc_metadata.name:
            ext = doc_metadata.name.rsplit('.', 1)[-1].lower()
            content_types = {
                'pdf': 'application/pdf',
                'png': 'image/png',
                'jpg': 'image/jpeg',
                'jpeg': 'image/jpeg',
                'json': 'application/json',
                'doc': 'application/msword',
                'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            }
            content_type = content_types.get(ext, content_type)
        
        return send_file(
            io.BytesIO(content),
            mimetype=content_type,
            as_attachment=False,
            download_name=doc_metadata.name if doc_metadata else ipfs_hash
        )
        
    except Exception as e:
        logger.error("document_get_error", error=str(e), ipfs_hash=ipfs_hash)
        return jsonify({'error': 'Failed to get document'}), 500


@documents_bp.route('/<ipfs_hash>/metadata', methods=['GET'])
def get_document_metadata(ipfs_hash: str):
    """Get metadata for a document by IPFS hash"""
    try:
        storage_service = get_storage_service()
        
        doc = storage_service.get_metadata(ipfs_hash)
        
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        return jsonify({
            'ipfs_hash': doc.ipfs_hash,
            'name': doc.name,
            'size': doc.size,
            'gateway_url': doc.gateway_url,
            'pin_date': doc.pin_date.isoformat() if doc.pin_date else None,
            'metadata': doc.metadata
        })
        
    except Exception as e:
        logger.error("document_metadata_error", error=str(e), ipfs_hash=ipfs_hash)
        return jsonify({'error': 'Failed to get document metadata'}), 500


@documents_bp.route('/list', methods=['GET'])
@jwt_required()
def list_documents():
    """List pinned documents (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role not in ['admin', 'transfer_agent']:
            return jsonify({'error': 'Unauthorized'}), 403
        
        limit = request.args.get('limit', 20, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        storage_service = get_storage_service()
        
        # Check if service supports listing
        if hasattr(storage_service, 'list_pins'):
            docs = storage_service.list_pins(limit=limit, offset=offset)
            
            return jsonify({
                'documents': [
                    {
                        'ipfs_hash': doc.ipfs_hash,
                        'name': doc.name,
                        'size': doc.size,
                        'gateway_url': doc.gateway_url,
                        'pin_date': doc.pin_date.isoformat() if doc.pin_date else None,
                        'metadata': doc.metadata
                    }
                    for doc in docs
                ],
                'limit': limit,
                'offset': offset
            })
        else:
            return jsonify({
                'error': 'Document listing not supported by storage provider'
            }), 501
        
    except Exception as e:
        logger.error("document_list_error", error=str(e))
        return jsonify({'error': 'Failed to list documents'}), 500


@documents_bp.route('/<ipfs_hash>', methods=['DELETE'])
@jwt_required()
def delete_document(ipfs_hash: str):
    """Unpin a document from IPFS (admin only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or user.role != 'admin':
            return jsonify({'error': 'Unauthorized'}), 403
        
        storage_service = get_storage_service()
        
        success = storage_service.unpin(ipfs_hash)
        
        if success:
            logger.info("document_unpinned", ipfs_hash=ipfs_hash, by=user.username)
            return jsonify({'success': True, 'message': 'Document unpinned'})
        else:
            return jsonify({'error': 'Failed to unpin document'}), 500
        
    except Exception as e:
        logger.error("document_delete_error", error=str(e), ipfs_hash=ipfs_hash)
        return jsonify({'error': 'Failed to delete document'}), 500


@documents_bp.route('/verify/<ipfs_hash>', methods=['GET'])
def verify_document(ipfs_hash: str):
    """
    Verify a document exists and is pinned
    
    Returns verification status and basic metadata.
    """
    try:
        storage_service = get_storage_service()
        
        doc = storage_service.get_metadata(ipfs_hash)
        
        return jsonify({
            'verified': doc is not None,
            'ipfs_hash': ipfs_hash,
            'gateway_url': storage_service.get_gateway_url(ipfs_hash),
            'size': doc.size if doc else None,
            'pin_date': doc.pin_date.isoformat() if doc and doc.pin_date else None
        })
        
    except Exception as e:
        logger.error("document_verify_error", error=str(e), ipfs_hash=ipfs_hash)
        return jsonify({
            'verified': False,
            'ipfs_hash': ipfs_hash,
            'error': 'Failed to verify document'
        })
