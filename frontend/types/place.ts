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
  depth?: number | null;
  depth_source?: "auto" | "manual" | null;
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
  depth?: number | null;
  depth_source?: "auto" | "manual";
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

export interface CatchPoint {
  id: string;
  latitude: number;
  longitude: number;
  fish_type: FishType;
  river: "volga" | "oka";
  name: string;
  description?: string;
  season?: string[];
  depth?: number | null;
  bait?: string;
  weight_avg?: number | null;
  is_demo: boolean;
  source_label?: string;
  created_at: string;
}

export interface CatchPointListResponse {
  catches: CatchPoint[];
  total: number;
  page: number;
  page_size: number;
}

export interface CatchPointFilters {
  river?: "volga" | "oka";
  fish_type_id?: string;
  min_lat?: number;
  min_lon?: number;
  max_lat?: number;
  max_lon?: number;
  page?: number;
  page_size?: number;
}
