"""
Profile models for Koroh platform.

This module defines the Profile model and related functionality for
user profile management, CV storage, and portfolio settings.
"""

import os
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse

User = get_user_model()


def cv_upload_path(instance, filename):
    """Generate upload path for CV files."""
    return f'cvs/{instance.user.id}/{filename}'


def profile_picture_upload_path(instance, filename):
    """Generate upload path for profile pictures."""
    return f'profiles/{instance.user.id}/{filename}'


class Profile(models.Model):
    """
    User profile model with professional information and settings.
    
    Extends the User model with additional profile fields including
    professional information, CV storage, and portfolio settings.
    """
    
    EXPERIENCE_LEVELS = [
        ('entry', _('Entry Level (0-2 years)')),
        ('junior', _('Junior (2-4 years)')),
        ('mid', _('Mid Level (4-7 years)')),
        ('senior', _('Senior (7-10 years)')),
        ('lead', _('Lead/Principal (10+ years)')),
        ('executive', _('Executive/C-Level')),
    ]
    
    # Core relationship
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_('user')
    )
    
    # Professional information
    headline = models.CharField(
        _('professional headline'),
        max_length=200,
        blank=True,
        help_text=_('Brief professional headline (e.g., "Senior Software Engineer")')
    )
    summary = models.TextField(
        _('professional summary'),
        blank=True,
        help_text=_('Professional summary or bio')
    )
    location = models.CharField(
        _('location'),
        max_length=100,
        blank=True,
        help_text=_('Current location (city, country)')
    )
    industry = models.CharField(
        _('industry'),
        max_length=100,
        blank=True,
        help_text=_('Primary industry or field')
    )
    experience_level = models.CharField(
        _('experience level'),
        max_length=50,
        choices=EXPERIENCE_LEVELS,
        blank=True,
        help_text=_('Professional experience level')
    )
    
    # Skills and expertise
    skills = models.JSONField(
        _('skills'),
        default=list,
        blank=True,
        help_text=_('List of professional skills and technologies')
    )
    
    # CV and portfolio
    cv_file = models.FileField(
        _('CV file'),
        upload_to=cv_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'md'])],
        help_text=_('Upload your CV (PDF, DOC, DOCX, or MD format)')
    )
    cv_uploaded_at = models.DateTimeField(
        _('CV uploaded at'),
        blank=True,
        null=True,
        help_text=_('When the CV was last uploaded')
    )
    cv_metadata = models.JSONField(
        _('CV metadata'),
        default=dict,
        blank=True,
        help_text=_('Extracted metadata from CV')
    )
    
    portfolio_url = models.URLField(
        _('portfolio URL'),
        blank=True,
        help_text=_('Generated portfolio website URL')
    )
    portfolio_settings = models.JSONField(
        _('portfolio settings'),
        default=dict,
        blank=True,
        help_text=_('Portfolio customization settings')
    )
    
    # User preferences
    preferences = models.JSONField(
        _('user preferences'),
        default=dict,
        blank=True,
        help_text=_('User preferences and settings')
    )
    
    # Privacy settings
    is_public = models.BooleanField(
        _('public profile'),
        default=True,
        help_text=_('Whether the profile is publicly visible')
    )
    show_email = models.BooleanField(
        _('show email'),
        default=False,
        help_text=_('Whether to show email address on public profile')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.get_full_name()}'s Profile"
    
    def save(self, *args, **kwargs):
        """Override save to update cv_uploaded_at when CV is uploaded."""
        if self.cv_file and not self.cv_uploaded_at:
            from django.utils import timezone
            self.cv_uploaded_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_complete(self):
        """Check if profile is complete with basic information."""
        return bool(
            self.headline and
            self.summary and
            self.location and
            self.industry and
            self.experience_level
        )
    
    @property
    def has_cv(self):
        """Check if user has uploaded a CV."""
        return bool(self.cv_file)
    
    @property
    def has_portfolio(self):
        """Check if user has a generated portfolio."""
        return bool(self.portfolio_url)
    
    def get_absolute_url(self):
        """Return the absolute URL for this profile."""
        return reverse('profiles:detail', kwargs={'pk': self.pk})
    
    def get_cv_filename(self):
        """Get the original filename of the uploaded CV."""
        if self.cv_file:
            return os.path.basename(self.cv_file.name)
        return None
    
    def get_skills_display(self):
        """Get skills as a comma-separated string."""
        if self.skills:
            return ', '.join(self.skills)
        return ''
    
    def add_skill(self, skill):
        """Add a skill to the skills list."""
        if not self.skills:
            self.skills = []
        if skill not in self.skills:
            self.skills.append(skill)
            self.save(update_fields=['skills'])
    
    def remove_skill(self, skill):
        """Remove a skill from the skills list."""
        if self.skills and skill in self.skills:
            self.skills.remove(skill)
            self.save(update_fields=['skills'])
    
    def update_cv_metadata(self, metadata):
        """Update CV metadata with extracted information."""
        self.cv_metadata = metadata
        self.save(update_fields=['cv_metadata'])