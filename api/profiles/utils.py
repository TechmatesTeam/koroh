"""
Utility functions for profiles app.

This module provides utility functions for file handling,
validation, and security operations.
"""

import os
import magic
import hashlib
from typing import List, Dict, Any, Optional
from django.core.files.uploadedfile import UploadedFile
from django.conf import settings
from django.utils import timezone


def get_file_type(file_path: str) -> Optional[str]:
    """
    Get the actual file type using python-magic.
    
    This provides more accurate file type detection than
    relying on file extensions alone.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string or None if detection fails
    """
    try:
        return magic.from_file(file_path, mime=True)
    except Exception:
        return None


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe for storage.
    
    Args:
        filename: The filename to check
        
    Returns:
        True if filename is safe, False otherwise
    """
    if not filename:
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for hidden files
    if filename.startswith('.'):
        return False
    
    # Check for reserved names (Windows)
    reserved_names = [
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    ]
    
    name_without_ext = os.path.splitext(filename)[0].upper()
    if name_without_ext in reserved_names:
        return False
    
    return True


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not filename:
        return f'file_{timezone.now().strftime("%Y%m%d_%H%M%S")}'
    
    # Keep only safe characters
    safe_chars = '-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    sanitized = ''.join(c for c in filename if c in safe_chars)
    
    # Ensure filename is not empty after sanitization
    if not sanitized:
        ext = os.path.splitext(filename)[1]
        sanitized = f'file_{timezone.now().strftime("%Y%m%d_%H%M%S")}{ext}'
    
    return sanitized


def calculate_file_hash(file: UploadedFile, algorithm: str = 'sha256') -> str:
    """
    Calculate hash of uploaded file.
    
    Args:
        file: The uploaded file
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hex digest of file hash
    """
    hasher = hashlib.new(algorithm)
    
    # Reset file pointer
    file.seek(0)
    
    # Read file in chunks
    for chunk in file.chunks():
        hasher.update(chunk)
    
    # Reset file pointer
    file.seek(0)
    
    return hasher.hexdigest()


def get_file_info(file: UploadedFile) -> Dict[str, Any]:
    """
    Get comprehensive file information.
    
    Args:
        file: The uploaded file
        
    Returns:
        Dictionary containing file information
    """
    return {
        'name': file.name,
        'size': file.size,
        'content_type': getattr(file, 'content_type', None),
        'charset': getattr(file, 'charset', None),
        'hash_sha256': calculate_file_hash(file, 'sha256'),
        'hash_md5': calculate_file_hash(file, 'md5'),
        'is_safe_filename': is_safe_filename(file.name),
        'sanitized_filename': sanitize_filename(file.name),
        'timestamp': timezone.now().isoformat(),
    }


def validate_file_security(file: UploadedFile) -> Dict[str, Any]:
    """
    Perform security validation on uploaded file.
    
    Args:
        file: The uploaded file
        
    Returns:
        Dictionary containing security validation results
    """
    validation_result = {
        'is_safe': True,
        'warnings': [],
        'errors': [],
        'checks_performed': []
    }
    
    # Check filename safety
    validation_result['checks_performed'].append('filename_safety')
    if not is_safe_filename(file.name):
        validation_result['warnings'].append('Unsafe filename detected')
        validation_result['is_safe'] = False
    
    # Check file size
    validation_result['checks_performed'].append('file_size')
    max_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)
    if file.size > max_size:
        validation_result['errors'].append(f'File size exceeds maximum allowed ({max_size} bytes)')
        validation_result['is_safe'] = False
    
    # Check for empty file
    validation_result['checks_performed'].append('empty_file')
    if file.size == 0:
        validation_result['errors'].append('Empty file not allowed')
        validation_result['is_safe'] = False
    
    return validation_result


class FileTypeDetector:
    """
    Advanced file type detection utility.
    """
    
    # File signatures (magic numbers) for common file types
    FILE_SIGNATURES = {
        'pdf': [b'%PDF'],
        'doc': [b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'],  # OLE2 signature
        'docx': [b'PK\x03\x04'],  # ZIP signature (DOCX is a ZIP file)
        'md': [],  # Markdown files don't have a specific signature
    }
    
    @classmethod
    def detect_file_type(cls, file: UploadedFile) -> Optional[str]:
        """
        Detect file type based on content signature.
        
        Args:
            file: The uploaded file
            
        Returns:
            Detected file type or None
        """
        # Read first 512 bytes for signature detection
        file.seek(0)
        header = file.read(512)
        file.seek(0)
        
        for file_type, signatures in cls.FILE_SIGNATURES.items():
            if not signatures:  # Skip types without signatures (like markdown)
                continue
                
            for signature in signatures:
                if header.startswith(signature):
                    return file_type
        
        return None
    
    @classmethod
    def validate_file_type(cls, file: UploadedFile, expected_types: List[str]) -> bool:
        """
        Validate that file matches one of the expected types.
        
        Args:
            file: The uploaded file
            expected_types: List of expected file types
            
        Returns:
            True if file type is valid, False otherwise
        """
        detected_type = cls.detect_file_type(file)
        
        # For files without signatures (like markdown), fall back to extension
        if not detected_type:
            extension = os.path.splitext(file.name)[1].lower().lstrip('.')
            return extension in expected_types
        
        return detected_type in expected_types