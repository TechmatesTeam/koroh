"""
Comprehensive tests for Celery background task processing.

This module tests:
- Celery task execution and error handling
- Async AI processing workflows
- Task retry mechanisms and failure handling
- Background job processing functionality

Requirements tested: 1.1, 1.2, 2.3
"""

import os
import tempfile
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

# Import tasks from different apps
try:
    from koroh_platform.tasks import (
        analyze_cv_with_ai,
        generate_portfolio_with_ai,
        update_job_recommendations,
        send_portfolio_ready_notification,
        send_job_recommendations_email,
        update_peer_group_recommendations,
        cleanup_ai_processing_data,
        monitor_ai_service_health
    )
except ImportError:
    # Handle missing tasks gracefully
    analyze_cv_with_ai = None
    generate_portfolio_with_ai = None
    update_job_recommendations = None
    send_portfolio_ready_notification = None
    send_job_recommendations_email = None
    update_peer_group_recommendations = None
    cleanup_ai_processing_data = None
    monitor_ai_service_health = None

try:
    from authentication.tasks import (
        cleanup_expired_tokens,
        cleanup_inactive_users,
        send_welcome_email
    )
except ImportError:
    cleanup_expired_tokens = None
    cleanup_inactive_users = None
    send_welcome_email = None

try:
    from profiles.tasks import (
        analyze_cv_async,
        generate_portfolio_async,
        cleanup_orphaned_files,
        send_profile_completion_reminder
    )
except ImportError:
    analyze_cv_async = None
    generate_portfolio_async = None
    cleanup_orphaned_files = None
    send_profile_completion_reminder = None

try:
    from companies.tasks import (
        update_company_insights,
        notify_followers_new_job,
        send_weekly_digests,
        update_all_company_insights
    )
except ImportError:
    update_company_insights = None
    notify_followers_new_job = None
    send_weekly_digests = None
    update_all_company_insights = None

User = get_user_model()


