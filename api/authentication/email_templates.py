"""
Professional email templates for Koroh platform authentication.

This module provides HTML email templates for user authentication flows
including registration confirmation, password reset, and account verification.
"""

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

# Email template configurations
EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Welcome to Koroh - Verify Your Account',
        'template': 'emails/welcome.html',
    },
    'password_reset': {
        'subject': 'Reset Your Koroh Password',
        'template': 'emails/password_reset.html',
    },
    'password_reset_success': {
        'subject': 'Your Koroh Password Has Been Reset',
        'template': 'emails/password_reset_success.html',
    },
    'account_verified': {
        'subject': 'Your Koroh Account is Now Verified',
        'template': 'emails/account_verified.html',
    },
    'job_recommendation': {
        'subject': 'New Job Recommendations for You',
        'template': 'emails/job_recommendation.html',
    },
    'company_update': {
        'subject': 'Update from {company_name}',
        'template': 'emails/company_update.html',
    },
    'peer_group_invitation': {
        'subject': 'You\'re Invited to Join {group_name}',
        'template': 'emails/peer_group_invitation.html',
    },
    'peer_group_activity': {
        'subject': 'New Activity in {group_name}',
        'template': 'emails/peer_group_activity.html',
    },
    'portfolio_generated': {
        'subject': 'Your AI-Generated Portfolio is Ready!',
        'template': 'emails/portfolio_generated.html',
    },
    'profile_completion_reminder': {
        'subject': 'Complete Your Profile to Unlock AI Features',
        'template': 'emails/profile_completion_reminder.html',
    },
    'weekly_digest': {
        'subject': 'Your Weekly Koroh Digest',
        'template': 'emails/weekly_digest.html',
    },
}

