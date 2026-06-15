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

export type ColorScheme = "navionics" | "contrast" | "sport";

export interface DepthLayerConfig {
  enabled: boolean;
  opacity: number;
  showIsobaths: boolean;
  showLabels: boolean;
  colorScheme: ColorScheme;
}

export interface DepthAreaFeature {
  type: "Feature";
  geometry: {
    type: "Polygon";
    coordinates: number[][][];
  };
  properties: {
    name: string;
    water_type: string;
    max_depth: number | null;
    avg_depth: number | null;
    depth: number | null;
    color: string;
    category: string | null;
    region?: string;
    fallback_bbox?: boolean;
  };
}

export interface DepthAreaCollection {
  type: "FeatureCollection";
  features: DepthAreaFeature[];
}

export interface DepthLabelFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: number[];
  };
  properties: {
    name: string;
    depth: number;
    label: string;
    water_type: string;
  };
}

export interface DepthLabelCollection {
  type: "FeatureCollection";
  features: DepthLabelFeature[];
}
