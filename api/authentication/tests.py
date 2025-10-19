"""
Tests for authentication app.

This module contains tests for user registration, login,
and other authentication functionality.
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the custom User model."""
    
    def setUp(self):
        """Set up test data."""
        self.user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpassword123'
        }
    
    def test_create_user(self):
        """Test creating a user with email."""
        user = User.objects.create_user(**self.user_data)
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertEqual(user.first_name, self.user_data['first_name'])
        self.assertEqual(user.last_name, self.user_data['last_name'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertFalse(user.is_verified)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
    
    def test_create_superuser(self):
        """Test creating a superuser."""
        user = User.objects.create_superuser(**self.user_data)
        
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_user_string_representation(self):
        """Test the string representation of user."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), self.user_data['email'])
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        user = User.objects.create_user(**self.user_data)
        expected_name = f"{self.user_data['first_name']} {self.user_data['last_name']}"
        self.assertEqual(user.get_full_name(), expected_name)
    
    def test_get_short_name(self):
        """Test get_short_name method."""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.get_short_name(), self.user_data['first_name'])
    
    def test_is_profile_complete(self):
        """Test is_profile_complete property."""
        user = User.objects.create_user(**self.user_data)
        
        # Profile should not be complete initially (not verified)
        self.assertFalse(user.is_profile_complete)
        
        # Mark as verified
        user.is_verified = True
        user.save()
        
        # Now profile should be complete
        self.assertTrue(user.is_profile_complete)


class AuthenticationAPITest(APITestCase):
    """Test cases for authentication API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.registration_data = {
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpassword123',
            'password_confirm': 'newpassword123'
        }
        
        self.existing_user = User.objects.create_user(
            email='existing@example.com',
            first_name='Existing',
            last_name='User',
            password='existingpassword123'
        )
    
    def test_user_registration_success(self):
        """Test successful user registration."""
        url = reverse('authentication:register')
        response = self.client.post(url, self.registration_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertEqual(response.data['user']['email'], self.registration_data['email'])
        
        # Verify user was created in database
        user = User.objects.get(email=self.registration_data['email'])
        self.assertEqual(user.first_name, self.registration_data['first_name'])
        self.assertEqual(user.last_name, self.registration_data['last_name'])
    
    def test_user_registration_duplicate_email(self):
        """Test registration with duplicate email."""
        self.registration_data['email'] = self.existing_user.email
        
        url = reverse('authentication:register')
        response = self.client.post(url, self.registration_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_user_registration_password_mismatch(self):
        """Test registration with password mismatch."""
        self.registration_data['password_confirm'] = 'differentpassword'
        
        url = reverse('authentication:register')
        response = self.client.post(url, self.registration_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
    
    def test_user_login_success(self):
        """Test successful user login."""
        login_data = {
            'email': self.existing_user.email,
            'password': 'existingpassword123'
        }
        
        url = reverse('authentication:login')
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
    
    def test_user_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        login_data = {
            'email': self.existing_user.email,
            'password': 'wrongpassword'
        }
        
        url = reverse('authentication:login')
        response = self.client.post(url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_check_email_availability_available(self):
        """Test email availability check for available email."""
        url = reverse('authentication:check_email')
        data = {'email': 'available@example.com'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
    
    def test_check_email_availability_taken(self):
        """Test email availability check for taken email."""
        url = reverse('authentication:check_email')
        data = {'email': self.existing_user.email}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['available'])
    
    def test_user_profile_access_authenticated(self):
        """Test accessing user profile when authenticated."""
        self.client.force_authenticate(user=self.existing_user)
        
        url = reverse('authentication:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.existing_user.email)
    
    def test_user_profile_access_unauthenticated(self):
        """Test accessing user profile when not authenticated."""
        url = reverse('authentication:profile')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)