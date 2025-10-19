"""
AWS Bedrock integration utilities for Koroh platform.

This module provides a centralized interface for interacting with
AWS Bedrock foundation models for various AI tasks including:
- CV analysis and parsing
- Portfolio content generation
- Job recommendations
- Peer group matching
"""

import json
import logging
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError, BotoCoreError
from django.conf import settings

logger = logging.getLogger(__name__)


class BedrockClient:
    """
    Centralized client for AWS Bedrock operations.
    
    Provides methods for interacting with different foundation models
    and handles error management, retries, and response parsing.
    """
    
    def __init__(self):
        """Initialize the Bedrock client with AWS credentials."""
        try:
            self.client = boto3.client(
                'bedrock-runtime',
                region_name=settings.AWS_BEDROCK_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            logger.info("AWS Bedrock client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock client: {e}")
            self.client = None
    
    def invoke_model(
        self,
        model_id: str,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Invoke a Bedrock foundation model with the given prompt.
        
        Args:
            model_id: The ID of the foundation model to use
            prompt: The input prompt for the model
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional model-specific parameters
            
        Returns:
            Dict containing the model response or None if failed
        """
        if not self.client:
            logger.error("Bedrock client not initialized")
            return None
        
        try:
            # Prepare the request body based on model type
            if 'claude' in model_id.lower():
                body = {
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                    "top_p": kwargs.get('top_p', 0.9),
                    "stop_sequences": kwargs.get('stop_sequences', ["\n\nHuman:"]),
                }
            elif 'titan' in model_id.lower():
                body = {
                    "inputText": prompt,
                    "textGenerationConfig": {
                        "maxTokenCount": max_tokens,
                        "temperature": temperature,
                        "topP": kwargs.get('top_p', 0.9),
                        "stopSequences": kwargs.get('stop_sequences', []),
                    }
                }
            else:
                # Generic format
                body = {
                    "prompt": prompt,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                }
            
            response = self.client.invoke_model(
                modelId=model_id,
                body=json.dumps(body),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            logger.info(f"Successfully invoked model {model_id}")
            return response_body
            
        except ClientError as e:
            logger.error(f"AWS Bedrock ClientError: {e}")
            return None
        except BotoCoreError as e:
            logger.error(f"AWS Bedrock BotoCoreError: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock model: {e}")
            return None
    
    def extract_text_from_response(
        self,
        response: Dict[str, Any],
        model_id: str
    ) -> Optional[str]:
        """
        Extract generated text from model response.
        
        Args:
            response: The response from invoke_model
            model_id: The model ID used for the request
            
        Returns:
            Extracted text or None if extraction failed
        """
        try:
            if 'claude' in model_id.lower():
                return response.get('completion', '').strip()
            elif 'titan' in model_id.lower():
                results = response.get('results', [])
                if results:
                    return results[0].get('outputText', '').strip()
            else:
                # Try common response formats
                if 'text' in response:
                    return response['text'].strip()
                elif 'completion' in response:
                    return response['completion'].strip()
                elif 'generated_text' in response:
                    return response['generated_text'].strip()
            
            logger.warning(f"Could not extract text from response for model {model_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting text from response: {e}")
            return None


# Global instance for use throughout the application
bedrock_client = BedrockClient()


def analyze_cv_content(cv_text: str) -> Optional[Dict[str, Any]]:
    """
    Analyze CV content using AWS Bedrock to extract structured information.
    
    Args:
        cv_text: The raw text content of the CV
        
    Returns:
        Dict containing extracted CV information or None if failed
    """
    prompt = f"""
    Please analyze the following CV/resume text and extract structured information in JSON format.
    
    Extract the following information:
    - personal_info: name, email, phone, location
    - summary: professional summary or objective
    - skills: list of technical and soft skills
    - experience: list of work experiences with company, role, duration, description
    - education: list of educational qualifications
    - certifications: list of certifications or licenses
    - languages: list of languages spoken
    
    CV Text:
    {cv_text}
    
    Please respond with valid JSON only, no additional text.
    """
    
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"  # Use Claude for structured analysis
    response = bedrock_client.invoke_model(
        model_id=model_id,
        prompt=prompt,
        max_tokens=2000,
        temperature=0.3  # Lower temperature for more consistent structured output
    )
    
    if not response:
        return None
    
    text = bedrock_client.extract_text_from_response(response, model_id)
    if not text:
        return None
    
    try:
        # Parse the JSON response
        cv_data = json.loads(text)
        logger.info("Successfully analyzed CV content")
        return cv_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse CV analysis JSON: {e}")
        return None


def generate_portfolio_content(cv_data: Dict[str, Any], template_style: str = "professional") -> Optional[str]:
    """
    Generate portfolio website content based on CV data.
    
    Args:
        cv_data: Structured CV data from analyze_cv_content
        template_style: Style of portfolio to generate
        
    Returns:
        Generated portfolio content or None if failed
    """
    prompt = f"""
    Based on the following CV data, generate professional portfolio website content in {template_style} style.
    
    Create engaging, professional content including:
    - Hero section with compelling headline
    - About section with professional summary
    - Skills section highlighting key competencies
    - Experience section showcasing achievements
    - Education and certifications
    
    CV Data:
    {json.dumps(cv_data, indent=2)}
    
    Generate content that is professional, engaging, and optimized for career opportunities.
    Focus on achievements and impact rather than just responsibilities.
    """
    
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    response = bedrock_client.invoke_model(
        model_id=model_id,
        prompt=prompt,
        max_tokens=3000,
        temperature=0.7
    )
    
    if not response:
        return None
    
    content = bedrock_client.extract_text_from_response(response, model_id)
    if content:
        logger.info("Successfully generated portfolio content")
    
    return content


def get_job_recommendations(user_profile: Dict[str, Any], available_jobs: List[Dict[str, Any]]) -> Optional[List[Dict[str, Any]]]:
    """
    Generate personalized job recommendations using AI analysis.
    
    Args:
        user_profile: User's profile and preferences
        available_jobs: List of available job postings
        
    Returns:
        List of recommended jobs with match scores or None if failed
    """
    prompt = f"""
    Based on the user profile and available jobs, provide personalized job recommendations.
    
    User Profile:
    {json.dumps(user_profile, indent=2)}
    
    Available Jobs:
    {json.dumps(available_jobs[:10], indent=2)}  # Limit to first 10 for prompt size
    
    Analyze the match between user skills, experience, and preferences with each job.
    Return a JSON array of recommended jobs with match scores (0-100) and reasons.
    
    Format:
    [
        {
            "job_id": "job_id_here",
            "match_score": 85,
            "match_reasons": ["skill match", "experience level", "location preference"],
            "recommendation_text": "Why this job is a good fit"
        }
    ]
    """
    
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    response = bedrock_client.invoke_model(
        model_id=model_id,
        prompt=prompt,
        max_tokens=2000,
        temperature=0.5
    )
    
    if not response:
        return None
    
    text = bedrock_client.extract_text_from_response(response, model_id)
    if not text:
        return None
    
    try:
        recommendations = json.loads(text)
        logger.info(f"Generated {len(recommendations)} job recommendations")
        return recommendations
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse job recommendations JSON: {e}")
        return None