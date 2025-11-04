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
import logging

from .models import User, EmailVerificationToken, PasswordResetToken
from .serializers import (
    UserRegistrationSerializer,
    UserLoginSerializer,
    CustomTokenObtainPairSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    EmailVerificationSerializer,
    ResendVerificationSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)
from koroh_platform.permissions import (
    IsSelfOrAdminOnly,
    IsAnonymousOrAuthenticated,
    log_permission_denied
)

logger = logging.getLogger('koroh_platform.security')


class UserRegistrationView(generics.CreateAPIView):
    """
    API view for user registration.
    
    Allows new users to create an account with email-based authentication.
    Returns user data and JWT tokens upon successful registration.
    """
    
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [IsAnonymousOrAuthenticated]
    
    def create(self, request, *args, **kwargs):
        """Create a new user account and send verification email."""
        # Log registration attempt
        client_ip = self.get_client_ip(request)
        logger.info(f"Registration attempt from IP {client_ip}")
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the user (not verified by default)
        user = serializer.save()
        
        # Log successful registration
        logger.info(f"User {user.id} registered successfully from IP {client_ip}")
        
        # Create verification token and send email
        verification_token = EmailVerificationToken.create_for_user(user)
        
        # Send verification email synchronously (temporary fix until Celery is working)
        from .email_templates import send_welcome_email
        try:
            email_sent = send_welcome_email(user, str(verification_token.token))
            if email_sent:
                logger.info(f"Verification email sent synchronously to {user.email}")
            else:
                logger.error(f"Failed to send verification email to {user.email}")
        except Exception as e:
            logger.error(f"Error sending verification email to {user.email}: {str(e)}")
            email_sent = False
        
        # Prepare response data (no tokens until verified)
        response_data = {
            'message': _('Account created successfully. Please check your email to verify your account.'),
            'user': UserProfileSerializer(user).data,
            'verification_required': True,
            'email': user.email,
            'email_sent': email_sent if 'email_sent' in locals() else False
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom JWT token obtain view.
    
    Extends the default JWT token view to include user profile
    information in the response and check email verification.
    """
    
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        """Override to add email verification check."""
        # Get client IP for logging
        client_ip = self.get_client_ip(request)
        email = request.data.get('email', 'unknown')
        logger.info(f"Login attempt for {email} from IP {client_ip}")
        
        try:
            # Call parent method to get tokens
            response = super().post(request, *args, **kwargs)
            
            # Check if user is verified
            if response.status_code == 200:
                user_data = response.data.get('user', {})
                if not user_data.get('is_verified', False):
                    logger.warning(f"Unverified user {user_data.get('id')} attempted login from IP {client_ip}")
                    return Response({
                        'error': _('Please verify your email address before logging in.'),
                        'verification_required': True,
                        'email': user_data.get('email')
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # Log successful login
                logger.info(f"User {user_data.get('id')} logged in successfully from IP {client_ip}")
            
            return response
            
        except Exception as e:
            # Log failed login attempt
            logger.warning(f"Failed login attempt for {email} from IP {client_ip}: {str(e)}")
            raise
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class UserLoginView(APIView):
    """
    API view for user login.
    
    Alternative login endpoint that uses custom authentication logic
    and returns detailed user information.
    """
    
    permission_classes = [IsAnonymousOrAuthenticated]
    
    def post(self, request):
        """Authenticate user and return tokens with user data."""
        # Log login attempt
        client_ip = self.get_client_ip(request)
        email = request.data.get('email', 'unknown')
        logger.info(f"Login attempt for {email} from IP {client_ip}")
        
        serializer = UserLoginSerializer(
            data=request.data,
            context={'request': request}
        )
        
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            
            # Check if user is verified
            if not user.is_verified:
                logger.warning(f"Unverified user {user.id} attempted login from IP {client_ip}")
                return Response({
                    'error': _('Please verify your email address before logging in.'),
                    'verification_required': True,
                    'email': user.email
                }, status=status.HTTP_403_FORBIDDEN)
            
            # Log successful login
            logger.info(f"User {user.id} logged in successfully from IP {client_ip}")
            
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
            
        except Exception as e:
            # Log failed login attempt
            logger.warning(f"Failed login attempt for {email} from IP {client_ip}: {str(e)}")
            raise
    
    def get_client_ip(self, request):
        """Get client IP address."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


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
    permission_classes = [IsSelfOrAdminOnly]
    
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
@permission_classes([IsAnonymousOrAuthenticated])
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
    
    def list(self, request, *args, **kwargs):
        """List users with security logging."""
        logger.info(f"Admin user {request.user.id} accessed user list")
        return super().list(request, *args, **kwargs)
    
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


class EmailVerificationView(APIView):
    """
    API view for email verification.
    
    Verifies user email address using verification token.
    """
    
    permission_classes = [IsAnonymousOrAuthenticated]
    
    def post(self, request):
        """Verify email address using token."""
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_str = serializer.validated_data['token']
        
        try:
            # Find the verification token
            verification_token = EmailVerificationToken.objects.get(
                token=token_str,
                is_used=False
            )
            
            # Check if token is expired
            if verification_token.is_expired:
                return Response({
                    'error': _('Verification token has expired. Please request a new one.'),
                    'expired': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify the user
            user = verification_token.user
            user.is_verified = True
            user.save(update_fields=['is_verified'])
            
            # Mark token as used
            verification_token.mark_as_used()
            
            # Send account verified email
            from .tasks import send_account_verified_email_task
            send_account_verified_email_task.delay(user.id)
            
            # Generate JWT tokens for immediate login
            refresh = RefreshToken.for_user(user)
            
            logger.info(f"User {user.id} email verified successfully")
            
            return Response({
                'message': _('Email verified successfully. You can now log in.'),
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_200_OK)
            
        except EmailVerificationToken.DoesNotExist:
            return Response({
                'error': _('Invalid or expired verification token.')
            }, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationEmailView(APIView):
    """
    API view for resending verification email.
    
    Allows users to request a new verification email.
    """
    
    permission_classes = [IsAnonymousOrAuthenticated]
    
    def post(self, request):
        """Resend verification email."""
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email)
            
            # Check if user is already verified
            if user.is_verified:
                return Response({
                    'message': _('This email address is already verified.')
                }, status=status.HTTP_200_OK)
            
            # Create new verification token
            verification_token = EmailVerificationToken.create_for_user(user)
            
            # Send verification email
            from .tasks import send_verification_email_task
            send_verification_email_task.delay(user.id, str(verification_token.token))
            
            logger.info(f"Verification email resent to {email}")
            
            return Response({
                'message': _('Verification email sent. Please check your inbox.')
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            # Don't reveal if email exists for security
            return Response({
                'message': _('If this email is registered, a verification email will be sent.')
            }, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """
    API view for password reset request.
    
    Sends password reset email to user.
    """
    
    permission_classes = [IsAnonymousOrAuthenticated]
    
    def post(self, request):
        """Request password reset."""
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Create password reset token
            reset_token = PasswordResetToken.create_for_user(user)
            
            # Send password reset email
            from .tasks import send_password_reset_email_task
            send_password_reset_email_task.delay(user.id, str(reset_token.token))
            
            logger.info(f"Password reset email sent to {email}")
            
        except User.DoesNotExist:
            # Don't reveal if email exists for security
            pass
        
        # Always return success message for security
        return Response({
            'message': _('If this email is registered, a password reset link will be sent.')
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):
    """
    API view for password reset confirmation.
    
    Resets user password using reset token.
    """
    
    permission_classes = [IsAnonymousOrAuthenticated]
    
    def post(self, request):
        """Reset password using token."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token_str = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        try:
            # Find the reset token
            reset_token = PasswordResetToken.objects.get(
                token=token_str,
                is_used=False
            )
            
            # Check if token is expired
            if reset_token.is_expired:
                return Response({
                    'error': _('Password reset token has expired. Please request a new one.'),
                    'expired': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Reset the password
            user = reset_token.user
            user.set_password(new_password)
            user.save(update_fields=['password'])
            
            # Mark token as used
            reset_token.mark_as_used()
            
            # Send password reset success email
            from .tasks import send_password_reset_success_email_task
            send_password_reset_success_email_task.delay(user.id)
            
            logger.info(f"Password reset successful for user {user.id}")
            
            return Response({
                'message': _('Password reset successful. You can now log in with your new password.')
            }, status=status.HTTP_200_OK)
            
        except PasswordResetToken.DoesNotExist:
            return Response({
                'error': _('Invalid or expired password reset token.')
            }, status=status.HTTP_400_BAD_REQUEST)
