"""
Tests for peer groups app.

This module contains unit tests for peer group models, views, and functionality.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

from .models import PeerGroup, GroupMembership, GroupAdminship, GroupPost, GroupComment

User = get_user_model()


class PeerGroupModelTest(TestCase):
    """Test cases for PeerGroup model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.group = PeerGroup.objects.create(
            name='Test Group',
            description='A test peer group',
            group_type='industry',
            industry='Technology',
            privacy_level='public',
            created_by=self.user
        )
    
    def test_group_creation(self):
        """Test that a peer group can be created."""
        self.assertEqual(self.group.name, 'Test Group')
        self.assertEqual(self.group.created_by, self.user)
        self.assertTrue(self.group.slug)
        self.assertEqual(self.group.member_count, 0)
    
    def test_group_string_representation(self):
        """Test the string representation of a peer group."""
        self.assertEqual(str(self.group), 'Test Group')
    
    def test_group_membership_methods(self):
        """Test group membership helper methods."""
        # Initially user is not a member
        self.assertFalse(self.group.is_member(self.user))
        self.assertTrue(self.group.can_user_join(self.user))
        
        # Add user as member
        GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            status='active'
        )
        
        # Now user is a member
        self.assertTrue(self.group.is_member(self.user))
        self.assertFalse(self.group.can_user_join(self.user))
    
    def test_group_admin_methods(self):
        """Test group admin helper methods."""
        # Creator is admin by default
        self.assertTrue(self.group.is_admin(self.user))
        
        # Create another user
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        # Other user is not admin
        self.assertFalse(self.group.is_admin(other_user))
        
        # Add other user as admin
        GroupAdminship.objects.create(
            user=other_user,
            group=self.group,
            role='admin',
            granted_by=self.user
        )
        
        # Now other user is admin
        self.assertTrue(self.group.is_admin(other_user))


class GroupMembershipModelTest(TestCase):
    """Test cases for GroupMembership model."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.group = PeerGroup.objects.create(
            name='Test Group',
            description='A test peer group',
            created_by=self.user
        )
    
    def test_membership_creation(self):
        """Test that a group membership can be created."""
        membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            status='active'
        )
        
        self.assertEqual(membership.user, self.user)
        self.assertEqual(membership.group, self.group)
        self.assertEqual(membership.status, 'active')
        self.assertTrue(membership.is_active)
    
    def test_membership_string_representation(self):
        """Test the string representation of a membership."""
        membership = GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            status='active'
        )
        
        expected = f"{self.user.get_full_name()} in {self.group.name}"
        self.assertEqual(str(membership), expected)


class PeerGroupAPITest(APITestCase):
    """Test cases for PeerGroup API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.group = PeerGroup.objects.create(
            name='Test Group',
            description='A test peer group',
            group_type='industry',
            industry='Technology',
            privacy_level='public',
            created_by=self.user
        )
    
    def test_group_list_endpoint(self):
        """Test the group list endpoint."""
        url = reverse('peer_groups:peergroup-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'Test Group')
    
    def test_group_detail_endpoint(self):
        """Test the group detail endpoint."""
        url = reverse('peer_groups:peergroup-detail', kwargs={'slug': self.group.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Group')
    
    def test_group_creation_requires_authentication(self):
        """Test that group creation requires authentication."""
        url = reverse('peer_groups:peergroup-list')
        data = {
            'name': 'New Group',
            'description': 'A new test group',
            'group_type': 'industry'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_authenticated_group_creation(self):
        """Test group creation with authentication."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('peer_groups:peergroup-list')
        data = {
            'name': 'New Group',
            'description': 'A new test group',
            'group_type': 'industry',
            'industry': 'Technology'
        }
        
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'New Group')
        
        # Check that creator is added as member and admin
        new_group = PeerGroup.objects.get(name='New Group')
        self.assertTrue(new_group.is_member(self.user))
        self.assertTrue(new_group.is_admin(self.user))
    
    def test_group_join_endpoint(self):
        """Test joining a group."""
        other_user = User.objects.create_user(
            email='other@example.com',
            password='testpass123',
            first_name='Other',
            last_name='User'
        )
        
        self.client.force_authenticate(user=other_user)
        
        url = reverse('peer_groups:peergroup-join', kwargs={'slug': self.group.slug})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('Successfully joined group', response.data['message'])
        
        # Check that user is now a member
        self.assertTrue(self.group.is_member(other_user))
    
    def test_my_groups_endpoint(self):
        """Test the my groups endpoint."""
        # Add user as member
        GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            status='active'
        )
        
        self.client.force_authenticate(user=self.user)
        
        url = reverse('peer_groups:peergroup-my-groups')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Group')