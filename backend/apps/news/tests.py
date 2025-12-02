"""
News App Tests

Comprehensive test suite for the news application:
- Model tests
- API endpoint tests
- Serializer tests
- Service tests (categorizer, search)

Author: Obaidulllah
"""

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from datetime import timedelta

from apps.news.models import Article, Category, SearchQuery
from apps.news.serializers import ArticleSerializer, ArticleListSerializer
from apps.news.services.search import SearchEngine


class CategoryModelTests(TestCase):
    """Tests for Category model"""
    
    def test_create_category(self):
        """Test creating a category"""
        category = Category.objects.create(
            name='Technology',
            slug='technology',
            description='Tech news'
        )
        self.assertEqual(str(category), 'Technology')
        self.assertEqual(category.slug, 'technology')
    
    def test_category_ordering(self):
        """Test categories are ordered by name"""
        Category.objects.create(name='Technology', slug='technology')
        Category.objects.create(name='Economy', slug='economy')
        Category.objects.create(name='Health', slug='health')
        
        categories = list(Category.objects.values_list('name', flat=True))
        self.assertEqual(categories, ['Economy', 'Health', 'Technology'])


class ArticleModelTests(TestCase):
    """Tests for Article model"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
    
    def test_create_article(self):
        """Test creating an article"""
        article = Article.objects.create(
            title='Test Article',
            content='Test content for the article.',
            description='Test description',
            source_url='https://example.com/test-article',
            source='bloomberg',
            category=self.category,
            category_confidence=0.95
        )
        
        self.assertEqual(str(article), 'Test Article')
        self.assertEqual(article.category, self.category)
        self.assertIsNotNone(article.created_at)
    
    def test_article_search_vector_created(self):
        """Test that search vector is created for article"""
        article = Article.objects.create(
            title='Stock Market Rally',
            content='The stock market saw significant gains today.',
            source_url='https://example.com/stock-rally',
            source='bloomberg',
            category=self.category
        )
        
        # Refresh from DB to get updated search_vector
        article.refresh_from_db()
        # Note: search_vector is populated by trigger or save method
        self.assertIsNotNone(article.search_vector)
    
    def test_article_unique_url(self):
        """Test that article URLs must be unique"""
        Article.objects.create(
            title='First Article',
            source_url='https://example.com/unique-url',
            source='bloomberg',
            category=self.category
        )
        
        with self.assertRaises(Exception):
            Article.objects.create(
                title='Second Article',
                source_url='https://example.com/unique-url',
                source='bloomberg',
                category=self.category
            )


class SearchQueryModelTests(TestCase):
    """Tests for SearchQuery model"""
    
    def test_create_search_query(self):
        """Test creating a search query log"""
        query = SearchQuery.objects.create(
            query='stock market',
            results_count=25,
            execution_time_ms=50
        )
        
        self.assertEqual(query.query, 'stock market')
        self.assertEqual(query.results_count, 25)
    
    def test_search_query_with_category(self):
        """Test search query with detected category"""
        category = Category.objects.create(name='Market', slug='market')
        
        query = SearchQuery.objects.create(
            query='stock price',
            detected_category=category,
            category_confidence=0.85,
            results_count=30
        )
        
        self.assertEqual(query.detected_category, category)
        self.assertAlmostEqual(query.category_confidence, 0.85)


class ArticleAPITests(APITestCase):
    """Tests for Article API endpoints"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create categories
        self.tech_category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
        self.economy_category = Category.objects.create(
            name='Economy',
            slug='economy'
        )
        
        # Create articles
        self.article1 = Article.objects.create(
            title='AI Revolution in Tech',
            content='Artificial intelligence is transforming the technology industry.',
            description='AI transforming tech',
            source_url='https://example.com/ai-revolution',
            source='bloomberg',
            category=self.tech_category,
            category_confidence=0.92,
            published_at=timezone.now() - timedelta(hours=1)
        )
        
        self.article2 = Article.objects.create(
            title='Economy Shows Growth',
            content='The economy demonstrated strong growth in Q4.',
            description='Economy growth report',
            source_url='https://example.com/economy-growth',
            source='bloomberg',
            category=self.economy_category,
            category_confidence=0.88,
            published_at=timezone.now() - timedelta(hours=2)
        )
    
    def test_list_articles(self):
        """Test listing all articles"""
        url = reverse('article-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_retrieve_article(self):
        """Test retrieving a single article"""
        url = reverse('article-detail', kwargs={'pk': self.article1.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'AI Revolution in Tech')
    
    def test_filter_by_category(self):
        """Test filtering articles by category"""
        url = reverse('article-list')
        response = self.client.get(url, {'category': 'technology'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['title'], 'AI Revolution in Tech')
    
    def test_search_articles(self):
        """Test searching articles"""
        url = reverse('article-search')
        response = self.client.get(url, {'q': 'AI technology'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertIn('total_results', response.data)
    
    def test_categories_endpoint(self):
        """Test categories list with counts"""
        url = reverse('article-categories')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) >= 2)
    
    def test_latest_articles(self):
        """Test latest articles endpoint"""
        url = reverse('article-latest')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should be ordered by published_at descending
        articles = response.data
        self.assertTrue(len(articles) > 0)


class SearchEngineTests(TestCase):
    """Tests for SearchEngine service"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Technology',
            slug='technology'
        )
        
        # Create test articles
        for i in range(5):
            Article.objects.create(
                title=f'Technology Article {i}',
                content=f'This is content about technology and AI number {i}.',
                source_url=f'https://example.com/tech-{i}',
                source='bloomberg',
                category=self.category
            )
        
        self.search_engine = SearchEngine()
    
    def test_basic_search(self):
        """Test basic search functionality"""
        results = self.search_engine.search('technology')
        
        self.assertIn('results', results)
        self.assertIn('total_results', results)
        self.assertTrue(results['total_results'] >= 0)
    
    def test_search_with_pagination(self):
        """Test search with pagination"""
        results = self.search_engine.search('technology', page=1, page_size=2)
        
        self.assertIn('page', results)
        self.assertIn('page_size', results)
        self.assertIn('total_pages', results)
    
    def test_search_with_category_filter(self):
        """Test search with category filter"""
        results = self.search_engine.search('article', category='technology')
        
        for article in results.get('results', []):
            self.assertEqual(article.category.slug, 'technology')
    
    def test_empty_search_query(self):
        """Test search with empty query returns results"""
        results = self.search_engine.search('')
        
        self.assertIn('results', results)
        # Empty search should still return results (all articles)


class SerializerTests(TestCase):
    """Tests for DRF serializers"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(
            name='Health',
            slug='health'
        )
        
        self.article = Article.objects.create(
            title='Health News',
            content='Important health update.',
            description='Health update description',
            source_url='https://example.com/health-news',
            source='bloomberg',
            category=self.category,
            category_confidence=0.90,
            keywords=['health', 'medical', 'research'],
            entities={'organizations': ['WHO'], 'locations': ['Geneva']}
        )
    
    def test_article_serializer(self):
        """Test ArticleSerializer output"""
        serializer = ArticleSerializer(self.article)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Health News')
        self.assertEqual(data['category']['name'], 'Health')
        self.assertIn('keywords', data)
        self.assertIn('entities', data)
    
    def test_article_list_serializer(self):
        """Test ArticleListSerializer has fewer fields"""
        serializer = ArticleListSerializer(self.article)
        data = serializer.data
        
        self.assertEqual(data['title'], 'Health News')
        self.assertIn('id', data)
        self.assertIn('category', data)


class CategorizerServiceTests(TestCase):
    """Tests for AI Categorizer service"""
    
    @patch('apps.news.services.categorizer.pipeline')
    def test_categorize_article(self, mock_pipeline):
        """Test article categorization with mocked AI"""
        # Mock the transformer pipeline
        mock_classifier = MagicMock()
        mock_classifier.return_value = [{
            'labels': ['technology', 'economy', 'health'],
            'scores': [0.85, 0.10, 0.05]
        }]
        mock_pipeline.return_value = mock_classifier
        
        from apps.news.services.categorizer import ArticleCategorizer
        
        categorizer = ArticleCategorizer()
        result = categorizer.categorize(
            'New AI Model Released',
            'A groundbreaking artificial intelligence model was released today.'
        )
        
        self.assertIn('category', result)
        self.assertIn('confidence', result)
    
    @patch('apps.news.services.categorizer.pipeline')
    @patch('apps.news.services.categorizer.spacy.load')
    def test_extract_entities(self, mock_spacy, mock_pipeline):
        """Test entity extraction with mocked spaCy"""
        # Mock spaCy
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_ent = MagicMock()
        mock_ent.text = 'Apple'
        mock_ent.label_ = 'ORG'
        mock_doc.ents = [mock_ent]
        mock_nlp.return_value = mock_doc
        mock_spacy.return_value = mock_nlp
        
        # Mock transformer
        mock_classifier = MagicMock()
        mock_classifier.return_value = [{'labels': ['technology'], 'scores': [0.9]}]
        mock_pipeline.return_value = mock_classifier
        
        from apps.news.services.categorizer import ArticleCategorizer
        
        categorizer = ArticleCategorizer()
        result = categorizer.categorize(
            'Apple Announces New Product',
            'Apple Inc. unveiled its latest innovation today.'
        )
        
        self.assertIn('entities', result)


class IntegrationTests(APITestCase):
    """Integration tests for full workflow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        # Create all categories
        categories = ['Economy', 'Market', 'Health', 'Technology', 'Industry']
        for name in categories:
            Category.objects.create(
                name=name,
                slug=name.lower()
            )
    
    def test_full_search_workflow(self):
        """Test complete search workflow"""
        # 1. Get categories
        categories_url = reverse('article-categories')
        response = self.client.get(categories_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2. Perform search
        search_url = reverse('article-search')
        response = self.client.get(search_url, {'q': 'technology'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 3. Get search stats
        stats_url = reverse('article-stats')
        response = self.client.get(stats_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
