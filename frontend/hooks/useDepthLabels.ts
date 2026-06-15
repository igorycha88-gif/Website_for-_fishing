import { useState, useCallback, useRef, useEffect } from "react";
import type { DepthLabelCollection } from "@/types/depth";

export function useDepthLabels() {
  const [labels, setLabels] = useState<DepthLabelCollection | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchLabels = useCallback(
    async (
      minLat: number,
      minLon: number,
      maxLat: number,
      maxLon: number,
      zoom: number = 10
    ): Promise<DepthLabelCollection | null> => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
      const controller = new AbortController();
      abortRef.current = controller;

      setLoading(true);
      setError(null);
      try {
        const url = `/api/v1/depth/labels?minLat=${minLat}&minLon=${minLon}&maxLat=${maxLat}&maxLon=${maxLon}&zoom=${zoom}`;
        const res = await fetch(url, { signal: controller.signal });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data: DepthLabelCollection = await res.json();
        setLabels(data);
        return data;
      } catch (err: any) {
        if (err.name === "AbortError") return null;
        console.error("[useDepthLabels] fetch error:", err);
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

  return { labels, loading, error, fetchLabels };
}
