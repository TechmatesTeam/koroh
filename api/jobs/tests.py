"""
Tests for Jobs app models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from companies.models import Company
from .models import Job, JobApplication, JobSavedByUser

User = get_user_model()


class JobModelTest(TestCase):
    """Test cases for Job model."""
    
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
        
        self.job_data = {
            'title': 'Senior Software Engineer',
            'company': self.company,
            'description': 'We are looking for a senior software engineer...',
            'job_type': 'full_time',
            'experience_level': 'senior',
            'work_arrangement': 'hybrid',
            'location': 'San Francisco, CA',
            'salary_min': 120000,
            'salary_max': 180000,
            'salary_currency': 'USD',
            'salary_period': 'yearly',
        }
    
    def test_job_creation(self):
        """Test basic job creation."""
        job = Job.objects.create(**self.job_data)
        
        self.assertEqual(job.title, 'Senior Software Engineer')
        self.assertEqual(job.company, self.company)
        self.assertEqual(job.job_type, 'full_time')
        self.assertEqual(job.experience_level, 'senior')
        self.assertEqual(job.status, 'draft')
        self.assertTrue(job.is_active)
        self.assertEqual(job.view_count, 0)
        self.assertEqual(job.application_count, 0)
    
    def test_job_slug_generation(self):
        """Test automatic slug generation."""
        job = Job.objects.create(**self.job_data)
        self.assertTrue(job.slug.startswith('senior-software-engineer-test-company'))
    
    def test_job_str_representation(self):
        """Test string representation of job."""
        job = Job.objects.create(**self.job_data)
        expected_str = f"{job.title} at {job.company.name}"
        self.assertEqual(str(job), expected_str)
    
    def test_job_salary_range_display(self):
        """Test salary range display property."""
        job = Job.objects.create(**self.job_data)
        expected_range = "$120,000 - $180,000"
        self.assertEqual(job.salary_range_display, expected_range)
        
        # Test job without salary
        job_no_salary = Job.objects.create(
            title='Test Job',
            company=self.company,
            description='Test description',
            job_type='full_time',
            experience_level='mid',
            location='Remote'
        )
        self.assertIsNone(job_no_salary.salary_range_display)
    
    def test_job_is_published_property(self):
        """Test is_published property."""
        job = Job.objects.create(**self.job_data)
        
        # Draft job should not be published
        self.assertFalse(job.is_published)
        
        # Published and active job should be published
        job.status = 'published'
        job.save()
        self.assertTrue(job.is_published)
    
    def test_job_increment_view_count(self):
        """Test view count increment."""
        job = Job.objects.create(**self.job_data)
        initial_count = job.view_count
        
        job.increment_view_count()
        job.refresh_from_db()
        
        self.assertEqual(job.view_count, initial_count + 1)
    
    def test_job_add_skill(self):
        """Test adding skills to job."""
        job = Job.objects.create(**self.job_data)
        
        job.add_skill('Python', is_required=True)
        job.add_skill('JavaScript', is_required=False)
        
        job.refresh_from_db()
        self.assertIn('Python', job.skills_required)
        self.assertIn('JavaScript', job.skills_preferred)


class JobApplicationModelTest(TestCase):
    """Test cases for JobApplication model."""
    
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
        
        self.job = Job.objects.create(
            title='Software Engineer',
            company=self.company,
            description='We are looking for a software engineer...',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA'
        )
    
    def test_job_application_creation(self):
        """Test basic job application creation."""
        application = JobApplication.objects.create(
            user=self.user,
            job=self.job,
            cover_letter='I am interested in this position...'
        )
        
        self.assertEqual(application.user, self.user)
        self.assertEqual(application.job, self.job)
        self.assertEqual(application.status, 'pending')
        self.assertEqual(application.ai_match_score, 0.0)
        self.assertTrue(application.is_active)
    
    def test_job_application_unique_constraint(self):
        """Test that a user can only apply to a job once."""
        JobApplication.objects.create(user=self.user, job=self.job)
        
        with self.assertRaises(IntegrityError):
            JobApplication.objects.create(user=self.user, job=self.job)
    
    def test_job_application_str_representation(self):
        """Test string representation of job application."""
        application = JobApplication.objects.create(
            user=self.user,
            job=self.job
        )
        expected_str = f"{self.user.get_full_name()} -> {self.job.title}"
        self.assertEqual(str(application), expected_str)
    
    def test_job_application_status_update(self):
        """Test application status update."""
        application = JobApplication.objects.create(
            user=self.user,
            job=self.job
        )
        
        # Update status to reviewing
        application.update_status('reviewing')
        application.refresh_from_db()
        
        self.assertEqual(application.status, 'reviewing')
        self.assertIsNotNone(application.reviewed_at)


class JobSavedByUserModelTest(TestCase):
    """Test cases for JobSavedByUser model."""
    
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
        
        self.job = Job.objects.create(
            title='Software Engineer',
            company=self.company,
            description='We are looking for a software engineer...',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA'
        )
    
    def test_job_saved_creation(self):
        """Test basic job saved creation."""
        saved_job = JobSavedByUser.objects.create(
            user=self.user,
            job=self.job,
            notes='Interesting position, good company culture'
        )
        
        self.assertEqual(saved_job.user, self.user)
        self.assertEqual(saved_job.job, self.job)
        self.assertEqual(saved_job.notes, 'Interesting position, good company culture')
    
    def test_job_saved_unique_constraint(self):
        """Test that a user can only save a job once."""
        JobSavedByUser.objects.create(user=self.user, job=self.job)
        
        with self.assertRaises(IntegrityError):
            JobSavedByUser.objects.create(user=self.user, job=self.job)
    
    def test_job_saved_str_representation(self):
        """Test string representation of saved job."""
        saved_job = JobSavedByUser.objects.create(
            user=self.user,
            job=self.job
        )
        expected_str = f"{self.user.get_full_name()} saved {self.job.title}"
        self.assertEqual(str(saved_job), expected_str)

class JobSearchServiceTest(TestCase):
    """Test cases for JobSearchService."""
    
    def setUp(self):
        """Set up test data."""
        self.company = Company.objects.create(
            name='Tech Company',
            description='A technology company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='New York, NY',
            website='https://techcompany.com',
        )
        
        self.job1 = Job.objects.create(
            title='Python Developer',
            company=self.company,
            description='We need a Python developer with Django experience',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            skills_required=['Python', 'Django'],
            status='published'
        )
        
        self.job2 = Job.objects.create(
            title='JavaScript Developer',
            company=self.company,
            description='Frontend developer with React experience',
            job_type='full_time',
            experience_level='senior',
            location='Remote',
            skills_required=['JavaScript', 'React'],
            is_remote_friendly=True,
            status='published'
        )
    
    def test_basic_search(self):
        """Test basic job search functionality."""
        from .services import JobSearchService
        
        search_params = {'query': 'Python'}
        result = JobSearchService.search_jobs(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.job1, result['queryset'])
        self.assertNotIn(self.job2, result['queryset'])
    
    def test_location_search(self):
        """Test location-based search."""
        from .services import JobSearchService
        
        search_params = {'location': 'San Francisco'}
        result = JobSearchService.search_jobs(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.job1, result['queryset'])
    
    def test_remote_filter(self):
        """Test remote work filter."""
        from .services import JobSearchService
        
        search_params = {'is_remote_friendly': True}
        result = JobSearchService.search_jobs(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.job2, result['queryset'])
    
    def test_skills_search(self):
        """Test skills-based search."""
        from .services import JobSearchService
        
        search_params = {'skills': ['React']}
        result = JobSearchService.search_jobs(search_params)
        
        self.assertEqual(result['total_count'], 1)
        self.assertIn(self.job2, result['queryset'])


class JobRecommendationServiceTest(TestCase):
    """Test cases for JobRecommendationService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='recommendation_test@example.com',
            first_name='Test',
            last_name='User',
            password='testpass123'
        )
        
        # Create user profile
        from profiles.models import Profile
        self.profile, created = Profile.objects.get_or_create(
            user=self.user,
            defaults={
                'experience_level': 'mid',
                'industry': 'Technology',
                'skills': ['Python', 'Django', 'JavaScript']
            }
        )
        
        self.company = Company.objects.create(
            name='Tech Company',
            description='A technology company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://techcompany.com',
        )
        
        self.job = Job.objects.create(
            title='Python Developer',
            company=self.company,
            description='We need a Python developer with Django experience',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            skills_required=['Python', 'Django'],
            status='published'
        )
    
    def test_fallback_recommendations(self):
        """Test fallback recommendations when AI is not available."""
        from .services import JobRecommendationService
        
        service = JobRecommendationService()
        recommendations = service._get_fallback_recommendations(5)
        
        self.assertIsInstance(recommendations, list)
        self.assertLessEqual(len(recommendations), 5)
    
    def test_fallback_score_calculation(self):
        """Test fallback score calculation."""
        from .services import JobRecommendationService
        
        service = JobRecommendationService()
        user_context = {
            'skills': ['Python', 'Django'],
            'experience_level': 'mid',
            'industry': 'Technology',
            'location': 'San Francisco'
        }
        
        score = service._calculate_fallback_score(user_context, self.job)
        
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
        self.assertGreater(score, 0.5)  # Should be a good match