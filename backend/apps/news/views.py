"""
API Views for News Application

This module provides REST API endpoints for:
- Article listing and detail views
- Search functionality with auto-category detection
- Category management
- Search analytics

Author: Obaidulllah
"""

import logging
from typing import Any

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Article, Category, SearchQuery as SearchQueryModel, ScraperConfig
from .serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    CategorySerializer,
    SearchRequestSerializer,
    SearchResponseSerializer,
    SearchQuerySerializer,
    ScraperConfigSerializer,
    ScraperToggleSerializer,
)
from .services import get_search_engine

logger = logging.getLogger(__name__)


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for Category model.
    
    Provides read-only access to news categories with
    article counts for each category.
    
    Endpoints:
        GET /api/v1/news/categories/ - List all categories
        GET /api/v1/news/categories/{id}/ - Get category detail
    """
    
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="List all categories",
        description="Returns all news categories with article counts"
    )
    def list(self, request, *args, **kwargs):
        """List all news categories."""
        return super().list(request, *args, **kwargs)


class ArticleViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API ViewSet for Article model.
    
    Provides read-only access to news articles with
    filtering, searching, and pagination.
    
    Endpoints:
        GET /api/v1/news/articles/ - List articles (paginated)
        GET /api/v1/news/articles/{id}/ - Get article detail
        GET /api/v1/news/articles/latest/ - Get latest articles
        GET /api/v1/news/articles/by_category/{category}/ - Get articles by category
    """
    
    queryset = Article.objects.filter(is_processed=True).select_related('category')
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['category__name', 'is_indexed']
    ordering_fields = ['published_at', 'scraped_at', 'category_confidence']
    ordering = ['-published_at']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        
        Returns:
            Serializer: List or Detail serializer
        """
        if self.action == 'retrieve':
            return ArticleDetailSerializer
        return ArticleListSerializer
    
    @extend_schema(
        summary="List all articles",
        description="Returns paginated list of processed articles"
    )
    def list(self, request, *args, **kwargs):
        """List all processed articles."""
        return super().list(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get article detail",
        description="Returns full article content and metadata"
    )
    def retrieve(self, request, *args, **kwargs):
        """Get single article with full details."""
        return super().retrieve(request, *args, **kwargs)
    
    @extend_schema(
        summary="Get latest articles",
        description="Returns the 10 most recently published articles"
    )
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """
        Get latest articles.
        
        Returns the 10 most recently published articles
        for homepage display.
        """
        articles = self.get_queryset().order_by('-published_at')[:10]
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Get articles by category",
        description="Returns articles filtered by category name",
        parameters=[
            OpenApiParameter(
                name='category',
                description='Category name (economy, market, health, technology, industry)',
                required=True,
                type=str
            )
        ]
    )
    @action(detail=False, methods=['get'], url_path='by_category/(?P<category>[^/.]+)')
    def by_category(self, request, category: str):
        """
        Get articles by category.
        
        Args:
            category: Category name to filter by
            
        Returns:
            Response: Paginated articles in the category
        """
        articles = self.get_queryset().filter(category__name=category)
        page = self.paginate_queryset(articles)
        
        if page is not None:
            serializer = ArticleListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ArticleListSerializer(articles, many=True)
        return Response(serializer.data)


class SearchView(APIView):
    """
    API View for search functionality.
    
    Provides the main search endpoint with:
    - Full-text search across articles
    - Auto-detection of category from query
    - Relevance ranking
    - Pagination support
    
    Endpoint:
        POST /api/v1/news/search/ - Perform search
        GET /api/v1/news/search/ - Perform search (query params)
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Search articles",
        description="""
        Search for news articles using keywords, phrases, or sentences.
        
        Features:
        - Auto-detection of category from search query
        - Full-text search with relevance ranking
        - Support for multiple search terms
        
        Example queries:
        - "stock market rally" → Auto-detects 'market' category
        - "inflation economic growth" → Auto-detects 'economy' category
        - "new cancer treatment" → Auto-detects 'health' category
        """,
        request=SearchRequestSerializer,
        responses={200: SearchResponseSerializer}
    )
    def post(self, request) -> Response:
        """
        Perform search via POST request.
        
        Args:
            request: Request with search parameters in body
            
        Returns:
            Response: Search results with metadata
        """
        return self._perform_search(request.data)
    
    @extend_schema(
        summary="Search articles (GET)",
        description="Search using query parameters",
        parameters=[
            OpenApiParameter(name='query', description='Search query', required=True, type=str),
            OpenApiParameter(name='category', description='Category filter', required=False, type=str),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
            OpenApiParameter(name='page_size', description='Results per page', required=False, type=int),
            OpenApiParameter(name='sort_by', description='Sort order', required=False, type=str),
        ],
        responses={200: SearchResponseSerializer}
    )
    def get(self, request) -> Response:
        """
        Perform search via GET request.
        
        Args:
            request: Request with search parameters in query string
            
        Returns:
            Response: Search results with metadata
        """
        return self._perform_search(request.query_params)
    
    def _perform_search(self, params: dict) -> Response:
        """
        Execute search with given parameters.
        
        Args:
            params: Search parameters dict
            
        Returns:
            Response: Formatted search results
        """
        # Validate input
        serializer = SearchRequestSerializer(data=params)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get validated data
        data = serializer.validated_data
        query = data['query']
        category = data.get('category')
        page = data.get('page', 1)
        page_size = data.get('page_size', 20)
        sort_by = data.get('sort_by', 'relevance')
        
        # Perform search
        search_engine = get_search_engine()
        result = search_engine.search(
            query=query,
            category=category if category else None,
            page=page,
            page_size=page_size,
            sort_by=sort_by
        )
        
        # Calculate total pages
        total_pages = (result.total_count + page_size - 1) // page_size
        
        # Serialize articles
        articles_serializer = ArticleListSerializer(result.articles, many=True)
        
        # Build response
        response_data = {
            'query': query,
            'detected_category': result.detected_category,
            'detected_category_confidence': result.category_confidence,
            'total_results': result.total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'execution_time_ms': result.execution_time_ms,
            'results': articles_serializer.data
        }
        
        return Response(response_data)


