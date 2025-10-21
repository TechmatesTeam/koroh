"""
Tests for Companies app models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .models import Company, CompanyFollow, CompanyInsight

User = get_user_model()


class CompanyModelTest(TestCase):
    """Test cases for Company model."""
    
    def setUp(self):
        """Set up test data."""
        self.company_data = {
            'name': 'Test Company',
            'description': 'A test company for unit testing',
            'industry': 'Technology',
            'company_size': 'medium',
            'company_type': 'private',
            'headquarters': 'San Francisco, CA',
            'website': 'https://testcompany.com',
        }
    
    def test_company_creation(self):
        """Test basic company creation."""
        company = Company.objects.create(**self.company_data)
        
        self.assertEqual(company.name, 'Test Company')
        self.assertEqual(company.industry, 'Technology')
        self.assertTrue(company.is_active)
        self.assertFalse(company.is_verified)
        self.assertEqual(company.follower_count, 0)
        self.assertEqual(company.job_count, 0)
    
    def test_company_slug_generation(self):
        """Test automatic slug generation."""
        company = Company.objects.create(**self.company_data)
        self.assertEqual(company.slug, 'test-company')
    
    def test_company_str_representation(self):
        """Test string representation of company."""
        company = Company.objects.create(**self.company_data)
        self.assertEqual(str(company), 'Test Company')
    
    def test_company_unique_name(self):
        """Test that company names must be unique."""
        Company.objects.create(**self.company_data)
        
        with self.assertRaises(IntegrityError):
            Company.objects.create(**self.company_data)
    
    def test_company_is_complete_property(self):
        """Test is_complete property."""
        # Incomplete company (missing required fields)
        incomplete_company = Company.objects.create(
            name='Incomplete Company',
            description='',
            industry='',
            company_size='',
            headquarters='',
            website=''
        )
        self.assertFalse(incomplete_company.is_complete)
        
        # Complete company
        complete_company = Company.objects.create(**self.company_data)
        self.assertTrue(complete_company.is_complete)


class CompanyFollowModelTest(TestCase):
    """Test cases for CompanyFollow model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://testcompany.com',
        )
    
    def test_company_follow_creation(self):
        """Test basic company follow creation."""
        follow = CompanyFollow.objects.create(
            user=self.user,
            company=self.company
        )
        
        self.assertEqual(follow.user, self.user)
        self.assertEqual(follow.company, self.company)
        self.assertTrue(follow.notifications_enabled)
        self.assertEqual(follow.interaction_count, 0)
    
    def test_company_follow_unique_constraint(self):
        """Test that a user can only follow a company once."""
        CompanyFollow.objects.create(user=self.user, company=self.company)
        
        with self.assertRaises(IntegrityError):
            CompanyFollow.objects.create(user=self.user, company=self.company)
    
    def test_company_follow_str_representation(self):
        """Test string representation of company follow."""
        follow = CompanyFollow.objects.create(
            user=self.user,
            company=self.company
        )
        expected_str = f"{self.user.get_full_name()} follows {self.company.name}"
        self.assertEqual(str(follow), expected_str)


class CompanyInsightModelTest(TestCase):
    """Test cases for CompanyInsight model."""
    
    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://testcompany.com',
        )
    
    def test_company_insight_creation(self):
        """Test basic company insight creation."""
        insight = CompanyInsight.objects.create(
            company=self.company,
            insight_type='growth',
            title='Company Growth Metrics',
            description='Growth metrics for Q4',
            data={'revenue_growth': '25%', 'employee_growth': '15%'},
            confidence_score=0.85
        )
        
        self.assertEqual(insight.company, self.company)
        self.assertEqual(insight.insight_type, 'growth')
        self.assertEqual(insight.title, 'Company Growth Metrics')
        self.assertTrue(insight.is_public)
        self.assertEqual(insight.confidence_score, 0.85)
    
    def test_company_insight_str_representation(self):
        """Test string representation of company insight."""
        insight = CompanyInsight.objects.create(
            company=self.company,
            insight_type='growth',
            title='Company Growth Metrics',
            data={'revenue_growth': '25%'}
        )
        expected_str = f"{self.company.name} - Company Growth Metrics"
        self.assertEqual(str(insight), expected_str)
