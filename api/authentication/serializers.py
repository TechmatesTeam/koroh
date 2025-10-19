"""
Authentication serializers for Koroh platform.

This module defines serializers for user registration, login,
and profile management using Django REST Framework.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    
    Handles user account creation with email-based authentication,
    password validation, and basic profile information.
    """
    
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
        help_text='Password must be at least 8 characters long'
    )
    password_confirm = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text='Confirm your password'
    )
    
    class Meta:
        model = User
        fields = [
            'email',
            'first_name',
            'last_name',
            'password',
            'password_confirm',
            'phone_number',
            'date_of_birth'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError(
                'A user with this email address already exists.'
            )
        return value.lower()
    
    def validate_password(self, value):
        """Validate password using Django's password validators."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Password confirmation does not match.'
            })
        return attrs
    
    def create(self, validated_data):
        """Create a new user account."""
        # Remove password_confirm from validated_data
        validated_data.pop('password_confirm', None)
        
        # Create user with encrypted password
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data.get('phone_number', ''),
            date_of_birth=validated_data.get('date_of_birth'),
        )
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer for user login.
    
    Handles email/password authentication and returns user data
    along with JWT tokens.
    """
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        """Authenticate user credentials."""
        email = attrs.get('email', '').lower()
        password = attrs.get('password', '')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,  # Django uses username field for authentication
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Invalid email or password.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include email and password.'
            )


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes additional user data.
    
    Extends the default JWT serializer to include user profile
    information in the token response.
    """
    
    username_field = 'email'
    
    @classmethod
    def get_token(cls, user):
        """Add custom claims to JWT token."""
        token = super().get_token(user)
        
        # Add custom claims
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_verified'] = user.is_verified
        
        return token
    
    def validate(self, attrs):
        """Validate and return token data with user information."""
        data = super().validate(attrs)
        
        # Add user data to response
        data['user'] = {
            'id': self.user.id,
            'email': self.user.email,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
            'is_verified': self.user.is_verified,
            'profile_picture': self.user.profile_picture.url if self.user.profile_picture else None,
            'is_profile_complete': self.user.is_profile_complete,
        }
        
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile information.
    
    Used for retrieving and updating user profile data.
    """
    
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'profile_picture',
            'phone_number',
            'date_of_birth',
            'is_verified',
            'is_profile_complete',
            'date_joined',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'email',
            'is_verified',
            'date_joined',
            'created_at',
            'updated_at',
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """
    Serializer for password change functionality.
    
    Allows authenticated users to change their password.
    """
    
    current_password = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        min_length=8,
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_current_password(self, value):
        """Validate current password."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
    
    def validate_new_password(self, value):
        """Validate new password."""
        try:
            validate_password(value, user=self.context['request'].user)
        except ValidationError as e:
            raise serializers.ValidationError(e.messages)
        return value
    
    def validate(self, attrs):
        """Validate password confirmation."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'New password confirmation does not match.'
            })
        return attrs
    
    def save(self):
        """Update user password."""
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user