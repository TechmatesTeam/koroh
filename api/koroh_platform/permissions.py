"""
Custom permission classes for Koroh platform.

This module defines comprehensive permission classes for securing API endpoints
with role-based access control, object-level permissions, and security measures.
"""

from rest_framework import permissions
from rest_framework.permissions import BasePermission
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger('koroh_platform.security')

User = get_user_model()


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    Read permissions are allowed for any authenticated user.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Write permissions only to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        
        return False


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """
    Permission that allows owners and admins to edit, others to read.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
        # Admin users can edit anything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Write permissions only to the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        elif hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'author'):
            return obj.author == request.user
        
        return False


class IsProfileOwner(BasePermission):
    """
    Permission for profile-related operations.
    Only allows users to access their own profile data.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # For profile objects, check if user owns the profile
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # For user objects, check if it's the same user
        if isinstance(obj, User):
            return obj == request.user
        
        return False


class IsGroupMemberOrReadOnly(BasePermission):
    """
    Permission for peer group operations.
    Allows group members to participate, others to read public groups.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # For read operations, check if group is public or user is member
        if request.method in permissions.SAFE_METHODS:
            if hasattr(obj, 'privacy_level'):
                if obj.privacy_level == 'public':
                    return True
                return obj.is_member(request.user)
            return True
        
        # For write operations, user must be a member
        if hasattr(obj, 'is_member'):
            return obj.is_member(request.user)
        
        # For group-related objects (posts, comments), check group membership
        if hasattr(obj, 'group'):
            return obj.group.is_member(request.user)
        
        return False


class IsGroupAdminOrOwner(BasePermission):
    """
    Permission for group administration operations.
    Only group admins or object owners can perform admin actions.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if user is group admin
        if hasattr(obj, 'is_admin'):
            if obj.is_admin(request.user):
                return True
        
        # Check if user is the owner of the object
        if hasattr(obj, 'author') and obj.author == request.user:
            return True
        if hasattr(obj, 'created_by') and obj.created_by == request.user:
            return True
        
        # For group-related objects, check group admin status
        if hasattr(obj, 'group'):
            return obj.group.is_admin(request.user)
        
        return False


class IsCompanyAdminOrReadOnly(BasePermission):
    """
    Permission for company-related operations.
    Only company admins can edit company data.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True  # Allow read access to everyone
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin users can edit anything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Company creator can edit
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        
        # Check if user is company admin (if such relationship exists)
        if hasattr(obj, 'admins') and request.user in obj.admins.all():
            return True
        
        return False


class IsJobPosterOrReadOnly(BasePermission):
    """
    Permission for job-related operations.
    Only job posters (company admins) can edit job postings.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True  # Allow read access to everyone
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Admin users can edit anything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Job poster can edit
        if hasattr(obj, 'posted_by'):
            return obj.posted_by == request.user
        
        # Company admin can edit company jobs
        if hasattr(obj, 'company') and hasattr(obj.company, 'created_by'):
            return obj.company.created_by == request.user
        
        return False


class IsApplicationOwnerOrJobPoster(BasePermission):
    """
    Permission for job application operations.
    Only application owners or job posters can access applications.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Application owner can access
        if hasattr(obj, 'user') and obj.user == request.user:
            return True
        
        # Job poster can access applications to their jobs
        if hasattr(obj, 'job'):
            job = obj.job
            if hasattr(job, 'posted_by') and job.posted_by == request.user:
                return True
            if hasattr(job, 'company') and hasattr(job.company, 'created_by'):
                return job.company.created_by == request.user
        
        # Admin users can access
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        return False


class IsAdminOrReadOnly(BasePermission):
    """
    Permission that allows read access to authenticated users,
    but only allows write access to admin users.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_staff or request.user.is_superuser


class IsSelfOrAdminOnly(BasePermission):
    """
    Permission that only allows users to access their own data,
    or admin users to access any data.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access anything
        if request.user.is_staff or request.user.is_superuser:
            return True
        
        # Users can only access their own data
        if isinstance(obj, User):
            return obj == request.user
        
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        return False


class IsAnonymousOrAuthenticated(BasePermission):
    """
    Permission that allows both anonymous and authenticated users.
    Used for endpoints that should be publicly accessible.
    """
    
    def has_permission(self, request, view):
        return True


class RateLimitedPermission(BasePermission):
    """
    Permission that implements additional rate limiting checks.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Check if user is rate limited (this would integrate with middleware)
        # For now, just ensure user is authenticated
        return True


class SecureFileUploadPermission(BasePermission):
    """
    Permission for secure file upload operations.
    Includes additional security checks for file uploads.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Additional checks for file uploads
        if request.method == 'POST' and request.FILES:
            # Check file size limits (handled by Django settings)
            # Check file types (handled by serializers)
            # Log file upload attempts
            logger.info(
                f"File upload attempt by user {request.user.id} "
                f"from IP {self.get_client_ip(request)}"
            )
        
        return True
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class AIServicePermission(BasePermission):
    """
    Permission for AI service operations with usage tracking.
    """
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            # Allow anonymous chat with limitations
            if 'anonymous' in request.path:
                return True
            return False
        
        # Log AI service usage
        logger.info(
            f"AI service access by user {request.user.id} "
            f"endpoint: {request.path}"
        )
        
        return True


def log_permission_denied(user, action, resource, reason=""):
    """
    Log permission denied events for security monitoring.
    """
    logger.warning(
        f"Permission denied: User {user.id if user.is_authenticated else 'anonymous'} "
        f"attempted {action} on {resource}. Reason: {reason}"
    )


def check_object_permissions(user, obj, action):
    """
    Utility function to check object-level permissions.
    """
    if not user.is_authenticated:
        return False
    
    # Admin users have all permissions
    if user.is_staff or user.is_superuser:
        return True
    
    # Check ownership
    if hasattr(obj, 'user') and obj.user == user:
        return True
    if hasattr(obj, 'created_by') and obj.created_by == user:
        return True
    if hasattr(obj, 'author') and obj.author == user:
        return True
    
    return False


def get_user_permissions_context(user):
    """
    Get user permissions context for logging and debugging.
    """
    if not user.is_authenticated:
        return {'authenticated': False}
    
    return {
        'authenticated': True,
        'user_id': user.id,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'groups': list(user.groups.values_list('name', flat=True)),
    }