class CompanySearchServiceTest(TestCase):
    """Test cases for CompanySearchService."""
    
    def setUp(self):
        """Set up test data."""
        self.company1 = Company.objects.create(
            name='Tech Startup',
            description='A fast-growing technology startup',
            industry='Technology',
            company_size='small',
            company_type='startup',
            headquarters='San Francisco, CA',
            website='https://techstartup.com',
            is_hiring=True
        )
        
        self.company2 = Company.objects.create(
            name='Finance Corp',
            description='A large financial services company',
            industry='Finance',
            company_size='large',
            company_type='public',
            headquarters='New York, NY',
            website='https://financecorp.com',
            is_verified=True
        )
    
    def test_basic_company_search(self):
        """Test basic company search functionality."""
        from jobs.services import CompanySearchService
        
        search_params = {'query': 'Tech'}
        result = CompanySearchService.search_companies(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.company1, result['queryset'])
        self.assertNotIn(self.company2, result['queryset'])
    
    def test_industry_filter(self):
        """Test industry-based filtering."""
        from jobs.services import CompanySearchService
        
        search_params = {'industry': 'Finance'}
        result = CompanySearchService.search_companies(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.company2, result['queryset'])
    
    def test_company_size_filter(self):
        """Test company size filtering."""
        from jobs.services import CompanySearchService
        
        search_params = {'company_size': 'small'}
        result = CompanySearchService.search_companies(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.company1, result['queryset'])
    
    def test_hiring_filter(self):
        """Test hiring status filter."""
        from jobs.services import CompanySearchService
        
        search_params = {'is_hiring': True}
        result = CompanySearchService.search_companies(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.company1, result['queryset'])
    
    def test_verified_filter(self):
        """Test verified status filter."""
        from jobs.services import CompanySearchService
        
        search_params = {'is_verified': True}
        result = CompanySearchService.search_companies(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.company2, result['queryset'])


class CompanyTrackingServiceTest(TestCase):
    """Test cases for CompanyTrackingService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://testcompany.com',
        )
    
    def test_follow_company(self):
        """Test following a company."""
        from .services import CompanyTrackingService
        
        result = CompanyTrackingService.follow_company(self.user, self.company)
        
        self.assertTrue(result['followed'])
        self.assertTrue(result['created'])
        self.assertTrue(result['notifications_enabled'])
        self.assertEqual(result['company_name'], self.company.name)
        
        # Verify the follow was created
        self.assertTrue(
            CompanyFollow.objects.filter(user=self.user, company=self.company).exists()
        )
    
    def test_follow_company_twice(self):
        """Test following a company that's already followed."""
        from .services import CompanyTrackingService
        
        # First follow
        result1 = CompanyTrackingService.follow_company(self.user, self.company)
        self.assertTrue(result1['created'])
        
        # Second follow
        result2 = CompanyTrackingService.follow_company(self.user, self.company)
        self.assertFalse(result2['created'])
        self.assertTrue(result2['followed'])
    
    def test_unfollow_company(self):
        """Test unfollowing a company."""
        from .services import CompanyTrackingService
        
        # First follow the company
        CompanyTrackingService.follow_company(self.user, self.company)
        
        # Then unfollow
        result = CompanyTrackingService.unfollow_company(self.user, self.company)
        
        self.assertTrue(result['unfollowed'])
        self.assertEqual(result['company_name'], self.company.name)
        
        # Verify the follow was deleted
        self.assertFalse(
            CompanyFollow.objects.filter(user=self.user, company=self.company).exists()
        )
    
    def test_unfollow_not_followed_company(self):
        """Test unfollowing a company that's not followed."""
        from .services import CompanyTrackingService
        
        result = CompanyTrackingService.unfollow_company(self.user, self.company)
        
        self.assertFalse(result['unfollowed'])
        self.assertIn('error', result)
    
    def test_get_follow_stats(self):
        """Test getting follow statistics."""
        from .services import CompanyTrackingService
        
        # Create some follows
        user2 = User.objects.create_user(
            email='test2@example.com',
            first_name='Test2',
            last_name='User2',
            password='testpass123'
        )
        
        CompanyTrackingService.follow_company(self.user, self.company)
        CompanyTrackingService.follow_company(user2, self.company, notifications_enabled=False)
        
        stats = CompanyTrackingService.get_follow_stats(self.company)
        
        self.assertEqual(stats['total_followers'], 2)
        self.assertEqual(stats['followers_with_notifications'], 1)
        self.assertIn('follower_growth', stats)


