"""
Database Models for News Application

This module defines the database schema for storing news articles
with support for full-text search and AI-powered categorization.

Database Schema Design:
- Article: Main news article storage with full-text search support
- Category: Predefined news categories
- Keyword: Extracted keywords from articles
- SearchQuery: User search history for analytics

Author: Obaidulllah
"""

import uuid
from django.db import models
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex
from django.utils import timezone


class Category(models.Model):
    """
    Represents a news category for article classification.
    
    Categories are predefined based on requirements:
    - Economy: Economic news, financial markets, GDP, inflation
    - Market: Commodities, stocks, trading, forex
    - Health: Healthcare, medicine, public health
    - Technology: Tech industry, software, hardware, AI
    - Industry: Manufacturing, production, business sectors
    
    Attributes:
        name (str): Category name (unique identifier)
        display_name (str): Human-readable category name
        description (str): Category description
        keywords (JSONField): Keywords associated with this category for detection
        created_at (datetime): Timestamp of category creation
    """
    
    CATEGORY_CHOICES = [
        ('economy', 'Economy'),
        ('market', 'Market (Commodities)'),
        ('health', 'Health'),
        ('technology', 'Technology'),
        ('industry', 'Industry'),
    ]
    
    id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=50, 
        unique=True,
        choices=CATEGORY_CHOICES,
        help_text="Category identifier"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Human-readable category name"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this category covers"
    )
    keywords = models.JSONField(
        default=list,
        help_text="List of keywords used for category detection"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self) -> str:
        """Return string representation of category."""
        return self.display_name


