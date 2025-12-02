"""
Django Settings for Bloomberg News Scraper & Search Engine

This module contains all Django configuration settings including:
- Database configuration (PostgreSQL)
- Celery settings for async task processing
- Elasticsearch configuration for search
- REST framework settings
- CORS configuration for frontend integration

Author: Obaidulllah
Created: December 2024
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security Settings
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-change-this-in-production')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Application Definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # For PostgreSQL full-text search
    
    # Third-party apps
    'rest_framework',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',  # Shell plus, model graph, and more
    
    # Local apps
    'apps.news.apps.NewsConfig',  # Using AppConfig for signals
    'apps.scraper',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Custom middleware for logging and performance monitoring
    'apps.news.middleware.RequestCorrelationMiddleware',
    'apps.news.middleware.PerformanceMonitoringMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database Configuration
# Using PostgreSQL for production-ready setup with full-text search support
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'bloomberg_news'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static Files
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default Primary Key Field Type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# =============================================================================
# REST Framework Configuration
# =============================================================================
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
    },
}

# API Documentation Settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Bloomberg News Scraper API',
    'DESCRIPTION': 'API for searching and managing scraped Bloomberg news articles',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# =============================================================================
# CORS Configuration for Frontend
# =============================================================================
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://127.0.0.1:3000'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# Celery Configuration for Async Task Processing
# =============================================================================
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = 'django-db'
CELERY_CACHE_BACKEND = 'django-cache'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes max per task

# Celery Beat Schedule for Periodic Scraping
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# =============================================================================
# Elasticsearch Configuration for Search
# =============================================================================
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': os.getenv('ELASTICSEARCH_HOST', 'localhost:9200'),
    },
}

# =============================================================================
# Scraper Configuration
# =============================================================================
SCRAPER_CONFIG = {
    'DEFAULT_FETCH_ENABLED': os.getenv('SCRAPER_FETCH_ENABLED', 'True').lower() == 'true',
    'FETCH_INTERVAL_SECONDS': int(os.getenv('SCRAPER_INTERVAL', '300')),  # 5 minutes default
    'MAX_ARTICLES_PER_FETCH': int(os.getenv('SCRAPER_MAX_ARTICLES', '50')),
    'USER_AGENT': 'BloombergNewsScraper/1.0 (Educational Purpose)',
}

# =============================================================================
# AI/ML Model Configuration
# =============================================================================
AI_CONFIG = {
    'CATEGORIZATION_MODEL': os.getenv('AI_MODEL', 'facebook/bart-large-mnli'),
    'EMBEDDING_MODEL': os.getenv('EMBEDDING_MODEL', 'all-MiniLM-L6-v2'),
    'CATEGORIES': ['economy', 'market', 'health', 'technology', 'industry'],
}

# =============================================================================
# Logging Configuration (Production-Ready)
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} [{name}:{lineno}] {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
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
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 10 * 1024 * 1024,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django.request': {
            'handlers': ['file', 'console', 'mail_admins'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.scraper': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.news': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'apps.news.middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Create logs directory if it doesn't exist
(BASE_DIR / 'logs').mkdir(exist_ok=True)
