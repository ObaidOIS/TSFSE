/**
 * TypeScript Type Definitions for News Application
 * 
 * This module defines all TypeScript interfaces and types
 * used throughout the frontend application.
 * 
 * @author Obaid
 */

/**
 * Represents a news category
 */
export interface Category {
  /** Unique identifier */
  id: number;
  /** Category slug (economy, market, health, technology, industry) */
  name: string;
  /** Human-readable display name */
  display_name: string;
  /** Category description */
  description: string;
  /** Number of articles in this category */
  article_count: number;
}

/**
 * Represents an extracted keyword with relevance score
 */
export interface Keyword {
  /** The keyword text */
  word: string;
  /** Relevance score (0-1) */
  score: number;
}

/**
 * Represents extracted named entities
 */
export interface Entities {
  /** Organization names */
  organizations?: string[];
  /** Person names */
  people?: string[];
  /** Location names */
  locations?: string[];
  /** Monetary values */
  money?: string[];
  /** Date references */
  dates?: string[];
  /** Percentage values */
  percentages?: string[];
}

/**
 * Represents a news article in list/search views
 */
export interface ArticleListItem {
  /** Unique article identifier (UUID) */
  id: string;
  /** Article headline */
  title: string;
  /** Article summary */
  summary: string;
  /** Original Bloomberg URL */
  url: string;
  /** Article author(s) */
  author: string;
  /** Featured image URL */
  image_url: string | null;
  /** Category slug */
  category_name: string;
  /** Category display name */
  category_display: string;
  /** AI categorization confidence (0-1) */
  category_confidence: number;
  /** Extracted keywords */
  keywords: Keyword[];
  /** Publication timestamp */
  published_at: string;
  /** Scraping timestamp */
  scraped_at: string;
}

/**
 * Represents a full news article with all details
 */
export interface ArticleDetail extends Omit<ArticleListItem, 'category_name' | 'category_display'> {
  /** Full article content */
  content: string;
  /** Full category object */
  category: Category;
  /** List of keyword strings */
  keywords_list: string[];
  /** Named entities */
  entities: Entities;
  /** Database creation timestamp */
  created_at: string;
  /** Last update timestamp */
  updated_at: string;
}

/**
 * Parameters for search requests
 */
export interface SearchParams {
  /** Search query text */
  query: string;
  /** Optional category filter */
  category?: string;
  /** Page number (1-indexed) */
  page?: number;
  /** Results per page */
  page_size?: number;
  /** Sort order */
  sort_by?: 'relevance' | 'date' | '-date';
}

/**
 * Response from search API
 */
export interface SearchResponse {
  /** Original search query */
  query: string;
  /** AI-detected category from query */
  detected_category: string | null;
  /** Confidence of category detection */
  detected_category_confidence: number;
  /** Total number of matching results */
  total_results: number;
  /** Current page number */
  page: number;
  /** Results per page */
  page_size: number;
  /** Total number of pages */
  total_pages: number;
  /** Search execution time in milliseconds */
  execution_time_ms: number;
  /** Array of matching articles */
  results: ArticleListItem[];
}

/**
 * Scraper status and configuration
 */
export interface ScraperStatus {
  /** Unique identifier */
  id: number;
  /** Whether automatic fetching is enabled */
  is_active: boolean;
  /** Scraping interval in seconds */
  interval_seconds: number;
  /** Last scraper run timestamp */
  last_run_at: string | null;
  /** URL of most recently scraped article */
  last_article_url: string;
  /** Total articles fetched */
  articles_fetched_total: number;
  /** Last error message if any */
  last_error: string;
  /** Current status (running, disabled, error) */
  status: 'running' | 'disabled' | 'error';
  /** Last update timestamp */
  updated_at: string;
}

/**
 * Search statistics
 */
export interface SearchStats {
  /** Popular search queries */
  popular_searches: Array<{
    query: string;
    count: number;
  }>;
  /** Article counts by category */
  category_stats: Array<{
    name: string;
    display_name: string;
    article_count: number;
  }>;
  /** Total processed articles */
  total_articles: number;
  /** Total searches performed */
  total_searches: number;
}

/**
 * Paginated API response wrapper
 */
export interface PaginatedResponse<T> {
  /** Total item count */
  count: number;
  /** URL for next page */
  next: string | null;
  /** URL for previous page */
  previous: string | null;
  /** Array of items */
  results: T[];
}
