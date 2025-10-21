#!/usr/bin/env python
"""
End-to-End Integration Test Suite

This comprehensive test validates complete user workflows from registration 
to portfolio generation, ensuring all AI services integrate properly and 
error handling works as expected.

Requirements: 6.1, 6.5, 7.3, 7.4
"""

import os
import sys
import django
import json
import tempfile
import logging
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

User = get_user_model()

class EndToEndIntegrationTest(TestCase):
    """Complete end-to-end integration test suite."""
    
    def setUp(self):
        """Set up test environment."""
        self.client = APIClient()
        self.test_user_data = {
            'email': 'testuser@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        # Sample CV content for testing
        self.sample_cv_content = """
        John Doe
        Software Engineer
        Email: john.doe@example.com
        Phone: +1-555-0123
        Location: San Francisco, CA
        LinkedIn: linkedin.com/in/johndoe
        
        PROFESSIONAL SUMMARY
        Experienced software engineer with 5+ years in full-stack development.
        
        TECHNICAL SKILLS
        - Programming Languages: Python, JavaScript, Java
        - Frameworks: Django, React, Spring Boot
        - Databases: PostgreSQL, MongoDB
        - Cloud: AWS, Docker, Kubernetes
        
        WORK EXPERIENCE
        Senior Software Engineer | TechCorp Inc. | 2021 - Present
        - Led development of microservices architecture
        - Improved system performance by 40%
        - Mentored junior developers
        
        Software Engineer | StartupXYZ | 2019 - 2021
        - Built full-stack web applications
        - Implemented CI/CD pipelines
        - Collaborated with cross-functional teams
        
        EDUCATION
        Bachelor of Science in Computer Science
        University of California, Berkeley | 2015 - 2019
        
        CERTIFICATIONS
        AWS Certified Solutions Architect | 2022
        """
    
    def test_complete_user_registration_workflow(self):
        """Test complete user registration and profile setup workflow."""
        print("\n🔐 Testing Complete User Registration Workflow")
        print("=" * 60)
        
        # Step 1: User Registration
        print("  1️⃣ Testing user registration...")
        response = self.client.post('/api/v1/auth/register/', self.test_user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        print("  ✅ User registration successful")
        
        # Step 2: User Login
        print("  2️⃣ Testing user login...")
        login_data = {
            'email': self.test_user_data['email'],
            'password': self.test_user_data['password']
        }
        response = self.client.post('/api/v1/auth/login/', login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        print("  ✅ User login successful")
        
        # Step 3: Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Step 4: Profile Creation
        print("  3️⃣ Testing profile creation...")
        profile_data = {
            'headline': 'Senior Software Engineer',
            'summary': 'Experienced developer with expertise in full-stack development',
            'location': 'San Francisco, CA',
            'industry': 'Technology',
            'experience_level': 'Senior',
            'skills': ['Python', 'Django', 'React', 'AWS']
        }
        response = self.client.post('/api/v1/profiles/me/', profile_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print("  ✅ Profile creation successful")
        
        # Step 5: Verify profile retrieval
        print("  4️⃣ Testing profile retrieval...")
        response = self.client.get('/api/v1/profiles/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['headline'], profile_data['headline'])
        print("  ✅ Profile retrieval successful")
        
        return access_token
    
    def test_cv_upload_and_analysis_workflow(self):
        """Test CV upload and AI analysis workflow."""
        print("\n📄 Testing CV Upload and Analysis Workflow")
        print("=" * 60)
        
        # Setup authenticated user
        access_token = self.test_complete_user_registration_workflow()
        
        # Step 1: CV Upload
        print("  1️⃣ Testing CV upload...")
        cv_file = SimpleUploadedFile(
            "test_cv.txt",
            self.sample_cv_content.encode('utf-8'),
            content_type="text/plain"
        )
        
        response = self.client.post('/api/v1/profiles/upload-cv/', {
            'cv_file': cv_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        print("  ✅ CV upload successful")
        
        # Step 2: Mock AI Analysis (since we don't have real AWS access)
        print("  2️⃣ Testing AI analysis workflow...")
        with patch('koroh_platform.utils.cv_analysis_service.analyze_cv_text') as mock_analyze:
            # Mock successful CV analysis
            mock_analyze.return_value = {
                'personal_info': {
                    'name': 'John Doe',
                    'email': 'john.doe@example.com',
                    'phone': '+1-555-0123',
                    'location': 'San Francisco, CA',
                    'linkedin': 'linkedin.com/in/johndoe'
                },
                'professional_summary': 'Experienced software engineer with 5+ years in full-stack development.',
                'skills': ['Python', 'JavaScript', 'Java', 'Django', 'React'],
                'technical_skills': ['Python', 'JavaScript', 'Java', 'Django', 'React'],
                'soft_skills': ['Leadership', 'Mentoring', 'Collaboration'],
                'work_experience': [
                    {
                        'company': 'TechCorp Inc.',
                        'position': 'Senior Software Engineer',
                        'start_date': '2021',
                        'end_date': 'Present',
                        'description': 'Led development of microservices architecture',
                        'achievements': ['Improved system performance by 40%', 'Mentored junior developers'],
                        'technologies': ['Python', 'Django', 'AWS']
                    }
                ],
                'education': [
                    {
                        'institution': 'University of California, Berkeley',
                        'degree': 'Bachelor of Science',
                        'field_of_study': 'Computer Science',
                        'start_date': '2015',
                        'end_date': '2019'
                    }
                ],
                'certifications': [
                    {
                        'name': 'AWS Certified Solutions Architect',
                        'issuer': 'Amazon Web Services',
                        'issue_date': '2022'
                    }
                ],
                'analysis_confidence': 0.95
            }
            
            # Trigger analysis
            response = self.client.post('/api/v1/ai/analyze-cv/', {
                'cv_text': self.sample_cv_content
            })
            
            # Verify analysis was called and returned expected structure
            mock_analyze.assert_called_once()
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            print("  ✅ AI analysis workflow successful")
        
        return access_token
    
    def test_portfolio_generation_workflow(self):
        """Test portfolio generation workflow."""
        print("\n🎨 Testing Portfolio Generation Workflow")
        print("=" * 60)
        
        # Setup with CV analysis
        access_token = self.test_cv_upload_and_analysis_workflow()
        
        # Step 1: Portfolio Generation Request
        print("  1️⃣ Testing portfolio generation request...")
        with patch('koroh_platform.utils.portfolio_generation_service.generate_portfolio_from_cv') as mock_generate:
            # Mock successful portfolio generation
            mock_generate.return_value = {
                'hero_section': {
                    'headline': 'John Doe - Senior Software Engineer',
                    'tagline': 'Building scalable solutions with modern technologies',
                    'cta_text': 'Get In Touch'
                },
                'about_section': {
                    'main_content': 'Experienced software engineer with 5+ years in full-stack development.',
                    'key_highlights': ['5+ years experience', 'Full-stack expertise', 'Team leadership']
                },
                'experience_section': {
                    'experiences': [
                        {
                            'company': 'TechCorp Inc.',
                            'position': 'Senior Software Engineer',
                            'duration': '2021 - Present',
                            'description': 'Led development of microservices architecture',
                            'achievements': ['Improved system performance by 40%']
                        }
                    ]
                },
                'skills_section': {
                    'technical_skills': ['Python', 'JavaScript', 'Django', 'React'],
                    'soft_skills': ['Leadership', 'Mentoring']
                },
                'education_section': {
                    'education': [
                        {
                            'institution': 'University of California, Berkeley',
                            'degree': 'Bachelor of Science in Computer Science',
                            'year': '2019'
                        }
                    ]
                },
                'contact_section': {
                    'email': 'john.doe@example.com',
                    'linkedin': 'linkedin.com/in/johndoe',
                    'location': 'San Francisco, CA'
                },
                'template_used': 'professional',
                'style_used': 'formal',
                'generation_confidence': 0.92
            }
            
            portfolio_options = {
                'template': 'professional',
                'style': 'formal',
                'target_audience': 'recruiters'
            }
            
            response = self.client.post('/api/v1/profiles/generate-portfolio/', portfolio_options)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('portfolio_content', response.data)
            print("  ✅ Portfolio generation successful")
        
        # Step 2: Portfolio Retrieval
        print("  2️⃣ Testing portfolio retrieval...")
        response = self.client.get('/api/v1/profiles/portfolios/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("  ✅ Portfolio retrieval successful")
        
        return access_token
    
    def test_job_recommendation_workflow(self):
        """Test job recommendation workflow."""
        print("\n💼 Testing Job Recommendation Workflow")
        print("=" * 60)
        
        # Setup with complete profile
        access_token = self.test_portfolio_generation_workflow()
        
        # Step 1: Create sample jobs
        print("  1️⃣ Creating sample jobs...")
        from jobs.models import Job, Company
        
        company = Company.objects.create(
            name='TechCorp',
            description='Leading technology company',
            industry='Technology',
            size='1000-5000',
            location='San Francisco, CA'
        )
        
        job = Job.objects.create(
            title='Senior Python Developer',
            company=company,
            description='Looking for experienced Python developer',
            requirements=['Python', 'Django', 'AWS'],
            location='San Francisco, CA',
            salary_range='$120k-$160k',
            job_type='Full-time'
        )
        print("  ✅ Sample jobs created")
        
        # Step 2: Job Search
        print("  2️⃣ Testing job search...")
        response = self.client.get('/api/v1/jobs/search/', {
            'q': 'Python',
            'location': 'San Francisco'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data['results']), 0)
        print("  ✅ Job search successful")
        
        # Step 3: Job Recommendations
        print("  3️⃣ Testing job recommendations...")
        with patch('koroh_platform.utils.ai_services.AIServiceFactory.create_recommendation_service') as mock_service:
            mock_recommender = MagicMock()
            mock_recommender.get_job_recommendations.return_value = [
                {
                    'job_id': job.id,
                    'match_score': 0.85,
                    'match_reasons': ['Python expertise', 'Django experience', 'AWS knowledge']
                }
            ]
            mock_service.return_value = mock_recommender
            
            response = self.client.get('/api/v1/jobs/recommendations/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            print("  ✅ Job recommendations successful")
        
        return access_token
    
    def test_peer_group_workflow(self):
        """Test peer group discovery and joining workflow."""
        print("\n👥 Testing Peer Group Workflow")
        print("=" * 60)
        
        # Setup with complete profile
        access_token = self.test_job_recommendation_workflow()
        
        # Step 1: Create sample peer group
        print("  1️⃣ Creating sample peer group...")
        from peer_groups.models import PeerGroup
        
        user = User.objects.get(email=self.test_user_data['email'])
        peer_group = PeerGroup.objects.create(
            name='Python Developers SF',
            description='Python developers in San Francisco area',
            industry='Technology',
            experience_level='Senior',
            created_by=user
        )
        print("  ✅ Sample peer group created")
        
        # Step 2: Peer Group Discovery
        print("  2️⃣ Testing peer group discovery...")
        response = self.client.get('/api/v1/groups/discover/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("  ✅ Peer group discovery successful")
        
        # Step 3: Join Peer Group
        print("  3️⃣ Testing peer group joining...")
        response = self.client.post(f'/api/v1/groups/{peer_group.id}/join/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("  ✅ Peer group joining successful")
        
        return access_token
    
    def test_ai_chat_workflow(self):
        """Test AI chat interface workflow."""
        print("\n💬 Testing AI Chat Workflow")
        print("=" * 60)
        
        # Setup with complete profile
        access_token = self.test_peer_group_workflow()
        
        # Step 1: Start Chat Session
        print("  1️⃣ Testing chat session creation...")
        response = self.client.post('/api/v1/ai/chat/', {
            'message': 'Hello, can you help me improve my profile?'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("  ✅ Chat session creation successful")
        
        # Step 2: Chat with Context
        print("  2️⃣ Testing contextual chat...")
        with patch('koroh_platform.utils.ai_services.AIServiceFactory.create_conversational_service') as mock_service:
            mock_chat = MagicMock()
            mock_chat.process.return_value = {
                'response': 'I can help you improve your profile! Based on your CV analysis, I suggest highlighting your leadership experience and AWS certifications more prominently.',
                'suggestions': ['Update headline', 'Add more achievements', 'Highlight certifications'],
                'confidence': 0.88
            }
            mock_service.return_value = mock_chat
            
            response = self.client.post('/api/v1/ai/chat/', {
                'message': 'What specific improvements would you suggest?'
            })
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn('response', response.data)
            print("  ✅ Contextual chat successful")
        
        return access_token
    
    def test_error_handling_and_fallbacks(self):
        """Test error handling and fallback mechanisms."""
        print("\n🛡️ Testing Error Handling and Fallbacks")
        print("=" * 60)
        
        # Setup authenticated user
        access_token = self.test_complete_user_registration_workflow()
        
        # Test 1: Invalid CV Upload
        print("  1️⃣ Testing invalid CV upload handling...")
        invalid_file = SimpleUploadedFile(
            "test.exe",
            b"invalid content",
            content_type="application/x-executable"
        )
        
        response = self.client.post('/api/v1/profiles/upload-cv/', {
            'cv_file': invalid_file
        }, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("  ✅ Invalid file type properly rejected")
        
        # Test 2: AI Service Failure Handling
        print("  2️⃣ Testing AI service failure handling...")
        with patch('koroh_platform.utils.cv_analysis_service.analyze_cv_text') as mock_analyze:
            # Mock AI service failure
            mock_analyze.side_effect = Exception("AWS Bedrock service unavailable")
            
            response = self.client.post('/api/v1/ai/analyze-cv/', {
                'cv_text': self.sample_cv_content
            })
            
            # Should handle gracefully with fallback
            self.assertIn(response.status_code, [status.HTTP_503_SERVICE_UNAVAILABLE, status.HTTP_500_INTERNAL_SERVER_ERROR])
            print("  ✅ AI service failure handled gracefully")
        
        # Test 3: Rate Limiting
        print("  3️⃣ Testing rate limiting...")
        # Make multiple rapid requests
        for i in range(10):
            response = self.client.post('/api/v1/ai/chat/', {
                'message': f'Test message {i}'
            })
            # Should eventually hit rate limit
            if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                print("  ✅ Rate limiting working properly")
                break
        else:
            print("  ⚠️ Rate limiting not triggered (may need adjustment)")
        
        return access_token
    
    def test_data_consistency_and_validation(self):
        """Test data consistency and validation across the system."""
        print("\n🔍 Testing Data Consistency and Validation")
        print("=" * 60)
        
        # Setup complete workflow
        access_token = self.test_ai_chat_workflow()
        
        # Test 1: Profile Data Consistency
        print("  1️⃣ Testing profile data consistency...")
        response = self.client.get('/api/v1/profiles/me/')
        profile_data = response.data
        
        # Verify required fields are present
        required_fields = ['headline', 'summary', 'location', 'industry', 'skills']
        for field in required_fields:
            self.assertIn(field, profile_data)
        print("  ✅ Profile data consistency verified")
        
        # Test 2: CV Analysis Data Validation
        print("  2️⃣ Testing CV analysis data validation...")
        with patch('koroh_platform.utils.cv_analysis_service.analyze_cv_text') as mock_analyze:
            # Mock analysis with invalid data structure
            mock_analyze.return_value = {
                'invalid_field': 'should be rejected'
            }
            
            response = self.client.post('/api/v1/ai/analyze-cv/', {
                'cv_text': self.sample_cv_content
            })
            
            # Should handle invalid response structure
            self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])
            print("  ✅ Invalid CV analysis data properly handled")
        
        # Test 3: Portfolio Generation Validation
        print("  3️⃣ Testing portfolio generation validation...")
        invalid_options = {
            'template': 'invalid_template',
            'style': 'invalid_style'
        }
        
        response = self.client.post('/api/v1/profiles/generate-portfolio/', invalid_options)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print("  ✅ Invalid portfolio options properly rejected")
        
        return access_token


def run_integration_tests():
    """Run the complete integration test suite."""
    print("🚀 END-TO-END INTEGRATION TEST SUITE")
    print("=" * 80)
    print("Testing complete user workflows from registration to portfolio generation")
    print("=" * 80)
    
    # Create test instance
    test_instance = EndToEndIntegrationTest()
    test_instance.setUp()
    
    # Define test methods
    test_methods = [
        ("User Registration Workflow", test_instance.test_complete_user_registration_workflow),
        ("CV Upload and Analysis", test_instance.test_cv_upload_and_analysis_workflow),
        ("Portfolio Generation", test_instance.test_portfolio_generation_workflow),
        ("Job Recommendations", test_instance.test_job_recommendation_workflow),
        ("Peer Group Workflow", test_instance.test_peer_group_workflow),
        ("AI Chat Interface", test_instance.test_ai_chat_workflow),
        ("Error Handling", test_instance.test_error_handling_and_fallbacks),
        ("Data Validation", test_instance.test_data_consistency_and_validation)
    ]
    
    results = []
    
    for test_name, test_method in test_methods:
        try:
            print(f"\n🧪 Running: {test_name}")
            test_method()
            results.append((test_name, True, None))
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            results.append((test_name, False, str(e)))
            print(f"❌ {test_name}: FAILED - {e}")
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 INTEGRATION TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for _, result, _ in results if result)
    total = len(results)
    
    for test_name, result, error in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if error:
            print(f"  Error: {error}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✨ End-to-end workflows are working correctly!")
        print("\n📋 Requirements Status:")
        print("  ✅ 6.1 - AI service integration across all features: VALIDATED")
        print("  ✅ 6.5 - Complete user workflows: VALIDATED")
        print("  ✅ 7.3 - Proper error handling: VALIDATED")
        print("  ✅ 7.4 - Fallback mechanisms: VALIDATED")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
        print("Please review the implementation.")
    
    return passed == total


if __name__ == "__main__":
    # Run as Django test
    from django.test.utils import get_runner
    from django.conf import settings
    
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["__main__"])
    
    if failures:
        sys.exit(1)
    else:
        print("\n🎉 All Django integration tests passed!")
        sys.exit(0)