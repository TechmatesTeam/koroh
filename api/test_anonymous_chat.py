#!/usr/bin/env python
"""
Test Anonymous Chat Functionality

Tests the anonymous chat feature with message limits.
"""

import requests
import json

def test_anonymous_chat():
    """Test anonymous chat functionality."""
    print("🤖 Testing Anonymous Chat Functionality")
    print("=" * 50)
    
    base_url = "http://localhost:8000"
    session = requests.Session()
    
    # Test 1: Send first anonymous message
    print("\n1. Testing first anonymous message...")
    response = session.post(f"{base_url}/api/v1/ai/anonymous/", json={
        "message": "Hello, I'm looking for career advice!"
    })
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Response: {data.get('response', '')[:100]}...")
        print(f"Messages remaining: {data.get('messages_remaining')}")
        print(f"Session ID: {data.get('session_id')}")
        session_id = data.get('session_id')
    else:
        print(f"Error: {response.text}")
        return
    
    # Test 2: Send multiple messages to test limit
    for i in range(2, 6):
        print(f"\n{i}. Testing message {i}...")
        response = session.post(f"{base_url}/api/v1/ai/anonymous/", json={
            "message": f"This is message number {i}. Can you help me with job searching?",
            "session_id": session_id
        })
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Messages remaining: {data.get('messages_remaining')}")
            print(f"Registration prompt: {data.get('registration_prompt')}")
        else:
            print(f"Error: {response.text}")
    
    # Test 3: Try to exceed limit
    print(f"\n6. Testing limit exceeded...")
    response = session.post(f"{base_url}/api/v1/ai/anonymous/", json={
        "message": "This should exceed the limit",
        "session_id": session_id
    })
    
    print(f"Status: {response.status_code}")
    if response.status_code == 429:
        data = response.json()
        print(f"Limit exceeded message: {data.get('message')}")
        print("✅ Limit enforcement working correctly!")
    else:
        print(f"Unexpected response: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎯 Anonymous Chat Test Complete")


if __name__ == "__main__":
    test_anonymous_chat()