"""
Services for Companies app including tracking, insights, and notifications.
"""

import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q, Count, Avg, F
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta, datetime
from django.core.mail import send_mail
from django.conf import settings
from .models import Company, CompanyFollow, CompanyInsight

User = get_user_model()
logger = logging.getLogger(__name__)


class CompanyTrackingService:
    """Service for company tracking and following functionality."""
    
    @staticmethod
    def follow_company(user: User, company: Company, notifications_enabled: bool = True) -> Dict[str, Any]:
        """
        Follow a company.
        
        Args:
            user: User who wants to follow the company
            company: Company to follow
            notifications_enabled: Whether to enable notifications
            
        Returns:
            Dictionary with follow status and information
        """
        follow, created = CompanyFollow.objects.get_or_create(
            user=user,
            company=company,
            defaults={'notifications_enabled': notifications_enabled}
        )
        
        if not created and follow.notifications_enabled != notifications_enabled:
            follow.notifications_enabled = notifications_enabled
            follow.save(update_fields=['notifications_enabled'])
        
        return {
            'followed': True,
            'created': created,
            'notifications_enabled': follow.notifications_enabled,
            'followed_at': follow.followed_at,
            'company_name': company.name
        }
    
    @staticmethod
    def unfollow_company(user: User, company: Company) -> Dict[str, Any]:
        """
        Unfollow a company.
        
        Args:
            user: User who wants to unfollow the company
            company: Company to unfollow
            
        Returns:
            Dictionary with unfollow status
        """
        try:
            follow = CompanyFollow.objects.get(user=user, company=company)
            follow.delete()
            return {
                'unfollowed': True,
                'company_name': company.name
            }
        except CompanyFollow.DoesNotExist:
            return {
                'unfollowed': False,
                'error': 'Not following this company',
                'company_name': company.name
            }
    
    @staticmethod
    def get_user_followed_companies(user: User) -> List[Company]:
        """Get companies followed by a user."""
        follows = CompanyFollow.objects.filter(user=user).select_related('company')
        return [follow.company for follow in follows]
    
    @staticmethod
    def get_company_followers(company: Company) -> List[User]:
        """Get users following a company."""
        follows = CompanyFollow.objects.filter(company=company).select_related('user')
        return [follow.user for follow in follows]
    
    @staticmethod
    def get_follow_stats(company: Company) -> Dict[str, Any]:
        """Get follow statistics for a company."""
        follows = CompanyFollow.objects.filter(company=company)
        
        return {
            'total_followers': follows.count(),
            'followers_with_notifications': follows.filter(notifications_enabled=True).count(),
            'recent_followers': follows.filter(
                followed_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'follower_growth': {
                'last_7_days': follows.filter(
                    followed_at__gte=timezone.now() - timedelta(days=7)
                ).count(),
                'last_30_days': follows.filter(
                    followed_at__gte=timezone.now() - timedelta(days=30)
                ).count(),
                'last_90_days': follows.filter(
                    followed_at__gte=timezone.now() - timedelta(days=90)
                ).count(),
            }
        }
    
    @staticmethod
    def record_user_interaction(user: User, company: Company) -> None:
        """Record a user interaction with a company."""
        try:
            follow = CompanyFollow.objects.get(user=user, company=company)
            follow.record_interaction()
        except CompanyFollow.DoesNotExist:
            # User is not following the company, but we can still track the interaction
            # by incrementing the company's view count
            company.increment_view_count()


class CompanyInsightService:
    """Service for generating and managing company insights."""
    
    @staticmethod
    def create_insight(
        company: Company,
        insight_type: str,
        title: str,
        description: str = '',
        data: Dict[str, Any] = None,
        source: str = '',
        confidence_score: float = 1.0,
        is_public: bool = True,
        expires_at: Optional[datetime] = None
    ) -> CompanyInsight:
        """Create a new company insight."""
        return CompanyInsight.objects.create(
            company=company,
            insight_type=insight_type,
            title=title,
            description=description,
            data=data or {},
            source=source,
            confidence_score=confidence_score,
            is_public=is_public,
            expires_at=expires_at
        )
    
    @staticmethod
    def generate_hiring_insights(company: Company) -> List[CompanyInsight]:
        """Generate hiring trend insights for a company."""
        insights = []
        
        # Get job posting data
        from jobs.models import Job
        jobs = Job.objects.filter(company=company)
        
        # Recent hiring activity
        recent_jobs = jobs.filter(
            posted_date__gte=timezone.now() - timedelta(days=30)
        )
        
        if recent_jobs.exists():
            insight_data = {
                'total_jobs_posted': recent_jobs.count(),
                'job_types': list(recent_jobs.values_list('job_type', flat=True).distinct()),
                'experience_levels': list(recent_jobs.values_list('experience_level', flat=True).distinct()),
                'locations': list(recent_jobs.values_list('location', flat=True).distinct()),
                'remote_friendly_percentage': (
                    recent_jobs.filter(is_remote_friendly=True).count() / recent_jobs.count() * 100
                ) if recent_jobs.count() > 0 else 0
            }
            
            insights.append(CompanyInsightService.create_insight(
                company=company,
                insight_type='hiring',
                title='Recent Hiring Activity',
                description=f'Posted {recent_jobs.count()} new jobs in the last 30 days',
                data=insight_data,
                source='platform_data',
                confidence_score=1.0
            ))
        
        # Salary trends
        jobs_with_salary = jobs.filter(salary_min__isnull=False, salary_max__isnull=False)
        if jobs_with_salary.exists():
            avg_min_salary = jobs_with_salary.aggregate(avg_min=Avg('salary_min'))['avg_min']
            avg_max_salary = jobs_with_salary.aggregate(avg_max=Avg('salary_max'))['avg_max']
            
            insight_data = {
                'average_salary_range': {
                    'min': round(avg_min_salary, 2) if avg_min_salary else None,
                    'max': round(avg_max_salary, 2) if avg_max_salary else None,
                    'currency': 'USD'  # Default currency
                },
                'jobs_with_equity': jobs_with_salary.filter(equity_offered=True).count(),
                'total_jobs_analyzed': jobs_with_salary.count()
            }
            
            insights.append(CompanyInsightService.create_insight(
                company=company,
                insight_type='salary',
                title='Salary Information',
                description='Average salary ranges for positions at this company',
                data=insight_data,
                source='platform_data',
                confidence_score=0.8
            ))
        
        return insights
    
    @staticmethod
    def generate_growth_insights(company: Company) -> List[CompanyInsight]:
        """Generate growth insights for a company."""
        insights = []
        
        # Follower growth
        follows = CompanyFollow.objects.filter(company=company)
        if follows.exists():
            growth_data = CompanyTrackingService.get_follow_stats(company)
            
            insights.append(CompanyInsightService.create_insight(
                company=company,
                insight_type='growth',
                title='Follower Growth',
                description='Company following trends and growth metrics',
                data=growth_data,
                source='platform_data',
                confidence_score=1.0
            ))
        
        # Job posting growth
        from jobs.models import Job
        jobs = Job.objects.filter(company=company)
        
        if jobs.exists():
            job_growth_data = {
                'total_jobs_posted': jobs.count(),
                'active_jobs': jobs.filter(is_active=True, status='published').count(),
                'jobs_by_month': {}
            }
            
            # Calculate jobs posted by month for the last 6 months
            for i in range(6):
                month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
                month_end = month_start + timedelta(days=31)
                month_jobs = jobs.filter(
                    posted_date__gte=month_start,
                    posted_date__lt=month_end
                ).count()
                job_growth_data['jobs_by_month'][month_start.strftime('%Y-%m')] = month_jobs
            
            insights.append(CompanyInsightService.create_insight(
                company=company,
                insight_type='growth',
                title='Job Posting Activity',
                description='Job posting trends and activity levels',
                data=job_growth_data,
                source='platform_data',
                confidence_score=1.0
            ))
        
        return insights
    
    @staticmethod
    def get_company_insights(
        company: Company,
        insight_types: Optional[List[str]] = None,
        is_public: bool = True
    ) -> List[CompanyInsight]:
        """Get insights for a company."""
        queryset = CompanyInsight.objects.filter(company=company, is_public=is_public)
        
        if insight_types:
            queryset = queryset.filter(insight_type__in=insight_types)
        
        # Filter out expired insights
        queryset = queryset.filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )
        
        return list(queryset.order_by('-created_at'))
    
    @staticmethod
    def update_company_insights(company: Company) -> Dict[str, Any]:
        """Update all insights for a company."""
        try:
            # Generate new insights
            hiring_insights = CompanyInsightService.generate_hiring_insights(company)
            growth_insights = CompanyInsightService.generate_growth_insights(company)
            
            all_insights = hiring_insights + growth_insights
            
            return {
                'success': True,
                'insights_created': len(all_insights),
                'insight_types': [insight.insight_type for insight in all_insights]
            }
        except Exception as e:
            logger.error(f"Error updating insights for company {company.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class CompanyNotificationService:
    """Service for company-related notifications."""
    
    @staticmethod
    def notify_followers_of_new_job(company: Company, job) -> Dict[str, Any]:
        """Notify company followers of a new job posting."""
        from jobs.models import Job
        
        # Get followers with notifications enabled
        followers = CompanyFollow.objects.filter(
            company=company,
            notifications_enabled=True
        ).select_related('user')
        
        if not followers.exists():
            return {'notifications_sent': 0, 'message': 'No followers with notifications enabled'}
        
        notification_count = 0
        failed_notifications = []
        
        for follow in followers:
            try:
                # Send email notification
                subject = f"New Job at {company.name}: {job.title}"
                message = f"""
                Hi {follow.user.get_full_name()},
                
                {company.name} has posted a new job that might interest you:
                
                Job Title: {job.title}
                Location: {job.location}
                Job Type: {job.get_job_type_display()}
                Experience Level: {job.get_experience_level_display()}
                
                View the full job posting and apply at: [Job URL]
                
                Best regards,
                The Koroh Team
                """
                
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[follow.user.email],
                    fail_silently=False
                )
                
                notification_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send notification to {follow.user.email}: {e}")
                failed_notifications.append(follow.user.email)
        
        return {
            'notifications_sent': notification_count,
            'failed_notifications': failed_notifications,
            'total_followers': followers.count()
        }
    
    @staticmethod
    def notify_followers_of_company_update(company: Company, update_type: str, message: str) -> Dict[str, Any]:
        """Notify company followers of general company updates."""
        followers = CompanyFollow.objects.filter(
            company=company,
            notifications_enabled=True
        ).select_related('user')
        
        if not followers.exists():
            return {'notifications_sent': 0, 'message': 'No followers with notifications enabled'}
        
        notification_count = 0
        failed_notifications = []
        
        for follow in followers:
            try:
                subject = f"Update from {company.name}"
                email_message = f"""
                Hi {follow.user.get_full_name()},
                
                {company.name} has an update for you:
                
                {message}
                
                Visit the company profile to learn more: [Company URL]
                
                Best regards,
                The Koroh Team
                """
                
                send_mail(
                    subject=subject,
                    message=email_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[follow.user.email],
                    fail_silently=False
                )
                
                notification_count += 1
                
            except Exception as e:
                logger.error(f"Failed to send notification to {follow.user.email}: {e}")
                failed_notifications.append(follow.user.email)
        
        return {
            'notifications_sent': notification_count,
            'failed_notifications': failed_notifications,
            'total_followers': followers.count()
        }
    
    @staticmethod
    def send_weekly_digest(user: User) -> Dict[str, Any]:
        """Send weekly digest of followed companies' activities."""
        followed_companies = CompanyTrackingService.get_user_followed_companies(user)
        
        if not followed_companies:
            return {'digest_sent': False, 'message': 'User is not following any companies'}
        
        # Collect activities from the last week
        week_ago = timezone.now() - timedelta(days=7)
        activities = []
        
        for company in followed_companies:
            # New jobs
            from jobs.models import Job
            new_jobs = Job.objects.filter(
                company=company,
                posted_date__gte=week_ago,
                is_active=True,
                status='published'
            )
            
            if new_jobs.exists():
                activities.append({
                    'company': company.name,
                    'type': 'new_jobs',
                    'count': new_jobs.count(),
                    'details': [{'title': job.title, 'location': job.location} for job in new_jobs[:3]]
                })
            
            # New insights
            new_insights = CompanyInsight.objects.filter(
                company=company,
                created_at__gte=week_ago,
                is_public=True
            )
            
            if new_insights.exists():
                activities.append({
                    'company': company.name,
                    'type': 'new_insights',
                    'count': new_insights.count(),
                    'details': [{'title': insight.title, 'type': insight.insight_type} for insight in new_insights[:3]]
                })
        
        if not activities:
            return {'digest_sent': False, 'message': 'No activities to report'}
        
        # Send digest email
        try:
            subject = "Your Weekly Company Updates - Koroh"
            message = f"""
            Hi {user.get_full_name()},
            
            Here's your weekly digest of activities from companies you follow:
            
            """
            
            for activity in activities:
                if activity['type'] == 'new_jobs':
                    message += f"\n{activity['company']} posted {activity['count']} new job(s):\n"
                    for job in activity['details']:
                        message += f"  - {job['title']} in {job['location']}\n"
                elif activity['type'] == 'new_insights':
                    message += f"\n{activity['company']} has {activity['count']} new insight(s):\n"
                    for insight in activity['details']:
                        message += f"  - {insight['title']} ({insight['type']})\n"
            
            message += """
            
            Visit Koroh to explore these opportunities and updates in detail.
            
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
            
            return {
                'digest_sent': True,
                'activities_count': len(activities),
                'companies_count': len(followed_companies)
            }
            
        except Exception as e:
            logger.error(f"Failed to send weekly digest to {user.email}: {e}")
            return {
                'digest_sent': False,
                'error': str(e)
            }