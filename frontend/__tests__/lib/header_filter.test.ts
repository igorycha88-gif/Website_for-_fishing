import { NextRequest } from 'next/server';
import {
  filterRequestHeaders,
  validateHeader,
  generateForwardedHeaders,
  ensureRequestId,
} from '@/lib/header_filter';

const createMockRequest = (
  headers: Record<string, string> = {},
  options: {
    ip?: string;
    protocol?: string;
    pathname?: string;
  } = {}
): NextRequest => {
  const mockHeaders = new Headers(headers);

  return {
    headers: mockHeaders,
    ip: options.ip,
    nextUrl: {
      protocol: options.protocol || 'https:',
      pathname: options.pathname || '/api/v1/test',
    },
  } as unknown as NextRequest;
};

describe('Header Filter Module', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  describe('validateHeader', () => {
    it('should pass valid headers', () => {
      expect(validateHeader('Authorization', 'Bearer token')).toBe(true);
      expect(validateHeader('Content-Type', 'application/json')).toBe(true);
      expect(validateHeader('X-Custom-Header', 'value')).toBe(true);
    });

    it('should reject \\r in value', () => {
      expect(validateHeader('X-Custom', 'value\r\nInjected: header')).toBe(false);
      expect(validateHeader('X-Test', 'value\r')).toBe(false);
    });

    it('should reject \\n in value', () => {
      expect(validateHeader('X-Custom', 'value\nInjected: header')).toBe(false);
      expect(validateHeader('X-Test', 'value\n')).toBe(false);
    });

    it('should reject \\r in key', () => {
      expect(validateHeader('X-Custom\r', 'value')).toBe(false);
      expect(validateHeader('X-Test\r\n', 'value')).toBe(false);
    });

    it('should reject invalid header names with spaces', () => {
      expect(validateHeader('X Custom Header', 'value')).toBe(false);
      expect(validateHeader('X-Custom Header', 'value')).toBe(false);
    });

    it('should reject invalid header names with special characters', () => {
      expect(validateHeader('X-Custom@Header', 'value')).toBe(false);
      expect(validateHeader('X-Custom:Header', 'value')).toBe(false);
    });

    it('should accept valid header name characters', () => {
      expect(validateHeader('X-Custom-Header_123', 'value')).toBe(true);
      expect(validateHeader('Accept-Encoding', 'gzip')).toBe(true);
    });
  });

  describe('generateForwardedHeaders', () => {
    it('should generate X-Forwarded-For from request.ip', () => {
      const request = createMockRequest({}, { ip: '192.168.1.100' });
      const headers = generateForwardedHeaders(request);

      expect(headers.get('X-Forwarded-For')).toBe('192.168.1.100');
    });

    it('should fallback to x-real-ip when request.ip is undefined', () => {
      const request = createMockRequest({ 'x-real-ip': '10.0.0.1' });
      const headers = generateForwardedHeaders(request);

      expect(headers.get('X-Forwarded-For')).toBe('10.0.0.1');
    });

    it('should fallback to unknown when both ip and x-real-ip are missing', () => {
      const request = createMockRequest({});
      const headers = generateForwardedHeaders(request);

      expect(headers.get('X-Forwarded-For')).toBe('unknown');
    });

    it('should generate X-Forwarded-Proto from request protocol', () => {
      const request = createMockRequest({}, { protocol: 'https:' });
      const headers = generateForwardedHeaders(request);

      expect(headers.get('X-Forwarded-Proto')).toBe('https');
    });

    it('should generate X-Forwarded-Proto as http', () => {
      const request = createMockRequest({}, { protocol: 'http:' });
      const headers = generateForwardedHeaders(request);

      expect(headers.get('X-Forwarded-Proto')).toBe('http');
    });

    it('should generate X-Forwarded-Host from Host header', () => {
      const request = createMockRequest({ host: 'example.com:3000' });
      const headers = generateForwardedHeaders(request);

      expect(headers.get('X-Forwarded-Host')).toBe('example.com:3000');
    });

    it('should fallback to unknown when Host header is missing', () => {
      const request = createMockRequest({});
      const headers = generateForwardedHeaders(request);

      expect(headers.get('X-Forwarded-Host')).toBe('unknown');
    });
  });

  describe('ensureRequestId', () => {
    it('should add UUID if missing', () => {
      const headers = new Headers();
      ensureRequestId(headers);

      const requestId = headers.get('X-Request-ID');
      expect(requestId).toBeDefined();
      expect(requestId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
      );
    });

    it('should not modify if exists', () => {
      const headers = new Headers();
      headers.set('X-Request-ID', 'custom-id-123');
      ensureRequestId(headers);

      expect(headers.get('X-Request-ID')).toBe('custom-id-123');
    });

    it('should preserve case-insensitive existing ID', () => {
      const headers = new Headers();
      headers.set('x-request-id', 'lowercase-id');
      ensureRequestId(headers);

      expect(headers.get('x-request-id')).toBe('lowercase-id');
    });
  });

  describe('filterRequestHeaders', () => {
    beforeEach(() => {
      delete process.env.PROXY_ALLOWED_HEADERS;
    });

    it('should pass allowed headers', () => {
      const request = createMockRequest({
        Authorization: 'Bearer token',
        'Content-Type': 'application/json',
        Accept: 'application/json',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('Authorization')).toBe('Bearer token');
      expect(filteredHeaders.get('Content-Type')).toBe('application/json');
      expect(filteredHeaders.get('Accept')).toBe('application/json');
    });

    it('should block non-whitelisted headers', () => {
      const request = createMockRequest({
        'X-Custom-Header': 'custom-value',
        'X-Another-Header': 'another-value',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Custom-Header')).toBeNull();
      expect(filteredHeaders.get('X-Another-Header')).toBeNull();
    });

    it('should always block Transfer-Encoding', () => {
      const request = createMockRequest({
        'Transfer-Encoding': 'chunked',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('Transfer-Encoding')).toBeNull();
    });

    it('should always block Host', () => {
      const request = createMockRequest({
        Host: 'malicious.com',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('Host')).toBeNull();
    });

    it('should always block Content-Length', () => {
      const request = createMockRequest({
        'Content-Length': '9999',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('Content-Length')).toBeNull();
    });

    it('should block CRLF injection attempts', () => {
      const mockHeaders = new Map<string, string>();
      mockHeaders.set('authorization', 'Bearer token\r\nSet-Cookie: malicious');

      const request = {
        headers: {
          forEach: (callback: (value: string, key: string) => void) => {
            mockHeaders.forEach((value, key) => callback(value, key));
          },
          get: (key: string) => mockHeaders.get(key.toLowerCase()),
        },
        ip: undefined,
        nextUrl: {
          protocol: 'https:',
          pathname: '/api/v1/test',
        },
      } as NextRequest;

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('Authorization')).toBeNull();
    });

    it('should ignore client X-Forwarded-For', () => {
      const request = createMockRequest(
        {
          'X-Forwarded-For': '127.0.0.1',
        },
        { ip: '192.168.1.100' }
      );

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Forwarded-For')).toBe('192.168.1.100');
    });

    it('should generate trusted X-Forwarded headers', () => {
      const request = createMockRequest(
        {},
        {
          ip: '192.168.1.100',
          protocol: 'https:',
        }
      );

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Forwarded-For')).toBe('192.168.1.100');
      expect(filteredHeaders.get('X-Forwarded-Proto')).toBe('https');
    });

    it('should generate X-Request-ID if missing', () => {
      const request = createMockRequest();

      const filteredHeaders = filterRequestHeaders(request);

      const requestId = filteredHeaders.get('X-Request-ID');
      expect(requestId).toBeDefined();
      expect(requestId).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i
      );
    });

    it('should preserve existing X-Request-ID', () => {
      const request = createMockRequest({
        'X-Request-ID': 'custom-request-id',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Request-ID')).toBe('custom-request-id');
    });

    it('should load custom headers from env', () => {
      process.env.PROXY_ALLOWED_HEADERS = 'x-custom-header,x-another-header';

      const request = createMockRequest({
        'X-Custom-Header': 'custom-value',
        'X-Another-Header': 'another-value',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Custom-Header')).toBe('custom-value');
      expect(filteredHeaders.get('X-Another-Header')).toBe('another-value');
    });

    it('should handle empty PROXY_ALLOWED_HEADERS', () => {
      process.env.PROXY_ALLOWED_HEADERS = '';

      const request = createMockRequest({
        Authorization: 'Bearer token',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('Authorization')).toBe('Bearer token');
    });

    it('should handle whitespace in PROXY_ALLOWED_HEADERS', () => {
      process.env.PROXY_ALLOWED_HEADERS = '  x-custom-header ,  x-another-header  ';

      const request = createMockRequest({
        'X-Custom-Header': 'custom-value',
        'X-Another-Header': 'another-value',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Custom-Header')).toBe('custom-value');
      expect(filteredHeaders.get('X-Another-Header')).toBe('another-value');
    });

    it('should filter empty strings from PROXY_ALLOWED_HEADERS', () => {
      process.env.PROXY_ALLOWED_HEADERS = 'x-custom-header,,x-another-header';

      const request = createMockRequest({
        'X-Custom-Header': 'custom-value',
        'X-Another-Header': 'another-value',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Custom-Header')).toBe('custom-value');
      expect(filteredHeaders.get('X-Another-Header')).toBe('another-value');
    });

    it('should support X-Correlation-ID', () => {
      const request = createMockRequest({
        'X-Correlation-ID': 'correlation-123',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Correlation-ID')).toBe('correlation-123');
    });

    it('should block X-Forwarded-Proto from client', () => {
      const request = createMockRequest({
        'X-Forwarded-Proto': 'http',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Forwarded-Proto')).not.toBe('http');
    });

    it('should block X-Forwarded-Host from client', () => {
      const request = createMockRequest({
        'X-Forwarded-Host': 'malicious.com',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Forwarded-Host')).not.toBe('malicious.com');
    });

    it('should block X-Real-IP from client', () => {
      const request = createMockRequest({
        'X-Real-IP': '127.0.0.1',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Real-IP')).toBeNull();
    });

    it('should block security headers from client', () => {
      const request = createMockRequest({
        'X-Frame-Options': 'DENY',
        'X-Content-Type-Options': 'nosniff',
        'Strict-Transport-Security': 'max-age=31536000',
      });

      const filteredHeaders = filterRequestHeaders(request);

      expect(filteredHeaders.get('X-Frame-Options')).toBeNull();
      expect(filteredHeaders.get('X-Content-Type-Options')).toBeNull();
      expect(filteredHeaders.get('Strict-Transport-Security')).toBeNull();
    });

    it('should handle multiple blocked headers', () => {
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      const request = createMockRequest({
        'X-Custom-1': 'value1',
        'X-Custom-2': 'value2',
        'X-Custom-3': 'value3',
      });

      filterRequestHeaders(request);

      expect(consoleWarnSpy).toHaveBeenCalled();

      consoleWarnSpy.mockRestore();
    });

    it('should log blocked headers in development', () => {
      const originalEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'development',
        writable: true,
        configurable: true,
      });

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      const request = createMockRequest({
        'X-Custom-Header': 'custom-value',
      });

      filterRequestHeaders(request);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('[SECURITY] Blocked header:'),
        expect.objectContaining({
          value: 'custom-value',
          reason: 'NOT_IN_WHITELIST',
        })
      );

      consoleWarnSpy.mockRestore();
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalEnv,
        writable: true,
        configurable: true,
      });
    });

    it('should log CRLF injection attempts in production', () => {
      const originalEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'production',
        writable: true,
        configurable: true,
      });

      const consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation();
      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      const mockHeaders = new Map<string, string>();
      mockHeaders.set('authorization', 'Bearer token\r\nSet-Cookie: malicious');

      const request = {
        headers: {
          forEach: (callback: (value: string, key: string) => void) => {
            mockHeaders.forEach((value, key) => callback(value, key));
          },
          get: (key: string) => mockHeaders.get(key.toLowerCase()),
        },
        ip: undefined,
        nextUrl: {
          protocol: 'https:',
          pathname: '/api/v1/test',
        },
      } as unknown as NextRequest;

      filterRequestHeaders(request);

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        '[SECURITY] CRLF Injection attempt detected',
        expect.objectContaining({
          header: 'authorization',
        })
      );

      consoleErrorSpy.mockRestore();
      consoleWarnSpy.mockRestore();
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalEnv,
        writable: true,
        configurable: true,
      });
    });

    it('should only log count in production for non-CRLF blocks', () => {
      const originalEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'production',
        writable: true,
        configurable: true,
      });

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      const request = createMockRequest(
        {
          'X-Custom-1': 'value1',
          'X-Custom-2': 'value2',
        },
        { ip: '192.168.1.100' }
      );

      filterRequestHeaders(request);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[SECURITY] Blocked 2 headers from 192.168.1.100'
      );

      consoleWarnSpy.mockRestore();
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalEnv,
        writable: true,
        configurable: true,
      });
    });

    it('should handle undefined ip in production log', () => {
      const originalEnv = process.env.NODE_ENV;
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: 'production',
        writable: true,
        configurable: true,
      });

      const consoleWarnSpy = jest.spyOn(console, 'warn').mockImplementation();

      const request = createMockRequest({
        'X-Custom-Header': 'value',
      });

      filterRequestHeaders(request);

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        '[SECURITY] Blocked 1 headers from unknown'
      );

      consoleWarnSpy.mockRestore();
      Object.defineProperty(process.env, 'NODE_ENV', {
        value: originalEnv,
        writable: true,
        configurable: true,
      });
    });
  });
});
