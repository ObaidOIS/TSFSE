"""
Scraper App Tests

Test suite for the scraper application:
- Scraper functionality tests
- API endpoint tests
- Task tests

Author: Obaidulllah
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import timedelta

from apps.news.models import Article, Category
from apps.scraper.bloomberg_scraper import BloombergScraper


class BloombergScraperTests(TestCase):
    """Tests for Bloomberg Scraper"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.scraper = BloombergScraper()
    
    def test_scraper_initialization(self):
        """Test scraper initializes correctly"""
        self.assertIsNotNone(self.scraper.rss_feeds)
        self.assertTrue(len(self.scraper.rss_feeds) > 0)
    
    @patch('apps.scraper.bloomberg_scraper.feedparser.parse')
    def test_parse_rss_feed(self, mock_parse):
        """Test RSS feed parsing"""
        # Mock feed response
        mock_entry = MagicMock()
        mock_entry.title = 'Test Article Title'
        mock_entry.link = 'https://bloomberg.com/test-article'
        mock_entry.summary = 'Test article summary'
        mock_entry.published_parsed = timezone.now().timetuple()
        
        mock_feed = MagicMock()
        mock_feed.entries = [mock_entry]
        mock_parse.return_value = mock_feed
        
        articles = self.scraper.parse_rss_feed('https://example.com/rss')
        
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]['title'], 'Test Article Title')
    
    @patch('apps.scraper.bloomberg_scraper.requests.get')
    def test_fetch_article_content(self, mock_get):
        """Test article content fetching"""
        # Mock HTML response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <body>
                    <article>
                        <h1>Article Title</h1>
                        <p>Article content paragraph one.</p>
                        <p>Article content paragraph two.</p>
                    </article>
                </body>
            </html>
        '''
        mock_get.return_value = mock_response
        
        content = self.scraper.fetch_article_content('https://bloomberg.com/test')
        
        self.assertIsNotNone(content)
    
    def test_detect_duplicate(self):
        """Test duplicate URL detection"""
        # Create an existing article
        category = Category.objects.create(name='Tech', slug='tech')
        Article.objects.create(
            title='Existing Article',
            source_url='https://bloomberg.com/existing',
            source='bloomberg',
            category=category
        )
        
        is_duplicate = self.scraper.is_duplicate('https://bloomberg.com/existing')
        is_not_duplicate = self.scraper.is_duplicate('https://bloomberg.com/new-article')
        
        self.assertTrue(is_duplicate)
        self.assertFalse(is_not_duplicate)


class ScraperAPITests(APITestCase):
    """Tests for Scraper API endpoints"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        cache.clear()
        
        # Create category and articles
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
        
        for i in range(5):
            Article.objects.create(
                title=f'Article {i}',
                source_url=f'https://bloomberg.com/article-{i}',
                source='bloomberg',
                category=self.category,
                scraped_at=timezone.now() - timedelta(hours=i)
            )
    
    def test_get_scraper_status(self):
        """Test getting scraper status"""
        url = reverse('scraper-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('enabled', response.data)
        self.assertIn('statistics', response.data)
        self.assertIn('status', response.data)
    
    def test_toggle_scraper_on(self):
        """Test enabling scraper"""
        url = reverse('scraper-toggle')
        response = self.client.post(url, {'fetch': True}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['fetch'])
    
    def test_toggle_scraper_off(self):
        """Test disabling scraper"""
        url = reverse('scraper-toggle')
        response = self.client.post(url, {'fetch': False}, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['fetch'])
    
    def test_toggle_scraper_no_body(self):
        """Test toggle without body toggles current state"""
        cache.set('scraper_enabled', True)
        
        url = reverse('scraper-toggle')
        response = self.client.post(url, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['fetch'])  # Should toggle to False
    
    @patch('apps.scraper.views.scrape_bloomberg_news.delay')
    def test_trigger_scraper(self, mock_task):
        """Test manual scraper trigger"""
        mock_task.return_value = MagicMock(id='test-task-id')
        
        url = reverse('scraper-trigger')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('task_id', response.data)
        mock_task.assert_called_once()
    
    def test_trigger_scraper_already_running(self):
        """Test triggering scraper when already running"""
        cache.set('scraper_running', True)
        
        url = reverse('scraper-trigger')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        
        cache.delete('scraper_running')
    
    def test_scraper_history(self):
        """Test scraper history endpoint"""
        url = reverse('scraper-history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('articles', response.data)
        self.assertEqual(response.data['count'], 5)
    
    def test_scraper_history_with_limit(self):
        """Test scraper history with limit parameter"""
        url = reverse('scraper-history')
        response = self.client.get(url, {'limit': 2})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
    
    def test_clear_cache(self):
        """Test clearing scraper cache"""
        cache.set('last_scrape_time', timezone.now())
        cache.set('scraper_running', True)
        
        url = reverse('scraper-clear-cache')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(cache.get('scraper_running'))
    
    def test_get_feeds(self):
        """Test getting RSS feeds list"""
        url = reverse('scraper-feeds')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('feeds', response.data)
        self.assertIn('count', response.data)


class CeleryTaskTests(TestCase):
    """Tests for Celery tasks"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
    
    @patch('apps.scraper.tasks.BloombergScraper')
    @patch('apps.scraper.tasks.ArticleCategorizer')
    def test_scrape_bloomberg_news_task(self, mock_categorizer, mock_scraper):
        """Test scrape_bloomberg_news task"""
        from apps.scraper.tasks import scrape_bloomberg_news
        
        # Mock scraper
        mock_scraper_instance = MagicMock()
        mock_scraper_instance.scrape_all.return_value = [
            {
                'title': 'Test Article',
                'url': 'https://bloomberg.com/test',
                'content': 'Test content',
                'description': 'Test description',
            }
        ]
        mock_scraper.return_value = mock_scraper_instance
        
        # Mock categorizer
        mock_categorizer_instance = MagicMock()
        mock_categorizer_instance.categorize.return_value = {
            'category': 'technology',
            'confidence': 0.9,
            'keywords': ['test'],
            'entities': {}
        }
        mock_categorizer.return_value = mock_categorizer_instance
        
        # Run task (synchronously for testing)
        with patch('apps.scraper.tasks.cache') as mock_cache:
            mock_cache.get.return_value = True  # Scraper enabled
            
            result = scrape_bloomberg_news()
        
        self.assertIsNotNone(result)
    
    @patch('apps.news.services.categorizer.ArticleCategorizer')
    def test_process_article_task(self, mock_categorizer):
        """Test process_article task"""
        from apps.scraper.tasks import process_article
        
        # Create article without category
        article = Article.objects.create(
            title='Uncategorized Article',
            content='Some content here',
            source_url='https://bloomberg.com/uncategorized',
            source='bloomberg',
            category=self.category
        )
        
        # Mock categorizer
        mock_categorizer_instance = MagicMock()
        mock_categorizer_instance.categorize.return_value = {
            'category': 'technology',
            'confidence': 0.85,
            'keywords': ['tech'],
            'entities': {'organizations': ['TechCorp']}
        }
        mock_categorizer.return_value = mock_categorizer_instance
        
        # Run task
        result = process_article(article.id)
        
        # Verify article was updated
        article.refresh_from_db()
        self.assertIsNotNone(result)


class ScraperStatisticsTests(TestCase):
    """Tests for scraper statistics"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
        
        now = timezone.now()
        
        # Create articles with different timestamps
        for i in range(10):
            Article.objects.create(
                title=f'Article {i}',
                source_url=f'https://bloomberg.com/article-{i}',
                source='bloomberg',
                category=self.category,
                scraped_at=now - timedelta(hours=i * 5)
            )
    
    def test_articles_today_count(self):
        """Test counting articles scraped today"""
        now = timezone.now()
        count = Article.objects.filter(
            scraped_at__gte=now - timedelta(days=1)
        ).count()
        
        # Should have articles from last 24 hours
        self.assertTrue(count > 0)
    
    def test_articles_week_count(self):
        """Test counting articles scraped this week"""
        now = timezone.now()
        count = Article.objects.filter(
            scraped_at__gte=now - timedelta(days=7)
        ).count()
        
        # Should have all 10 articles (all within 50 hours)
        self.assertEqual(count, 10)
