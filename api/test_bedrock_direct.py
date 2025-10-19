#!/usr/bin/env python
"""
Direct AWS Bedrock Test - Bypassing Connection Validation

This test directly invokes AWS Bedrock models without the connection validation
that requires ListFoundationModels permission.
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


def test_direct_bedrock_invocation():
    """Test direct Bedrock model invocation without connection validation."""
    print("🧪 Testing Direct AWS Bedrock Model Invocation")
    print("=" * 60)
    
    try:
        # Create Bedrock runtime client directly
        config = Config(
            region_name=getattr(settings, 'AWS_BEDROCK_REGION', 'us-east-1'),
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60,
            connect_timeout=10
        )
        
        client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            config=config
        )
        
        print("✅ Bedrock runtime client created successfully")
        
        # Test with a simple prompt
        test_prompt = """
        Please analyze this CV text and extract the person's name and skills:
        
        John Smith
        Senior Software Engineer
        Email: john@example.com
        Skills: Python, JavaScript, React, AWS
        
        Respond in JSON format with 'name' and 'skills' fields.
        """
        
        # Prepare the request body for Claude 3 Sonnet
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "temperature": 0.3,
            "messages": [
                {
                    "role": "user",
                    "content": test_prompt
                }
            ]
        }
        
        print("🚀 Invoking Claude 3 Sonnet model...")
        
        # Invoke the model
        response = client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        print("✅ Model invocation successful!")
        
        # Parse the response
        response_body = json.loads(response['body'].read())
        
        if 'content' in response_body and response_body['content']:
            content = response_body['content'][0]['text']
            print(f"📝 Model Response: {content[:200]}...")
            
            # Try to parse as JSON
            try:
                parsed_content = json.loads(content)
                print("✅ Response is valid JSON")
                print(f"📊 Extracted Data: {json.dumps(parsed_content, indent=2)}")
                return True, parsed_content
            except json.JSONDecodeError:
                print("⚠️ Response is not JSON, but model invocation worked")
                return True, content
        else:
            print("❌ No content in response")
            return False, None
            
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        print(f"❌ AWS Client Error: {error_code} - {error_message}")
        return False, None
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None


def test_cv_analysis_with_real_bedrock():
    """Test CV analysis using real Bedrock but with direct client."""
    print("\n🧠 Testing CV Analysis with Real Bedrock (Direct)")
    print("=" * 60)
    
    # Sample CV text
    cv_text = """
SARAH JOHNSON
Senior Product Manager
Email: sarah.johnson@email.com
Phone: +1-555-987-6543
Location: Seattle, WA
LinkedIn: linkedin.com/in/sarahjohnson

PROFESSIONAL SUMMARY
Results-driven Product Manager with 5+ years of experience leading cross-functional teams 
to deliver innovative cloud solutions. Proven track record of increasing user engagement 
and driving product growth through data-driven decision making.

TECHNICAL SKILLS
Product Management, Data Analysis, Agile, Python, SQL, Tableau, Azure, AWS

SOFT SKILLS
Leadership, Communication, Strategic Thinking, Problem Solving

WORK EXPERIENCE

Senior Product Manager | Microsoft Corporation | Jan 2021 - Present
• Led product strategy and development for cloud-based solutions
• Increased user engagement by 45% through data-driven product improvements
• Led cross-functional team of 12 engineers and designers
• Launched 3 major product features serving 2M+ users

Product Manager | Amazon Web Services | Jun 2018 - Dec 2020
• Managed product roadmap for AWS developer tools
• Delivered 15+ product releases on schedule
• Reduced customer churn by 30% through improved UX

EDUCATION

Master of Business Administration | Stanford University | 2016 - 2018
• Technology Management focus
• GPA: 3.9/4.0

Bachelor of Science | University of Washington | 2012 - 2016
• Computer Science
• GPA: 3.7/4.0