class CompanyInsightServiceTest(TestCase):
    """Test cases for CompanyInsightService."""
    
    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://testcompany.com',
        )
    
    def test_create_insight(self):
        """Test creating a company insight."""
        from .services import CompanyInsightService
        
        insight = CompanyInsightService.create_insight(
            company=self.company,
            insight_type='growth',
            title='Test Insight',
            description='A test insight',
            data={'test': 'data'},
            confidence_score=0.8
        )
        
        self.assertEqual(insight.company, self.company)
        self.assertEqual(insight.insight_type, 'growth')
        self.assertEqual(insight.title, 'Test Insight')
        self.assertEqual(insight.data, {'test': 'data'})
        self.assertEqual(insight.confidence_score, 0.8)
        self.assertTrue(insight.is_public)
    
    def test_generate_hiring_insights(self):
        """Test generating hiring insights."""
        from .services import CompanyInsightService
        from jobs.models import Job
        
        # Create some jobs
        Job.objects.create(
            title='Software Engineer',
            company=self.company,
            description='A software engineering role',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            status='published'
        )
        
        insights = CompanyInsightService.generate_hiring_insights(self.company)
        
        self.assertGreater(len(insights), 0)
        self.assertTrue(any(insight.insight_type == 'hiring' for insight in insights))
    
    def test_get_company_insights(self):
        """Test getting company insights."""
        from .services import CompanyInsightService
        
        # Create some insights
        insight1 = CompanyInsightService.create_insight(
            company=self.company,
            insight_type='growth',
            title='Growth Insight',
            is_public=True
        )
        
        insight2 = CompanyInsightService.create_insight(
            company=self.company,
            insight_type='hiring',
            title='Hiring Insight',
            is_public=False
        )
        
        # Get public insights
        public_insights = CompanyInsightService.get_company_insights(self.company, is_public=True)
        self.assertEqual(len(public_insights), 1)
        self.assertEqual(public_insights[0].title, 'Growth Insight')
        
        # Get insights by type
        growth_insights = CompanyInsightService.get_company_insights(
            self.company, insight_types=['growth'], is_public=True
        )
        self.assertEqual(len(growth_insights), 1)
        self.assertEqual(growth_insights[0].insight_type, 'growth')
    
    def test_update_company_insights(self):
        """Test updating all company insights."""
        from .services import CompanyInsightService
        from jobs.models import Job
        
        # Create some jobs for insights
        Job.objects.create(
            title='Software Engineer',
            company=self.company,
            description='A software engineering role',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            status='published',
            salary_min=80000,
            salary_max=120000
        )
        
        result = CompanyInsightService.update_company_insights(self.company)
        
        self.assertTrue(result['success'])
        self.assertGreater(result['insights_created'], 0)
        self.assertIn('insight_types', result)


