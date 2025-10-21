"""
Security utilities for the Koroh platform.

Requirements: 4.4, 4.5
"""

import hashlib
import hmac
import secrets
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.http import HttpRequest
from django.utils import timezone
import re

logger = logging.getLogger(__name__)


class SecurityValidator:
    """
    Security validation utilities.
    """
    
    # File type validation
    ALLOWED_CV_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt'}
    ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
    
    # Content type validation
    ALLOWED_CV_CONTENT_TYPES = {
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain'
    }
    
    ALLOWED_IMAGE_CONTENT_TYPES = {
        'image/jpeg',
        'image/png', 
        'image/gif',
        'image/webp'
    }
    
    # File size limits (in bytes)
    MAX_CV_SIZE = 10 * 1024 * 1024  # 10MB
    MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
    
    @classmethod
    def validate_file_upload(cls, file, file_type: str = 'cv') -> Dict[str, Any]:
        """
        Validate uploaded file for security and format compliance.
        
        Args:
            file: Uploaded file object
            file_type: Type of file ('cv' or 'image')
        
        Returns:
            Dict with validation results
        """
        validation_result = {
            'is_valid': False,
            'errors': [],
            'warnings': []
        }
        
        if not file:
            validation_result['errors'].append('No file provided')
            return validation_result
        
        # Get file extension and content type
        file_name = file.name.lower() if file.name else ''
        file_extension = '.' + file_name.split('.')[-1] if '.' in file_name else ''
        content_type = getattr(file, 'content_type', '').lower()
        
        # Validate based on file type
        if file_type == 'cv':
            allowed_extensions = cls.ALLOWED_CV_EXTENSIONS
            allowed_content_types = cls.ALLOWED_CV_CONTENT_TYPES
            max_size = cls.MAX_CV_SIZE
        elif file_type == 'image':
            allowed_extensions = cls.ALLOWED_IMAGE_EXTENSIONS
            allowed_content_types = cls.ALLOWED_IMAGE_CONTENT_TYPES
            max_size = cls.MAX_IMAGE_SIZE
        else:
            validation_result['errors'].append(f'Unknown file type: {file_type}')
            return validation_result
        
        # Extension validation
        if file_extension not in allowed_extensions:
            validation_result['errors'].append(
                f'Invalid file extension. Allowed: {", ".join(allowed_extensions)}'
            )
        
        # Content type validation
        if content_type not in allowed_content_types:
            validation_result['errors'].append(
                f'Invalid content type: {content_type}'
            )
        
        # File size validation
        if hasattr(file, 'size') and file.size > max_size:
            validation_result['errors'].append(
                f'File too large. Maximum size: {max_size // (1024*1024)}MB'
            )
        
        # File name security validation
        if not cls.is_safe_filename(file_name):
            validation_result['errors'].append('Unsafe filename detected')
        
        # Content validation (basic)
        try:
            file.seek(0)
            file_content = file.read(1024)  # Read first 1KB
            file.seek(0)  # Reset file pointer
            
            if cls.contains_malicious_content(file_content):
                validation_result['errors'].append('Potentially malicious content detected')
        except Exception as e:
            validation_result['warnings'].append(f'Could not scan file content: {e}')
        
        validation_result['is_valid'] = len(validation_result['errors']) == 0
        return validation_result
    
    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """
        Check if filename is safe (no path traversal, etc.).
        """
        if not filename:
            return False
        
        # Check for path traversal attempts
        if '..' in filename or '/' in filename or '\\' in filename:
            return False
        
        # Check for null bytes
        if '\x00' in filename:
            return False
        
        # Check for control characters
        if any(ord(char) < 32 for char in filename):
            return False
        
        # Check filename length
        if len(filename) > 255:
            return False
        
        return True
    
    @staticmethod
    def contains_malicious_content(content: bytes) -> bool:
        """
        Basic check for potentially malicious content.
        """
        # Check for executable signatures
        malicious_signatures = [
            b'MZ',  # Windows executable
            b'\x7fELF',  # Linux executable
            b'<script',  # JavaScript
            b'javascript:',  # JavaScript URL
            b'vbscript:',  # VBScript URL
        ]
        
        content_lower = content.lower()
        return any(sig in content_lower for sig in malicious_signatures)


class InputSanitizer:
    """
    Input sanitization utilities.
    """
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 1000) -> str:
        """
        Sanitize text input by removing potentially dangerous content.
        """
        if not text:
            return ''
        
        # Truncate to max length
        text = text[:max_length]
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except newlines and tabs
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Basic HTML/script tag removal
        text = re.sub(r'<[^>]*>', '', text)
        
        return text.strip()
    
    @staticmethod
    def sanitize_email(email: str) -> Optional[str]:
        """
        Sanitize and validate email address.
        """
        if not email:
            return None
        
        email = email.strip().lower()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return None
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'\.{2,}',  # Multiple consecutive dots
            r'^\.|\.$',  # Starting or ending with dot
            r'@.*@',  # Multiple @ symbols
        ]
        
        if any(re.search(pattern, email) for pattern in suspicious_patterns):
            return None
        
        return email
    
    @staticmethod
    def sanitize_url(url: str) -> Optional[str]:
        """
        Sanitize and validate URL.
        """
        if not url:
            return None
        
        url = url.strip()
        
        # Allow only HTTP and HTTPS
        if not url.startswith(('http://', 'https://')):
            return None
        
        # Basic URL validation
        url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$'
        if not re.match(url_pattern, url):
            return None
        
        # Check for suspicious patterns
        if any(pattern in url.lower() for pattern in ['javascript:', 'data:', 'vbscript:']):
            return None
        
        return url


