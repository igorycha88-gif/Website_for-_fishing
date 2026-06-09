import { useAuthStore } from "@/app/stores/useAuthStore";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

export interface Place {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  address: string;
  place_type: "wild" | "camping" | "resort";
  access_type: "car" | "boat" | "foot";
  fish_types: Array<{
    id: string;
    name: string;
    icon: string;
    category: string;
  }>;
  seasonality?: Array<"spring" | "summer" | "autumn" | "winter">;
  visibility: "private" | "public";
  images: string[];
  description?: string;
  rating_avg?: number;
  reviews_count?: number;
  is_favorite?: boolean;
  created_at: string;
  updated_at: string;
  owner_id: string;
}

export interface PlaceFilters {
  visibility?: "private" | "public" | "all";
  place_type?: "wild" | "camping" | "resort";
  access_type?: "car" | "boat" | "foot";
  fish_type_id?: string;
  seasonality?: string;
  search?: string;
  page?: number;
  page_size?: number;
  sort?: string;
  order?: string;
}

export interface PlaceListResponse {
  places: Place[];
  total: number;
  page: number;
  page_size: number;
}

class PlacesAPIError extends Error {
  constructor(message: string, public status?: number) {
    super(message);
    this.name = "PlacesAPIError";
    this.status = status;
  }
}

async function getAuthHeaders(): Promise<HeadersInit> {
  const token = useAuthStore.getState().token;
  return {
    "Content-Type": "application/json",
    Authorization: token ? `Bearer ${token}` : "",
  };
}

export async function getPlaces(filters: PlaceFilters = {}): Promise<PlaceListResponse> {
  const params = new URLSearchParams();
  
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

  const response = await fetch(`${API_BASE_URL}/places/my?${params}`, {
    headers: await getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new PlacesAPIError(error.detail || "Failed to fetch places", response.status);
  }

  return response.json();
}

export async function getPlace(id: string): Promise<Place> {
  const response = await fetch(`${API_BASE_URL}/places/my/${id}`, {
    headers: await getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new PlacesAPIError(error.detail || "Failed to fetch place", response.status);
  }

  return response.json();
}

export async function createPlace(placeData: any): Promise<Place> {
  const response = await fetch(`${API_BASE_URL}/places/my`, {
    method: "POST",
    headers: await getAuthHeaders(),
    body: JSON.stringify(placeData),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new PlacesAPIError(error.detail || "Failed to create place", response.status);
  }

  return response.json();
}

export async function updatePlace(id: string, placeData: any): Promise<Place> {
  console.log("[placesApi] updatePlace called with:", { id, placeData });
  const body = JSON.stringify(placeData);
  console.log("[placesApi] Request body:", body);
  
  const response = await fetch(`${API_BASE_URL}/places/my/${id}`, {
    method: "PUT",
    headers: await getAuthHeaders(),
    body,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    console.error("[placesApi] Update place error:", { status: response.status, error });
    throw new PlacesAPIError(error.detail || "Failed to update place", response.status);
  }

  return response.json();
}

export async function deletePlace(id: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/places/my/${id}`, {
    method: "DELETE",
    headers: await getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new PlacesAPIError(error.detail || "Failed to delete place", response.status);
  }
}

export async function toggleFavorite(placeId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/places/favorites/${placeId}`, {
    method: "POST",
    headers: await getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new PlacesAPIError(error.detail || "Failed to toggle favorite", response.status);
  }
}

export async function removeFavorite(placeId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/places/favorites/${placeId}`, {
    method: "DELETE",
    headers: await getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new PlacesAPIError(error.detail || "Failed to remove favorite", response.status);
  }
}

export async function getFavorites(page: number = 1, page_size: number = 20): Promise<PlaceListResponse> {
  const response = await fetch(`${API_BASE_URL}/places/favorites?page=${page}&page_size=${page_size}`, {
    headers: await getAuthHeaders(),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new PlacesAPIError(error.detail || "Failed to fetch favorites", response.status);
  }

  return response.json();
}

export async function getFishTypes(category?: string, is_active: boolean = true): Promise<any> {
  const params = new URLSearchParams();
  if (category) {
    params.append("category", category);
  }
  params.append("is_active", is_active.toString());

  const response = await fetch(`${API_BASE_URL}/fish-types?${params}`, {
    headers: { "Content-Type": "application/json" },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new PlacesAPIError(error.detail || "Failed to fetch fish types", response.status);
  }

  return response.json();
}
