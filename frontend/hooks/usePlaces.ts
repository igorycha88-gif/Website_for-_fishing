import { useState, useCallback } from "react";
import { useAuthStore } from "@/app/stores/useAuthStore";
import { Place, PlaceListResponse, PlaceCreate, PlaceUpdate, PlaceFilters } from "@/types/place";

interface ValidationError {
  loc: string[];
  msg: string;
  type: string;
}

function formatValidationErrors(errors: ValidationError[]): string {
  const fieldNames: Record<string, string> = {
    fish_types: "Виды рыбы",
    name: "Название",
    address: "Адрес",
    latitude: "Широта",
    longitude: "Долгота",
    place_type: "Тип места",
    access_type: "Тип подъезда",
    water_type: "Тип водоема",
    visibility: "Видимость",
  };

  const formattedErrors = errors.map((err) => {
    const field = err.loc[err.loc.length - 1];
    const fieldName = fieldNames[field] || field;
    return `${fieldName}: ${err.msg}`;
  });

  return formattedErrors.join("; ");
}

export function usePlaces() {
  const { token } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getAuthHeaders = useCallback(() => ({
    "Content-Type": "application/json",
    Authorization: token ? `Bearer ${token}` : "",
  }), [token]);

  const getPlaces = useCallback(async (filters?: PlaceFilters): Promise<PlaceListResponse> => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (filters) {
        if (filters.visibility && filters.visibility !== "all") {
          params.append("visibility", filters.visibility);
        }
        if (filters.place_type) {
          params.append("place_type", filters.place_type);
        }
        if (filters.access_type) {
          params.append("access_type", filters.access_type);
        }
        if (filters.fish_type_id) {
          params.append("fish_type_id", filters.fish_type_id);
        }
        if (filters.seasonality) {
          params.append("seasonality", filters.seasonality);
        }
        if (filters.search) {
          params.append("search", filters.search);
        }
        if (filters.page) {
          params.append("page", filters.page.toString());
        }
        if (filters.page_size) {
          params.append("page_size", filters.page_size.toString());
        }
        if (filters.sort) {
          params.append("sort", filters.sort);
        }
        if (filters.order) {
          params.append("order", filters.order);
        }
      }

      const response = await fetch(
        `/api/v1/places/my${params.toString() ? `?${params.toString()}` : ""}`,
        { headers: getAuthHeaders() }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch places");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch places");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const getPlace = useCallback(async (id: string): Promise<Place> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/places/my/${id}`, {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch place");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch place");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const createPlace = useCallback(async (placeData: PlaceCreate): Promise<Place> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/v1/places/my", {
        method: "POST",
        headers: getAuthHeaders(),
        body: JSON.stringify(placeData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        
        if (response.status === 422 && Array.isArray(errorData.detail)) {
          throw new Error(formatValidationErrors(errorData.detail));
        }
        
        if (response.status === 500) {
          throw new Error("Ошибка сервера. Попробуйте позже или обратитесь в поддержку.");
        }
        
        if (response.status === 400) {
          throw new Error(errorData.detail || "Некорректные данные");
        }
        
        throw new Error(errorData.detail || "Failed to create place");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create place");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const updatePlace = useCallback(async (id: string, placeData: PlaceUpdate): Promise<Place> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/places/my/${id}`, {
        method: "PUT",
        headers: getAuthHeaders(),
        body: JSON.stringify(placeData),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        
        if (response.status === 422 && Array.isArray(errorData.detail)) {
          throw new Error(formatValidationErrors(errorData.detail));
        }
        
        throw new Error(errorData.detail || "Failed to update place");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update place");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const deletePlace = useCallback(async (id: string): Promise<void> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v1/places/my/${id}`, {
        method: "DELETE",
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to delete place");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete place");
      throw err;
    } finally {
      setLoading(false);
    }
  }, [getAuthHeaders]);

  const getFishTypes = useCallback(async (category?: string): Promise<any> => {
    try {
      const params = new URLSearchParams();
      if (category) {
        params.append("category", category);
      }
      params.append("is_active", "true");

      const response = await fetch(
        `/api/v1/places/fish-types${params.toString() ? `?${params.toString()}` : ""}`,
        { headers: { "Content-Type": "application/json" } }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: "Unknown error" }));
        throw new Error(errorData.detail || "Failed to fetch fish types");
      }

      return response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch fish types");
      throw err;
    }
  }, []);

  return {
    loading,
    error,
    getPlaces,
    getPlace,
    createPlace,
    updatePlace,
    deletePlace,
    getFishTypes,
  };
}
