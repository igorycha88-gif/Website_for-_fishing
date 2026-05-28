import { parseRetryAfter, RateLimitError, APIError } from '@/lib/api/client';

describe('parseRetryAfter', () => {
  it('should return the number when header is a valid number', () => {
    expect(parseRetryAfter('45')).toBe(45);
    expect(parseRetryAfter('60')).toBe(60);
    expect(parseRetryAfter('1')).toBe(1);
  });

  it('should return 60 when header is null', () => {
    expect(parseRetryAfter(null)).toBe(60);
  });

  it('should return 60 when header is empty string', () => {
    expect(parseRetryAfter('')).toBe(60);
  });

  it('should return 60 when header is not a number', () => {
    expect(parseRetryAfter('invalid')).toBe(60);
    expect(parseRetryAfter('abc')).toBe(60);
  });

  it('should return 60 when header is negative', () => {
    expect(parseRetryAfter('-5')).toBe(60);
  });

  it('should return 60 when header is zero', () => {
    expect(parseRetryAfter('0')).toBe(60);
  });

  it('should parse number from string with spaces', () => {
    expect(parseRetryAfter(' 30 ')).toBe(30);
  });
});

describe('RateLimitError', () => {
  it('should create error with correct properties', () => {
    const details = {
      retryAfter: 45,
      limit: '5/minute',
      endpoint: '/api/v1/auth/login',
    };

    const error = new RateLimitError('Too many requests', details);

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(RateLimitError);
    expect(error.name).toBe('RateLimitError');
    expect(error.message).toBe('Too many requests');
    expect(error.retryAfter).toBe(45);
    expect(error.limit).toBe('5/minute');
    expect(error.endpoint).toBe('/api/v1/auth/login');
  });

  it('should be throwable', () => {
    const details = {
      retryAfter: 60,
      limit: '10/hour',
      endpoint: '/api/v1/auth/register',
    };

    expect(() => {
      throw new RateLimitError('Rate limit exceeded', details);
    }).toThrow(RateLimitError);
  });

  it('should be catchable as RateLimitError', () => {
    const details = {
      retryAfter: 30,
      limit: '3/hour',
      endpoint: '/api/v1/auth/reset-password/request',
    };

    try {
      throw new RateLimitError('Rate limit exceeded', details);
    } catch (error) {
      expect(error).toBeInstanceOf(RateLimitError);
      if (error instanceof RateLimitError) {
        expect(error.retryAfter).toBe(30);
        expect(error.limit).toBe('3/hour');
      }
    }
  });
});

describe('APIError', () => {
  it('should create error with correct properties', () => {
    const error = new APIError('Not found', 404, 'NOT_FOUND');

    expect(error).toBeInstanceOf(Error);
    expect(error).toBeInstanceOf(APIError);
    expect(error.name).toBe('APIError');
    expect(error.message).toBe('Not found');
    expect(error.status).toBe(404);
    expect(error.code).toBe('NOT_FOUND');
  });

  it('should create error without code', () => {
    const error = new APIError('Server error', 500);

    expect(error.message).toBe('Server error');
    expect(error.status).toBe(500);
    expect(error.code).toBeUndefined();
  });

  it('should be throwable', () => {
    expect(() => {
      throw new APIError('Unauthorized', 401, 'UNAUTHORIZED');
    }).toThrow(APIError);
  });
});
