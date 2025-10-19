"""
AWS Bedrock Configuration Management

This module provides configuration management for AWS Bedrock services,
including model selection, parameter validation, and environment-specific settings.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
from django.conf import settings

logger = logging.getLogger(__name__)


class BedrockRegion(Enum):
    """Supported AWS regions for Bedrock."""
    US_EAST_1 = "us-east-1"
    US_WEST_2 = "us-west-2"
    EU_WEST_1 = "eu-west-1"
    AP_SOUTHEAST_1 = "ap-southeast-1"


class ModelFamily(Enum):
    """Bedrock model families."""
    CLAUDE = "claude"
    TITAN = "titan"
    JURASSIC = "jurassic"
    LLAMA = "llama"


@dataclass
class ModelConfig:
    """Configuration for a specific Bedrock model."""
    model_id: str
    family: ModelFamily
    max_tokens: int
    supports_streaming: bool = False
    cost_per_1k_tokens: float = 0.0
    context_window: int = 4096
    description: str = ""


@dataclass
class BedrockConfig:
    """Main configuration for AWS Bedrock integration."""
    region: BedrockRegion = BedrockRegion.US_EAST_1
    default_model: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    enable_logging: bool = True
    log_level: str = "INFO"
    models: Dict[str, ModelConfig] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize default model configurations."""
        if not self.models:
            self.models = self._get_default_models()
    
    def _get_default_models(self) -> Dict[str, ModelConfig]:
        """Get default model configurations."""
        return {
            # Claude 3 Models
            "anthropic.claude-3-sonnet-20240229-v1:0": ModelConfig(
                model_id="anthropic.claude-3-sonnet-20240229-v1:0",
                family=ModelFamily.CLAUDE,
                max_tokens=4096,
                supports_streaming=True,
                cost_per_1k_tokens=0.003,
                context_window=200000,
                description="Claude 3 Sonnet - Balanced performance and speed"
            ),
            "anthropic.claude-3-haiku-20240307-v1:0": ModelConfig(
                model_id="anthropic.claude-3-haiku-20240307-v1:0",
                family=ModelFamily.CLAUDE,
                max_tokens=4096,
                supports_streaming=True,
                cost_per_1k_tokens=0.00025,
                context_window=200000,
                description="Claude 3 Haiku - Fast and cost-effective"
            ),
            "anthropic.claude-3-opus-20240229-v1:0": ModelConfig(
                model_id="anthropic.claude-3-opus-20240229-v1:0",
                family=ModelFamily.CLAUDE,
                max_tokens=4096,
                supports_streaming=True,
                cost_per_1k_tokens=0.015,
                context_window=200000,
                description="Claude 3 Opus - Highest performance"
            ),
            
            # Titan Models
            "amazon.titan-text-lite-v1": ModelConfig(
                model_id="amazon.titan-text-lite-v1",
                family=ModelFamily.TITAN,
                max_tokens=4000,
                supports_streaming=False,
                cost_per_1k_tokens=0.0003,
                context_window=4000,
                description="Titan Text Lite - Lightweight text generation"
            ),
            "amazon.titan-text-express-v1": ModelConfig(
                model_id="amazon.titan-text-express-v1",
                family=ModelFamily.TITAN,
                max_tokens=8000,
                supports_streaming=False,
                cost_per_1k_tokens=0.0008,
                context_window=8000,
                description="Titan Text Express - Enhanced text generation"
            ),
        }
    
    def get_model_config(self, model_id: str) -> Optional[ModelConfig]:
        """Get configuration for a specific model."""
        return self.models.get(model_id)
    
    def get_models_by_family(self, family: ModelFamily) -> List[ModelConfig]:
        """Get all models from a specific family."""
        return [config for config in self.models.values() if config.family == family]
    
    def get_recommended_model(self, task_type: str) -> str:
        """Get recommended model for a specific task type."""
        recommendations = {
            "text_analysis": "anthropic.claude-3-sonnet-20240229-v1:0",
            "content_generation": "anthropic.claude-3-sonnet-20240229-v1:0",
            "conversation": "anthropic.claude-3-haiku-20240307-v1:0",
            "recommendation": "anthropic.claude-3-sonnet-20240229-v1:0",
            "fast_processing": "anthropic.claude-3-haiku-20240307-v1:0",
            "high_quality": "anthropic.claude-3-opus-20240229-v1:0",
            "cost_effective": "amazon.titan-text-lite-v1",
        }
        
        return recommendations.get(task_type, self.default_model)
    
    def validate_model_parameters(
        self, 
        model_id: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, Any]:
        """Validate and adjust model parameters."""
        model_config = self.get_model_config(model_id)
        if not model_config:
            logger.warning(f"Unknown model {model_id}, using default validation")
            model_config = ModelConfig(
                model_id=model_id,
                family=ModelFamily.CLAUDE,
                max_tokens=4096
            )
        
        # Validate and adjust max_tokens
        if max_tokens > model_config.max_tokens:
            logger.warning(
                f"max_tokens {max_tokens} exceeds model limit {model_config.max_tokens}, "
                f"adjusting to {model_config.max_tokens}"
            )
            max_tokens = model_config.max_tokens
        
        # Validate temperature
        if not (0.0 <= temperature <= 1.0):
            logger.warning(f"Temperature {temperature} out of range, clamping to [0.0, 1.0]")
            temperature = max(0.0, min(1.0, temperature))
        
        return {
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model_config": model_config
        }


