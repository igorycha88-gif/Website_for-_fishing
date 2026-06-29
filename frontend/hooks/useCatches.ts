import { useState, useCallback } from "react";
import {
  CatchPoint,
  CatchPointListResponse,
  CatchPointFilters,
} from "@/types/place";

export function useCatches() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getCatches = useCallback(
    async (filters?: CatchPointFilters): Promise<CatchPointListResponse> => {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams();
        if (filters) {
          if (filters.river) params.append("river", filters.river);
          if (filters.fish_type_id)
            params.append("fish_type_id", filters.fish_type_id);
          if (filters.min_lat != null)
            params.append("min_lat", String(filters.min_lat));
          if (filters.min_lon != null)
            params.append("min_lon", String(filters.min_lon));
          if (filters.max_lat != null)
            params.append("max_lat", String(filters.max_lat));
          if (filters.max_lon != null)
            params.append("max_lon", String(filters.max_lon));
          if (filters.page) params.append("page", String(filters.page));
          if (filters.page_size)
            params.append("page_size", String(filters.page_size));
        }

        const response = await fetch(
          `/api/v1/catches${params.toString() ? `?${params.toString()}` : ""}`,
          { headers: { "Content-Type": "application/json" } }
        );

        if (!response.ok) {
          const errorData = await response
            .json()
            .catch(() => ({ detail: "Unknown error" }));
          throw new Error(errorData.detail || "Failed to fetch catch points");
        }

        return response.json();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to fetch catch points"
        );
        return { catches: [], total: 0, page: 1, page_size: 200 };
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const getCatch = useCallback(async (id: string): Promise<CatchPoint | null> => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/v1/catches/${id}`, {
        headers: { "Content-Type": "application/json" },
      });
      if (!response.ok) {
        return null;
      }
      return response.json();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch catch point"
      );
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { loading, error, getCatches, getCatch };
}
