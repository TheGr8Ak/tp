/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Allow static file serving from public folder
  webpack: (config) => {
    config.resolve.fallback = { fs: false };
    return config;
  },
}

module.exports = nextConfig;