class BedrockConfigManager:
    """Manager for Bedrock configuration with environment-specific settings."""
    
    def __init__(self):
        """Initialize configuration manager."""
        self._config = None
        self._load_config()
    
    def _load_config(self):
        """Load configuration from Django settings and environment."""
        try:
            # Get region from settings
            region_str = getattr(settings, 'AWS_BEDROCK_REGION', 'us-east-1')
            try:
                region = BedrockRegion(region_str)
            except ValueError:
                logger.warning(f"Invalid region {region_str}, using us-east-1")
                region = BedrockRegion.US_EAST_1
            
            # Get other settings
            default_model = getattr(
                settings, 
                'AWS_BEDROCK_DEFAULT_MODEL', 
                'anthropic.claude-3-sonnet-20240229-v1:0'
            )
            
            timeout = getattr(settings, 'AWS_BEDROCK_TIMEOUT', 30)
            max_retries = getattr(settings, 'AWS_BEDROCK_MAX_RETRIES', 3)
            retry_delay = getattr(settings, 'AWS_BEDROCK_RETRY_DELAY', 1.0)
            enable_logging = getattr(settings, 'AWS_BEDROCK_ENABLE_LOGGING', True)
            log_level = getattr(settings, 'AWS_BEDROCK_LOG_LEVEL', 'INFO')
            
            self._config = BedrockConfig(
                region=region,
                default_model=default_model,
                timeout=timeout,
                max_retries=max_retries,
                retry_delay=retry_delay,
                enable_logging=enable_logging,
                log_level=log_level
            )
            
            logger.info(f"Bedrock configuration loaded: region={region.value}, default_model={default_model}")
            
        except Exception as e:
            logger.error(f"Failed to load Bedrock configuration: {e}")
            # Use default configuration
            self._config = BedrockConfig()
    
    @property
    def config(self) -> BedrockConfig:
        """Get the current configuration."""
        if self._config is None:
            self._load_config()
        return self._config
    
    def reload_config(self):
        """Reload configuration from settings."""
        self._load_config()
    
    def get_model_for_task(self, task_type: str) -> str:
        """Get the recommended model for a specific task."""
        return self.config.get_recommended_model(task_type)
    
    def validate_request_parameters(
        self, 
        model_id: str, 
        max_tokens: int, 
        temperature: float
    ) -> Dict[str, Any]:
        """Validate request parameters for a model."""
        return self.config.validate_model_parameters(model_id, max_tokens, temperature)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model IDs."""
        return list(self.config.models.keys())
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a model."""
        model_config = self.config.get_model_config(model_id)
        if not model_config:
            return None
        
        return {
            "model_id": model_config.model_id,
            "family": model_config.family.value,
            "max_tokens": model_config.max_tokens,
            "supports_streaming": model_config.supports_streaming,
            "cost_per_1k_tokens": model_config.cost_per_1k_tokens,
            "context_window": model_config.context_window,
            "description": model_config.description
        }


# Global configuration manager instance
config_manager = BedrockConfigManager()


def get_bedrock_config() -> BedrockConfig:
    """Get the global Bedrock configuration."""
    return config_manager.config


def get_model_for_task(task_type: str) -> str:
    """Get recommended model for a task type."""
    return config_manager.get_model_for_task(task_type)


def validate_model_request(
    model_id: str, 
    max_tokens: int, 
    temperature: float
) -> Dict[str, Any]:
    """Validate model request parameters."""
    return config_manager.validate_request_parameters(model_id, max_tokens, temperature)