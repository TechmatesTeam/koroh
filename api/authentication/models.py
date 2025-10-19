"""
Authentication models for Koroh platform.

This module defines the custom User model with email-based authentication
and related authentication functionality.
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


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
