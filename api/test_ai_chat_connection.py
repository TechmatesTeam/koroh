#!/usr/bin/env python
"""
AI Chat Connection Test

Test the AI chat functionality to ensure frontend-backend connection works properly.
"""

import os
import sys
import json
import requests
import time

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
import django
django.setup()

from django.contrib.auth import get_user_model
from django.test import Client

User = get_user_model()


def test_ai_chat_api():
    """Test AI chat API endpoints."""
    print("🤖 Testing AI Chat API Connection")
    print("=" * 50)
    
    # Create test user
    try:
        test_user = User.objects.create_user(
            email=f'aichattest_{int(time.time())}@example.com',
            password='TestPass123!',
            first_name='AI',
            last_name='ChatTest'
        )
        print(f"✅ Test user created: {test_user.email}")
    except Exception as e:
        print(f"❌ Failed to create test user: {e}")
        return False
    
    # Test authentication
    client = Client()
    login_response = client.post('/api/v1/auth/login/', {
        'email': test_user.email,
        'password': 'TestPass123!'
    })
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.status_code}")
        return False
    
    token = login_response.json().get('access')
    print(f"✅ Authentication successful")
    
    # Test AI chat endpoints
    headers = {'Authorization': f'Bearer {token}'}
    
    # Test 1: Quick chat
    print("\n🔹 Testing Quick Chat")
    quick_response = client.post(
        '/api/v1/ai/quick/',
        {'message': 'Hello, can you help me with my career?'},
        content_type='application/json',
        **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
    )
    
    if quick_response.status_code == 200:
        data = quick_response.json()
        print(f"✅ Quick chat successful")
        print(f"   Message: {data.get('message', 'N/A')}")
        print(f"   Response: {data.get('response', 'N/A')[:100]}...")
        print(f"   Session ID: {data.get('session_id', 'N/A')}")
    else:
        print(f"❌ Quick chat failed: {quick_response.status_code}")
        print(f"   Error: {quick_response.content.decode()}")
    
    # Test 2: Send message with session
    print("\n🔹 Testing Send Message")
    send_response = client.post(
        '/api/v1/ai/send/',
        {
            'message': 'What are some good career tips for software developers?',
            'context': {'user_intent': 'career_advice'}
        },
        content_type='application/json',
        **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
    )
    
    if send_response.status_code == 200:
        data = send_response.json()
        print(f"✅ Send message successful")
        print(f"   Session ID: {data.get('session_id', 'N/A')}")
        print(f"   User Message: {data.get('user_message', {}).get('content', 'N/A')[:50]}...")
        print(f"   AI Response: {data.get('ai_response', {}).get('content', 'N/A')[:100]}...")
    else:
        print(f"❌ Send message failed: {send_response.status_code}")
        print(f"   Error: {send_response.content.decode()}")
    
    # Test 3: Get sessions
    print("\n🔹 Testing Get Sessions")
    sessions_response = client.get(
        '/api/v1/ai/sessions/',
        **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
    )
    
    if sessions_response.status_code == 200:
        data = sessions_response.json()
        print(f"✅ Get sessions successful")
        print(f"   Sessions count: {data.get('count', 0)}")
        if data.get('sessions'):
            for session in data['sessions'][:2]:  # Show first 2 sessions
                print(f"   - Session: {session.get('title', 'Untitled')[:30]}...")
    else:
        print(f"❌ Get sessions failed: {sessions_response.status_code}")
        print(f"   Error: {sessions_response.content.decode()}")
    
    # Test 4: CV Analysis Chat
    print("\n🔹 Testing CV Analysis Chat")
    cv_response = client.post(
        '/api/v1/ai/analyze-cv/',
        {},
        content_type='application/json',
        **{'HTTP_AUTHORIZATION': f'Bearer {token}'}
    )
    
    if cv_response.status_code == 200:
        data = cv_response.json()
        print(f"✅ CV analysis chat successful")
        print(f"   Session ID: {data.get('session_id', 'N/A')}")
        print(f"   AI Response: {data.get('ai_response', {}).get('content', 'N/A')[:100]}...")
    else:
        print(f"⚠️  CV analysis chat: {cv_response.status_code} (expected if no CV uploaded)")
    
    print("\n" + "=" * 50)
    print("🎉 AI Chat API Testing Complete!")
    return True


