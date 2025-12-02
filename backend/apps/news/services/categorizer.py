"""
AI-Powered Categorization Service

This module provides text categorization using
lightweight keyword-based classification for automatic news article classification.

Features:
- Fast keyword-based classification
- Keyword extraction using TF-IDF
- Named Entity Recognition using regex patterns
- Category detection from search queries

Author: Obaidulllah
"""

import logging
from typing import Dict, List, Tuple, Optional
from functools import lru_cache
import re
from collections import Counter

from django.conf import settings

logger = logging.getLogger(__name__)


class CategoryDetector:
    """
    Lightweight category detection for news articles and search queries.
    
    Uses keyword matching for fast, resource-efficient detection.
    No heavy ML models required.
    
    Attributes:
        categories: List of valid category names
        keyword_patterns: Compiled regex patterns for each category
    """
    
    # Category keywords for fast rule-based detection
    CATEGORY_KEYWORDS = {
        'economy': [
            'economy', 'economic', 'gdp', 'inflation', 'recession', 'growth',
            'federal reserve', 'fed', 'central bank', 'monetary policy',
            'fiscal policy', 'budget', 'deficit', 'surplus', 'employment',
            'unemployment', 'jobs report', 'labor market', 'wages', 'income',
            'consumer spending', 'retail sales', 'housing market', 'mortgage',
            'interest rate', 'treasury', 'bond yield', 'economic indicator',
            'rate cut', 'rate hike', 'cpi', 'ppi', 'gdp growth'
        ],
        'market': [
            'market', 'stock', 'stocks', 'shares', 'equity', 'equities',
            'commodity', 'commodities', 'oil', 'gold', 'silver', 'copper',
            'wheat', 'corn', 'trading', 'traders', 'wall street', 'nasdaq',
            's&p 500', 'dow jones', 'futures', 'options', 'derivatives',
            'forex', 'currency', 'exchange rate', 'bitcoin', 'crypto',
            'hedge fund', 'etf', 'index', 'bull market', 'bear market',
            'rally', 'selloff', 'ipo', 'earnings', 'dividend', 'yield',
            'investor', 'investment', 'portfolio', 'asset', 'securities'
        ],
        'health': [
            'health', 'healthcare', 'medical', 'medicine', 'hospital',
            'doctor', 'patient', 'disease', 'treatment', 'vaccine',
            'pharmaceutical', 'drug', 'fda', 'clinical trial', 'therapy',
            'cancer', 'diabetes', 'heart', 'mental health', 'pandemic',
            'epidemic', 'virus', 'covid', 'public health', 'insurance',
            'medicare', 'medicaid', 'biotech', 'wellness', 'nutrition'
        ],
        'technology': [
            'technology', 'tech', 'software', 'hardware', 'computer',
            'ai', 'artificial intelligence', 'machine learning', 'data',
            'cloud', 'cybersecurity', 'cyber', 'hack', 'digital',
            'internet', 'app', 'smartphone', 'apple', 'google', 'microsoft',
            'amazon', 'meta', 'facebook', 'startup', 'silicon valley',
            'semiconductor', 'chip', 'processor', '5g', 'blockchain',
            'automation', 'robot', 'quantum', 'virtual reality', 'ar', 'vr',
            'nvidia', 'openai', 'chatgpt', 'llm', 'gpu'
        ],
        'industry': [
            'industry', 'industrial', 'manufacturing', 'factory', 'production',
            'automotive', 'auto', 'car', 'vehicle', 'ev', 'electric vehicle',
            'aerospace', 'airline', 'aviation', 'shipping', 'logistics',
            'supply chain', 'retail', 'consumer goods', 'construction',
            'real estate', 'energy', 'renewable', 'solar', 'wind', 'oil gas',
            'mining', 'steel', 'chemical', 'agriculture', 'food', 'beverage',
            'textile', 'apparel', 'luxury', 'entertainment', 'media'
        ]
    }
    
    def __init__(self):
        """Initialize the category detector with compiled patterns."""
        self.categories = settings.AI_CONFIG.get(
            'CATEGORIES',
            ['economy', 'market', 'health', 'technology', 'industry']
        )
        self._compile_patterns()
        logger.info("CategoryDetector initialized (keyword-based)")
    
    def _compile_patterns(self):
        """Compile regex patterns for keyword matching."""
        self.keyword_patterns = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.keyword_patterns[category] = re.compile(pattern, re.IGNORECASE)
    
    def categorize_text(
        self,
        text: str,
        use_ai: bool = False  # Disabled by default for performance
    ) -> Tuple[str, float]:
        """
        Categorize text into one of the predefined categories.
        
        Uses fast keyword matching approach.
        
        Args:
            text: Text to categorize (title + content)
            use_ai: Ignored (kept for API compatibility)
            
        Returns:
            Tuple[str, float]: (category_name, confidence_score)
        """
        if not text or not text.strip():
            return 'economy', 0.0
        
        return self._keyword_categorize(text)
    
    def _keyword_categorize(self, text: str) -> Tuple[str, float]:
        """
        Categorize using keyword matching.
        
        Args:
            text: Text to categorize
            
        Returns:
            Tuple[str, float]: (category, confidence)
        """
        text_lower = text.lower()
        scores = {}
        
        for category, pattern in self.keyword_patterns.items():
            matches = pattern.findall(text_lower)
            # Score based on unique keyword matches
            unique_matches = set(m.lower() for m in matches)
            scores[category] = len(unique_matches)
        
        if not scores or max(scores.values()) == 0:
            return 'economy', 0.3  # Default with low confidence
        
        # Find best category
        best_category = max(scores, key=scores.get)
        max_score = scores[best_category]
        total_score = sum(scores.values())
        
        # Calculate confidence (more matches = higher confidence)
        confidence = min(max_score / 3, 1.0)  # 3+ matches = full confidence
        if total_score > max_score:
            # Reduce confidence if other categories also match
            confidence *= (max_score / total_score) * 1.2
            confidence = min(confidence, 1.0)
        
        return best_category, round(confidence, 2)
    
    def detect_category_from_query(self, query: str) -> Tuple[Optional[str], float]:
        """
        Detect category from a search query.
        
        Uses lightweight keyword matching for fast response.
        
        Args:
            query: Search query text
            
        Returns:
            Tuple[Optional[str], float]: (category or None, confidence)
        """
        if not query or not query.strip():
            return None, 0.0
        
        # Use keyword matching for speed
        result = self._keyword_categorize(query)
        
        # Only return category if confidence is reasonable
        if result[1] >= 0.3:
            return result
        
        return None, 0.0