def send_professional_email(template_name, recipient_email, context=None, from_email=None):
    """
    Send a professional HTML email using predefined templates.
    
    Args:
        template_name (str): Name of the email template to use
        recipient_email (str): Recipient's email address
        context (dict): Template context variables
        from_email (str): Sender email address (optional)
    
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    if template_name not in EMAIL_TEMPLATES:
        logger.error(f"Unknown email template: {template_name}")
        return False
    
    template_config = EMAIL_TEMPLATES[template_name]
    context = context or {}
    
    # Add common context variables
    context.update({
        'site_name': 'Koroh',
        'site_url': getattr(settings, 'FRONTEND_URL', 'http://localhost:3000'),
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'support@koroh.com'),
        'company_name': 'Koroh Platform',
        'current_year': 2024,
    })
    
    try:
        # Render HTML content
        html_content = render_to_string(template_config['template'], context)
        
        # Create plain text version
        text_content = strip_tags(html_content)
        
        # Create email message
        email = EmailMultiAlternatives(
            subject=template_config['subject'],
            body=text_content,
            from_email=from_email or settings.DEFAULT_FROM_EMAIL,
            to=[recipient_email],
        )
        
        # Attach HTML version
        email.attach_alternative(html_content, "text/html")
        
        # Send email
        email.send()
        
        logger.info(f"Email sent successfully: {template_name} to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email {template_name} to {recipient_email}: {str(e)}")
        return False

def send_welcome_email(user, verification_token):
    """Send welcome email with account verification link."""
    verification_url = f"{settings.FRONTEND_URL}/auth/verify?token={verification_token}"
    
    context = {
        'user': user,
        'verification_url': verification_url,
        'verification_token': verification_token,
    }
    
    return send_professional_email('welcome', user.email, context)

def send_password_reset_email(user, reset_token):
    """Send password reset email with reset link."""
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={reset_token}"
    
    context = {
        'user': user,
        'reset_url': reset_url,
        'reset_token': reset_token,
        'expiry_hours': 24,  # Token expires in 24 hours
    }
    
    return send_professional_email('password_reset', user.email, context)

def send_password_reset_success_email(user):
    """Send confirmation email after successful password reset."""
    context = {
        'user': user,
        'login_url': f"{settings.FRONTEND_URL}/auth/login",
    }
    
    return send_professional_email('password_reset_success', user.email, context)

def send_account_verified_email(user):
    """Send confirmation email after account verification."""
    context = {
        'user': user,
        'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
    }
    
    return send_professional_email('account_verified', user.email, context)

def send_job_recommendation_email(user, recommended_jobs, match_percentage=85):
    """Send job recommendation email with personalized job matches."""
    context = {
        'user': user,
        'recommended_jobs': recommended_jobs,
        'job_count': len(recommended_jobs),
        'top_skills': user.profile.skills[:5] if hasattr(user, 'profile') and user.profile.skills else [],
        'match_percentage': match_percentage,
        'jobs_url': f"{settings.FRONTEND_URL}/jobs",
        'preferences_url': f"{settings.FRONTEND_URL}/profile/preferences",
    }
    
    return send_professional_email('job_recommendation', user.email, context)

def send_company_update_email(user, company, update_type, update_message, job=None):
    """Send company update notification email."""
    # Dynamic subject with company name
    template_config = EMAIL_TEMPLATES['company_update'].copy()
    template_config['subject'] = template_config['subject'].format(company_name=company.name)
    
    context = {
        'user': user,
        'company': company,
        'update_type': update_type,
        'update_message': update_message,
        'job': job,
        'job_url': f"{settings.FRONTEND_URL}/jobs/{job.id}" if job else None,
        'company_url': f"{settings.FRONTEND_URL}/companies/{company.id}",
        'companies_url': f"{settings.FRONTEND_URL}/companies",
    }
    
    # Use custom subject
    html_content = render_to_string(template_config['template'], context)
    text_content = strip_tags(html_content)
    
    try:
        from django.core.mail import EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=template_config['subject'],
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@koroh.com'),
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Company update email sent to {user.email} for {company.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to send company update email to {user.email}: {str(e)}")
        return False

def send_peer_group_invitation_email(user, group, inviter, recent_posts=None):
    """Send peer group invitation email."""
    # Dynamic subject with group name
    template_config = EMAIL_TEMPLATES['peer_group_invitation'].copy()
    template_config['subject'] = template_config['subject'].format(group_name=group.name)
    
    context = {
        'user': user,
        'group': group,
        'inviter': inviter,
        'recent_posts': recent_posts or [],
        'accept_invitation_url': f"{settings.FRONTEND_URL}/peer-groups/{group.id}/accept-invitation",
        'decline_invitation_url': f"{settings.FRONTEND_URL}/peer-groups/{group.id}/decline-invitation",
    }
    
    # Use custom subject
    html_content = render_to_string(template_config['template'], context)
    text_content = strip_tags(html_content)
    
    try:
        from django.core.mail import EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=template_config['subject'],
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@koroh.com'),
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Peer group invitation email sent to {user.email} for {group.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to send peer group invitation email to {user.email}: {str(e)}")
        return False

def send_peer_group_activity_email(user, group, activity_type, **kwargs):
    """Send peer group activity notification email."""
    # Dynamic subject with group name
    template_config = EMAIL_TEMPLATES['peer_group_activity'].copy()
    template_config['subject'] = template_config['subject'].format(group_name=group.name)
    
    context = {
        'user': user,
        'group': group,
        'activity_type': activity_type,
        'post_url': f"{settings.FRONTEND_URL}/peer-groups/{group.id}",
        'group_url': f"{settings.FRONTEND_URL}/peer-groups/{group.id}",
        'notification_settings_url': f"{settings.FRONTEND_URL}/settings/notifications",
        'unsubscribe_url': f"{settings.FRONTEND_URL}/unsubscribe/group/{group.id}",
        **kwargs  # Include additional context like post, comment, new_member, etc.
    }
    
    # Add suggested actions based on activity type
    suggested_actions = []
    if activity_type == 'new_post':
        suggested_actions = [
            "Share your thoughts by commenting on the post",
            "Start a related discussion with your own post",
            "Connect with the post author"
        ]
    elif activity_type == 'new_member':
        suggested_actions = [
            "Welcome the new member with a comment",
            "Share your expertise to help them get started",
            "Invite them to relevant discussions"
        ]
    
    context['suggested_actions'] = suggested_actions
    
    # Use custom subject
    html_content = render_to_string(template_config['template'], context)
    text_content = strip_tags(html_content)
    
    try:
        from django.core.mail import EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject=template_config['subject'],
            body=text_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@koroh.com'),
            to=[user.email],
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Peer group activity email sent to {user.email} for {group.name}")
        return True
    except Exception as e:
        logger.error(f"Failed to send peer group activity email to {user.email}: {str(e)}")
        return False

def send_portfolio_generated_email(user, portfolio_url, quality_score=85, template_count=5):
    """Send portfolio generation completion email."""
    context = {
        'user': user,
        'portfolio_url': portfolio_url,
        'quality_score': quality_score,
        'template_count': template_count,
        'customization_options': True,
        'customize_url': f"{settings.FRONTEND_URL}/portfolio/customize",
    }
    
    return send_professional_email('portfolio_generated', user.email, context)

def send_profile_completion_reminder_email(user, completion_percentage, missing_items=None):
    """Send profile completion reminder email."""
    # Default missing items if not provided
    if missing_items is None:
        missing_items = [
            {'description': 'Add a professional headline', 'time_estimate': '1 minute'},
            {'description': 'Write a professional summary', 'time_estimate': '3 minutes'},
            {'description': 'Upload your CV for AI analysis', 'time_estimate': '2 minutes'},
            {'description': 'Add your location and industry', 'time_estimate': '1 minute'},
        ]
    
    profile_tips = [
        "Use keywords relevant to your industry in your headline and summary",
        "Upload a high-quality, professional profile picture",
        "List your top 10-15 skills, focusing on the most relevant ones",
        "Keep your summary concise but compelling (2-3 paragraphs)",
        "Update your profile regularly with new achievements and skills"
    ]
    
    context = {
        'user': user,
        'completion_percentage': completion_percentage,
        'missing_items': missing_items,
        'profile_tips': profile_tips,
        'profile_url': f"{settings.FRONTEND_URL}/profile",
    }
    
    return send_professional_email('profile_completion_reminder', user.email, context)

def send_weekly_digest_email(user, digest_data):
    """Send weekly digest email with personalized content."""
    context = {
        'user': user,
        'new_jobs_count': digest_data.get('new_jobs_count', 0),
        'featured_jobs': digest_data.get('featured_jobs', []),
        'company_updates': digest_data.get('company_updates', []),
        'peer_group_activity': digest_data.get('peer_group_activity', []),
        'profile_views': digest_data.get('profile_views', 0),
        'job_applications': digest_data.get('job_applications', 0),
        'new_connections': digest_data.get('new_connections', 0),
        'portfolio_views': digest_data.get('portfolio_views', 0),
        'recommendations': digest_data.get('recommendations', []),
        'trending_skills': digest_data.get('trending_skills', []),
        'action_items': digest_data.get('action_items', []),
        'dashboard_url': f"{settings.FRONTEND_URL}/dashboard",
        'profile_url': f"{settings.FRONTEND_URL}/profile",
        'jobs_url': f"{settings.FRONTEND_URL}/jobs",
        'companies_url': f"{settings.FRONTEND_URL}/companies",
        'groups_url': f"{settings.FRONTEND_URL}/peer-groups",
        'digest_settings_url': f"{settings.FRONTEND_URL}/settings/digest",
        'unsubscribe_url': f"{settings.FRONTEND_URL}/unsubscribe/digest",
    }
    
    return send_professional_email('weekly_digest', user.email, context)