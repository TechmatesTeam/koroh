"""
AI Service Base Classes for Koroh Platform

This module provides base classes and interfaces for different types of AI services
using AWS Bedrock. It implements proper error handling, retry logic, and service
abstraction for various AI tasks.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from dataclasses import dataclass
from django.conf import settings
from .aws_bedrock import bedrock_client

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Enumeration of supported AI model types."""
    CLAUDE_3_SONNET = "anthropic.claude-3-sonnet-20240229-v1:0"
    CLAUDE_3_HAIKU = "anthropic.claude-3-haiku-20240307-v1:0"
    TITAN_TEXT_G1_LARGE = "amazon.titan-text-lite-v1"
    TITAN_TEXT_G1_EXPRESS = "amazon.titan-text-express-v1"


class AIServiceError(Exception):
    """Base exception for AI service errors."""
    pass


class ModelInvocationError(AIServiceError):
    """Exception raised when model invocation fails."""
    pass


class ResponseParsingError(AIServiceError):
    """Exception raised when response parsing fails."""
    pass


@dataclass
class AIServiceConfig:
    """Configuration for AI services."""
    model_type: ModelType
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: int = 30


class BaseAIService(ABC):
    """
    Abstract base class for all AI services.
    
    Provides common functionality for AWS Bedrock integration including:
    - Error handling and retry logic
    - Response parsing
    - Logging and monitoring
    - Configuration management
    """
    
    def __init__(self, config: AIServiceConfig):
        """
        Initialize the AI service with configuration.
        
        Args:
            config: Configuration object for the service
        """
        self.config = config
        self.client = bedrock_client
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _validate_client(self) -> None:
        """Validate that the Bedrock client is properly initialized."""
        if not self.client or not self.client.client:
            raise AIServiceError("AWS Bedrock client is not properly initialized")
    
    def _invoke_model_with_retry(
        self,
        prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Invoke model with retry logic and error handling.
        
        Args:
            prompt: The input prompt for the model
            **kwargs: Additional parameters for model invocation
            
        Returns:
            Model response dictionary
            
        Raises:
            ModelInvocationError: If model invocation fails after retries
        """
        self._validate_client()
        
        last_error = None
        for attempt in range(self.config.max_retries):
            try:
                response = self.client.invoke_model(
                    model_id=self.config.model_type.value,
                    prompt=prompt,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    top_p=self.config.top_p,
                    **kwargs
                )
                
                if response:
                    self.logger.info(f"Model invocation successful on attempt {attempt + 1}")
                    return response
                else:
                    raise ModelInvocationError("Model returned empty response")
                    
            except Exception as e:
                last_error = e
                self.logger.warning(
                    f"Model invocation attempt {attempt + 1} failed: {e}"
                )
                
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay * (2 ** attempt))  # Exponential backoff
                    
        raise ModelInvocationError(
            f"Model invocation failed after {self.config.max_retries} attempts. "
            f"Last error: {last_error}"
        )
    
    def _extract_response_text(self, response: Dict[str, Any]) -> str:
        """
        Extract text from model response.
        
        Args:
            response: Raw model response
            
        Returns:
            Extracted text content
            
        Raises:
            ResponseParsingError: If text extraction fails
        """
        try:
            text = self.client.extract_text_from_response(
                response, 
                self.config.model_type.value
            )
            
            if not text:
                raise ResponseParsingError("Could not extract text from response")
                
            return text.strip()
            
        except Exception as e:
            raise ResponseParsingError(f"Failed to extract response text: {e}")
    
    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Parse JSON response from model text output.
        
        Args:
            text: Text response from model
            
        Returns:
            Parsed JSON data
            
        Raises:
            ResponseParsingError: If JSON parsing fails
        """
        try:
            # Clean up the text - remove markdown code blocks if present
            cleaned_text = text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]
            cleaned_text = cleaned_text.strip()
            
            return json.loads(cleaned_text)
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing failed for text: {text[:200]}...")
            raise ResponseParsingError(f"Failed to parse JSON response: {e}")
    
    @abstractmethod
    def process(self, input_data: Any) -> Any:
        """
        Process input data using the AI service.
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed output data
        """
        pass