class SearchSuggestionsView(APIView):
    """
    API View for search suggestions/autocomplete.
    
    Endpoint:
        GET /api/v1/news/search/suggestions/ - Get search suggestions
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get search suggestions",
        description="Returns autocomplete suggestions based on partial query",
        parameters=[
            OpenApiParameter(
                name='q',
                description='Partial search query',
                required=True,
                type=str
            )
        ]
    )
    def get(self, request) -> Response:
        """
        Get search suggestions.
        
        Args:
            request: Request with partial query
            
        Returns:
            Response: List of suggestions
        """
        partial_query = request.query_params.get('q', '')
        
        if len(partial_query) < 2:
            return Response({'suggestions': []})
        
        search_engine = get_search_engine()
        suggestions = search_engine.get_suggestions(partial_query)
        
        return Response({'suggestions': suggestions})


class SearchStatsView(APIView):
    """
    API View for search analytics and statistics.
    
    Endpoints:
        GET /api/v1/news/search/stats/ - Get search statistics
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get search statistics",
        description="Returns search analytics including popular queries and category stats"
    )
    def get(self, request) -> Response:
        """
        Get search statistics.
        
        Returns:
            Response: Search statistics data
        """
        search_engine = get_search_engine()
        
        return Response({
            'popular_searches': search_engine.get_popular_searches(),
            'category_stats': search_engine.get_category_stats(),
            'total_articles': Article.objects.filter(is_processed=True).count(),
            'total_searches': SearchQueryModel.objects.count()
        })


class ScraperControlView(APIView):
    """
    API View for controlling the web scraper.
    
    Provides the fetch: True/False toggle as specified in requirements.
    
    Endpoints:
        GET /api/v1/scraper/status/ - Get scraper status
        POST /api/v1/scraper/toggle/ - Toggle scraper on/off
    """
    
    permission_classes = [AllowAny]  # In production, add authentication
    
    @extend_schema(
        summary="Get scraper status",
        description="Returns current scraper configuration and status",
        responses={200: ScraperConfigSerializer}
    )
    def get(self, request) -> Response:
        """
        Get scraper status.
        
        Returns:
            Response: Scraper configuration data
        """
        config = ScraperConfig.get_config()
        serializer = ScraperConfigSerializer(config)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Toggle scraper fetch",
        description="Enable or disable automatic article fetching (fetch: True/False)",
        request=ScraperToggleSerializer,
        responses={200: ScraperConfigSerializer}
    )
    def post(self, request) -> Response:
        """
        Toggle scraper on/off.
        
        This implements the fetch: True/False parameter requirement.
        
        Args:
            request: Request with fetch boolean
            
        Returns:
            Response: Updated scraper configuration
        """
        serializer = ScraperToggleSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fetch_enabled = serializer.validated_data['fetch']
        
        config = ScraperConfig.get_config()
        config.is_active = fetch_enabled
        config.save()
        
        logger.info(f"Scraper fetch toggled: {fetch_enabled}")
        
        response_serializer = ScraperConfigSerializer(config)
        return Response(response_serializer.data)