class RateLimiter:
    """
    Advanced rate limiting utilities.
    """
    
    @staticmethod
    def is_rate_limited(identifier: str, action: str, limit: int, window: int) -> bool:
        """
        Check if an action is rate limited.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            action: Action being performed
            limit: Maximum number of actions allowed
            window: Time window in seconds
        
        Returns:
            True if rate limited, False otherwise
        """
        cache_key = f"rate_limit:{identifier}:{action}"
        
        try:
            current_count = cache.get(cache_key, 0)
            
            if current_count >= limit:
                logger.warning(f"Rate limit exceeded: {identifier} for {action}")
                return True
            
            # Increment counter
            cache.set(cache_key, current_count + 1, window)
            return False
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - don't block if cache is unavailable
            return False
    
    @staticmethod
    def get_rate_limit_status(identifier: str, action: str, limit: int) -> Dict[str, Any]:
        """
        Get current rate limit status.
        """
        cache_key = f"rate_limit:{identifier}:{action}"
        
        try:
            current_count = cache.get(cache_key, 0)
            remaining = max(0, limit - current_count)
            
            return {
                'current': current_count,
                'limit': limit,
                'remaining': remaining,
                'is_limited': current_count >= limit
            }
        except Exception as e:
            logger.error(f"Rate limit status error: {e}")
            return {
                'current': 0,
                'limit': limit,
                'remaining': limit,
                'is_limited': False
            }


class SecurityAuditor:
    """
    Security auditing and logging utilities.
    """
    
    @staticmethod
    def log_security_event(event_type: str, user_id: Optional[int], 
                          request: HttpRequest, details: Dict[str, Any] = None):
        """
        Log security-related events.
        """
        event_data = {
            'timestamp': timezone.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'ip_address': SecurityAuditor.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'path': request.path,
            'method': request.method,
            'details': details or {}
        }
        
        # Log to security log
        logger.info(f"Security event: {event_data}")
        
        # Store in cache for recent events tracking
        cache_key = f"security_events:{user_id or 'anonymous'}"
        try:
            recent_events = cache.get(cache_key, [])
            recent_events.append(event_data)
            
            # Keep only last 10 events
            recent_events = recent_events[-10:]
            cache.set(cache_key, recent_events, 3600)  # 1 hour
        except Exception as e:
            logger.error(f"Failed to cache security event: {e}")
    
    @staticmethod
    def get_client_ip(request: HttpRequest) -> str:
        """
        Get the real client IP address.
        """
        # Check for forwarded IP (behind proxy/load balancer)
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        
        return ip
    
    @staticmethod
    def detect_suspicious_activity(user_id: int, request: HttpRequest) -> List[str]:
        """
        Detect potentially suspicious activity patterns.
        """
        warnings = []
        
        # Check for rapid requests
        cache_key = f"request_times:{user_id}"
        try:
            request_times = cache.get(cache_key, [])
            current_time = time.time()
            
            # Add current request time
            request_times.append(current_time)
            
            # Keep only requests from last minute
            request_times = [t for t in request_times if current_time - t < 60]
            
            # Check for too many requests
            if len(request_times) > 30:  # More than 30 requests per minute
                warnings.append('High request frequency detected')
            
            cache.set(cache_key, request_times, 300)  # 5 minutes
        except Exception as e:
            logger.error(f"Suspicious activity detection error: {e}")
        
        # Check for unusual user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if not user_agent or len(user_agent) < 10:
            warnings.append('Suspicious or missing user agent')
        
        # Check for unusual request patterns
        if request.path.count('../') > 0:
            warnings.append('Path traversal attempt detected')
        
        return warnings


class TokenManager:
    """
    Secure token generation and validation.
    """
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """
        Generate a cryptographically secure random token.
        """
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def generate_signed_token(data: str, secret_key: str = None) -> str:
        """
        Generate a signed token using HMAC.
        """
        secret_key = secret_key or settings.SECRET_KEY
        signature = hmac.new(
            secret_key.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return f"{data}.{signature}"
    
    @staticmethod
    def verify_signed_token(token: str, secret_key: str = None) -> Optional[str]:
        """
        Verify a signed token and return the original data.
        """
        try:
            data, signature = token.rsplit('.', 1)
            secret_key = secret_key or settings.SECRET_KEY
            
            expected_signature = hmac.new(
                secret_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            if hmac.compare_digest(signature, expected_signature):
                return data
            else:
                return None
        except ValueError:
            return None
    
    @staticmethod
    def hash_sensitive_data(data: str, salt: str = None) -> str:
        """
        Hash sensitive data with salt.
        """
        if salt is None:
            salt = secrets.token_hex(16)
        
        hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
        return f"{salt}${hash_obj.hex()}"
    
    @staticmethod
    def verify_hashed_data(data: str, hashed_data: str) -> bool:
        """
        Verify data against its hash.
        """
        try:
            salt, hash_hex = hashed_data.split('$', 1)
            hash_obj = hashlib.pbkdf2_hmac('sha256', data.encode(), salt.encode(), 100000)
            return hmac.compare_digest(hash_hex, hash_obj.hex())
        except ValueError:
            return False


class SecurityHeaders:
    """
    Security headers management.
    """
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get recommended security headers.
        """
        return {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; "
                "img-src 'self' data: https:; "
                "connect-src 'self' https://api.koroh.dev; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        }
    
    @staticmethod
    def apply_security_headers(response, request=None):
        """
        Apply security headers to a response.
        """
        headers = SecurityHeaders.get_security_headers()
        
        for header, value in headers.items():
            response[header] = value
        
        # Add HSTS only for HTTPS
        if request and request.is_secure() and not settings.DEBUG:
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        return response