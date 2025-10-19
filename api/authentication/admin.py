"""
Admin configuration for authentication app.

This module defines the Django admin interface for the custom User model
with appropriate fields, filters, and search functionality.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin configuration for the custom User model.
    
    Customizes the Django admin interface to work with email-based
    authentication and additional user fields.
    """
    
    # Fields to display in the user list
    list_display = [
        'email',
        'first_name',
        'last_name',
        'is_verified',
        'is_active',
        'is_staff',
        'created_at',
    ]
    
    # Fields to filter by in the admin sidebar
    list_filter = [
        'is_active',
        'is_staff',
        'is_superuser',
        'is_verified',
        'created_at',
        'last_login',
    ]
    
    # Fields to search by
    search_fields = [
        'email',
        'first_name',
        'last_name',
        'phone_number',
    ]
    
    # Default ordering
    ordering = ['-created_at']
    
    # Fields that are read-only
    readonly_fields = [
        'created_at',
        'updated_at',
        'last_login',
        'date_joined',
    ]
    
    # Fieldsets for the user detail/edit page
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': (
                'first_name',
                'last_name',
                'profile_picture',
                'phone_number',
                'date_of_birth',
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_verified',
                'groups',
                'user_permissions',
            ),
        }),
        (_('Important dates'), {
            'fields': (
                'last_login',
                'date_joined',
                'created_at',
                'updated_at',
            )
        }),
    )
    
    # Fieldsets for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'password1',
                'password2',
                'is_active',
                'is_staff',
                'is_verified',
            ),
        }),
    )
    
    # Actions
    actions = ['make_verified', 'make_unverified', 'activate_users', 'deactivate_users']
    
    def make_verified(self, request, queryset):
        """Mark selected users as verified."""
        updated = queryset.update(is_verified=True)
        self.message_user(
            request,
            f'{updated} user(s) were successfully marked as verified.'
        )
    make_verified.short_description = _('Mark selected users as verified')
    
    def make_unverified(self, request, queryset):
        """Mark selected users as unverified."""
        updated = queryset.update(is_verified=False)
        self.message_user(
            request,
            f'{updated} user(s) were successfully marked as unverified.'
        )
    make_unverified.short_description = _('Mark selected users as unverified')
    
    def activate_users(self, request, queryset):
        """Activate selected users."""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} user(s) were successfully activated.'
        )
    activate_users.short_description = _('Activate selected users')
    
    def deactivate_users(self, request, queryset):
        """Deactivate selected users."""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} user(s) were successfully deactivated.'
        )
    deactivate_users.short_description = _('Deactivate selected users')
