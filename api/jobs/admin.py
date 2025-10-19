"""
Admin configuration for Jobs app.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Job, JobApplication, JobSavedByUser


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for Job model."""
    
    list_display = [
        'title', 'company', 'job_type', 'experience_level', 
        'location', 'work_arrangement', 'status', 'is_active',
        'view_count', 'application_count', 'posted_date'
    ]
    list_filter = [
        'job_type', 'experience_level', 'work_arrangement', 'status',
        'is_active', 'is_featured', 'is_urgent', 'posted_date',
        'company__industry'
    ]
    search_fields = [
        'title', 'description', 'company__name', 'location',
        'skills_required', 'skills_preferred'
    ]
    readonly_fields = [
        'slug', 'view_count', 'application_count', 'ai_match_score',
        'posted_date', 'updated_at'
    ]
    prepopulated_fields = {'slug': ('title',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'company', 'description', 'summary')
        }),
        ('Job Classification', {
            'fields': (
                'job_type', 'experience_level', 'work_arrangement',
                'status', 'is_active', 'is_featured', 'is_urgent'
            )
        }),
        ('Location', {
            'fields': (
                'location', 'is_remote_friendly', 'timezone_requirements'
            )
        }),
        ('Compensation', {
            'fields': (
                'salary_min', 'salary_max', 'salary_currency', 
                'salary_period', 'equity_offered'
            )
        }),
        ('Requirements', {
            'fields': (
                'requirements', 'skills_required', 'skills_preferred',
                'education_requirements'
            )
        }),
        ('Benefits', {
            'fields': ('benefits',)
        }),
        ('Application Details', {
            'fields': (
                'application_deadline', 'application_url', 
                'application_email', 'application_instructions'
            )
        }),
        ('SEO & Search', {
            'fields': ('meta_description', 'search_keywords'),
            'classes': ('collapse',)
        }),
        ('AI & Analytics', {
            'fields': (
                'ai_match_score', 'ai_tags', 'view_count', 
                'application_count'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('posted_date', 'updated_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related('company')
    
    def salary_range(self, obj):
        """Display formatted salary range."""
        return obj.salary_range_display or 'Not specified'
    salary_range.short_description = 'Salary Range'


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    """Admin interface for JobApplication model."""
    
    list_display = [
        'user', 'job', 'status', 'ai_match_score',
        'applied_at', 'reviewed_at'
    ]
    list_filter = [
        'status', 'applied_at', 'reviewed_at', 'job__company',
        'job__job_type', 'job__experience_level'
    ]
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'job__title', 'job__company__name'
    ]
    readonly_fields = [
        'applied_at', 'updated_at', 'reviewed_at', 'ai_match_score'
    ]
    
    fieldsets = (
        ('Application Details', {
            'fields': ('user', 'job', 'status', 'cover_letter')
        }),
        ('Custom Responses', {
            'fields': ('custom_responses',),
            'classes': ('collapse',)
        }),
        ('AI Insights', {
            'fields': ('ai_match_score', 'ai_summary'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('source', 'referrer')
        }),
        ('Timestamps', {
            'fields': ('applied_at', 'updated_at', 'reviewed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'user', 'job', 'job__company', 'referrer'
        )
    
    def job_company(self, obj):
        """Display job company name."""
        return obj.job.company.name
    job_company.short_description = 'Company'
    job_company.admin_order_field = 'job__company__name'


@admin.register(JobSavedByUser)
class JobSavedByUserAdmin(admin.ModelAdmin):
    """Admin interface for JobSavedByUser model."""
    
    list_display = ['user', 'job', 'saved_at', 'has_notes']
    list_filter = ['saved_at', 'job__company', 'job__job_type']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name',
        'job__title', 'job__company__name'
    ]
    readonly_fields = ['saved_at']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        return super().get_queryset(request).select_related(
            'user', 'job', 'job__company'
        )
    
    def has_notes(self, obj):
        """Check if the saved job has notes."""
        return bool(obj.notes)
    has_notes.boolean = True
    has_notes.short_description = 'Has Notes'
    
    def job_company(self, obj):
        """Display job company name."""
        return obj.job.company.name
    job_company.short_description = 'Company'
    job_company.admin_order_field = 'job__company__name'