"""
Job models for Koroh platform.

This module defines the Job model and related functionality for
job postings, applications, and search optimization.
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from companies.models import Company

User = get_user_model()


class Job(models.Model):
    """
    Job posting model with company relationship and job details.
    
    Represents job postings with comprehensive information including
    requirements, benefits, and application tracking.
    """
    
    JOB_TYPES = [
        ('full_time', _('Full-time')),
        ('part_time', _('Part-time')),
        ('contract', _('Contract')),
        ('freelance', _('Freelance')),
        ('internship', _('Internship')),
        ('temporary', _('Temporary')),
    ]
    
    EXPERIENCE_LEVELS = [
        ('entry', _('Entry Level (0-2 years)')),
        ('junior', _('Junior (2-4 years)')),
        ('mid', _('Mid Level (4-7 years)')),
        ('senior', _('Senior (7-10 years)')),
        ('lead', _('Lead/Principal (10+ years)')),
        ('executive', _('Executive/C-Level')),
    ]
    
    WORK_ARRANGEMENTS = [
        ('onsite', _('On-site')),
        ('remote', _('Remote')),
        ('hybrid', _('Hybrid')),
    ]
    
    APPLICATION_STATUSES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('paused', _('Paused')),
        ('closed', _('Closed')),
        ('filled', _('Filled')),
    ]
    
    # Basic job information
    title = models.CharField(
        _('job title'),
        max_length=200,
        help_text=_('Job position title')
    )
    slug = models.SlugField(
        _('slug'),
        max_length=250,
        help_text=_('URL-friendly job identifier')
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='jobs',
        verbose_name=_('company'),
        help_text=_('Company posting this job')
    )
    
    # Job details
    description = models.TextField(
        _('job description'),
        help_text=_('Detailed job description and responsibilities')
    )
    summary = models.CharField(
        _('job summary'),
        max_length=500,
        blank=True,
        help_text=_('Brief job summary for listings')
    )
    
    # Job classification
    job_type = models.CharField(
        _('job type'),
        max_length=50,
        choices=JOB_TYPES,
        help_text=_('Type of employment')
    )
    experience_level = models.CharField(
        _('experience level'),
        max_length=50,
        choices=EXPERIENCE_LEVELS,
        help_text=_('Required experience level')
    )
    work_arrangement = models.CharField(
        _('work arrangement'),
        max_length=50,
        choices=WORK_ARRANGEMENTS,
        default='onsite',
        help_text=_('Work location arrangement')
    )
    
    # Location information
    location = models.CharField(
        _('job location'),
        max_length=200,
        help_text=_('Job location (city, state, country)')
    )
    is_remote_friendly = models.BooleanField(
        _('remote friendly'),
        default=False,
        help_text=_('Whether remote work is allowed')
    )
    timezone_requirements = models.CharField(
        _('timezone requirements'),
        max_length=100,
        blank=True,
        help_text=_('Required timezone overlap (for remote jobs)')
    )
    
    # Compensation
    salary_min = models.PositiveIntegerField(
        _('minimum salary'),
        blank=True,
        null=True,
        help_text=_('Minimum salary amount')
    )
    salary_max = models.PositiveIntegerField(
        _('maximum salary'),
        blank=True,
        null=True,
        help_text=_('Maximum salary amount')
    )
    salary_currency = models.CharField(
        _('salary currency'),
        max_length=3,
        default='USD',
        help_text=_('Currency code (e.g., USD, EUR)')
    )
    salary_period = models.CharField(
        _('salary period'),
        max_length=20,
        choices=[
            ('hourly', _('Per Hour')),
            ('daily', _('Per Day')),
            ('weekly', _('Per Week')),
            ('monthly', _('Per Month')),
            ('yearly', _('Per Year')),
        ],
        default='yearly',
        help_text=_('Salary payment period')
    )
    equity_offered = models.BooleanField(
        _('equity offered'),
        default=False,
        help_text=_('Whether equity/stock options are offered')
    )
    
    # Requirements and qualifications
    requirements = models.JSONField(
        _('job requirements'),
        default=list,
        help_text=_('List of job requirements and qualifications')
    )
    skills_required = models.JSONField(
        _('required skills'),
        default=list,
        help_text=_('List of required technical skills')
    )
    skills_preferred = models.JSONField(
        _('preferred skills'),
        default=list,
        help_text=_('List of preferred/nice-to-have skills')
    )
    education_requirements = models.TextField(
        _('education requirements'),
        blank=True,
        help_text=_('Educational background requirements')
    )
    
    # Benefits and perks
    benefits = models.JSONField(
        _('benefits'),
        default=list,
        blank=True,
        help_text=_('List of job benefits and perks')
    )
    
    # Application information
    application_deadline = models.DateTimeField(
        _('application deadline'),
        blank=True,
        null=True,
        help_text=_('Deadline for job applications')
    )
    application_url = models.URLField(
        _('external application URL'),
        blank=True,
        help_text=_('External URL for job applications (optional)')
    )
    application_email = models.EmailField(
        _('application email'),
        blank=True,
        help_text=_('Email for job applications (optional)')
    )
    application_instructions = models.TextField(
        _('application instructions'),
        blank=True,
        help_text=_('Special instructions for applicants')
    )
    
    # Job status and visibility
    status = models.CharField(
        _('job status'),
        max_length=20,
        choices=APPLICATION_STATUSES,
        default='draft',
        help_text=_('Current status of the job posting')
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Whether the job is actively accepting applications')
    )
    is_featured = models.BooleanField(
        _('featured'),
        default=False,
        help_text=_('Whether this is a featured job posting')
    )
    is_urgent = models.BooleanField(
        _('urgent'),
        default=False,
        help_text=_('Whether this is an urgent hiring need')
    )
    
    # SEO and search optimization
    meta_description = models.CharField(
        _('meta description'),
        max_length=160,
        blank=True,
        help_text=_('SEO meta description')
    )
    search_keywords = models.JSONField(
        _('search keywords'),
        default=list,
        blank=True,
        help_text=_('Keywords for search optimization')
    )
    
    # Analytics and tracking
    view_count = models.PositiveIntegerField(
        _('view count'),
        default=0,
        help_text=_('Number of times this job was viewed')
    )
    application_count = models.PositiveIntegerField(
        _('application count'),
        default=0,
        help_text=_('Number of applications received')
    )
    
    # AI and recommendation data
    ai_match_score = models.FloatField(
        _('AI match score'),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text=_('AI-generated relevance score for recommendations')
    )
    ai_tags = models.JSONField(
        _('AI tags'),
        default=list,
        blank=True,
        help_text=_('AI-generated tags for better matching')
    )
    
    # Timestamps
    posted_date = models.DateTimeField(
        _('posted date'),
        auto_now_add=True,
        help_text=_('When the job was first posted')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When the job was last updated')
    )
    expires_at = models.DateTimeField(
        _('expires at'),
        blank=True,
        null=True,
        help_text=_('When the job posting expires')
    )
    
    class Meta:
        verbose_name = _('Job')
        verbose_name_plural = _('Jobs')
        ordering = ['-posted_date']
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['company', 'is_active']),
            models.Index(fields=['job_type', 'experience_level']),
            models.Index(fields=['location']),
            models.Index(fields=['work_arrangement']),
            models.Index(fields=['salary_min', 'salary_max']),
            models.Index(fields=['posted_date']),
            models.Index(fields=['status', 'is_active']),
            models.Index(fields=['is_featured', 'is_urgent']),
            models.Index(fields=['ai_match_score']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
    
    def save(self, *args, **kwargs):
        """Override save to generate slug and update company job count."""
        if not self.slug:
            from django.utils.text import slugify
            import uuid
            base_slug = slugify(f"{self.title}-{self.company.name}")
            self.slug = f"{base_slug}-{str(uuid.uuid4())[:8]}"
        
        # Update summary if not provided
        if not self.summary and self.description:
            self.summary = self.description[:497] + '...' if len(self.description) > 500 else self.description
        
        super().save(*args, **kwargs)
        
        # Update company job count
        self.company.update_job_count()
    
    def delete(self, *args, **kwargs):
        """Override delete to update company job count."""
        company = self.company
        super().delete(*args, **kwargs)
        company.update_job_count()
    
    def get_absolute_url(self):
        """Return the absolute URL for this job."""
        return reverse('jobs:detail', kwargs={'slug': self.slug})
    
    @property
    def is_expired(self):
        """Check if the job posting has expired."""
        if not self.expires_at:
            return False
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    @property
    def is_published(self):
        """Check if the job is published and active."""
        return self.status == 'published' and self.is_active and not self.is_expired
    
    @property
    def salary_range_display(self):
        """Get formatted salary range display."""
        if not self.salary_min and not self.salary_max:
            return None
        
        currency_symbol = {'USD': '$', 'EUR': '€', 'GBP': '£'}.get(self.salary_currency, self.salary_currency)
        
        if self.salary_min and self.salary_max:
            return f"{currency_symbol}{self.salary_min:,} - {currency_symbol}{self.salary_max:,}"
        elif self.salary_min:
            return f"{currency_symbol}{self.salary_min:,}+"
        elif self.salary_max:
            return f"Up to {currency_symbol}{self.salary_max:,}"
        
        return None
    
    def increment_view_count(self):
        """Increment the view count."""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_application_count(self):
        """Increment the application count."""
        self.application_count += 1
        self.save(update_fields=['application_count'])
    
    def add_requirement(self, requirement):
        """Add a requirement to the requirements list."""
        if not self.requirements:
            self.requirements = []
        if requirement not in self.requirements:
            self.requirements.append(requirement)
            self.save(update_fields=['requirements'])
    
    def add_skill(self, skill, is_required=True):
        """Add a skill to the required or preferred skills list."""
        skill_list = 'skills_required' if is_required else 'skills_preferred'
        skills = getattr(self, skill_list) or []
        
        if skill not in skills:
            skills.append(skill)
            setattr(self, skill_list, skills)
            self.save(update_fields=[skill_list])
    
    def add_benefit(self, benefit):
        """Add a benefit to the benefits list."""
        if not self.benefits:
            self.benefits = []
        if benefit not in self.benefits:
            self.benefits.append(benefit)
            self.save(update_fields=['benefits'])
    
    def get_matching_users(self, limit=10):
        """Get users that might be a good match for this job."""
        from profiles.models import Profile
        
        # Basic matching based on skills and experience level
        matching_profiles = Profile.objects.filter(
            experience_level=self.experience_level,
            skills__overlap=self.skills_required
        ).select_related('user')[:limit]
        
        return [profile.user for profile in matching_profiles]


class JobApplication(models.Model):
    """
    Job application model tracking user applications to jobs.
    
    Tracks job applications with status, timestamps, and additional
    application data like cover letters and custom responses.
    """
    
    APPLICATION_STATUSES = [
        ('pending', _('Pending Review')),
        ('reviewing', _('Under Review')),
        ('shortlisted', _('Shortlisted')),
        ('interview', _('Interview Scheduled')),
        ('offer', _('Offer Extended')),
        ('accepted', _('Offer Accepted')),
        ('rejected', _('Rejected')),
        ('withdrawn', _('Withdrawn')),
    ]
    
    # Core relationship
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='job_applications',
        verbose_name=_('applicant')
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name=_('job')
    )
    
    # Application details
    status = models.CharField(
        _('application status'),
        max_length=20,
        choices=APPLICATION_STATUSES,
        default='pending',
        help_text=_('Current status of the application')
    )
    cover_letter = models.TextField(
        _('cover letter'),
        blank=True,
        help_text=_('Applicant cover letter')
    )
    custom_responses = models.JSONField(
        _('custom responses'),
        default=dict,
        blank=True,
        help_text=_('Responses to custom application questions')
    )
    
    # AI-generated insights
    ai_match_score = models.FloatField(
        _('AI match score'),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text=_('AI-calculated match score for this application')
    )
    ai_summary = models.TextField(
        _('AI summary'),
        blank=True,
        help_text=_('AI-generated summary of the application')
    )
    
    # Tracking and metadata
    source = models.CharField(
        _('application source'),
        max_length=100,
        blank=True,
        help_text=_('Where the application came from')
    )
    referrer = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='referred_applications',
        verbose_name=_('referrer'),
        help_text=_('User who referred this applicant')
    )
    
    # Timestamps
    applied_at = models.DateTimeField(
        _('applied at'),
        auto_now_add=True,
        help_text=_('When the application was submitted')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('When the application was last updated')
    )
    reviewed_at = models.DateTimeField(
        _('reviewed at'),
        blank=True,
        null=True,
        help_text=_('When the application was first reviewed')
    )
    
    class Meta:
        verbose_name = _('Job Application')
        verbose_name_plural = _('Job Applications')
        unique_together = ['user', 'job']
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['job', 'status']),
            models.Index(fields=['applied_at']),
            models.Index(fields=['ai_match_score']),
            models.Index(fields=['status', 'applied_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} -> {self.job.title}"
    
    def save(self, *args, **kwargs):
        """Override save to update job application count."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        if is_new:
            self.job.increment_application_count()
    
    @property
    def is_active(self):
        """Check if the application is in an active state."""
        active_statuses = ['pending', 'reviewing', 'shortlisted', 'interview', 'offer']
        return self.status in active_statuses
    
    def update_status(self, new_status, save=True):
        """Update application status with timestamp tracking."""
        old_status = self.status
        self.status = new_status
        
        # Set reviewed_at timestamp when first reviewed
        if old_status == 'pending' and new_status in ['reviewing', 'shortlisted']:
            from django.utils import timezone
            self.reviewed_at = timezone.now()
        
        if save:
            self.save(update_fields=['status', 'reviewed_at', 'updated_at'])


class JobSavedByUser(models.Model):
    """
    Model for users saving/bookmarking jobs.
    
    Allows users to save jobs for later review and application.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='saved_jobs',
        verbose_name=_('user')
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='saved_by_users',
        verbose_name=_('job')
    )
    
    # Metadata
    saved_at = models.DateTimeField(
        _('saved at'),
        auto_now_add=True,
        help_text=_('When the job was saved')
    )
    notes = models.TextField(
        _('personal notes'),
        blank=True,
        help_text=_('Personal notes about this job')
    )
    
    class Meta:
        verbose_name = _('Saved Job')
        verbose_name_plural = _('Saved Jobs')
        unique_together = ['user', 'job']
        ordering = ['-saved_at']
        indexes = [
            models.Index(fields=['user', 'saved_at']),
            models.Index(fields=['job', 'saved_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} saved {self.job.title}"