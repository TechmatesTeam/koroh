"""
Tests for peer groups app.

This module contains comprehensive unit tests for peer group models, views, 
services, and functionality including group creation, membership management,
recommendation systems, communication features, and notifications.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
from django.utils import timezone
from datetime import timedelta

from .models import PeerGroup, GroupMembership, GroupAdminship, GroupPost, GroupComment
from .services import PeerGroupRecommendationService, GroupMatchingService
from .notifications import GroupNotificationService

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


class GroupPostModelTest(TestCase):
    """Test cases for GroupPost model."""
    
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
        
        # Add user as member
        GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            status='active'
        )
    
    def test_post_creation(self):
        """Test that a group post can be created."""
        post = GroupPost.objects.create(
            group=self.group,
            author=self.user,
            title='Test Post',
            content='This is a test post content.',
            post_type='discussion'
        )
        
        self.assertEqual(post.title, 'Test Post')
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.like_count, 0)
        self.assertEqual(post.comment_count, 0)
    
    def test_post_string_representation(self):
        """Test the string representation of a post."""
        post = GroupPost.objects.create(
            group=self.group,
            author=self.user,
            title='Test Post',
            content='This is a test post content.'
        )
        
        expected = f"Test Post in {self.group.name}"
        self.assertEqual(str(post), expected)
    
    def test_post_like_functionality(self):
        """Test post like increment and decrement."""
        post = GroupPost.objects.create(
            group=self.group,
            author=self.user,
            title='Test Post',
            content='This is a test post content.'
        )
        
        # Test like increment
        post.increment_like_count()
        self.assertEqual(post.like_count, 1)
        
        # Test like decrement
        post.decrement_like_count()
        self.assertEqual(post.like_count, 0)
        
        # Test decrement doesn't go below 0
        post.decrement_like_count()
        self.assertEqual(post.like_count, 0)


class GroupCommentModelTest(TestCase):
    """Test cases for GroupComment model."""
    
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
        
        self.post = GroupPost.objects.create(
            group=self.group,
            author=self.user,
            title='Test Post',
            content='This is a test post content.'
        )
    
    def test_comment_creation(self):
        """Test that a comment can be created."""
        comment = GroupComment.objects.create(
            post=self.post,
            author=self.user,
            content='This is a test comment.'
        )
        
        self.assertEqual(comment.content, 'This is a test comment.')
        self.assertEqual(comment.author, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.like_count, 0)
        self.assertFalse(comment.is_reply)
    
    def test_comment_reply(self):
        """Test comment reply functionality."""
        parent_comment = GroupComment.objects.create(
            post=self.post,
            author=self.user,
            content='Parent comment.'
        )
        
        reply_comment = GroupComment.objects.create(
            post=self.post,
            author=self.user,
            content='Reply comment.',
            parent=parent_comment
        )
        
        self.assertTrue(reply_comment.is_reply)
        self.assertEqual(reply_comment.parent, parent_comment)


class PeerGroupRecommendationServiceTest(TestCase):
    """Test cases for PeerGroupRecommendationService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create user profile
        from profiles.models import Profile
        self.profile = Profile.objects.create(
            user=self.user,
            industry='Technology',
            skills=['Python', 'Django', 'AI'],
            experience_level='Mid-level'
        )
        
        # Create test groups
        self.group1 = PeerGroup.objects.create(
            name='Tech Group',
            description='Technology professionals',
            group_type='industry',
            industry='Technology',
            skills=['Python', 'Django'],
            created_by=self.user,
            activity_score=75.0
        )
        
        self.group2 = PeerGroup.objects.create(
            name='AI Enthusiasts',
            description='AI and ML professionals',
            group_type='skill',
            industry='Technology',
            skills=['AI', 'Machine Learning'],
            created_by=self.user,
            activity_score=85.0
        )
        
        self.service = PeerGroupRecommendationService()
    
    @patch('peer_groups.services.AIServiceFactory.create_recommendation_service')
    def test_get_recommendations_with_ai_success(self, mock_ai_service):
        """Test successful AI-powered recommendations."""
        # Mock AI service response
        mock_ai_instance = MagicMock()
        mock_ai_instance.process.return_value = [
            {
                'option_id': self.group2.id,
                'match_score': 85,
                'match_reasons': ['Matches AI skills', 'Technology industry'],
                'recommendation_text': 'Great match for AI enthusiasts',
                'confidence': 'high'
            }
        ]
        mock_ai_service.return_value = mock_ai_instance
        
        recommendations = self.service.get_recommendations_for_user(
            user=self.user,
            limit=5,
            exclude_joined=True
        )
        
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(recommendations[0]['group']['id'], self.group2.id)
        self.assertEqual(recommendations[0]['match_score'], 85)
        self.assertIn('AI skills', recommendations[0]['match_reasons'])
    
    @patch('peer_groups.services.AIServiceFactory.create_recommendation_service')
    def test_get_recommendations_ai_fallback(self, mock_ai_service):
        """Test fallback to rule-based recommendations when AI fails."""
        # Mock AI service to raise exception
        mock_ai_service.side_effect = Exception("AI service unavailable")
        
        recommendations = self.service.get_recommendations_for_user(
            user=self.user,
            limit=5,
            exclude_joined=True
        )
        
        # Should get fallback recommendations
        self.assertGreater(len(recommendations), 0)
        self.assertIn('group', recommendations[0])
        self.assertIn('match_score', recommendations[0])
    
    def test_build_user_profile(self):
        """Test user profile building for AI analysis."""
        user_profile = self.service._build_user_profile(self.user)
        
        self.assertEqual(user_profile['user_id'], self.user.id)
        self.assertEqual(user_profile['industry'], 'Technology')
        self.assertEqual(user_profile['skills'], ['Python', 'Django', 'AI'])
        self.assertEqual(user_profile['experience_level'], 'Mid-level')
    
    def test_get_available_groups(self):
        """Test getting available groups for recommendations."""
        available_groups = self.service._get_available_groups(
            user=self.user,
            exclude_joined=True,
            limit=10
        )
        
        self.assertGreater(len(available_groups), 0)
        group_ids = [g['id'] for g in available_groups]
        self.assertIn(self.group1.id, group_ids)
        self.assertIn(self.group2.id, group_ids)


