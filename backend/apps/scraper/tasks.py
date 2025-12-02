"""
Celery Tasks for Scraper Application

This module defines async tasks for:
- Periodic article scraping
- Article processing and categorization
- Search index updates
- Scraper monitoring

Tasks are executed by Celery workers and scheduled
by Celery Beat for continuous operation.

Author: Obaidulllah
"""

import logging
from datetime import datetime
from typing import List, Optional

from celery import shared_task
from django.utils import timezone
from django.db import transaction

from apps.news.models import Article, Category, ScraperConfig
from apps.news.services import (
    get_category_detector,
    get_keyword_extractor,
    get_entity_extractor,
)
from .bloomberg_scraper import get_scraper, ScrapedArticle

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name='apps.scraper.tasks.check_for_new_articles',
    max_retries=3,
    default_retry_delay=60
)
def check_for_new_articles(self) -> dict:
    """
    Check for new articles from Bloomberg.
    
    This is the main periodic task that:
    1. Checks if fetching is enabled (fetch: True/False)
    2. Scrapes new articles from Bloomberg
    3. Saves raw articles to database
    4. Triggers processing tasks
    
    Returns:
        dict: Summary of articles found and processed
    """
    try:
        # Check if fetching is enabled
        config = ScraperConfig.get_config()
        
        if not config.is_active:
            logger.info("Scraper is disabled (fetch: False)")
            return {'status': 'disabled', 'articles_found': 0}
        
        # Get scraper instance
        # Use mock scraper in development (set DEBUG=True)
        from django.conf import settings
        use_mock = settings.DEBUG
        scraper = get_scraper(use_mock=use_mock)
        
        # Check for new articles
        new_articles = scraper.check_for_new_articles()
        
        if not new_articles:
            logger.info("No new articles found")
            config.last_run_at = timezone.now()
            config.save()
            return {'status': 'success', 'articles_found': 0}
        
        # Save new articles to database
        saved_count = 0
        for article_data in new_articles:
            try:
                saved = save_raw_article(article_data)
                if saved:
                    saved_count += 1
            except Exception as e:
                logger.error(f"Error saving article: {e}")
                continue
        
        # Update config
        config.last_run_at = timezone.now()
        config.articles_fetched_total += saved_count
        if new_articles:
            config.last_article_url = new_articles[0].url
        config.last_error = ''
        config.save()
        
        logger.info(f"Saved {saved_count} new articles")
        
        return {
            'status': 'success',
            'articles_found': len(new_articles),
            'articles_saved': saved_count
        }
        
    except Exception as e:
        logger.error(f"Error in check_for_new_articles: {e}")
        
        # Update error status
        try:
            config = ScraperConfig.get_config()
            config.last_error = str(e)
            config.save()
        except Exception:
            pass
        
        raise self.retry(exc=e)


@shared_task(
    bind=True,
    name='apps.scraper.tasks.process_pending_articles',
    max_retries=3
)
def process_pending_articles(self, batch_size: int = 10) -> dict:
    """
    Process articles that haven't been categorized yet.
    
    This task:
    1. Fetches unprocessed articles
    2. Categorizes them using AI
    3. Extracts keywords and entities
    4. Updates the database
    
    Args:
        batch_size: Number of articles to process per run
        
    Returns:
        dict: Processing summary
    """
    try:
        # Get unprocessed articles
        pending = Article.objects.filter(
            is_processed=False
        ).order_by('created_at')[:batch_size]
        
        if not pending:
            return {'status': 'success', 'processed': 0}
        
        # Initialize AI services
        categorizer = get_category_detector()
        keyword_extractor = get_keyword_extractor()
        entity_extractor = get_entity_extractor()
        
        processed_count = 0
        
        for article in pending:
            try:
                # Combine title and content for analysis
                text = f"{article.title}\n\n{article.content}"
                
                # Categorize
                category_name, confidence = categorizer.categorize_text(text)
                category = Category.objects.filter(name=category_name).first()
                
                # Extract keywords
                keywords = keyword_extractor.extract_keywords(text, max_keywords=10)
                
                # Extract entities
                entities = entity_extractor.extract_entities(text)
                
                # Generate summary if not present
                if not article.summary:
                    # Simple extractive summary: first 2-3 sentences
                    sentences = text.split('.')[:3]
                    article.summary = '. '.join(sentences).strip() + '.'
                
                # Update article
                article.category = category
                article.category_confidence = confidence
                article.keywords = keywords
                article.entities = entities
                article.is_processed = True
                article.save()
                
                processed_count += 1
                logger.debug(f"Processed article: {article.title[:50]}")
                
            except Exception as e:
                logger.error(f"Error processing article {article.id}: {e}")
                continue
        
        logger.info(f"Processed {processed_count} articles")
        
        return {
            'status': 'success',
            'processed': processed_count,
            'pending': Article.objects.filter(is_processed=False).count()
        }
        
    except Exception as e:
        logger.error(f"Error in process_pending_articles: {e}")
        raise self.retry(exc=e)


