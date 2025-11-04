"""
Django settings for koroh_platform project.

This configuration includes all required integrations for the Koroh platform:
- PostgreSQL database
- Redis cache and sessions
- MeiliSearch integration
- AWS Bedrock configuration
- Celery task queue
- JWT authentication
- CORS headers for frontend communication
"""

import os
from pathlib import Path
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Initialize environment variables
env = environ.Env(
    DEBUG=(bool, True),
    DJANGO_SECRET_KEY=(str, 'django-insecure-change-in-production'),
    DJANGO_ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1', 'api']),
    DJANGO_CORS_ALLOWED_ORIGINS=(list, ['http://localhost:3000', 'http://127.0.0.1:3000']),
)

# Read environment variables from .env file in project root
environ.Env.read_env(os.path.join(BASE_DIR.parent, '.env'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS')

# Enhanced Security Configuration
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Enhanced SSL/TLS Security
SECURE_SSL_REDIRECT = not DEBUG
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https') if not DEBUG else None
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Session Security
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True

# CSRF Protection
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = env('DJANGO_CORS_ALLOWED_ORIGINS')
CSRF_FAILURE_VIEW = 'koroh_platform.views.csrf_failure'

# Additional Security Headers
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_PERMISSIONS_POLICY = {
    'geolocation': [],
    'microphone': [],
    'camera': [],
    'payment': [],
    'usb': [],
}

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://fonts.googleapis.com")
CSP_FONT_SRC = ("'self'", "https://fonts.gstatic.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_CONNECT_SRC = ("'self'", "https://api.koroh.dev", "wss://api.koroh.dev")
CSP_FRAME_ANCESTORS = ("'none'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'django_filters',
    'django_prometheus',
]

LOCAL_APPS = [
    'authentication',
    'profiles',
    'companies',
    'jobs',
    'peer_groups',
    'ai_chat',
]

# Add channels for WebSocket support
THIRD_PARTY_APPS.append('channels')

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS
MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    'koroh_platform.security.SecurityValidationMiddleware',
    'koroh_platform.security.AuthenticationSecurityMiddleware',
    'koroh_platform.security.APISecurityMiddleware',
    'koroh_platform.middleware.SecurityHeadersMiddleware',
    'koroh_platform.middleware.PerformanceMiddleware',
    'koroh_platform.middleware.RateLimitMiddleware',
    'koroh_platform.middleware.CacheOptimizationMiddleware',
    'koroh_platform.middleware.CompressionMiddleware',
    'koroh_platform.middleware.DatabaseOptimizationMiddleware',
    'koroh_platform.middleware.CORSMiddleware',
    'koroh_platform.utils.logging.LoggingMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

ROOT_URLCONF = 'koroh_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'koroh_platform.wsgi.application'
ASGI_APPLICATION = 'koroh_platform.asgi.application'

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL', default='redis://localhost:6379/3')],
            'capacity': 1500,
            'expiry': 60,
        },
    },
}

# Database Configuration
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
        'OPTIONS': {
            'connect_timeout': 60,
        },
        'CONN_MAX_AGE': 600,
        'CONN_HEALTH_CHECKS': True,
        'CONN_MAX_AGE': 600,  # 10 minutes
        'CONN_HEALTH_CHECKS': True,
    }
}

# Cache Configuration (Redis)
REDIS_URL = env('REDIS_URL', default='redis://localhost:6379/0')
CACHES = {
    'default': {
        'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'IGNORE_EXCEPTIONS': True,
        },
        'TIMEOUT': 300,  # 5 minutes default
        'KEY_PREFIX': 'koroh',
        'VERSION': 1,
    },
    'sessions': {
        'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 3600,  # 1 hour
        'KEY_PREFIX': 'koroh_session',
    },
    'api_cache': {
        'BACKEND': 'django_prometheus.cache.backends.redis.RedisCache',
        'LOCATION': env('REDIS_URL', default='redis://localhost:6379/2'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'TIMEOUT': 600,  # 10 minutes
        'KEY_PREFIX': 'koroh_api',
    }
}

# Session Configuration (Redis)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'
SESSION_COOKIE_AGE = 3600  # 1 hour for security

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'authentication.User'

# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FileUploadParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour',
        'login': '10/min',
        'register': '5/hour',
        'ai_service': '50/min',
        'file_upload': '10/hour',
    },
    'EXCEPTION_HANDLER': 'koroh_platform.utils.exception_handler.custom_exception_handler',
}

# JWT Configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = env('DJANGO_CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Only in development

# Enhanced CORS Security
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.koroh\.dev$",  # Production subdomains
] if not DEBUG else []

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

CORS_EXPOSE_HEADERS = [
    'x-response-time',
    'x-cache',
    'x-db-queries',
]

CORS_PREFLIGHT_MAX_AGE = 86400  # 24 hours

# AWS Configuration
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')
AWS_DEFAULT_REGION = env('AWS_DEFAULT_REGION', default='us-east-1')
AWS_BEDROCK_REGION = env('AWS_BEDROCK_REGION', default='us-east-1')

# AWS Bedrock Specific Configuration
AWS_BEDROCK_DEFAULT_MODEL = env('AWS_BEDROCK_DEFAULT_MODEL', default='anthropic.claude-3-sonnet-20240229-v1:0')
AWS_BEDROCK_TIMEOUT = env('AWS_BEDROCK_TIMEOUT', default=30)
AWS_BEDROCK_MAX_RETRIES = env('AWS_BEDROCK_MAX_RETRIES', default=3)
AWS_BEDROCK_RETRY_DELAY = env('AWS_BEDROCK_RETRY_DELAY', default=1.0)
AWS_BEDROCK_ENABLE_LOGGING = env('AWS_BEDROCK_ENABLE_LOGGING', default=True)
AWS_BEDROCK_LOG_LEVEL = env('AWS_BEDROCK_LOG_LEVEL', default='INFO')

# AI Chat Response Configuration
AI_CHAT_CONCISE_MODE = env('AI_CHAT_CONCISE_MODE', default=True)
AI_CHAT_MAX_RESPONSE_WORDS = env('AI_CHAT_MAX_RESPONSE_WORDS', default=50)
AI_CHAT_MAX_RESPONSE_CHARS = env('AI_CHAT_MAX_RESPONSE_CHARS', default=500)
AI_CHAT_ENABLE_CONTEXT_OPTIMIZATION = env('AI_CHAT_ENABLE_CONTEXT_OPTIMIZATION', default=True)

# MeiliSearch Configuration
MEILISEARCH_URL = env('MEILISEARCH_URL', default='http://localhost:7700')
MEILISEARCH_MASTER_KEY = env('MEILISEARCH_MASTER_KEY', default='')

# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default=REDIS_URL)
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Email Configuration (MailHog for development)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='localhost')
EMAIL_PORT = env('EMAIL_PORT', default=1025)
EMAIL_USE_TLS = env('EMAIL_USE_TLS', default=False)
EMAIL_USE_SSL = env('EMAIL_USE_SSL', default=False)
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = 'noreply@koroh.com'

# Frontend URL for email links
FRONTEND_URL = env('FRONTEND_URL', default='http://localhost:3000')
SUPPORT_EMAIL = env('SUPPORT_EMAIL', default='support@koroh.com')

# File Upload Configuration
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Logging Configuration
import logging.config
import os

# Ensure logs directory exists
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
        'json': {
            '()': 'koroh_platform.utils.logging.JSONFormatter',
        },
        'security': {
            'format': 'SECURITY {levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'django.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'errors.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'security_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'security.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 10,
            'formatter': 'security',
        },
        'ai_services_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'ai_services.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'celery_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'celery.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'performance_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOGS_DIR / 'performance.log',
            'maxBytes': 50 * 1024 * 1024,  # 50MB
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': True,
        },
        'django.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'koroh_platform': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'koroh_platform.ai_services': {
            'handlers': ['ai_services_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'koroh_platform.celery': {
            'handlers': ['celery_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'koroh_platform.performance': {
            'handlers': ['performance_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'koroh_platform.security': {
            'handlers': ['security_file'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['celery_file'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery.task': {
            'handlers': ['celery_file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
