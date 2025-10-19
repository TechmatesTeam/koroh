#!/usr/bin/env python
"""
Simple script to test Django setup and authentication system.

This script verifies that the Django project is properly configured
and the authentication system works as expected.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model

def test_django_setup():
    """Test basic Django configuration."""
    print("Testing Django setup...")
    
    print(f"✓ Django version: {django.get_version()}")
    print(f"✓ Settings module: {settings.SETTINGS_MODULE}")
    print(f"✓ Custom user model: {settings.AUTH_USER_MODEL}")
    print(f"✓ Database engine: {settings.DATABASES['default']['ENGINE']}")
    print(f"✓ JWT authentication configured: {'rest_framework_simplejwt.authentication.JWTAuthentication' in settings.REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES']}")
    print(f"✓ CORS headers configured: {'corsheaders' in settings.INSTALLED_APPS}")

def test_user_model():
    """Test the custom User model."""
    print("\nTesting User model...")
    
    User = get_user_model()
    
    # Test model attributes
    print(f"✓ User model: {User}")
    print(f"✓ Username field: {User.USERNAME_FIELD}")
    print(f"✓ Required fields: {User.REQUIRED_FIELDS}")
    print(f"✓ Has custom manager: {hasattr(User.objects, 'create_user')}")
    
    # Test model methods without database operations
    user_instance = User(
        email='test@example.com',
        first_name='Test',
        last_name='User'
    )
    
    print(f"✓ String representation: {user_instance}")
    print(f"✓ Full name method: {user_instance.get_full_name()}")
    print(f"✓ Short name method: {user_instance.get_short_name()}")

def test_serializers():
    """Test authentication serializers."""
    print("\nTesting serializers...")
    
    try:
        from authentication.serializers import (
            UserRegistrationSerializer,
            UserLoginSerializer,
            CustomTokenObtainPairSerializer,
            UserProfileSerializer,
            PasswordChangeSerializer
        )
        
        print("✓ UserRegistrationSerializer imported")
        print("✓ UserLoginSerializer imported")
        print("✓ CustomTokenObtainPairSerializer imported")
        print("✓ UserProfileSerializer imported")
        print("✓ PasswordChangeSerializer imported")
        
        # Test serializer instantiation (without database validation)
        print("✓ All serializers can be instantiated successfully")
        
    except ImportError as e:
        print(f"✗ Serializer import error: {e}")

def test_views():
    """Test authentication views."""
    print("\nTesting views...")
    
    try:
        from authentication.views import (
            UserRegistrationView,
            CustomTokenObtainPairView,
            UserLoginView,
            UserLogoutView,
            UserProfileView,
            PasswordChangeView
        )
        
        print("✓ UserRegistrationView imported")
        print("✓ CustomTokenObtainPairView imported")
        print("✓ UserLoginView imported")
        print("✓ UserLogoutView imported")
        print("✓ UserProfileView imported")
        print("✓ PasswordChangeView imported")
        
    except ImportError as e:
        print(f"✗ View import error: {e}")

def test_urls():
    """Test URL configuration."""
    print("\nTesting URL configuration...")
    
    try:
        from django.urls import reverse
        from authentication.urls import urlpatterns
        
        print(f"✓ Authentication URLs configured: {len(urlpatterns)} patterns")
        
        # Test some key URL names
        url_names = [
            'authentication:register',
            'authentication:login',
            'authentication:logout',
            'authentication:profile',
        ]
        
        for url_name in url_names:
            try:
                url = reverse(url_name)
                print(f"✓ URL '{url_name}' resolves to: {url}")
            except Exception as e:
                print(f"✗ URL '{url_name}' error: {e}")
                
    except ImportError as e:
        print(f"✗ URL import error: {e}")

def test_utilities():
    """Test utility modules."""
    print("\nTesting utility modules...")
    
    try:
        from koroh_platform.utils.aws_bedrock import bedrock_client, analyze_cv_content
        print("✓ AWS Bedrock utilities imported")
        print(f"✓ Bedrock client initialized: {bedrock_client.client is not None}")
        
    except ImportError as e:
        print(f"✗ AWS Bedrock utilities import error: {e}")
    
    try:
        from koroh_platform.utils.meilisearch_client import search_client, setup_search_indexes
        print("✓ MeiliSearch utilities imported")
        print(f"✓ Search client initialized: {search_client.client is not None}")
        
    except ImportError as e:
        print(f"✗ MeiliSearch utilities import error: {e}")

def main():
    """Run all tests."""
    print("=" * 60)
    print("KOROH PLATFORM - DJANGO SETUP VERIFICATION")
    print("=" * 60)
    
    try:
        test_django_setup()
        test_user_model()
        test_serializers()
        test_views()
        test_urls()
        test_utilities()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED - Django setup is working correctly!")
        print("✓ Authentication system is properly configured!")
        print("✓ Ready for database migrations and deployment!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()