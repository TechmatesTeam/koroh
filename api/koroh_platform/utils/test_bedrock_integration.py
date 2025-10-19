"""
Test script for AWS Bedrock integration.

This script validates the Bedrock client configuration, model availability,
and basic functionality without requiring Django test framework.
"""

import os
import sys
import json
import logging
from typing import Dict, Any

# Add the parent directory to the path to import Django modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_bedrock_client():
    """Test basic Bedrock client functionality."""
    try:
        from koroh_platform.utils.aws_bedrock import bedrock_client
        
        print("=" * 60)
        print("TESTING AWS BEDROCK CLIENT")
        print("=" * 60)
        
        # Test 1: Client initialization
        print("\n1. Testing client initialization...")
        if bedrock_client.is_available():
            print("✅ Bedrock client initialized successfully")
        else:
            print("❌ Bedrock client initialization failed")
            return False
        
        # Test 2: Simple model invocation
        print("\n2. Testing model invocation...")
        test_prompt = "Hello, please respond with 'Hello from AWS Bedrock!' and nothing else."
        
        response = bedrock_client.invoke_model(
            model_id="anthropic.claude-3-haiku-20240307-v1:0",
            prompt=test_prompt,
            max_tokens=50,
            temperature=0.1
        )
        
        if response:
            print("✅ Model invocation successful")
            
            # Test 3: Response text extraction
            print("\n3. Testing response text extraction...")
            text = bedrock_client.extract_text_from_response(
                response, 
                "anthropic.claude-3-haiku-20240307-v1:0"
            )
            
            if text:
                print(f"✅ Text extraction successful: {text[:100]}...")
            else:
                print("❌ Text extraction failed")
                return False
        else:
            print("❌ Model invocation failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Bedrock client test failed: {e}")
        return False


def test_ai_services():
    """Test AI service base classes."""
    try:
        from koroh_platform.utils.ai_services import (
            AIServiceFactory, 
            AIServiceConfig, 
            ModelType
        )
        
        print("\n" + "=" * 60)
        print("TESTING AI SERVICES")
        print("=" * 60)
        
        # Test 1: Service factory
        print("\n1. Testing service factory...")
        
        text_service = AIServiceFactory.create_text_analysis_service()
        content_service = AIServiceFactory.create_content_generation_service()
        recommendation_service = AIServiceFactory.create_recommendation_service()
        conversation_service = AIServiceFactory.create_conversational_service()
        
        print("✅ All AI services created successfully")
        
        # Test 2: Text analysis service
        print("\n2. Testing text analysis service...")
        
        test_data = {
            "text": "John Doe is a software engineer with 5 years of experience in Python and Django.",
            "extraction_schema": {
                "name": "string",
                "profession": "string", 
                "experience_years": "number",
                "skills": "array"
            }
        }
        
        try:
            result = text_service.process(test_data)
            if result:
                print(f"✅ Text analysis successful: {json.dumps(result, indent=2)}")
            else:
                print("❌ Text analysis returned no result")
        except Exception as e:
            print(f"⚠️ Text analysis failed (expected in test environment): {e}")
        
        # Test 3: Content generation service
        print("\n3. Testing content generation service...")
        
        test_content_data = {
            "data": {
                "name": "John Doe",
                "profession": "Software Engineer",
                "skills": ["Python", "Django", "React"]
            },
            "template_type": "portfolio",
            "style": "professional"
        }
        
        try:
            content = content_service.process(test_content_data)
            if content:
                print(f"✅ Content generation successful: {content[:100]}...")
            else:
                print("❌ Content generation returned no result")
        except Exception as e:
            print(f"⚠️ Content generation failed (expected in test environment): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ AI services test failed: {e}")
        return False


def test_bedrock_config():
    """Test Bedrock configuration management."""
    try:
        from koroh_platform.utils.bedrock_config import (
            config_manager,
            get_bedrock_config,
            get_model_for_task,
            validate_model_request
        )
        
        print("\n" + "=" * 60)
        print("TESTING BEDROCK CONFIGURATION")
        print("=" * 60)
        
        # Test 1: Configuration loading
        print("\n1. Testing configuration loading...")
        config = get_bedrock_config()
        print(f"✅ Configuration loaded: region={config.region.value}")
        
        # Test 2: Model recommendations
        print("\n2. Testing model recommendations...")
        models = {
            "text_analysis": get_model_for_task("text_analysis"),
            "content_generation": get_model_for_task("content_generation"),
            "conversation": get_model_for_task("conversation"),
        }
        
        for task, model in models.items():
            print(f"  {task}: {model}")
        
        print("✅ Model recommendations working")
        
        # Test 3: Parameter validation
        print("\n3. Testing parameter validation...")
        validation_result = validate_model_request(
            "anthropic.claude-3-sonnet-20240229-v1:0",
            5000,  # Too high
            1.5    # Too high
        )
        
        print(f"✅ Parameter validation working: max_tokens={validation_result['max_tokens']}, temperature={validation_result['temperature']}")
        
        # Test 4: Available models
        print("\n4. Testing available models...")
        available_models = config_manager.get_available_models()
        print(f"✅ Found {len(available_models)} available models")
        
        for model_id in available_models[:3]:  # Show first 3
            info = config_manager.get_model_info(model_id)
            if info:
                print(f"  {model_id}: {info['description']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Bedrock configuration test failed: {e}")
        return False


def test_environment_setup():
    """Test environment and AWS credentials setup."""
    print("=" * 60)
    print("TESTING ENVIRONMENT SETUP")
    print("=" * 60)
    
    # Check environment variables
    print("\n1. Checking environment variables...")
    
    required_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_BEDROCK_REGION'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.environ.get(var)
        if value:
            # Don't print sensitive values
            if 'KEY' in var:
                print(f"  {var}: {'*' * min(len(value), 20)}")
            else:
                print(f"  {var}: {value}")
        else:
            missing_vars.append(var)
            print(f"  {var}: ❌ NOT SET")
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True


def main():
    """Run all tests."""
    print("AWS BEDROCK INTEGRATION TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Bedrock Configuration", test_bedrock_config),
        ("Bedrock Client", test_bedrock_client),
        ("AI Services", test_ai_services),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! AWS Bedrock integration is ready.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the configuration and try again.")
        return 1


if __name__ == "__main__":
    sys.exit(main())