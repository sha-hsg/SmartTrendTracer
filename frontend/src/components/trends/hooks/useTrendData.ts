/**
 * Custom hook for fetching trend data from the API
 */

import { useState, useEffect, useCallback } from 'react';
import http from '@/services/http'
import {
  AtAGlanceData,
  HeatmapData,
  BubbleChartData,
  CooccurrenceData,
  NetworkGraphData,
  AnimatedTimelineData,
  TrendQueryParams,
  ContentType,
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

  useEffect(() => {
    if (autoFetch) {
      fetch();
    }
  }, [fetch, autoFetch]);

  return { data, loading, error, refetch: fetch };
}

// At-a-Glance data hook
export function useAtAGlanceData(
  hours: number = 48,
  anomalyThreshold: number = 2.5,
  limit: number = 10
): UseTrendDataReturn<AtAGlanceData> {
  return useFetch<AtAGlanceData>('/at-a-glance', {
    hours,
    anomaly_threshold: anomalyThreshold,
    limit,
  });
}

// Heatmap data hook
export function useHeatmapData(
  days: number = 14,
  topN: number = 20
): UseTrendDataReturn<HeatmapData> {
  return useFetch<HeatmapData>('/heatmap', {
    days,
    top_n: topN,
  });
}

// Bubble chart data hook
export function useBubbleChartData(
  days: number = 30,
  limit: number = 50
): UseTrendDataReturn<BubbleChartData> {
  return useFetch<BubbleChartData>('/bubble-chart', {
    days,
    limit,
  });
}

// Co-occurrence data hook
export function useCooccurrenceData(
  days: number = 30,
  topN: number = 25,
  minCooccurrence: number = 2
): UseTrendDataReturn<CooccurrenceData> {
  return useFetch<CooccurrenceData>('/cooccurrence', {
    days,
    top_n: topN,
    min_cooccurrence: minCooccurrence,
  });
}

// Network graph data hook
export function useNetworkGraphData(
  days: number = 30,
  minConnections: number = 2,
  topN: number = 40
): UseTrendDataReturn<NetworkGraphData> {
  return useFetch<NetworkGraphData>('/network', {
    days,
    min_connections: minConnections,
    top_n: topN,
  });
}

// Animated timeline data hook
export function useAnimatedTimelineData(
  days: number = 30,
  topN: number = 15
): UseTrendDataReturn<AnimatedTimelineData> {
  return useFetch<AnimatedTimelineData>('/animated-timeline', {
    days,
    top_n: topN,
  });
}

// Combined dashboard data hook
export function useTrendDashboard(params: TrendQueryParams) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const atAGlance = useAtAGlanceData(params.hours || 48, params.anomaly_threshold || 2.5, params.top_n || 10);
  const heatmap = useHeatmapData(params.days || 14, params.top_n || 20);
  const bubbleChart = useBubbleChartData(params.days || 30, params.top_n || 50);
  const cooccurrence = useCooccurrenceData(params.days || 30, params.top_n || 25, 2);
  const network = useNetworkGraphData(params.days || 30, 2, params.top_n || 40);
  const timeline = useAnimatedTimelineData(params.days || 30, params.top_n || 15);

  useEffect(() => {
    const isLoading = atAGlance.loading || heatmap.loading || bubbleChart.loading ||
                      cooccurrence.loading || network.loading || timeline.loading;
    setLoading(isLoading);

    const errors = [atAGlance.error, heatmap.error, bubbleChart.error,
                   cooccurrence.error, network.error, timeline.error].filter(Boolean);
    setError(errors.length > 0 ? errors[0] : null);
  }, [
    atAGlance.loading, heatmap.loading, bubbleChart.loading,
    cooccurrence.loading, network.loading, timeline.loading,
    atAGlance.error, heatmap.error, bubbleChart.error,
    cooccurrence.error, network.error, timeline.error
  ]);

  const refetchAll = useCallback(async () => {
    await Promise.all([
      atAGlance.refetch(),
      heatmap.refetch(),
      bubbleChart.refetch(),
      cooccurrence.refetch(),
      network.refetch(),
      timeline.refetch(),
    ]);
  }, [atAGlance, heatmap, bubbleChart, cooccurrence, network, timeline]);

  return {
    atAGlance,
    heatmap,
    bubbleChart,
    cooccurrence,
    network,
    timeline,
    loading,
    error,
    refetchAll,
  };
}

export default useTrendDashboard;
