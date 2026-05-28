/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    domains: ['localhost', 'host.docker.internal'],
  },
  async rewrites() {
    return [
      {
        source: '/api/v1/auth/:path*',
        destination: 'http://host.docker.internal:8001/api/v1/auth/:path*',
      },
      {
        source: '/api/v1/users/:path*',
        destination: 'http://host.docker.internal:8001/api/v1/users/:path*',
      },
      {
        source: '/api/v1/places/:path*',
        destination: 'http://host.docker.internal:8002/api/v1/places/:path*',
      },
      {
        source: '/api/v1/reports/:path*',
        destination: 'http://host.docker.internal:8003/api/v1/reports/:path*',
      },
      {
        source: '/api/v1/booking/:path*',
        destination: 'http://host.docker.internal:8004/api/v1/booking/:path*',
      },
      {
        source: '/api/v1/shop/:path*',
        destination: 'http://host.docker.internal:8005/api/v1/shop/:path*',
      },
      {
        source: '/api/v1/email/:path*',
        destination: 'http://host.docker.internal:8006/api/v1/email/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
