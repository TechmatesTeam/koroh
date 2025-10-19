"""
Tests for profiles app.

This module contains tests for Profile model, API endpoints,
CV upload functionality, and related services.
"""

import os
import tempfile
from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Profile
from .services import CVProcessingService, CVStorageService
from .utils import sanitize_filename, is_safe_filename, get_file_info

User = get_user_model()


class ProfileModelTest(TestCase):
    """Test cases for Profile model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    def test_profile_creation(self):
        """Test profile is created automatically for new user."""
        # Profile should be created automatically via signals
        self.assertTrue(hasattr(self.user, 'profile'))
        self.assertIsInstance(self.user.profile, Profile)
    
    def test_profile_str_representation(self):
        """Test profile string representation."""
        profile = self.user.profile
        expected = f"{self.user.get_full_name()}'s Profile"
        self.assertEqual(str(profile), expected)
    
    def test_profile_is_complete(self):
        """Test profile completion check."""
        profile = self.user.profile
        
        # Initially incomplete
        self.assertFalse(profile.is_complete)
        
        # Fill required fields
        profile.headline = "Software Engineer"
        profile.summary = "Experienced developer"
        profile.location = "San Francisco, CA"
        profile.industry = "Technology"
        profile.experience_level = "senior"
        profile.save()
        
        # Now should be complete
        self.assertTrue(profile.is_complete)
    
    def test_skills_management(self):
        """Test skills add/remove functionality."""
        profile = self.user.profile
        
        # Add skills
        profile.add_skill("Python")
        profile.add_skill("Django")
        
        self.assertIn("Python", profile.skills)
        self.assertIn("Django", profile.skills)
        
        # Remove skill
        profile.remove_skill("Python")
        self.assertNotIn("Python", profile.skills)
        self.assertIn("Django", profile.skills)
    
    def test_cv_properties(self):
        """Test CV-related properties."""
        profile = self.user.profile
        
        # Initially no CV
        self.assertFalse(profile.has_cv)
        self.assertIsNone(profile.get_cv_filename())
        
        # Add CV file
        cv_content = b"This is a test CV content"
        cv_file = SimpleUploadedFile("test_cv.pdf", cv_content, content_type="application/pdf")
        profile.cv_file = cv_file
        profile.save()
        
        # Now has CV
        self.assertTrue(profile.has_cv)
        self.assertEqual(profile.get_cv_filename(), "test_cv.pdf")


class ProfileAPITest(APITestCase):
    """Test cases for Profile API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # Set authentication header
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_get_profile(self):
        """Test retrieving user profile."""
        url = reverse('profiles:detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['email'], self.user.email)
    
    def test_update_profile(self):
        """Test updating user profile."""
        url = reverse('profiles:update')
        data = {
            'headline': 'Senior Software Engineer',
            'summary': 'Experienced Python developer',
            'location': 'San Francisco, CA',
            'industry': 'Technology',
            'experience_level': 'senior',
            'skills': ['Python', 'Django', 'React']
        }
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['headline'], data['headline'])
        self.assertEqual(response.data['skills'], data['skills'])
    
    def test_cv_upload(self):
        """Test CV file upload."""
        url = reverse('profiles:upload-cv')
        
        # Create test PDF content
        cv_content = b"%PDF-1.4\nThis is a test PDF content"
        cv_file = SimpleUploadedFile(
            "test_cv.pdf",
            cv_content,
            content_type="application/pdf"
        )
        
        data = {'cv_file': cv_file}
        response = self.client.patch(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_cv'])
        self.assertIn('processing_result', response.data)
    
    def test_cv_upload_invalid_file(self):
        """Test CV upload with invalid file."""
        url = reverse('profiles:upload-cv')
        
        # Create invalid file (too large)
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        cv_file = SimpleUploadedFile(
            "large_cv.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        data = {'cv_file': cv_file}
        response = self.client.patch(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_add_skill(self):
        """Test adding a skill."""
        url = reverse('profiles:add-skill')
        data = {'skill': 'Python'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Python', response.data['skills'])
    
    def test_remove_skill(self):
        """Test removing a skill."""
        # First add a skill
        profile = self.user.profile
        profile.add_skill('Python')
        
        url = reverse('profiles:remove-skill')
        data = {'skill': 'Python'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('Python', response.data['skills'])
    
    def test_profile_stats(self):
        """Test profile statistics endpoint."""
        url = reverse('profiles:stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('completion_percentage', response.data)
        self.assertIn('recommendations', response.data)
        self.assertIn('is_complete', response.data)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access profile endpoints."""
        self.client.credentials()  # Remove authentication
        
        url = reverse('profiles:detail')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CVProcessingServiceTest(TestCase):
    """Test cases for CV processing service."""
    
    def setUp(self):
        """Set up test data."""
        self.cv_processor = CVProcessingService()
    
    def test_validate_pdf_file(self):
        """Test PDF file validation."""
        pdf_content = b"%PDF-1.4\nThis is a test PDF content"
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        result = self.cv_processor.validate_cv_file(pdf_file)
        
        self.assertTrue(result['is_valid'])
        self.assertEqual(len(result['errors']), 0)
        self.assertEqual(result['metadata']['file_extension'], 'pdf')
    
    def test_validate_invalid_extension(self):
        """Test validation with invalid file extension."""
        txt_content = b"This is a text file"
        txt_file = SimpleUploadedFile(
            "test.txt",
            txt_content,
            content_type="text/plain"
        )
        
        result = self.cv_processor.validate_cv_file(txt_file)
        
        self.assertFalse(result['is_valid'])
        self.assertGreater(len(result['errors']), 0)
    
    def test_validate_large_file(self):
        """Test validation with file too large."""
        large_content = b"x" * (11 * 1024 * 1024)  # 11MB
        large_file = SimpleUploadedFile(
            "large.pdf",
            large_content,
            content_type="application/pdf"
        )
        
        result = self.cv_processor.validate_cv_file(large_file)
        
        self.assertFalse(result['is_valid'])
        self.assertTrue(any('size' in error.lower() for error in result['errors']))
    
    def test_extract_metadata(self):
        """Test metadata extraction."""
        pdf_content = b"%PDF-1.4\nThis is a test PDF content"
        pdf_file = SimpleUploadedFile(
            "test.pdf",
            pdf_content,
            content_type="application/pdf"
        )
        
        metadata = self.cv_processor.extract_cv_metadata(pdf_file)
        
        self.assertIn('extraction_timestamp', metadata)
        self.assertIn('file_info', metadata)
        self.assertIn('content_analysis', metadata)
        self.assertEqual(metadata['file_info']['file_extension'], 'pdf')


class CVStorageServiceTest(TestCase):
    """Test cases for CV storage service."""
    
    def setUp(self):
        """Set up test data."""
        self.cv_storage = CVStorageService()
    
    def test_get_storage_path(self):
        """Test storage path generation."""
        user_id = 123
        filename = "test_cv.pdf"
        
        path = self.cv_storage.get_storage_path(user_id, filename)
        
        self.assertIn(str(user_id), path)
        self.assertIn('cvs/', path)
        self.assertTrue(path.endswith('test_cv.pdf'))
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        unsafe_filename = "../../../etc/passwd"
        safe_filename = self.cv_storage._sanitize_filename(unsafe_filename)
        
        self.assertNotIn('..', safe_filename)
        self.assertNotIn('/', safe_filename)


class UtilsTest(TestCase):
    """Test cases for utility functions."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Test normal filename
        self.assertEqual(sanitize_filename("test.pdf"), "test.pdf")
        
        # Test filename with unsafe characters
        unsafe = "../test file!@#.pdf"
        safe = sanitize_filename(unsafe)
        self.assertNotIn('..', safe)
        self.assertNotIn('!', safe)
        self.assertNotIn('@', safe)
        self.assertNotIn('#', safe)
    
    def test_is_safe_filename(self):
        """Test filename safety check."""
        # Safe filenames
        self.assertTrue(is_safe_filename("test.pdf"))
        self.assertTrue(is_safe_filename("my_cv_2024.docx"))
        
        # Unsafe filenames
        self.assertFalse(is_safe_filename("../test.pdf"))
        self.assertFalse(is_safe_filename(".hidden"))
        self.assertFalse(is_safe_filename("CON.pdf"))
        self.assertFalse(is_safe_filename(""))
    
    def test_get_file_info(self):
        """Test file information extraction."""
        test_content = b"Test file content"
        test_file = SimpleUploadedFile(
            "test.pdf",
            test_content,
            content_type="application/pdf"
        )
        
        info = get_file_info(test_file)
        
        self.assertEqual(info['name'], 'test.pdf')
        self.assertEqual(info['size'], len(test_content))
        self.assertIn('hash_sha256', info)
        self.assertIn('hash_md5', info)
        self.assertTrue(info['is_safe_filename'])