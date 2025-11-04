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
    
    Optimized for maintaining context and providing concise, helpful responses.
    """
    
    def __init__(self, config: Optional[AIServiceConfig] = None):
        """Initialize conversational AI service with appropriate configuration."""
        if config is None:
            config = AIServiceConfig(
                model_type=ModelType.CLAUDE_3_HAIKU,  # Faster model for conversations
                max_tokens=800,  # Reduced from 1500 for more concise responses
                temperature=0.6,  # Reduced from 0.8 for more focused responses
                max_retries=2
            )
        super().__init__(config)
    
    def process(self, input_data: Dict[str, Any]) -> str:
        """
        Process conversational input and generate context-aware response.
        
        Args:
            input_data: Dictionary containing 'message', 'context', 'user_profile', and enhanced context data
            
        Returns:
            AI response as string
        """
        message = input_data.get('message', '')
        context = input_data.get('context', [])
        user_profile = input_data.get('user_profile', {})
        conversation_context = input_data.get('conversation_context', {})
        conversation_memory = input_data.get('conversation_memory', {})
        
        if not message:
            raise ValueError("Message is required for conversational AI")
        
        # Build enhanced prompt with context awareness
        prompt = self._build_enhanced_conversation_prompt(
            message, context, user_profile, conversation_context, conversation_memory
        )
        response = self._invoke_model_with_retry(prompt)
        
        return self._extract_response_text(response)
    
    def _build_enhanced_conversation_prompt(
        self, 
        message: str, 
        context: List[Dict[str, str]], 
        user_profile: Dict[str, Any],
        conversation_context: Dict[str, Any],
        conversation_memory: Dict[str, Any]
    ) -> str:
        """Build enhanced context-aware prompt."""
        # Build conversation history
        context_str = ""
        if context:
            context_str = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context[-4:]
            ])
        
        # Enhanced profile information
        profile_summary = self._create_profile_summary(user_profile)
        
        # Build context awareness section
        context_awareness = self._build_context_awareness_section(conversation_context, conversation_memory)
        
        return f"""You are Koroh AI, a highly context-aware assistant for the Koroh professional networking platform.

ENHANCED CONTEXT-AWARE GUIDELINES:
- Keep responses under 150 words but be contextually intelligent
- Reference and build upon previous conversation topics and user goals
- Acknowledge user's progress and journey
- Use established context to provide more relevant suggestions
- Be direct and actionable while maintaining conversation continuity
- Show understanding of user's evolving needs and preferences

User Profile: {profile_summary}

{context_awareness}

{f"Recent Conversation:\n{context_str}" if context_str else ""}

Current Message: {message}

Provide a contextually intelligent response that demonstrates understanding of our ongoing conversation:"""
    
    def _build_context_awareness_section(
        self, 
        conversation_context: Dict[str, Any], 
        conversation_memory: Dict[str, Any]
    ) -> str:
        """Build the context awareness section for the prompt."""
        sections = []
        
        # Conversation stage and topics
        stage = conversation_context.get('stage', 'initial')
        active_topics = conversation_context.get('active_topics', [])
        if active_topics:
            sections.append(f"Active Topics: {', '.join(active_topics)}")
        
        # User goals and insights
        user_goals = conversation_context.get('user_goals', [])
        if user_goals:
            sections.append(f"User Goals: {', '.join(user_goals)}")
        
        key_insights = conversation_context.get('key_insights', [])
        if key_insights:
            sections.append(f"Key Insights: {', '.join(key_insights)}")
        
        # Recent intents
        recent_intents = conversation_context.get('recent_intents', [])
        if recent_intents:
            sections.append(f"Recent User Intents: {', '.join(recent_intents)}")
        
        # Conversation memory
        summary = conversation_memory.get('summary', '')
        if summary:
            sections.append(f"Conversation Summary: {summary}")
        
        previous_recommendations = conversation_memory.get('previous_recommendations', [])
        if previous_recommendations:
            recent_recs = previous_recommendations[-2:]  # Last 2 recommendations
            sections.append(f"Previous Recommendations: {', '.join(str(rec) for rec in recent_recs)}")
        
        # Follow-up actions
        follow_up_actions = conversation_memory.get('follow_up_actions', [])
        if follow_up_actions:
            sections.append(f"Pending Actions: {', '.join(follow_up_actions)}")
        
        if sections:
            return f"CONVERSATION CONTEXT:\n{chr(10).join(f'- {section}' for section in sections)}\n"
        else:
            return f"CONVERSATION STAGE: {stage.title()}\n"
    
    def _build_conversation_prompt(
        self, 
        message: str, 
        context: List[Dict[str, str]], 
        user_profile: Dict[str, Any]
    ) -> str:
        """Build context-aware prompt for conversational AI with enhanced understanding."""
        # Build conversation history
        context_str = ""
        if context:
            context_str = "\n".join([
                f"{msg['role']}: {msg['content']}" 
                for msg in context[-4:]  # Increased to 4 for better context awareness
            ])
        
        # Enhanced profile information
        profile_summary = self._create_profile_summary(user_profile)
        
        return f"""You are Koroh AI, a context-aware assistant for the Koroh professional networking platform.

