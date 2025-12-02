"""
URL Configuration for Scraper Application

Defines API endpoints for scraper control and status.

Author: Obaidulllah
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ScraperViewSet

# Create router for ViewSet
router = DefaultRouter()
router.register('', ScraperViewSet, basename='scraper')

urlpatterns = [
    path('', include(router.urls)),
]