class KeywordExtractor:
    """
    Lightweight keyword extraction using word frequency.
    No heavy ML models required.
    """
    
    # Common English stopwords
    STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
        'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
        'were', 'been', 'be', 'have', 'has', 'had', 'do', 'does', 'did',
        'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'that', 'this', 'these', 'those', 'it', 'its', 'they', 'their',
        'we', 'you', 'he', 'she', 'who', 'which', 'what', 'when', 'where',
        'how', 'why', 'all', 'each', 'every', 'both', 'few', 'more', 'most',
        'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'can', 'just', 'should', 'now', 'also',
        'said', 'says', 'new', 'year', 'years', 'one', 'two', 'first', 'last'
    }
    
    def __init__(self):
        """Initialize the keyword extractor."""
        logger.info("KeywordExtractor initialized (frequency-based)")
    
    def extract_keywords(
        self,
        text: str,
        max_keywords: int = 10
    ) -> List[Dict[str, float]]:
        """
        Extract keywords from text using word frequency.
        
        Args:
            text: Text to extract keywords from
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List[Dict]: List of {word: str, score: float}
        """
        if not text or not text.strip():
            return []
        
        # Tokenize and filter
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        words = [w for w in words if w not in self.STOPWORDS]
        
        if not words:
            return []
        
        counter = Counter(words)
        total = sum(counter.values())
        
        return [
            {'word': word, 'score': round(count / total, 4)}
            for word, count in counter.most_common(max_keywords)
        ]


class EntityExtractor:
    """
    Lightweight named entity extraction using regex patterns.
    No spaCy or heavy NLP models required.
    """
    
    # Known company names (add more as needed)
    KNOWN_COMPANIES = {
        'apple', 'google', 'microsoft', 'amazon', 'meta', 'facebook', 'tesla',
        'nvidia', 'netflix', 'twitter', 'uber', 'lyft', 'airbnb', 'spotify',
        'salesforce', 'oracle', 'ibm', 'intel', 'amd', 'qualcomm', 'cisco',
        'jpmorgan', 'goldman sachs', 'morgan stanley', 'bank of america',
        'wells fargo', 'citigroup', 'blackrock', 'vanguard', 'berkshire',
        'walmart', 'target', 'costco', 'home depot', 'starbucks', 'mcdonalds',
        'pfizer', 'moderna', 'johnson & johnson', 'merck', 'abbvie',
        'exxon', 'chevron', 'shell', 'bp', 'conocophillips',
        'boeing', 'airbus', 'lockheed martin', 'raytheon', 'general electric',
        'ford', 'gm', 'toyota', 'volkswagen', 'bmw', 'mercedes', 'honda'
    }
    
    def __init__(self):
        """Initialize the entity extractor."""
        # Compile regex patterns
        self.money_pattern = re.compile(r'\$[\d,]+(?:\.\d+)?(?:\s*(?:million|billion|trillion|[BMT]))?', re.I)
        self.percent_pattern = re.compile(r'\d+(?:\.\d+)?(?:\s*)?%')
        self.company_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(c) for c in self.KNOWN_COMPANIES) + r')\b',
            re.IGNORECASE
        )
        logger.info("EntityExtractor initialized (regex-based)")
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text using regex patterns.
        
        Args:
            text: Text to extract entities from
            
        Returns:
            Dict: {entity_type: [entity_values]}
        """
        if not text or not text.strip():
            return {}
        
        entities = {}
        
        # Extract money amounts
        money = list(set(self.money_pattern.findall(text)))
        if money:
            entities['money'] = money[:10]
        
        # Extract percentages
        percentages = list(set(self.percent_pattern.findall(text)))
        if percentages:
            entities['percentages'] = percentages[:10]
        
        # Extract known companies
        companies = list(set(m.title() for m in self.company_pattern.findall(text)))
        if companies:
            entities['organizations'] = companies[:10]
        
        # Extract capitalized phrases (potential company/person names)
        cap_pattern = re.compile(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b')
        capitalized = list(set(cap_pattern.findall(text)))
        if capitalized and 'organizations' not in entities:
            entities['organizations'] = capitalized[:5]
        
        return entities


# Singleton instances
_category_detector = None
_keyword_extractor = None
_entity_extractor = None


def get_category_detector() -> CategoryDetector:
    """Get singleton CategoryDetector instance."""
    global _category_detector
    if _category_detector is None:
        _category_detector = CategoryDetector()
    return _category_detector


def get_keyword_extractor() -> KeywordExtractor:
    """Get singleton KeywordExtractor instance."""
    global _keyword_extractor
    if _keyword_extractor is None:
        _keyword_extractor = KeywordExtractor()
    return _keyword_extractor


def get_entity_extractor() -> EntityExtractor:
    """Get singleton EntityExtractor instance."""
    global _entity_extractor
    if _entity_extractor is None:
        _entity_extractor = EntityExtractor()
    return _entity_extractor