@shared_task(name='apps.news.tasks.update_search_index')
def update_search_index() -> dict:
    """
    Update PostgreSQL full-text search vectors.
    
    This task updates the search_vector field for articles
    that haven't been indexed yet.
    
    Returns:
        dict: Indexing summary
    """
    try:
        from django.contrib.postgres.search import SearchVector
        
        # Get unindexed articles
        unindexed = Article.objects.filter(
            is_processed=True,
            is_indexed=False
        )
        
        count = unindexed.count()
        
        if count == 0:
            return {'status': 'success', 'indexed': 0}
        
        # Update search vectors
        unindexed.update(
            search_vector=SearchVector('title', weight='A') +
                         SearchVector('summary', weight='B') +
                         SearchVector('content', weight='C')
        )
        
        # Mark as indexed
        unindexed.update(is_indexed=True)
        
        logger.info(f"Indexed {count} articles")
        
        return {'status': 'success', 'indexed': count}
        
    except Exception as e:
        logger.error(f"Error updating search index: {e}")
        return {'status': 'error', 'error': str(e)}


@shared_task(name='apps.scraper.tasks.fetch_article_content')
def fetch_article_content(article_id: str) -> dict:
    """
    Fetch full content for an article.
    
    If an article was saved with only summary from RSS,
    this task fetches the full content.
    
    Args:
        article_id: UUID of the article
        
    Returns:
        dict: Fetch result
    """
    try:
        article = Article.objects.get(id=article_id)
        
        if article.content:
            return {'status': 'skipped', 'reason': 'content exists'}
        
        from django.conf import settings
        use_mock = settings.DEBUG
        scraper = get_scraper(use_mock=use_mock)
        
        content = scraper.fetch_article_content(article.url)
        
        if content:
            article.content = content
            article.save()
            return {'status': 'success'}
        
        return {'status': 'failed', 'reason': 'no content found'}
        
    except Article.DoesNotExist:
        return {'status': 'error', 'reason': 'article not found'}
    except Exception as e:
        logger.error(f"Error fetching content for {article_id}: {e}")
        return {'status': 'error', 'reason': str(e)}


def save_raw_article(article_data: ScrapedArticle) -> bool:
    """
    Save a scraped article to the database.
    
    Handles duplicate detection via URL uniqueness.
    
    Args:
        article_data: ScrapedArticle instance
        
    Returns:
        bool: True if saved, False if duplicate
    """
    try:
        # Check for duplicate
        if Article.objects.filter(url=article_data.url).exists():
            logger.debug(f"Duplicate article: {article_data.url}")
            return False
        
        # Create article
        article = Article.objects.create(
            title=article_data.title,
            content=article_data.content or '',
            summary=article_data.summary,
            url=article_data.url,
            author=article_data.author,
            published_at=article_data.published_at,
            image_url=article_data.image_url,
            is_processed=False,
            is_indexed=False
        )
        
        # If no content, schedule content fetch
        if not article.content:
            fetch_article_content.delay(str(article.id))
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving article: {e}")
        return False


