"""
Authentication models for Koroh platform.

This module defines the custom User model with email-based authentication
and related authentication functionality.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta
import uuid


class UserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication.
    
    Handles user creation with email as the primary identifier
    instead of username.
    """
    
    def create_user(self, email, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_verified', True)  # Superusers are auto-verified
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model with email-based authentication.
    
    Extends Django's AbstractUser to use email as the primary
    authentication field instead of username.
    """
    
    # Remove username field and use email instead
    username = None
    email = models.EmailField(
        _('email address'),
        unique=True,
        help_text=_('Required. Enter a valid email address.'),
        error_messages={
            'unique': _('A user with that email address already exists.'),
        },
    )
    
    # Additional user fields
    first_name = models.CharField(_('first name'), max_length=150)
    last_name = models.CharField(_('last name'), max_length=150)
    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profiles/',
        blank=True,
        null=True,
        help_text=_('Upload a profile picture (optional)')
    )
    is_verified = models.BooleanField(
        _('verified'),
        default=False,
        help_text=_('Designates whether this user has verified their email address.')
    )
    phone_number = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        help_text=_('Optional phone number')
    )
    date_of_birth = models.DateField(
        _('date of birth'),
        blank=True,
        null=True,
        help_text=_('Optional date of birth')
    )
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    # Use email as the unique identifier for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    # Use custom manager
    objects = UserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        db_table = 'auth_user'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Return the first_name plus the last_name, with a space in between."""
        full_name = f'{self.first_name} {self.last_name}'
        return full_name.strip()
    
    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name
    
    @property
    def is_profile_complete(self):
        """Check if user profile is complete."""
        return bool(
            self.first_name and 
            self.last_name and 
            self.email and 
            self.is_verified
        )


class EmailVerificationToken(models.Model):
    """
    Model for storing email verification tokens.
    
    Used to verify user email addresses during registration
    and email change processes.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='verification_tokens',
        help_text=_('User associated with this verification token')
    )
    token = models.UUIDField(
        _('verification token'),
        default=uuid.uuid4,
        unique=True,
        help_text=_('Unique verification token')
    )
    email = models.EmailField(
        _('email to verify'),
        help_text=_('Email address to be verified')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    expires_at = models.DateTimeField(
        _('expires at'),
        help_text=_('Token expiration time')
    )
    is_used = models.BooleanField(
        _('is used'),
        default=False,
        help_text=_('Whether this token has been used')
    )
    
    class Meta:
        verbose_name = _('Email Verification Token')
        verbose_name_plural = _('Email Verification Tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f'Verification token for {self.email}'
    
    def save(self, *args, **kwargs):
        """Set expiration time if not provided."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if the token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self):
        """Mark the token as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    @classmethod
    def create_for_user(cls, user, email=None):
        """
        Create a new verification token for a user.
        
        Args:
            user: User instance
            email: Email to verify (defaults to user.email)
        
        Returns:
            EmailVerificationToken instance
        """
        if email is None:
            email = user.email
        
        # Invalidate existing tokens for this user and email
        cls.objects.filter(
            user=user,
            email=email,
            is_used=False
        ).update(is_used=True)
        
        # Create new token
        return cls.objects.create(
            user=user,
            email=email
        )
    
    @classmethod
    def cleanup_expired_tokens(cls):
        """Remove expired tokens from the database."""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        
        return expired_count


class PasswordResetToken(models.Model):
    """
    Model for storing password reset tokens.
    
    Used for secure password reset functionality.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        help_text=_('User associated with this reset token')
    )
    token = models.UUIDField(
        _('reset token'),
        default=uuid.uuid4,
        unique=True,
        help_text=_('Unique password reset token')
    )
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True
    )
    expires_at = models.DateTimeField(
        _('expires at'),
        help_text=_('Token expiration time')
    )
    is_used = models.BooleanField(
        _('is used'),
        default=False,
        help_text=_('Whether this token has been used')
    )
    
    class Meta:
        verbose_name = _('Password Reset Token')
        verbose_name_plural = _('Password Reset Tokens')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['user', 'is_used']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f'Password reset token for {self.user.email}'
    
    def save(self, *args, **kwargs):
        """Set expiration time if not provided."""
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if the token has expired."""
        return timezone.now() > self.expires_at
    
    @property
    def is_valid(self):
        """Check if the token is valid (not used and not expired)."""
        return not self.is_used and not self.is_expired
    
    def mark_as_used(self):
        """Mark the token as used."""
        self.is_used = True
        self.save(update_fields=['is_used'])
    
    @classmethod
    def create_for_user(cls, user):
        """
        Create a new password reset token for a user.
        
        Args:
            user: User instance
        
        Returns:
            PasswordResetToken instance
        """
        # Invalidate existing tokens for this user
        cls.objects.filter(
            user=user,
            is_used=False
        ).update(is_used=True)
        
        # Create new token
        return cls.objects.create(user=user)
    
    @classmethod
    def cleanup_expired_tokens(cls):
        """Remove expired tokens from the database."""
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now()
        ).count()
        
        cls.objects.filter(
            expires_at__lt=timezone.now()
        ).delete()
        
        return expired_count