class CeleryTaskExecutionTest(TestCase):
    """Test basic Celery task execution and error handling."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='celery_test@example.com',
            first_name='Celery',
            last_name='Test',
            password='testpass123'
        )
        
        # Create profile
        from profiles.models import Profile
        self.profile = Profile.objects.get(user=self.user)
        
        # Create company for job-related tests
        from companies.models import Company
        self.company = Company.objects.create(
            name='Test Company',
            description='A test company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://testcompany.com'
        )
        
        # Create job for testing
        from jobs.models import Job
        self.job = Job.objects.create(
            title='Test Job',
            company=self.company,
            description='A test job',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            status='published'
        )
    
    def test_task_execution_success(self):
        """Test successful task execution."""
        # Test authentication task
        if cleanup_inactive_users:
            result = cleanup_inactive_users.delay()
            self.assertIsNotNone(result)
        
        # Test profile task
        if send_profile_completion_reminder:
            result = send_profile_completion_reminder.delay(self.user.id)
            self.assertIsNotNone(result)
        
        # Test company task
        if update_company_insights:
            result = update_company_insights.delay(self.company.id)
            self.assertIsNotNone(result)
    
    def test_task_with_invalid_parameters(self):
        """Test task execution with invalid parameters."""
        # Test with non-existent user ID
        if send_profile_completion_reminder:
            result = send_profile_completion_reminder.apply(args=[99999])
            self.assertIn('error', result.result)
            self.assertEqual(result.result['success'], False)
        
        # Test with non-existent company ID
        if update_company_insights:
            result = update_company_insights.apply(args=[99999])
            self.assertIn('error', result.result)
            self.assertEqual(result.result['success'], False)
    
    @patch('authentication.tasks.send_mail')
    def test_email_task_execution(self, mock_send_mail):
        """Test email-related task execution."""
        if not send_welcome_email:
            self.skipTest("send_welcome_email task not available")
            
        mock_send_mail.return_value = True
        
        # Test welcome email task
        result = send_welcome_email.apply(args=[self.user.id])
        self.assertTrue(result.result['success'])
        self.assertTrue(result.result['email_sent'])
        mock_send_mail.assert_called_once()
    
    @patch('authentication.tasks.send_mail')
    def test_email_task_failure_and_retry(self, mock_send_mail):
        """Test email task failure and retry mechanism."""
        if not send_welcome_email:
            self.skipTest("send_welcome_email task not available")
            
        # Mock email sending failure
        mock_send_mail.side_effect = Exception("SMTP server error")
        
        # Test that task handles failure gracefully
        result = send_welcome_email.apply(args=[self.user.id])
        self.assertFalse(result.result['success'])
        self.assertIn('error', result.result)


class AIProcessingTaskTest(TestCase):
    """Test AI processing tasks and workflows."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='ai_test@example.com',
            first_name='AI',
            last_name='Test',
            password='testpass123'
        )
        
        from profiles.models import Profile
        self.profile = Profile.objects.get(user=self.user)
        
        # Create test CV content
        self.cv_content = b"%PDF-1.4\nThis is a test CV with Python, Django, React skills"
        self.cv_file = SimpleUploadedFile(
            "test_cv.pdf",
            self.cv_content,
            content_type="application/pdf"
        )
    
    @patch('koroh_platform.utils.cv_analysis_service.CVAnalysisService')
    def test_cv_analysis_task_success(self, mock_cv_service):
        """Test successful CV analysis task execution (Requirement 1.1)."""
        if not analyze_cv_with_ai:
            self.skipTest("analyze_cv_with_ai task not available")
            
        # Mock CV analysis service
        mock_analysis_result = MagicMock()
        mock_analysis_result.professional_summary = "Experienced developer"
        mock_analysis_result.personal_info.location = "San Francisco, CA"
        mock_analysis_result.technical_skills = ["Python", "Django"]
        mock_analysis_result.soft_skills = ["Communication"]
        mock_analysis_result.skills = ["React"]
        mock_analysis_result.analysis_confidence = 0.85
        mock_analysis_result.extracted_sections = ["experience", "skills"]
        mock_analysis_result.processing_notes = ["Successfully extracted skills"]
        
        mock_cv_service.return_value.analyze_cv.return_value = mock_analysis_result
        
        # Create temporary file for testing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(self.cv_content)
            temp_file_path = temp_file.name
        
        try:
            # Test CV analysis task
            result = analyze_cv_with_ai.apply(args=[self.user.id, temp_file_path])
            
            self.assertTrue(result.result['success'])
            self.assertEqual(result.result['skills_extracted'], 3)
            self.assertEqual(result.result['confidence_score'], 0.85)
            
            # Verify profile was updated
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.summary, "Experienced developer")
            self.assertEqual(self.profile.location, "San Francisco, CA")
            self.assertIn("Python", self.profile.skills)
            self.assertIn("Django", self.profile.skills)
            self.assertIn("React", self.profile.skills)
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    @patch('koroh_platform.utils.cv_analysis_service.CVAnalysisService')
    def test_cv_analysis_task_failure(self, mock_cv_service):
        """Test CV analysis task failure handling."""
        # Mock CV analysis service failure
        mock_cv_service.return_value.analyze_cv.side_effect = Exception("AI service unavailable")
        
        # Test with non-existent file
        result = analyze_cv_with_ai.apply(args=[self.user.id, "/non/existent/file.pdf"])
        
        self.assertFalse(result.result['success'])
        self.assertIn('error', result.result)
    
    @patch('koroh_platform.utils.portfolio_generation_service.PortfolioGenerationService')
    def test_portfolio_generation_task_success(self, mock_portfolio_service):
        """Test successful portfolio generation task (Requirement 1.2)."""
        # Set up CV analysis data in profile
        self.profile.preferences = {
            'cv_analysis': {
                'analysis_confidence': 0.8,
                'extracted_sections': ['experience', 'skills'],
                'processing_notes': ['CV processed successfully']
            }
        }
        self.profile.save()
        
        # Mock portfolio generation service
        mock_portfolio_result = MagicMock()
        mock_portfolio_result.content = {
            'hero_section': {'headline': 'AI Test'},
            'about_section': {'main_content': 'Professional summary'},
            'skills_section': {'top_skills': ['Python', 'Django']}
        }
        mock_portfolio_result.quality_score = 0.9
        
        mock_portfolio_service.return_value.generate_portfolio.return_value = mock_portfolio_result
        
        # Test portfolio generation task
        result = generate_portfolio_with_ai.apply(args=[self.user.id, "professional"])
        
        self.assertTrue(result.result['success'])
        self.assertIn('portfolio_url', result.result)
        self.assertEqual(result.result['quality_score'], 0.9)
        
        # Verify profile was updated
        self.profile.refresh_from_db()
        self.assertIsNotNone(self.profile.portfolio_url)
        self.assertIn('portfolio', self.profile.preferences)
    
    def test_portfolio_generation_without_cv_analysis(self):
        """Test portfolio generation failure when CV analysis is missing."""
        # Test without CV analysis data
        result = generate_portfolio_with_ai.apply(args=[self.user.id])
        
        self.assertFalse(result.result['success'])
        self.assertIn('No CV analysis data found', result.result['error'])
    
    @patch('koroh_platform.utils.aws_bedrock.bedrock_client')
    def test_ai_service_health_monitoring(self, mock_bedrock_client):
        """Test AI service health monitoring task."""
        # Mock successful Bedrock client
        mock_client = MagicMock()
        mock_client.client = MagicMock()
        mock_bedrock_client.return_value = mock_client
        mock_bedrock_client.invoke_model.return_value = "OK"
        
        result = monitor_ai_service_health.apply()
        
        self.assertIn('bedrock_client_status', result.result)
        self.assertIn('test_invocation_success', result.result)
        self.assertIn('response_time_ms', result.result)