@shared_task(name='apps.scraper.tasks.run_full_scrape')
def run_full_scrape() -> dict:
    """
    Run a full scrape of all categories.
    
    This task is for manual triggering to populate
    the database with initial articles.
    
    Returns:
        dict: Scrape summary
    """
    logger.info("Starting full scrape")
    
    result = check_for_new_articles()
    
    # Trigger processing
    if result.get('articles_saved', 0) > 0:
        process_pending_articles.delay()
    
    return result


@shared_task(
    name='apps.scraper.tasks.update_category_stats',
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3
)
def update_category_stats(category_id: int = None) -> dict:
    """
    Update article counts and statistics for categories.
    
    This task maintains denormalized statistics for performance.
    Called via signals when articles are created/deleted.
    
    Args:
        category_id: Specific category to update, or None for all
        
    Returns:
        dict: Updated statistics
    """
    from django.db.models import Count
    from django.core.cache import cache
    
    try:
        if category_id:
            categories = Category.objects.filter(id=category_id)
        else:
            categories = Category.objects.all()
        
        stats = {}
        for category in categories:
            count = Article.objects.filter(
                category=category,
                is_processed=True
            ).count()
            stats[category.name] = count
            
            # Update cache
            cache.set(
                f"category_{category.id}_count",
                count,
                timeout=3600  # 1 hour
            )
        
        # Invalidate aggregate caches
        cache.delete('all_categories')
        cache.delete('category_stats')
        
        logger.info(f"Updated category stats: {stats}")
        return {'status': 'success', 'stats': stats}
        
    except Exception as e:
        logger.error(f"Error updating category stats: {e}")
        raise


