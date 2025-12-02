"""
Django Signals for News Application

This module implements the Observer pattern using Django signals to handle
cross-cutting concerns and maintain loose coupling between components.

Signal Handlers:
- Article lifecycle events (pre_save, post_save, post_delete)
- Search query analytics tracking
- Cache invalidation strategies
- Audit logging for compliance

Design Patterns Used:
- Observer Pattern: Decoupled event handling
- Strategy Pattern: Pluggable processing pipelines
- Decorator Pattern: Signal handler composition

Author: Obaidulllah
Created: December 2024
"""

import logging
from typing import Any, Optional
from datetime import datetime, timedelta

from django.db.models.signals import pre_save, post_save, post_delete, m2m_changed
from django.dispatch import receiver, Signal
from django.core.cache import cache
from django.db import transaction
from django.conf import settings

from .models import Article, Category, SearchQuery

logger = logging.getLogger(__name__)

# =============================================================================
# Custom Signals - Domain Events
# =============================================================================

# Signal fired when article processing is complete
article_processed = Signal()

# Signal fired when search is performed
search_performed = Signal()

# Signal fired when scraping batch completes
scraping_completed = Signal()

# Signal for cache invalidation events
cache_invalidation_required = Signal()


# =============================================================================
# Article Lifecycle Signals
# =============================================================================

@receiver(pre_save, sender=Article)
def article_pre_save_handler(sender, instance: Article, **kwargs) -> None:
    """
    Pre-save handler for Article model.
    
    Responsibilities:
    - Validate article data integrity
    - Normalize text content
    - Generate content hash for deduplication
    - Set default values
    
    Args:
        sender: The model class
        instance: The article instance being saved
        **kwargs: Additional arguments
    """
    # Track if this is a new article
    instance._is_new = instance.pk is None
    
    # Normalize title - ensure consistent formatting
    if instance.title:
        instance.title = instance.title.strip()
        
    # Generate content fingerprint for deduplication
    if instance.content and not hasattr(instance, '_skip_fingerprint'):
        content_hash = hash(instance.content[:500] if instance.content else '')
        instance._content_fingerprint = content_hash
        
    logger.debug(
        f"Article pre-save: {instance.title[:50]}... "
        f"(new={instance._is_new})"
    )


@receiver(post_save, sender=Article)
def article_post_save_handler(
    sender, 
    instance: Article, 
    created: bool, 
    **kwargs
) -> None:
    """
    Post-save handler for Article model.
    
    Responsibilities:
    - Trigger async processing for new articles
    - Update category article counts
    - Invalidate relevant caches
    - Emit domain events
    
    Args:
        sender: The model class
        instance: The article instance that was saved
        created: Whether this is a new instance
        **kwargs: Additional arguments
    """
    # Invalidate category cache when article is saved
    if instance.category_id:
        cache_key = f"category_articles_{instance.category_id}"
        cache.delete(cache_key)
        
    # Invalidate latest articles cache
    cache.delete('latest_articles')
    cache.delete('search_stats')
    
    if created:
        logger.info(
            f"New article created: {instance.title[:50]}... "
            f"[ID: {instance.id}]"
        )
        
        # Update category statistics asynchronously
        _update_category_stats_async(instance.category_id)
        
    else:
        logger.debug(f"Article updated: {instance.id}")
        
    # Emit domain event
    article_processed.send(
        sender=sender,
        article=instance,
        created=created
    )


@receiver(post_delete, sender=Article)
def article_post_delete_handler(sender, instance: Article, **kwargs) -> None:
    """
    Post-delete handler for Article model.
    
    Responsibilities:
    - Clean up related data
    - Update statistics
    - Invalidate caches
    - Log deletion for audit trail
    
    Args:
        sender: The model class
        instance: The article instance that was deleted
        **kwargs: Additional arguments
    """
    logger.info(
        f"Article deleted: {instance.title[:50]}... "
        f"[ID: {instance.id}]"
    )
    
    # Invalidate caches
    if instance.category_id:
        cache.delete(f"category_articles_{instance.category_id}")
    cache.delete('latest_articles')
    cache.delete('search_stats')
    
    # Update category stats
    _update_category_stats_async(instance.category_id)


# =============================================================================
# Category Signals
# =============================================================================

@receiver(post_save, sender=Category)
def category_post_save_handler(
    sender, 
    instance: Category, 
    created: bool, 
    **kwargs
) -> None:
    """
    Post-save handler for Category model.
    
    Args:
        sender: The model class
        instance: The category instance
        created: Whether this is a new instance
        **kwargs: Additional arguments
    """
    # Invalidate categories cache
    cache.delete('all_categories')
    cache.delete('category_stats')
    
    if created:
        logger.info(f"New category created: {instance.name}")