class Article(models.Model):
    """
    Represents a news article scraped from Bloomberg.
    
    This model stores all article data with support for:
    - Full-text search using PostgreSQL tsvector
    - AI-powered categorization with confidence scores
    - Extracted keywords and named entities
    - Duplicate detection via URL uniqueness
    
    Attributes:
        id (UUID): Unique identifier for the article
        title (str): Article headline
        content (str): Full article text content
        summary (str): AI-generated or extracted summary
        url (str): Original Bloomberg URL (unique)
        author (str): Article author(s)
        category (FK): Reference to Category model
        category_confidence (float): AI confidence score for categorization
        keywords (JSON): Extracted keywords with relevance scores
        entities (JSON): Named entities (companies, people, locations)
        published_at (datetime): Original publication time
        scraped_at (datetime): When article was scraped
        search_vector (tsvector): PostgreSQL full-text search vector
        is_indexed (bool): Whether article is indexed in Elasticsearch
        created_at (datetime): Database creation timestamp
        updated_at (datetime): Last update timestamp
    """
    
    # Primary identification
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for the article"
    )
    
    # Core content fields
    title = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Article headline"
    )
    content = models.TextField(
        help_text="Full article text content"
    )
    summary = models.TextField(
        blank=True,
        help_text="Article summary (AI-generated or extracted)"
    )
    url = models.URLField(
        max_length=1000,
        unique=True,
        help_text="Original Bloomberg article URL"
    )
    author = models.CharField(
        max_length=200,
        blank=True,
        help_text="Article author(s)"
    )
    image_url = models.URLField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="Featured image URL"
    )
    
    # Categorization fields
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles',
        help_text="Article category"
    )
    category_confidence = models.FloatField(
        default=0.0,
        help_text="AI confidence score for category (0.0 to 1.0)"
    )
    
    # AI-extracted metadata
    keywords = models.JSONField(
        default=list,
        help_text="Extracted keywords with relevance scores"
    )
    entities = models.JSONField(
        default=dict,
        help_text="Named entities: companies, people, locations, etc."
    )
    
    # Timestamps
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Original publication timestamp"
    )
    scraped_at = models.DateTimeField(
        default=timezone.now,
        help_text="When article was scraped"
    )
    
    # Search optimization
    search_vector = SearchVectorField(
        null=True,
        help_text="PostgreSQL full-text search vector"
    )
    
    # Processing status
    is_indexed = models.BooleanField(
        default=False,
        help_text="Whether article is indexed in search engine"
    )
    is_processed = models.BooleanField(
        default=False,
        help_text="Whether AI processing is complete"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Article'
        verbose_name_plural = 'Articles'
        ordering = ['-published_at', '-scraped_at']
        indexes = [
            GinIndex(fields=['search_vector']),
            models.Index(fields=['category', 'published_at']),
            models.Index(fields=['is_indexed', 'is_processed']),
            models.Index(fields=['-scraped_at']),
        ]
    
    def __str__(self) -> str:
        """Return string representation of article."""
        return f"{self.title[:50]}..." if len(self.title) > 50 else self.title
    
    def get_category_name(self) -> str:
        """
        Get the category name for this article.
        
        Returns:
            str: Category name or 'Uncategorized' if no category assigned
        """
        return self.category.name if self.category else 'uncategorized'
    
    def get_keywords_list(self) -> list:
        """
        Get list of keywords as strings.
        
        Returns:
            list: List of keyword strings
        """
        if isinstance(self.keywords, list):
            return [k.get('word', k) if isinstance(k, dict) else k for k in self.keywords]
        return []


class SearchQuery(models.Model):
    """
    Stores user search queries for analytics and optimization.
    
    This model helps track:
    - Popular search terms
    - Category detection accuracy
    - Search patterns for improving relevance
    
    Attributes:
        query (str): The search query text
        detected_category (FK): AI-detected category from query
        results_count (int): Number of results returned
        user_ip (str): Anonymized user identifier
        created_at (datetime): When search was performed
    """
    
    id = models.AutoField(primary_key=True)
    query = models.CharField(
        max_length=500,
        db_index=True,
        help_text="User search query"
    )
    detected_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='search_queries',
        help_text="AI-detected category from query"
    )
    results_count = models.IntegerField(
        default=0,
        help_text="Number of results returned"
    )
    execution_time_ms = models.IntegerField(
        default=0,
        help_text="Search execution time in milliseconds"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Search Query'
        verbose_name_plural = 'Search Queries'
        ordering = ['-created_at']
    
    def __str__(self) -> str:
        """Return string representation of search query."""
        return f'"{self.query}" - {self.results_count} results'


class ScraperConfig(models.Model):
    """
    Configuration model for controlling the web scraper.
    
    This singleton model stores scraper settings including:
    - Whether automatic fetching is enabled (fetch: True/False)
    - Scraping interval
    - Last successful scrape information
    
    Attributes:
        is_active (bool): Whether auto-fetching is enabled
        interval_seconds (int): Time between scraping runs
        last_run_at (datetime): Timestamp of last scrape
        last_article_url (str): URL of most recently scraped article
        articles_fetched_total (int): Total articles fetched
    """
    
    id = models.AutoField(primary_key=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether automatic fetching is enabled (fetch parameter)"
    )
    interval_seconds = models.IntegerField(
        default=300,
        help_text="Interval between scraping runs in seconds"
    )
    last_run_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last scraper run"
    )
    last_article_url = models.URLField(
        max_length=1000,
        blank=True,
        help_text="URL of most recently scraped article"
    )
    articles_fetched_total = models.IntegerField(
        default=0,
        help_text="Total number of articles fetched"
    )
    last_error = models.TextField(
        blank=True,
        help_text="Last error message if any"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Scraper Configuration'
        verbose_name_plural = 'Scraper Configurations'
    
    def __str__(self) -> str:
        """Return string representation of scraper config."""
        status = "Active" if self.is_active else "Inactive"
        return f"Scraper Config ({status})"
    
    @classmethod
    def get_config(cls) -> 'ScraperConfig':
        """
        Get or create the singleton scraper configuration.
        
        Returns:
            ScraperConfig: The scraper configuration instance
        """
        config, _ = cls.objects.get_or_create(pk=1)
        return config
