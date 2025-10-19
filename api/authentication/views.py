"""
Authentication views for Koroh platform.

This module defines API views for user registration, login,
profile management, and other authentication-related operations.
"""

from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.db import models
from django.utils.translation import gettext_lazy as _

from .models import User
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
)


class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    
    Allows new users to create an account with email-based authentication.
    Returns user data and JWT tokens upon successful registration.
    """
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        """Create a new user account and return tokens."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the user
        user = serializer.save()
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare response data
        response_data = {
            'message': _('Account created successfully'),
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view.
    
    Extends the default JWT token view to include user profile
    information in the response.
    """
    
    serializer_class = CustomTokenObtainPairSerializer


class UserLoginView(APIView):
    """
    API view for user login.
    
    Alternative login endpoint that uses custom authentication logic
    and returns detailed user information.
    """
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Authenticate user and return tokens with user data."""
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Prepare response data
        response_data = {
            'message': _('Login successful'),
            'user': UserProfileSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)


class UserLogoutView(APIView):
    """
    API view for user logout.
    
    Blacklists the refresh token to prevent further use.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Logout user by blacklisting refresh token."""
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Django logout (clears session)
            logout(request)
            
            return Response(
                {'message': _('Logout successful')},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': _('Invalid token')},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    API view for user profile management.
    
    Allows authenticated users to view and update their profile information.
    """
    
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        """Return the current user's profile."""
        return self.request.user
    
    def update(self, request, *args, **kwargs):
        """Update user profile."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        
        return Response({
            'message': _('Profile updated successfully'),
            'user': serializer.data
        })


class PasswordChangeView(APIView):
    """
    API view for password change.
    
    Allows authenticated users to change their password.
    """
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Change user password."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(
            {'message': _('Password changed successfully')},
            status=status.HTTP_200_OK
        )


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_profile_detail(request):
    """
    Get current user's profile information.
    
    Simple function-based view for retrieving user profile data.
    """
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def check_email_availability(request):
    """
    Check if an email address is available for registration.
    
    Utility endpoint to check email availability without creating an account.
    """
    email = request.data.get('email', '').lower().strip()
    
    if not email:
        return Response(
            {'error': _('Email address is required')},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    is_available = not User.objects.filter(email=email).exists()
    
    return Response({
        'email': email,
        'available': is_available,
        'message': _('Email is available') if is_available else _('Email is already taken')
    })


class UserListView(generics.ListAPIView):
    """
    API view for listing users (admin only).
    
    Provides a paginated list of all users for administrative purposes.
    """
    
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        """Filter users based on query parameters."""
        queryset = super().get_queryset()
        
        # Filter by verification status
        is_verified = self.request.query_params.get('is_verified')
        if is_verified is not None:
            queryset = queryset.filter(is_verified=is_verified.lower() == 'true')
        
        # Search by name or email
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                models.Q(first_name__icontains=search) |
                models.Q(last_name__icontains=search) |
                models.Q(email__icontains=search)
            )
        
        return queryset.order_by('-created_at')
