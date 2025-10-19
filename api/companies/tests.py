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