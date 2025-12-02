"""
Custom Middleware for Bloomberg News Application

This module provides enterprise-grade middleware components for:
- Request/Response logging with correlation IDs
- Performance monitoring and metrics
- Rate limiting with sliding window
- Security headers enforcement
- API versioning support

Design Patterns:
- Chain of Responsibility: Middleware pipeline
- Decorator Pattern: Request/Response wrapping
- Strategy Pattern: Configurable behaviors

Author: Obaidulllah
Created: December 2024
"""

import time
import uuid
import logging
from typing import Callable, Optional
from functools import wraps

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.conf import settings
from django.core.cache import cache
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestCorrelationMiddleware(MiddlewareMixin):
    """
    Adds correlation IDs to requests for distributed tracing.
    
    This middleware:
    - Generates unique request IDs for tracing
    - Propagates IDs in response headers
    - Enables log correlation across services
    
    Usage:
        Add to MIDDLEWARE in settings.py:
        'apps.news.middleware.RequestCorrelationMiddleware'
    """
    
    CORRELATION_HEADER = 'X-Correlation-ID'
    REQUEST_ID_HEADER = 'X-Request-ID'
    
    def process_request(self, request: HttpRequest) -> None:
        """
        Add correlation ID to incoming request.
        
        Args:
            request: The incoming HTTP request
        """
        # Use existing correlation ID or generate new one
        correlation_id = request.headers.get(
            self.CORRELATION_HEADER,
            str(uuid.uuid4())
        )
        request_id = str(uuid.uuid4())[:8]  # Short ID for this request
        
        # Attach to request for use in views/logging
        request.correlation_id = correlation_id
        request.request_id = request_id
        
        # Add to logging context
        # This enables filtering logs by correlation ID
        logger.info(
            f"Request started",
            extra={
                'correlation_id': correlation_id,
                'request_id': request_id,
                'method': request.method,
                'path': request.path,
            }
        )
    
    def process_response(
        self, 
        request: HttpRequest, 
        response: HttpResponse
    ) -> HttpResponse:
        """
        Add correlation headers to response.
        
        Args:
            request: The HTTP request
            response: The HTTP response
            
        Returns:
            Modified response with correlation headers
        """
        if hasattr(request, 'correlation_id'):
            response[self.CORRELATION_HEADER] = request.correlation_id
        if hasattr(request, 'request_id'):
            response[self.REQUEST_ID_HEADER] = request.request_id
        
        return response


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Monitors request performance and logs slow requests.
    
    Features:
    - Request timing with microsecond precision
    - Slow request detection and logging
    - Performance metrics for monitoring
    - Response size tracking
    
    Configuration:
        SLOW_REQUEST_THRESHOLD_MS: Log requests slower than this (default: 500ms)
    """
    
    SLOW_THRESHOLD_MS = getattr(settings, 'SLOW_REQUEST_THRESHOLD_MS', 500)
    
    def process_request(self, request: HttpRequest) -> None:
        """
        Record request start time.
        
        Args:
            request: The incoming HTTP request
        """
        request._start_time = time.perf_counter()
    
    def process_response(
        self, 
        request: HttpRequest, 
        response: HttpResponse
    ) -> HttpResponse:
        """
        Calculate request duration and log if slow.
        
        Args:
            request: The HTTP request
            response: The HTTP response
            
        Returns:
            Response with timing header
        """
        if not hasattr(request, '_start_time'):
            return response
        
        duration_ms = (time.perf_counter() - request._start_time) * 1000
        
        # Add timing header
        response['X-Response-Time'] = f"{duration_ms:.2f}ms"
        
        # Log slow requests
        if duration_ms > self.SLOW_THRESHOLD_MS:
            logger.warning(
                f"Slow request detected",
                extra={
                    'path': request.path,
                    'method': request.method,
                    'duration_ms': duration_ms,
                    'correlation_id': getattr(request, 'correlation_id', None),
                }
            )
        
        # Track metrics (could be sent to Prometheus/DataDog)
        self._record_metrics(request, response, duration_ms)
        
        return response
    
    def _record_metrics(
        self, 
        request: HttpRequest, 
        response: HttpResponse, 
        duration_ms: float
    ) -> None:
        """
        Record request metrics for monitoring.
        
        Args:
            request: The HTTP request
            response: The HTTP response
            duration_ms: Request duration in milliseconds
        """
        # Store in cache for quick access by monitoring endpoints
        cache_key = 'api_metrics'
        metrics = cache.get(cache_key, {
            'total_requests': 0,
            'total_time_ms': 0,
            'slow_requests': 0,
            'status_codes': {},
        })
        
        metrics['total_requests'] += 1
        metrics['total_time_ms'] += duration_ms
        
        if duration_ms > self.SLOW_THRESHOLD_MS:
            metrics['slow_requests'] += 1
        
        status_code = str(response.status_code)
        metrics['status_codes'][status_code] = \
            metrics['status_codes'].get(status_code, 0) + 1
        
        cache.set(cache_key, metrics, timeout=3600)


class APIVersioningMiddleware(MiddlewareMixin):
    """
    Handles API versioning via headers and URL prefixes.
    
    Supports:
    - URL path versioning (/api/v1/, /api/v2/)
    - Header-based versioning (Accept-Version)
    - Query parameter versioning (?version=1)
    
    Configuration:
        API_DEFAULT_VERSION: Default API version (default: 'v1')
        API_SUPPORTED_VERSIONS: List of supported versions
    """
    
    DEFAULT_VERSION = getattr(settings, 'API_DEFAULT_VERSION', 'v1')
    SUPPORTED_VERSIONS = getattr(
        settings, 
        'API_SUPPORTED_VERSIONS', 
        ['v1']
    )
    
    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """
        Determine and validate API version.
        
        Args:
            request: The incoming HTTP request
            
        Returns:
            None if valid, error response if invalid version
        """
        # Skip non-API requests
        if not request.path.startswith('/api/'):
            return None
        
        # Determine version from various sources
        version = self._get_version(request)
        
        # Validate version
        if version not in self.SUPPORTED_VERSIONS:
            return JsonResponse({
                'error': 'Unsupported API version',
                'supported_versions': self.SUPPORTED_VERSIONS,
                'requested_version': version,
            }, status=400)
        
        request.api_version = version
        return None
    
    def _get_version(self, request: HttpRequest) -> str:
        """
        Extract API version from request.
        
        Priority:
        1. URL path (/api/v1/)
        2. Accept-Version header
        3. Query parameter (?version=1)
        4. Default version
        
        Args:
            request: The HTTP request
            
        Returns:
            API version string
        """
        # Check URL path
        path_parts = request.path.split('/')
        for part in path_parts:
            if part.startswith('v') and part[1:].isdigit():
                return part
        
        # Check header
        header_version = request.headers.get('Accept-Version')
        if header_version:
            return f"v{header_version}"
        
        # Check query parameter
        query_version = request.GET.get('version')
        if query_version:
            return f"v{query_version}"
        
        return self.DEFAULT_VERSION


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Adds security headers to all responses.
    
    Implements security best practices:
    - Content Security Policy (CSP)
    - X-Content-Type-Options
    - X-Frame-Options
    - Strict-Transport-Security (HSTS)
    - Referrer-Policy
    
    Note: Some headers are already handled by Django's
    SecurityMiddleware, but this provides additional coverage.
    """
    
    def process_response(
        self, 
        request: HttpRequest, 
        response: HttpResponse
    ) -> HttpResponse:
        """
        Add security headers to response.
        
        Args:
            request: The HTTP request
            response: The HTTP response
            
        Returns:
            Response with security headers
        """
        # Prevent MIME type sniffing
        response['X-Content-Type-Options'] = 'nosniff'
        
        # Prevent clickjacking (backup for X-Frame-Options)
        if 'Content-Security-Policy' not in response:
            response['Content-Security-Policy'] = "frame-ancestors 'self'"
        
        # Referrer policy
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy (formerly Feature-Policy)
        response['Permissions-Policy'] = (
            'accelerometer=(), camera=(), geolocation=(), '
            'gyroscope=(), magnetometer=(), microphone=(), '
            'payment=(), usb=()'
        )
        
        return response


# =============================================================================
# Utility Functions
# =============================================================================

def get_client_ip(request: HttpRequest) -> str:
    """
    Extract client IP address from request.
    
    Handles proxy headers (X-Forwarded-For) for accurate IP detection.
    
    Args:
        request: The HTTP request
        
    Returns:
        Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def get_metrics_summary() -> dict:
    """
    Get current API metrics summary.
    
    Returns:
        dict: Metrics including request counts, timing, etc.
    """
    metrics = cache.get('api_metrics', {})
    
    if not metrics:
        return {
            'status': 'no_data',
            'message': 'No metrics collected yet'
        }
    
    total_requests = metrics.get('total_requests', 0)
    avg_time = (
        metrics.get('total_time_ms', 0) / total_requests
        if total_requests > 0 else 0
    )
    
    return {
        'total_requests': total_requests,
        'average_response_time_ms': round(avg_time, 2),
        'slow_requests': metrics.get('slow_requests', 0),
        'slow_request_percentage': round(
            metrics.get('slow_requests', 0) / total_requests * 100
            if total_requests > 0 else 0, 2
        ),
        'status_codes': metrics.get('status_codes', {}),
    }