class GroupMatchingServiceTest(TestCase):
    """Test cases for GroupMatchingService."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        self.group1 = PeerGroup.objects.create(
            name='Tech Group',
            description='Technology professionals',
            group_type='industry',
            industry='Technology',
            created_by=self.user,
            activity_score=75.0
        )
        
        self.group2 = PeerGroup.objects.create(
            name='Similar Tech Group',
            description='Another tech group',
            group_type='industry',
            industry='Technology',
            created_by=self.user,
            activity_score=65.0
        )
        
        self.service = GroupMatchingService()
    
    def test_find_similar_groups(self):
        """Test finding groups similar to a reference group."""
        similar_groups = self.service.find_similar_groups(
            reference_group=self.group1,
            user=self.user,
            limit=5
        )
        
        # Should find the similar group but not the reference group itself
        group_ids = [g.id for g in similar_groups]
        self.assertIn(self.group2.id, group_ids)
        self.assertNotIn(self.group1.id, group_ids)
    
    def test_get_trending_groups(self):
        """Test getting trending groups."""
        # Create recent activity
        recent_date = timezone.now() - timedelta(days=3)
        GroupMembership.objects.create(
            user=self.user,
            group=self.group1,
            status='active'
        )
        GroupMembership.objects.filter(
            group=self.group1
        ).update(joined_at=recent_date)
        
        trending_groups = self.service.get_trending_groups(
            user=self.user,
            limit=10
        )
        
        self.assertGreater(len(trending_groups), 0)
    
    def test_search_groups(self):
        """Test group search functionality."""
        search_results = self.service.search_groups(
            query='Tech',
            user=self.user,
            filters={'group_type': 'industry'},
            limit=10
        )
        
        self.assertGreater(len(search_results), 0)
        # Should find groups with 'Tech' in the name
        group_names = [g.name for g in search_results]
        self.assertTrue(any('Tech' in name for name in group_names))


class GroupNotificationServiceTest(TestCase):
    """Test cases for GroupNotificationService."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )
        
        self.group = PeerGroup.objects.create(
            name='Test Group',
            description='A test peer group',
            created_by=self.user1
        )
        
        self.service = GroupNotificationService()
    
    @patch('peer_groups.notifications.send_mail')
    def test_notify_new_member_joined(self, mock_send_mail):
        """Test notification when new member joins."""
        membership = GroupMembership.objects.create(
            user=self.user2,
            group=self.group,
            status='active'
        )
        
        self.service.notify_new_member_joined(membership)
        
        # Should attempt to send email notification
        self.assertTrue(mock_send_mail.called)
    
    @patch('peer_groups.notifications.send_mail')
    def test_notify_new_post(self, mock_send_mail):
        """Test notification for new post."""
        # Add user2 as member with notifications enabled
        GroupMembership.objects.create(
            user=self.user2,
            group=self.group,
            status='active',
            notifications_enabled=True,
            email_notifications=True
        )
        
        post = GroupPost.objects.create(
            group=self.group,
            author=self.user1,
            title='Test Post',
            content='Test content'
        )
        
        self.service.notify_new_post(post)
        
        # Should attempt to send email notification
        self.assertTrue(mock_send_mail.called)
    
    @patch('peer_groups.notifications.send_mail')
    def test_notify_new_comment(self, mock_send_mail):
        """Test notification for new comment."""
        post = GroupPost.objects.create(
            group=self.group,
            author=self.user1,
            title='Test Post',
            content='Test content'
        )
        
        comment = GroupComment.objects.create(
            post=post,
            author=self.user2,
            content='Test comment'
        )
        
        self.service.notify_new_comment(comment)
        
        # Should attempt to send email notification to post author
        self.assertTrue(mock_send_mail.called)
    
    def test_get_group_admins(self):
        """Test getting group admins."""
        # Add another admin
        GroupAdminship.objects.create(
            user=self.user2,
            group=self.group,
            role='admin',
            granted_by=self.user1
        )
        
        admins = self.service._get_group_admins(self.group)
        
        # Should include creator and added admin
        admin_ids = [admin.id for admin in admins]
        self.assertIn(self.user1.id, admin_ids)
        self.assertIn(self.user2.id, admin_ids)


