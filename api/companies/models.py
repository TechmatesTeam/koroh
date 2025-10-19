"""
Company models for Koroh platform.

This module defines the Company model and related functionality for
company profiles, tracking, and social features.
"""

import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

User = get_user_model()


def company_logo_upload_path(instance, filename):
    """Generate upload path for company logos."""
    return f'companies/{instance.id}/{filename}'


class Company(models.Model):
    """
    Company model with profile information and social features.
    
    Represents companies that can post jobs and be followed by users.
    Includes company profile information, social features, and analytics.
    """
    
    COMPANY_SIZES = [
        ('startup', _('Startup (1-10 employees)')),
        ('small', _('Small (11-50 employees)')),
        ('medium', _('Medium (51-200 employees)')),
        ('large', _('Large (201-1000 employees)')),
        ('enterprise', _('Enterprise (1000+ employees)')),
    ]
    
    COMPANY_TYPES = [
        ('public', _('Public Company')),
        ('private', _('Private Company')),
        ('nonprofit', _('Non-Profit')),
        ('government', _('Government')),
        ('startup', _('Startup')),
        ('agency', _('Agency')),
        ('consultancy', _('Consultancy')),
    ]
    
    # Basic company information
    name = models.CharField(
        _('company name'),
        max_length=200,
        unique=True,
        help_text=_('Official company name')
    )
    slug = models.SlugField(
        _('slug'),
        max_length=200,
        unique=True,
        help_text=_('URL-friendly company identifier')
    )
    description = models.TextField(
        _('company description'),
        help_text=_('Company overview and description')
    )
    tagline = models.CharField(
        _('tagline'),
        max_length=200,
        blank=True,
        help_text=_('Short company tagline or mission statement')
    )
    
    # Company details
    industry = models.CharField(
        _('industry'),
        max_length=100,
        help_text=_('Primary industry or sector')
    )
    company_size = models.CharField(
        _('company size'),
        max_length=50,
        choices=COMPANY_SIZES,
        help_text=_('Number of employees')
    )
    company_type = models.CharField(
        _('company type'),
        max_length=50,
        choices=COMPANY_TYPES,
        help_text=_('Type of organization')
    )
    founded_year = models.PositiveIntegerField(
        _('founded year'),
        blank=True,
        null=True,
        help_text=_('Year the company was founded')
    )
    
    # Location information
    headquarters = models.CharField(
        _('headquarters'),
        max_length=200,
        help_text=_('Main headquarters location')
    )
    locations = models.JSONField(
        _('office locations'),
        default=list,
        blank=True,
        help_text=_('List of office locations')
    )
    
    # Contact and web presence
    website = models.URLField(
        _('website'),
        validators=[URLValidator()],
        help_text=_('Company website URL')
    )
    email = models.EmailField(
        _('contact email'),
        blank=True,
        help_text=_('General contact email')
    )
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        help_text=_('Contact phone number')
    )
    
    # Social media links
    linkedin_url = models.URLField(
        _('LinkedIn URL'),
        blank=True,
        help_text=_('Company LinkedIn profile')
    )
    twitter_url = models.URLField(
        _('Twitter URL'),
        blank=True,
        help_text=_('Company Twitter profile')
    )
    github_url = models.URLField(
        _('GitHub URL'),
        blank=True,
        help_text=_('Company GitHub organization')
    )
    
    # Media
    logo = models.ImageField(
        _('company logo'),
        upload_to=company_logo_upload_path,
        blank=True,
        null=True,
        help_text=_('Company logo image')
    )
    cover_image = models.ImageField(
        _('cover image'),
        upload_to=company_logo_upload_path,
        blank=True,
        null=True,
        help_text=_('Company cover/banner image')
    )
    
    # Company culture and benefits
    culture_description = models.TextField(
        _('company culture'),
        blank=True,
        help_text=_('Description of company culture and values')
    )
    benefits = models.JSONField(
        _('benefits'),
        default=list,
        blank=True,
        help_text=_('List of employee benefits and perks')
    )
    tech_stack = models.JSONField(
        _('technology stack'),
        default=list,
        blank=True,
        help_text=_('Technologies and tools used by the company')
    )
    
    # Social features
    followers = models.ManyToManyField(
        User,
        through='CompanyFollow',
        related_name='followed_companies',
        blank=True,
        help_text=_('Users following this company')
    )
    
    # Verification and status
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Whether the company profile is verified')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the company is actively posting jobs')
    )
    is_hiring = models.BooleanField(
        _('currently hiring'),
        default=False,
        help_text=_('Whether the company is actively hiring')
    )
    
    # SEO and metadata
    meta_description = models.CharField(
        _('meta description'),
        max_length=160,
        blank=True,
        help_text=_('SEO meta description')
    )
    meta_keywords = models.JSONField(
        _('meta keywords'),
        default=list,
        blank=True,
        help_text=_('SEO keywords')
    )
    
    # Analytics and insights
    view_count = models.PositiveIntegerField(
        _('view count'),
        default=0,
        help_text=_('Number of profile views')
    )
    follower_count = models.PositiveIntegerField(
        _('follower count'),
        default=0,
        help_text=_('Cached follower count for performance')
    )
    job_count = models.PositiveIntegerField(
        _('active job count'),
        default=0,
        help_text=_('Number of active job postings')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Company')
        verbose_name_plural = _('Companies')
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
            models.Index(fields=['industry']),
            models.Index(fields=['company_size']),
            models.Index(fields=['headquarters']),
            models.Index(fields=['is_active', 'is_hiring']),
            models.Index(fields=['created_at']),
            models.Index(fields=['follower_count']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Override save to generate slug if not provided."""
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        """Return the absolute URL for this company."""
        return reverse('companies:detail', kwargs={'slug': self.slug})
    
    @property
    def is_complete(self):
        """Check if company profile is complete."""
        return bool(
            self.name and
            self.description and
            self.industry and
            self.company_size and
            self.headquarters and
            self.website
        )
    
    @property
    def has_logo(self):
        """Check if company has a logo."""
        return bool(self.logo)
    
    def get_follower_count(self):
        """Get the current follower count."""
        return self.followers.count()
    
    def update_follower_count(self):
        """Update the cached follower count."""
        self.follower_count = self.get_follower_count()
        self.save(update_fields=['follower_count'])
    
    def get_active_jobs_count(self):
        """Get the number of active job postings."""
        return self.jobs.filter(is_active=True).count()
    
    def update_job_count(self):
        """Update the cached job count."""
        self.job_count = self.get_active_jobs_count()
        self.save(update_fields=['job_count'])
    
    def increment_view_count(self):
        """Increment the view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def add_benefit(self, benefit):
        """Add a benefit to the benefits list."""
        if not self.benefits:
            self.benefits = []
        if benefit not in self.benefits:
            self.benefits.append(benefit)
            self.save(update_fields=['benefits'])
    
    def add_tech(self, technology):
        """Add a technology to the tech stack."""
        if not self.tech_stack:
            self.tech_stack = []
        if technology not in self.tech_stack:
            self.tech_stack.append(technology)
            self.save(update_fields=['tech_stack'])


class CompanyFollow(models.Model):
    """
    Through model for company following relationship.
    
    Tracks when users follow/unfollow companies and provides
    additional metadata about the relationship.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='company_follows',
        verbose_name=_('user')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='company_follows',
        verbose_name=_('company')
    )
    
    # Follow metadata
    followed_at = models.DateTimeField(
        _('followed at'),
        auto_now_add=True,
        help_text=_('When the user started following this company')
    )
    notifications_enabled = models.BooleanField(
        _('notifications enabled'),
        default=True,
        help_text=_('Whether to receive notifications about this company')
    )
    
    # Interaction tracking
    last_interaction = models.DateTimeField(
        _('last interaction'),
        blank=True,
        null=True,
        help_text=_('Last time user interacted with company content')
    )
    interaction_count = models.PositiveIntegerField(
        _('interaction count'),
        default=0,
        help_text=_('Number of interactions with company content')
    )
    
    class Meta:
        verbose_name = _('Company Follow')
        verbose_name_plural = _('Company Follows')
        unique_together = ['user', 'company']
        ordering = ['-followed_at']
        indexes = [
            models.Index(fields=['user', 'followed_at']),
            models.Index(fields=['company', 'followed_at']),
            models.Index(fields=['notifications_enabled']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} follows {self.company.name}"
    
    def save(self, *args, **kwargs):
        """Override save to update company follower count."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.company.update_follower_count()
    
    def delete(self, *args, **kwargs):
        """Override delete to update company follower count."""
        company = self.company
        super().delete(*args, **kwargs)
        company.update_follower_count()
    
    def record_interaction(self):
        """Record a user interaction with this company."""
        from django.utils import timezone
        self.last_interaction = timezone.now()
        self.interaction_count += 1
        self.save(update_fields=['last_interaction', 'interaction_count'])


class CompanyInsight(models.Model):
    """
    Company insights and analytics data.
    
    Stores various metrics and insights about companies for
    analytics and recommendation purposes.
    """
    
    INSIGHT_TYPES = [
        ('growth', _('Growth Metrics')),
        ('hiring', _('Hiring Trends')),
        ('culture', _('Culture Score')),
        ('salary', _('Salary Information')),
        ('reviews', _('Employee Reviews')),
        ('news', _('Company News')),
    ]
    
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='insights',
        verbose_name=_('company')
    )
    insight_type = models.CharField(
        _('insight type'),
        max_length=50,
        choices=INSIGHT_TYPES,
        help_text=_('Type of insight data')
    )
    
    # Insight data
    title = models.CharField(
        _('insight title'),
        max_length=200,
        help_text=_('Title or summary of the insight')
    )
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Detailed description of the insight')
    )
    data = models.JSONField(
        _('insight data'),
        default=dict,
        help_text=_('Structured insight data')
    )
    
    # Metadata
    source = models.CharField(
        _('data source'),
        max_length=100,
        blank=True,
        help_text=_('Source of the insight data')
    )
    confidence_score = models.FloatField(
        _('confidence score'),
        default=0.0,
        help_text=_('Confidence score for the insight (0.0-1.0)')
    )
    is_public = models.BooleanField(
        _('public insight'),
        default=True,
        help_text=_('Whether this insight is publicly visible')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    expires_at = models.DateTimeField(
        _('expires at'),
        blank=True,
        null=True,
        help_text=_('When this insight expires (optional)')
    )
    
    class Meta:
        verbose_name = _('Company Insight')
        verbose_name_plural = _('Company Insights')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'insight_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['is_public']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.company.name} - {self.title}"
    
    @property
    def is_expired(self):
        """Check if the insight has expired."""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at