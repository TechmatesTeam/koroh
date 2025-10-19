"""
Profile serializers for Koroh platform.

This module defines serializers for Profile model and related
API endpoints with proper validation and field handling.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from .models import Profile

User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information serializer for profile context."""
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'profile_picture', 'is_verified', 'created_at'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'created_at']


class ProfileSerializer(serializers.ModelSerializer):
    """
    Profile serializer with full profile information.
    
    Includes user information and handles file uploads for CV.
    """
    
    user = UserBasicSerializer(read_only=True)
    cv_filename = serializers.CharField(source='get_cv_filename', read_only=True)
    skills_display = serializers.CharField(source='get_skills_display', read_only=True)
    is_complete = serializers.BooleanField(read_only=True)
    has_cv = serializers.BooleanField(read_only=True)
    has_portfolio = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'headline', 'summary', 'location', 'industry',
            'experience_level', 'skills', 'skills_display', 'cv_file',
            'cv_filename', 'cv_uploaded_at', 'cv_metadata', 'portfolio_url',
            'portfolio_settings', 'preferences', 'is_public', 'show_email',
            'is_complete', 'has_cv', 'has_portfolio', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'cv_uploaded_at', 'cv_metadata', 'portfolio_url',
            'created_at', 'updated_at'
        ]
    
    def validate_cv_file(self, value):
        """Validate CV file upload."""
        if value:
            # Check file size (max 10MB)
            if value.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    "CV file size cannot exceed 10MB."
                )
            
            # Validate file extension
            validator = FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'md']
            )
            validator(value)
        
        return value
    
    def validate_skills(self, value):
        """Validate skills list."""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError(
                    "Skills must be provided as a list."
                )
            
            # Limit number of skills
            if len(value) > 50:
                raise serializers.ValidationError(
                    "Maximum 50 skills allowed."
                )
            
            # Validate each skill
            for skill in value:
                if not isinstance(skill, str):
                    raise serializers.ValidationError(
                        "Each skill must be a string."
                    )
                if len(skill.strip()) == 0:
                    raise serializers.ValidationError(
                        "Skills cannot be empty."
                    )
                if len(skill) > 100:
                    raise serializers.ValidationError(
                        "Each skill cannot exceed 100 characters."
                    )
        
        return value
    
    def validate_headline(self, value):
        """Validate professional headline."""
        if value and len(value.strip()) == 0:
            raise serializers.ValidationError(
                "Headline cannot be empty."
            )
        return value
    
    def validate_summary(self, value):
        """Validate professional summary."""
        if value and len(value.strip()) == 0:
            raise serializers.ValidationError(
                "Summary cannot be empty."
            )
        return value


class ProfileCreateSerializer(serializers.ModelSerializer):
    """
    Profile creation serializer for initial profile setup.
    
    Used when creating a new profile with basic information.
    """
    
    class Meta:
        model = Profile
        fields = [
            'headline', 'summary', 'location', 'industry',
            'experience_level', 'skills', 'is_public', 'show_email'
        ]
    
    def validate_skills(self, value):
        """Validate skills list."""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError(
                    "Skills must be provided as a list."
                )
            
            # Limit number of skills
            if len(value) > 50:
                raise serializers.ValidationError(
                    "Maximum 50 skills allowed."
                )
            
            # Validate each skill
            for skill in value:
                if not isinstance(skill, str):
                    raise serializers.ValidationError(
                        "Each skill must be a string."
                    )
                if len(skill.strip()) == 0:
                    raise serializers.ValidationError(
                        "Skills cannot be empty."
                    )
                if len(skill) > 100:
                    raise serializers.ValidationError(
                        "Each skill cannot exceed 100 characters."
                    )
        
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Profile update serializer for partial updates.
    
    Allows updating specific profile fields without requiring all fields.
    """
    
    class Meta:
        model = Profile
        fields = [
            'headline', 'summary', 'location', 'industry',
            'experience_level', 'skills', 'preferences',
            'is_public', 'show_email'
        ]
    
    def validate_skills(self, value):
        """Validate skills list."""
        if value:
            if not isinstance(value, list):
                raise serializers.ValidationError(
                    "Skills must be provided as a list."
                )
            
            # Limit number of skills
            if len(value) > 50:
                raise serializers.ValidationError(
                    "Maximum 50 skills allowed."
                )
            
            # Validate each skill
            for skill in value:
                if not isinstance(skill, str):
                    raise serializers.ValidationError(
                        "Each skill must be a string."
                    )
                if len(skill.strip()) == 0:
                    raise serializers.ValidationError(
                        "Skills cannot be empty."
                    )
                if len(skill) > 100:
                    raise serializers.ValidationError(
                        "Each skill cannot exceed 100 characters."
                    )
        
        return value


class CVUploadSerializer(serializers.ModelSerializer):
    """
    CV upload serializer for handling CV file uploads.
    
    Specialized serializer for CV upload functionality.
    """
    
    class Meta:
        model = Profile
        fields = ['cv_file']
    
    def validate_cv_file(self, value):
        """Validate CV file upload."""
        if not value:
            raise serializers.ValidationError(
                "CV file is required."
            )
        
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "CV file size cannot exceed 10MB."
            )
        
        # Validate file extension
        validator = FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'md']
        )
        validator(value)
        
        return value


class ProfilePublicSerializer(serializers.ModelSerializer):
    """
    Public profile serializer for displaying profiles to other users.
    
    Excludes private information and respects privacy settings.
    """
    
    user = UserBasicSerializer(read_only=True)
    skills_display = serializers.CharField(source='get_skills_display', read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'headline', 'summary', 'location', 'industry',
            'experience_level', 'skills', 'skills_display', 'portfolio_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'headline', 'summary', 'location', 'industry',
            'experience_level', 'skills', 'skills_display', 'portfolio_url',
            'created_at', 'updated_at'
        ]
    
    def to_representation(self, instance):
        """Customize representation based on privacy settings."""
        data = super().to_representation(instance)
        
        # Remove email if user doesn't want to show it
        if not instance.show_email and 'user' in data and 'email' in data['user']:
            data['user']['email'] = None
        
        return data