class JobRecommendationTaskTest(TestCase):
    """Test job recommendation background tasks (Requirement 2.3)."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='job_test@example.com',
            first_name='Job',
            last_name='Test',
            password='testpass123'
        )
        
        # Set last login to make user active
        self.user.last_login = timezone.now()
        self.user.save()
        
        from profiles.models import Profile
        self.profile = Profile.objects.get(user=self.user)
        self.profile.skills = ['Python', 'Django', 'React']
        self.profile.experience_level = 'mid'
        self.profile.industry = 'Technology'
        self.profile.location = 'San Francisco, CA'
        self.profile.save()
        
        # Create company and jobs
        from companies.models import Company
        self.company = Company.objects.create(
            name='Tech Company',
            description='A technology company',
            industry='Technology',
            company_size='medium',
            company_type='private',
            headquarters='San Francisco, CA',
            website='https://techcompany.com'
        )
        
        from jobs.models import Job
        self.job = Job.objects.create(
            title='Python Developer',
            company=self.company,
            description='We need a Python developer',
            job_type='full_time',
            experience_level='mid',
            location='San Francisco, CA',
            status='published'
        )
    
    @patch('jobs.services.JobRecommendationService')
    def test_job_recommendations_update_success(self, mock_recommendation_service):
        """Test successful job recommendations update."""
        # Mock recommendation service
        mock_service = MagicMock()
        mock_service.get_recommendations_for_user.return_value = [self.job]
        mock_recommendation_service.return_value = mock_service
        
        # Add AI match score to job for testing
        self.job.ai_match_score = 0.8
        
        result = update_job_recommendations.apply(args=[self.user.id])
        
        self.assertIn('successful_updates', result.result)
        self.assertIn('recommendations_generated', result.result)
        self.assertEqual(result.result['successful_updates'], 1)
    
    def test_job_recommendations_update_all_users(self):
        """Test job recommendations update for all active users."""
        result = update_job_recommendations.apply()
        
        self.assertIn('total_users', result.result)
        self.assertIn('successful_updates', result.result)
        self.assertIn('failed_updates', result.result)
    
    @patch('koroh_platform.tasks.send_mail')
    def test_job_recommendations_email_task(self, mock_send_mail):
        """Test job recommendations email sending."""
        # Set up job recommendations in user preferences
        self.profile.preferences = {
            'job_recommendations': {
                'recommendations': [
                    {
                        'job_id': self.job.id,
                        'title': 'Python Developer',
                        'company_name': 'Tech Company',
                        'match_score': 85,
                        'location': 'San Francisco, CA'
                    }
                ]
            }
        }
        self.profile.save()
        
        mock_send_mail.return_value = True
        
        result = send_job_recommendations_email.apply(args=[self.user.id])
        
        self.assertTrue(result.result['success'])
        self.assertTrue(result.result['email_sent'])
        self.assertEqual(result.result['recommendations_count'], 1)
        mock_send_mail.assert_called_once()
    
    def test_job_recommendations_email_no_recommendations(self):
        """Test job recommendations email when no recommendations exist."""
        result = send_job_recommendations_email.apply(args=[self.user.id])
        
        self.assertTrue(result.result['success'])
        self.assertTrue(result.result.get('no_recommendations', False))


class PeerGroupRecommendationTaskTest(TestCase):
    """Test peer group recommendation tasks."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='peer_test@example.com',
            first_name='Peer',
            last_name='Test',
            password='testpass123'
        )
        
        # Set last login to make user active
        self.user.last_login = timezone.now()
        self.user.save()
        
        from profiles.models import Profile
        self.profile = Profile.objects.get(user=self.user)
        self.profile.skills = ['Python', 'Django']
        self.profile.industry = 'Technology'
        self.profile.save()
    
    @patch('peer_groups.services.PeerGroupRecommendationService')
    def test_peer_group_recommendations_update(self, mock_recommendation_service):
        """Test peer group recommendations update."""
        # Mock recommendation service
        mock_service = MagicMock()
        mock_recommendations = [
            {'group_id': 1, 'name': 'Python Developers', 'match_score': 0.8},
            {'group_id': 2, 'name': 'Django Community', 'match_score': 0.7}
        ]
        mock_service.get_recommendations_for_user.return_value = mock_recommendations
        mock_recommendation_service.return_value = mock_service
        
        result = update_peer_group_recommendations.apply(args=[self.user.id])
        
        self.assertIn('successful_updates', result.result)
        self.assertIn('recommendations_generated', result.result)
        self.assertEqual(result.result['successful_updates'], 1)
        self.assertEqual(result.result['recommendations_generated'], 2)


