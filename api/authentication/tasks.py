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
def send_verification_email_task(self, user_id, verification_token):
    """
    Background task to send email verification email to new users.
    
    Args:
        user_id: ID of the user to send verification email to
        verification_token: Email verification token
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Import here to avoid circular imports
        from authentication.email_templates import send_welcome_email
        
        # Send professional welcome email with verification
        success = send_welcome_email(user, verification_token)
        
        if success:
            logger.info(f"Verification email sent to {user.email}")
            return {'success': True, 'email_sent': True}
        else:
            return {'success': False, 'error': 'Failed to send email'}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send verification email to user {user_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_account_verified_email_task(self, user_id):
    """
    Background task to send account verified confirmation email.
    
    Args:
        user_id: ID of the user whose account was verified
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Import here to avoid circular imports
        from authentication.email_templates import send_account_verified_email
        
        # Send account verified email
        success = send_account_verified_email(user)
        
        if success:
            logger.info(f"Account verified email sent to {user.email}")
            return {'success': True, 'email_sent': True}
        else:
            return {'success': False, 'error': 'Failed to send email'}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send account verified email to user {user_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_password_reset_success_email_task(self, user_id):
    """
    Background task to send password reset success email.
    
    Args:
        user_id: ID of the user whose password was reset
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Import here to avoid circular imports
        from authentication.email_templates import send_password_reset_success_email
        
        # Send password reset success email
        success = send_password_reset_success_email(user)
        
        if success:
            logger.info(f"Password reset success email sent to {user.email}")
            return {'success': True, 'email_sent': True}
        else:
            return {'success': False, 'error': 'Failed to send email'}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send password reset success email to user {user_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_password_reset_email_task(self, user_id, reset_token):
    """
    Background task to send password reset email.
    
    Args:
        user_id: ID of the user requesting password reset
        reset_token: Password reset token
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Import here to avoid circular imports
        from authentication.email_templates import send_password_reset_email
        
        # Send professional password reset email
        success = send_password_reset_email(user, reset_token)
        
        if success:
            logger.info(f"Password reset email sent to {user.email}")
            return {'success': True, 'email_sent': True}
        else:
            return {'success': False, 'error': 'Failed to send email'}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send password reset email to user {user_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}

@shared_task
def cleanup_expired_verification_tokens():
    """
    Background task to clean up expired verification and reset tokens.
    
    This task should be scheduled to run daily to maintain database performance.
    """
    try:
        from authentication.models import EmailVerificationToken, PasswordResetToken
        
        # Clean up expired verification tokens
        verification_count = EmailVerificationToken.cleanup_expired_tokens()
        
        # Clean up expired password reset tokens
        reset_count = PasswordResetToken.cleanup_expired_tokens()
        
        result = {
            'verification_tokens_deleted': verification_count,
            'reset_tokens_deleted': reset_count,
            'total_deleted': verification_count + reset_count
        }
        
        logger.info(f"Token cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Token cleanup failed: {e}")
        return {'success': False, 'error': str(e)}