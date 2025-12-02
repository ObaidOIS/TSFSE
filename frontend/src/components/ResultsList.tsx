/**
 * ResultsList Component
 * 
 * Displays search results with pagination.
 * Shows loading states and empty states.
 * 
 * @author Obaid
 */

'use client';

import React from 'react';
import { ChevronLeft, ChevronRight, Loader2, SearchX } from 'lucide-react';
import NewsCard from './NewsCard';
import { ArticleListItem } from '@/types/news';
import clsx from 'clsx';

/**
 * Props for ResultsList component
 */
interface ResultsListProps {
  /** Array of articles to display */
  articles: ArticleListItem[];
  /** Total number of results */
  totalResults: number;
  /** Current page number */
  currentPage: number;
  /** Total number of pages */
  totalPages: number;
  /** Results per page */
  pageSize: number;
  /** Whether results are loading */
  isLoading: boolean;
  /** Search execution time in ms */
  executionTime?: number;
  /** Callback when page changes */
  onPageChange: (page: number) => void;
  /** CSS class name */
  className?: string;
}

/**
 * ResultsList component for displaying search results
 * 
 * Features:
 * - Grid layout for articles
 * - Pagination controls
 * - Loading state
 * - Empty state
 * 
 * @example
 * <ResultsList
 *   articles={results}
 *   totalResults={100}
 *   currentPage={1}
 *   totalPages={5}
 *   pageSize={20}
 *   isLoading={false}
 *   onPageChange={(page) => setPage(page)}
 * />
 */
export default function ResultsList({
  articles,
  totalResults,
  currentPage,
  totalPages,
  pageSize,
  isLoading,
  executionTime,
  onPageChange,
  className,
}: ResultsListProps) {
  // Loading state
  if (isLoading) {
    return (
      <div className={clsx('flex flex-col items-center justify-center py-16', className)}>
        <Loader2 className="h-10 w-10 animate-spin text-bloomberg-orange" />
        <p className="mt-4 text-gray-500">Searching...</p>
      </div>
    );
  }

  // Empty state
  if (articles.length === 0) {
    return (
      <div className={clsx('flex flex-col items-center justify-center py-16', className)}>
        <SearchX className="h-16 w-16 text-gray-300" />
        <h3 className="mt-4 text-lg font-medium text-gray-900">No results found</h3>
        <p className="mt-2 text-gray-500">
          Try adjusting your search terms or filters
        </p>
      </div>
    );
  }

  /**
   * Calculate pagination range
   */
  const getPageNumbers = (): (number | string)[] => {
    const pages: (number | string)[] = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        pages.push(1, 2, 3, 4, '...', totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1, '...', totalPages - 3, totalPages - 2, totalPages - 1, totalPages);
      } else {
        pages.push(1, '...', currentPage - 1, currentPage, currentPage + 1, '...', totalPages);
      }
    }

    return pages;
  };

  const startResult = (currentPage - 1) * pageSize + 1;
  const endResult = Math.min(currentPage * pageSize, totalResults);

  return (
    <div className={className}>
      {/* Results Header */}
      <div className="flex items-center justify-between mb-6">
        <p className="text-sm text-gray-600">
          Showing <span className="font-medium">{startResult}</span> to{' '}
          <span className="font-medium">{endResult}</span> of{' '}
          <span className="font-medium">{totalResults}</span> results
          {executionTime && (
            <span className="text-gray-400"> ({executionTime}ms)</span>
          )}
        </p>
      </div>

      {/* Results Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {articles.map((article) => (
          <NewsCard key={article.id} article={article} />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2">
          {/* Previous Button */}
          <button
            onClick={() => onPageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className={clsx(
              'flex items-center gap-1 px-3 py-2 rounded-lg',
              'text-sm font-medium transition-colors',
              currentPage === 1
                ? 'text-gray-300 cursor-not-allowed'
                : 'text-gray-600 hover:bg-gray-100'
            )}
          >
            <ChevronLeft className="h-4 w-4" />
            Previous
          </button>

          {/* Page Numbers */}
          <div className="flex items-center gap-1">
            {getPageNumbers().map((page, index) => (
              <React.Fragment key={index}>
                {page === '...' ? (
                  <span className="px-2 py-2 text-gray-400">...</span>
                ) : (
                  <button
                    onClick={() => onPageChange(page as number)}
                    className={clsx(
                      'w-10 h-10 rounded-lg text-sm font-medium',
                      'transition-colors',
                      currentPage === page
                        ? 'bg-bloomberg-orange text-white'
                        : 'text-gray-600 hover:bg-gray-100'
                    )}
                  >
                    {page}
                  </button>
                )}
              </React.Fragment>
            ))}
          </div>

          {/* Next Button */}
          <button
            onClick={() => onPageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className={clsx(
              'flex items-center gap-1 px-3 py-2 rounded-lg',
              'text-sm font-medium transition-colors',
              currentPage === totalPages
                ? 'text-gray-300 cursor-not-allowed'
                : 'text-gray-600 hover:bg-gray-100'
            )}
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
