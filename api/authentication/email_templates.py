"""
Professional email templates for Koroh platform authentication.

This module provides HTML email templates for user authentication flows
including registration confirmation, password reset, and account verification.
"""

from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.html import strip_tags
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