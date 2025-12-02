/**
 * SearchBar Component
 * 
 * A search input component with:
 * - Real-time suggestions/autocomplete
 * - Category auto-detection feedback
 * - Loading states
 * - Keyboard navigation
 * 
 * @author Obaid
 */

'use client';

import React, { useState, useRef, useEffect, FormEvent, KeyboardEvent } from 'react';
import { Search, X, Loader2 } from 'lucide-react';
import { useSearchSuggestions } from '@/hooks/useSearch';
import clsx from 'clsx';

/**
 * Props for SearchBar component
 */
interface SearchBarProps {
  /** Callback when search is submitted */
  onSearch: (query: string) => void;
  /** Initial search value */
  initialValue?: string;
  /** Placeholder text */
  placeholder?: string;
  /** Whether search is in progress */
  isLoading?: boolean;
  /** Detected category from previous search */
  detectedCategory?: string | null;
  /** Category detection confidence */
  categoryConfidence?: number;
  /** CSS class name */
  className?: string;
}

/**
 * SearchBar component for searching news articles
 * 
 * Features:
 * - Autocomplete suggestions
 * - Shows detected category
 * - Keyboard navigation for suggestions
 * - Clear button
 * 
 * @example
 * <SearchBar
 *   onSearch={(query) => handleSearch(query)}
 *   placeholder="Search news..."
 *   detectedCategory="economy"
 * />
 */
export default function SearchBar({
  onSearch,
  initialValue = '',
  placeholder = 'Search for news articles...',
  isLoading = false,
  detectedCategory,
  categoryConfidence = 0,
  className,
}: SearchBarProps) {
  const [query, setQuery] = useState(initialValue);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const inputRef = useRef<HTMLInputElement>(null);
  const suggestionsRef = useRef<HTMLDivElement>(null);

  // Fetch suggestions
  const { suggestions, isLoading: suggestionsLoading } = useSearchSuggestions(
    query,
    showSuggestions
  );

  // Close suggestions when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        suggestionsRef.current &&
        !suggestionsRef.current.contains(event.target as Node) &&
        !inputRef.current?.contains(event.target as Node)
      ) {
        setShowSuggestions(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  /**
   * Handle form submission
   */
  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (query.trim()) {
      onSearch(query.trim());
      setShowSuggestions(false);
    }
  };

  /**
   * Handle keyboard navigation in suggestions
   */
  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!showSuggestions || suggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev < suggestions.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1));
        break;
      case 'Enter':
        if (selectedIndex >= 0) {
          e.preventDefault();
          const selected = suggestions[selectedIndex];
          setQuery(selected);
          onSearch(selected);
          setShowSuggestions(false);
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
    }
  };

  /**
   * Handle suggestion click
   */
  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
    onSearch(suggestion);
    setShowSuggestions(false);
  };

  /**
   * Clear search input
   */
  const handleClear = () => {
    setQuery('');
    inputRef.current?.focus();
  };

  return (
    <div className={clsx('relative w-full', className)}>
      {/* Search Form */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center">
          {/* Search Icon */}
          <div className="absolute left-4 text-gray-400">
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Search className="h-5 w-5" />
            )}
          </div>

          {/* Input Field */}
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setShowSuggestions(true);
              setSelectedIndex(-1);
            }}
            onFocus={() => setShowSuggestions(true)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={clsx(
              'w-full py-4 pl-12 pr-24 text-lg',
              'bg-white border-2 border-gray-200 rounded-xl',
              'focus:border-bloomberg-orange focus:ring-2 focus:ring-bloomberg-orange/20',
              'outline-none transition-all duration-200',
              'placeholder:text-gray-400'
            )}
          />

          {/* Clear Button */}
          {query && (
            <button
              type="button"
              onClick={handleClear}
              className="absolute right-20 p-1 text-gray-400 hover:text-gray-600"
            >
              <X className="h-5 w-5" />
            </button>
          )}

          {/* Search Button */}
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className={clsx(
              'absolute right-2 px-4 py-2 rounded-lg',
              'bg-bloomberg-orange text-white font-medium',
              'hover:bg-orange-600 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
          >
            Search
          </button>
        </div>
      </form>

      {/* Category Detection Badge */}
      {detectedCategory && categoryConfidence > 0.3 && (
        <div className="mt-2 flex items-center gap-2">
          <span className="text-sm text-gray-500">Category detected:</span>
          <span
            className={clsx(
              'px-2 py-0.5 text-sm rounded-full font-medium',
              'bg-bloomberg-orange/10 text-bloomberg-orange'
            )}
          >
            {detectedCategory}
          </span>
          <span className="text-xs text-gray-400">
            ({Math.round(categoryConfidence * 100)}% confidence)
          </span>
        </div>
      )}

      {/* Suggestions Dropdown */}
      {showSuggestions && suggestions.length > 0 && (
        <div
          ref={suggestionsRef}
          className={clsx(
            'absolute z-50 w-full mt-2',
            'bg-white border border-gray-200 rounded-xl shadow-lg',
            'max-h-64 overflow-y-auto'
          )}
        >
          {suggestionsLoading ? (
            <div className="p-4 text-center text-gray-500">
              <Loader2 className="h-5 w-5 animate-spin mx-auto" />
            </div>
          ) : (
            <ul className="py-2">
              {suggestions.map((suggestion, index) => (
                <li
                  key={suggestion}
                  onClick={() => handleSuggestionClick(suggestion)}
                  className={clsx(
                    'px-4 py-2 cursor-pointer',
                    'hover:bg-gray-100',
                    index === selectedIndex && 'bg-gray-100'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <Search className="h-4 w-4 text-gray-400" />
                    <span className="text-gray-700">{suggestion}</span>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
