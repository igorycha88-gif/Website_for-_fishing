import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const SERVICES: Record<string, string> = {
  '/api/v1/auth': process.env.AUTH_SERVICE_URL || 'http://auth-service:8000',
  '/api/v1/users': process.env.AUTH_SERVICE_URL || 'http://auth-service:8000',
  '/api/v1/maps': process.env.AUTH_SERVICE_URL || 'http://auth-service:8000',
  '/api/v1/places': process.env.PLACES_SERVICE_URL || 'http://places-service:8001',
  '/api/v1/reports': process.env.REPORTS_SERVICE_URL || 'http://reports-service:8002',
  '/api/v1/booking': process.env.BOOKING_SERVICE_URL || 'http://booking-service:8003',
  '/api/v1/shop': process.env.SHOP_SERVICE_URL || 'http://shop-service:8004',
  '/api/v1/email': process.env.EMAIL_SERVICE_URL || 'http://email-service:8005',
};

export async function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;

  for (const [prefix, baseUrl] of Object.entries(SERVICES)) {
    if (pathname.startsWith(prefix)) {
      const targetUrl = `${baseUrl}${pathname}${search}`;

      const headers = new Headers();
      request.headers.forEach((value, key) => {
        const lowerKey = key.toLowerCase();
        if (lowerKey !== 'host' && lowerKey !== 'content-length') {
          headers.set(key, value);
        }
      });

      const hasBody = ['POST', 'PUT', 'PATCH'].includes(request.method);
      const body = hasBody ? await request.arrayBuffer() : null;

      const fetchOptions: RequestInit = {
        method: request.method,
        headers,
        redirect: 'manual',
      };

      if (body && body.byteLength > 0) {
        fetchOptions.body = body;
        fetchOptions.headers = new Headers(headers);
      }

      const response = await fetch(targetUrl, fetchOptions);

  const responseHeaders = new Headers(response.headers);
  
  // Delete problematic headers
  responseHeaders.delete('content-encoding');
  responseHeaders.delete('transfer-encoding');
  responseHeaders.delete('keep-alive');
  
  // Clone the response body
  const modifiedBody = await response.text();
  
  // Return modified response
  return new NextResponse(modifiedBody, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: '/api/v1/:path*',
};
