"use client";

import { useState, useEffect, useCallback, useRef } from "react";

export interface RateLimitState {
  isLimited: boolean;
  remainingSeconds: number;
  startLimit: (seconds: number) => void;
  clearLimit: () => void;
}

export function useRateLimit(): RateLimitState {
  const [isLimited, setIsLimited] = useState(false);
  const [remainingSeconds, setRemainingSeconds] = useState(0);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const endTimeRef = useRef<number | null>(null);

  const clearLimit = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    endTimeRef.current = null;
    setIsLimited(false);
    setRemainingSeconds(0);
  }, []);

  const startLimit = useCallback((seconds: number) => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
    }

    const endTime = Date.now() + seconds * 1000;
    endTimeRef.current = endTime;
    
    setIsLimited(true);
    setRemainingSeconds(seconds);

    intervalRef.current = setInterval(() => {
      const now = Date.now();
      const remaining = Math.max(0, Math.ceil((endTime - now) / 1000));
      
      setRemainingSeconds(remaining);

      if (remaining <= 0) {
        clearLimit();
      }
    }, 1000);
  }, [clearLimit]);

  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    isLimited,
    remainingSeconds,
    startLimit,
    clearLimit,
  };
}

export function formatRemainingTime(seconds: number): string {
  if (seconds <= 0) return "";
  
  if (seconds < 60) {
    return `${seconds} ${pluralize(seconds, "секунда", "секунды", "секунд")}`;
  }
  
  const minutes = Math.floor(seconds / 60);
  const secs = seconds % 60;
  
  if (secs === 0) {
    return `${minutes} ${pluralize(minutes, "минута", "минуты", "минут")}`;
  }
  
  return `${minutes} ${pluralize(minutes, "минута", "минуты", "минут")} ${secs} ${pluralize(secs, "секунда", "секунды", "секунд")}`;
}

function pluralize(n: number, one: string, few: string, many: string): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  
  if (mod10 === 1 && mod100 !== 11) {
    return one;
  }
  
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) {
    return few;
  }
  
  return many;
}

export default useRateLimit;
