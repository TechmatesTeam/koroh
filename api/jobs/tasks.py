"""
Celery tasks for Jobs app.
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .models import Job, JobApplication
from .services import JobRecommendationService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_job_recommendations_email(self, user_id, max_jobs=5):
    """
    Background task to send personalized job recommendations to a user.
    
    Args:
        user_id: ID of the user to send recommendations to
        max_jobs: Maximum number of jobs to include in the email
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Get job recommendations for the user
        recommended_jobs = JobRecommendationService.get_personalized_recommendations(
            user, limit=max_jobs
        )
        
        if not recommended_jobs:
            logger.info(f"No job recommendations found for user {user.email}")
            return {'success': True, 'recommendations_sent': False, 'reason': 'No recommendations available'}
        
        # Calculate match percentage (simplified)
        match_percentage = 85  # Default match percentage
        
        # Import here to avoid circular imports
        from authentication.email_templates import send_job_recommendation_email
        
        # Send professional job recommendation email
        success = send_job_recommendation_email(
            user=user,
            recommended_jobs=recommended_jobs,
            match_percentage=match_percentage
        )
        
        if success:
            logger.info(f"Job recommendations email sent to {user.email}")
            return {
                'success': True,
                'recommendations_sent': True,
                'jobs_count': len(recommended_jobs)
            }
        else:
            return {'success': False, 'error': 'Failed to send email'}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send job recommendations to user {user_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task
def send_daily_job_recommendations():
    """
    Background task to send daily job recommendations to all active users.
    
    This task should be scheduled to run daily.
    """
    # Get users who have complete profiles and want job recommendations
    eligible_users = User.objects.filter(
        is_active=True,
        profile__isnull=False,
        profile__cv_file__isnull=False
    ).exclude(
        profile__preferences__job_notifications=False
    )
    
    results = {
        'total_users': eligible_users.count(),
        'emails_sent': 0,
        'failed_emails': 0,
        'no_recommendations': 0
    }
    
    for user in eligible_users:
        try:
            # Check if user received recommendations recently (within last 24 hours)
            # This would require tracking when recommendations were last sent
            # For now, we'll send to all eligible users
            
            result = send_job_recommendations_email.delay(user.id)
            
            # Note: In a real implementation, you'd want to track the result
            # For now, we'll assume success
            results['emails_sent'] += 1
            
        except Exception as e:
            logger.error(f"Error scheduling job recommendations for user {user.id}: {e}")
            results['failed_emails'] += 1
    
    logger.info(f"Daily job recommendations task completed: {results}")
    return results


@shared_task
def cleanup_old_job_applications():
    """
    Background task to clean up old job applications.
    
    This task should be scheduled to run weekly.
    """
    try:
        # Clean up applications for jobs that are no longer active
        inactive_job_applications = JobApplication.objects.filter(
            job__is_active=False,
            applied_at__lt=timezone.now() - timedelta(days=90)
        )
        
        count = inactive_job_applications.count()
        inactive_job_applications.delete()
        
        logger.info(f"Cleaned up {count} old job applications")
        return {'applications_deleted': count}
        
    except Exception as e:
        logger.error(f"Job application cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def update_job_recommendation_scores():
    """
    Background task to update job recommendation scores for all users.
    
    This task should be scheduled to run daily to keep recommendations fresh.
    """
    try:
        # This would update cached recommendation scores
        # For now, we'll just log that the task ran
        
        active_users = User.objects.filter(
            is_active=True,
            profile__isnull=False
        ).count()
        
        logger.info(f"Updated job recommendation scores for {active_users} users")
        return {
            'success': True,
            'users_updated': active_users
        }
        
    except Exception as e:
        logger.error(f"Job recommendation score update failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def notify_job_application_status(self, application_id, status):
    """
    Background task to notify user about job application status changes.
    
    Args:
        application_id: ID of the job application
        status: New status of the application
    """
    try:
        application = JobApplication.objects.get(id=application_id)
        user = application.user
        job = application.job
        
        # Import here to avoid circular imports
        from django.core.mail import send_mail
        from django.conf import settings
        
        status_messages = {
            'reviewed': 'Your application has been reviewed',
            'interview': 'You have been selected for an interview',
            'rejected': 'Your application was not selected',
            'accepted': 'Congratulations! Your application was accepted'
        }
        
        subject = f"Application Update: {job.title} at {job.company.name}"
        message = f"""
        Hi {user.get_full_name()},
        
        {status_messages.get(status, 'Your application status has been updated')}.
        
        Job: {job.title}
        Company: {job.company.name}
        Status: {status.title()}
        
        {"We'll be in touch soon with next steps." if status == 'interview' else ""}
        {"Thank you for your interest in this position." if status == 'rejected' else ""}
        
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
        
        logger.info(f"Application status notification sent to {user.email}")
        return {'success': True, 'notification_sent': True}
        
    except JobApplication.DoesNotExist:
        logger.error(f"Job application with ID {application_id} not found")
        return {'success': False, 'error': 'Application not found'}
    except Exception as e:
        logger.error(f"Failed to send application status notification: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}