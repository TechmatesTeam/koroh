#!/usr/bin/env python
"""
Test the specific Qwen model configured in AWS settings
"""

import os
import sys
import django
import json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koroh_platform.settings')
django.setup()

from django.conf import settings


def test_qwen_model():
    """Test the Qwen model specifically configured."""
    print("🧪 Testing Qwen Model Configuration")
    print("=" * 60)
    
    try:
        # Get configuration from settings
        model_id = getattr(settings, 'AWS_BEDROCK_MODEL_ID', 'qwen.qwen3-32b-v1:0')
        max_tokens = getattr(settings, 'AWS_BEDROCK_MAX_TOKENS', 4096)
        temperature = getattr(settings, 'AWS_BEDROCK_TEMPERATURE', 0.7)
        region = getattr(settings, 'AWS_BEDROCK_REGION', 'us-east-1')
        
        print(f"📋 Configuration:")
        print(f"  Model ID: {model_id}")
        print(f"  Max Tokens: {max_tokens}")
        print(f"  Temperature: {temperature}")
        print(f"  Region: {region}")
        
        # Create Bedrock runtime client
        config = Config(
            region_name=region,
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60
        )
        
        client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            config=config
        )
        
        print("\n🚀 Testing Qwen model invocation...")
        
        # Test with a simple prompt
        test_prompt = """Please analyze this CV text and extract the person's name and skills in JSON format:

John Smith
Senior Software Engineer
Email: john@example.com
Skills: Python, JavaScript, React, AWS

Respond with JSON containing 'name' and 'skills' fields."""
        
        # Qwen model format (try different formats)
        # Format 1: OpenAI-style (based on error message)
        body = {
            "messages": [
                {
                    "role": "user",
                    "content": test_prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": 0.9
        }
        
        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        print("✅ Qwen model invocation successful!")
        
        # Parse response
        response_body = json.loads(response['body'].read())
        print(f"📝 Response structure: {list(response_body.keys())}")
        
        # Extract text based on response structure
        if 'results' in response_body:
            content = response_body['results'][0].get('outputText', '')
        elif 'outputText' in response_body:
            content = response_body['outputText']
        elif 'content' in response_body:
            content = response_body['content']
        else:
            content = str(response_body)
        
        print(f"📄 Response content: {content[:200]}...")
        
        # Try to parse as JSON
        try:
            if '{' in content and '}' in content:
                # Extract JSON part
                start = content.find('{')
                end = content.rfind('}') + 1
                json_part = content[start:end]
                parsed_json = json.loads(json_part)
                print("✅ Successfully parsed JSON response")
                print(f"📊 Extracted data: {json.dumps(parsed_json, indent=2)}")
                return True, parsed_json
        except json.JSONDecodeError:
            pass
        
        print("✅ Model responded successfully (non-JSON format)")
        return True, content
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS Client Error: {error_code} - {error_message}")
        return False, None
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None


def main():
    """Test Qwen model configuration."""
    print("🚀 QWEN MODEL CONFIGURATION TEST")
    print("=" * 80)
    
    success, result = test_qwen_model()
    
    if success:
        print("\n🎉 QWEN MODEL TEST SUCCESSFUL!")
        print("✨ The configured Qwen model is working correctly!")
        print("🔄 Ready to run full AI integration tests with real AWS Bedrock")
    else:
        print("\n❌ QWEN MODEL TEST FAILED")
        print("🔧 Please check the model configuration")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())