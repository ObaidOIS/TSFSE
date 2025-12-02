"""
Scraper App Serializers

Serializers for scraper data representation.

Author: Obaidulllah
"""

from rest_framework import serializers


class ScraperStatusSerializer(serializers.Serializer):
    """Serializer for scraper status response"""
    enabled = serializers.BooleanField()
    last_scrape = serializers.DateTimeField(allow_null=True)
    status = serializers.CharField()
    
    class StatisticsSerializer(serializers.Serializer):
        articles_today = serializers.IntegerField()
        articles_week = serializers.IntegerField()
        total_articles = serializers.IntegerField()
    
    statistics = StatisticsSerializer()


class ScraperToggleSerializer(serializers.Serializer):
    """Serializer for toggle request"""
    fetch = serializers.BooleanField(required=False)


class ScraperToggleResponseSerializer(serializers.Serializer):
    """Serializer for toggle response"""
    fetch = serializers.BooleanField()
    message = serializers.CharField()
    timestamp = serializers.DateTimeField()


class ScraperTriggerResponseSerializer(serializers.Serializer):
    """Serializer for manual trigger response"""
    message = serializers.CharField()
    task_id = serializers.CharField()
    timestamp = serializers.DateTimeField()


class ScrapedArticleSerializer(serializers.Serializer):
    """Serializer for scraped article in history"""
    id = serializers.IntegerField()
    title = serializers.CharField()
    source_url = serializers.URLField()
    scraped_at = serializers.DateTimeField()
    category__name = serializers.CharField()
    category_confidence = serializers.FloatField()


class ScraperHistorySerializer(serializers.Serializer):
    """Serializer for scraping history response"""
    count = serializers.IntegerField()
    articles = ScrapedArticleSerializer(many=True)


class ScraperFeedsSerializer(serializers.Serializer):
    """Serializer for RSS feeds list"""
    feeds = serializers.ListField(child=serializers.URLField())
    count = serializers.IntegerField()
