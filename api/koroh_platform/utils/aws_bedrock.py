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
import os
from typing import Dict, Any, Optional, List
import boto3
from botocore.exceptions import ClientError, BotoCoreError, NoCredentialsError
from botocore.config import Config
from django.conf import settings

logger = logging.getLogger(__name__)


class BedrockClient:
    """
    Centralized client for AWS Bedrock operations.
    
    Provides methods for interacting with different foundation models
    and handles error management, retries, and response parsing.
    Supports both IAM roles and access key authentication.
    """
    
    def __init__(self):
        """Initialize the Bedrock client with AWS credentials or IAM role."""
        self.client = None
        self.region = getattr(settings, 'AWS_BEDROCK_REGION', 'us-east-1')
        
        try:
            # Configure retry and timeout settings
            config = Config(
                region_name=self.region,
                retries={
                    'max_attempts': 3,
                    'mode': 'adaptive'
                },
                max_pool_connections=50,
                read_timeout=60,
                connect_timeout=10
            )
            
            # Try to initialize client with different authentication methods
            self.client = self._initialize_client(config)
            
            if self.client:
                # Test the client with a simple operation
                self._test_client_connection()
                logger.info(f"AWS Bedrock client initialized successfully in region {self.region}")
            else:
                logger.error("Failed to initialize AWS Bedrock client - no valid credentials found")
                
        except Exception as e:
            logger.error(f"Failed to initialize AWS Bedrock client: {e}")
            self.client = None
    
    def _initialize_client(self, config: Config):
        """
        Initialize the Bedrock client using available authentication methods.
        
        Priority order:
        1. Explicit access keys from settings
        2. IAM role (for EC2/ECS/Lambda)
        3. Environment variables
        4. AWS credentials file
        """
        # Method 1: Explicit credentials from Django settings
        access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        
        if access_key and secret_key:
            logger.info("Using explicit AWS credentials from Django settings")
            return boto3.client(
                'bedrock-runtime',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                config=config
            )
        
        # Method 2: IAM role or environment variables (boto3 default chain)
        try:
            logger.info("Attempting to use AWS default credential chain (IAM role/env vars)")
            return boto3.client('bedrock-runtime', config=config)
        except NoCredentialsError:
            logger.warning("No AWS credentials found in default chain")
            return None
    
    def _test_client_connection(self):
        """Test the client connection by listing available models."""
        try:
            # Use bedrock client (not bedrock-runtime) for listing models
            bedrock_client = boto3.client(
                'bedrock',
                region_name=self.region,
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', None),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', None),
            )
            
            # This will raise an exception if credentials are invalid
            response = bedrock_client.list_foundation_models(byOutputModality='TEXT')
            logger.info(f"Successfully connected to AWS Bedrock. Found {len(response.get('modelSummaries', []))} text models")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'UnauthorizedOperation':
                logger.warning("AWS credentials valid but insufficient permissions for listing models")
            else:
                logger.error(f"AWS Bedrock connection test failed: {error_code}")
                raise
        except Exception as e:
            logger.error(f"Unexpected error testing Bedrock connection: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if the Bedrock client is available and properly configured."""
        return self.client is not None
    
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
        if not self.is_available():
            logger.error("Bedrock client not available - check AWS configuration")
            return None
        
        # Validate input parameters
        if not model_id or not prompt:
            logger.error("Model ID and prompt are required")
            return None
        
        if not (0.0 <= temperature <= 1.0):
            logger.warning(f"Temperature {temperature} out of range [0.0, 1.0], clamping")
            temperature = max(0.0, min(1.0, temperature))
        
        if max_tokens <= 0:
            logger.warning(f"Invalid max_tokens {max_tokens}, using default 1000")
            max_tokens = 1000
        
        try:
            # Prepare the request body based on model type
            body = self._prepare_model_body(model_id, prompt, max_tokens, temperature, **kwargs)
            
            logger.debug(f"Invoking model {model_id} with {len(prompt)} character prompt")
            
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
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            if error_code == 'ValidationException':
                logger.error(f"Invalid request parameters for model {model_id}: {error_message}")
            elif error_code == 'ResourceNotFoundException':
                logger.error(f"Model {model_id} not found or not available in region {self.region}")
            elif error_code == 'ThrottlingException':
                logger.error(f"Request throttled for model {model_id}: {error_message}")
            elif error_code == 'AccessDeniedException':
                logger.error(f"Access denied for model {model_id}: {error_message}")
            else:
                logger.error(f"AWS Bedrock ClientError ({error_code}): {error_message}")
            
            return None
            
        except BotoCoreError as e:
            logger.error(f"AWS Bedrock BotoCoreError: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse response JSON: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error invoking Bedrock model {model_id}: {e}")
            return None
    
    def _prepare_model_body(
        self, 
        model_id: str, 
        prompt: str, 
        max_tokens: int, 
        temperature: float, 
        **kwargs
    ) -> Dict[str, Any]:
        """Prepare request body based on model type."""
        model_lower = model_id.lower()
        
        if 'claude' in model_lower:
            # Claude 3 models use the new messages API format
            if 'claude-3' in model_lower:
                return {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": kwargs.get('top_p', 0.9),
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "stop_sequences": kwargs.get('stop_sequences', [])
                }
            else:
                # Legacy Claude models
                return {
                    "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
                    "max_tokens_to_sample": max_tokens,
                    "temperature": temperature,
                    "top_p": kwargs.get('top_p', 0.9),
                    "stop_sequences": kwargs.get('stop_sequences', ["\n\nHuman:"]),
                }
        
        elif 'titan' in model_lower:
            return {
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": max_tokens,
                    "temperature": temperature,
                    "topP": kwargs.get('top_p', 0.9),
                    "stopSequences": kwargs.get('stop_sequences', []),
                }
            }
        
        else:
            # Generic format for other models
            return {
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "top_p": kwargs.get('top_p', 0.9),
            }
    
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
            model_lower = model_id.lower()
            
            if 'claude' in model_lower:
                # Claude 3 models use content array format
                if 'claude-3' in model_lower:
                    content = response.get('content', [])
                    if content and isinstance(content, list):
                        return content[0].get('text', '').strip()
                else:
                    # Legacy Claude models
                    return response.get('completion', '').strip()
            
            elif 'titan' in model_lower:
                results = response.get('results', [])
                if results:
                    return results[0].get('outputText', '').strip()
            
            else:
                # Try common response formats for other models
                for key in ['text', 'completion', 'generated_text', 'output']:
                    if key in response:
                        text = response[key]
                        if isinstance(text, str):
                            return text.strip()
                        elif isinstance(text, list) and text:
                            return str(text[0]).strip()
            
            logger.warning(f"Could not extract text from response for model {model_id}. Response keys: {list(response.keys())}")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting text from response: {e}")
            return None


