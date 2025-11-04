"""
Custom exception handler for enhanced security and error handling.

This module provides custom exception handling for the Koroh platform
with security-focused error responses and logging.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.utils import timezone

logger = logging.getLogger('koroh_platform.security')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides security-focused error responses.
    
    Args:
        exc: The exception instance
        context: The context in which the exception occurred
        
    Returns:
        Response: Custom error response
    """
    
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Get request information for logging
    request = context.get('request')
    user = getattr(request, 'user', None) if request else None
    client_ip = get_client_ip(request) if request else 'unknown'
    
    # Log the exception with security context
    log_security_exception(exc, user, client_ip, context)
    
    if response is not None:
        # Customize error response format
        custom_response_data = {
            'error': {
                'code': get_error_code(exc),
                'message': get_safe_error_message(exc, response.data),
                'timestamp': timezone.now().isoformat(),
            }
        }
        
        # Add request ID for tracking (if available)
        if request and hasattr(request, 'META'):
            request_id = request.META.get('HTTP_X_REQUEST_ID')
            if request_id:
                custom_response_data['error']['request_id'] = request_id
        
        # Don't expose sensitive information in production
        if not getattr(context.get('request'), 'user', None) or not context.get('request').user.is_staff:
            # Remove detailed error information for non-admin users
            if isinstance(response.data, dict) and 'detail' in response.data:
                if response.status_code >= 500:
                    custom_response_data['error']['message'] = 'Internal server error occurred'
        
        response.data = custom_response_data
    
    return response


def get_error_code(exc):
    """
    Get a standardized error code for the exception.
    
    Args:
        exc: The exception instance
        
    Returns:
        str: Error code
    """
    
    error_code_mapping = {
        'ValidationError': 'VALIDATION_ERROR',
        'PermissionDenied': 'PERMISSION_DENIED',
        'NotAuthenticated': 'AUTHENTICATION_REQUIRED',
        'AuthenticationFailed': 'AUTHENTICATION_FAILED',
        'NotFound': 'RESOURCE_NOT_FOUND',
        'MethodNotAllowed': 'METHOD_NOT_ALLOWED',
        'Throttled': 'RATE_LIMIT_EXCEEDED',
        'ParseError': 'INVALID_REQUEST_FORMAT',
        'UnsupportedMediaType': 'UNSUPPORTED_MEDIA_TYPE',
    }
    
    exc_name = exc.__class__.__name__
    return error_code_mapping.get(exc_name, 'UNKNOWN_ERROR')


def get_safe_error_message(exc, response_data):
    """
    Get a safe error message that doesn't expose sensitive information.
    
    Args:
        exc: The exception instance
        response_data: Original response data
        
    Returns:
        str: Safe error message
    """
    
    # Default safe messages for different exception types
    safe_messages = {
        'ValidationError': 'Invalid input data provided',
        'PermissionDenied': 'You do not have permission to perform this action',
        'NotAuthenticated': 'Authentication credentials were not provided',
        'AuthenticationFailed': 'Invalid authentication credentials',
        'NotFound': 'The requested resource was not found',
        'MethodNotAllowed': 'This HTTP method is not allowed for this endpoint',
        'Throttled': 'Request rate limit exceeded. Please try again later',
        'ParseError': 'Invalid request format',
        'UnsupportedMediaType': 'Unsupported media type in request',
    }
    
    exc_name = exc.__class__.__name__
    
    # Use safe message by default
    safe_message = safe_messages.get(exc_name, 'An error occurred while processing your request')
    
    # For validation errors, we can provide more specific information
    if exc_name == 'ValidationError' and isinstance(response_data, dict):
        if 'detail' in response_data:
            return str(response_data['detail'])
        elif isinstance(response_data, dict):
            # Format field-specific validation errors
            field_errors = []
            for field, errors in response_data.items():
                if isinstance(errors, list):
                    field_errors.append(f"{field}: {', '.join(str(e) for e in errors)}")
                else:
                    field_errors.append(f"{field}: {str(errors)}")
            
            if field_errors:
                return f"Validation failed: {'; '.join(field_errors)}"
    
    return safe_message


def log_security_exception(exc, user, client_ip, context):
    """
    Log security-relevant exceptions for monitoring and analysis.
    
    Args:
        exc: The exception instance
        user: User object (if authenticated)
        client_ip: Client IP address
        context: Exception context
    """
    
    request = context.get('request')
    view = context.get('view')
    
    # Determine log level based on exception type
    exc_name = exc.__class__.__name__
    
    if exc_name in ['PermissionDenied', 'NotAuthenticated', 'AuthenticationFailed']:
        log_level = 'WARNING'
    elif exc_name in ['Throttled']:
        log_level = 'INFO'
    elif exc_name in ['ValidationError', 'ParseError']:
        log_level = 'INFO'
    else:
        log_level = 'ERROR'
    
    # Prepare log data
    log_data = {
        'exception_type': exc_name,
        'exception_message': str(exc),
        'user_id': user.id if user and user.is_authenticated else None,
        'client_ip': client_ip,
        'request_method': request.method if request else None,
        'request_path': request.path if request else None,
        'view_name': view.__class__.__name__ if view else None,
        'timestamp': timezone.now().isoformat(),
    }
    
    # Add user agent for security analysis
    if request and hasattr(request, 'META'):
        log_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
    
    log_message = f"Exception: {exc_name} - {str(exc)}"
    
    # Log with appropriate level
    if log_level == 'WARNING':
        logger.warning(log_message, extra=log_data)
    elif log_level == 'ERROR':
        logger.error(log_message, extra=log_data)
    else:
        logger.info(log_message, extra=log_data)
    
    # Special handling for security-critical exceptions
    if exc_name in ['PermissionDenied', 'AuthenticationFailed']:
        # Log to security-specific logger
        security_logger = logging.getLogger('koroh_platform.security.auth')
        security_logger.warning(
            f"Security event: {exc_name} for user {user.id if user and user.is_authenticated else 'anonymous'} "
            f"from IP {client_ip} on {request.path if request else 'unknown path'}",
            extra=log_data
        )


def get_client_ip(request):
    """
    Get client IP address from request.
    
    Args:
        request: Django request object
        
    Returns:
        str: Client IP address
    """
    
    if not request:
        return 'unknown'
    
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', 'unknown')
    
    return ip


def handle_csrf_failure(request, reason=""):
    """
    Custom CSRF failure handler.
    
    Args:
        request: Django request object
        reason: CSRF failure reason
        
    Returns:
        JsonResponse: CSRF error response
    """
    
    from django.http import JsonResponse
    
    client_ip = get_client_ip(request)
    user = getattr(request, 'user', None)
    
    # Log CSRF failure
    logger.warning(
        f"CSRF failure from IP {client_ip} for user {user.id if user and user.is_authenticated else 'anonymous'}: {reason}",
        extra={
            'event_type': 'csrf_failure',
            'client_ip': client_ip,
            'user_id': user.id if user and user.is_authenticated else None,
            'reason': reason,
            'timestamp': timezone.now().isoformat(),
        }
    )
    
    return JsonResponse(
        {
            'error': {
                'code': 'CSRF_FAILURE',
                'message': 'CSRF verification failed. Please refresh the page and try again.',
                'timestamp': timezone.now().isoformat(),
            }
        },
        status=status.HTTP_403_FORBIDDEN
    )