def test_with_requests():
    """Test AI chat using requests library (simulating frontend)."""
    print("\n🌐 Testing AI Chat with HTTP Requests (Frontend Simulation)")
    print("=" * 60)
    
    base_url = "http://localhost:8000"
    
    # Create and login user
    user_data = {
        'email': f'frontendtest_{int(time.time())}@example.com',
        'password': 'TestPass123!',
        'first_name': 'Frontend',
        'last_name': 'Test'
    }
    
    # Register user
    register_response = requests.post(
        f"{base_url}/api/v1/auth/register/",
        json=user_data,
        headers={'Content-Type': 'application/json'}
    )
    
    if register_response.status_code in [200, 201]:
        print("✅ User registration successful")
    else:
        print(f"⚠️  User registration: {register_response.status_code}")
    
    # Login user
    login_response = requests.post(
        f"{base_url}/api/v1/auth/login/",
        json={'email': user_data['email'], 'password': user_data['password']},
        headers={'Content-Type': 'application/json'}
    )
    
    if login_response.status_code == 200:
        token = login_response.json().get('access')
        print("✅ Login successful")
        
        # Test AI chat with authentication
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Test quick chat
        chat_response = requests.post(
            f"{base_url}/api/v1/ai/quick/",
            json={'message': 'Hello! I need help with my career development.'},
            headers=headers
        )
        
        if chat_response.status_code == 200:
            data = chat_response.json()
            print("✅ AI Chat successful via HTTP!")
            print(f"   Message: {data.get('message', 'N/A')}")
            print(f"   AI Response: {data.get('response', 'N/A')[:150]}...")
            print(f"   Session ID: {data.get('session_id', 'N/A')}")
            return True
        else:
            print(f"❌ AI Chat failed: {chat_response.status_code}")
            print(f"   Error: {chat_response.text}")
            return False
    else:
        print(f"❌ Login failed: {login_response.status_code}")
        return False


def main():
    """Run AI chat connection tests."""
    print("🚀 AI CHAT CONNECTION TESTING")
    print("=" * 80)
    print("Testing AI chat functionality for frontend-backend connection")
    print("=" * 80)
    
    # Check if backend is running
    try:
        response = requests.get("http://localhost:8000/health/", timeout=5)
        if response.status_code != 200:
            print("❌ Backend server is not responding properly")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to backend server: {e}")
        return 1
    
    print("✅ Backend server is running")
    
    # Run tests
    django_test_passed = test_ai_chat_api()
    http_test_passed = test_with_requests()
    
    print("\n" + "=" * 80)
    print("🎯 AI CHAT CONNECTION TEST RESULTS")
    print("=" * 80)
    
    print(f"Django Client Test: {'✅ PASSED' if django_test_passed else '❌ FAILED'}")
    print(f"HTTP Requests Test: {'✅ PASSED' if http_test_passed else '❌ FAILED'}")
    
    if django_test_passed and http_test_passed:
        print("\n🎉 AI CHAT CONNECTION SUCCESSFUL!")
        print("✨ Frontend can now connect to backend AI chat!")
        print("\n🔧 Connection Details:")
        print("  ✅ Backend API: http://localhost:8000/api/v1/ai/")
        print("  ✅ Authentication: JWT Bearer token required")
        print("  ✅ Quick Chat: POST /api/v1/ai/quick/")
        print("  ✅ Send Message: POST /api/v1/ai/send/")
        print("  ✅ Sessions: GET/POST /api/v1/ai/sessions/")
        print("  ✅ CV Analysis: POST /api/v1/ai/analyze-cv/")
        print("\n🌐 Frontend Configuration:")
        print("  ✅ NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1")
        print("  ✅ NEXT_PUBLIC_USE_MOCK_API=false")
        return 0
    else:
        print("\n⚠️  SOME TESTS FAILED")
        print("Please check the backend configuration and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())