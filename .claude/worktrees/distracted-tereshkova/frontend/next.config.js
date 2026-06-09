/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    const API_HOST = process.env.API_HOST || 'host.docker.internal';
    return [
      {
        source: '/api/v1/auth/:path*',
        destination: `http://${API_HOST}:8001/api/v1/auth/:path*`,
      },
      {
        source: '/api/v1/users/:path*',
        destination: `http://${API_HOST}:8001/api/v1/users/:path*`,
      },
      {
        source: '/api/v1/places/:path*',
        destination: `http://${API_HOST}:8002/api/v1/places/:path*`,
      },
      {
        source: '/api/v1/reports/:path*',
        destination: `http://${API_HOST}:8003/api/v1/reports/:path*`,
      },
      {
        source: '/api/v1/bookings/:path*',
        destination: `http://${API_HOST}:8004/api/v1/bookings/:path*`,
      },
      {
        source: '/api/v1/booking-slots/:path*',
        destination: `http://${API_HOST}:8004/api/v1/booking-slots/:path*`,
      },
      {
        source: '/api/v1/shop/:path*',
        destination: `http://${API_HOST}:8005/api/v1/shop/:path*`,
      },
      {
        source: '/api/v1/orders/:path*',
        destination: `http://${API_HOST}:8005/api/v1/orders/:path*`,
      },
      {
        source: '/api/v1/email/:path*',
        destination: `http://${API_HOST}:8006/api/v1/email/:path*`,
      },
    ]
  },
};

module.exports = nextConfig;
