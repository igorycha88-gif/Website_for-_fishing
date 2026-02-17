import { renderHook, act, waitFor } from '@testing-library/react';
import { useForecast } from '@/hooks/useForecast';

const mockFetch = global.fetch as jest.Mock;

describe('useForecast', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('getRegions', () => {
    it('should fetch regions successfully', async () => {
      const mockRegions = {
        regions: [
          {
            id: '1',
            name: 'Москва',
            code: 'MOW',
            latitude: 55.7558,
            longitude: 37.6173,
            timezone: 'Europe/Moscow',
            is_active: true,
          },
          {
            id: '2',
            name: 'Санкт-Петербург',
            code: 'SPE',
            latitude: 59.9343,
            longitude: 30.3351,
            timezone: 'Europe/Moscow',
            is_active: true,
          },
        ],
        total: 2,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockRegions,
      });

      const { result } = renderHook(() => useForecast());

      await act(async () => {
        const response = await result.current.getRegions();
        expect(response).toEqual(mockRegions);
      });

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/regions');
    });

    it('should handle fetch error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Server error' }),
      });

      const { result } = renderHook(() => useForecast());

      await act(async () => {
        await expect(result.current.getRegions()).rejects.toThrow('Server error');
      });
    });

    it('should set error state on failure', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Network error' }),
      });

      const { result } = renderHook(() => useForecast());

      await act(async () => {
        try {
          await result.current.getRegions();
        } catch (e) {
          // expected
        }
      });

      expect(result.current.error).toBe('Network error');
    });
  });

  describe('getForecast', () => {
    it('should fetch forecast for a region', async () => {
      const mockForecast = {
        region: {
          id: '1',
          name: 'Москва',
          code: 'MOW',
          latitude: 55.7558,
          longitude: 37.6173,
          timezone: 'Europe/Moscow',
          is_active: true,
        },
        forecast_date: '2025-02-17',
        weather: {
          temperature: -5,
          pressure: 760,
          wind_speed: 3,
          precipitation: 0,
          moon_phase: 0.75,
          sunrise: '07:45',
          sunset: '17:30',
        },
        forecasts: [
          {
            fish_type: { id: '1', name: 'Щука', icon: '🐟' },
            forecasts: [
              { time_of_day: 'morning', bite_score: 75 },
              { time_of_day: 'day', bite_score: 55 },
              { time_of_day: 'evening', bite_score: 70 },
              { time_of_day: 'night', bite_score: 30 },
            ],
          },
        ],
        multi_day_forecast: [],
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockForecast,
      });

      const { result } = renderHook(() => useForecast());

      await act(async () => {
        const response = await result.current.getForecast('1');
        expect(response).toEqual(mockForecast);
      });

      expect(mockFetch).toHaveBeenCalledWith('/api/v1/forecast/1');
    });

    it('should send forecast_date as query param', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ region: {}, forecast_date: '2025-02-18', weather: null, forecasts: [] }),
      });

      const { result } = renderHook(() => useForecast());

      await act(async () => {
        await result.current.getForecast('1', '2025-02-18');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('forecast_date=2025-02-18')
      );
    });

    it('should handle forecast fetch error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Region not found' }),
      });

      const { result } = renderHook(() => useForecast());

      await act(async () => {
        await expect(result.current.getForecast('invalid-id')).rejects.toThrow('Region not found');
      });
    });
  });

  describe('findNearestRegion', () => {
    it('should find nearest region by coordinates', async () => {
      const mockRegions = {
        regions: [
          {
            id: '1',
            name: 'Москва',
            code: 'MOW',
            latitude: 55.7558,
            longitude: 37.6173,
            timezone: 'Europe/Moscow',
            is_active: true,
          },
          {
            id: '2',
            name: 'Санкт-Петербург',
            code: 'SPE',
            latitude: 59.9343,
            longitude: 30.3351,
            timezone: 'Europe/Moscow',
            is_active: true,
          },
        ],
        total: 2,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockRegions,
      });

      const { result } = renderHook(() => useForecast());

      const nearest = await result.current.findNearestRegion(55.7, 37.6);

      expect(nearest).not.toBeNull();
      expect(nearest?.code).toBe('MOW');
    });

    it('should return null when no regions available', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ regions: [], total: 0 }),
      });

      const { result } = renderHook(() => useForecast());

      const nearest = await result.current.findNearestRegion(55.7, 37.6);

      expect(nearest).toBeNull();
    });

    it('should return null on fetch error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Error' }),
      });

      const { result } = renderHook(() => useForecast());

      const nearest = await result.current.findNearestRegion(55.7, 37.6);

      expect(nearest).toBeNull();
    });
  });

  describe('loading state', () => {
    it('should set loading to true during fetch', async () => {
      let resolvePromise: (value: any) => void;
      const pendingPromise = new Promise((resolve) => {
        resolvePromise = resolve;
      });

      mockFetch.mockImplementationOnce(() => pendingPromise);

      const { result } = renderHook(() => useForecast());

      act(() => {
        result.current.getRegions();
      });

      expect(result.current.loading).toBe(true);

      await act(async () => {
        resolvePromise!({
          ok: true,
          json: async () => ({ regions: [], total: 0 }),
        });
      });

      expect(result.current.loading).toBe(false);
    });
  });
});