@shared_task(
    name='apps.scraper.tasks.cleanup_old_articles',
    autoretry_for=(Exception,),
    max_retries=2
)
def cleanup_old_articles(days: int = 90) -> dict:
    """
    Remove articles older than specified days.
    
    Implements data retention policy for storage optimization.
    
    Args:
        days: Articles older than this will be deleted
        
    Returns:
        dict: Cleanup summary
    """
    from datetime import timedelta
    
    try:
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Get count before deletion for reporting
        old_articles = Article.objects.filter(
            published_at__lt=cutoff_date
        )
        count = old_articles.count()
        
        if count > 0:
            old_articles.delete()
            logger.info(f"Cleaned up {count} articles older than {days} days")
        
        return {
            'status': 'success',
            'deleted_count': count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_articles: {e}")
        raise


@shared_task(name='apps.scraper.tasks.health_check')
def health_check() -> dict:
    """
    Celery health check task.
    
    Used by Flower and monitoring systems to verify
    worker health and responsiveness.
    
    Returns:
        dict: Health status
    """
    from django.db import connection
    from django.core.cache import cache
    
    status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        status['checks']['database'] = 'ok'
    except Exception as e:
        status['checks']['database'] = f'error: {str(e)}'
        status['status'] = 'degraded'
    
    # Cache check
    try:
        cache.set('health_check', 'ok', timeout=10)
        if cache.get('health_check') == 'ok':
            status['checks']['cache'] = 'ok'
        else:
            status['checks']['cache'] = 'error: read failed'
            status['status'] = 'degraded'
    except Exception as e:
        status['checks']['cache'] = f'error: {str(e)}'
        status['status'] = 'degraded'
    
    # Article stats
    try:
        status['checks']['articles'] = {
            'total': Article.objects.count(),
            'processed': Article.objects.filter(is_processed=True).count(),
            'pending': Article.objects.filter(is_processed=False).count()
        }
    except Exception as e:
        status['checks']['articles'] = f'error: {str(e)}'
    
    return status


@shared_task(name='apps.scraper.tasks.system_health_check')
def system_health_check() -> dict:
    """
    Comprehensive system health check for monitoring.
    
    This task runs periodically to:
    1. Check database connectivity and performance
    2. Verify cache (Redis) is operational
    3. Log system metrics for alerting
    4. Update monitoring dashboard data
    
    Used by:
    - Celery Beat scheduled monitoring
    - External monitoring systems
    - Alerting pipelines
    
    Returns:
        dict: Comprehensive health status with metrics
    """
    import time
    from django.db import connection
    from django.core.cache import cache
    
    status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {},
        'metrics': {},
        'alerts': []
    }
    
    # 1. Database Performance Check
    try:
        start = time.perf_counter()
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM news_article')
            article_count = cursor.fetchone()[0]
        db_latency = (time.perf_counter() - start) * 1000
        
        status['checks']['database'] = {
            'status': 'ok',
            'latency_ms': round(db_latency, 2)
        }
        status['metrics']['articles_total'] = article_count
        
        if db_latency > 200:
            status['alerts'].append({
                'level': 'warning',
                'message': f'High database latency: {db_latency:.1f}ms'
            })
    except Exception as e:
        status['checks']['database'] = {'status': 'error', 'error': str(e)}
        status['status'] = 'unhealthy'
        status['alerts'].append({
            'level': 'critical',
            'message': f'Database connection failed: {e}'
        })
    
    # 2. Cache Performance Check
    try:
        start = time.perf_counter()
        test_key = f'system_health_{timezone.now().timestamp()}'
        cache.set(test_key, 'test', timeout=60)
        result = cache.get(test_key)
        cache.delete(test_key)
        cache_latency = (time.perf_counter() - start) * 1000
        
        if result == 'test':
            status['checks']['cache'] = {
                'status': 'ok',
                'latency_ms': round(cache_latency, 2)
            }
        else:
            status['checks']['cache'] = {'status': 'error', 'error': 'Read/write mismatch'}
            status['status'] = 'degraded'
    except Exception as e:
        status['checks']['cache'] = {'status': 'error', 'error': str(e)}
        status['status'] = 'degraded'
        status['alerts'].append({
            'level': 'warning',
            'message': f'Cache error: {e}'
        })
    
    # 3. Scraper Status Check
    try:
        config = ScraperConfig.get_config()
        status['checks']['scraper'] = {
            'status': 'ok' if config.is_active else 'inactive',
            'is_active': config.is_active,
            'last_run': config.last_run_at.isoformat() if config.last_run_at else None,
            'total_fetched': config.articles_fetched_total
        }
        
        # Check for stale scraper
        if config.last_run_at:
            time_since_last_run = timezone.now() - config.last_run_at
            if time_since_last_run.total_seconds() > 3600:  # 1 hour
                status['alerts'].append({
                    'level': 'warning',
                    'message': f'Scraper has not run in {time_since_last_run.seconds // 60} minutes'
                })
    except Exception as e:
        status['checks']['scraper'] = {'status': 'error', 'error': str(e)}
    
    # 4. Article Processing Metrics
    try:
        processed = Article.objects.filter(is_processed=True).count()
        pending = Article.objects.filter(is_processed=False).count()
        
        status['metrics']['articles_processed'] = processed
        status['metrics']['articles_pending'] = pending
        
        if pending > 100:
            status['alerts'].append({
                'level': 'warning',
                'message': f'{pending} articles pending processing'
            })
    except Exception as e:
        logger.error(f"Error getting article metrics: {e}")
    
    # Log summary
    if status['alerts']:
        for alert in status['alerts']:
            if alert['level'] == 'critical':
                logger.critical(f"HEALTH CHECK ALERT: {alert['message']}")
            else:
                logger.warning(f"HEALTH CHECK: {alert['message']}")
    else:
        logger.info(f"System health check: {status['status']}")
    
    # Store in cache for quick access
    cache.set('system_health_status', status, timeout=300)
    
    return status
