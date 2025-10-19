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
        # Django may add random characters to filename to avoid conflicts
        self.assertTrue(profile.get_cv_filename().startswith("test_cv"))
        self.assertTrue(profile.get_cv_filename().endswith(".pdf"))


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


class ProfileManagementSecurityTest(APITestCase):
    """
    Comprehensive test cases for profile management security measures.
    
    Tests file format restrictions, security validations, and upload safety
    as required by Requirements 1.1 and 1.3.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='security@example.com',
            password='testpass123',
            first_name='Security',
            last_name='Tester'
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_cv_upload_allowed_formats(self):
        """Test CV upload with all allowed file formats (Requirement 1.1)."""
        url = reverse('profiles:upload-cv')
        
        # Test PDF format
        pdf_content = b"%PDF-1.4\nThis is a test PDF content"
        pdf_file = SimpleUploadedFile("test.pdf", pdf_content, content_type="application/pdf")
        response = self.client.patch(url, {'cv_file': pdf_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test DOC format
        doc_content = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"This is a test DOC content"
        doc_file = SimpleUploadedFile("test.doc", doc_content, content_type="application/msword")
        response = self.client.patch(url, {'cv_file': doc_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test DOCX format
        docx_content = b"PK\x03\x04" + b"This is a test DOCX content"
        docx_file = SimpleUploadedFile(
            "test.docx", 
            docx_content, 
            content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        response = self.client.patch(url, {'cv_file': docx_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test MD format
        md_content = b"# My CV\n\nThis is my markdown CV"
        md_file = SimpleUploadedFile("test.md", md_content, content_type="text/markdown")
        response = self.client.patch(url, {'cv_file': md_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_cv_upload_forbidden_formats(self):
        """Test CV upload rejects forbidden file formats (Requirement 1.1)."""
        url = reverse('profiles:upload-cv')
        
        # Test TXT format (not allowed)
        txt_content = b"This is a text file"
        txt_file = SimpleUploadedFile("test.txt", txt_content, content_type="text/plain")
        response = self.client.patch(url, {'cv_file': txt_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test EXE format (dangerous)
        exe_content = b"MZ\x90\x00" + b"This is a fake exe"
        exe_file = SimpleUploadedFile("malware.exe", exe_content, content_type="application/octet-stream")
        response = self.client.patch(url, {'cv_file': exe_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test JS format (potentially dangerous)
        js_content = b"alert('xss')"
        js_file = SimpleUploadedFile("script.js", js_content, content_type="application/javascript")
        response = self.client.patch(url, {'cv_file': js_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_cv_upload_file_size_limits(self):
        """Test CV upload file size restrictions (Requirement 1.1)."""
        url = reverse('profiles:upload-cv')
        
        # Test file too large (11MB)
        large_content = b"x" * (11 * 1024 * 1024)
        large_file = SimpleUploadedFile("large.pdf", large_content, content_type="application/pdf")
        response = self.client.patch(url, {'cv_file': large_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        # Test empty file
        empty_file = SimpleUploadedFile("empty.pdf", b"", content_type="application/pdf")
        response = self.client.patch(url, {'cv_file': empty_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_cv_upload_filename_security(self):
        """Test CV upload filename security measures (Requirement 1.3)."""
        url = reverse('profiles:upload-cv')
        
        # Test path traversal attempt
        pdf_content = b"%PDF-1.4\nThis is a test PDF content"
        malicious_file = SimpleUploadedFile(
            "../../../etc/passwd.pdf", 
            pdf_content, 
            content_type="application/pdf"
        )
        response = self.client.patch(url, {'cv_file': malicious_file}, format='multipart')
        # Should still process but sanitize filename
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify filename was sanitized
        profile = self.user.profile
        profile.refresh_from_db()
        self.assertNotIn('..', profile.get_cv_filename())
        self.assertNotIn('/', profile.get_cv_filename())
    
    def test_cv_upload_replaces_old_file(self):
        """Test CV upload replaces old file properly (Requirement 1.3)."""
        url = reverse('profiles:upload-cv')
        
        # Upload first CV
        pdf_content1 = b"%PDF-1.4\nFirst CV content"
        pdf_file1 = SimpleUploadedFile("cv1.pdf", pdf_content1, content_type="application/pdf")
        response1 = self.client.patch(url, {'cv_file': pdf_file1}, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Get first CV metadata
        first_metadata = response1.data['cv_metadata']
        
        # Upload second CV
        pdf_content2 = b"%PDF-1.4\nSecond CV content"
        pdf_file2 = SimpleUploadedFile("cv2.pdf", pdf_content2, content_type="application/pdf")
        response2 = self.client.patch(url, {'cv_file': pdf_file2}, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify new CV replaced old one
        second_metadata = response2.data['cv_metadata']
        self.assertNotEqual(first_metadata['file_hash'], second_metadata['file_hash'])
        self.assertTrue(response2.data['has_cv'])
    
    def test_profile_privacy_settings(self):
        """Test profile privacy and visibility settings (Requirement 1.3)."""
        # Test private profile
        profile = self.user.profile
        profile.is_public = False
        profile.show_email = False
        profile.save()
        
        # Try to access private profile as anonymous user
        self.client.credentials()  # Remove authentication
        url = reverse('profiles:public', kwargs={'user_id': self.user.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Make profile public but hide email
        profile.is_public = True
        profile.save()
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(response.data['user']['email'])
    
    def test_skills_validation_security(self):
        """Test skills validation and security measures (Requirement 1.3)."""
        url = reverse('profiles:update')
        
        # Test XSS attempt in skills
        malicious_skills = ['<script>alert("xss")</script>', 'Python', 'Django']
        data = {'skills': malicious_skills}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test too many skills
        too_many_skills = [f'skill_{i}' for i in range(51)]
        data = {'skills': too_many_skills}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test empty skills
        data = {'skills': ['']}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test skill too long
        long_skill = 'x' * 101
        data = {'skills': [long_skill]}
        response = self.client.patch(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileManagementFunctionalTest(APITestCase):
    """
    Comprehensive functional tests for profile management features.
    
    Tests profile creation, updates, and complete workflows
    as required by Requirements 1.1 and 1.3.
    """
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='functional@example.com',
            password='testpass123',
            first_name='Functional',
            last_name='Tester'
        )
        
        # Get JWT token for authentication
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_complete_profile_creation_workflow(self):
        """Test complete profile creation and update workflow (Requirement 1.3)."""
        # Step 1: Get initial empty profile
        url = reverse('profiles:detail')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_complete'])
        self.assertFalse(response.data['has_cv'])
        
        # Step 2: Update profile with basic information
        update_url = reverse('profiles:update')
        profile_data = {
            'headline': 'Senior Software Engineer',
            'summary': 'Experienced Python developer with 5+ years in web development',
            'location': 'San Francisco, CA',
            'industry': 'Technology',
            'experience_level': 'senior',
            'skills': ['Python', 'Django', 'React', 'PostgreSQL']
        }
        response = self.client.patch(update_url, profile_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check profile is complete by getting the full profile
        response = self.client.get(url)
        self.assertTrue(response.data['is_complete'])
        
        # Step 3: Upload CV
        cv_url = reverse('profiles:upload-cv')
        cv_content = b"%PDF-1.4\nThis is a comprehensive CV content"
        cv_file = SimpleUploadedFile("my_cv.pdf", cv_content, content_type="application/pdf")
        response = self.client.patch(cv_url, {'cv_file': cv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_cv'])
        
        # Step 4: Verify complete profile
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_complete'])
        self.assertTrue(response.data['has_cv'])
        self.assertEqual(len(response.data['skills']), 4)
    
    def test_profile_stats_and_recommendations(self):
        """Test profile statistics and completion recommendations (Requirement 1.3)."""
        stats_url = reverse('profiles:stats')
        
        # Get initial stats
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['completion_percentage'], 0.0)
        self.assertFalse(response.data['is_complete'])
        self.assertGreater(len(response.data['recommendations']), 0)
        
        # Update profile partially
        update_url = reverse('profiles:update')
        data = {
            'headline': 'Software Engineer',
            'location': 'New York, NY'
        }
        self.client.patch(update_url, data, format='json')
        
        # Check updated stats
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['completion_percentage'], 40.0)  # 2 out of 5 fields
        self.assertFalse(response.data['is_complete'])
    
    def test_cv_metadata_extraction_workflow(self):
        """Test CV metadata extraction and analysis workflow (Requirement 1.1)."""
        # Upload CV
        cv_url = reverse('profiles:upload-cv')
        cv_content = b"%PDF-1.4\nThis is a test CV with skills: Python, Django, React"
        cv_file = SimpleUploadedFile("test_cv.pdf", cv_content, content_type="application/pdf")
        response = self.client.patch(cv_url, {'cv_file': cv_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check metadata was extracted
        self.assertIn('cv_metadata', response.data)
        metadata = response.data['cv_metadata']
        self.assertIn('extraction_timestamp', metadata)
        self.assertIn('file_info', metadata)
        self.assertIn('content_analysis', metadata)
        
        # Test metadata endpoint
        metadata_url = reverse('profiles:cv-metadata')
        response = self.client.get(metadata_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_metadata'])
        self.assertIsNotNone(response.data['cv_uploaded_at'])
        
        # Test re-analysis
        analyze_url = reverse('profiles:analyze-cv')
        response = self.client.post(analyze_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('metadata', response.data)
    
    def test_skill_management_workflow(self):
        """Test complete skill management workflow (Requirement 1.3)."""
        # Add individual skills
        add_url = reverse('profiles:add-skill')
        
        skills_to_add = ['Python', 'Django', 'React', 'PostgreSQL']
        for skill in skills_to_add:
            response = self.client.post(add_url, {'skill': skill}, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertIn(skill, response.data['skills'])
        
        # Try to add duplicate skill
        response = self.client.post(add_url, {'skill': 'Python'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should not duplicate
        python_count = response.data['skills'].count('Python')
        self.assertEqual(python_count, 1)
        
        # Remove a skill
        remove_url = reverse('profiles:remove-skill')
        response = self.client.post(remove_url, {'skill': 'React'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('React', response.data['skills'])
        
        # Verify final skills list
        profile_url = reverse('profiles:detail')
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_skills = ['Python', 'Django', 'PostgreSQL']
        self.assertEqual(set(response.data['skills']), set(expected_skills))
    
    def test_profile_update_validation(self):
        """Test profile update validation and error handling (Requirement 1.3)."""
        update_url = reverse('profiles:update')
        
        # Test invalid experience level
        data = {'experience_level': 'invalid_level'}
        response = self.client.patch(update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid skills format (not a list)
        data = {'skills': 'not_a_list'}
        response = self.client.patch(update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test too many skills
        data = {'skills': [f'skill_{i}' for i in range(51)]}
        response = self.client.patch(update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test valid update
        data = {
            'headline': 'Valid Headline',
            'summary': 'Valid summary content',
            'experience_level': 'senior',
            'skills': ['Python', 'Django']
        }
        response = self.client.patch(update_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_concurrent_cv_uploads(self):
        """Test handling of concurrent CV uploads (Requirement 1.3)."""
        cv_url = reverse('profiles:upload-cv')
        
        # Simulate rapid successive uploads
        cv_content1 = b"%PDF-1.4\nFirst CV content"
        cv_file1 = SimpleUploadedFile("cv1.pdf", cv_content1, content_type="application/pdf")
        
        cv_content2 = b"%PDF-1.4\nSecond CV content"
        cv_file2 = SimpleUploadedFile("cv2.pdf", cv_content2, content_type="application/pdf")
        
        # Upload first CV
        response1 = self.client.patch(cv_url, {'cv_file': cv_file1}, format='multipart')
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Upload second CV immediately
        response2 = self.client.patch(cv_url, {'cv_file': cv_file2}, format='multipart')
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Verify only the latest CV is stored
        profile_url = reverse('profiles:detail')
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_cv'])
        
        # Verify metadata is from the second upload
        latest_hash = response.data['cv_metadata']['file_hash']
        second_hash = response2.data['cv_metadata']['file_hash']
        self.assertEqual(latest_hash, second_hash)