# Global instance for use throughout the application
bedrock_client = BedrockClient()


def analyze_cv_content(cv_text: str) -> Optional[Dict[str, Any]]:
    """
    Analyze CV content using AWS Bedrock to extract structured information.
    
    This is a legacy function maintained for backward compatibility.
    For new implementations, use the CVAnalysisService directly.
    
    Args:
        cv_text: The raw text content of the CV
        
    Returns:
        Dict containing extracted CV information or None if failed
    """
    try:
        from .cv_analysis_service import analyze_cv_text
        
        # Use the new comprehensive CV analysis service
        result = analyze_cv_text(cv_text)
        
        # Convert to legacy format for backward compatibility
        legacy_format = {
            "personal_info": {
                "name": result.personal_info.name,
                "email": result.personal_info.email,
                "phone": result.personal_info.phone,
                "location": result.personal_info.location,
                "linkedin": result.personal_info.linkedin,
                "website": result.personal_info.website,
                "github": result.personal_info.github
            },
            "summary": result.professional_summary,
            "skills": result.skills + result.technical_skills + result.soft_skills,
            "technical_skills": result.technical_skills,
            "soft_skills": result.soft_skills,
            "experience": [
                {
                    "company": exp.company,
                    "role": exp.position,
                    "duration": exp.duration,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "description": exp.description,
                    "achievements": exp.achievements,
                    "technologies": exp.technologies
                }
                for exp in result.work_experience
            ],
            "education": [
                {
                    "institution": edu.institution,
                    "degree": edu.degree,
                    "field_of_study": edu.field_of_study,
                    "start_date": edu.start_date,
                    "end_date": edu.end_date,
                    "gpa": edu.gpa,
                    "honors": edu.honors
                }
                for edu in result.education
            ],
            "certifications": [
                {
                    "name": cert.name,
                    "issuer": cert.issuer,
                    "issue_date": cert.issue_date,
                    "expiry_date": cert.expiry_date,
                    "credential_id": cert.credential_id
                }
                for cert in result.certifications
            ],
            "languages": result.languages,
            "projects": result.projects,
            "awards": result.awards,
            "volunteer_experience": result.volunteer_experience,
            "interests": result.interests,
            
            # Additional metadata
            "analysis_confidence": result.analysis_confidence,
            "extracted_sections": result.extracted_sections,
            "processing_notes": result.processing_notes
        }
        
        logger.info("Successfully analyzed CV content using enhanced service")
        return legacy_format
        
    except Exception as e:
        logger.error(f"Enhanced CV analysis failed, falling back to basic analysis: {e}")
        
        # Fallback to basic analysis if enhanced service fails
        return _basic_cv_analysis(cv_text)


