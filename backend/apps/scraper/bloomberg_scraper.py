"""
Bloomberg News Scraper

This module provides the core scraping functionality for Bloomberg news.
It handles:
- Article extraction from Bloomberg.com
- RSS feed parsing for new article detection
- Change detection to trigger on new articles
- Content parsing and cleaning

Note: This scraper is designed for educational purposes. In production,
you should respect robots.txt and implement proper rate limiting.

Author: Obaidulllah
"""

import logging
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import feedparser

logger = logging.getLogger(__name__)


@dataclass
class ScrapedArticle:
    """
    Container for scraped article data.
    
    Attributes:
        title: Article headline
        content: Full article text
        summary: Article summary/description
        url: Original article URL
        author: Article author(s)
        published_at: Publication timestamp
        image_url: Featured image URL
        source_hash: Hash for change detection
    """
    title: str
    content: str
    summary: str
    url: str
    author: str
    published_at: Optional[datetime]
    image_url: Optional[str]
    source_hash: str


class BloombergScraper:
    """
    Web scraper for Bloomberg news articles.
    
    Provides functionality to:
    - Fetch and parse Bloomberg news articles
    - Monitor RSS feeds for new content
    - Detect changes in article listings
    - Extract structured content from pages
    
    The scraper uses multiple strategies:
    1. RSS feed monitoring (preferred - lowest impact)
    2. Section page scraping (fallback)
    3. Individual article parsing
    
    Attributes:
        base_url: Bloomberg base URL
        rss_feeds: Dictionary of category to RSS feed URLs
        headers: HTTP headers for requests
        session: Requests session for connection pooling
    
    Example:
        >>> scraper = BloombergScraper()
        >>> new_articles = scraper.check_for_new_articles()
        >>> for article in new_articles:
        ...     print(f"New: {article.title}")
    """
    
    # Bloomberg base URL
    BASE_URL = 'https://www.bloomberg.com'
    
    # RSS feeds for different categories (Bloomberg public feeds)
    RSS_FEEDS = {
        'economy': 'https://feeds.bloomberg.com/economics/news.rss',
        'market': 'https://feeds.bloomberg.com/markets/news.rss',
        'technology': 'https://feeds.bloomberg.com/technology/news.rss',
        'industry': 'https://feeds.bloomberg.com/industries/news.rss',
    }
    
    # Fallback: Section URLs for scraping
    SECTION_URLS = {
        'economy': '/economics',
        'market': '/markets',
        'health': '/health',  # Note: No direct RSS for health
        'technology': '/technology',
        'industry': '/industries',
    }
    
    def __init__(self):
        """
        Initialize the Bloomberg scraper.
        
        Sets up HTTP session with appropriate headers and
        initializes tracking for change detection.
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                         'Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                     'image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Cache for seen article URLs
        self._seen_urls: set = set()
        
    def check_for_new_articles(
        self,
        categories: Optional[List[str]] = None,
        max_articles: int = 50
    ) -> List[ScrapedArticle]:
        """
        Check for new articles across specified categories.
        
        This method checks RSS feeds and section pages for new articles
        that haven't been seen before. Uses change detection to identify
        genuinely new content.
        
        Args:
            categories: List of categories to check (default: all)
            max_articles: Maximum number of articles to return
            
        Returns:
            List[ScrapedArticle]: List of newly discovered articles
        """
        if categories is None:
            categories = list(self.RSS_FEEDS.keys())
        
        new_articles = []
        
        for category in categories:
            try:
                # Try RSS feed first (preferred method)
                if category in self.RSS_FEEDS:
                    articles = self._fetch_from_rss(category)
                else:
                    # Fall back to section page scraping
                    articles = self._fetch_from_section(category)
                
                # Filter for new articles
                for article in articles:
                    if article.url not in self._seen_urls:
                        new_articles.append(article)
                        self._seen_urls.add(article.url)
                        
                        if len(new_articles) >= max_articles:
                            return new_articles
                            
            except Exception as e:
                logger.error(f"Error checking {category}: {e}")
                continue
        
        logger.info(f"Found {len(new_articles)} new articles")
        return new_articles
    
    def _fetch_from_rss(self, category: str) -> List[ScrapedArticle]:
        """
        Fetch articles from RSS feed.
        
        RSS feeds are the preferred method as they:
        - Have lower server impact
        - Provide structured data
        - Include publication dates
        
        Args:
            category: Category name
            
        Returns:
            List[ScrapedArticle]: Articles from RSS feed
        """
        feed_url = self.RSS_FEEDS.get(category)
        if not feed_url:
            return []
        
        try:
            feed = feedparser.parse(feed_url)
            articles = []
            
            for entry in feed.entries[:20]:  # Limit per feed
                try:
                    article = ScrapedArticle(
                        title=entry.get('title', ''),
                        content='',  # Will be fetched separately if needed
                        summary=entry.get('summary', entry.get('description', '')),
                        url=entry.get('link', ''),
                        author=entry.get('author', ''),
                        published_at=self._parse_date(entry.get('published')),
                        image_url=self._extract_image_from_entry(entry),
                        source_hash=self._compute_hash(entry.get('link', ''))
                    )
                    
                    if article.url and article.title:
                        articles.append(article)
                        
                except Exception as e:
                    logger.warning(f"Error parsing RSS entry: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
            return []
    
    def _fetch_from_section(self, category: str) -> List[ScrapedArticle]:
        """
        Fetch articles from section page (fallback method).
        
        Used when RSS feed is not available for a category.
        
        Args:
            category: Category name
            
        Returns:
            List[ScrapedArticle]: Articles from section page
        """
        section_path = self.SECTION_URLS.get(category)
        if not section_path:
            return []
        
        url = f"{self.BASE_URL}{section_path}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            articles = []
            
            # Find article links (Bloomberg's structure)
            article_elements = soup.find_all('article') or soup.find_all(
                'a', href=re.compile(r'/news/articles/')
            )
            
            for element in article_elements[:20]:
                try:
                    article = self._parse_article_element(element, category)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.warning(f"Error parsing article element: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching section page {url}: {e}")
            return []
    
    def fetch_article_content(self, url: str) -> Optional[str]:
        """
        Fetch full article content from URL.
        
        Args:
            url: Article URL
            
        Returns:
            str: Full article text content or None
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try multiple selectors for article content
            content_selectors = [
                'article[data-component="article-body"]',
                '.body-content',
                '.article-body',
                'article .body',
                '.article__body',
            ]
            
            content = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    # Get text from paragraphs
                    paragraphs = element.find_all('p')
                    content = '\n\n'.join(p.get_text().strip() for p in paragraphs)
                    break
            
            if not content:
                # Fallback: Get all paragraphs from main content area
                main = soup.find('main') or soup.find('article')
                if main:
                    paragraphs = main.find_all('p')
                    content = '\n\n'.join(p.get_text().strip() for p in paragraphs)
            
            return content if content else None
            
        except Exception as e:
            logger.error(f"Error fetching article content from {url}: {e}")
            return None
    
    def _parse_article_element(
        self,
        element,
        category: str
    ) -> Optional[ScrapedArticle]:
        """
        Parse an article element from HTML.
        
        Args:
            element: BeautifulSoup element
            category: Category name
            
        Returns:
            ScrapedArticle or None
        """
        # Try to find title
        title_elem = element.find(['h1', 'h2', 'h3', 'a'])
        if not title_elem:
            return None
        
        title = title_elem.get_text().strip()
        
        # Find link
        link_elem = element.find('a', href=True) or element
        if not link_elem.get('href'):
            return None
        
        url = urljoin(self.BASE_URL, link_elem['href'])
        
        # Find summary
        summary_elem = element.find(['p', 'div'], class_=re.compile(r'summary|desc'))
        summary = summary_elem.get_text().strip() if summary_elem else ''
        
        # Find image
        img_elem = element.find('img', src=True)
        image_url = img_elem['src'] if img_elem else None
        
        return ScrapedArticle(
            title=title,
            content='',
            summary=summary,
            url=url,
            author='',
            published_at=None,
            image_url=image_url,
            source_hash=self._compute_hash(url)
        )
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """
        Parse date string to datetime object.
        
        Args:
            date_str: Date string from RSS or HTML
            
        Returns:
            datetime or None
        """
        if not date_str:
            return None
        
        try:
            from dateutil import parser
            return parser.parse(date_str)
        except Exception:
            return None
    
    def _extract_image_from_entry(self, entry) -> Optional[str]:
        """
        Extract image URL from RSS entry.
        
        Args:
            entry: feedparser entry object
            
        Returns:
            str: Image URL or None
        """
        # Try media:content
        if hasattr(entry, 'media_content') and entry.media_content:
            for media in entry.media_content:
                if 'image' in media.get('type', ''):
                    return media.get('url')
        
        # Try enclosure
        if hasattr(entry, 'enclosures') and entry.enclosures:
            for enc in entry.enclosures:
                if 'image' in enc.get('type', ''):
                    return enc.get('url')
        
        # Try to find in summary
        if hasattr(entry, 'summary'):
            soup = BeautifulSoup(entry.summary, 'html.parser')
            img = soup.find('img', src=True)
            if img:
                return img['src']
        
        return None
    
    def _compute_hash(self, content: str) -> str:
        """
        Compute hash for change detection.
        
        Args:
            content: Content to hash
            
        Returns:
            str: SHA256 hash
        """
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def clear_seen_cache(self):
        """Clear the cache of seen URLs."""
        self._seen_urls.clear()
        logger.info("Cleared seen URLs cache")


