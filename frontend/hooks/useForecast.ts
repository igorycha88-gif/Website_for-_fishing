import { useState, useCallback } from "react";
import {
  Region,
  RegionsResponse,
  ForecastResponse,
  FishTypeBrief,
  AvailableDatesResponse,
  DaySummaryResponse,
} from "@/types/forecast";

interface CustomFishResponse {
  id: string;
  fish_type: FishTypeBrief;
  created_at?: string;
}

interface CustomFishListResponse {
  fish_types: CustomFishResponse[];
  total: number;
}

interface AllFishTypesResponse {
  fish_types: FishTypeBrief[];
  total: number;
}

export function useForecast() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getRegions = useCallback(async (): Promise<RegionsResponse> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/regions");

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch regions");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch regions");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getForecast = useCallback(async (
    regionId: string,
    forecastDate?: string
  ): Promise<ForecastResponse> => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (forecastDate) {
        params.append("forecast_date", forecastDate);
      }

      const response = await fetch(
        `/api/v1/forecast/${regionId}${params.toString() ? `?${params.toString()}` : ""}`
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch forecast");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch forecast");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const findNearestRegion = useCallback(async (
    latitude: number,
    longitude: number
  ): Promise<Region | null> => {
    try {
      const regionsData = await getRegions();
      
      if (!regionsData.regions || regionsData.regions.length === 0) {
        return null;
      }

      let nearestRegion: Region | null = null;
      let minDistance = Infinity;

      for (const region of regionsData.regions) {
        const distance = Math.sqrt(
          Math.pow(Number(region.latitude) - latitude, 2) +
          Math.pow(Number(region.longitude) - longitude, 2)
        );

        if (distance < minDistance) {
          minDistance = distance;
          nearestRegion = region;
        }
      }

      return nearestRegion;
    } catch (err) {
      console.error("Error finding nearest region:", err);
      return null;
    }
  }, [getRegions]);

  const getCustomFish = useCallback(async (regionId: string, token?: string | null): Promise<CustomFishListResponse> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/forecast/${regionId}/custom-fish`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch custom fish");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch custom fish");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const addCustomFish = useCallback(async (regionId: string, fishTypeId: string, token?: string | null): Promise<{ success: boolean; fish_type: FishTypeBrief }> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/forecast/${regionId}/custom-fish`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ fish_type_id: fishTypeId }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || errorData.message || "Failed to add custom fish");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add custom fish");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const removeCustomFish = useCallback(async (regionId: string, fishTypeId: string, token?: string | null): Promise<{ success: boolean }> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/forecast/${regionId}/custom-fish/${fishTypeId}`, {
        method: "DELETE",
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || errorData.message || "Failed to remove custom fish");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to remove custom fish");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getAllFishTypes = useCallback(async (regionId: string, token?: string | null): Promise<AllFishTypesResponse> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/forecast/${regionId}/all-fish-types`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch fish types");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch fish types");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getAvailableDates = useCallback(async (regionId: string): Promise<AvailableDatesResponse> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/forecast/${regionId}/available-dates`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch available dates");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch available dates");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getDaySummary = useCallback(async (regionId: string, date: string): Promise<DaySummaryResponse> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/forecast/${regionId}/day-summary?forecast_date=${date}`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch day summary");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch day summary");
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    loading,
    error,
    getRegions,
    getForecast,
    findNearestRegion,
    getCustomFish,
    addCustomFish,
    removeCustomFish,
    getAllFishTypes,
    getAvailableDates,
    getDaySummary,
  };
}
