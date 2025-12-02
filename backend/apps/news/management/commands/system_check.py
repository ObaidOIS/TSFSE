"""
Custom Management Commands for Bloomberg News Application

This module provides CLI commands for:
- System health checks
- Database maintenance
- Cache management
- Scraper control

Usage:
    python manage.py system_check
    python manage.py system_check --full
    python manage.py system_check --json

Author: Obaidulllah
Created: December 2024
"""

import json
import sys
from datetime import datetime
from typing import Any, Dict

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone

from apps.news.models import Article, Category, SearchQuery, ScraperConfig


class Command(BaseCommand):
    """
    Comprehensive system health check command.
    
    Validates:
    - Database connectivity and performance
    - Cache (Redis) availability
    - Celery worker status
    - Scraper configuration
    - Data integrity
    
    Examples:
        # Basic health check
        python manage.py system_check
        
        # Full diagnostic report
        python manage.py system_check --full
        
        # JSON output for monitoring
        python manage.py system_check --json
    """
    
    help = 'Perform comprehensive system health checks'
    
    def add_arguments(self, parser):
        """Add command arguments."""
        parser.add_argument(
            '--full',
            action='store_true',
            help='Run full diagnostic including performance tests'
        )
        parser.add_argument(
            '--json',
            action='store_true',
            help='Output results as JSON'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix detected issues'
        )
    
    def handle(self, *args, **options):
        """Execute health checks."""
        self.is_json = options['json']
        self.is_full = options['full']
        self.should_fix = options['fix']
        
        results = {
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy',
            'checks': {},
            'issues': [],
            'recommendations': []
        }
        
        # Run all checks
        self._check_database(results)
        self._check_cache(results)
        self._check_celery(results)
        self._check_scraper_config(results)
        self._check_data_integrity(results)
        
        if self.is_full:
            self._check_performance(results)
            self._check_disk_usage(results)
        
        # Determine overall status
        if results['issues']:
            results['status'] = 'degraded' if len(results['issues']) < 3 else 'unhealthy'
        
        # Output results
        if self.is_json:
            self.stdout.write(json.dumps(results, indent=2, default=str))
        else:
            self._print_results(results)
        
        # Exit with appropriate code
        if results['status'] == 'unhealthy':
            sys.exit(2)
        elif results['status'] == 'degraded':
            sys.exit(1)
        sys.exit(0)
    
    def _check_database(self, results: Dict[str, Any]) -> None:
        """Check database connectivity and health."""
        check_name = 'database'
        try:
            # Basic connectivity
            with connection.cursor() as cursor:
                start = datetime.now()
                cursor.execute('SELECT 1')
                latency = (datetime.now() - start).total_seconds() * 1000
            
            # Check table counts
            article_count = Article.objects.count()
            category_count = Category.objects.count()
            
            results['checks'][check_name] = {
                'status': 'ok',
                'latency_ms': round(latency, 2),
                'articles': article_count,
                'categories': category_count,
            }
            
            if latency > 100:
                results['recommendations'].append(
                    'Database latency is high. Consider query optimization.'
                )
                
        except Exception as e:
            results['checks'][check_name] = {
                'status': 'error',
                'error': str(e)
            }
            results['issues'].append(f'Database error: {e}')
    
    def _check_cache(self, results: Dict[str, Any]) -> None:
        """Check Redis cache connectivity."""
        check_name = 'cache'
        try:
            # Write test
            test_key = 'health_check_test'
            test_value = timezone.now().isoformat()
            cache.set(test_key, test_value, timeout=10)
            
            # Read test
            retrieved = cache.get(test_key)
            
            if retrieved == test_value:
                results['checks'][check_name] = {
                    'status': 'ok',
                    'type': 'redis'
                }
            else:
                results['checks'][check_name] = {
                    'status': 'warning',
                    'message': 'Cache read/write mismatch'
                }
                results['issues'].append('Cache read/write mismatch')
                
            # Cleanup
            cache.delete(test_key)
            
        except Exception as e:
            results['checks'][check_name] = {
                'status': 'error',
                'error': str(e)
            }
            results['issues'].append(f'Cache error: {e}')
    
    def _check_celery(self, results: Dict[str, Any]) -> None:
        """Check Celery worker availability."""
        check_name = 'celery'
        try:
            from config.celery import app
            
            # Check if workers are responding
            inspector = app.control.inspect()
            active = inspector.active()
            
            if active:
                worker_count = len(active)
                task_count = sum(len(tasks) for tasks in active.values())
                
                results['checks'][check_name] = {
                    'status': 'ok',
                    'workers': worker_count,
                    'active_tasks': task_count
                }
            else:
                results['checks'][check_name] = {
                    'status': 'warning',
                    'message': 'No active workers found'
                }
                results['issues'].append('No Celery workers responding')
                results['recommendations'].append(
                    'Start Celery workers with: celery -A config worker -l INFO'
                )
                
        except Exception as e:
            results['checks'][check_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_scraper_config(self, results: Dict[str, Any]) -> None:
        """Check scraper configuration."""
        check_name = 'scraper'
        try:
            config = ScraperConfig.get_config()
            
            results['checks'][check_name] = {
                'status': 'ok' if config.is_active else 'inactive',
                'is_active': config.is_active,
                'interval_minutes': config.fetch_interval_minutes,
                'last_run': config.last_run_at.isoformat() if config.last_run_at else None,
                'total_fetched': config.articles_fetched_total,
                'last_error': config.last_error or None
            }
            
            if config.last_error:
                results['issues'].append(f'Last scraper error: {config.last_error}')
                
        except Exception as e:
            results['checks'][check_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_data_integrity(self, results: Dict[str, Any]) -> None:
        """Check data integrity."""
        check_name = 'data_integrity'
        try:
            # Articles without categories
            orphan_articles = Article.objects.filter(
                category__isnull=True,
                is_processed=True
            ).count()
            
            # Unprocessed articles
            unprocessed = Article.objects.filter(is_processed=False).count()
            
            # Duplicate URLs check
            from django.db.models import Count
            duplicates = Article.objects.values('url').annotate(
                count=Count('id')
            ).filter(count__gt=1).count()
            
            results['checks'][check_name] = {
                'status': 'ok' if (orphan_articles == 0 and duplicates == 0) else 'warning',
                'orphan_articles': orphan_articles,
                'unprocessed_articles': unprocessed,
                'duplicate_urls': duplicates
            }
            
            if orphan_articles > 0:
                results['issues'].append(
                    f'{orphan_articles} processed articles without category'
                )
            if duplicates > 0:
                results['issues'].append(f'{duplicates} duplicate URL entries')
                
            if self.should_fix and duplicates > 0:
                self._fix_duplicates()
                results['recommendations'].append('Duplicate URLs were removed')
                
        except Exception as e:
            results['checks'][check_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_performance(self, results: Dict[str, Any]) -> None:
        """Check system performance (full mode only)."""
        check_name = 'performance'
        try:
            import time
            
            # Database query performance
            start = time.perf_counter()
            list(Article.objects.all()[:100])
            db_time = (time.perf_counter() - start) * 1000
            
            # Cache performance
            start = time.perf_counter()
            for i in range(100):
                cache.set(f'perf_test_{i}', i, timeout=10)
            cache_write_time = (time.perf_counter() - start) * 1000
            
            start = time.perf_counter()
            for i in range(100):
                cache.get(f'perf_test_{i}')
            cache_read_time = (time.perf_counter() - start) * 1000
            
            # Cleanup
            for i in range(100):
                cache.delete(f'perf_test_{i}')
            
            results['checks'][check_name] = {
                'status': 'ok',
                'db_100_rows_ms': round(db_time, 2),
                'cache_100_writes_ms': round(cache_write_time, 2),
                'cache_100_reads_ms': round(cache_read_time, 2)
            }
            
        except Exception as e:
            results['checks'][check_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    def _check_disk_usage(self, results: Dict[str, Any]) -> None:
        """Check disk usage (full mode only)."""
        check_name = 'disk'
        try:
            import shutil
            
            total, used, free = shutil.disk_usage('/')
            
            results['checks'][check_name] = {
                'status': 'ok' if free > 1_000_000_000 else 'warning',
                'total_gb': round(total / (1024**3), 2),
                'used_gb': round(used / (1024**3), 2),
                'free_gb': round(free / (1024**3), 2),
                'usage_percent': round(used / total * 100, 1)
            }
            
            if free < 1_000_000_000:
                results['issues'].append('Low disk space (<1GB free)')
                
        except Exception as e:
            results['checks'][check_name] = {
                'status': 'error',
                'error': str(e)
            }
    
    def _fix_duplicates(self) -> None:
        """Remove duplicate URL entries, keeping the oldest."""
        from django.db.models import Min
        
        # Find duplicates
        duplicates = (
            Article.objects
            .values('url')
            .annotate(
                min_id=Min('id'),
                count=Count('id')
            )
            .filter(count__gt=1)
        )
        
        for dup in duplicates:
            Article.objects.filter(
                url=dup['url']
            ).exclude(
                id=dup['min_id']
            ).delete()
    
    def _print_results(self, results: Dict[str, Any]) -> None:
        """Print formatted results to console."""
        status_colors = {
            'healthy': self.style.SUCCESS,
            'degraded': self.style.WARNING,
            'unhealthy': self.style.ERROR,
        }
        
        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write(
            status_colors[results['status']](
                f"  System Status: {results['status'].upper()}"
            )
        )
        self.stdout.write('=' * 60)
        self.stdout.write('')
        
        for check_name, check_data in results['checks'].items():
            status = check_data.get('status', 'unknown')
            if status == 'ok':
                icon = self.style.SUCCESS('✓')
            elif status == 'warning':
                icon = self.style.WARNING('⚠')
            else:
                icon = self.style.ERROR('✗')
            
            self.stdout.write(f"  {icon} {check_name.upper()}")
            
            for key, value in check_data.items():
                if key != 'status':
                    self.stdout.write(f"      {key}: {value}")
            self.stdout.write('')
        
        if results['issues']:
            self.stdout.write(self.style.ERROR('  ISSUES:'))
            for issue in results['issues']:
                self.stdout.write(f"    • {issue}")
            self.stdout.write('')
        
        if results['recommendations']:
            self.stdout.write(self.style.WARNING('  RECOMMENDATIONS:'))
            for rec in results['recommendations']:
                self.stdout.write(f"    → {rec}")
            self.stdout.write('')
