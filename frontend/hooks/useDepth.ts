import { useState, useCallback } from "react";
import type { DepthResponse } from "@/types/depth";

export function useDepth() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [depthData, setDepthData] = useState<DepthResponse | null>(null);

  const queryDepth = useCallback(
    async (lat: number, lon: number): Promise<DepthResponse | null> => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `/api/v1/depth/point?lat=${lat}&lon=${lon}`
        );
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data: DepthResponse = await response.json();
        setDepthData(data);
        return data;
      } catch (err) {
        console.error("[useDepth] Failed to query depth:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
        return null;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const clearDepth = useCallback(() => {
    setDepthData(null);
    setError(null);
  }, []);

  return {
    loading,
    error,
    depthData,
    queryDepth,
    clearDepth,
  };
}
