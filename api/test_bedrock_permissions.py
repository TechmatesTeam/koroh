#!/usr/bin/env python
"""
Test AWS Bedrock permissions and available models
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


def test_bedrock_permissions():
    """Test various Bedrock permissions to understand what's available."""
    print("🔍 Testing AWS Bedrock Permissions")
    print("=" * 60)
    
    # Test different regions
    regions = ['us-east-1', 'us-west-2', 'eu-west-1']
    
    for region in regions:
        print(f"\n📍 Testing region: {region}")
        
        try:
            # Test bedrock client (for listing models)
            bedrock_client = boto3.client(
                'bedrock',
                region_name=region,
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            )
            
            print("  🔍 Testing ListFoundationModels...")
            try:
                response = bedrock_client.list_foundation_models()
                models = response.get('modelSummaries', [])
                print(f"  ✅ Found {len(models)} models")
                
                # Show available models
                text_models = [m for m in models if 'TEXT' in m.get('outputModalities', [])]
                print(f"  📝 Text models available: {len(text_models)}")
                
                for model in text_models[:5]:  # Show first 5
                    print(f"    - {model['modelId']}")
                    
            except ClientError as e:
                print(f"  ❌ ListFoundationModels failed: {e.response['Error']['Code']}")
            
            # Test bedrock-runtime client (for invoking models)
            runtime_client = boto3.client(
                'bedrock-runtime',
                region_name=region,
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            )
            
            print("  🚀 Testing model invocation...")
            
            # Try different models
            models_to_test = [
                "anthropic.claude-3-sonnet-20240229-v1:0",
                "anthropic.claude-3-haiku-20240307-v1:0",
                "amazon.titan-text-lite-v1",
                "amazon.titan-text-express-v1"
            ]
            
            for model_id in models_to_test:
                try:
                    print(f"    Testing {model_id}...")
                    
                    if model_id.startswith("anthropic"):
                        # Claude format
                        body = {
                            "anthropic_version": "bedrock-2023-05-31",
                            "max_tokens": 100,
                            "temperature": 0.1,
                            "messages": [{"role": "user", "content": "Hello, respond with 'Test successful'"}]
                        }
                    else:
                        # Titan format
                        body = {
                            "inputText": "Hello, respond with 'Test successful'",
                            "textGenerationConfig": {
                                "maxTokenCount": 100,
                                "temperature": 0.1
                            }
                        }
                    
                    response = runtime_client.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body),
                        contentType="application/json",
                        accept="application/json"
                    )
                    
                    print(f"    ✅ {model_id} - SUCCESS!")
                    
                    # Parse response
                    response_body = json.loads(response['body'].read())
                    if model_id.startswith("anthropic"):
                        content = response_body.get('content', [{}])[0].get('text', '')
                    else:
                        content = response_body.get('results', [{}])[0].get('outputText', '')
                    
                    print(f"    📝 Response: {content[:50]}...")
                    return True, model_id, region  # Return first successful model
                    
                except ClientError as e:
                    error_code = e.response['Error']['Code']
                    print(f"    ❌ {model_id} - {error_code}")
                    
        except Exception as e:
            print(f"  ❌ Region {region} failed: {e}")
    
    return False, None, None


def test_iam_permissions():
    """Test IAM permissions to understand what the user can do."""
    print("\n🔐 Testing IAM Permissions")
    print("=" * 60)
    
    try:
        iam_client = boto3.client(
            'iam',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
        )
        
        # Get current user
        try:
            user_info = iam_client.get_user()
            username = user_info['User']['UserName']
            print(f"👤 Current user: {username}")
            
            # Get user policies
            try:
                policies = iam_client.list_attached_user_policies(UserName=username)
                print(f"📋 Attached policies: {len(policies['AttachedPolicies'])}")
                for policy in policies['AttachedPolicies']:
                    print(f"  - {policy['PolicyName']}")
            except ClientError as e:
                print(f"❌ Cannot list user policies: {e.response['Error']['Code']}")
            
            # Check for permissions boundary
            try:
                user_details = iam_client.get_user(UserName=username)
                if 'PermissionsBoundary' in user_details['User']:
                    boundary = user_details['User']['PermissionsBoundary']
                    print(f"🚧 Permissions boundary: {boundary['PermissionsBoundaryArn']}")
                else:
                    print("✅ No permissions boundary set")
            except ClientError as e:
                print(f"❌ Cannot check permissions boundary: {e.response['Error']['Code']}")
                
        except ClientError as e:
            print(f"❌ Cannot get user info: {e.response['Error']['Code']}")
            
    except Exception as e:
        print(f"❌ IAM test failed: {e}")


def main():
    """Run permission tests."""
    print("🚀 AWS BEDROCK PERMISSIONS TEST")
    print("=" * 80)
    
    # Test IAM permissions first
    test_iam_permissions()
    
    # Test Bedrock permissions
    success, working_model, working_region = test_bedrock_permissions()
    
    print("\n" + "=" * 80)
    print("🎯 PERMISSION TEST SUMMARY")
    print("=" * 80)
    
    if success:
        print("✅ SUCCESS! Found working Bedrock access")
        print(f"🎯 Working model: {working_model}")
        print(f"📍 Working region: {working_region}")
        print("\n💡 You can now run real Bedrock integration tests!")
    else:
        print("❌ No working Bedrock access found")
        print("\n🔧 Possible issues:")
        print("  - Permissions boundary blocking bedrock:InvokeModel")
        print("  - Model not available in tested regions")
        print("  - IAM policy doesn't include required permissions")
        print("\n📋 Required permissions:")
        print("  - bedrock:InvokeModel")
        print("  - bedrock:ListFoundationModels (optional)")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())