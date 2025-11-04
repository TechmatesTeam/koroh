"""
Real-time data update service for Koroh Platform.

This service handles real-time data updates and notifications across
the platform, integrating with WebSocket consumers and background tasks.
"""

import logging
from typing import Dict, List, Any, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from celery import shared_task
from koroh_platform.realtime import (
    send_dashboard_update, 
    send_notification, 
    send_peer_group_update
)

User = get_user_model()
logger = logging.getLogger('koroh_platform')


class RealtimeDataService:
    """Service for managing real-time data updates across the platform."""
    
    @staticmethod
    def notify_job_recommendation_update(user_id: int, jobs: List[Dict[str, Any]]) -> None:
        """Notify user of new job recommendations."""
        try:
            send_dashboard_update(user_id, 'job_recommendation_update', {
                'recommendations': jobs,
                'count': len(jobs),
                'timestamp': timezone.now().isoformat()
            })
            
            # Also send a notification
            send_notification(user_id, {
                'type': 'info',
                'title': 'New Job Recommendations',
                'message': f'{len(jobs)} new job recommendations are available!',
                'action_url': '/jobs',
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send job recommendation update: {e}")
    
    @staticmethod
    def notify_company_update(user_id: int, company_data: Dict[str, Any], update_type: str) -> None:
        """Notify user of company updates."""
        try:
            send_dashboard_update(user_id, 'company_update', {
                'type': update_type,
                'company': company_data,
                'timestamp': timezone.now().isoformat()
            })
            
            # Send notification based on update type
            if update_type == 'new_job':
                message = f"New job at {company_data.get('name', 'a company you follow')}"
            elif update_type == 'followed':
                message = f"You are now following {company_data.get('name')}"
            elif update_type == 'unfollowed':
                message = f"You unfollowed {company_data.get('name')}"
            else:
                message = f"Update from {company_data.get('name', 'a company you follow')}"
            
            send_notification(user_id, {
                'type': 'info',
                'title': 'Company Update',
                'message': message,
                'action_url': f"/companies/{company_data.get('id', '')}",
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send company update: {e}")
    
    @staticmethod
    def notify_peer_group_activity(group_slug: str, activity_type: str, activity_data: Dict[str, Any]) -> None:
        """Notify peer group members of new activity."""
        try:
            send_peer_group_update(group_slug, activity_type, activity_data)
            
            # Also notify individual users who are members
            from peer_groups.models import GroupMembership
            members = GroupMembership.objects.filter(
                group__slug=group_slug,
                status='active',
                notifications_enabled=True
            ).select_related('user')
            
            for membership in members:
                # Don't notify the user who created the activity
                if (activity_data.get('author', {}).get('id') != membership.user.id):
                    RealtimeDataService._send_peer_group_notification(
                        membership.user.id, group_slug, activity_type, activity_data
                    )
                    
        except Exception as e:
            logger.error(f"Failed to send peer group activity update: {e}")
    
    @staticmethod
    def _send_peer_group_notification(user_id: int, group_slug: str, activity_type: str, activity_data: Dict[str, Any]) -> None:
        """Send individual peer group notification to user."""
        try:
            group_name = activity_data.get('group_name', 'a peer group')
            
            if activity_type == 'new_post':
                message = f"New post in {group_name}: {activity_data.get('title', 'Untitled')}"
            elif activity_type == 'new_comment':
                message = f"New comment in {group_name} on: {activity_data.get('post_title', 'a post')}"
            elif activity_type == 'member_joined':
                message = f"{activity_data.get('name', 'Someone')} joined {group_name}"
            else:
                message = f"New activity in {group_name}"
            
            send_notification(user_id, {
                'type': 'info',
                'title': 'Peer Group Activity',
                'message': message,
                'action_url': f"/peer-groups/{group_slug}",
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send peer group notification: {e}")
    
    @staticmethod
    def notify_profile_update(user_id: int, update_type: str, update_data: Dict[str, Any]) -> None:
        """Notify user of profile-related updates."""
        try:
            send_dashboard_update(user_id, 'profile_update', {
                'type': update_type,
                'data': update_data,
                'timestamp': timezone.now().isoformat()
            })
            
            if update_type == 'cv_analyzed':
                message = "Your CV has been analyzed and new insights are available"
            elif update_type == 'portfolio_generated':
                message = "Your portfolio has been generated successfully"
            elif update_type == 'skills_updated':
                message = "Your skills have been updated based on your CV"
            else:
                message = "Your profile has been updated"
            
            send_notification(user_id, {
                'type': 'success',
                'title': 'Profile Update',
                'message': message,
                'action_url': '/profile',
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to send profile update: {e}")
    
    @staticmethod
    def refresh_user_dashboard(user_id: int, reason: str = 'data_update') -> None:
        """Trigger a dashboard refresh for a user."""
        try:
            send_dashboard_update(user_id, 'refresh', {
                'reason': reason,
                'timestamp': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Failed to refresh user dashboard: {e}")


# Signal handlers for automatic real-time updates
@receiver(post_save, sender='jobs.Job')
def handle_job_created(sender, instance, created, **kwargs):
    """Handle new job creation for real-time updates."""
    if created and instance.is_published:
        # Notify followers of the company
        schedule_company_job_notifications.delay(instance.company.id, instance.id)


@receiver(post_save, sender='peer_groups.GroupPost')
def handle_group_post_created(sender, instance, created, **kwargs):
    """Handle new group post creation for real-time updates."""
    if created:
        # This is already handled in the model's save method
        # but we can add additional logic here if needed
        pass


@receiver(post_save, sender='peer_groups.GroupComment')
def handle_group_comment_created(sender, instance, created, **kwargs):
    """Handle new group comment creation for real-time updates."""
    if created:
        # This is already handled in the model's save method
        # but we can add additional logic here if needed
        pass


@receiver(post_save, sender='companies.CompanyFollow')
def handle_company_follow_created(sender, instance, created, **kwargs):
    """Handle new company follow for real-time updates."""
    if created:
        # This is already handled in the service
        pass


# Celery tasks for background real-time processing
@shared_task
def schedule_company_job_notifications(company_id: int, job_id: int):
    """Schedule notifications for company followers about new jobs."""
    try:
        from companies.models import Company
        from jobs.models import Job
        from companies.services import CompanyNotificationService
        
        company = Company.objects.get(id=company_id)
        job = Job.objects.get(id=job_id)
        
        # Send notifications to followers
        result = CompanyNotificationService.notify_followers_of_new_job(company, job)
        logger.info(f"Sent {result['notifications_sent']} job notifications for company {company.name}")
        
    except Exception as e:
        logger.error(f"Failed to schedule company job notifications: {e}")


@shared_task
def update_user_recommendations(user_id: int):
    """Update job recommendations for a user and send real-time notifications."""
    try:
        from jobs.services import JobRecommendationService
        
        user = User.objects.get(id=user_id)
        service = JobRecommendationService()
        
        # Get new recommendations
        recommendations = service.get_recommendations_for_user(user, limit=5)
        
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
                    'match_score': getattr(job, 'ai_match_score', 0) * 100,
                    'posted_date': job.posted_date.isoformat()
                })
            
            # Send real-time notification
            RealtimeDataService.notify_job_recommendation_update(user_id, job_data)
            
        logger.info(f"Updated recommendations for user {user_id}: {len(recommendations)} jobs")
        
    except Exception as e:
        logger.error(f"Failed to update user recommendations: {e}")


@shared_task
def refresh_dashboard_data(user_id: int):
    """Refresh dashboard data for a user."""
    try:
        RealtimeDataService.refresh_user_dashboard(user_id, 'scheduled_refresh')
        logger.info(f"Refreshed dashboard data for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to refresh dashboard data: {e}")


@shared_task
def process_cv_analysis_complete(user_id: int, analysis_data: Dict[str, Any]):
    """Process CV analysis completion and send real-time updates."""
    try:
        RealtimeDataService.notify_profile_update(user_id, 'cv_analyzed', analysis_data)
        
        # Schedule recommendation updates
        update_user_recommendations.delay(user_id)
        
        logger.info(f"Processed CV analysis completion for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to process CV analysis completion: {e}")


@shared_task
def process_portfolio_generation_complete(user_id: int, portfolio_data: Dict[str, Any]):
    """Process portfolio generation completion and send real-time updates."""
    try:
        RealtimeDataService.notify_profile_update(user_id, 'portfolio_generated', portfolio_data)
        logger.info(f"Processed portfolio generation completion for user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to process portfolio generation completion: {e}")


# Utility functions for triggering real-time updates
def trigger_job_recommendations_update(user_id: int):
    """Trigger job recommendations update for a user."""
    update_user_recommendations.delay(user_id)


def trigger_dashboard_refresh(user_id: int):
    """Trigger dashboard refresh for a user."""
    refresh_dashboard_data.delay(user_id)


def trigger_cv_analysis_notification(user_id: int, analysis_data: Dict[str, Any]):
    """Trigger CV analysis completion notification."""
    process_cv_analysis_complete.delay(user_id, analysis_data)


def trigger_portfolio_generation_notification(user_id: int, portfolio_data: Dict[str, Any]):
    """Trigger portfolio generation completion notification."""
    process_portfolio_generation_complete.delay(user_id, portfolio_data)