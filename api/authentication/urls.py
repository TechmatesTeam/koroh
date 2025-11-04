"""
URL configuration for authentication app.

This module defines URL patterns for authentication-related endpoints
including registration, login, logout, and profile management.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views

app_name = 'authentication'

urlpatterns = [
    # Authentication endpoints
    path('register/', views.UserRegistrationView.as_view(), name='register'),
    path('login/', views.CustomTokenObtainPairView.as_view(), name='login'),
    path('login-alt/', views.UserLoginView.as_view(), name='login_alt'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),
    
    # Email verification endpoints
    path('verify-email/', views.EmailVerificationView.as_view(), name='verify_email'),
    path('resend-verification/', views.ResendVerificationEmailView.as_view(), name='resend_verification'),
    
    # Password reset endpoints
    path('password/reset/', views.PasswordResetRequestView.as_view(), name='password_reset'),
    path('password/reset/confirm/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    
    # JWT token endpoints
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # Profile management
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/detail/', views.user_profile_detail, name='profile_detail'),
    path('password/change/', views.PasswordChangeView.as_view(), name='password_change'),
    
    # Utility endpoints
    path('check-email/', views.check_email_availability, name='check_email'),
    
    # Admin endpoints
    path('users/', views.UserListView.as_view(), name='user_list'),
]