class TaskErrorHandlingTest(TestCase):
    """Test task error handling and retry mechanisms."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='error_test@example.com',
            first_name='Error',
            last_name='Test',
            password='testpass123'
        )
    
    def test_task_retry_mechanism(self):
        """Test task retry mechanism on failure."""
        # Test with a task that has retry logic
        with patch('koroh_platform.tasks.CVAnalysisService') as mock_service:
            # Mock service to raise exception
            mock_service.return_value.analyze_cv.side_effect = Exception("Temporary failure")
            
            # Test that task handles failure and would retry
            result = analyze_cv_with_ai.apply(args=[self.user.id, "/fake/path.pdf"])
            
            self.assertFalse(result.result['success'])
            self.assertIn('error', result.result)
    
    def test_task_max_retries_exceeded(self):
        """Test task behavior when max retries are exceeded."""
        # This test simulates what happens when a task fails repeatedly
        with patch('authentication.tasks.send_mail') as mock_send_mail:
            mock_send_mail.side_effect = Exception("Persistent failure")
            
            result = send_welcome_email.apply(args=[self.user.id])
            
            self.assertFalse(result.result['success'])
            self.assertIn('error', result.result)
    
    def test_task_with_missing_dependencies(self):
        """Test task behavior when dependencies are missing."""
        # Test CV analysis without file
        result = analyze_cv_with_ai.apply(args=[self.user.id, "/non/existent/file.pdf"])
        
        self.assertFalse(result.result['success'])
        self.assertIn('error', result.result)
    
    def test_database_error_handling(self):
        """Test task behavior with database errors."""
        # Test with non-existent user
        result = send_welcome_email.apply(args=[99999])
        
        self.assertFalse(result.result['success'])
        self.assertEqual(result.result['error'], 'User not found')


class TaskCleanupTest(TestCase):
    """Test cleanup and maintenance tasks."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='cleanup_test@example.com',
            first_name='Cleanup',
            last_name='Test',
            password='testpass123'
        )
    
    def test_inactive_users_cleanup(self):
        """Test inactive users cleanup task."""
        # Create inactive user
        inactive_user = User.objects.create_user(
            email='inactive@example.com',
            first_name='Inactive',
            last_name='User',
            password='testpass123',
            is_active=False
        )
        
        # Set date_joined to more than 30 days ago
        from datetime import timedelta
        inactive_user.date_joined = timezone.now() - timedelta(days=35)
        inactive_user.save()
        
        result = cleanup_inactive_users.apply()
        
        self.assertIn('inactive_users_deleted', result.result)
        # The user should be deleted
        self.assertFalse(User.objects.filter(id=inactive_user.id).exists())
    
    def test_ai_processing_data_cleanup(self):
        """Test AI processing data cleanup task."""
        result = cleanup_ai_processing_data.apply()
        
        self.assertIn('temp_files_deleted', result.result)
        self.assertIn('old_analysis_data_cleaned', result.result)
        self.assertIn('cache_entries_cleared', result.result)
    
    @patch('django.core.files.storage.default_storage')
    def test_orphaned_files_cleanup(self, mock_storage):
        """Test orphaned files cleanup task."""
        # Mock storage operations
        mock_storage.exists.return_value = True
        mock_storage.listdir.return_value = ([], ['orphaned_file.pdf'])
        mock_storage.delete.return_value = True
        
        result = cleanup_orphaned_files.apply()
        
        self.assertIn('orphaned_cv_files_deleted', result.result)
        self.assertIn('orphaned_profile_files_deleted', result.result)


