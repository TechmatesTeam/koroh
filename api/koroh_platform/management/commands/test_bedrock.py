"""
Django management command to test AWS Bedrock integration.

Usage:
    python manage.py test_bedrock
    python manage.py test_bedrock --verbose
    python manage.py test_bedrock --model claude-3-haiku
"""

import json
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from koroh_platform.utils.aws_bedrock import bedrock_client
from koroh_platform.utils.ai_services import AIServiceFactory, AIServiceConfig, ModelType
from koroh_platform.utils.bedrock_config import config_manager, get_model_for_task


class Command(BaseCommand):
    help = 'Test AWS Bedrock integration and AI services'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Specific model to test (claude-3-sonnet, claude-3-haiku, titan-lite)',
            default='claude-3-haiku'
        )
        parser.add_argument(
            '--skip-ai-services',
            action='store_true',
            help='Skip AI services testing (only test basic client)',
        )

    def handle(self, *args, **options):
        self.verbosity = options['verbosity']
        self.verbose = options['verbose']
        
        # Map model shortcuts to full model IDs
        model_map = {
            'claude-3-sonnet': 'anthropic.claude-3-sonnet-20240229-v1:0',
            'claude-3-haiku': 'anthropic.claude-3-haiku-20240307-v1:0',
            'claude-3-opus': 'anthropic.claude-3-opus-20240229-v1:0',
            'titan-lite': 'amazon.titan-text-lite-v1',
            'titan-express': 'amazon.titan-text-express-v1',
        }
        
        model_id = model_map.get(options['model'], options['model'])
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting AWS Bedrock Integration Test')
        )
        
        try:
            # Test 1: Configuration
            self._test_configuration()
            
            # Test 2: Client initialization
            self._test_client_initialization()
            
            # Test 3: Basic model invocation
            self._test_model_invocation(model_id)
            
            # Test 4: AI Services (if not skipped)
            if not options['skip_ai_services']:
                self._test_ai_services()
            
            self.stdout.write(
                self.style.SUCCESS('✅ All tests passed! AWS Bedrock integration is working.')
            )
            
        except Exception as e:
            raise CommandError(f'Bedrock integration test failed: {e}')

    def _test_configuration(self):
        """Test configuration loading and validation."""
        self.stdout.write('📋 Testing configuration...')
        
        try:
            config = config_manager.config
            
            if self.verbose:
                self.stdout.write(f'  Region: {config.region.value}')
                self.stdout.write(f'  Default model: {config.default_model}')
                self.stdout.write(f'  Timeout: {config.timeout}s')
                self.stdout.write(f'  Max retries: {config.max_retries}')
            
            # Test model recommendations
            task_models = {
                'text_analysis': get_model_for_task('text_analysis'),
                'content_generation': get_model_for_task('content_generation'),
                'conversation': get_model_for_task('conversation'),
            }
            
            if self.verbose:
                self.stdout.write('  Model recommendations:')
                for task, model in task_models.items():
                    self.stdout.write(f'    {task}: {model}')
            
            # Test available models
            available_models = config_manager.get_available_models()
            self.stdout.write(f'  Available models: {len(available_models)}')
            
            self.stdout.write(self.style.SUCCESS('  ✅ Configuration test passed'))
            
        except Exception as e:
            raise CommandError(f'Configuration test failed: {e}')

    def _test_client_initialization(self):
        """Test Bedrock client initialization."""
        self.stdout.write('🔧 Testing client initialization...')
        
        try:
            if bedrock_client.is_available():
                self.stdout.write(f'  Region: {bedrock_client.region}')
                self.stdout.write(self.style.SUCCESS('  ✅ Client initialization passed'))
            else:
                raise CommandError('Bedrock client is not available')
                
        except Exception as e:
            raise CommandError(f'Client initialization failed: {e}')

    def _test_model_invocation(self, model_id):
        """Test basic model invocation."""
        self.stdout.write(f'🤖 Testing model invocation with {model_id}...')
        
        try:
            test_prompt = "Please respond with exactly: 'Bedrock integration test successful'"
            
            response = bedrock_client.invoke_model(
                model_id=model_id,
                prompt=test_prompt,
                max_tokens=50,
                temperature=0.1
            )
            
            if not response:
                raise CommandError('Model invocation returned no response')
            
            # Extract text from response
            text = bedrock_client.extract_text_from_response(response, model_id)
            
            if not text:
                raise CommandError('Could not extract text from response')
            
            if self.verbose:
                self.stdout.write(f'  Response: {text}')
            
            self.stdout.write(self.style.SUCCESS('  ✅ Model invocation test passed'))
            
        except Exception as e:
            raise CommandError(f'Model invocation test failed: {e}')

    def _test_ai_services(self):
        """Test AI service classes."""
        self.stdout.write('🧠 Testing AI services...')
        
        try:
            # Test service factory
            text_service = AIServiceFactory.create_text_analysis_service()
            content_service = AIServiceFactory.create_content_generation_service()
            recommendation_service = AIServiceFactory.create_recommendation_service()
            conversation_service = AIServiceFactory.create_conversational_service()
            
            self.stdout.write('  ✅ Service factory working')
            
            # Test text analysis service with simple data
            if self.verbose:
                self.stdout.write('  Testing text analysis service...')
                
                test_data = {
                    "text": "John Smith is a senior software engineer with 8 years of experience in Python, Django, and React. He has worked at Google and Microsoft.",
                    "extraction_schema": {
                        "name": "string",
                        "profession": "string",
                        "experience_years": "number",
                        "skills": "array of strings",
                        "companies": "array of strings"
                    }
                }
                
                try:
                    result = text_service.process(test_data)
                    if result:
                        self.stdout.write(f'    Analysis result: {json.dumps(result, indent=2)}')
                        self.stdout.write('    ✅ Text analysis working')
                    else:
                        self.stdout.write('    ⚠️ Text analysis returned empty result')
                except Exception as e:
                    self.stdout.write(f'    ⚠️ Text analysis failed: {e}')
            
            # Test conversational service
            if self.verbose:
                self.stdout.write('  Testing conversational service...')
                
                conversation_data = {
                    "message": "Hello, can you help me with my career?",
                    "context": [],
                    "user_profile": {
                        "name": "Test User",
                        "profession": "Software Engineer"
                    }
                }
                
                try:
                    response = conversation_service.process(conversation_data)
                    if response:
                        self.stdout.write(f'    AI Response: {response[:100]}...')
                        self.stdout.write('    ✅ Conversational AI working')
                    else:
                        self.stdout.write('    ⚠️ Conversational AI returned empty response')
                except Exception as e:
                    self.stdout.write(f'    ⚠️ Conversational AI failed: {e}')
            
            self.stdout.write(self.style.SUCCESS('  ✅ AI services test completed'))
            
        except Exception as e:
            raise CommandError(f'AI services test failed: {e}')

    def _log_verbose(self, message):
        """Log message if verbose mode is enabled."""
        if self.verbose:
            self.stdout.write(f'  {message}')