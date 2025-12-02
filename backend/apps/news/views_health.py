"""
Health Check and Metrics API Views

This module provides production-ready endpoints for:
- Health checks (for load balancers and orchestrators)
- Prometheus-style metrics
- System diagnostics

These endpoints are critical for:
- Kubernetes liveness/readiness probes
- Load balancer health checks
- Monitoring and alerting systems

Author: Obaidulllah
Created: December 2024
"""

import time
from datetime import timedelta
from typing import Any, Dict

from django.db import connection
from django.core.cache import cache
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.news.models import Article, Category, ScraperConfig


# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request) -> Response:
    """
    Lightweight health check endpoint.
    
    Used by:
    - Docker HEALTHCHECK
    - Kubernetes liveness probes
    - Load balancers
    
    Returns:
        200: Service is healthy
        503: Service is unhealthy
    """
    checks = {}
    is_healthy = True
    
    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = 'ok'
    except Exception as e:
        checks['database'] = f'error: {str(e)}'
        is_healthy = False
    
    # Cache check
    try:
        cache.set('health_check', 'ok', timeout=5)
        if cache.get('health_check') == 'ok':
            checks['cache'] = 'ok'
        else:
            checks['cache'] = 'error: read/write mismatch'
            is_healthy = False
    except Exception as e:
        checks['cache'] = f'error: {str(e)}'
        is_healthy = False
    
    response_data = {
        'status': 'healthy' if is_healthy else 'unhealthy',
        'timestamp': timezone.now().isoformat(),
        'checks': checks
    }
    
    return Response(
        response_data,
        status=status.HTTP_200_OK if is_healthy else status.HTTP_503_SERVICE_UNAVAILABLE
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def readiness_check(request) -> Response:
    """
    Readiness check endpoint.
    
    More comprehensive than health check.
    Used by Kubernetes readiness probes.
    
    Checks:
    - Database connectivity and query performance
    - Cache availability
    - Celery worker availability (optional)
    
    Returns:
        200: Service is ready to accept traffic
        503: Service is not ready
    """
    checks = {}
    is_ready = True
    
    # Database connectivity and performance
    try:
        start = time.perf_counter()
        with connection.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM news_article')
            row_count = cursor.fetchone()[0]
        latency_ms = (time.perf_counter() - start) * 1000
        
        checks['database'] = {
            'status': 'ok',
            'latency_ms': round(latency_ms, 2),
            'articles': row_count
        }
        
        if latency_ms > 500:
            checks['database']['status'] = 'slow'
            is_ready = False
    except Exception as e:
        checks['database'] = {'status': 'error', 'message': str(e)}
        is_ready = False
    
    # Cache check with timing
    try:
        start = time.perf_counter()
        cache.set('readiness_test', timezone.now().isoformat(), timeout=10)
        cache.get('readiness_test')
        cache.delete('readiness_test')
        latency_ms = (time.perf_counter() - start) * 1000
        
        checks['cache'] = {
            'status': 'ok',
            'latency_ms': round(latency_ms, 2)
        }
    except Exception as e:
        checks['cache'] = {'status': 'error', 'message': str(e)}
        is_ready = False
    
    response_data = {
        'status': 'ready' if is_ready else 'not_ready',
        'timestamp': timezone.now().isoformat(),
        'checks': checks
    }
    
    return Response(
        response_data,
        status=status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    )


# =============================================================================
# METRICS ENDPOINTS
# =============================================================================

@api_view(['GET'])
@permission_classes([AllowAny])
def metrics(request) -> Response:
    """
    Prometheus-compatible metrics endpoint.
    
    Provides:
    - Article counts by category
    - Scraper statistics
    - Search query metrics
    - System performance indicators
    
    Format: JSON (can be adapted for Prometheus format)
    
    Example response:
    {
        "articles": {
            "total": 150,
            "by_category": {...},
            "by_date": {...}
        },
        "scraper": {
            "total_fetched": 500,
            "last_run": "2024-01-15T10:30:00Z"
        }
    }
    """
    metrics_data: Dict[str, Any] = {}
    
    # Article metrics
    try:
        total_articles = Article.objects.count()
        processed_articles = Article.objects.filter(is_processed=True).count()
        
        # By category
        categories = Category.objects.prefetch_related('articles').all()
        by_category = {
            cat.name: cat.articles.count() 
            for cat in categories
        }
        
        # Recent activity
        now = timezone.now()
        last_24h = Article.objects.filter(
            created_at__gte=now - timedelta(hours=24)
        ).count()
        last_7d = Article.objects.filter(
            created_at__gte=now - timedelta(days=7)
        ).count()
        
        metrics_data['articles'] = {
            'total': total_articles,
            'processed': processed_articles,
            'unprocessed': total_articles - processed_articles,
            'by_category': by_category,
            'last_24_hours': last_24h,
            'last_7_days': last_7d
        }
    except Exception as e:
        metrics_data['articles'] = {'error': str(e)}
    
    # Scraper metrics
    try:
        config = ScraperConfig.get_config()
        metrics_data['scraper'] = {
            'is_active': config.is_active,
            'interval_minutes': config.fetch_interval_minutes,
            'total_fetched': config.articles_fetched_total,
            'last_run': config.last_run_at.isoformat() if config.last_run_at else None,
            'last_error': config.last_error
        }
    except Exception as e:
        metrics_data['scraper'] = {'error': str(e)}
    
    # Search metrics
    try:
        from apps.news.models import SearchQuery
        
        total_searches = SearchQuery.objects.count()
        recent_searches = SearchQuery.objects.filter(
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()
        
        # Top search terms
        top_terms = list(
            SearchQuery.objects
            .values('query')
            .annotate(count=models.Count('id'))
            .order_by('-count')[:10]
        )
        
        metrics_data['search'] = {
            'total_queries': total_searches,
            'last_24_hours': recent_searches,
            'top_terms': top_terms
        }
    except Exception as e:
        metrics_data['search'] = {'error': str(e)}
    
    # System info
    metrics_data['system'] = {
        'timestamp': timezone.now().isoformat(),
        'uptime': _get_uptime()
    }
    
    return Response(metrics_data)


@api_view(['GET'])
@permission_classes([AllowAny])
def prometheus_metrics(request):
    """
    Prometheus format metrics endpoint.
    
    Returns plain text in Prometheus exposition format.
    Compatible with Prometheus scraping.
    
    Example:
        # HELP bloomberg_articles_total Total number of articles
        # TYPE bloomberg_articles_total gauge
        bloomberg_articles_total 150
    """
    lines = []
    
    # Article metrics
    try:
        total = Article.objects.count()
        processed = Article.objects.filter(is_processed=True).count()
        
        lines.append('# HELP bloomberg_articles_total Total number of articles')
        lines.append('# TYPE bloomberg_articles_total gauge')
        lines.append(f'bloomberg_articles_total {total}')
        
        lines.append('# HELP bloomberg_articles_processed Number of processed articles')
        lines.append('# TYPE bloomberg_articles_processed gauge')
        lines.append(f'bloomberg_articles_processed {processed}')
        
        # By category
        categories = Category.objects.prefetch_related('articles').all()
        lines.append('# HELP bloomberg_articles_by_category Articles per category')
        lines.append('# TYPE bloomberg_articles_by_category gauge')
        for cat in categories:
            count = cat.articles.count()
            safe_name = cat.slug.replace('-', '_')
            lines.append(f'bloomberg_articles_by_category{{category="{safe_name}"}} {count}')
        
    except Exception as e:
        lines.append(f'# ERROR: {e}')
    
    # Scraper metrics
    try:
        config = ScraperConfig.get_config()
        
        lines.append('# HELP bloomberg_scraper_active Is scraper active (1/0)')
        lines.append('# TYPE bloomberg_scraper_active gauge')
        lines.append(f'bloomberg_scraper_active {1 if config.is_active else 0}')
        
        lines.append('# HELP bloomberg_scraper_total_fetched Total articles fetched')
        lines.append('# TYPE bloomberg_scraper_total_fetched counter')
        lines.append(f'bloomberg_scraper_total_fetched {config.articles_fetched_total}')
        
    except Exception as e:
        lines.append(f'# ERROR scraper: {e}')
    
    from django.http import HttpResponse
    return HttpResponse('\n'.join(lines), content_type='text/plain; charset=utf-8')


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_uptime() -> str:
    """Get application uptime."""
    try:
        import os
        import psutil
        
        process = psutil.Process(os.getpid())
        create_time = process.create_time()
        uptime_seconds = time.time() - create_time
        
        hours, remainder = divmod(int(uptime_seconds), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours}h {minutes}m {seconds}s"
    except Exception:
        return "unknown"


# Import for Count in metrics
from django.db import models
