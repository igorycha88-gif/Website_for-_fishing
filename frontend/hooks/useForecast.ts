import { useState, useCallback } from "react";
import {
  Region,
  RegionsResponse,
  ForecastResponse,
} from "@/types/forecast";

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

  return {
    loading,
    error,
    getRegions,
    getForecast,
    findNearestRegion,
  };
}
