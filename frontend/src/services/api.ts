/**
 * API Service for Bloomberg News Application
 * 
 * This module provides functions to interact with the Django REST API.
 * All API calls are centralized here for maintainability.
 * 
 * @author Obaid
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import {
  Category,
  ArticleListItem,
  ArticleDetail,
  SearchParams,
  SearchResponse,
  ScraperStatus,
  SearchStats,
  PaginatedResponse,
} from '@/types/news';

/**
 * Base API URL from environment or default to localhost
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

/**
 * Axios instance configured for the API
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Error handler for API calls
 * 
 * @param error - Axios error object
 * @throws Formatted error message
 */
const handleApiError = (error: AxiosError): never => {
  if (error.response) {
    // Server responded with error status
    const message = (error.response.data as any)?.detail || 
                    (error.response.data as any)?.message ||
                    'An error occurred';
    throw new Error(message);
  } else if (error.request) {
    // Request was made but no response
    throw new Error('Unable to connect to the server. Please try again.');
  } else {
    // Error setting up the request
    throw new Error(error.message);
  }
};

/**
 * News API functions
 */
export const newsApi = {
  /**
   * Get all categories with article counts
   * 
   * @returns Promise<Category[]> - Array of categories
   * 
   * @example
   * const categories = await newsApi.getCategories();
   * console.log(categories[0].name); // 'economy'
   */
  async getCategories(): Promise<Category[]> {
    try {
      const response = await apiClient.get<PaginatedResponse<Category>>('/news/categories/');
      return response.data.results;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  /**
   * Get paginated list of articles
   * 
   * @param page - Page number (1-indexed)
   * @param pageSize - Number of items per page
   * @param category - Optional category filter
   * @returns Promise<PaginatedResponse<ArticleListItem>>
   * 
   * @example
   * const articles = await newsApi.getArticles(1, 20, 'technology');
   */
  async getArticles(
    page: number = 1,
    pageSize: number = 20,
    category?: string
  ): Promise<PaginatedResponse<ArticleListItem>> {
    try {
      const params: Record<string, any> = {
        page,
        page_size: pageSize,
      };
      
      if (category) {
        params.category__name = category;
      }
      
      const response = await apiClient.get<PaginatedResponse<ArticleListItem>>(
        '/news/articles/',
        { params }
      );
      return response.data;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  /**
   * Get single article by ID
   * 
   * @param id - Article UUID
   * @returns Promise<ArticleDetail> - Full article details
   * 
   * @example
   * const article = await newsApi.getArticle('uuid-here');
   */
  async getArticle(id: string): Promise<ArticleDetail> {
    try {
      const response = await apiClient.get<ArticleDetail>(`/news/articles/${id}/`);
      return response.data;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  /**
   * Get latest articles for homepage
   * 
   * @returns Promise<ArticleListItem[]> - Latest 10 articles
   */
  async getLatestArticles(): Promise<ArticleListItem[]> {
    try {
      const response = await apiClient.get<ArticleListItem[]>('/news/articles/latest/');
      return response.data;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  /**
   * Get articles by category
   * 
   * @param category - Category name
   * @param page - Page number
   * @returns Promise<PaginatedResponse<ArticleListItem>>
   */
  async getArticlesByCategory(
    category: string,
    page: number = 1
  ): Promise<PaginatedResponse<ArticleListItem>> {
    try {
      const response = await apiClient.get<PaginatedResponse<ArticleListItem>>(
        `/news/articles/by_category/${category}/`,
        { params: { page } }
      );
      return response.data;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },
};

/**
 * Search API functions
 */
export const searchApi = {
  /**
   * Perform a search across all articles
   * 
   * This is the main search function that:
   * - Auto-detects category from query
   * - Performs full-text search
   * - Returns ranked results
   * 
   * @param params - Search parameters
   * @returns Promise<SearchResponse> - Search results with metadata
   * 
   * @example
   * const results = await searchApi.search({
   *   query: 'stock market rally',
   *   page: 1,
   *   page_size: 20
   * });
   * console.log(results.detected_category); // 'market'
   */
  async search(params: SearchParams): Promise<SearchResponse> {
    try {
      const response = await apiClient.post<SearchResponse>('/news/search/', params);
      return response.data;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  /**
   * Get search suggestions for autocomplete
   * 
   * @param query - Partial search query
   * @returns Promise<string[]> - Array of suggestions
   */
  async getSuggestions(query: string): Promise<string[]> {
    try {
      const response = await apiClient.get<{ suggestions: string[] }>(
        '/news/search/suggestions/',
        { params: { q: query } }
      );
      return response.data.suggestions;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  /**
   * Get search statistics
   * 
   * @returns Promise<SearchStats> - Search analytics data
   */
  async getStats(): Promise<SearchStats> {
    try {
      const response = await apiClient.get<SearchStats>('/news/search/stats/');
      return response.data;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },
};

/**
 * Scraper API functions
 */
export const scraperApi = {
  /**
   * Get current scraper status
   * 
   * @returns Promise<ScraperStatus> - Scraper configuration and status
   */
  async getStatus(): Promise<ScraperStatus> {
    try {
      const response = await apiClient.get<ScraperStatus>('/scraper/status/');
      return response.data;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },

  /**
   * Toggle scraper on/off
   * 
   * This implements the fetch: True/False parameter requirement.
   * 
   * @param fetch - Enable (true) or disable (false) auto-fetching
   * @returns Promise<ScraperStatus> - Updated scraper status
   * 
   * @example
   * // Enable scraper
   * await scraperApi.toggle(true);
   * 
   * // Disable scraper
   * await scraperApi.toggle(false);
   */
  async toggle(fetch: boolean): Promise<ScraperStatus> {
    try {
      const response = await apiClient.post<ScraperStatus>('/scraper/toggle/', { fetch });
      return response.data;
    } catch (error) {
      return handleApiError(error as AxiosError);
    }
  },
};

export default {
  news: newsApi,
  search: searchApi,
  scraper: scraperApi,
};
