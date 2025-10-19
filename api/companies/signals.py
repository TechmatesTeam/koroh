"""
Signals for Companies app.
"""

import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Company, CompanyFollow
from .tasks import update_company_insights, notify_followers_new_job

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Company)
def company_post_save(sender, instance, created, **kwargs):
    """Handle company post-save signal."""
    if created:
        # Generate initial insights for new companies
        try:
            update_company_insights.delay(instance.id)
            logger.info(f"Scheduled insight generation for new company: {instance.name}")
        except Exception as e:
            logger.error(f"Error scheduling insight generation for company {instance.id}: {e}")


@receiver(post_save, sender='jobs.Job')
def job_post_save(sender, instance, created, **kwargs):
    """Handle job post-save signal to notify company followers."""
    if created and instance.status == 'published' and instance.is_active:
        try:
            # Notify company followers of new job
            notify_followers_new_job.delay(instance.company.id, instance.id)
            logger.info(f"Scheduled follower notification for new job: {instance.title}")
        except Exception as e:
            logger.error(f"Error scheduling follower notification for job {instance.id}: {e}")


@receiver(post_save, sender=CompanyFollow)
def company_follow_post_save(sender, instance, created, **kwargs):
    """Handle company follow post-save signal."""
    if created:
        # Update company insights when follower count changes significantly
        try:
            follower_count = instance.company.get_follower_count()
            
            # Update insights if this is a milestone (every 10 followers)
            if follower_count % 10 == 0:
                update_company_insights.delay(instance.company.id)
                logger.info(f"Scheduled insight update for company {instance.company.name} (milestone: {follower_count} followers)")
                
        except Exception as e:
            logger.error(f"Error scheduling insight update for company {instance.company.id}: {e}")


@receiver(post_delete, sender=CompanyFollow)
def company_follow_post_delete(sender, instance, **kwargs):
    """Handle company follow post-delete signal."""
    try:
        # Update company follower count cache
        instance.company.update_follower_count()
        logger.info(f"Updated follower count for company {instance.company.name}")
    except Exception as e:
        logger.error(f"Error updating follower count for company {instance.company.id}: {e}")