# =============================================================================
# Search Analytics Signals
# =============================================================================

@receiver(post_save, sender=SearchQuery)
def search_query_post_save_handler(
    sender, 
    instance: SearchQuery, 
    created: bool, 
    **kwargs
) -> None:
    """
    Post-save handler for SearchQuery model.
    
    Tracks search analytics for insights:
    - Popular search terms
    - Category detection accuracy
    - Search performance metrics
    
    Args:
        sender: The model class
        instance: The search query instance
        created: Whether this is a new instance
        **kwargs: Additional arguments
    """
    if created:
        # Update search statistics cache
        cache.delete('search_stats')
        cache.delete('popular_searches')
        
        # Log for analytics
        logger.info(
            f"Search performed: '{instance.query}' "
            f"-> {instance.detected_category or 'no category'} "
            f"({instance.results_count} results, {instance.execution_time_ms}ms)"
        )
        
        # Emit search event for further processing
        search_performed.send(
            sender=sender,
            query=instance.query,
            category=instance.detected_category,
            results_count=instance.results_count
        )


# =============================================================================
# Custom Signal Handlers
# =============================================================================

@receiver(article_processed)
def on_article_processed(sender, article: Article, created: bool, **kwargs) -> None:
    """
    Handler for article_processed custom signal.
    
    This demonstrates the Observer pattern for domain events,
    allowing multiple subscribers to react to article processing.
    
    Args:
        sender: The signal sender
        article: The processed article
        created: Whether the article was newly created
        **kwargs: Additional arguments
    """
    if created and article.is_processed:
        # Could trigger notifications, webhooks, or other integrations
        logger.debug(
            f"Article processing complete event: {article.id}"
        )


@receiver(scraping_completed)
def on_scraping_completed(
    sender, 
    articles_count: int, 
    duration_seconds: float, 
    **kwargs
) -> None:
    """
    Handler for scraping batch completion.
    
    Args:
        sender: The signal sender
        articles_count: Number of articles scraped
        duration_seconds: Time taken for scraping
        **kwargs: Additional arguments
    """
    logger.info(
        f"Scraping batch completed: {articles_count} articles "
        f"in {duration_seconds:.2f}s"
    )
    
    # Invalidate all article-related caches
    cache_invalidation_required.send(
        sender=sender,
        cache_keys=['latest_articles', 'search_stats', 'all_categories']
    )


@receiver(cache_invalidation_required)
def on_cache_invalidation(sender, cache_keys: list, **kwargs) -> None:
    """
    Handler for cache invalidation events.
    
    Implements a centralized cache invalidation strategy
    to ensure data consistency across the application.
    
    Args:
        sender: The signal sender
        cache_keys: List of cache keys to invalidate
        **kwargs: Additional arguments
    """
    for key in cache_keys:
        cache.delete(key)
        logger.debug(f"Cache invalidated: {key}")


# =============================================================================
# Helper Functions
# =============================================================================

def _update_category_stats_async(category_id: Optional[int]) -> None:
    """
    Trigger async update of category statistics.
    
    Uses Celery to avoid blocking the main request.
    
    Args:
        category_id: The category ID to update, or None for all
    """
    if category_id:
        try:
            from apps.scraper.tasks import update_category_stats
            transaction.on_commit(
                lambda: update_category_stats.delay(category_id)
            )
        except ImportError:
            # Task not available, skip async update
            pass


# =============================================================================
# Signal Registration Verification
# =============================================================================

def verify_signal_connections() -> dict:
    """
    Verify all signal handlers are properly connected.
    
    Returns:
        dict: Status of signal connections
        
    Usage:
        >>> from apps.news.signals import verify_signal_connections
        >>> status = verify_signal_connections()
        >>> print(status)
    """
    return {
        'article_pre_save': pre_save.has_listeners(Article),
        'article_post_save': post_save.has_listeners(Article),
        'article_post_delete': post_delete.has_listeners(Article),
        'category_post_save': post_save.has_listeners(Category),
        'search_query_post_save': post_save.has_listeners(SearchQuery),
        'custom_article_processed': len(article_processed.receivers) > 0,
        'custom_scraping_completed': len(scraping_completed.receivers) > 0,
        'custom_cache_invalidation': len(cache_invalidation_required.receivers) > 0,
    }
