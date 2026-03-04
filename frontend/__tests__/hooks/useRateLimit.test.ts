import { renderHook, act } from '@testing-library/react';
import { useRateLimit, formatRemainingTime } from '@/hooks/useRateLimit';

describe('useRateLimit', () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('initial state', () => {
    it('should start with isLimited false', () => {
      const { result } = renderHook(() => useRateLimit());

      expect(result.current.isLimited).toBe(false);
    });

    it('should start with remainingSeconds 0', () => {
      const { result } = renderHook(() => useRateLimit());

      expect(result.current.remainingSeconds).toBe(0);
    });
  });

  describe('startLimit', () => {
    it('should set isLimited to true', () => {
      const { result } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(60);
      });

      expect(result.current.isLimited).toBe(true);
    });

    it('should set remainingSeconds to the provided value', () => {
      const { result } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(45);
      });

      expect(result.current.remainingSeconds).toBe(45);
    });

    it('should countdown remaining seconds', () => {
      const { result } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(10);
      });

      expect(result.current.remainingSeconds).toBe(10);

      act(() => {
        jest.advanceTimersByTime(1000);
      });

      expect(result.current.remainingSeconds).toBe(9);

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(result.current.remainingSeconds).toBe(6);
    });

    it('should reset limit when countdown reaches 0', () => {
      const { result } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(3);
      });

      expect(result.current.isLimited).toBe(true);
      expect(result.current.remainingSeconds).toBe(3);

      act(() => {
        jest.advanceTimersByTime(3000);
      });

      expect(result.current.isLimited).toBe(false);
      expect(result.current.remainingSeconds).toBe(0);
    });

    it('should replace existing limit when called again', () => {
      const { result } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(60);
      });

      expect(result.current.remainingSeconds).toBe(60);

      act(() => {
        result.current.startLimit(30);
      });

      expect(result.current.remainingSeconds).toBe(30);
    });
  });

  describe('clearLimit', () => {
    it('should set isLimited to false', () => {
      const { result } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(60);
      });

      expect(result.current.isLimited).toBe(true);

      act(() => {
        result.current.clearLimit();
      });

      expect(result.current.isLimited).toBe(false);
    });

    it('should set remainingSeconds to 0', () => {
      const { result } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(60);
      });

      act(() => {
        result.current.clearLimit();
      });

      expect(result.current.remainingSeconds).toBe(0);
    });

    it('should stop the countdown', () => {
      const { result } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(60);
        result.current.clearLimit();
      });

      act(() => {
        jest.advanceTimersByTime(5000);
      });

      expect(result.current.isLimited).toBe(false);
      expect(result.current.remainingSeconds).toBe(0);
    });
  });

  describe('cleanup on unmount', () => {
    it('should clear interval on unmount', () => {
      const { result, unmount } = renderHook(() => useRateLimit());

      act(() => {
        result.current.startLimit(60);
      });

      unmount();

      act(() => {
        jest.advanceTimersByTime(5000);
      });
    });
  });
});

describe('formatRemainingTime', () => {
  it('should return empty string for 0 seconds', () => {
    expect(formatRemainingTime(0)).toBe('');
  });

  it('should return empty string for negative seconds', () => {
    expect(formatRemainingTime(-5)).toBe('');
  });

  it('should format seconds correctly', () => {
    expect(formatRemainingTime(1)).toBe('1 секунда');
    expect(formatRemainingTime(2)).toBe('2 секунды');
    expect(formatRemainingTime(5)).toBe('5 секунд');
    expect(formatRemainingTime(30)).toBe('30 секунд');
    expect(formatRemainingTime(59)).toBe('59 секунд');
  });

  it('should format minutes correctly', () => {
    expect(formatRemainingTime(60)).toBe('1 минута');
    expect(formatRemainingTime(120)).toBe('2 минуты');
    expect(formatRemainingTime(300)).toBe('5 минут');
  });

  it('should format minutes and seconds correctly', () => {
    expect(formatRemainingTime(61)).toBe('1 минута 1 секунда');
    expect(formatRemainingTime(90)).toBe('1 минута 30 секунд');
    expect(formatRemainingTime(125)).toBe('2 минуты 5 секунд');
  });
});