class TextAnalysisService(BaseAIService):
    """
    Service for text analysis tasks like CV parsing and content extraction.
    
    Optimized for structured data extraction from unstructured text.
    """
    
    def __init__(self, config: Optional[AIServiceConfig] = None):
        """Initialize text analysis service with appropriate configuration."""
        if config is None:
            config = AIServiceConfig(
                model_type=ModelType.CLAUDE_3_SONNET,
                max_tokens=2000,
                temperature=0.3,  # Lower temperature for consistent structured output
                max_retries=3
            )
        super().__init__(config)
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process text for analysis and extraction.
        
        Args:
            input_data: Dictionary containing 'text' and 'extraction_schema'
            
        Returns:
            Extracted structured data
        """
        text = input_data.get('text', '')
        schema = input_data.get('extraction_schema', {})
        
        if not text:
            raise ValueError("Input text is required for text analysis")
        
        prompt = self._build_analysis_prompt(text, schema)
        response = self._invoke_model_with_retry(prompt)
        response_text = self._extract_response_text(response)
        
        return self._parse_json_response(response_text)
    
    def _build_analysis_prompt(self, text: str, schema: Dict[str, Any]) -> str:
        """Build prompt for text analysis based on schema."""
        schema_description = json.dumps(schema, indent=2) if schema else "general information"
        
        return f"""
        Please analyze the following text and extract structured information in JSON format.
        
        Extraction Schema:
        {schema_description}
        
        Text to analyze:
        {text}
        
        Please respond with valid JSON only, no additional text or formatting.
        Ensure all extracted information is accurate and properly formatted.
        """


class ContentGenerationService(BaseAIService):
    """
    Service for content generation tasks like portfolio creation and summaries.
    
    Optimized for creative and professional content generation.
    """
    
    def __init__(self, config: Optional[AIServiceConfig] = None):
        """Initialize content generation service with appropriate configuration."""
        if config is None:
            config = AIServiceConfig(
                model_type=ModelType.CLAUDE_3_SONNET,
                max_tokens=3000,
                temperature=0.7,  # Higher temperature for creative content
                max_retries=2
            )
        super().__init__(config)
    
    def process(self, input_data: Dict[str, Any]) -> str:
        """
        Generate content based on input data and template.
        
        Args:
            input_data: Dictionary containing 'data', 'template_type', and 'style'
            
        Returns:
            Generated content as string
        """
        data = input_data.get('data', {})
        template_type = input_data.get('template_type', 'professional')
        style = input_data.get('style', 'professional')
        
        if not data:
            raise ValueError("Input data is required for content generation")
        
        prompt = self._build_generation_prompt(data, template_type, style)
        response = self._invoke_model_with_retry(prompt)
        
        return self._extract_response_text(response)
    
    def _build_generation_prompt(
        self, 
        data: Dict[str, Any], 
        template_type: str, 
        style: str
    ) -> str:
        """Build prompt for content generation."""
        return f"""
        Based on the following data, generate professional {template_type} content in {style} style.
        
        Data:
        {json.dumps(data, indent=2)}
        
        Generate engaging, professional content that:
        - Highlights key achievements and skills
        - Uses action-oriented language
        - Is optimized for professional networking
        - Maintains a {style} tone throughout
        - Is well-structured and easy to read
        
        Focus on impact and results rather than just responsibilities.
        """


class RecommendationService(BaseAIService):
    """
    Service for generating recommendations and matches.
    
    Optimized for analyzing user preferences and generating personalized suggestions.
    """
    
    def __init__(self, config: Optional[AIServiceConfig] = None):
        """Initialize recommendation service with appropriate configuration."""
        if config is None:
            config = AIServiceConfig(
                model_type=ModelType.CLAUDE_3_SONNET,
                max_tokens=2000,
                temperature=0.5,  # Balanced temperature for consistent recommendations
                max_retries=2
            )
        super().__init__(config)
    
    def process(self, input_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on user profile and available options.
        
        Args:
            input_data: Dictionary containing 'user_profile' and 'options'
            
        Returns:
            List of recommendations with scores and explanations
        """
        user_profile = input_data.get('user_profile', {})
        options = input_data.get('options', [])
        recommendation_type = input_data.get('type', 'general')
        
        if not user_profile or not options:
            raise ValueError("User profile and options are required for recommendations")
        
        prompt = self._build_recommendation_prompt(user_profile, options, recommendation_type)
        response = self._invoke_model_with_retry(prompt)
        response_text = self._extract_response_text(response)
        
        return self._parse_json_response(response_text)
    
    def _build_recommendation_prompt(
        self, 
        user_profile: Dict[str, Any], 
        options: List[Dict[str, Any]], 
        recommendation_type: str
    ) -> str:
        """Build prompt for generating recommendations."""
        return f"""
        Based on the user profile and available options, provide personalized {recommendation_type} recommendations.
        
        User Profile:
        {json.dumps(user_profile, indent=2)}
        
        Available Options:
        {json.dumps(options[:10], indent=2)}
        
        Analyze the match between user preferences, skills, experience, and each option.
        Return a JSON array of recommendations with match scores (0-100) and detailed explanations.
        
        Format:
        [
            {{
                "option_id": "unique_identifier",
                "match_score": 85,
                "match_reasons": ["reason1", "reason2", "reason3"],
                "recommendation_text": "Detailed explanation of why this is recommended",
                "confidence": "high|medium|low"
            }}
        ]
        
        Sort recommendations by match score (highest first) and include only the top 5 matches.
        """


