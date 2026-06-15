import { useState, useCallback, useRef, useEffect } from "react";
import type { DepthAreaCollection, ColorScheme } from "@/types/depth";

export function useDepthAreas() {
  const [areas, setAreas] = useState<DepthAreaCollection | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchAreas = useCallback(
    async (
      minLat: number,
      minLon: number,
      maxLat: number,
      maxLon: number,
      scheme: ColorScheme = "navionics"
    ): Promise<DepthAreaCollection | null> => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);
      try {
        const url = `/api/v1/depth/areas?minLat=${minLat}&minLon=${minLon}&maxLat=${maxLat}&maxLon=${maxLon}&scheme=${scheme}`;
        const res = await fetch(url, { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: DepthAreaCollection = await res.json();
        setAreas(data);
        return data;
      } catch (err: any) {
        if (err.name === "AbortError") return null;
        console.error("[useDepthAreas] fetch error:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    return () => {
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  return { areas, loading, error, fetchAreas };
}
