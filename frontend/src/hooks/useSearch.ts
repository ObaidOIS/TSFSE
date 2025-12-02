/**
 * Custom React Hooks for Search Functionality
 * 
 * This module provides custom hooks for managing search state,
 * API calls, and debouncing.
 * 
 * @author Obaid
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { searchApi, newsApi } from '@/services/api';
import { SearchParams, SearchResponse, Category } from '@/types/news';

/**
 * Debounce hook for delaying function execution
 * 
 * @param value - Value to debounce
 * @param delay - Delay in milliseconds
 * @returns Debounced value
 * 
 * @example
 * const debouncedQuery = useDebounce(searchQuery, 300);
 */
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * Hook for managing search state and API calls
 * 
 * Provides:
 * - Search execution with auto-category detection
 * - Loading and error states
 * - Pagination support
 * - Query caching via React Query
 * 
 * @returns Search state and functions
 * 
 * @example
 * const { search, results, isLoading, detectedCategory } = useSearch();
 * 
 * // Perform search
 * search({ query: 'stock market', page: 1 });
 */
export function useSearch() {
  const [searchParams, setSearchParams] = useState<SearchParams | null>(null);
  const queryClient = useQueryClient();

  // Search query with React Query
  const {
    data: results,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery<SearchResponse, Error>({
    queryKey: ['search', searchParams],
    queryFn: () => searchApi.search(searchParams!),
    enabled: !!searchParams?.query,
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  });

  /**
   * Execute a search
   * 
   * @param params - Search parameters
   */
  const search = useCallback((params: SearchParams) => {
    setSearchParams(params);
  }, []);

  /**
   * Clear search results
   */
  const clearSearch = useCallback(() => {
    setSearchParams(null);
    queryClient.removeQueries({ queryKey: ['search'] });
  }, [queryClient]);

  /**
   * Go to a specific page
   * 
   * @param page - Page number
   */
  const goToPage = useCallback((page: number) => {
    if (searchParams) {
      setSearchParams({ ...searchParams, page });
    }
  }, [searchParams]);

  return {
    search,
    clearSearch,
    goToPage,
    results,
    isLoading,
    isError,
    error,
    currentParams: searchParams,
    detectedCategory: results?.detected_category || null,
    categoryConfidence: results?.detected_category_confidence || 0,
  };
}

/**
 * Hook for fetching search suggestions
 * 
 * @param query - Partial search query
 * @param enabled - Whether to fetch suggestions
 * @returns Suggestions array and loading state
 */
export function useSearchSuggestions(query: string, enabled: boolean = true) {
  const debouncedQuery = useDebounce(query, 300);

  const { data: suggestions = [], isLoading } = useQuery<string[], Error>({
    queryKey: ['suggestions', debouncedQuery],
    queryFn: () => searchApi.getSuggestions(debouncedQuery),
    enabled: enabled && debouncedQuery.length >= 2,
    staleTime: 1000 * 60 * 2, // Cache for 2 minutes
  });

  return { suggestions, isLoading };
}

/**
 * Hook for fetching categories
 * 
 * @returns Categories array and loading state
 */
export function useCategories() {
  const { data: categories = [], isLoading, isError } = useQuery<Category[], Error>({
    queryKey: ['categories'],
    queryFn: () => newsApi.getCategories(),
    staleTime: 1000 * 60 * 10, // Cache for 10 minutes
  });

  return { categories, isLoading, isError };
}

/**
 * Hook for fetching search statistics
 * 
 * @returns Search stats and loading state
 */
export function useSearchStats() {
  const { data: stats, isLoading, isError } = useQuery({
    queryKey: ['searchStats'],
    queryFn: () => searchApi.getStats(),
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
  });

  return { stats, isLoading, isError };
}

/**
 * Hook for fetching latest articles
 * 
 * @returns Latest articles and loading state
 */
export function useLatestArticles() {
  const { data: articles = [], isLoading, isError } = useQuery({
    queryKey: ['latestArticles'],
    queryFn: () => newsApi.getLatestArticles(),
    staleTime: 1000 * 60 * 2, // Cache for 2 minutes
  });

  return { articles, isLoading, isError };
}

/**
 * Hook for fetching paginated articles with optional category filter
 * 
 * @param page - Page number
 * @param pageSize - Items per page
 * @param category - Optional category filter
 * @returns Paginated articles and loading state
 */
export function useArticles(page: number = 1, pageSize: number = 20, category?: string | null) {
  const { data, isLoading, isError } = useQuery({
    queryKey: ['articles', page, pageSize, category],
    queryFn: () => newsApi.getArticles(page, pageSize, category || undefined),
    staleTime: 1000 * 60 * 2, // Cache for 2 minutes
  });

  return { 
    articles: data?.results || [], 
    totalCount: data?.count || 0,
    hasNext: !!data?.next,
    hasPrevious: !!data?.previous,
    isLoading, 
    isError 
  };
}
