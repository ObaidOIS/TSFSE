"""
Celery Configuration for Bloomberg News Scraper

This module configures Celery for async task processing,
including periodic tasks for scraping and news processing.

Features:
- Periodic news scraping (every 5 minutes)
- Article processing pipeline
- Scheduled maintenance tasks
- System health monitoring

Author: Obaidulllah
"""

import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create the Celery application instance
app = Celery('bloomberg_scraper')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# =============================================================================
# Celery Beat Schedule (Periodic Tasks)
# =============================================================================
app.conf.beat_schedule = {
    # Primary Scraping Tasks
    'check-for-new-articles': {
        'task': 'apps.scraper.tasks.check_for_new_articles',
        'schedule': 300.0,  # Every 5 minutes
        'options': {'queue': 'scraper'},
    },
    'process-pending-articles': {
        'task': 'apps.scraper.tasks.process_pending_articles',
        'schedule': 60.0,  # Every minute
        'options': {'queue': 'processing'},
    },
    'update-search-index': {
        'task': 'apps.news.tasks.update_search_index',
        'schedule': 120.0,  # Every 2 minutes
        'options': {'queue': 'indexing'},
    },
    
    # Maintenance Tasks (Senior-level additions)
    'update-category-stats': {
        'task': 'apps.scraper.tasks.update_category_stats',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
        'options': {'queue': 'default'},
    },
    'generate-trending-topics': {
        'task': 'apps.scraper.tasks.generate_trending_topics',
        'schedule': crontab(minute=0, hour='*/6'),  # Every 6 hours
        'options': {'queue': 'default'},
    },
    'cleanup-old-articles': {
        'task': 'apps.scraper.tasks.cleanup_old_articles',
        'schedule': crontab(minute=0, hour=3),  # Daily at 3 AM
        'args': [30],  # Keep articles for 30 days
        'options': {'queue': 'default'},
    },
    
    # Health Check (runs every 5 minutes, logs to monitoring)
    'system-health-check': {
        'task': 'apps.scraper.tasks.system_health_check',
        'schedule': 300.0,  # Every 5 minutes
        'options': {'queue': 'default'},
    },
}

# Configure task queues
app.conf.task_queues = {
    'default': {},
    'scraper': {},
    'processing': {},
    'indexing': {},
    'maintenance': {},
}

app.conf.task_default_queue = 'default'

# Task routing
app.conf.task_routes = {
    'apps.scraper.tasks.check_for_new_articles': {'queue': 'scraper'},
    'apps.scraper.tasks.process_pending_articles': {'queue': 'processing'},
    'apps.news.tasks.*': {'queue': 'indexing'},
    'apps.scraper.tasks.cleanup_*': {'queue': 'maintenance'},
    'apps.scraper.tasks.update_*': {'queue': 'maintenance'},
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """
    Debug task for testing Celery configuration.
    
    This task prints the current request information for debugging purposes.
    """
    print(f'Request: {self.request!r}')
