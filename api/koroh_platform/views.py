"""
Core views for Koroh platform.

This module provides core views including error handlers
and security-related endpoints.
"""

from django.http import JsonResponse
from django.utils import timezone
from rest_framework import status
import logging

logger = logging.getLogger('koroh_platform.security')


def csrf_failure(request, reason=""):
    """
    Custom CSRF failure view.
    
    Args:
        request: Django request object
        reason: CSRF failure reason
        
    Returns:
        JsonResponse: CSRF error response
    """
    
    from koroh_platform.utils.exception_handler import get_client_ip
    
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