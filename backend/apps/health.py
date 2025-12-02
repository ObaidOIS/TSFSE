"""
Health Check Endpoint

Simple health check for Docker and load balancer health checks.

Author: Obaidulllah
"""

from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.utils import timezone


def health_check(request):
    """
    Health check endpoint for monitoring
    
    Returns:
        JsonResponse with health status
    
    Checks:
        - Database connectivity
        - Redis connectivity
        - Basic application health
    """
    health_status = {
        'status': 'healthy',
        'timestamp': timezone.now().isoformat(),
        'checks': {}
    }
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        health_status['checks']['database'] = 'ok'
    except Exception as e:
        health_status['checks']['database'] = f'error: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis/cache
    try:
        cache.set('health_check', 'ok', timeout=1)
        cache_result = cache.get('health_check')
        if cache_result == 'ok':
            health_status['checks']['cache'] = 'ok'
        else:
            health_status['checks']['cache'] = 'error: value mismatch'
            health_status['status'] = 'unhealthy'
    except Exception as e:
        health_status['checks']['cache'] = f'error: {str(e)}'
        # Cache failure is not critical
    
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)