class PeerGroupAdvancedAPITest(APITestCase):
    """Advanced test cases for PeerGroup API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        
        self.user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )
        
        self.group = PeerGroup.objects.create(
            name='Test Group',
            description='A test peer group',
            group_type='industry',
            industry='Technology',
            privacy_level='public',
            created_by=self.user1
        )
        
        # Add user1 as member and admin
        GroupMembership.objects.create(
            user=self.user1,
            group=self.group,
            status='active'
        )
        GroupAdminship.objects.create(
            user=self.user1,
            group=self.group,
            role='admin'
        )
    
    def test_group_discovery_endpoint(self):
        """Test group discovery with AI recommendations."""
        self.client.force_authenticate(user=self.user2)
        
        url = reverse('peer_groups:peergroup-discover')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('recommendations', response.data)
        self.assertIn('ai_powered', response.data)
    
    def test_group_search_endpoint(self):
        """Test group search functionality."""
        self.client.force_authenticate(user=self.user2)
        
        url = reverse('peer_groups:peergroup-search')
        response = self.client.get(url, {'q': 'Test'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertGreater(len(response.data['results']), 0)
    
    def test_group_member_management(self):
        """Test group member management functionality."""
        self.client.force_authenticate(user=self.user1)
        
        # First, user2 joins the group
        join_url = reverse('peer_groups:peergroup-join', kwargs={'slug': self.group.slug})
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(join_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Now admin manages the member
        self.client.force_authenticate(user=self.user1)
        manage_url = reverse('peer_groups:peergroup-manage-member', kwargs={'slug': self.group.slug})
        response = self.client.post(manage_url, {
            'member_id': self.user2.id,
            'action': 'promote',
            'reason': 'Good contributor'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('promoted', response.data['message'].lower())
    
    def test_group_activity_feed(self):
        """Test group activity feed endpoint."""
        # Create some activity
        post = GroupPost.objects.create(
            group=self.group,
            author=self.user1,
            title='Test Post',
            content='Test content'
        )
        
        GroupComment.objects.create(
            post=post,
            author=self.user1,
            content='Test comment'
        )
        
        self.client.force_authenticate(user=self.user1)
        url = reverse('peer_groups:peergroup-activity-feed', kwargs={'slug': self.group.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('activity', response.data)
        self.assertGreater(len(response.data['activity']), 0)
    
    def test_my_activity_feed(self):
        """Test user's activity feed across all groups."""
        # Add user as member
        GroupMembership.objects.create(
            user=self.user2,
            group=self.group,
            status='active'
        )
        
        # Create activity
        GroupPost.objects.create(
            group=self.group,
            author=self.user1,
            title='Test Post',
            content='Test content'
        )
        
        self.client.force_authenticate(user=self.user2)
        url = reverse('peer_groups:peergroup-my-activity-feed')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('activity', response.data)


