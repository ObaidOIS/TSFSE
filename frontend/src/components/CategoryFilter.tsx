/**
 * CategoryFilter Component
 * 
 * Displays category buttons for filtering search results.
 * Shows article counts for each category.
 * 
 * @author Obaid
 */

'use client';

import React from 'react';
import { useCategories } from '@/hooks/useSearch';
import clsx from 'clsx';
import { 
  TrendingUp, 
  LineChart, 
  Heart, 
  Cpu, 
  Factory,
  Loader2 
} from 'lucide-react';

/**
 * Props for CategoryFilter component
 */
interface CategoryFilterProps {
  /** Currently selected category */
  selectedCategory: string | null;
  /** Callback when category is selected */
  onSelectCategory: (category: string | null) => void;
  /** CSS class name */
  className?: string;
}

/**
 * Category icon mapping
 */
const categoryIcons: Record<string, React.ReactNode> = {
  economy: <TrendingUp className="h-4 w-4" />,
  market: <LineChart className="h-4 w-4" />,
  health: <Heart className="h-4 w-4" />,
  technology: <Cpu className="h-4 w-4" />,
  industry: <Factory className="h-4 w-4" />,
};

/**
 * Category color mapping
 */
const categoryColors: Record<string, string> = {
  economy: 'bg-blue-100 text-blue-700 border-blue-200 hover:bg-blue-200',
  market: 'bg-green-100 text-green-700 border-green-200 hover:bg-green-200',
  health: 'bg-red-100 text-red-700 border-red-200 hover:bg-red-200',
  technology: 'bg-purple-100 text-purple-700 border-purple-200 hover:bg-purple-200',
  industry: 'bg-amber-100 text-amber-700 border-amber-200 hover:bg-amber-200',
};

const selectedColors: Record<string, string> = {
  economy: 'bg-blue-500 text-white border-blue-500',
  market: 'bg-green-500 text-white border-green-500',
  health: 'bg-red-500 text-white border-red-500',
  technology: 'bg-purple-500 text-white border-purple-500',
  industry: 'bg-amber-500 text-white border-amber-500',
};

/**
 * CategoryFilter component for filtering articles by category
 * 
 * @example
 * <CategoryFilter
 *   selectedCategory="technology"
 *   onSelectCategory={(cat) => setCategory(cat)}
 * />
 */
export default function CategoryFilter({
  selectedCategory,
  onSelectCategory,
  className,
}: CategoryFilterProps) {
  const { categories, isLoading, isError } = useCategories();

  if (isLoading) {
    return (
      <div className={clsx('flex items-center justify-center py-4', className)}>
        <Loader2 className="h-5 w-5 animate-spin text-gray-400" />
      </div>
    );
  }

  if (isError || categories.length === 0) {
    return null;
  }

  return (
    <div className={clsx('flex flex-wrap gap-2', className)}>
      {/* All Categories Button */}
      <button
        onClick={() => onSelectCategory(null)}
        className={clsx(
          'px-4 py-2 rounded-full text-sm font-medium',
          'border transition-all duration-200',
          selectedCategory === null
            ? 'bg-bloomberg-orange text-white border-bloomberg-orange'
            : 'bg-gray-100 text-gray-700 border-gray-200 hover:bg-gray-200'
        )}
      >
        All
      </button>

      {/* Category Buttons */}
      {categories.map((category) => (
        <button
          key={category.name}
          onClick={() => onSelectCategory(category.name)}
          className={clsx(
            'px-4 py-2 rounded-full text-sm font-medium',
            'border transition-all duration-200',
            'flex items-center gap-2',
            selectedCategory === category.name
              ? selectedColors[category.name]
              : categoryColors[category.name]
          )}
        >
          {categoryIcons[category.name]}
          <span>{category.display_name}</span>
          <span
            className={clsx(
              'px-1.5 py-0.5 text-xs rounded-full',
              selectedCategory === category.name
                ? 'bg-white/20'
                : 'bg-black/5'
            )}
          >
            {category.article_count}
          </span>
        </button>
      ))}
    </div>
  );
}
