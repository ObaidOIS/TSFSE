"""
URL Configuration for Bloomberg News Scraper API

This module defines all URL routes for the application including:
- Admin interface
- API endpoints for news and search
- Scraper control endpoints
- API documentation

Author: Obaidulllah
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from apps.health import health_check
from apps.news.views_health import (
    health_check as advanced_health_check,
    readiness_check,
    metrics,
    prometheus_metrics,
)

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API Endpoints
    path('api/v1/', include([
        # News and Search API
        path('news/', include('apps.news.urls')),
        
        # Scraper Control API
        path('scraper/', include('apps.scraper.urls')),
    ])),
    
    # Shorthand API (without version prefix)
    path('api/', include([
        path('news/', include('apps.news.urls')),
        path('articles/', include('apps.news.urls')),
        path('scraper/', include('apps.scraper.urls')),
    ])),
    
    # Health Check Endpoints (Production-ready)
    path('api/health/', health_check, name='health-check'),
    path('health/', advanced_health_check, name='health-check-advanced'),
    path('health/ready/', readiness_check, name='readiness-check'),
    path('health/live/', advanced_health_check, name='liveness-check'),
    
    # Metrics Endpoints
    path('metrics/', metrics, name='metrics'),
    path('metrics/prometheus/', prometheus_metrics, name='prometheus-metrics'),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
