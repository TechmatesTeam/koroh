"""
Celery tasks for Profiles app.
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from .models import Profile
from koroh_platform.utils.cv_analysis_service import CVAnalysisService
from koroh_platform.utils.portfolio_generation_service import PortfolioGenerationService

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def analyze_cv_async(self, profile_id, cv_file_path):
    """
    Background task to analyze uploaded CV using AWS Bedrock.
    
    Args:
        profile_id: ID of the profile to update
        cv_file_path: Path to the uploaded CV file
    """
    try:
        profile = Profile.objects.get(id=profile_id)
        
        # Read CV file content
        if default_storage.exists(cv_file_path):
            with default_storage.open(cv_file_path, 'r') as cv_file:
                cv_content = cv_file.read()
        else:
            raise FileNotFoundError(f"CV file not found: {cv_file_path}")
        
        # Initialize CV analysis service
        cv_service = CVAnalysisService()
        
        # Analyze CV content
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
            profile.skills = list(set(all_skills))  # Remove duplicates
        
        # Extract industry from work experience
        if analysis_result.work_experience:
            # Simple industry extraction - could be enhanced
            latest_exp = analysis_result.work_experience[0]
            if latest_exp.company:
                profile.industry = "Technology"  # Default - could be enhanced with AI
        
        # Estimate experience level
        experience_years = cv_service._estimate_experience_years(analysis_result)
        if experience_years <= 2:
            profile.experience_level = "Entry Level"
        elif experience_years <= 5:
            profile.experience_level = "Mid Level"
        elif experience_years <= 10:
            profile.experience_level = "Senior Level"
        else:
            profile.experience_level = "Executive Level"
        
        # Store analysis results in preferences for later use
        profile.preferences = profile.preferences or {}
        profile.preferences['cv_analysis'] = {
            'analysis_confidence': analysis_result.analysis_confidence,
            'extracted_sections': analysis_result.extracted_sections,
            'processing_notes': analysis_result.processing_notes,
            'analyzed_at': analysis_result.generated_at if hasattr(analysis_result, 'generated_at') else None
        }
        
        profile.save()
        
        logger.info(f"CV analysis completed for profile {profile_id}")
        
        # Trigger portfolio generation if requested
        if profile.preferences.get('auto_generate_portfolio', True):
            generate_portfolio_async.delay(profile_id)
        
        return {
            'success': True,
            'profile_updated': True,
            'skills_extracted': len(all_skills),
            'confidence_score': analysis_result.analysis_confidence
        }
        
    except Profile.DoesNotExist:
        logger.error(f"Profile with ID {profile_id} not found")
        return {'success': False, 'error': 'Profile not found'}
    except Exception as e:
        logger.error(f"CV analysis failed for profile {profile_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def generate_portfolio_async(self, profile_id, template="professional", style="formal"):
    """
    Background task to generate portfolio from CV analysis.
    
    Args:
        profile_id: ID of the profile to generate portfolio for
        template: Portfolio template to use
        style: Content style to use
    """
    try:
        profile = Profile.objects.get(id=profile_id)
        
        # Check if we have CV analysis data
        cv_analysis_data = profile.preferences.get('cv_analysis')
        if not cv_analysis_data:
            raise ValueError("No CV analysis data found. Please analyze CV first.")
        
        # For now, we'll create a simplified portfolio generation
        # In a full implementation, you'd reconstruct the CVAnalysisResult from stored data
        # or re-analyze the CV
        
        portfolio_service = PortfolioGenerationService()
        
        # Create a basic portfolio content structure
        # This is simplified - in production you'd want to store and retrieve full CV analysis
        portfolio_content = {
            'hero_section': {
                'headline': f"{profile.user.first_name} {profile.user.last_name}",
                'subheadline': profile.headline or "Professional",
                'value_proposition': profile.summary or "Experienced professional ready to make an impact",
                'call_to_action': "Let's connect"
            },
            'about_section': {
                'main_content': profile.summary or "Professional with expertise in various domains.",
                'key_highlights': profile.skills[:3] if profile.skills else [],
                'personal_touch': "Passionate about delivering excellent results."
            },
            'skills_section': {
                'top_skills': profile.skills[:10] if profile.skills else [],
                'skills_summary': f"Skilled in {', '.join(profile.skills[:5])}" if profile.skills else "Diverse skill set"
            },
            'contact_section': {
                'email': profile.user.email,
                'location': profile.location,
                'call_to_action': "Ready to discuss opportunities and collaborations."
            }
        }
        
        # Store portfolio content in profile preferences
        profile.preferences = profile.preferences or {}
        profile.preferences['portfolio'] = {
            'content': portfolio_content,
            'template': template,
            'style': style,
            'generated_at': timezone.now().isoformat(),
            'quality_score': 0.8  # Default score
        }
        
        # Generate portfolio URL (simplified)
        portfolio_url = f"/portfolio/{profile.user.username or profile.user.id}"
        profile.portfolio_url = portfolio_url
        
        profile.save()
        
        logger.info(f"Portfolio generated for profile {profile_id}")
        
        return {
            'success': True,
            'portfolio_generated': True,
            'portfolio_url': portfolio_url,
            'template_used': template,
            'style_used': style
        }
        
    except Profile.DoesNotExist:
        logger.error(f"Profile with ID {profile_id} not found")
        return {'success': False, 'error': 'Profile not found'}
    except Exception as e:
        logger.error(f"Portfolio generation failed for profile {profile_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}


@shared_task
def cleanup_orphaned_files():
    """
    Background task to clean up orphaned CV and profile picture files.
    
    This task should be scheduled to run weekly.
    """
    try:
        from django.core.files.storage import default_storage
        import os
        
        # Get all CV files referenced in profiles
        referenced_cv_files = set()
        for profile in Profile.objects.exclude(cv_file=''):
            if profile.cv_file:
                referenced_cv_files.add(profile.cv_file.name)
        
        # Get all profile picture files referenced in profiles
        referenced_profile_pics = set()
        for user in User.objects.exclude(profile_picture=''):
            if user.profile_picture:
                referenced_profile_pics.add(user.profile_picture.name)
        
        # Check CV directory for orphaned files
        cv_directory = 'cvs/'
        orphaned_cv_files = []
        
        if default_storage.exists(cv_directory):
            cv_dirs, cv_files = default_storage.listdir(cv_directory)
            for cv_dir in cv_dirs:
                cv_subdir = os.path.join(cv_directory, cv_dir)
                if default_storage.exists(cv_subdir):
                    _, files = default_storage.listdir(cv_subdir)
                    for file in files:
                        file_path = os.path.join(cv_subdir, file)
                        if file_path not in referenced_cv_files:
                            orphaned_cv_files.append(file_path)
        
        # Check profile pictures directory for orphaned files
        profile_directory = 'profiles/'
        orphaned_profile_files = []
        
        if default_storage.exists(profile_directory):
            _, profile_files = default_storage.listdir(profile_directory)
            for file in profile_files:
                file_path = os.path.join(profile_directory, file)
                if file_path not in referenced_profile_pics:
                    orphaned_profile_files.append(file_path)
        
        # Delete orphaned files
        deleted_cv_count = 0
        for file_path in orphaned_cv_files:
            try:
                default_storage.delete(file_path)
                deleted_cv_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete orphaned CV file {file_path}: {e}")
        
        deleted_profile_count = 0
        for file_path in orphaned_profile_files:
            try:
                default_storage.delete(file_path)
                deleted_profile_count += 1
            except Exception as e:
                logger.warning(f"Failed to delete orphaned profile file {file_path}: {e}")
        
        result = {
            'orphaned_cv_files_deleted': deleted_cv_count,
            'orphaned_profile_files_deleted': deleted_profile_count,
            'total_deleted': deleted_cv_count + deleted_profile_count
        }
        
        logger.info(f"File cleanup completed: {result}")
        return result
        
    except Exception as e:
        logger.error(f"File cleanup failed: {e}")
        return {'success': False, 'error': str(e)}


@shared_task(bind=True, max_retries=3)
def send_profile_completion_reminder(self, user_id):
    """
    Background task to send profile completion reminder email.
    
    Args:
        user_id: ID of the user to send reminder to
    """
    try:
        user = User.objects.get(id=user_id)
        profile = user.profile
        
        # Calculate profile completion percentage
        completion_fields = [
            profile.headline,
            profile.summary,
            profile.location,
            profile.industry,
            profile.skills,
            profile.cv_file,
            user.profile_picture
        ]
        
        completed_fields = sum(1 for field in completion_fields if field)
        completion_percentage = (completed_fields / len(completion_fields)) * 100
        
        # Only send reminder if profile is less than 70% complete
        if completion_percentage >= 70:
            return {'success': True, 'reminder_not_needed': True}
        
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = "Complete Your Koroh Profile"
        message = f"""
        Hi {user.first_name or user.email},
        
        Your Koroh profile is {completion_percentage:.0f}% complete. 
        
        Complete your profile to:
        - Get better job recommendations
        - Generate an AI-powered portfolio
        - Connect with relevant peer groups
        - Increase your visibility to recruiters
        
        Missing items:
        {chr(10).join([f"- {item}" for item, field in zip([
            "Professional headline",
            "Professional summary", 
            "Location",
            "Industry",
            "Skills",
            "CV upload",
            "Profile picture"
        ], completion_fields) if not field])}
        
        Complete your profile now to unlock the full potential of Koroh!
        
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
        
        logger.info(f"Profile completion reminder sent to {user.email}")
        return {
            'success': True, 
            'email_sent': True,
            'completion_percentage': completion_percentage
        }
        
    except User.DoesNotExist:
        logger.error(f"User with ID {user_id} not found")
        return {'success': False, 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send profile completion reminder to user {user_id}: {e}")
        
        # Retry the task
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {'success': False, 'error': str(e)}