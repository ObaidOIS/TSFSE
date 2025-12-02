"""
Django Admin Configuration for News Application

Registers models with the Django admin interface for
easy management and monitoring of scraped articles.

Author: Obaidulllah
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Article, Category, SearchQuery, ScraperConfig


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category model.
    
    Provides easy management of news categories with
    keyword configuration for AI detection.
    """
    
    list_display = ['name', 'display_name', 'article_count', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at']
    
    def article_count(self, obj):
        """Display count of articles in this category."""
        return obj.articles.count()
    article_count.short_description = 'Articles'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Admin interface for Article model.
    
    Provides comprehensive article management including:
    - Search and filtering capabilities
    - Category and processing status display
    - Quick links to original articles
    """
    
    list_display = [
        'short_title', 
        'category', 
        'category_confidence_display',
        'is_processed',
        'is_indexed',
        'published_at',
        'scraped_at'
    ]
    list_filter = [
        'category', 
        'is_processed', 
        'is_indexed',
        'published_at',
        'scraped_at'
    ]
    search_fields = ['title', 'content', 'author', 'url']
    readonly_fields = [
        'id', 
        'scraped_at', 
        'search_vector',
        'created_at', 
        'updated_at'
    ]
    date_hierarchy = 'published_at'
    ordering = ['-scraped_at']
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'content', 'summary', 'url', 'author', 'image_url')
        }),
        ('Categorization', {
            'fields': ('category', 'category_confidence', 'keywords', 'entities')
        }),
        ('Timestamps', {
            'fields': ('published_at', 'scraped_at', 'created_at', 'updated_at')
        }),
        ('Processing Status', {
            'fields': ('is_processed', 'is_indexed', 'search_vector')
        }),
        ('Identification', {
            'fields': ('id',),
            'classes': ('collapse',)
        }),
    )
    
    def short_title(self, obj):
        """Display truncated title with link to original article."""
        title = obj.title[:60] + '...' if len(obj.title) > 60 else obj.title
        return format_html(
            '<a href="{}" target="_blank">{}</a>',
            obj.url,
            title
        )
    short_title.short_description = 'Title'
    
    def category_confidence_display(self, obj):
        """Display category confidence as percentage with color coding."""
        confidence = obj.category_confidence * 100
        if confidence >= 80:
            color = 'green'
        elif confidence >= 50:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{}%</span>',
            color,
            f'{confidence:.1f}'
        )
    category_confidence_display.short_description = 'Confidence'


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    """
    Admin interface for SearchQuery model.
    
    Provides analytics on user searches including
    popular queries and category detection accuracy.
    """
    
    list_display = [
        'query', 
        'detected_category', 
        'results_count',
        'execution_time_ms',
        'created_at'
    ]
    list_filter = ['detected_category', 'created_at']
    search_fields = ['query']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(ScraperConfig)
class ScraperConfigAdmin(admin.ModelAdmin):
    """
    Admin interface for ScraperConfig model.
    
    Provides control over the web scraper including:
    - Enable/disable auto-fetching
    - Configure scraping interval
    - Monitor scraper status
    """
    
    list_display = [
        'status_display',
        'interval_seconds',
        'articles_fetched_total',
        'last_run_at',
        'updated_at'
    ]
    readonly_fields = [
        'last_run_at',
        'last_article_url',
        'articles_fetched_total',
        'last_error',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Scraper Control', {
            'fields': ('is_active', 'interval_seconds')
        }),
        ('Status', {
            'fields': (
                'last_run_at',
                'last_article_url',
                'articles_fetched_total',
                'last_error'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_display(self, obj):
        """Display scraper status with color indicator."""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">● Active</span>'
            )
        return format_html(
            '<span style="color: red;">● Inactive</span>'
        )
    status_display.short_description = 'Status'
    
    def has_add_permission(self, request):
        """Prevent creation of multiple config instances."""
        return not ScraperConfig.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of config."""
        return False
