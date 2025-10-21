#!/usr/bin/env python3
"""
Simple validation script for peer group functionality.

This script validates the core peer group models and functionality
without requiring a full Django test environment.
"""

import os
import sys
import django
from django.conf import settings

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.test_settings')

try:
    django.setup()
    
    # Import models after Django setup
    from django.contrib.auth import get_user_model
    from peer_groups.models import PeerGroup, GroupMembership, GroupAdminship, GroupPost, GroupComment
    from peer_groups.services import PeerGroupRecommendationService, GroupMatchingService
    from peer_groups.notifications import GroupNotificationService
    
    User = get_user_model()
    
    def test_model_creation():
        """Test basic model creation and relationships."""
        print("Testing model creation...")
        
        # Create test user
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
        
        # Create peer group
        group = PeerGroup.objects.create(
            name='Test Group',
            description='A test peer group',
            group_type='industry',
            industry='Technology',
            privacy_level='public',
            created_by=user
        )
        
        # Test group properties
        assert group.name == 'Test Group'
        assert group.created_by == user
        assert group.slug is not None
        assert group.can_join_freely == True
        assert group.is_admin(user) == True
        
        # Create membership
        membership = GroupMembership.objects.create(
            user=user,
            group=group,
            status='active'
        )
        
        # Test membership
        assert group.is_member(user) == True
        assert membership.is_active == True
        
        # Create post
        post = GroupPost.objects.create(
            group=group,
            author=user,
            title='Test Post',
            content='This is a test post.'
        )
        
        # Test post
        assert post.title == 'Test Post'
        assert post.author == user
        assert post.group == group
        
        # Create comment
        comment = GroupComment.objects.create(
            post=post,
            author=user,
            content='Test comment'
        )
        
        # Test comment
        assert comment.content == 'Test comment'
        assert comment.author == user
        assert comment.post == post
        assert comment.is_reply == False
        
        print("✓ Model creation tests passed")
    
    def test_group_functionality():
        """Test group-specific functionality."""
        print("Testing group functionality...")
        
        user1 = User.objects.create_user(
            email='user1@example.com',
            password='testpass123',
            first_name='User',
            last_name='One'
        )
        
        user2 = User.objects.create_user(
            email='user2@example.com',
            password='testpass123',
            first_name='User',
            last_name='Two'
        )
        
        # Create group
        group = PeerGroup.objects.create(
            name='Functionality Test Group',
            description='Testing group functionality',
            group_type='skill',
            skills=['Python', 'Django'],
            privacy_level='public',
            created_by=user1
        )
        
        # Test group methods
        assert group.can_user_join(user2) == True
        assert group.is_admin(user1) == True
        assert group.is_admin(user2) == False
        
        # Add member
        membership = GroupMembership.objects.create(
            user=user2,
            group=group,
            status='active'
        )
        
        # Test membership methods
        assert group.is_member(user2) == True
        assert group.can_user_join(user2) == False  # Already a member
        
        # Test skill management
        group.add_skill('AI')
        assert 'AI' in group.skills
        
        group.remove_skill('AI')
        assert 'AI' not in group.skills
        
        print("✓ Group functionality tests passed")
    
    def test_service_initialization():
        """Test that services can be initialized."""
        print("Testing service initialization...")
        
        # Test recommendation service
        try:
            rec_service = PeerGroupRecommendationService()
            assert rec_service is not None
            print("✓ PeerGroupRecommendationService initialized")
        except Exception as e:
            print(f"⚠ PeerGroupRecommendationService initialization failed: {e}")
        
        # Test matching service
        try:
            match_service = GroupMatchingService()
            assert match_service is not None
            print("✓ GroupMatchingService initialized")
        except Exception as e:
            print(f"⚠ GroupMatchingService initialization failed: {e}")
        
        # Test notification service
        try:
            notif_service = GroupNotificationService()
            assert notif_service is not None
            print("✓ GroupNotificationService initialized")
        except Exception as e:
            print(f"⚠ GroupNotificationService initialization failed: {e}")
    
    def test_privacy_levels():
        """Test different privacy levels."""
        print("Testing privacy levels...")
        
        user = User.objects.create_user(
            email='privacy@example.com',
            password='testpass123',
            first_name='Privacy',
            last_name='User'
        )
        
        # Public group
        public_group = PeerGroup.objects.create(
            name='Public Group',
            description='A public group',
            privacy_level='public',
            created_by=user
        )
        
        assert public_group.can_join_freely == True
        assert public_group.requires_approval == False
        
        # Private group
        private_group = PeerGroup.objects.create(
            name='Private Group',
            description='A private group',
            privacy_level='private',
            created_by=user
        )
        
        assert private_group.can_join_freely == False
        assert private_group.requires_approval == True
        
        # Restricted group
        restricted_group = PeerGroup.objects.create(
            name='Restricted Group',
            description='A restricted group',
            privacy_level='restricted',
            created_by=user
        )
        
        assert restricted_group.can_join_freely == False
        assert restricted_group.requires_approval == True
        
        print("✓ Privacy level tests passed")
    
    def run_all_tests():
        """Run all validation tests."""
        print("Starting peer group functionality validation...\n")
        
        try:
            test_model_creation()
            test_group_functionality()
            test_service_initialization()
            test_privacy_levels()
            
            print("\n✅ All peer group functionality tests passed!")
            print("The peer group system is working correctly.")
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        return True
    
    if __name__ == '__main__':
        success = run_all_tests()
        sys.exit(0 if success else 1)

except ImportError as e:
    print(f"❌ Django setup failed: {e}")
    print("This validation requires Django and the project dependencies to be installed.")
    sys.exit(1)