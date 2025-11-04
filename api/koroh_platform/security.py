"""
Enhanced security utilities and middleware for Koroh platform.

This module provides additional security measures including
input validation, security headers, and threat detection.
"""

import re
import logging
from django.http import HttpResponseForbidden, JsonResponse
from django.core.cache import cache
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from rest_framework import status
import json

logger = logging.getLogger('koroh_platform.security')
User = get_user_model()


class SecurityValidationMiddleware(MiddlewareMixin):
    """
    Enhanced security validation middleware.
    
    Provides input validation, SQL injection detection,
    XSS prevention, and other security measures.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        
        # Compile regex patterns for performance
        self.sql_injection_patterns = [
            re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)", re.IGNORECASE),
            re.compile(r"(\b(OR|AND)\s+\d+\s*=\s*\d+)", re.IGNORECASE),
            re.compile(r"('|(\\')|(;)|(\\;)|(\-\-)|(\#))", re.IGNORECASE),
            re.compile(r"(\b(SCRIPT|JAVASCRIPT|VBSCRIPT|ONLOAD|ONERROR|ONCLICK)\b)", re.IGNORECASE),
        ]
        
        self.xss_patterns = [
            re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile(r"javascript:", re.IGNORECASE),
            re.compile(r"on\w+\s*=", re.IGNORECASE),
            re.compile(r"<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL),
        ]
        
        # Suspicious user agents
        self.suspicious_user_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus',
            'openvas', 'w3af', 'burp', 'zap', 'acunetix'
        ]
    
    def process_request(self, request):
        """Validate request for security threats."""
        
        # Skip validation for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return None
        
        # Check user agent for suspicious patterns
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        if any(suspicious in user_agent for suspicious in self.suspicious_user_agents):
            logger.warning(f"Suspicious user agent detected: {user_agent} from IP {self.get_client_ip(request)}")
            return self.security_response("Suspicious user agent detected")
        
        # Validate request parameters
        if not self.validate_request_data(request):
            return self.security_response("Invalid request data detected")
        
        # Check for excessive header size
        if self.check_header_size(request):
            logger.warning(f"Excessive header size from IP {self.get_client_ip(request)}")
            return self.security_response("Request headers too large")
        
        return None
    
    def validate_request_data(self, request):
        """Validate request data for security threats."""
        
        # Check GET parameters
        for key, value in request.GET.items():
            if not self.is_safe_input(key) or not self.is_safe_input(value):
                logger.warning(f"Suspicious GET parameter: {key}={value} from IP {self.get_client_ip(request)}")
                return False
        
        # Check POST data
        if request.method == 'POST':
            try:
                if hasattr(request, 'body') and request.body:
                    # For JSON data
                    if request.content_type == 'application/json':
                        try:
                            data = json.loads(request.body.decode('utf-8'))
                            if not self.validate_json_data(data):
                                return False
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            pass  # Let Django handle invalid JSON
                    
                    # Check raw body for suspicious patterns
                    body_str = request.body.decode('utf-8', errors='ignore')
                    if not self.is_safe_input(body_str):
                        logger.warning(f"Suspicious POST body from IP {self.get_client_ip(request)}")
                        return False
                        
            except Exception as e:
                logger.error(f"Error validating POST data: {e}")
        
        return True
    
    def validate_json_data(self, data, depth=0):
        """Recursively validate JSON data."""
        if depth > 10:  # Prevent deep recursion attacks
            return False
        
        if isinstance(data, dict):
            for key, value in data.items():
                if not self.is_safe_input(str(key)):
                    return False
                if isinstance(value, (dict, list)):
                    if not self.validate_json_data(value, depth + 1):
                        return False
                elif not self.is_safe_input(str(value)):
                    return False
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    if not self.validate_json_data(item, depth + 1):
                        return False
                elif not self.is_safe_input(str(item)):
                    return False
        
        return True
    
    def is_safe_input(self, input_str):
        """Check if input string is safe from common attacks."""
        if not isinstance(input_str, str):
            input_str = str(input_str)
        
        # Check for SQL injection patterns
        for pattern in self.sql_injection_patterns:
            if pattern.search(input_str):
                return False
        
        # Check for XSS patterns
        for pattern in self.xss_patterns:
            if pattern.search(input_str):
                return False
        
        # Check for path traversal
        if '../' in input_str or '..\\' in input_str:
            return False
        
        # Check for null bytes
        if '\x00' in input_str:
            return False
        
        return True
    
    def check_header_size(self, request):
        """Check if request headers are excessively large."""
        total_header_size = sum(
            len(key) + len(value) 
            for key, value in request.META.items() 
            if key.startswith('HTTP_')
        )
        return total_header_size > 8192  # 8KB limit
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def security_response(self, message):
        """Return a security error response."""
        return JsonResponse(
            {'error': 'Security validation failed', 'message': message},
            status=status.HTTP_400_BAD_REQUEST
        )


class AuthenticationSecurityMiddleware(MiddlewareMixin):
    """
    Enhanced authentication security middleware.
    
    Provides additional authentication security measures including
    session validation, concurrent session limits, and suspicious activity detection.
    """
    
    def process_request(self, request):
        """Enhanced authentication security checks."""
        
        # Skip for non-API endpoints
        if not request.path.startswith('/api/'):
            return None
        
        # Check for authenticated users
        if hasattr(request, 'user') and request.user.is_authenticated:
            
            # Check for concurrent session limits
            if self.check_concurrent_sessions(request.user):
                logger.warning(f"Concurrent session limit exceeded for user {request.user.id}")
                return JsonResponse(
                    {'error': 'Too many concurrent sessions'},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Check for suspicious activity patterns
            if self.detect_suspicious_activity(request):
                logger.warning(f"Suspicious activity detected for user {request.user.id}")
                # Don't block, just log for now
        
        return None
    
    def check_concurrent_sessions(self, user):
        """Check if user has too many concurrent sessions."""
        if not user.is_authenticated:
            return False
        
        # Use cache to track active sessions
        cache_key = f"active_sessions:{user.id}"
        active_sessions = cache.get(cache_key, 0)
        
        # Allow up to 5 concurrent sessions per user
        max_sessions = 5
        if active_sessions > max_sessions:
            return True
        
        # Increment session count
        cache.set(cache_key, active_sessions + 1, 3600)  # 1 hour timeout
        return False
    
    def detect_suspicious_activity(self, request):
        """Detect suspicious user activity patterns."""
        if not request.user.is_authenticated:
            return False
        
        user_id = request.user.id
        client_ip = self.get_client_ip(request)
        
        # Check for rapid requests (simple rate limiting)
        cache_key = f"user_requests:{user_id}:{client_ip}"
        request_count = cache.get(cache_key, 0)
        
        if request_count > 100:  # More than 100 requests per minute
            return True
        
        cache.set(cache_key, request_count + 1, 60)  # 1 minute window
        return False
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class APISecurityMiddleware(MiddlewareMixin):
    """
    API-specific security middleware.
    
    Provides API endpoint protection, request validation,
    and response security measures.
    """
    
    def process_request(self, request):
        """API security validation."""
        
        # Only process API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Validate API version
        if not self.validate_api_version(request):
            return JsonResponse(
                {'error': 'Invalid API version'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for required headers
        if not self.validate_required_headers(request):
            return JsonResponse(
                {'error': 'Missing required headers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return None
    
    def process_response(self, request, response):
        """Add API security headers."""
        
        if request.path.startswith('/api/'):
            # Add API-specific security headers
            response['X-API-Version'] = 'v1'
            response['X-Content-Type-Options'] = 'nosniff'
            response['X-Frame-Options'] = 'DENY'
            
            # Remove sensitive headers
            if 'Server' in response:
                del response['Server']
            if 'X-Powered-By' in response:
                del response['X-Powered-By']
        
        return response
    
    def validate_api_version(self, request):
        """Validate API version in request."""
        # For now, just check if it's a valid API path
        return '/v1/' in request.path or request.path == '/api/'
    
    def validate_required_headers(self, request):
        """Validate required headers for API requests."""
        # For POST/PUT/PATCH requests, require Content-Type
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            if not content_type:
                return False
        
        return True


def log_security_event(event_type, user, details, severity='INFO'):
    """
    Log security events for monitoring and analysis.
    
    Args:
        event_type: Type of security event (e.g., 'login_attempt', 'permission_denied')
        user: User object or None for anonymous events
        details: Dictionary with event details
        severity: Log severity level ('INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    
    log_data = {
        'event_type': event_type,
        'user_id': user.id if user and user.is_authenticated else None,
        'timestamp': timezone.now().isoformat(),
        'details': details
    }
    
    log_message = f"Security Event: {event_type} - {details}"
    
    if severity == 'CRITICAL':
        logger.critical(log_message, extra=log_data)
    elif severity == 'ERROR':
        logger.error(log_message, extra=log_data)
    elif severity == 'WARNING':
        logger.warning(log_message, extra=log_data)
    else:
        logger.info(log_message, extra=log_data)


def validate_file_upload(uploaded_file):
    """
    Validate uploaded files for security.
    
    Args:
        uploaded_file: Django UploadedFile object
        
    Returns:
        dict: Validation result with 'valid' boolean and 'errors' list
    """
    
    errors = []
    
    # Check file size (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    if uploaded_file.size > max_size:
        errors.append(f"File size {uploaded_file.size} exceeds maximum allowed size {max_size}")
    
    # Check file extension
    allowed_extensions = ['.pdf', '.doc', '.docx', '.txt', '.jpg', '.jpeg', '.png']
    file_extension = uploaded_file.name.lower().split('.')[-1] if '.' in uploaded_file.name else ''
    if f'.{file_extension}' not in allowed_extensions:
        errors.append(f"File extension '.{file_extension}' is not allowed")
    
    # Check for suspicious file names
    suspicious_patterns = ['../', '..\\', '<script', 'javascript:', 'data:']
    if any(pattern in uploaded_file.name.lower() for pattern in suspicious_patterns):
        errors.append("Suspicious file name detected")
    
    # Basic content validation for text files
    if file_extension in ['txt', 'csv']:
        try:
            content = uploaded_file.read(1024).decode('utf-8', errors='ignore')
            uploaded_file.seek(0)  # Reset file pointer
            
            # Check for suspicious content
            if any(pattern in content.lower() for pattern in ['<script', 'javascript:', 'data:']):
                errors.append("Suspicious content detected in file")
                
        except Exception as e:
            errors.append(f"Error reading file content: {str(e)}")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors
    }


