/**
 * Home Page Component
 * 
 * Main search page with:
 * - Search bar with auto-complete
 * - Category filters
 * - Search results grid
 * - Latest articles on initial load
 * 
 * @author Obaid
 */

'use client';

import React, { useState, useCallback, useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { Sparkles, TrendingUp, BarChart3 } from 'lucide-react';
import SearchBar from '@/components/SearchBar';
import CategoryFilter from '@/components/CategoryFilter';
import ResultsList from '@/components/ResultsList';
import NewsCard from '@/components/NewsCard';
import { useSearch, useLatestArticles, useArticles, useSearchStats } from '@/hooks/useSearch';

/**
 * Home page component
 */
export default function HomePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  
  // Get initial values from URL
  const initialQuery = searchParams.get('q') || '';
  const initialCategory = searchParams.get('category') || null;
  
  // State
  const [selectedCategory, setSelectedCategory] = useState<string | null>(initialCategory);
  
  // Hooks
  const {
    search,
    clearSearch,
    goToPage,
    results,
    isLoading,
    isError,
    detectedCategory,
    categoryConfidence,
    currentParams,
  } = useSearch();
  
  const { articles: latestArticles, isLoading: latestLoading } = useLatestArticles();
  const { stats } = useSearchStats();
  
  // Paginated articles with category filter (used when category selected without search)
  const [articlesPage, setArticlesPage] = useState(1);
  const { 
    articles: filteredArticles, 
    totalCount: filteredTotalCount,
    isLoading: filteredLoading 
  } = useArticles(articlesPage, 20, selectedCategory);
  
  // Perform initial search if query in URL
  useEffect(() => {
    if (initialQuery) {
      search({
        query: initialQuery,
        category: initialCategory || undefined,
        page: 1,
      });
    }
  }, []); // Only on mount
  
  /**
   * Handle search submission
   */
  const handleSearch = useCallback((query: string) => {
    // Update URL
    const params = new URLSearchParams();
    params.set('q', query);
    if (selectedCategory) {
      params.set('category', selectedCategory);
    }
    router.push(`/?${params.toString()}`);
    
    // Perform search
    search({
      query,
      category: selectedCategory || undefined,
      page: 1,
    });
  }, [search, selectedCategory, router]);
  
  /**
   * Handle category selection
   */
  const handleCategoryChange = useCallback((category: string | null) => {
    setSelectedCategory(category);
    setArticlesPage(1); // Reset to first page
    
    // Update URL
    const params = new URLSearchParams();
    if (currentParams?.query) {
      params.set('q', currentParams.query);
    }
    if (category) {
      params.set('category', category);
    }
    router.push(params.toString() ? `/?${params.toString()}` : '/');
    
    // If we have an active search, re-search with new category
    if (currentParams?.query) {
      search({
        query: currentParams.query,
        category: category || undefined,
        page: 1,
      });
    }
  }, [search, currentParams, router]);
  
  /**
   * Handle page change
   */
  const handlePageChange = useCallback((page: number) => {
    goToPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [goToPage]);
  
  // Determine what to show
  const showResults = !!results;
  const showCategoryFiltered = !showResults && !isLoading && selectedCategory !== null;
  const showLatest = !showResults && !isLoading && selectedCategory === null;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Hero Section */}
      <div className="text-center mb-12">
        <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
          <span className="text-bloomberg-orange">AI-Powered</span> News Search
        </h1>
        <p className="text-xl text-gray-600 max-w-2xl mx-auto">
          Search Bloomberg news with automatic category detection.
          Find articles about economy, markets, health, technology, and industry.
        </p>
        
        {/* Stats */}
        {stats && (
          <div className="flex items-center justify-center gap-8 mt-6">
            <div className="flex items-center gap-2 text-gray-500">
              <BarChart3 className="h-5 w-5" />
              <span>{stats.total_articles} articles</span>
            </div>
            <div className="flex items-center gap-2 text-gray-500">
              <TrendingUp className="h-5 w-5" />
              <span>{stats.total_searches} searches</span>
            </div>
          </div>
        )}
      </div>
      
      {/* Search Section */}
      <div className="mb-8">
        <SearchBar
          onSearch={handleSearch}
          initialValue={initialQuery}
          placeholder="Search for news (e.g., 'stock market rally', 'inflation economy')..."
          isLoading={isLoading}
          detectedCategory={detectedCategory}
          categoryConfidence={categoryConfidence}
          className="max-w-3xl mx-auto"
        />
      </div>
      
      {/* Category Filter */}
      <div className="mb-8 flex justify-center">
        <CategoryFilter
          selectedCategory={selectedCategory}
          onSelectCategory={handleCategoryChange}
        />
      </div>
      
      {/* AI Feature Highlight */}
      {detectedCategory && results && (
        <div className="mb-8 p-4 bg-gradient-to-r from-orange-50 to-amber-50 rounded-xl border border-orange-100">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-bloomberg-orange rounded-lg">
              <Sparkles className="h-5 w-5 text-white" />
            </div>
            <div>
              <h3 className="font-medium text-gray-900">AI Category Detection</h3>
              <p className="text-sm text-gray-600">
                Your search "{currentParams?.query}" was automatically detected as{' '}
                <span className="font-medium text-bloomberg-orange">{detectedCategory}</span>
                {' '}with {Math.round(categoryConfidence * 100)}% confidence
              </p>
            </div>
          </div>
        </div>
      )}
      
      {/* Search Results */}
      {showResults && results && (
        <ResultsList
          articles={results.results}
          totalResults={results.total_results}
          currentPage={results.page}
          totalPages={results.total_pages}
          pageSize={results.page_size}
          isLoading={isLoading}
          executionTime={results.execution_time_ms}
          onPageChange={handlePageChange}
        />
      )}
      
      {/* Category Filtered Articles (when category selected without search) */}
      {showCategoryFiltered && (
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-2xl font-bold text-gray-900">
              {selectedCategory ? selectedCategory.charAt(0).toUpperCase() + selectedCategory.slice(1) : ''} News
            </h2>
            <span className="text-gray-500">{filteredTotalCount} articles</span>
          </div>
          
          {filteredLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="bg-gray-100 rounded-xl h-64 animate-pulse"
                />
              ))}
            </div>
          ) : filteredArticles.length > 0 ? (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {filteredArticles.map((article, index) => (
                  <NewsCard
                    key={article.id}
                    article={article}
                    variant={index === 0 ? 'featured' : 'default'}
                  />
                ))}
              </div>
              {/* Pagination for category filtered articles */}
              {filteredTotalCount > 20 && (
                <div className="flex justify-center mt-8 gap-2">
                  <button
                    onClick={() => setArticlesPage(p => Math.max(1, p - 1))}
                    disabled={articlesPage === 1}
                    className="px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  <span className="px-4 py-2 text-gray-600">
                    Page {articlesPage} of {Math.ceil(filteredTotalCount / 20)}
                  </span>
                  <button
                    onClick={() => setArticlesPage(p => p + 1)}
                    disabled={articlesPage >= Math.ceil(filteredTotalCount / 20)}
                    className="px-4 py-2 rounded-lg bg-gray-100 hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-12 text-gray-500">
              No articles found in this category.
            </div>
          )}
        </div>
      )}
      
      {/* Latest Articles (shown when no search and no category filter) */}
      {showLatest && (
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Latest News</h2>
          
          {latestLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[...Array(6)].map((_, i) => (
                <div
                  key={i}
                  className="bg-gray-100 rounded-xl h-64 animate-pulse"
                />
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {latestArticles.slice(0, 6).map((article, index) => (
                <NewsCard
                  key={article.id}
                  article={article}
                  variant={index === 0 ? 'featured' : 'default'}
                />
              ))}
            </div>
          )}
        </div>
      )}
      
      {/* Error State */}
      {isError && (
        <div className="text-center py-12">
          <p className="text-red-500">
            An error occurred while searching. Please try again.
          </p>
        </div>
      )}
    </div>
  );
}
