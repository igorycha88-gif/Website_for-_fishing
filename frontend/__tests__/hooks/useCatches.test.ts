import { renderHook, act } from '@testing-library/react';
import { useCatches } from '@/hooks/useCatches';

const mockFetch = global.fetch as jest.Mock;

const mockCatchPoint = {
  id: '1',
  latitude: 56.86,
  longitude: 35.92,
  fish_type: { id: 'ft1', name: 'Щука', icon: '🐟', category: 'predatory' },
  river: 'volga',
  name: 'Верхняя Волга — Тверь',
  description: 'Закоряженные ямы',
  season: ['summer', 'autumn'],
  depth: 3.5,
  bait: 'Воблер',
  weight_avg: 2.1,
  is_demo: true,
  source_label: 'Демонстрационные данные',
  created_at: '2024-01-01',
};

describe('useCatches', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('should fetch catch points successfully', async () => {
    const mockResponse = {
      catches: [mockCatchPoint],
      total: 1,
      page: 1,
      page_size: 200,
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useCatches());

    let response;
    await act(async () => {
      response = await result.current.getCatches();
    });

    expect(response).toEqual(mockResponse);
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/catches',
      expect.objectContaining({
        headers: { 'Content-Type': 'application/json' },
      })
    );
  });

  it('should pass river filter as query param', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ catches: [], total: 0, page: 1, page_size: 200 }),
    });

    const { result } = renderHook(() => useCatches());

    await act(async () => {
      await result.current.getCatches({ river: 'oka' });
    });

    expect(mockFetch).toHaveBeenCalledWith(
      '/api/v1/catches?river=oka',
      expect.any(Object)
    );
  });

  it('should return empty list on fetch error', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ detail: 'Server error' }),
    });

    const { result } = renderHook(() => useCatches());

    let response: any;
    await act(async () => {
      response = await result.current.getCatches();
    });

    expect(response.catches).toEqual([]);
    expect(result.current.error).toBeTruthy();
  });

  it('should fetch a single catch point', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockCatchPoint,
    });

    const { result } = renderHook(() => useCatches());

    let response: any;
    await act(async () => {
      response = await result.current.getCatch('1');
    });

    expect(response).toEqual(mockCatchPoint);
    expect(mockFetch).toHaveBeenCalledWith('/api/v1/catches/1', expect.any(Object));
  });

  it('should return null when single catch not found', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, json: async () => ({}) });

    const { result } = renderHook(() => useCatches());

    let response: any;
    await act(async () => {
      response = await result.current.getCatch('missing');
    });

    expect(response).toBeNull();
  });
});