def sanitize_input(input_str, max_length=1000):
    """
    Sanitize user input to prevent XSS and other attacks.
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        str: Sanitized input string
    """
    
    if not isinstance(input_str, str):
        input_str = str(input_str)
    
    # Truncate to max length
    if len(input_str) > max_length:
        input_str = input_str[:max_length]
    
    # Remove null bytes
    input_str = input_str.replace('\x00', '')
    
    # Basic HTML escaping
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    
    for char, escape in html_escape_table.items():
        input_str = input_str.replace(char, escape)
    
    return input_str


def check_password_strength(password):
    """
    Check password strength and return recommendations.
    
    Args:
        password: Password string to check
        
    Returns:
        dict: Result with 'strong' boolean and 'recommendations' list
    """
    
    recommendations = []
    
    # Length check
    if len(password) < 8:
        recommendations.append("Password should be at least 8 characters long")
    
    # Character variety checks
    if not re.search(r'[a-z]', password):
        recommendations.append("Password should contain lowercase letters")
    
    if not re.search(r'[A-Z]', password):
        recommendations.append("Password should contain uppercase letters")
    
    if not re.search(r'\d', password):
        recommendations.append("Password should contain numbers")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        recommendations.append("Password should contain special characters")
    
    # Common password check (basic)
    common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein']
    if password.lower() in common_passwords:
        recommendations.append("Password is too common, please choose a unique password")
    
    return {
        'strong': len(recommendations) == 0,
        'recommendations': recommendations
    }