class GroupPostAPITest(APITestCase):
    """Test cases for GroupPost API endpoints."""
    
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
        
        # Add user as member
        GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            status='active'
        )
    
    def test_create_post(self):
        """Test creating a post in a group."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('peer_groups:group-posts-list', kwargs={'group_slug': self.group.slug})
        data = {
            'title': 'Test Post',
            'content': 'This is a test post content.',
            'post_type': 'discussion'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Test Post')
        
        # Verify post was created in database
        post = GroupPost.objects.get(title='Test Post')
        self.assertEqual(post.group, self.group)
        self.assertEqual(post.author, self.user)
    
    def test_list_posts(self):
        """Test listing posts in a group."""
        # Create a test post
        GroupPost.objects.create(
            group=self.group,
            author=self.user,
            title='Test Post',
            content='Test content'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('peer_groups:group-posts-list', kwargs={'group_slug': self.group.slug})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'Test Post')
    
    def test_post_like_functionality(self):
        """Test liking and unliking posts."""
        post = GroupPost.objects.create(
            group=self.group,
            author=self.user,
            title='Test Post',
            content='Test content'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('peer_groups:group-posts-detail', kwargs={
            'group_slug': self.group.slug,
            'pk': post.id
        })
        
        # Test liking
        response = self.client.post(f"{url}like/", {'action': 'like'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['like_count'], 1)
        
        # Test unliking
        response = self.client.post(f"{url}like/", {'action': 'unlike'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['like_count'], 0)


class GroupCommentAPITest(APITestCase):
    """Test cases for GroupComment API endpoints."""
    
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
        
        # Add user as member
        GroupMembership.objects.create(
            user=self.user,
            group=self.group,
            status='active'
        )
        
        self.post = GroupPost.objects.create(
            group=self.group,
            author=self.user,
            title='Test Post',
            content='Test content'
        )
    
    def test_create_comment(self):
        """Test creating a comment on a post."""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('peer_groups:post-comments-list', kwargs={
            'group_slug': self.group.slug,
            'post_pk': self.post.id
        })
        data = {
            'content': 'This is a test comment.'
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['content'], 'This is a test comment.')
        
        # Verify comment was created in database
        comment = GroupComment.objects.get(content='This is a test comment.')
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.author, self.user)
    
    def test_list_comments(self):
        """Test listing comments for a post."""
        # Create a test comment
        GroupComment.objects.create(
            post=self.post,
            author=self.user,
            content='Test comment'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('peer_groups:post-comments-list', kwargs={
            'group_slug': self.group.slug,
            'post_pk': self.post.id
        })
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['content'], 'Test comment')
    
    def test_comment_like_functionality(self):
        """Test liking and unliking comments."""
        comment = GroupComment.objects.create(
            post=self.post,
            author=self.user,
            content='Test comment'
        )
        
        self.client.force_authenticate(user=self.user)
        url = reverse('peer_groups:post-comments-detail', kwargs={
            'group_slug': self.group.slug,
            'post_pk': self.post.id,
            'pk': comment.id
        })
        
        # Test liking
        response = self.client.post(f"{url}like/", {'action': 'like'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['like_count'], 1)
        
        # Test unliking
        response = self.client.post(f"{url}like/", {'action': 'unlike'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['like_count'], 0)


class GroupIntegrationTest(TestCase):
    """Integration tests for complete group workflows."""
    
    def setUp(self):
        """Set up test data."""
        self.creator = User.objects.create_user(
            email='creator@example.com',
            password='testpass123',
            first_name='Group',
            last_name='Creator'
        )
        
        self.member = User.objects.create_user(
            email='member@example.com',
            password='testpass123',
            first_name='Group',
            last_name='Member'
        )
    
    def test_complete_group_workflow(self):
        """Test complete group creation and interaction workflow."""
        # 1. Create group
        group = PeerGroup.objects.create(
            name='Integration Test Group',
            description='A group for integration testing',
            group_type='industry',
            industry='Technology',
            privacy_level='public',
            created_by=self.creator
        )
        
        # Creator should be automatically added as member and admin
        creator_membership = GroupMembership.objects.create(
            user=self.creator,
            group=group,
            status='active'
        )
        creator_adminship = GroupAdminship.objects.create(
            user=self.creator,
            group=group,
            role='admin'
        )
        
        # 2. Member joins group
        member_membership = GroupMembership.objects.create(
            user=self.member,
            group=group,
            status='active'
        )
        
        # 3. Member creates post
        post = GroupPost.objects.create(
            group=group,
            author=self.member,
            title='Welcome Post',
            content='Hello everyone!'
        )
        
        # 4. Creator comments on post
        comment = GroupComment.objects.create(
            post=post,
            author=self.creator,
            content='Welcome to the group!'
        )
        
        # 5. Verify all relationships
        self.assertTrue(group.is_member(self.creator))
        self.assertTrue(group.is_member(self.member))
        self.assertTrue(group.is_admin(self.creator))
        self.assertFalse(group.is_admin(self.member))
        
        self.assertEqual(group.posts.count(), 1)
        self.assertEqual(post.comments.count(), 1)
        self.assertEqual(group.member_count, 0)  # Will be updated when save is called
        
        # Update member count
        group.update_member_count()
        self.assertEqual(group.member_count, 2)
    
    def test_group_privacy_and_permissions(self):
        """Test group privacy levels and permission enforcement."""
        # Create private group
        private_group = PeerGroup.objects.create(
            name='Private Group',
            description='A private group',
            privacy_level='private',
            created_by=self.creator
        )
        
        # Creator can join freely
        self.assertTrue(private_group.can_user_join(self.creator))
        
        # Non-member cannot join private group freely
        self.assertTrue(private_group.can_user_join(self.member))  # can_user_join checks basic eligibility
        self.assertFalse(private_group.can_join_freely)  # but group doesn't allow free joining
        
        # Test restricted group
        restricted_group = PeerGroup.objects.create(
            name='Restricted Group',
            description='A restricted group',
            privacy_level='restricted',
            created_by=self.creator
        )
        
        self.assertTrue(restricted_group.requires_approval)
        self.assertFalse(restricted_group.can_join_freely)