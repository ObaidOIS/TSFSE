"""
Search Engine Service

This module provides a mini search engine implementation with:
- Full-text search using PostgreSQL
- AI-powered category detection from queries
- Relevance ranking and scoring
- Semantic search capabilities (optional)

Author: Obaidulllah
"""

import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from django.db.models import Q, F, Value, CharField
from django.db.models.functions import Concat
from django.contrib.postgres.search import (
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)

from apps.news.models import Article, Category, SearchQuery as SearchQueryModel
from .categorizer import get_category_detector

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """
    Container for search results with metadata.
    
    Attributes:
        articles: List of matching articles
        total_count: Total number of matches
        detected_category: AI-detected category from query
        category_confidence: Confidence of category detection
        execution_time_ms: Search execution time
    """
    articles: List[Article]
    total_count: int
    detected_category: Optional[str]
    category_confidence: float
    execution_time_ms: int


class SearchEngine:
    """
    Mini search engine for news articles.
    
    Provides multi-layer search functionality:
    1. Query preprocessing and category detection
    2. Full-text search with PostgreSQL
    3. Trigram similarity for fuzzy matching
    4. Relevance ranking and scoring
    
    Features:
    - Auto-detection of category from search query
    - Support for keyword, phrase, and sentence searches
    - Configurable relevance weights
    - Search analytics logging
    
    Example:
        >>> engine = SearchEngine()
        >>> result = engine.search("stock market rally today")
        >>> print(result.detected_category)  # 'market'
        >>> print(len(result.articles))  # Number of results
    """
    
    # Relevance weights for different fields
    FIELD_WEIGHTS = {
        'title': 'A',      # Highest priority
        'keywords': 'B',   # High priority
        'summary': 'C',    # Medium priority
        'content': 'D',    # Lower priority
    }
    
    def __init__(self):
        """Initialize the search engine."""
        self.category_detector = get_category_detector()
    
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = 'relevance',
        log_query: bool = True
    ) -> SearchResult:
        """
        Perform a search across news articles.
        
        This is the main search method that:
        1. Preprocesses the query
        2. Auto-detects category if not provided
        3. Executes full-text search
        4. Ranks and sorts results
        5. Logs search for analytics
        
        Args:
            query: Search query text (words, phrases, or sentences)
            category: Optional category filter (auto-detected if not provided)
            page: Page number for pagination (1-indexed)
            page_size: Number of results per page
            sort_by: Sort order ('relevance', 'date', '-date')
            log_query: Whether to log this search for analytics
            
        Returns:
            SearchResult: Container with articles and metadata
            
        Example:
            >>> result = engine.search(
            ...     query="inflation economic growth",
            ...     category=None,  # Will auto-detect 'economy'
            ...     page=1,
            ...     page_size=10
            ... )
        """
        start_time = time.time()
        
        # Preprocess query
        cleaned_query = self._preprocess_query(query)
        
        if not cleaned_query:
            return SearchResult(
                articles=[],
                total_count=0,
                detected_category=None,
                category_confidence=0.0,
                execution_time_ms=0
            )
        
        # Auto-detect category from query if not provided
        detected_category = category
        category_confidence = 1.0 if category else 0.0
        
        if not category:
            detected_category, category_confidence = (
                self.category_detector.detect_category_from_query(cleaned_query)
            )
        
        # Build and execute search query
        queryset = self._build_search_queryset(
            cleaned_query,
            detected_category,
            sort_by
        )
        
        # Get total count before pagination
        total_count = queryset.count()
        
        # Apply pagination
        offset = (page - 1) * page_size
        articles = list(queryset[offset:offset + page_size])
        
        # Calculate execution time
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Log search query for analytics
        if log_query:
            self._log_search_query(
                query=query,
                detected_category=detected_category,
                results_count=total_count,
                execution_time_ms=execution_time_ms
            )
        
        return SearchResult(
            articles=articles,
            total_count=total_count,
            detected_category=detected_category,
            category_confidence=category_confidence,
            execution_time_ms=execution_time_ms
        )
    
    def _preprocess_query(self, query: str) -> str:
        """
        Preprocess and clean the search query.
        
        Performs:
        - Whitespace normalization
        - Basic sanitization
        
        Args:
            query: Raw query string
            
        Returns:
            str: Cleaned query string
        """
        if not query:
            return ''
        
        # Normalize whitespace
        cleaned = ' '.join(query.split())
        
        # Remove special characters that might break search
        # but keep basic punctuation
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _build_search_queryset(
        self,
        query: str,
        category: Optional[str],
        sort_by: str
    ):
        """
        Build the Django queryset for search.
        
        Creates a comprehensive search using:
        - PostgreSQL full-text search
        - Trigram similarity for fuzzy matching
        - Field-specific weighting
        
        Args:
            query: Preprocessed search query
            category: Category filter (optional)
            sort_by: Sort order
            
        Returns:
            QuerySet: Filtered and ranked article queryset
        """
        # Start with base queryset
        queryset = Article.objects.filter(is_processed=True)
        
        # Apply category filter if provided
        if category:
            queryset = queryset.filter(category__name=category)
        
        # Create search vector for full-text search
        search_vector = SearchVector(
            'title', weight='A'
        ) + SearchVector(
            'summary', weight='B'
        ) + SearchVector(
            'content', weight='C'
        )
        
        # Create search query
        search_query = SearchQuery(query, search_type='websearch')
        
        # Annotate with search rank
        queryset = queryset.annotate(
            search_rank=SearchRank(search_vector, search_query),
            title_similarity=TrigramSimilarity('title', query),
        )
        
        # Filter by relevance threshold
        queryset = queryset.filter(
            Q(search_rank__gt=0.01) | Q(title_similarity__gt=0.1)
        )
        
        # Calculate combined score
        queryset = queryset.annotate(
            combined_score=F('search_rank') * 0.7 + F('title_similarity') * 0.3
        )
        
        # Apply sorting
        if sort_by == 'relevance':
            queryset = queryset.order_by('-combined_score', '-published_at')
        elif sort_by == 'date':
            queryset = queryset.order_by('published_at', '-combined_score')
        elif sort_by == '-date':
            queryset = queryset.order_by('-published_at', '-combined_score')
        else:
            queryset = queryset.order_by('-combined_score')
        
        return queryset.select_related('category')
    
    def _log_search_query(
        self,
        query: str,
        detected_category: Optional[str],
        results_count: int,
        execution_time_ms: int
    ):
        """
        Log search query for analytics.
        
        Args:
            query: Original search query
            detected_category: Detected category name
            results_count: Number of results found
            execution_time_ms: Execution time in milliseconds
        """
        try:
            category = None
            if detected_category:
                category = Category.objects.filter(name=detected_category).first()
            
            SearchQueryModel.objects.create(
                query=query[:500],  # Truncate long queries
                detected_category=category,
                results_count=results_count,
                execution_time_ms=execution_time_ms
            )
        except Exception as e:
            logger.error(f"Failed to log search query: {e}")
    
    def get_suggestions(
        self,
        partial_query: str,
        limit: int = 5
    ) -> List[str]:
        """
        Get search suggestions based on partial query.
        
        Uses previous searches and article titles for suggestions.
        
        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List[str]: List of suggested queries
        """
        suggestions = []
        
        if len(partial_query) < 2:
            return suggestions
        
        # Get suggestions from previous searches
        recent_queries = SearchQueryModel.objects.filter(
            query__icontains=partial_query
        ).values_list('query', flat=True).distinct()[:limit]
        
        suggestions.extend(recent_queries)
        
        # If not enough, add from article titles
        if len(suggestions) < limit:
            remaining = limit - len(suggestions)
            title_suggestions = Article.objects.filter(
                title__icontains=partial_query
            ).values_list('title', flat=True)[:remaining]
            
            # Truncate long titles
            for title in title_suggestions:
                if title not in suggestions:
                    suggestions.append(title[:100])
        
        return suggestions[:limit]
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular search queries.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List[Dict]: Popular searches with counts
        """
        from django.db.models import Count
        
        popular = SearchQueryModel.objects.values('query').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        return list(popular)
    
    def get_category_stats(self) -> List[Dict[str, Any]]:
        """
        Get article counts by category.
        
        Returns:
            List[Dict]: Category statistics
        """
        from django.db.models import Count
        
        stats = Category.objects.annotate(
            article_count=Count('articles')
        ).values('name', 'display_name', 'article_count')
        
        return list(stats)


# Singleton instance
_search_engine = None


def get_search_engine() -> SearchEngine:
    """
    Get singleton SearchEngine instance.
    
    Returns:
        SearchEngine: The search engine instance
    """
    global _search_engine
    if _search_engine is None:
        _search_engine = SearchEngine()
    return _search_engine
