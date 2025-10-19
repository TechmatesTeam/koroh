#!/usr/bin/env python
"""
Validation script for AWS Bedrock setup.

This script validates the Bedrock integration setup without requiring
actual AWS credentials or making API calls.
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from koroh_platform.utils.aws_bedrock import bedrock_client, BedrockClient
        from koroh_platform.utils.ai_services import (
            AIServiceFactory, BaseAIService, TextAnalysisService,
            ContentGenerationService, RecommendationService, ConversationalAIService,
            ModelType, AIServiceConfig
        )
        from koroh_platform.utils.bedrock_config import (
            config_manager, BedrockConfig, ModelConfig, BedrockConfigManager
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration management."""
    print("\n🔧 Testing configuration...")
    
    try:
        from koroh_platform.utils.bedrock_config import config_manager, get_model_for_task
        
        config = config_manager.config
        print(f"  Region: {config.region.value}")
        print(f"  Default model: {config.default_model}")
        print(f"  Available models: {len(config.models)}")
        
        # Test model recommendations
        tasks = ['text_analysis', 'content_generation', 'conversation']
        for task in tasks:
            model = get_model_for_task(task)
            print(f"  {task}: {model}")
        
        print("✅ Configuration test passed")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_ai_services():
    """Test AI service classes."""
    print("\n🧠 Testing AI services...")
    
    try:
        from koroh_platform.utils.ai_services import AIServiceFactory, AIServiceConfig, ModelType
        
        # Test service creation
        services = {
            'text_analysis': AIServiceFactory.create_text_analysis_service(),
            'content_generation': AIServiceFactory.create_content_generation_service(),
            'recommendation': AIServiceFactory.create_recommendation_service(),
            'conversation': AIServiceFactory.create_conversational_service(),
        }
        
        for name, service in services.items():
            print(f"  {name}: {service.__class__.__name__}")
            print(f"    Model: {service.config.model_type.value}")
            print(f"    Max tokens: {service.config.max_tokens}")
            print(f"    Temperature: {service.config.temperature}")
        
        print("✅ AI services test passed")
        return True
    except Exception as e:
        print(f"❌ AI services test failed: {e}")
        return False

def test_bedrock_client():
    """Test Bedrock client structure."""
    print("\n🔌 Testing Bedrock client...")
    
    try:
        from koroh_platform.utils.aws_bedrock import bedrock_client
        
        print(f"  Client type: {type(bedrock_client).__name__}")
        print(f"  Region: {bedrock_client.region}")
        print(f"  Available: {bedrock_client.is_available()}")
        
        # Test method existence
        methods = ['invoke_model', 'extract_text_from_response', 'is_available']
        for method in methods:
            if hasattr(bedrock_client, method):
                print(f"  ✅ Method {method} exists")
            else:
                print(f"  ❌ Method {method} missing")
                return False
        
        print("✅ Bedrock client structure test passed")
        return True
    except Exception as e:
        print(f"❌ Bedrock client test failed: {e}")
        return False

def test_model_configurations():
    """Test model configurations."""
    print("\n📋 Testing model configurations...")
    
    try:
        from koroh_platform.utils.bedrock_config import config_manager
        
        models = config_manager.get_available_models()
        print(f"  Total models configured: {len(models)}")
        
        for model_id in models[:3]:  # Test first 3 models
            info = config_manager.get_model_info(model_id)
            if info:
                print(f"  {model_id}:")
                print(f"    Family: {info['family']}")
                print(f"    Max tokens: {info['max_tokens']}")
                print(f"    Description: {info['description'][:50]}...")
        
        print("✅ Model configurations test passed")
        return True
    except Exception as e:
        print(f"❌ Model configurations test failed: {e}")
        return False

def main():
    """Run all validation tests."""
    print("AWS BEDROCK SETUP VALIDATION")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("AI Services", test_ai_services),
        ("Bedrock Client", test_bedrock_client),
        ("Model Configurations", test_model_configurations),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("VALIDATION SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 AWS Bedrock setup validation successful!")
        print("The integration is properly configured and ready for use.")
        print("\nNote: Actual AWS API calls will require valid credentials.")
        return 0
    else:
        print("\n⚠️ Some validation tests failed.")
        print("Please check the setup and try again.")
        return 1

if __name__ == "__main__":
    sys.exit(main())