class CompanyNotificationServiceTest(TestCase):
    """Test cases for CompanyNotificationService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='notification_test@example.com',
            first_name='Notification',
            last_name='User',
            password='testpass123'
        )
        
        self.company = Company.objects.create(
            name='Notification Test Company',
            description='A test company for notifications',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://notificationtest.com',
        )
        
        # Create a follow relationship
        CompanyFollow.objects.create(
            user=self.user,
            company=self.company,
            notifications_enabled=True
        )
    
    def test_notify_followers_of_new_job(self):
        """Test notifying followers of new job postings."""
        from .services import CompanyNotificationService
        from jobs.models import Job
        from django.test import override_settings
        from django.core import mail
        
        # Create a job
        job = Job.objects.create(
            title='Test Job',
            company=self.company,
            description='A test job',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            status='published'
        )
        
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            result = CompanyNotificationService.notify_followers_of_new_job(
                self.company, job
            )
            
            self.assertEqual(result['notifications_sent'], 1)
            self.assertEqual(result['total_followers'], 1)
            self.assertEqual(len(result['failed_notifications']), 0)
            
            # Verify email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn('New Job at', mail.outbox[0].subject)
    
    def test_notify_followers_no_notifications_enabled(self):
        """Test notification when no followers have notifications enabled."""
        from .services import CompanyNotificationService
        from jobs.models import Job
        
        # Disable notifications for the follower
        follow = CompanyFollow.objects.get(user=self.user, company=self.company)
        follow.notifications_enabled = False
        follow.save()
        
        job = Job.objects.create(
            title='Test Job',
            company=self.company,
            description='A test job',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            status='published'
        )
        
        result = CompanyNotificationService.notify_followers_of_new_job(
            self.company, job
        )
        
        self.assertEqual(result['notifications_sent'], 0)
        self.assertIn('No followers with notifications enabled', result['message'])
    
    def test_notify_followers_of_company_update(self):
        """Test notifying followers of company updates."""
        from .services import CompanyNotificationService
        from django.test import override_settings
        from django.core import mail
        
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            result = CompanyNotificationService.notify_followers_of_company_update(
                self.company,
                'general',
                'We have exciting news to share!'
            )
            
            self.assertEqual(result['notifications_sent'], 1)
            self.assertEqual(result['total_followers'], 1)
            
            # Verify email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn('Update from', mail.outbox[0].subject)
    
    def test_send_weekly_digest(self):
        """Test sending weekly digest to users."""
        from .services import CompanyNotificationService
        from jobs.models import Job
        from django.utils import timezone
        from datetime import timedelta
        from django.test import override_settings
        from django.core import mail
        
        # Create a recent job
        Job.objects.create(
            title='Recent Job',
            company=self.company,
            description='A recent job',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            status='published',
            posted_date=timezone.now() - timedelta(days=2)
        )
        
        with override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            result = CompanyNotificationService.send_weekly_digest(self.user)
            
            self.assertTrue(result['digest_sent'])
            self.assertGreater(result['activities_count'], 0)
            self.assertEqual(result['companies_count'], 1)
            
            # Verify email was sent
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn('Weekly Company Updates', mail.outbox[0].subject)
    
    def test_send_weekly_digest_no_activities(self):
        """Test weekly digest when there are no activities."""
        from .services import CompanyNotificationService
        
        result = CompanyNotificationService.send_weekly_digest(self.user)
        
        self.assertFalse(result['digest_sent'])
        self.assertIn('No activities to report', result['message'])


class CompanyAPIViewTest(TestCase):
    """Test cases for Company API views."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='company_api_test@example.com',
            first_name='Company API',
            last_name='User',
            password='testpass123'
        )
        
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            password='adminpass123',
            is_staff=True
        )
        
        self.company = Company.objects.create(
            name='API Test Company',
            description='A test company for API testing',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://apitestcompany.com',
        )
    
    def test_company_search_api(self):
        """Test company search API endpoint."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        response = client.post('/api/v1/companies/companies/search/', {
            'query': 'API Test',
            'industry': 'Technology'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        # API uses pagination, so it returns 'count' instead of 'total_count'
        self.assertIn('count', response.data)
        
        # Verify company is in results
        company_names = [company['name'] for company in response.data['results']]
        self.assertIn('API Test Company', company_names)
    
    def test_company_follow_api(self):
        """Test company follow API endpoint."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        response = client.post(f'/api/v1/companies/companies/{self.company.id}/follow/')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('message', response.data)
        
        # Verify follow was created
        self.assertTrue(
            CompanyFollow.objects.filter(user=self.user, company=self.company).exists()
        )
    
    def test_company_unfollow_api(self):
        """Test company unfollow API endpoint."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        # First follow the company
        CompanyFollow.objects.create(user=self.user, company=self.company)
        
        response = client.delete(f'/api/v1/companies/companies/{self.company.id}/unfollow/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify follow was deleted
        self.assertFalse(
            CompanyFollow.objects.filter(user=self.user, company=self.company).exists()
        )
    
    def test_company_insights_api(self):
        """Test company insights API endpoint."""
        from rest_framework.test import APIClient
        from rest_framework import status
        from .services import CompanyInsightService
        
        client = APIClient()
        
        # Create some insights
        CompanyInsightService.create_insight(
            company=self.company,
            insight_type='growth',
            title='Test Insight',
            is_public=True
        )
        
        response = client.get(f'/api/v1/companies/companies/{self.company.id}/insights/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # API uses pagination
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_company_stats_api(self):
        """Test company statistics API endpoint."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        
        # Create a follower
        CompanyFollow.objects.create(user=self.user, company=self.company)
        
        response = client.get(f'/api/v1/companies/companies/{self.company.id}/stats/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_followers', response.data)
        self.assertIn('total_jobs', response.data)
        self.assertIn('profile_views', response.data)
        self.assertEqual(response.data['total_followers'], 1)
    
    def test_company_view_count_increment(self):
        """Test that company view count increments on retrieve."""
        from rest_framework.test import APIClient
        
        client = APIClient()
        initial_count = self.company.view_count
        
        response = client.get(f'/api/v1/companies/companies/{self.company.id}/')
        
        self.company.refresh_from_db()
        self.assertEqual(self.company.view_count, initial_count + 1)
    
    def test_update_insights_api_admin_only(self):
        """Test update insights API endpoint (admin only)."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        
        # Test without authentication
        response = client.post(f'/api/v1/companies/companies/{self.company.id}/update_insights/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Test with regular user
        client.force_authenticate(user=self.user)
        response = client.post(f'/api/v1/companies/companies/{self.company.id}/update_insights/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with admin user
        client.force_authenticate(user=self.admin_user)
        response = client.post(f'/api/v1/companies/companies/{self.company.id}/update_insights/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success', response.data)
    
    def test_company_followers_api_admin_only(self):
        """Test company followers API endpoint (admin only)."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        
        # Create a follower
        CompanyFollow.objects.create(user=self.user, company=self.company)
        
        # Test without authentication - should return 401 or 403
        response = client.get(f'/api/v1/companies/companies/{self.company.id}/followers/')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        
        # Test with regular user
        client.force_authenticate(user=self.user)
        response = client.get(f'/api/v1/companies/companies/{self.company.id}/followers/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test with admin user
        client.force_authenticate(user=self.admin_user)
        response = client.get(f'/api/v1/companies/companies/{self.company.id}/followers/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # API uses pagination
        self.assertIn('results', response.data)
    
    def test_company_jobs_api(self):
        """Test company jobs API endpoint."""
        from rest_framework.test import APIClient
        from rest_framework import status
        from jobs.models import Job
        
        client = APIClient()
        
        # Create a job for the company
        Job.objects.create(
            title='Company Job',
            company=self.company,
            description='A job from the company',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            status='published'
        )
        
        response = client.get(f'/api/v1/companies/companies/{self.company.id}/jobs/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # API uses pagination
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
        
        # Verify job is in results
        job_titles = [job['title'] for job in response.data['results']]
        self.assertIn('Company Job', job_titles)


class CompanyFollowAPITest(TestCase):
    """Test cases for CompanyFollow API views."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='follow_test@example.com',
            first_name='Follow',
            last_name='User',
            password='testpass123'
        )
        
        self.company1 = Company.objects.create(
            name='Follow Test Company 1',
            description='First test company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://followtest1.com',
        )
        
        self.company2 = Company.objects.create(
            name='Follow Test Company 2',
            description='Second test company',
            industry='Finance',
            company_size='large',
            company_type='public',
            headquarters='New York, NY',
            website='https://followtest2.com',
        )
        
        # Create follows
        CompanyFollow.objects.create(user=self.user, company=self.company1)
        CompanyFollow.objects.create(user=self.user, company=self.company2)
    
    def test_get_user_follows(self):
        """Test getting user's company follows."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        response = client.get('/api/v1/companies/follows/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    def test_get_followed_companies(self):
        """Test getting companies followed by user."""
        from rest_framework.test import APIClient
        from rest_framework import status
        
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        response = client.get('/api/v1/companies/follows/companies/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
        # Verify companies are in results
        company_names = [company['name'] for company in response.data]
        self.assertIn('Follow Test Company 1', company_names)
        self.assertIn('Follow Test Company 2', company_names)