/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Enable standalone output for Docker
  output: 'standalone',
  
  // Image configuration for Bloomberg images
  images: {
    // Use unoptimized images to avoid sharp requirement in Docker
    unoptimized: true,
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'assets.bwbx.io',
        pathname: '/**',
      },
      {
        protocol: 'http',
        hostname: 'assets.bwbx.io',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'www.bloomberg.com',
        pathname: '/**',
      },
    ],
  },
  
  // Environment variables exposed to the browser
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1',
  },
};

module.exports = nextConfig;
