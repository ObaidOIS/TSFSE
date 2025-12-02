/**
 * React Query Provider Component
 * 
 * Sets up React Query for data fetching and caching.
 * 
 * @author Obaid
 */

'use client';

import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

/**
 * Create a new QueryClient instance
 */
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000, // 1 minute
        refetchOnWindowFocus: false,
      },
    },
  });
}

let browserQueryClient: QueryClient | undefined = undefined;

/**
 * Get or create QueryClient
 */
function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always make a new query client
    return makeQueryClient();
  } else {
    // Browser: make a new query client if we don't already have one
    if (!browserQueryClient) browserQueryClient = makeQueryClient();
    return browserQueryClient;
  }
}

/**
 * Providers wrapper component
 * 
 * @param children - Child components
 */
export default function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient();

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
