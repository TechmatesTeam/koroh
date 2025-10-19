"""
Celery tasks for Authentication app.
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_tokens():
    """
    Background task to clean up expired JWT tokens.
    
    This task should be scheduled to run daily to maintain database performance.
    """
    try:
        # Clean up expired blacklisted tokens
        expired_blacklisted = BlacklistedToken.objects.filter(
            token__expires_at__lt=timezone.now()
        )
        blacklisted_count = expired_blacklisted.count()
        expired_blacklisted.delete()
        
        # Clean up expired outstanding tokens
        expired_outstanding = OutstandingToken.objects.filter(
            expires_at__lt=timezone.now()
        )
        outstanding_count = expired_outstanding.count()
        expired_outstanding.delete()
        
        result = {
            'blacklisted_tokens_deleted': blacklisted_count,
            'outstanding_tokens_deleted': outstanding_count,
            'total_deleted': blacklisted_count + outstanding_count
        }
        
        logger.info(f"Token cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Token cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_inactive_users():
    """
    Background task to clean up inactive user accounts.
    
    Removes users who haven't verified their email after 30 days.
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        
        inactive_users = User.objects.filter(
            is_active=False,
            date_joined__lt=cutoff_date,
            last_login__isnull=True
        )
        
        count = inactive_users.count()
        inactive_users.delete()
        
        logger.info(f"Cleaned up {count} inactive user accounts")
        return {'inactive_users_deleted': count}
        
    except Exception as e:
        logger.error(f"Inactive user cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_welcome_email(self, user_id):
    """
    Background task to send welcome email to new users.
    
    Args:
        user_id: ID of the user to send welcome email to
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Import here to avoid circular imports
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = "Welcome to Koroh Platform!"
        message = f"""
        Hi {user.first_name or user.email},
        
        Welcome to Koroh! We're excited to have you join our professional networking platform.
        
        Here's what you can do next:
        1. Complete your profile
        2. Upload your CV for AI-powered portfolio generation
        3. Discover job opportunities and companies
        4. Connect with professional peer groups
        
        If you have any questions, feel free to reach out to our support team.
        
        Best regards,
        The Koroh Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return {'success': True, 'email_sent': True}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send welcome email to user {user_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_password_reset_email(self, user_id, reset_token):
    """
    Background task to send password reset email.
    
    Args:
        user_id: ID of the user requesting password reset
        reset_token: Password reset token
    """
    try:
        user = User.objects.get(id=user_id)
        
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = "Password Reset - Koroh Platform"
        message = f"""
        Hi {user.first_name or user.email},
        
        You requested a password reset for your Koroh account.
        
        Please use the following token to reset your password: {reset_token}
        
        If you didn't request this reset, please ignore this email.
        
        Best regards,
        The Koroh Team
        """
        
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False
        )
        
        logger.info(f"Password reset email sent to {user.email}")
        return {'success': True, 'email_sent': True}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send password reset email to user {user_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}