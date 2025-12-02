"""
Scraper App Views

API endpoints for controlling the Bloomberg news scraper.

Features:
- Toggle fetch on/off
- Get scraper status
- Manual trigger for scraping
- View scraping history

Author: Obaidulllah
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

from .tasks import check_for_new_articles
from apps.news.models import Article


class ScraperViewSet(viewsets.ViewSet):
    """
    API ViewSet for scraper control
    
    Provides endpoints to:
    - Start/stop automatic fetching
    - Manually trigger scraping
    - Get scraper status and history
    """
    
    # Cache keys
    SCRAPER_ENABLED_KEY = 'scraper_enabled'
    LAST_SCRAPE_KEY = 'last_scrape_time'
    SCRAPE_RESULTS_KEY = 'last_scrape_results'
    
    permission_classes = [AllowAny]  # For demo; use IsAuthenticated in production
    
    def list(self, request):
        """
        GET /api/scraper/
        
        Returns current scraper status and statistics
        """
        enabled = cache.get(self.SCRAPER_ENABLED_KEY, True)
        last_scrape = cache.get(self.LAST_SCRAPE_KEY)
        last_results = cache.get(self.SCRAPE_RESULTS_KEY, {})
        
        # Get recent articles stats
        now = timezone.now()
        articles_today = Article.objects.filter(
            scraped_at__gte=now - timedelta(days=1)
        ).count()
        articles_week = Article.objects.filter(
            scraped_at__gte=now - timedelta(days=7)
        ).count()
        total_articles = Article.objects.count()
        
        return Response({
            'enabled': enabled,
            'last_scrape': last_scrape.isoformat() if last_scrape else None,
            'last_results': last_results,
            'statistics': {
                'articles_today': articles_today,
                'articles_week': articles_week,
                'total_articles': total_articles,
            },
            'status': 'running' if enabled else 'stopped'
        })
    
    @action(detail=False, methods=['post'])
    def toggle(self, request):
        """
        POST /api/scraper/toggle/
        
        Toggle scraper on/off
        
        Request body:
        {
            "fetch": true/false
        }
        """
        fetch = request.data.get('fetch')
        
        if fetch is None:
            # Toggle current state
            current = cache.get(self.SCRAPER_ENABLED_KEY, True)
            fetch = not current
        
        # Store in cache (persists across restarts if using Redis)
        cache.set(self.SCRAPER_ENABLED_KEY, fetch, timeout=None)
        
        return Response({
            'fetch': fetch,
            'message': f"Scraper {'enabled' if fetch else 'disabled'}",
            'timestamp': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['post'], url_path='scrape')
    def scrape(self, request):
        """
        POST /api/scraper/scrape/
        
        Manually trigger a scraping run
        
        This bypasses the enabled/disabled state
        """
        # Check if scraper is already running
        if cache.get('scraper_running', False):
            return Response(
                {'error': 'Scraper is already running'},
                status=status.HTTP_409_CONFLICT
            )
        
        # Trigger async task
        task = check_for_new_articles.delay()
        
        return Response({
            'message': 'Scraping task started',
            'task_id': task.id,
            'timestamp': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['get'])
    def history(self, request):
        """
        GET /api/scraper/history/
        
        Get scraping history (last 100 articles scraped)
        """
        limit = int(request.query_params.get('limit', 100))
        limit = min(limit, 500)  # Max 500 to prevent abuse
        
        articles = Article.objects.order_by('-scraped_at')[:limit].values(
            'id',
            'title',
            'source_url',
            'scraped_at',
            'category__name',
            'category_confidence',
        )
        
        return Response({
            'count': len(articles),
            'articles': list(articles)
        })
    
    @action(detail=False, methods=['post'])
    def clear_cache(self, request):
        """
        POST /api/scraper/clear_cache/
        
        Clear scraper-related cache entries
        Useful for resetting state
        """
        cache.delete(self.LAST_SCRAPE_KEY)
        cache.delete(self.SCRAPE_RESULTS_KEY)
        cache.delete('scraper_running')
        
        return Response({
            'message': 'Scraper cache cleared',
            'timestamp': timezone.now().isoformat()
        })
    
    @action(detail=False, methods=['get'])
    def feeds(self, request):
        """
        GET /api/scraper/feeds/
        
        Get list of configured RSS feeds being scraped
        """
        from .bloomberg_scraper import BloombergScraper
        
        scraper = BloombergScraper()
        feeds = scraper.rss_feeds
        
        return Response({
            'feeds': feeds,
            'count': len(feeds)
        })
