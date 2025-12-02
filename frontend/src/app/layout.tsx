/**
 * Root Layout Component
 * 
 * Defines the global layout including:
 * - HTML structure
 * - Meta tags
 * - Global providers (React Query)
 * - Global styles
 * 
 * @author Obaid
 */

import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Providers from './providers';

const inter = Inter({ subsets: ['latin'] });

/**
 * Page metadata for SEO
 */
export const metadata: Metadata = {
  title: 'Bloomberg News Search | AI-Powered News Discovery',
  description: 'Search and discover Bloomberg news articles with AI-powered categorization. Find news about economy, markets, health, technology, and industry.',
  keywords: ['bloomberg', 'news', 'search', 'economy', 'market', 'technology', 'health', 'industry'],
  authors: [{ name: 'Obaid' }],
};

/**
 * Root layout component
 * 
 * @param children - Page content
 */
export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-50 text-gray-900 antialiased`}>
        <Providers>
          {/* Header */}
          <header className="bg-black text-white sticky top-0 z-50">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex items-center justify-between h-16">
                {/* Logo */}
                <a href="/" className="flex items-center gap-2">
                  <span className="text-2xl font-bold text-bloomberg-orange">Bloomberg</span>
                  <span className="text-lg font-light">News Search</span>
                </a>

                {/* Navigation */}
                <nav className="hidden md:flex items-center gap-6">
                  <a href="/" className="text-sm hover:text-bloomberg-orange transition-colors">
                    Home
                  </a>
                  <a href="/?category=economy" className="text-sm hover:text-bloomberg-orange transition-colors">
                    Economy
                  </a>
                  <a href="/?category=market" className="text-sm hover:text-bloomberg-orange transition-colors">
                    Markets
                  </a>
                  <a href="/?category=technology" className="text-sm hover:text-bloomberg-orange transition-colors">
                    Tech
                  </a>
                  <a href="/?category=health" className="text-sm hover:text-bloomberg-orange transition-colors">
                    Health
                  </a>
                  <a href="/?category=industry" className="text-sm hover:text-bloomberg-orange transition-colors">
                    Industry
                  </a>
                </nav>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="min-h-screen">
            {children}
          </main>

          {/* Footer */}
          <footer className="bg-gray-900 text-gray-400 py-12 mt-16">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                  <h3 className="text-white font-bold mb-4">Bloomberg News Search</h3>
                  <p className="text-sm">
                    AI-powered news discovery platform with automatic categorization
                    and full-text search capabilities.
                  </p>
                </div>
                <div>
                  <h4 className="text-white font-medium mb-4">Categories</h4>
                  <ul className="space-y-2 text-sm">
                    <li><a href="/?category=economy" className="hover:text-white">Economy</a></li>
                    <li><a href="/?category=market" className="hover:text-white">Markets</a></li>
                    <li><a href="/?category=technology" className="hover:text-white">Technology</a></li>
                    <li><a href="/?category=health" className="hover:text-white">Health</a></li>
                    <li><a href="/?category=industry" className="hover:text-white">Industry</a></li>
                  </ul>
                </div>
                <div>
                  <h4 className="text-white font-medium mb-4">About</h4>
                  <p className="text-sm">
                    Built with Next.js, Django, and AI/ML technologies.
                    Part of the Obaid assessment.
                  </p>
                </div>
              </div>
              <div className="border-t border-gray-800 mt-8 pt-8 text-center text-sm">
                <p>&copy; 2024 Bloomberg News Search. Educational Project.</p>
              </div>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