class ConversationalAIService(BaseAIService):
    """
    Service for conversational AI interactions and chat assistance.
    
    Optimized for maintaining context and providing helpful responses.
    """
    
    def __init__(self, config: Optional[AIServiceConfig] = None):
        """Initialize conversational AI service with appropriate configuration."""
        if config is None:
            config = AIServiceConfig(
                model_type=ModelType.CLAUDE_3_HAIKU,  # Faster model for conversations
                max_tokens=1500,
                temperature=0.8,  # Higher temperature for natural conversations
                max_retries=2
            )
        super().__init__(config)
    
    def process(self, input_data: Dict[str, Any]) -> str:
        """
        Process conversational input and generate response.
        
        Args:
            input_data: Dictionary containing 'message', 'context', and 'user_profile'
            
        Returns:
            AI response as string
        """
        message = input_data.get('message', '')
        context = input_data.get('context', [])
        user_profile = input_data.get('user_profile', {})
        
        if not message:
            raise ValueError("Message is required for conversational AI")
        
        prompt = self._build_conversation_prompt(message, context, user_profile)
        response = self._invoke_model_with_retry(prompt)
        
        return self._extract_response_text(response)
    
    def _build_conversation_prompt(
        self, 
        message: str, 
        context: List[Dict[str, str]], 
        user_profile: Dict[str, Any]
    ) -> str:
        """Build prompt for conversational AI."""
        context_str = ""
        if context:
            context_str = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context[-5:]  # Last 5 messages for context
            ])
        
        profile_str = json.dumps(user_profile, indent=2) if user_profile else "No profile available"
        
        return f"""
        You are Koroh AI, a helpful assistant for the Koroh professional networking platform.
        You help users with career advice, job searching, portfolio creation, and networking.
        
        User Profile:
        {profile_str}
        
        Recent Conversation Context:
        {context_str}
        
        Current User Message: {message}
        
        Provide a helpful, professional, and personalized response. Be concise but informative.
        If the user asks about platform features, explain how they can use Koroh's AI-powered tools.
        """


# Service factory for easy instantiation
class AIServiceFactory:
    """Factory class for creating AI service instances."""
    
    @staticmethod
    def create_text_analysis_service(config: Optional[AIServiceConfig] = None) -> TextAnalysisService:
        """Create a text analysis service instance."""
        return TextAnalysisService(config)
    
    @staticmethod
    def create_content_generation_service(config: Optional[AIServiceConfig] = None) -> ContentGenerationService:
        """Create a content generation service instance."""
        return ContentGenerationService(config)
    
    @staticmethod
    def create_recommendation_service(config: Optional[AIServiceConfig] = None) -> RecommendationService:
        """Create a recommendation service instance."""
        return RecommendationService(config)
    
    @staticmethod
    def create_conversational_service(config: Optional[AIServiceConfig] = None) -> ConversationalAIService:
        """Create a conversational AI service instance."""
        return ConversationalAIService(config)