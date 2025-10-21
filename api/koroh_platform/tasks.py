"""
Celery tasks for AI services and background processing.

This module contains tasks for:
- CV analysis and portfolio generation
- Job recommendation updates
- Email notifications
- System maintenance tasks
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from typing import Dict, Any, List, Optional

from .utils.ai_services import AIServiceFactory
from .utils.cv_analysis_service import CVAnalysisService
from .utils.portfolio_generation_service import PortfolioGenerationService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def analyze_cv_with_ai(self, user_id: int, cv_file_path: str) -> Dict[str, Any]:
    """
    Background task to analyze CV using AWS Bedrock AI services.
    
    Args:
        user_id: ID of the user whose CV to analyze
        cv_file_path: Path to the uploaded CV file
        
    Returns:
        Dictionary with analysis results
    """
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        # Initialize CV analysis service
        cv_service = CVAnalysisService()
        
        # Read and analyze CV
        from django.core.files.storage import default_storage
        
        if default_storage.exists(cv_file_path):
            with default_storage.open(cv_file_path, 'rb') as cv_file:
                cv_content = cv_file.read()
        else:
            raise FileNotFoundError(f"CV file not found: {cv_file_path}")
        
        analysis_result = cv_service.analyze_cv(cv_content)
        
        # Update profile with extracted information
        if analysis_result.professional_summary:
            profile.summary = analysis_result.professional_summary
        
        if analysis_result.personal_info.location:
            profile.location = analysis_result.personal_info.location
        
        # Update skills
        all_skills = (analysis_result.technical_skills + 
                     analysis_result.soft_skills + 
                     analysis_result.skills)
        if all_skills:
            profile.skills = list(set(all_skills))
        
        # Store analysis results
        profile.preferences = profile.preferences or {}
        profile.preferences['cv_analysis'] = {
            'analysis_confidence': analysis_result.analysis_confidence,
            'extracted_sections': analysis_result.extracted_sections,
            'processing_notes': analysis_result.processing_notes,
            'analyzed_at': timezone.now().isoformat()
        }
        
        profile.save()
        
        logger.info(f"CV analysis completed for user {user_id}")
        
        # Trigger portfolio generation
        generate_portfolio_with_ai.delay(user_id)
        
        return {
            'success': True,
            'user_id': user_id,
            'skills_extracted': len(all_skills),
            'confidence_score': analysis_result.analysis_confidence
        }
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"CV analysis failed for user {user_id}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_portfolio_with_ai(self, user_id: int, template: str = "professional") -> Dict[str, Any]:
    """
    Background task to generate portfolio using AI services.
    
    Args:
        user_id: ID of the user to generate portfolio for
        template: Portfolio template to use
        
    Returns:
        Dictionary with generation results
    """
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        # Check if we have CV analysis data
        cv_analysis_data = profile.preferences.get('cv_analysis')
        if not cv_analysis_data:
            raise ValueError("No CV analysis data found. Please analyze CV first.")
        
        # Initialize portfolio generation service
        portfolio_service = PortfolioGenerationService()
        
        # Generate portfolio content
        portfolio_result = portfolio_service.generate_portfolio(
            user_profile=profile,
            template=template
        )
        
        # Store portfolio content
        profile.preferences = profile.preferences or {}
        profile.preferences['portfolio'] = {
            'content': portfolio_result.content,
            'template': template,
            'generated_at': timezone.now().isoformat(),
            'quality_score': portfolio_result.quality_score
        }
        
        # Generate portfolio URL
        portfolio_url = f"/portfolio/{user.username or user.id}"
        profile.portfolio_url = portfolio_url
        
        profile.save()
        
        logger.info(f"Portfolio generated for user {user_id}")
        
        # Send notification email
        send_portfolio_ready_notification.delay(user_id, portfolio_url)
        
        return {
            'success': True,
            'user_id': user_id,
            'portfolio_url': portfolio_url,
            'quality_score': portfolio_result.quality_score
        }
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Portfolio generation failed for user {user_id}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def update_job_recommendations(self, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Background task to update job recommendations for users.
    
    Args:
        user_id: Optional specific user ID, if None updates for all active users
        
    Returns:
        Dictionary with update results
    """
    try:
        from jobs.models import Job
        from jobs.services import JobRecommendationService
        
        if user_id:
            users = User.objects.filter(id=user_id, is_active=True)
        else:
            # Update for users who have been active in the last 30 days
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            users = User.objects.filter(
                is_active=True,
                last_login__gte=cutoff_date
            ).select_related('profile')
        
        recommendation_service = JobRecommendationService()
        
        results = {
            'total_users': users.count(),
            'successful_updates': 0,
            'failed_updates': 0,
            'recommendations_generated': 0
        }
        
        for user in users:
            try:
                if not hasattr(user, 'profile') or not user.profile:
                    continue
                
                # Get user's job preferences and profile
                user_profile = {
                    'skills': user.profile.skills or [],
                    'experience_level': user.profile.experience_level,
                    'industry': user.profile.industry,
                    'location': user.profile.location,
                    'preferences': user.profile.preferences or {}
                }
                
                # Get available jobs
                available_jobs = Job.objects.filter(
                    is_active=True,
                    posted_date__gte=timezone.now() - timezone.timedelta(days=7)
                ).values(
                    'id', 'title', 'description', 'requirements',
                    'location', 'job_type', 'company__name', 'company__industry'
                )[:50]  # Limit to recent jobs
                
                # Generate recommendations using AI
                recommended_jobs = recommendation_service.get_recommendations_for_user(
                    user, limit=10
                )
                
                if recommended_jobs:
                    # Convert job objects to serializable data
                    recommendations = []
                    for job in recommended_jobs:
                        recommendations.append({
                            'job_id': job.id,
                            'title': job.title,
                            'company_name': job.company.name,
                            'location': job.location,
                            'job_type': job.job_type,
                            'match_score': getattr(job, 'ai_match_score', 0.5) * 100,
                            'posted_date': job.posted_date.isoformat(),
                            'url': f'/jobs/{job.id}/'
                        })
                    
                    # Store recommendations in user preferences
                    user.profile.preferences = user.profile.preferences or {}
                    user.profile.preferences['job_recommendations'] = {
                        'recommendations': recommendations,
                        'updated_at': timezone.now().isoformat(),
                        'total_count': len(recommendations)
                    }
                    user.profile.save()
                    
                    results['recommendations_generated'] += len(recommendations)
                
                results['successful_updates'] += 1
                
            except Exception as e:
                logger.error(f"Failed to update recommendations for user {user.id}: {e}")
                results['failed_updates'] += 1
        
        logger.info(f"Job recommendations update completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Job recommendations update failed: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_portfolio_ready_notification(self, user_id: int, portfolio_url: str) -> Dict[str, Any]:
    """
    Background task to send portfolio ready notification email.
    
    Args:
        user_id: ID of the user
        portfolio_url: URL of the generated portfolio
        
    Returns:
        Dictionary with email sending results
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = "Your AI-Generated Portfolio is Ready!"
        message = f"""
        Hi {user.first_name or user.email},
        
        Great news! Your AI-powered portfolio has been generated and is ready to view.
        
        Portfolio URL: {portfolio_url}
        
        Your portfolio includes:
        - Professional summary based on your CV
        - Skills and experience highlights
        - Customizable design and layout
        - Shareable link for networking
        
        You can further customize your portfolio and share it with potential employers
        and networking connections.
        
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
        
        logger.info(f"Portfolio ready notification sent to {user.email}")
        return {'success': True, 'email_sent': True}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send portfolio notification to user {user_id}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_job_recommendations_email(self, user_id: int) -> Dict[str, Any]:
    """
    Background task to send job recommendations email to user.
    
    Args:
        user_id: ID of the user to send recommendations to
        
    Returns:
        Dictionary with email sending results
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Get user's job recommendations
        recommendations = user.profile.preferences.get('job_recommendations', {}).get('recommendations', [])
        
        if not recommendations:
            return {'success': True, 'no_recommendations': True}
        
        # Get top 5 recommendations
        top_recommendations = recommendations[:5]
        
        subject = "New Job Recommendations for You"
        
        recommendations_text = "\n".join([
            f"- {rec.get('title', 'Job Title')} at {rec.get('company_name', 'Company')}\n"
            f"  Match Score: {rec.get('match_score', 0)}%\n"
            f"  Location: {rec.get('location', 'Not specified')}\n"
            f"  Why it's a match: {rec.get('match_reasons', ['Good fit'])[:2]}\n"
            for rec in top_recommendations
        ])
        
        message = f"""
        Hi {user.first_name or user.email},
        
        We've found some exciting job opportunities that match your profile:
        
        {recommendations_text}
        
        These recommendations are based on your skills, experience, and preferences.
        Log in to Koroh to view full details and apply to these positions.
        
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
        
        logger.info(f"Job recommendations email sent to {user.email}")
        return {'success': True, 'email_sent': True, 'recommendations_count': len(top_recommendations)}
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send job recommendations email to user {user_id}: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=2, default_retry_delay=300)
def update_peer_group_recommendations(self, user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    Background task to update peer group recommendations for users.
    
    Args:
        user_id: Optional specific user ID, if None updates for all active users
        
    Returns:
        Dictionary with update results
    """
    try:
        from peer_groups.services import PeerGroupRecommendationService
        
        if user_id:
            users = User.objects.filter(id=user_id, is_active=True)
        else:
            # Update for users who have been active in the last 30 days
            cutoff_date = timezone.now() - timezone.timedelta(days=30)
            users = User.objects.filter(
                is_active=True,
                last_login__gte=cutoff_date
            ).select_related('profile')
        
        recommendation_service = PeerGroupRecommendationService()
        
        results = {
            'total_users': users.count(),
            'successful_updates': 0,
            'failed_updates': 0,
            'recommendations_generated': 0
        }
        
        for user in users:
            try:
                if not hasattr(user, 'profile') or not user.profile:
                    continue
                
                # Generate peer group recommendations using AI
                recommendations = recommendation_service.get_recommendations_for_user(
                    user, limit=8
                )
                
                if recommendations:
                    # Store recommendations in user preferences
                    user.profile.preferences = user.profile.preferences or {}
                    user.profile.preferences['peer_group_recommendations'] = {
                        'recommendations': recommendations,
                        'updated_at': timezone.now().isoformat(),
                        'total_count': len(recommendations)
                    }
                    user.profile.save()
                    
                    results['recommendations_generated'] += len(recommendations)
                
                results['successful_updates'] += 1
                
            except Exception as e:
                logger.error(f"Failed to update peer group recommendations for user {user.id}: {e}")
                results['failed_updates'] += 1
        
        logger.info(f"Peer group recommendations update completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Peer group recommendations update failed: {e}")
        
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=300 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task
def send_weekly_job_digest():
    """
    Background task to send weekly job digest to all active users.
    
    This task should be scheduled to run weekly.
    """
    try:
        # Get users who want to receive job digests
        active_users = User.objects.filter(
            is_active=True,
            profile__preferences__job_notifications=True
        ).select_related('profile')
        
        results = {
            'total_users': active_users.count(),
            'emails_sent': 0,
            'failed_emails': 0
        }
        
        for user in active_users:
            try:
                # Schedule individual email task
                send_job_recommendations_email.delay(user.id)
                results['emails_sent'] += 1
                
            except Exception as e:
                logger.error(f"Failed to schedule job digest for user {user.id}: {e}")
                results['failed_emails'] += 1
        
        logger.info(f"Weekly job digest task completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"Weekly job digest task failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_ai_processing_data():
    """
    Background task to clean up old AI processing data and temporary files.
    
    This task should be scheduled to run daily.
    """
    try:
        from django.core.files.storage import default_storage
        import os
        from datetime import timedelta
        
        results = {
            'temp_files_deleted': 0,
            'old_analysis_data_cleaned': 0,
            'cache_entries_cleared': 0
        }
        
        # Clean up temporary CV files older than 24 hours
        temp_cv_dir = 'temp/cvs/'
        if default_storage.exists(temp_cv_dir):
            cutoff_time = timezone.now() - timedelta(hours=24)
            
            try:
                _, files = default_storage.listdir(temp_cv_dir)
                for file in files:
                    file_path = os.path.join(temp_cv_dir, file)
                    try:
                        # Check file modification time
                        file_stats = default_storage.stat(file_path)
                        if file_stats.st_mtime < cutoff_time.timestamp():
                            default_storage.delete(file_path)
                            results['temp_files_deleted'] += 1
                    except Exception as e:
                        logger.warning(f"Failed to process temp file {file_path}: {e}")
            except Exception as e:
                logger.warning(f"Failed to list temp directory: {e}")
        
        # Clean up old analysis data from user preferences
        old_analysis_cutoff = timezone.now() - timedelta(days=30)
        
        from profiles.models import Profile
        profiles_with_old_data = Profile.objects.filter(
            preferences__cv_analysis__analyzed_at__lt=old_analysis_cutoff.isoformat()
        )
        
        for profile in profiles_with_old_data:
            try:
                if 'cv_analysis' in profile.preferences:
                    # Keep only essential data, remove detailed processing notes
                    analysis_data = profile.preferences['cv_analysis']
                    profile.preferences['cv_analysis'] = {
                        'analysis_confidence': analysis_data.get('analysis_confidence'),
                        'analyzed_at': analysis_data.get('analyzed_at')
                    }
                    profile.save()
                    results['old_analysis_data_cleaned'] += 1
            except Exception as e:
                logger.warning(f"Failed to clean analysis data for profile {profile.id}: {e}")
        
        logger.info(f"AI processing data cleanup completed: {results}")
        return results
        
    except Exception as e:
        logger.error(f"AI processing data cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task
def monitor_ai_service_health():
    """
    Background task to monitor AI service health and performance.
    
    This task should be scheduled to run every 15 minutes.
    """
    try:
        from .utils.aws_bedrock import bedrock_client
        
        results = {
            'bedrock_client_status': 'unknown',
            'test_invocation_success': False,
            'response_time_ms': 0,
            'error_details': None
        }
        
        # Check Bedrock client initialization
        if bedrock_client and bedrock_client.client:
            results['bedrock_client_status'] = 'initialized'
            
            # Test a simple model invocation
            start_time = timezone.now()
            try:
                test_response = bedrock_client.invoke_model(
                    model_id="anthropic.claude-3-haiku-20240307-v1:0",
                    prompt="Hello, this is a health check. Please respond with 'OK'.",
                    max_tokens=10,
                    temperature=0.1
                )
                
                end_time = timezone.now()
                response_time = (end_time - start_time).total_seconds() * 1000
                results['response_time_ms'] = response_time
                
                if test_response:
                    results['test_invocation_success'] = True
                    results['bedrock_client_status'] = 'healthy'
                else:
                    results['bedrock_client_status'] = 'error'
                    results['error_details'] = 'Empty response from Bedrock'
                    
            except Exception as e:
                results['bedrock_client_status'] = 'error'
                results['error_details'] = str(e)
                logger.error(f"Bedrock health check failed: {e}")
        else:
            results['bedrock_client_status'] = 'not_initialized'
            results['error_details'] = 'Bedrock client not properly initialized'
        
        # Log results for monitoring
        if results['bedrock_client_status'] == 'healthy':
            logger.info(f"AI service health check passed: {results}")
        else:
            logger.warning(f"AI service health check failed: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"AI service health monitoring failed: {e}")
        return {'success': False, 'error': str(e)}