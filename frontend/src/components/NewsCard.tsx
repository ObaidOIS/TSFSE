/**
 * NewsCard Component
 * 
 * Displays a single news article in card format.
 * Used in search results and article lists.
 * 
 * @author Obaid
 */

'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { format, formatDistanceToNow } from 'date-fns';
import { ExternalLink, Clock, User, Tag } from 'lucide-react';
import { ArticleListItem } from '@/types/news';
import clsx from 'clsx';

/**
 * Props for NewsCard component
 */
interface NewsCardProps {
  /** Article data */
  article: ArticleListItem;
  /** Display variant */
  variant?: 'default' | 'compact' | 'featured';
  /** CSS class name */
  className?: string;
}

/**
 * Category color mapping for badges
 */
const categoryBadgeColors: Record<string, string> = {
  economy: 'bg-blue-100 text-blue-700',
  market: 'bg-green-100 text-green-700',
  health: 'bg-red-100 text-red-700',
  technology: 'bg-purple-100 text-purple-700',
  industry: 'bg-amber-100 text-amber-700',
};

/**
 * NewsCard component for displaying article previews
 * 
 * @example
 * <NewsCard article={article} variant="featured" />
 */
export default function NewsCard({
  article,
  variant = 'default',
  className,
}: NewsCardProps) {
  /**
   * Format the publication date
   */
  const formattedDate = article.published_at
    ? formatDistanceToNow(new Date(article.published_at), { addSuffix: true })
    : 'Recently';

  /**
   * Get category badge color
   */
  const badgeColor = categoryBadgeColors[article.category_name] || 'bg-gray-100 text-gray-700';

  // Featured variant - larger card for homepage
  if (variant === 'featured') {
    return (
      <article
        className={clsx(
          'group relative bg-white rounded-xl overflow-hidden',
          'border border-gray-200 shadow-sm',
          'hover:shadow-lg transition-shadow duration-300',
          className
        )}
      >
        {/* Image */}
        {article.image_url && (
          <div className="relative h-48 md:h-64 overflow-hidden">
            <Image
              src={article.image_url}
              alt={article.title}
              fill
              className="object-cover group-hover:scale-105 transition-transform duration-300"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          </div>
        )}

        {/* Content */}
        <div className="p-6">
          {/* Category Badge */}
          <div className="flex items-center gap-2 mb-3">
            <span className={clsx('px-2 py-1 text-xs font-medium rounded-full', badgeColor)}>
              {article.category_display}
            </span>
            {article.category_confidence > 0.8 && (
              <span className="text-xs text-gray-400">
                AI: {Math.round(article.category_confidence * 100)}%
              </span>
            )}
          </div>

          {/* Title */}
          <h2 className="text-xl font-bold text-gray-900 mb-2 line-clamp-2 group-hover:text-bloomberg-orange transition-colors">
            <a href={article.url} target="_blank" rel="noopener noreferrer">
              {article.title}
            </a>
          </h2>

          {/* Summary */}
          <p className="text-gray-600 mb-4 line-clamp-3">{article.summary}</p>

          {/* Meta */}
          <div className="flex items-center justify-between text-sm text-gray-500">
            <div className="flex items-center gap-4">
              {article.author && (
                <span className="flex items-center gap-1">
                  <User className="h-4 w-4" />
                  {article.author}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {formattedDate}
              </span>
            </div>
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-bloomberg-orange hover:underline"
            >
              Read <ExternalLink className="h-4 w-4" />
            </a>
          </div>

          {/* Keywords */}
          {article.keywords && article.keywords.length > 0 && (
            <div className="mt-4 flex flex-wrap gap-1">
              {article.keywords.slice(0, 5).map((keyword, index) => (
                <span
                  key={index}
                  className="px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded"
                >
                  {typeof keyword === 'string' ? keyword : keyword.word}
                </span>
              ))}
            </div>
          )}
        </div>
      </article>
    );
  }

  // Compact variant - for lists
  if (variant === 'compact') {
    return (
      <article
        className={clsx(
          'group flex gap-4 p-4 bg-white rounded-lg',
          'border border-gray-100 hover:border-gray-200',
          'hover:shadow-sm transition-all duration-200',
          className
        )}
      >
        {/* Thumbnail */}
        {article.image_url && (
          <div className="relative w-24 h-24 flex-shrink-0 rounded-lg overflow-hidden">
            <Image
              src={article.image_url}
              alt={article.title}
              fill
              className="object-cover"
            />
          </div>
        )}

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={clsx('px-2 py-0.5 text-xs font-medium rounded', badgeColor)}>
              {article.category_display}
            </span>
            <span className="text-xs text-gray-400">{formattedDate}</span>
          </div>

          <h3 className="font-semibold text-gray-900 line-clamp-2 group-hover:text-bloomberg-orange transition-colors">
            <a href={article.url} target="_blank" rel="noopener noreferrer">
              {article.title}
            </a>
          </h3>

          <p className="mt-1 text-sm text-gray-500 line-clamp-1">{article.summary}</p>
        </div>
      </article>
    );
  }

  // Default variant
  return (
    <article
      className={clsx(
        'group bg-white rounded-xl overflow-hidden',
        'border border-gray-200 shadow-sm',
        'hover:shadow-md transition-shadow duration-200',
        className
      )}
    >
      {/* Image */}
      {article.image_url && (
        <div className="relative h-40 overflow-hidden">
          <Image
            src={article.image_url}
            alt={article.title}
            fill
            className="object-cover group-hover:scale-105 transition-transform duration-300"
          />
        </div>
      )}

      {/* Content */}
      <div className="p-4">
        {/* Category & Time */}
        <div className="flex items-center justify-between mb-2">
          <span className={clsx('px-2 py-0.5 text-xs font-medium rounded', badgeColor)}>
            {article.category_display}
          </span>
          <span className="text-xs text-gray-400">{formattedDate}</span>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-bloomberg-orange transition-colors">
          <a href={article.url} target="_blank" rel="noopener noreferrer">
            {article.title}
          </a>
        </h3>

        {/* Summary */}
        <p className="text-sm text-gray-600 line-clamp-2">{article.summary}</p>

        {/* Footer */}
        <div className="mt-3 flex items-center justify-between">
          {article.author && (
            <span className="text-xs text-gray-500 flex items-center gap-1">
              <User className="h-3 w-3" />
              {article.author}
            </span>
          )}
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs text-bloomberg-orange hover:underline flex items-center gap-1"
          >
            Read more <ExternalLink className="h-3 w-3" />
          </a>
        </div>
      </div>
    </article>
  );
}
