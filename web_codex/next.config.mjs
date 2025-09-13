/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  experimental: {
    typedRoutes: true,
    optimizePackageImports: ["framer-motion"],
  },
  async rewrites() {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL
    if (!base) return []
    // Proxy API calls to the backend to avoid CORS in dev
    return [
      { source: '/v1/:path*', destination: `${base.replace(/\/$/, '')}/v1/:path*` },
      { source: '/health', destination: `${base.replace(/\/$/, '')}/health` },
      { source: '/docs', destination: `${base.replace(/\/$/, '')}/docs` },
      { source: '/redoc', destination: `${base.replace(/\/$/, '')}/redoc` },
    ]
  },
}

export default nextConfig