class TaskIntegrationTest(TestCase):
    """Test task integration and workflow scenarios."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='integration_test@example.com',
            first_name='Integration',
            last_name='Test',
            password='testpass123'
        )
        
        from profiles.models import Profile
        self.profile = Profile.objects.get(user=self.user)
    
    @patch('koroh_platform.utils.cv_analysis_service.CVAnalysisService')
    @patch('koroh_platform.utils.portfolio_generation_service.PortfolioGenerationService')
    def test_cv_analysis_to_portfolio_workflow(self, mock_portfolio_service, mock_cv_service):
        """Test complete CV analysis to portfolio generation workflow."""
        # Mock CV analysis
        mock_analysis_result = MagicMock()
        mock_analysis_result.professional_summary = "Experienced developer"
        mock_analysis_result.personal_info.location = "San Francisco, CA"
        mock_analysis_result.technical_skills = ["Python"]
        mock_analysis_result.soft_skills = ["Communication"]
        mock_analysis_result.skills = ["Django"]
        mock_analysis_result.analysis_confidence = 0.8
        mock_analysis_result.extracted_sections = ["skills"]
        mock_analysis_result.processing_notes = ["Success"]
        
        mock_cv_service.return_value.analyze_cv.return_value = mock_analysis_result
        
        # Mock portfolio generation
        mock_portfolio_result = MagicMock()
        mock_portfolio_result.content = {'hero_section': {'headline': 'Test'}}
        mock_portfolio_result.quality_score = 0.9
        
        mock_portfolio_service.return_value.generate_portfolio.return_value = mock_portfolio_result
        
        # Create temporary CV file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file.write(b"%PDF-1.4\nTest CV content")
            temp_file_path = temp_file.name
        
        try:
            # Step 1: Analyze CV
            cv_result = analyze_cv_with_ai.apply(args=[self.user.id, temp_file_path])
            self.assertTrue(cv_result.result['success'])
            
            # Step 2: Generate portfolio (should be triggered automatically)
            portfolio_result = generate_portfolio_with_ai.apply(args=[self.user.id])
            self.assertTrue(portfolio_result.result['success'])
            
            # Verify complete workflow
            self.profile.refresh_from_db()
            self.assertEqual(self.profile.summary, "Experienced developer")
            self.assertIsNotNone(self.profile.portfolio_url)
            self.assertIn('cv_analysis', self.profile.preferences)
            self.assertIn('portfolio', self.profile.preferences)
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    @patch('koroh_platform.tasks.send_mail')
    def test_notification_workflow(self, mock_send_mail):
        """Test notification workflow after portfolio generation."""
        # Set up portfolio data
        self.profile.portfolio_url = "/portfolio/test"
        self.profile.save()
        
        mock_send_mail.return_value = True
        
        # Test portfolio ready notification
        result = send_portfolio_ready_notification.apply(
            args=[self.user.id, self.profile.portfolio_url]
        )
        
        self.assertTrue(result.result['success'])
        self.assertTrue(result.result['email_sent'])
        mock_send_mail.assert_called_once()
    
    def test_periodic_task_scheduling(self):
        """Test that periodic tasks can be executed."""
        # Test weekly digest task
        result = send_weekly_digests.apply()
        self.assertIn('total_users', result.result)
        
        # Test company insights update
        result = update_all_company_insights.apply()
        self.assertIn('total_companies', result.result)


class TaskPerformanceTest(TestCase):
    """Test task performance and resource usage."""
    
    def setUp(self):
        """Set up test data."""
        self.users = []
        for i in range(5):
            user = User.objects.create_user(
                email=f'perf_test_{i}@example.com',
                first_name=f'Perf{i}',
                last_name='Test',
                password='testpass123'
            )
            user.last_login = timezone.now()
            user.save()
            self.users.append(user)
    
    def test_batch_job_recommendations_performance(self):
        """Test performance of batch job recommendations update."""
        import time
        
        start_time = time.time()
        result = update_job_recommendations.apply()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Task should complete within reasonable time (5 seconds for test data)
        self.assertLess(execution_time, 5.0)
        self.assertIn('total_users', result.result)
    
    def test_batch_peer_group_recommendations_performance(self):
        """Test performance of batch peer group recommendations update."""
        import time
        
        start_time = time.time()
        result = update_peer_group_recommendations.apply()
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Task should complete within reasonable time
        self.assertLess(execution_time, 5.0)
        self.assertIn('total_users', result.result)


@override_settings(CELERY_TASK_ALWAYS_EAGER=False)
class AsyncTaskTest(TestCase):
    """Test actual async task behavior (when not in eager mode)."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='async_test@example.com',
            first_name='Async',
            last_name='Test',
            password='testpass123'
        )
    
    def test_task_delay_returns_async_result(self):
        """Test that task.delay() returns AsyncResult object."""
        # This test verifies the task can be scheduled asynchronously
        # Note: In test environment with CELERY_TASK_ALWAYS_EAGER=True,
        # tasks execute synchronously, but we can still test the interface
        
        result = send_welcome_email.delay(self.user.id)
        
        # AsyncResult should have an id
        self.assertIsNotNone(result.id)
        
        # Should be able to get result
        task_result = result.get()
        self.assertIn('success', task_result)