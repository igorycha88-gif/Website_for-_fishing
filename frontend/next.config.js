/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  images: {
    domains: ['localhost', 'host.docker.internal'],
  },
  async rewrites() {
    const isDocker = process.env.DOCKER_ENV === 'true';
    
    const authHost = isDocker ? 'http://auth-service:8000' : 'http://localhost:8001';
    const placesHost = isDocker ? 'http://places-service:8001' : 'http://localhost:8002';
    const reportsHost = isDocker ? 'http://reports-service:8002' : 'http://localhost:8003';
    const bookingHost = isDocker ? 'http://booking-service:8003' : 'http://localhost:8004';
    const shopHost = isDocker ? 'http://shop-service:8004' : 'http://localhost:8005';
    const emailHost = isDocker ? 'http://email-service:8005' : 'http://localhost:8006';
    const forecastHost = isDocker ? 'http://forecast-service:8000' : 'http://localhost:8007';

    return [
      {
        source: '/api/v1/auth/:path*',
        destination: `${authHost}/api/v1/auth/:path*`,
      },
      {
        source: '/api/v1/users/:path*',
        destination: `${authHost}/api/v1/users/:path*`,
      },
      {
        source: '/api/v1/maps/:path*',
        destination: `${authHost}/api/v1/maps/:path*`,
      },
      {
        source: '/api/v1/places/:path*',
        destination: `${placesHost}/api/v1/places/:path*`,
      },
      {
        source: '/api/v1/reports/:path*',
        destination: `${reportsHost}/api/v1/reports/:path*`,
      },
      {
        source: '/api/v1/booking/:path*',
        destination: `${bookingHost}/api/v1/booking/:path*`,
      },
      {
        source: '/api/v1/shop/:path*',
        destination: `${shopHost}/api/v1/shop/:path*`,
      },
      {
        source: '/api/v1/email/:path*',
        destination: `${emailHost}/api/v1/email/:path*`,
      },
      {
        source: '/api/v1/forecast/:path*',
        destination: `${forecastHost}/api/v1/forecast/:path*`,
      },
      {
        source: '/api/v1/weather/:path*',
        destination: `${forecastHost}/api/v1/weather/:path*`,
      },
      {
        source: '/api/v1/regions/:path*',
        destination: `${forecastHost}/api/v1/regions/:path*`,
      },
    ];
  },
};

module.exports = nextConfig;
