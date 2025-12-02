"""
URL Configuration for News Application

Defines all API endpoints for news articles, search,
and category management.

Author: Obaidulllah
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    CategoryViewSet,
    ArticleViewSet,
    SearchView,
    SearchSuggestionsView,
    SearchStatsView,
    ScraperControlView,
)

# Create router for viewsets
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'articles', ArticleViewSet, basename='article')

urlpatterns = [
    # ViewSet routes
    path('', include(router.urls)),
    
    # Search endpoints
    path('search/', SearchView.as_view(), name='search'),
    path('search/suggestions/', SearchSuggestionsView.as_view(), name='search-suggestions'),
    path('search/stats/', SearchStatsView.as_view(), name='search-stats'),
]
