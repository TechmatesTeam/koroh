"""
Admin configuration for Companies app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Company, CompanyFollow, CompanyInsight


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for Company model."""
    
    list_display = [
        'name', 'industry', 'company_size', 'headquarters', 
        'is_verified', 'is_active', 'is_hiring', 'follower_count', 
        'job_count', 'created_at'
    ]
    list_filter = [
        'industry', 'company_size', 'company_type', 'is_verified', 
        'is_active', 'is_hiring', 'created_at'
    ]
    search_fields = ['name', 'description', 'industry', 'headquarters']
    readonly_fields = [
        'slug', 'follower_count', 'job_count', 'view_count', 
        'created_at', 'updated_at'
    ]
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'tagline')
        }),
        ('Company Details', {
            'fields': (
                'industry', 'company_size', 'company_type', 'founded_year',
                'headquarters', 'locations'
            )
        }),
        ('Contact & Web Presence', {
            'fields': (
                'website', 'email', 'phone', 'linkedin_url', 
                'twitter_url', 'github_url'
            )
        }),
        ('Media', {
            'fields': ('logo', 'cover_image')
        }),
        ('Culture & Benefits', {
            'fields': ('culture_description', 'benefits', 'tech_stack'),
            'classes': ('collapse',)
        }),
        ('Status & Verification', {
            'fields': ('is_verified', 'is_active', 'is_hiring')
        }),
        ('SEO & Metadata', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'follower_count', 'job_count'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).prefetch_related('followers')


@admin.register(CompanyFollow)
class CompanyFollowAdmin(admin.ModelAdmin):
    """Admin interface for CompanyFollow model."""
    
    list_display = [
        'user', 'company', 'followed_at', 'notifications_enabled',
        'interaction_count', 'last_interaction'
    ]
    list_filter = [
        'followed_at', 'notifications_enabled', 'company__industry'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'company__name'
    ]
    readonly_fields = ['followed_at', 'last_interaction']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('user', 'company')


@admin.register(CompanyInsight)
class CompanyInsightAdmin(admin.ModelAdmin):
    """Admin interface for CompanyInsight model."""
    
    list_display = [
        'company', 'insight_type', 'title', 'confidence_score',
        'is_public', 'created_at', 'expires_at'
    ]
    list_filter = [
        'insight_type', 'is_public', 'created_at', 'expires_at',
        'company__industry'
    ]
    search_fields = ['company__name', 'title', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'insight_type', 'title', 'description')
        }),
        ('Data', {
            'fields': ('data', 'source', 'confidence_score')
        }),
        ('Visibility', {
            'fields': ('is_public', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('company')