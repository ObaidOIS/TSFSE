"""
Management command to run the Bloomberg scraper manually.

Usage:
    python manage.py run_scraper
    python manage.py run_scraper --categories economy market
    python manage.py run_scraper --process

Author: Obaidulllah
"""

from django.core.management.base import BaseCommand, CommandError
from apps.scraper.tasks import (
    check_for_new_articles,
    process_pending_articles,
    run_full_scrape,
)


class Command(BaseCommand):
    """
    Django management command to run the news scraper.
    
    This command allows manual execution of the scraper
    for testing or initial data population.
    """
    
    help = 'Run the Bloomberg news scraper'
    
    def add_arguments(self, parser):
        """
        Add command line arguments.
        
        Args:
            parser: ArgumentParser instance
        """
        parser.add_argument(
            '--categories',
            nargs='+',
            type=str,
            help='Specific categories to scrape (economy, market, health, technology, industry)'
        )
        parser.add_argument(
            '--process',
            action='store_true',
            help='Also process articles after scraping'
        )
        parser.add_argument(
            '--full',
            action='store_true',
            help='Run full scrape of all categories'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            dest='run_async',
            help='Run as async Celery task'
        )
    
    def handle(self, *args, **options):
        """
        Execute the command.
        
        Args:
            *args: Positional arguments
            **options: Keyword options from command line
        """
        categories = options.get('categories')
        process = options.get('process', False)
        full = options.get('full', False)
        run_async = options.get('run_async', False)
        
        self.stdout.write(self.style.NOTICE('Starting Bloomberg scraper...'))
        
        try:
            if run_async:
                # Run as Celery task
                if full:
                    task = run_full_scrape.delay()
                else:
                    task = check_for_new_articles.delay()
                
                self.stdout.write(
                    self.style.SUCCESS(f'Task queued: {task.id}')
                )
                return
            
            # Run synchronously
            if full:
                result = run_full_scrape()
            else:
                result = check_for_new_articles()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Scrape complete: {result.get('articles_saved', 0)} articles saved"
                )
            )
            
            if process:
                self.stdout.write(self.style.NOTICE('Processing articles...'))
                process_result = process_pending_articles()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Processed {process_result.get('processed', 0)} articles"
                    )
                )
                
        except Exception as e:
            raise CommandError(f'Scraper failed: {e}')
