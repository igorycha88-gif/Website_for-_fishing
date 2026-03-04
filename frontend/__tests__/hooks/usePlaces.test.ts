import { renderHook, act, waitFor } from '@testing-library/react';
import { usePlaces } from '@/hooks/usePlaces';
import { useAuthStore } from '@/app/stores/useAuthStore';

jest.mock('@/app/stores/useAuthStore');

const mockFetch = global.fetch as jest.Mock;

describe('usePlaces', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      token: 'test-token',
    });
  });

  describe('getPlaces', () => {
    it('should fetch places successfully', async () => {
      const mockPlaces = {
        places: [
          {
            id: '1',
            owner_id: 'user1',
            name: 'Test Place',
            latitude: 55.7558,
            longitude: 37.6173,
            address: 'Test Address',
            place_type: 'wild',
            access_type: 'car',
            fish_types: [],
            visibility: 'private',
            images: [],
            rating_avg: 0,
            reviews_count: 0,
            is_active: true,
            created_at: '2024-01-01',
            updated_at: '2024-01-01',
          },
        ],
        total: 1,
        page: 1,
        page_size: 20,
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockPlaces,
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        const response = await result.current.getPlaces();
        expect(response).toEqual(mockPlaces);
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/places/my',
        expect.objectContaining({
          headers: expect.objectContaining({
            Authorization: 'Bearer test-token',
          }),
        })
      );
    });

    it('should handle fetch error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Not found' }),
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        await expect(result.current.getPlaces()).rejects.toThrow('Not found');
      });
    });

    it('should send filters as query params', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ places: [], total: 0, page: 1, page_size: 20 }),
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        await result.current.getPlaces({
          visibility: 'private',
          place_type: 'wild',
          search: 'test',
        });
      });

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('visibility=private'),
        expect.any(Object)
      );
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('place_type=wild'),
        expect.any(Object)
      );
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('search=test'),
        expect.any(Object)
      );
    });
  });

  describe('createPlace', () => {
    it('should create place successfully', async () => {
      const newPlace = {
        name: 'New Place',
        latitude: 55.7558,
        longitude: 37.6173,
        address: 'Test Address',
        place_type: 'wild' as const,
        access_type: 'car' as const,
        fish_types: [],
        visibility: 'private' as const,
        images: [],
      };

      const mockResponse = {
        id: '1',
        owner_id: 'user1',
        ...newPlace,
        rating_avg: 0,
        reviews_count: 0,
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-01',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        const response = await result.current.createPlace(newPlace);
        expect(response).toEqual(mockResponse);
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/places/my',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(newPlace),
        })
      );
    });
  });

  describe('deletePlace', () => {
    it('should delete place successfully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        await result.current.deletePlace('1');
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/places/my/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });

    it('should handle delete error', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Not authorized' }),
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        await expect(result.current.deletePlace('1')).rejects.toThrow('Not authorized');
      });
    });
  });

  describe('updatePlace', () => {
    it('should update place successfully', async () => {
      const updateData = {
        name: 'Updated Place',
        description: 'Updated description',
      };

      const mockResponse = {
        id: '1',
        owner_id: 'user1',
        name: 'Updated Place',
        description: 'Updated description',
        latitude: 55.7558,
        longitude: 37.6173,
        address: 'Test Address',
        place_type: 'wild',
        access_type: 'car',
        fish_types: [],
        visibility: 'private',
        images: [],
        rating_avg: 0,
        reviews_count: 0,
        is_active: true,
        created_at: '2024-01-01',
        updated_at: '2024-01-02',
      };

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        const response = await result.current.updatePlace('1', updateData);
        expect(response).toEqual(mockResponse);
      });

      expect(mockFetch).toHaveBeenCalledWith(
        '/api/v1/places/my/1',
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      );
    });

    it('should handle update error with 422 validation', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 422,
        json: async () => ({
          detail: [
            { loc: ['body', 'name'], msg: 'Name is required', type: 'value_error' },
          ],
        }),
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        await expect(result.current.updatePlace('1', { name: '' })).rejects.toThrow('Название');
      });
    });

    it('should handle update error with generic message', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Update failed' }),
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        await expect(result.current.updatePlace('1', {})).rejects.toThrow('Update failed');
      });
    });
  });

  describe('getFishTypes', () => {
    it('should fetch fish types successfully', async () => {
      const mockFishTypes = [
        { id: '1', name: 'Щука', icon: '🐟', category: 'predatory' },
        { id: '2', name: 'Карп', icon: '🐠', category: 'peaceful' },
      ];

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockFishTypes,
      });

      const { result } = renderHook(() => usePlaces());

      await act(async () => {
        const response = await result.current.getFishTypes();
        expect(response).toEqual(mockFishTypes);
      });
    });
  });
});
