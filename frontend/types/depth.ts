export interface FishMatch {
  name: string;
  icon: string;
  depth_range: string;
  season: string;
}

export interface DepthResponse {
  depth: number | null;
  depth_display: string | null;
  category: string | null;
  source: string | null;
  accuracy_m: number | null;
  has_data: boolean;
  lat: number;
  lon: number;
  season: string;
  fish_match: FishMatch[];
  water_body_name: string | null;
  water_body_type: string | null;
  depth_type: string | null;
}

export interface DepthLayerConfig {
  enabled: boolean;
  opacity: number;
  showIsobaths: boolean;
}