def _basic_cv_analysis(cv_text: str) -> Optional[Dict[str, Any]]:
    """Basic CV analysis fallback function."""
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
    
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    response = bedrock_client.invoke_model(
        model_id=model_id,
        prompt=prompt,
        max_tokens=2000,
        temperature=0.3
    )
    
    if not response:
        return None
    
    text = bedrock_client.extract_text_from_response(response, model_id)
    if not text:
        return None
    
    try:
        cv_data = json.loads(text)
        logger.info("Successfully completed basic CV analysis")
        return cv_data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse CV analysis JSON: {e}")
        return None


def generate_portfolio_content(cv_data: Dict[str, Any], template_style: str = "professional") -> Optional[str]:
    """
    Generate portfolio website content based on CV data.
    
    This is a legacy function maintained for backward compatibility.
    For new implementations, use the PortfolioGenerationService directly.
    
    Args:
        cv_data: Structured CV data from analyze_cv_content
        template_style: Style of portfolio to generate
        
    Returns:
        Generated portfolio content or None if failed
    """
    try:
        from .portfolio_generation_service import generate_portfolio_from_cv
        from .cv_analysis_service import CVAnalysisResult, PersonalInfo, WorkExperience, Education, Certification
        
        # Convert legacy CV data format to CVAnalysisResult
        personal_info_data = cv_data.get('personal_info', {})
        personal_info = PersonalInfo(
            name=personal_info_data.get('name'),
            email=personal_info_data.get('email'),
            phone=personal_info_data.get('phone'),
            location=personal_info_data.get('location'),
            linkedin=personal_info_data.get('linkedin'),
            website=personal_info_data.get('website'),
            github=personal_info_data.get('github')
        )
        
        # Convert work experience
        work_experience = []
        for exp_data in cv_data.get('experience', []):
            if isinstance(exp_data, dict):
                exp = WorkExperience(
                    company=exp_data.get('company'),
                    position=exp_data.get('role') or exp_data.get('position'),
                    start_date=exp_data.get('start_date'),
                    end_date=exp_data.get('end_date'),
                    duration=exp_data.get('duration'),
                    description=exp_data.get('description'),
                    achievements=exp_data.get('achievements', []),
                    technologies=exp_data.get('technologies', [])
                )
                work_experience.append(exp)
        
        # Convert education
        education = []
        for edu_data in cv_data.get('education', []):
            if isinstance(edu_data, dict):
                edu = Education(
                    institution=edu_data.get('institution'),
                    degree=edu_data.get('degree'),
                    field_of_study=edu_data.get('field_of_study'),
                    start_date=edu_data.get('start_date'),
                    end_date=edu_data.get('end_date'),
                    gpa=edu_data.get('gpa'),
                    honors=edu_data.get('honors')
                )
                education.append(edu)
        
        # Convert certifications
        certifications = []
        for cert_data in cv_data.get('certifications', []):
            if isinstance(cert_data, dict) and cert_data.get('name'):
                cert = Certification(
                    name=cert_data['name'],
                    issuer=cert_data.get('issuer'),
                    issue_date=cert_data.get('issue_date'),
                    expiry_date=cert_data.get('expiry_date'),
                    credential_id=cert_data.get('credential_id')
                )
                certifications.append(cert)
        
        # Create CVAnalysisResult
        cv_result = CVAnalysisResult(
            personal_info=personal_info,
            professional_summary=cv_data.get('summary'),
            skills=cv_data.get('skills', []),
            technical_skills=cv_data.get('technical_skills', []),
            soft_skills=cv_data.get('soft_skills', []),
            work_experience=work_experience,
            education=education,
            certifications=certifications,
            languages=cv_data.get('languages', []),
            projects=cv_data.get('projects', []),
            awards=cv_data.get('awards', []),
            volunteer_experience=cv_data.get('volunteer_experience', []),
            interests=cv_data.get('interests', [])
        )
        
        # Generate portfolio using new service
        portfolio_content = generate_portfolio_from_cv(
            cv_result, 
            template=template_style,
            style="formal"
        )
        
        # Convert to legacy string format
        content_sections = []
        
        if portfolio_content.hero_section:
            hero = portfolio_content.hero_section
            content_sections.append(f"""
# {hero.get('headline', 'Professional Portfolio')}

{hero.get('subheadline', '')}

**{hero.get('value_proposition', '')}**

*{hero.get('call_to_action', '')}*
""")
        
        if portfolio_content.about_section:
            about = portfolio_content.about_section
            content_sections.append(f"""
## About Me

{about.get('main_content', '')}

### Key Highlights
{chr(10).join(f"• {highlight}" for highlight in about.get('key_highlights', []))}

{about.get('personal_touch', '')}
""")
        
        if portfolio_content.experience_section:
            content_sections.append("## Professional Experience\n")
            for exp in portfolio_content.experience_section:
                content_sections.append(f"""
### {exp.get('position', '')} at {exp.get('company', '')}
*{exp.get('duration', '')}*

{exp.get('enhanced_description', exp.get('description', ''))}

**Key Achievements:**
{chr(10).join(f"• {achievement}" for achievement in exp.get('key_achievements', []))}

**Technologies:** {', '.join(exp.get('technologies', []))}
""")
        
        if portfolio_content.skills_section:
            skills = portfolio_content.skills_section
            content_sections.append(f"""
## Skills & Expertise

{skills.get('skills_summary', '')}

### Core Competencies
{chr(10).join(f"• {skill}" for skill in skills.get('top_skills', []))}
""")
        
        if portfolio_content.education_section:
            content_sections.append("## Education\n")
            for edu in portfolio_content.education_section:
                content_sections.append(f"""
### {edu.get('degree', '')} in {edu.get('field', '')}
**{edu.get('institution', '')}** | {edu.get('duration', '')}

{chr(10).join(f"• {detail}" for detail in edu.get('details', []))}
""")
        
        if portfolio_content.contact_section:
            contact = portfolio_content.contact_section
            content_sections.append(f"""
## Get In Touch

{contact.get('call_to_action', 'Let\'s connect and discuss opportunities!')}

**Contact Information:**
- Email: {contact.get('email', '')}
- Phone: {contact.get('phone', '')}
- Location: {contact.get('location', '')}
- LinkedIn: {contact.get('linkedin', '')}
- GitHub: {contact.get('github', '')}
""")
        
        final_content = "\n".join(content_sections)
        logger.info("Successfully generated portfolio content using enhanced service")
        return final_content
        
    except Exception as e:
        logger.error(f"Enhanced portfolio generation failed, falling back to basic generation: {e}")
        
        # Fallback to basic generation
        return _basic_portfolio_generation(cv_data, template_style)


def _basic_portfolio_generation(cv_data: Dict[str, Any], template_style: str) -> Optional[str]:
    """Basic portfolio generation fallback function."""
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
        logger.info("Successfully completed basic portfolio generation")
    
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