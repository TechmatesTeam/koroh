"""
Celery tasks for Koroh Platform.

This module contains background tasks for real-time data updates,
notifications, and periodic maintenance operations.
"""

import logging
from typing import Dict, List, Any
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from koroh_platform.services.realtime_data_service import RealtimeDataService

User = get_user_model()
logger = logging.getLogger('koroh_platform')


@shared_task
def update_all_user_recommendations():
    """Update job recommendations for all active users."""
    try:
        # Get active users (logged in within last 30 days)
        cutoff_date = timezone.now() - timedelta(days=30)
        active_users = User.objects.filter(
            last_login__gte=cutoff_date,
            is_active=True
        ).values_list('id', flat=True)
        
        updated_count = 0
        for user_id in active_users:
            try:
                update_user_job_recommendations.delay(user_id)
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to schedule recommendation update for user {user_id}: {e}")
        
        logger.info(f"Scheduled recommendation updates for {updated_count} users")
        return {'updated_count': updated_count}
        
    except Exception as e:
        logger.error(f"Failed to update user recommendations: {e}")
        return {'error': str(e)}


@shared_task
def update_user_job_recommendations(user_id: int):
    """Update job recommendations for a specific user."""
    try:
        from jobs.services import JobRecommendationService
        
        user = User.objects.get(id=user_id)
        service = JobRecommendationService()
        
        # Get fresh recommendations
        recommendations = service.get_recommendations_for_user(
            user, 
            limit=10,
            include_applied=False,
            min_match_score=0.4
        )
        
        if recommendations:
            # Convert to serializable format
            job_data = []
            for job in recommendations:
                job_data.append({
                    'id': str(job.id),
                    'title': job.title,
                    'company': {
                        'name': job.company.name,
                        'logo': job.company.logo.url if job.company.logo else None
                    },
                    'location': job.location,
                    'job_type': job.job_type,
                    'match_score': getattr(job, 'ai_match_score', 0) * 100,
                    'posted_date': job.posted_date.isoformat(),
                    'salary_range': job.salary_range_display
                })
            
            # Send real-time notification
            RealtimeDataService.notify_job_recommendation_update(user_id, job_data)
            
            logger.info(f"Updated recommendations for user {user_id}: {len(recommendations)} jobs")
            return {'user_id': user_id, 'recommendations_count': len(recommendations)}
        else:
            logger.info(f"No new recommendations for user {user_id}")
            return {'user_id': user_id, 'recommendations_count': 0}
            
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found")
        return {'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to update recommendations for user {user_id}: {e}")
        return {'error': str(e)}


@shared_task
def notify_company_followers_new_job(company_id: int, job_id: int):
    """Notify company followers about a new job posting."""
    try:
        from companies.models import Company
        from jobs.models import Job
        from companies.services import CompanyNotificationService
        
        company = Company.objects.get(id=company_id)
        job = Job.objects.get(id=job_id)
        
        # Send email notifications
        result = CompanyNotificationService.notify_followers_of_new_job(company, job)
        
        logger.info(f"Notified {result['notifications_sent']} followers of {company.name} about job: {job.title}")
        return result
        
    except (Company.DoesNotExist, Job.DoesNotExist) as e:
        logger.error(f"Company or job not found: {e}")
        return {'error': 'Company or job not found'}
    except Exception as e:
        logger.error(f"Failed to notify company followers: {e}")
        return {'error': str(e)}


@shared_task
def refresh_user_dashboard_data(user_id: int):
    """Refresh dashboard data for a specific user."""
    try:
        RealtimeDataService.refresh_user_dashboard(user_id, 'scheduled_refresh')
        logger.info(f"Refreshed dashboard data for user {user_id}")
        return {'user_id': user_id, 'status': 'refreshed'}
        
    except Exception as e:
        logger.error(f"Failed to refresh dashboard for user {user_id}: {e}")
        return {'error': str(e)}


@shared_task
def process_cv_analysis_completion(user_id: int, analysis_data: Dict[str, Any]):
    """Process CV analysis completion and trigger updates."""
    try:
        # Notify user of completion
        RealtimeDataService.notify_profile_update(user_id, 'cv_analyzed', analysis_data)
        
        # Update job recommendations based on new CV data
        update_user_job_recommendations.delay(user_id)
        
        # Refresh dashboard
        refresh_user_dashboard_data.delay(user_id)
        
        logger.info(f"Processed CV analysis completion for user {user_id}")
        return {'user_id': user_id, 'status': 'processed'}
        
    except Exception as e:
        logger.error(f"Failed to process CV analysis completion: {e}")
        return {'error': str(e)}


@shared_task
def process_portfolio_generation_completion(user_id: int, portfolio_data: Dict[str, Any]):
    """Process portfolio generation completion and notify user."""
    try:
        RealtimeDataService.notify_profile_update(user_id, 'portfolio_generated', portfolio_data)
        logger.info(f"Processed portfolio generation completion for user {user_id}")
        return {'user_id': user_id, 'status': 'processed'}
        
    except Exception as e:
        logger.error(f"Failed to process portfolio generation completion: {e}")
        return {'error': str(e)}


@shared_task
def update_peer_group_activity_scores():
    """Update activity scores for all peer groups."""
    try:
        from peer_groups.models import PeerGroup
        
        groups = PeerGroup.objects.filter(is_active=True)
        updated_count = 0
        
        for group in groups:
            try:
                group.update_activity_score()
                updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update activity score for group {group.id}: {e}")
        
        logger.info(f"Updated activity scores for {updated_count} peer groups")
        return {'updated_count': updated_count}
        
    except Exception as e:
        logger.error(f"Failed to update peer group activity scores: {e}")
        return {'error': str(e)}


@shared_task
def send_weekly_digest_emails():
    """Send weekly digest emails to all users."""
    try:
        from companies.services import CompanyNotificationService
        
        # Get users who have followed companies and want notifications
        from companies.models import CompanyFollow
        
        user_ids = CompanyFollow.objects.filter(
            notifications_enabled=True
        ).values_list('user_id', flat=True).distinct()
        
        sent_count = 0
        failed_count = 0
        
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                result = CompanyNotificationService.send_weekly_digest(user)
                
                if result.get('digest_sent'):
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to send weekly digest to user {user_id}: {e}")
                failed_count += 1
        
        logger.info(f"Sent weekly digests: {sent_count} successful, {failed_count} failed")
        return {'sent_count': sent_count, 'failed_count': failed_count}
        
    except Exception as e:
        logger.error(f"Failed to send weekly digest emails: {e}")
        return {'error': str(e)}


@shared_task
def cleanup_expired_data():
    """Clean up expired data and notifications."""
    try:
        from companies.models import CompanyInsight
        
        # Remove expired company insights
        expired_insights = CompanyInsight.objects.filter(
            expires_at__lt=timezone.now()
        )
        expired_count = expired_insights.count()
        expired_insights.delete()
        
        logger.info(f"Cleaned up {expired_count} expired company insights")
        return {'expired_insights_removed': expired_count}
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired data: {e}")
        return {'error': str(e)}


@shared_task
def update_company_insights():
    """Update insights for all active companies."""
    try:
        from companies.models import Company
        from companies.services import CompanyInsightService
        
        companies = Company.objects.filter(is_active=True)
        updated_count = 0
        
        for company in companies:
            try:
                result = CompanyInsightService.update_company_insights(company)
                if result.get('success'):
                    updated_count += 1
            except Exception as e:
                logger.error(f"Failed to update insights for company {company.id}: {e}")
        
        logger.info(f"Updated insights for {updated_count} companies")
        return {'updated_count': updated_count}
        
    except Exception as e:
        logger.error(f"Failed to update company insights: {e}")
        return {'error': str(e)}


# Periodic task scheduling (to be configured in Celery beat)
@shared_task
def run_periodic_updates():
    """Run all periodic update tasks."""
    try:
        # Update recommendations every 2 hours
        update_all_user_recommendations.delay()
        
        # Update peer group activity scores every hour
        update_peer_group_activity_scores.delay()
        
        # Update company insights daily
        update_company_insights.delay()
        
        # Cleanup expired data daily
        cleanup_expired_data.delay()
        
        logger.info("Scheduled all periodic update tasks")
        return {'status': 'scheduled'}
        
    except Exception as e:
        logger.error(f"Failed to run periodic updates: {e}")
        return {'error': str(e)}