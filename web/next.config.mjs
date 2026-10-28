/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://127.0.0.1:8001/api/:path*" },
      { source: "/health", destination: "http://127.0.0.1:8001/health" },
    ];
  },
};

export default nextConfig;
