"""
Serializers for News Application

This module defines Django REST Framework serializers for:
- Article data serialization
- Category serialization
- Search result formatting
- Scraper configuration

Author: Obaidulllah
"""

from rest_framework import serializers
from .models import Article, Category, SearchQuery, ScraperConfig


class CategorySerializer(serializers.ModelSerializer):
    """
    Serializer for Category model.
    
    Provides complete category data including article count
    for display in the frontend.
    """
    
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'display_name',
            'description',
            'article_count'
        ]
    
    def get_article_count(self, obj) -> int:
        """
        Get the count of articles in this category.
        
        Args:
            obj: Category instance
            
        Returns:
            int: Number of articles in category
        """
        return obj.articles.count()


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer for Article list views.
    
    Provides a lightweight representation of articles
    optimized for list/search results display.
    """
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_display = serializers.CharField(source='category.display_name', read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'summary',
            'url',
            'author',
            'image_url',
            'category_name',
            'category_display',
            'category_confidence',
            'keywords',
            'published_at',
            'scraped_at'
        ]


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Article detail views.
    
    Provides complete article data including full content
    and all metadata for detailed view.
    """
    
    category = CategorySerializer(read_only=True)
    keywords_list = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id',
            'title',
            'content',
            'summary',
            'url',
            'author',
            'image_url',
            'category',
            'category_confidence',
            'keywords',
            'keywords_list',
            'entities',
            'published_at',
            'scraped_at',
            'created_at',
            'updated_at'
        ]
    
    def get_keywords_list(self, obj) -> list:
        """
        Get flattened list of keywords.
        
        Args:
            obj: Article instance
            
        Returns:
            list: List of keyword strings
        """
        return obj.get_keywords_list()


class SearchQuerySerializer(serializers.ModelSerializer):
    """
    Serializer for SearchQuery model.
    
    Used for logging and analytics of user searches.
    """
    
    detected_category_name = serializers.CharField(
        source='detected_category.name',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = SearchQuery
        fields = [
            'id',
            'query',
            'detected_category_name',
            'results_count',
            'execution_time_ms',
            'created_at'
        ]
        read_only_fields = ['created_at']


class SearchRequestSerializer(serializers.Serializer):
    """
    Serializer for search request validation.
    
    Validates and processes incoming search queries
    before passing to the search engine.
    """
    
    query = serializers.CharField(
        max_length=500,
        required=True,
        help_text="Search query text"
    )
    category = serializers.CharField(
        max_length=50,
        required=False,
        allow_blank=True,
        help_text="Filter by category (optional, auto-detected if not provided)"
    )
    page = serializers.IntegerField(
        min_value=1,
        default=1,
        help_text="Page number for pagination"
    )
    page_size = serializers.IntegerField(
        min_value=1,
        max_value=100,
        default=20,
        help_text="Number of results per page"
    )
    sort_by = serializers.ChoiceField(
        choices=['relevance', 'date', '-date'],
        default='relevance',
        help_text="Sort order for results"
    )
    
    def validate_query(self, value: str) -> str:
        """
        Validate and clean the search query.
        
        Args:
            value: Raw search query
            
        Returns:
            str: Cleaned search query
        """
        # Remove excessive whitespace
        return ' '.join(value.split())


class SearchResponseSerializer(serializers.Serializer):
    """
    Serializer for search response formatting.
    
    Provides structured response including results,
    detected category, and pagination info.
    """
    
    query = serializers.CharField()
    detected_category = serializers.CharField(allow_null=True)
    detected_category_confidence = serializers.FloatField()
    total_results = serializers.IntegerField()
    page = serializers.IntegerField()
    page_size = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    execution_time_ms = serializers.IntegerField()
    results = ArticleListSerializer(many=True)


class ScraperConfigSerializer(serializers.ModelSerializer):
    """
    Serializer for ScraperConfig model.
    
    Provides scraper configuration and status information.
    """
    
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = ScraperConfig
        fields = [
            'id',
            'is_active',
            'interval_seconds',
            'last_run_at',
            'last_article_url',
            'articles_fetched_total',
            'last_error',
            'status',
            'updated_at'
        ]
        read_only_fields = [
            'last_run_at',
            'last_article_url',
            'articles_fetched_total',
            'last_error',
            'updated_at'
        ]
    
    def get_status(self, obj) -> str:
        """
        Get human-readable scraper status.
        
        Args:
            obj: ScraperConfig instance
            
        Returns:
            str: Status string
        """
        if not obj.is_active:
            return 'disabled'
        if obj.last_error:
            return 'error'
        return 'running'


class ScraperToggleSerializer(serializers.Serializer):
    """
    Serializer for toggling scraper on/off.
    
    Provides the fetch: True/False control as specified in requirements.
    """
    
    fetch = serializers.BooleanField(
        required=True,
        help_text="Enable (True) or disable (False) automatic fetching"
    )
