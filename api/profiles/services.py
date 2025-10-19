"""
Profile services for Koroh platform.

This module defines services for CV processing, file validation,
storage management, and metadata extraction.
"""

import os
import mimetypes
import hashlib
from typing import Dict, Any, Optional
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class CVProcessingService:
    """
    Service for processing CV files including validation,
    storage, and metadata extraction.
    """
    
    # Allowed file extensions and their MIME types
    ALLOWED_EXTENSIONS = {
        'pdf': ['application/pdf'],
        'doc': ['application/msword'],
        'docx': [
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        ],
        'md': ['text/markdown', 'text/plain']
    }
    
    # Maximum file size (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def __init__(self):
        """Initialize the CV processing service."""
        self.logger = logging.getLogger(__name__)
    
    def validate_cv_file(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Validate uploaded CV file for security and format compliance.
        
        Args:
            file: The uploaded file to validate
            
        Returns:
            Dict containing validation results and file metadata
            
        Raises:
            ValidationError: If file validation fails
        """
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': [],
            'metadata': {}
        }
        
        try:
            # Check if file exists
            if not file:
                validation_result['errors'].append('No file provided')
                return validation_result
            
            # Check file size
            if file.size > self.MAX_FILE_SIZE:
                validation_result['errors'].append(
                    f'File size ({file.size} bytes) exceeds maximum allowed size '
                    f'({self.MAX_FILE_SIZE} bytes)'
                )
            
            # Get file extension
            file_extension = self._get_file_extension(file.name)
            if not file_extension:
                validation_result['errors'].append('File must have a valid extension')
                return validation_result
            
            # Check if extension is allowed
            if file_extension not in self.ALLOWED_EXTENSIONS:
                validation_result['errors'].append(
                    f'File extension "{file_extension}" is not allowed. '
                    f'Allowed extensions: {", ".join(self.ALLOWED_EXTENSIONS.keys())}'
                )
            
            # Validate MIME type
            mime_type = self._get_mime_type(file)
            allowed_mime_types = self.ALLOWED_EXTENSIONS.get(file_extension, [])
            
            if mime_type not in allowed_mime_types:
                validation_result['warnings'].append(
                    f'MIME type "{mime_type}" does not match expected types for '
                    f'"{file_extension}" files: {", ".join(allowed_mime_types)}'
                )
            
            # Generate file hash for duplicate detection
            file_hash = self._generate_file_hash(file)
            
            # Extract basic metadata
            validation_result['metadata'] = {
                'original_filename': file.name,
                'file_size': file.size,
                'file_extension': file_extension,
                'mime_type': mime_type,
                'file_hash': file_hash,
                'uploaded_at': timezone.now().isoformat(),
            }
            
            # If no errors, mark as valid
            if not validation_result['errors']:
                validation_result['is_valid'] = True
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating CV file: {str(e)}")
            validation_result['errors'].append(f'Validation error: {str(e)}')
            return validation_result
    
    def extract_cv_metadata(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Extract metadata from CV file.
        
        This is a basic implementation that extracts file-level metadata.
        In a full implementation, this would use document parsing libraries
        to extract content-based metadata.
        
        Args:
            file: The uploaded CV file
            
        Returns:
            Dict containing extracted metadata
        """
        try:
            metadata = {
                'extraction_timestamp': timezone.now().isoformat(),
                'file_info': {
                    'original_filename': file.name,
                    'file_size': file.size,
                    'file_extension': self._get_file_extension(file.name),
                    'mime_type': self._get_mime_type(file),
                },
                'content_analysis': {
                    'text_extracted': False,
                    'page_count': None,
                    'word_count': None,
                    'language': None,
                },
                'extracted_data': {
                    'personal_info': {},
                    'skills': [],
                    'experience': [],
                    'education': [],
                    'certifications': [],
                },
                'processing_notes': [
                    'Basic metadata extraction completed',
                    'Advanced content analysis requires AI integration'
                ]
            }
            
            # Add file-specific metadata based on extension
            file_extension = self._get_file_extension(file.name)
            
            if file_extension == 'pdf':
                metadata['content_analysis']['supports_text_extraction'] = True
                metadata['processing_notes'].append('PDF format supports text extraction')
            elif file_extension in ['doc', 'docx']:
                metadata['content_analysis']['supports_text_extraction'] = True
                metadata['processing_notes'].append('Word document format supports text extraction')
            elif file_extension == 'md':
                metadata['content_analysis']['supports_text_extraction'] = True
                metadata['content_analysis']['format'] = 'markdown'
                metadata['processing_notes'].append('Markdown format - plain text processing')
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"Error extracting CV metadata: {str(e)}")
            return {
                'extraction_timestamp': timezone.now().isoformat(),
                'error': str(e),
                'processing_notes': ['Metadata extraction failed']
            }
    
    def process_cv_upload(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Complete CV processing pipeline including validation and metadata extraction.
        
        Args:
            file: The uploaded CV file
            
        Returns:
            Dict containing processing results
        """
        try:
            # Validate file
            validation_result = self.validate_cv_file(file)
            
            if not validation_result['is_valid']:
                return {
                    'success': False,
                    'validation': validation_result,
                    'metadata': None,
                    'message': 'CV validation failed'
                }
            
            # Extract metadata
            metadata = self.extract_cv_metadata(file)
            
            # Combine validation metadata with extracted metadata
            combined_metadata = {
                **validation_result['metadata'],
                **metadata
            }
            
            return {
                'success': True,
                'validation': validation_result,
                'metadata': combined_metadata,
                'message': 'CV processed successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing CV upload: {str(e)}")
            return {
                'success': False,
                'validation': None,
                'metadata': None,
                'error': str(e),
                'message': 'CV processing failed'
            }
    
    def _get_file_extension(self, filename: str) -> Optional[str]:
        """Extract file extension from filename."""
        if not filename:
            return None
        
        extension = os.path.splitext(filename)[1].lower().lstrip('.')
        return extension if extension else None
    
    def _get_mime_type(self, file: UploadedFile) -> str:
        """Get MIME type of uploaded file."""
        # Try to get MIME type from file content
        if hasattr(file, 'content_type') and file.content_type:
            return file.content_type
        
        # Fallback to guessing from filename
        mime_type, _ = mimetypes.guess_type(file.name)
        return mime_type or 'application/octet-stream'
    
    def _generate_file_hash(self, file: UploadedFile) -> str:
        """Generate SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        
        # Reset file pointer to beginning
        file.seek(0)
        
        # Read file in chunks to handle large files
        for chunk in file.chunks():
            hasher.update(chunk)
        
        # Reset file pointer for subsequent operations
        file.seek(0)
        
        return hasher.hexdigest()


class CVStorageService:
    """
    Service for managing CV file storage and organization.
    """
    
    def __init__(self):
        """Initialize the CV storage service."""
        self.logger = logging.getLogger(__name__)
    
    def get_storage_path(self, user_id: int, filename: str) -> str:
        """
        Generate organized storage path for CV files.
        
        Args:
            user_id: ID of the user uploading the CV
            filename: Original filename
            
        Returns:
            Organized storage path
        """
        # Create timestamp-based organization
        timestamp = timezone.now()
        year = timestamp.strftime('%Y')
        month = timestamp.strftime('%m')
        
        # Sanitize filename
        safe_filename = self._sanitize_filename(filename)
        
        return f'cvs/{user_id}/{year}/{month}/{safe_filename}'
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage.
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace unsafe characters
        safe_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        safe_filename = ''.join(c for c in filename if c in safe_chars)
        
        # Ensure filename is not empty
        if not safe_filename:
            safe_filename = f'cv_{timezone.now().strftime("%Y%m%d_%H%M%S")}'
        
        return safe_filename
    
    def cleanup_old_cv(self, old_cv_path: str) -> bool:
        """
        Clean up old CV file when a new one is uploaded.
        
        Args:
            old_cv_path: Path to the old CV file
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            if old_cv_path and os.path.exists(old_cv_path):
                os.remove(old_cv_path)
                self.logger.info(f"Cleaned up old CV file: {old_cv_path}")
                return True
            return True  # No file to clean up
        except Exception as e:
            self.logger.error(f"Error cleaning up old CV file {old_cv_path}: {str(e)}")
            return False