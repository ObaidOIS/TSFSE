"""
News Application Configuration

Django app configuration for the news module.
This includes signal registration for model lifecycle events.
"""

from django.apps import AppConfig


class NewsConfig(AppConfig):
    """
    Configuration class for the News application.
    
    This app handles all news article related functionality including
    storage, search, and categorization.
    
    Signal Connections:
    - Article pre_save: Content normalization and hash generation
    - Article post_save: Trigger AI categorization and stats update
    - Article post_delete: Update category statistics
    """
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.news'
    verbose_name = 'News Articles'
    
    def ready(self):
        """
        Called when Django starts.
        
        Import signals module to connect signal handlers.
        This ensures signals are registered when the app loads.
        """
        # Import signals to register handlers
        # Using noqa to suppress unused import warning - import has side effects
        from apps.news import signals  # noqa: F401
    
    def ready(self):
        """
        Initialize app when Django starts.
        
        Imports signal handlers and performs any necessary setup.
        """
        try:
            import apps.news.signals  # noqa: F401
        except ImportError:
            pass
