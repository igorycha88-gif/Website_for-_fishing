export interface Place {
  id: string;
  owner_id: string;
  name: string;
  description?: string;
  latitude: number;
  longitude: number;
  address: string;
  place_type: "wild" | "camping" | "resort";
  access_type: "car" | "boat" | "foot";
  water_type: "river" | "lake" | "sea";
  fish_types: FishType[];
  seasonality?: Array<"spring" | "summer" | "autumn" | "winter">;
  visibility: "private" | "public";
  images: string[];
  rating_avg: number;
  reviews_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  is_favorite?: boolean;
}

export interface FishType {
  id: string;
  name: string;
  icon?: string;
  category: string;
}

export interface PlaceListResponse {
  places: Place[];
  total: number;
  page: number;
  page_size: number;
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
  order?: "asc" | "desc";
}

export interface PlaceCreate {
  name: string;
  description?: string;
  latitude: number;
  longitude: number;
  address: string;
  place_type: "wild" | "camping" | "resort";
  access_type: "car" | "boat" | "foot";
  water_type?: "river" | "lake" | "sea";
  fish_types: string[];
  seasonality?: Array<"spring" | "summer" | "autumn" | "winter">;
  visibility: "private" | "public";
  images?: string[];
}

export interface PlaceUpdate {
  name?: string;
  description?: string;
  latitude?: number;
  longitude?: number;
  address?: string;
  place_type?: "wild" | "camping" | "resort";
  access_type?: "car" | "boat" | "foot";
  water_type?: "river" | "lake" | "sea";
  fish_types?: string[];
  seasonality?: Array<"spring" | "summer" | "autumn" | "winter">;
  visibility?: "private" | "public";
  images?: string[];
}