CONTEXT-AWARE RESPONSE GUIDELINES:
- Keep responses under 150 words but be contextually relevant
- Reference previous conversation when appropriate
- Build on established topics and user goals
- Use bullet points for lists
- Be direct and actionable
- Acknowledge user's journey and progress
- Focus on immediate next steps that align with conversation flow

User Context: {profile_summary}

{f"Conversation History:\n{context_str}" if context_str else ""}

Current Message: {message}

Provide a contextually aware, brief response that builds on our conversation:"""
    
    def _create_profile_summary(self, user_profile: Dict[str, Any]) -> str:
        """Create a concise profile summary for context."""
        if not user_profile:
            return "New user"
        
        name = user_profile.get('name', 'User')
        industry = user_profile.get('industry', '')
        experience_level = user_profile.get('experience_level', '')
        has_cv = user_profile.get('has_cv', False)
        has_portfolio = user_profile.get('has_portfolio', False)
        
        summary_parts = [name]
        if industry:
            summary_parts.append(f"in {industry}")
        if experience_level:
            summary_parts.append(f"({experience_level})")
        
        status_parts = []
        if has_cv:
            status_parts.append("CV uploaded")
        if has_portfolio:
            status_parts.append("Portfolio created")
        
        if status_parts:
            summary_parts.append(f"- {', '.join(status_parts)}")
        
        return " ".join(summary_parts)


class ConciseChatService(ConversationalAIService):
    """
    Specialized service for ultra-concise chat responses.
    
    Optimized for brief, actionable responses with minimal context.
    """
    
    def __init__(self, config: Optional[AIServiceConfig] = None):
        """Initialize concise chat service with strict limits."""
        if config is None:
            config = AIServiceConfig(
                model_type=ModelType.CLAUDE_3_HAIKU,  # Fastest model
                max_tokens=400,  # Very limited for conciseness
                temperature=0.4,  # Low temperature for focused responses
                max_retries=2
            )
        super().__init__(config)
    
    def _build_conversation_prompt(
        self, 
        message: str, 
        context: List[Dict[str, str]], 
        user_profile: Dict[str, Any]
    ) -> str:
        """Build ultra-concise conversation prompt."""
        # Only use last message for context to keep it minimal
        last_context = ""
        if context:
            last_msg = context[-1]
            last_context = f"Previous: {last_msg.get('content', '')[:50]}..."
        
        # Minimal profile info
        user_name = user_profile.get('name', 'User') if user_profile else 'User'
        
        return f"""You are Koroh AI. Respond in 1-2 sentences max.

User: {user_name}
{last_context}

Current: {message}

Brief response:"""
    
    def process(self, input_data: Dict[str, Any]) -> str:
        """Process input with additional conciseness enforcement."""
        response = super().process(input_data)
        
        # Enforce strict word limit
        words = response.split()
        if len(words) > 50:  # Approximately 1-2 sentences
            response = ' '.join(words[:50]) + '...'
        
        return response


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
    
    @staticmethod
    def create_concise_chat_service(config: Optional[AIServiceConfig] = None) -> 'ConciseChatService':
        """Create a concise chat service instance optimized for brief responses."""
        return ConciseChatService(config)