# Alternative scraper using mock data for development
class MockBloombergScraper:
    """
    Mock scraper for development and testing.
    
    Provides realistic sample data without making actual
    HTTP requests. Useful for:
    - Local development
    - Testing
    - Demo purposes
    """
    
    SAMPLE_ARTICLES = [
        {
            'title': 'Federal Reserve Signals Potential Rate Cuts in 2024',
            'summary': 'The Federal Reserve indicated it may begin cutting interest rates next year as inflation shows signs of cooling.',
            'category': 'economy',
            'author': 'Bloomberg Economics'
        },
        {
            'title': 'Oil Prices Surge Amid Middle East Tensions',
            'summary': 'Crude oil prices jumped 3% as geopolitical concerns raised fears of supply disruptions.',
            'category': 'market',
            'author': 'Bloomberg Markets'
        },
        {
            'title': 'New Cancer Treatment Shows Promise in Clinical Trials',
            'summary': 'A novel immunotherapy approach demonstrated significant efficacy against solid tumors in Phase 3 trials.',
            'category': 'health',
            'author': 'Bloomberg Health'
        },
        {
            'title': 'Apple Unveils Next-Generation AI Chip for iPhones',
            'summary': 'Apple announced its latest neural engine chip, promising 40% faster machine learning performance.',
            'category': 'technology',
            'author': 'Bloomberg Technology'
        },
        {
            'title': 'Tesla Opens New Gigafactory in Mexico',
            'summary': 'The electric vehicle maker began production at its newest manufacturing facility in Monterrey.',
            'category': 'industry',
            'author': 'Bloomberg Industries'
        },
        {
            'title': 'S&P 500 Hits Record High on Tech Rally',
            'summary': 'The benchmark index reached a new all-time high, driven by gains in technology stocks.',
            'category': 'market',
            'author': 'Bloomberg Markets'
        },
        {
            'title': 'GDP Growth Exceeds Expectations at 4.2%',
            'summary': 'The U.S. economy grew faster than anticipated in the third quarter, boosted by consumer spending.',
            'category': 'economy',
            'author': 'Bloomberg Economics'
        },
        {
            'title': 'Microsoft Launches New AI Assistant for Enterprise',
            'summary': 'The tech giant introduced an AI-powered productivity tool integrated with Office 365.',
            'category': 'technology',
            'author': 'Bloomberg Technology'
        },
    ]
    
    def __init__(self):
        """Initialize the mock scraper."""
        self._article_index = 0
        self._seen_urls = set()
    
    def check_for_new_articles(
        self,
        categories: Optional[List[str]] = None,
        max_articles: int = 50
    ) -> List[ScrapedArticle]:
        """
        Return sample articles for testing.
        
        Args:
            categories: Categories to filter
            max_articles: Maximum articles to return
            
        Returns:
            List[ScrapedArticle]: Sample articles
        """
        import random
        from datetime import datetime, timedelta
        
        articles = []
        
        for i, data in enumerate(self.SAMPLE_ARTICLES):
            if categories and data['category'] not in categories:
                continue
            
            url = f"https://www.bloomberg.com/news/articles/2024-01-{i+1:02d}/sample-{i}"
            
            if url in self._seen_urls:
                continue
            
            self._seen_urls.add(url)
            
            # Generate random published date within last week
            published = datetime.now() - timedelta(
                days=random.randint(0, 7),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )
            
            article = ScrapedArticle(
                title=data['title'],
                content=f"{data['summary']}\n\n" + "Lorem ipsum dolor sit amet. " * 50,
                summary=data['summary'],
                url=url,
                author=data['author'],
                published_at=published,
                image_url=f"https://assets.bwbx.io/images/sample-{i}.jpg",
                source_hash=hashlib.sha256(url.encode()).hexdigest()[:16]
            )
            
            articles.append(article)
            
            if len(articles) >= max_articles:
                break
        
        return articles
    
    def fetch_article_content(self, url: str) -> Optional[str]:
        """Return mock content for URL."""
        return "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 100
    
    def clear_seen_cache(self):
        """Clear seen URLs cache."""
        self._seen_urls.clear()


def get_scraper(use_mock: bool = False) -> BloombergScraper:
    """
    Get the appropriate scraper instance.
    
    Args:
        use_mock: Whether to use mock scraper
        
    Returns:
        Scraper instance
    """
    if use_mock:
        return MockBloombergScraper()
    return BloombergScraper()
