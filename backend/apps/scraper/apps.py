"""
Scraper Application Configuration

Django app configuration for the scraper module.
"""

from django.apps import AppConfig


class ScraperConfig(AppConfig):
    """
    Configuration class for the Scraper application.
    
    This app handles all web scraping functionality including
    Bloomberg news scraping and periodic updates.
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.scraper'
    verbose_name = 'News Scraper'
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        Sets up Celery tasks and signal handlers.
        """
        try:
            import apps.scraper.tasks  # noqa: F401
        except ImportError:
            pass