CERTIFICATIONS
• Certified Product Manager | Product Management Institute | 2020
• AWS Solutions Architect | Amazon Web Services | 2019
"""
    
    try:
        # Create direct Bedrock client
        config = Config(
            region_name=getattr(settings, 'AWS_BEDROCK_REGION', 'us-east-1'),
            retries={'max_attempts': 3, 'mode': 'adaptive'},
            read_timeout=60
        )
        
        client = boto3.client(
            'bedrock-runtime',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            config=config
        )
        
        # Create comprehensive CV analysis prompt
        analysis_prompt = f"""
        Please analyze the following CV text and extract structured information in JSON format.
        
        CV TEXT:
        {cv_text}
        
        Extract the following information in valid JSON format:
        {{
            "personal_info": {{
                "name": "Full name",
                "email": "Email address",
                "phone": "Phone number",
                "location": "Location",
                "linkedin": "LinkedIn URL"
            }},
            "professional_summary": "Professional summary text",
            "technical_skills": ["list", "of", "technical", "skills"],
            "soft_skills": ["list", "of", "soft", "skills"],
            "work_experience": [
                {{
                    "company": "Company name",
                    "position": "Job title",
                    "start_date": "Start date",
                    "end_date": "End date",
                    "description": "Job description",
                    "achievements": ["list", "of", "achievements"]
                }}
            ],
            "education": [
                {{
                    "institution": "School name",
                    "degree": "Degree type",
                    "field": "Field of study",
                    "start_date": "Start date",
                    "end_date": "End date",
                    "gpa": "GPA if mentioned"
                }}
            ],
            "certifications": [
                {{
                    "name": "Certification name",
                    "issuer": "Issuing organization",
                    "date": "Date obtained"
                }}
            ]
        }}
        
        Respond with valid JSON only, no additional text.
        """
        
        # Prepare request body
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4000,
            "temperature": 0.2,
            "messages": [
                {
                    "role": "user",
                    "content": analysis_prompt
                }
            ]
        }
        
        print("🔍 Analyzing CV with AWS Bedrock Claude 3 Sonnet...")
        
        # Invoke the model
        response = client.invoke_model(
            modelId="anthropic.claude-3-sonnet-20240229-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )
        
        # Parse response
        response_body = json.loads(response['body'].read())
        content = response_body['content'][0]['text']
        
        print("✅ CV analysis completed!")
        print(f"📝 Response length: {len(content)} characters")
        
        # Try to parse the JSON response
        try:
            # Clean up the response (remove any markdown formatting)
            cleaned_content = content.strip()
            if cleaned_content.startswith('```json'):
                cleaned_content = cleaned_content[7:]
            if cleaned_content.endswith('```'):
                cleaned_content = cleaned_content[:-3]
            cleaned_content = cleaned_content.strip()
            
            analysis_result = json.loads(cleaned_content)
            
            print("✅ Successfully parsed CV analysis JSON")
            print("\n📊 Analysis Results:")
            print(f"  Name: {analysis_result.get('personal_info', {}).get('name', 'N/A')}")
            print(f"  Email: {analysis_result.get('personal_info', {}).get('email', 'N/A')}")
            print(f"  Technical Skills: {len(analysis_result.get('technical_skills', []))}")
            print(f"  Work Experience: {len(analysis_result.get('work_experience', []))}")
            print(f"  Education: {len(analysis_result.get('education', []))}")
            print(f"  Certifications: {len(analysis_result.get('certifications', []))}")
            
            # Save results
            output_file = "test_portfolio_output/real_cv_analysis.json"
            os.makedirs("test_portfolio_output", exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(analysis_result, f, indent=2)
            
            print(f"💾 Results saved to {output_file}")
            
            return True, analysis_result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {content[:500]}...")
            return False, content
            
    except Exception as e:
        print(f"❌ CV analysis failed: {e}")
        return False, None


def main():
    """Run direct Bedrock tests."""
    print("🚀 DIRECT AWS BEDROCK INTEGRATION TEST")
    print("=" * 80)
    print("Testing real AWS Bedrock without connection validation")
    print("=" * 80)
    
    # Test 1: Basic model invocation
    basic_success, basic_result = test_direct_bedrock_invocation()
    
    # Test 2: CV analysis
    cv_success, cv_result = test_cv_analysis_with_real_bedrock()
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 TEST SUMMARY")
    print("=" * 80)
    
    tests = [
        ("Basic Model Invocation", basic_success),
        ("CV Analysis with Real Bedrock", cv_success)
    ]
    
    passed = 0
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 ALL TESTS PASSED!")
        print("✨ Real AWS Bedrock integration is working!")
        print("🔧 The issue was with the ListFoundationModels permission check")
        print("💡 Model invocation permissions are working correctly")
    else:
        print(f"\n⚠️ {len(tests) - passed} test(s) failed.")
        print("Please check AWS credentials and model access permissions.")
    
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())