import type { NextRequest } from 'next/server';

const DEFAULT_ALLOWED_HEADERS = new Set([
  'authorization',
  'content-type',
  'accept',
  'accept-encoding',
  'accept-language',
  'user-agent',
  'x-request-id',
  'x-correlation-id',
  'x-csrf-token',
]);

const ALWAYS_BLOCKED_HEADERS = new Set([
  'host',
  'content-length',
  'transfer-encoding',
  'connection',
  'keep-alive',
  'upgrade',
  'x-forwarded-for',
  'x-forwarded-proto',
  'x-forwarded-host',
  'x-real-ip',
  'x-frame-options',
  'x-content-type-options',
  'x-xss-protection',
  'strict-transport-security',
  'content-security-policy',
]);

function isCRLFInjection(value: string): boolean {
  return value.includes('\r') || value.includes('\n');
}

export function validateHeader(key: string, value: string): boolean {
  if (isCRLFInjection(key) || isCRLFInjection(value)) {
    return false;
  }

  const headerNameRegex = /^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$/;
  if (!headerNameRegex.test(key)) {
    return false;
  }

  return true;
}

export function generateForwardedHeaders(request: NextRequest): Headers {
  const headers = new Headers();

  const clientIp =
    (request as NextRequest & { ip?: string }).ip ||
    request.headers.get('x-real-ip') ||
    'unknown';
  headers.set('X-Forwarded-For', clientIp);

  const proto = request.nextUrl.protocol.replace(':', '');
  headers.set('X-Forwarded-Proto', proto);

  const host = request.headers.get('host') || 'unknown';
  headers.set('X-Forwarded-Host', host);

  return headers;
}

export function ensureRequestId(headers: Headers): void {
  if (!headers.has('x-request-id')) {
    let requestId: string;
    if (typeof crypto !== 'undefined' && crypto.randomUUID) {
      requestId = crypto.randomUUID();
    } else {
      requestId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      });
    }
    headers.set('X-Request-ID', requestId);
  }
}

function logBlockedHeader(
  headerName: string,
  headerValue: string,
  reason: string,
  request: NextRequest
): void {
  const env = process.env.NODE_ENV;

  if (env === 'development' || env === 'test') {
    console.warn(`[SECURITY] Blocked header: ${headerName}`, {
      value: headerValue,
      reason: reason,
      ip: (request as NextRequest & { ip?: string }).ip,
      endpoint: request.nextUrl.pathname,
      userAgent: request.headers.get('user-agent'),
    });
  } else if (reason === 'CRLF_INJECTION') {
    console.error(`[SECURITY] CRLF Injection attempt detected`, {
      header: headerName,
      ip: (request as NextRequest & { ip?: string }).ip,
      endpoint: request.nextUrl.pathname,
      userAgent: request.headers.get('user-agent'),
    });
  }
}

export function filterRequestHeaders(request: NextRequest): Headers {
  const filteredHeaders = new Headers();

  const envHeaders =
    process.env.PROXY_ALLOWED_HEADERS?.split(',')
      .map((h) => h.trim().toLowerCase())
      .filter((h) => h.length > 0) || [];
  const allowedHeaders = new Set([...DEFAULT_ALLOWED_HEADERS, ...envHeaders]);

  let blockedCount = 0;

  request.headers.forEach((value, key) => {
    const lowerKey = key.toLowerCase();

    if (ALWAYS_BLOCKED_HEADERS.has(lowerKey)) {
      logBlockedHeader(key, value, 'ALWAYS_BLOCKED', request);
      blockedCount++;
      return;
    }

    if (!allowedHeaders.has(lowerKey)) {
      logBlockedHeader(key, value, 'NOT_IN_WHITELIST', request);
      blockedCount++;
      return;
    }

    if (!validateHeader(key, value)) {
      logBlockedHeader(key, value, 'CRLF_INJECTION', request);
      blockedCount++;
      return;
    }

    filteredHeaders.set(key, value);
  });

  const forwardedHeaders = generateForwardedHeaders(request);
  forwardedHeaders.forEach((value, key) => {
    filteredHeaders.set(key, value);
  });

  ensureRequestId(filteredHeaders);

  if (process.env.NODE_ENV === 'production' && blockedCount > 0) {
    console.warn(
      `[SECURITY] Blocked ${blockedCount} headers from ${(request as NextRequest & { ip?: string }).ip || 'unknown'}`
    );
  }

  return filteredHeaders;
}
