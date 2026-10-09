/**
 * Custom hook for fetching trend data from the API
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import http from '@/services/http'
import {
  AtAGlanceData,
  HeatmapData,
  BubbleChartData,
  NetworkGraphData,
  AnimatedTimelineData,
} from '@/types/trends';

const API_BASE = '/api/analytics/trends';

interface UseTrendDataReturn<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

// Generic fetch hook
function useFetch<T>(
  endpoint: string,
  params: Record<string, any> = {},
  autoFetch: boolean = true
): UseTrendDataReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const queryParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          if (Array.isArray(value)) {
            value.forEach(v => queryParams.append(key, String(v)));
          } else {
            queryParams.set(key, String(value));
          }
        }
      });

      const url = `${API_BASE}${endpoint}${queryParams.toString() ? `?${queryParams}` : ''}`;
      const response = await http.get<T>(url);
      setData(response.data);
    } catch (err: any) {
      // Properly extract error message from Pydantic validation errors
      const detail = err.response?.data?.detail;
      let errorMessage = 'Failed to fetch data';

      if (typeof detail === 'string') {
        errorMessage = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        // Pydantic validation error array
        errorMessage = detail.map((e: any) => e.msg || JSON.stringify(e)).join(', ');
      } else if (detail?.msg) {
        errorMessage = detail.msg;
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [endpoint, JSON.stringify(params)]);

  // Fetch when enabled and the parameters changed since the last fetch, so
  // switching back to a tab does not reload it (Refresh does).
  const fetchedKey = useRef<string | null>(null);
  useEffect(() => {
    const key = `${endpoint}?${JSON.stringify(params)}`;
    if (autoFetch && fetchedKey.current !== key) {
      fetchedKey.current = key;
      fetch();
    }
  }, [fetch, autoFetch]);

  return { data, loading, error, refetch: fetch };
}

// At-a-Glance data hook
export function useAtAGlanceData(
  hours: number = 48,
  anomalyThreshold: number = 2.5,
  limit: number = 10,
  enabled: boolean = true
): UseTrendDataReturn<AtAGlanceData> {
  return useFetch<AtAGlanceData>('/at-a-glance', {
    hours,
    anomaly_threshold: anomalyThreshold,
    limit,
  }, enabled);
}

// Heatmap data hook
export function useHeatmapData(
  days: number = 14,
  topN: number = 20,
  enabled: boolean = true
): UseTrendDataReturn<HeatmapData> {
  return useFetch<HeatmapData>('/heatmap', {
    days,
    top_n: topN,
  }, enabled);
}

// Bubble chart data hook
export function useBubbleChartData(
  days: number = 30,
  limit: number = 50,
  enabled: boolean = true
): UseTrendDataReturn<BubbleChartData> {
  return useFetch<BubbleChartData>('/bubble-chart', {
    days,
    limit,
  }, enabled);
}

// Network graph data hook
export function useNetworkGraphData(
  days: number = 30,
  minConnections: number = 2,
  topN: number = 40,
  enabled: boolean = true
): UseTrendDataReturn<NetworkGraphData> {
  return useFetch<NetworkGraphData>('/network', {
    days,
    min_connections: minConnections,
    top_n: topN,
  }, enabled);
}

// Animated timeline data hook
export function useAnimatedTimelineData(
  days: number = 30,
  topN: number = 15,
  enabled: boolean = true
): UseTrendDataReturn<AnimatedTimelineData> {
  return useFetch<AnimatedTimelineData>('/animated-timeline', {
    days,
    top_n: topN,
  }, enabled);
}
