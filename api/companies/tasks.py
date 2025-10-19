"""
Celery tasks for Companies app.
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from .models import Company, CompanyFollow
from .services import CompanyInsightService, CompanyNotificationService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def update_company_insights(self, company_id):
    """
    Background task to update company insights.
    
    Args:
        company_id: ID of the company to update insights for
    """
    try:
        company = Company.objects.get(id=company_id)
        result = CompanyInsightService.update_company_insights(company)
        
        logger.info(f"Updated insights for company {company.name}: {result}")
        return result
        
    except Company.DoesNotExist:
        logger.error(f"Company with ID {company_id} not found")
        return {'success': False, 'error': 'Company not found'}
    except Exception as e:
        logger.error(f"Error updating insights for company {company_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def notify_followers_new_job(self, company_id, job_id):
    """
    Background task to notify company followers of a new job posting.
    
    Args:
        company_id: ID of the company
        job_id: ID of the new job
    """
    try:
        company = Company.objects.get(id=company_id)
        
        from jobs.models import Job
        job = Job.objects.get(id=job_id)
        
        result = CompanyNotificationService.notify_followers_of_new_job(company, job)
        
        logger.info(f"Notified followers of new job at {company.name}: {result}")
        return result
        
    except (Company.DoesNotExist, Job.DoesNotExist) as e:
        logger.error(f"Company or Job not found: {e}")
        return {'success': False, 'error': str(e)}
    except Exception as e:
        logger.error(f"Error notifying followers: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def notify_followers_company_update(self, company_id, update_type, message):
    """
    Background task to notify company followers of general updates.
    
    Args:
        company_id: ID of the company
        update_type: Type of update
        message: Update message
    """
    try:
        company = Company.objects.get(id=company_id)
        
        result = CompanyNotificationService.notify_followers_of_company_update(
            company, update_type, message
        )
        
        logger.info(f"Notified followers of {company.name} update: {result}")
        return result
        
    except Company.DoesNotExist:
        logger.error(f"Company with ID {company_id} not found")
        return {'success': False, 'error': 'Company not found'}
    except Exception as e:
        logger.error(f"Error notifying followers: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task
def send_weekly_digests():
    """
    Background task to send weekly digests to all users.
    
    This task should be scheduled to run weekly.
    """
    users_with_follows = User.objects.filter(
        company_follows__isnull=False
    ).distinct()
    
    results = {
        'total_users': users_with_follows.count(),
        'digests_sent': 0,
        'failed_digests': 0
    }
    
    for user in users_with_follows:
        try:
            result = CompanyNotificationService.send_weekly_digest(user)
            if result.get('digest_sent'):
                results['digests_sent'] += 1
            else:
                results['failed_digests'] += 1
                
        except Exception as e:
            logger.error(f"Error sending weekly digest to {user.email}: {e}")
            results['failed_digests'] += 1
    
    logger.info(f"Weekly digest task completed: {results}")
    return results


@shared_task
def update_all_company_insights():
    """
    Background task to update insights for all active companies.
    
    This task should be scheduled to run daily.
    """
    active_companies = Company.objects.filter(is_active=True)
    
    results = {
        'total_companies': active_companies.count(),
        'successful_updates': 0,
        'failed_updates': 0
    }
    
    for company in active_companies:
        try:
            # Schedule individual update tasks
            update_company_insights.delay(company.id)
            results['successful_updates'] += 1
            
        except Exception as e:
            logger.error(f"Error scheduling insight update for company {company.id}: {e}")
            results['failed_updates'] += 1
    
    logger.info(f"Company insights update task completed: {results}")
    return results


@shared_task
def cleanup_expired_insights():
    """
    Background task to clean up expired company insights.
    
    This task should be scheduled to run daily.
    """
    from django.utils import timezone
    from .models import CompanyInsight
    
    expired_insights = CompanyInsight.objects.filter(
        expires_at__lt=timezone.now()
    )
    
    count = expired_insights.count()
    expired_insights.delete()
    
    logger.info(f"Cleaned up {count} expired company insights")
    return {'expired_insights_deleted': count}