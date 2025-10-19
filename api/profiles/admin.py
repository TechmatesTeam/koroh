"""
Admin configuration for profiles app.

This module defines admin interface for Profile model management.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for Profile model."""
    
    list_display = [
        'user_email', 'user_full_name', 'headline', 'industry',
        'experience_level', 'has_cv_display', 'has_portfolio_display',
        'is_public', 'is_complete_display', 'updated_at'
    ]
    list_filter = [
        'industry', 'experience_level', 'is_public', 'created_at', 'updated_at'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'headline', 'industry', 'location'
    ]
    readonly_fields = [
        'user', 'cv_uploaded_at', 'cv_metadata', 'portfolio_url',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user',)
        }),
        ('Professional Information', {
            'fields': ('headline', 'summary', 'location', 'industry', 'experience_level')
        }),
        ('Skills and Expertise', {
            'fields': ('skills',)
        }),
        ('CV and Portfolio', {
            'fields': ('cv_file', 'cv_uploaded_at', 'cv_metadata', 'portfolio_url', 'portfolio_settings')
        }),
        ('Privacy Settings', {
            'fields': ('is_public', 'show_email')
        }),
        ('Preferences', {
            'fields': ('preferences',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def user_email(self, obj):
        """Display user email."""
        return obj.user.email
    user_email.short_description = 'Email'
    user_email.admin_order_field = 'user__email'
    
    def user_full_name(self, obj):
        """Display user full name."""
        return obj.user.get_full_name()
    user_full_name.short_description = 'Full Name'
    user_full_name.admin_order_field = 'user__first_name'
    
    def has_cv_display(self, obj):
        """Display CV status with icon."""
        if obj.has_cv:
            return format_html(
                '<span style="color: green;">✓ Yes</span>'
            )
        return format_html(
            '<span style="color: red;">✗ No</span>'
        )
    has_cv_display.short_description = 'Has CV'
    has_cv_display.admin_order_field = 'cv_file'
    
    def has_portfolio_display(self, obj):
        """Display portfolio status with icon."""
        if obj.has_portfolio:
            return format_html(
                '<span style="color: green;">✓ Yes</span>'
            )
        return format_html(
            '<span style="color: red;">✗ No</span>'
        )
    has_portfolio_display.short_description = 'Has Portfolio'
    has_portfolio_display.admin_order_field = 'portfolio_url'
    
    def is_complete_display(self, obj):
        """Display profile completion status with icon."""
        if obj.is_complete:
            return format_html(
                '<span style="color: green;">✓ Complete</span>'
            )
        return format_html(
            '<span style="color: orange;">⚠ Incomplete</span>'
        )
    is_complete_display.short_description = 'Profile Complete'
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user')
    
    def has_add_permission(self, request):
        """Profiles are created automatically, so disable manual creation."""
        return False