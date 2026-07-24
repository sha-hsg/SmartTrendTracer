/**
 * TypeScript interfaces for Trend Detection Dashboard
 */

// Trend classification types
export type TrendStatus = 'hot' | 'rising' | 'stable' | 'declining';
export type ContentType = 'tweet' | 'article' | 'paper' | 'reddit';

// Core concept trend data
export interface ConceptTrend {
  concept_id: string;
  display_name: string;
  slug: string;
  count: number;
  previous_count: number;
  velocity: number;  // Percentage change
  trend: TrendStatus;
  sparkline: number[];  // Last 7 days counts
  entity_type?: string;
  color?: string;
  content_breakdown?: {
    tweets: number;
    articles: number;
    papers: number;
    reddit: number;
  };
}

// Anomaly detection
export interface AnomalyAlert {
  concept_id: string;
  display_name: string;
  spike_magnitude: number;  // Absolute increase
  z_score: number;  // Standard deviations from mean
  timestamp: string;
  baseline_avg: number;
  current_value: number;
  possible_cause?: string;  // LLM-generated explanation
}

// At-a-Glance response
export interface AtAGlanceData {
  hot_topics: ConceptTrend[];
  declining: ConceptTrend[];
  stable: ConceptTrend[];
  anomalies: AnomalyAlert[];
  time_range: {
    start: string;
    end: string;
    hours: number;
  };
  statistics: {
    total_content: number;
    unique_concepts: number;
    avg_velocity: number;
  };
}

// Heatmap data structure
export interface HeatmapData {
  concepts: string[];  // Display names
  concept_ids: string[];
  dates: string[];  // YYYY-MM-DD format
  matrix: number[][];  // [concept_idx][date_idx] = count
  max_value: number;
  min_value: number;
}

// Bubble chart data point
export interface BubbleDataPoint {
  concept_id: string;
  display_name: string;
  x: number;  // Days since first occurrence
  y: number;  // Velocity (% change)
  z: number;  // Volume (total count)
  entity_type: string;
  color: string;
  first_seen: string;
  last_seen: string;
}

export interface BubbleChartData {
  data: BubbleDataPoint[];
  x_range: { min: number; max: number };
  y_range: { min: number; max: number };
  z_range: { min: number; max: number };
}

// Co-occurrence / Correlation data
export interface CooccurrencePair {
  concept_a: string;
  concept_a_id: string;
  concept_b: string;
  concept_b_id: string;
  count: number;
  strength: number;  // 0-1 normalized (Jaccard similarity)
}

export interface CooccurrenceData {
  concepts: string[];  // Display names for matrix axes
  concept_ids: string[];
  matrix: number[][];  // Symmetric matrix of co-occurrence counts
  pairs: CooccurrencePair[];  // Top pairs sorted by strength
  total_documents: number;
}

// Network graph data
export interface NetworkNode {
  id: string;
  name: string;
  val: number;  // Node size (activity level)
  color: string;
  entity_type?: string;
  activity: number;  // Recent activity count
  cluster?: number;
}

export interface NetworkLink {
  source: string;
  target: string;
  value: number;  // Edge thickness (co-occurrence count)
  strength: number;  // 0-1 normalized
}

export interface NetworkGraphData {
  nodes: NetworkNode[];
  links: NetworkLink[];
  clusters: {
    id: number;
    name: string;
    nodes: string[];
    color: string;
  }[];
  statistics: {
    total_nodes: number;
    total_edges: number;
    avg_connections: number;
    density: number;
  };
}

// Animated timeline data
export interface TimelineRanking {
  concept_id: string;
  display_name: string;
  value: number;
  rank: number;
  color: string;
  isNew?: boolean;      // Newly entered in this frame
  isExiting?: boolean;  // Will exit in the next frame
}

export interface TimelineFrame {
  date: string;
  rankings: TimelineRanking[];
}

// Concept lifecycle tracking
export interface ConceptLifecycle {
  concept_id: string;
  display_name: string;
  firstFrame: number;
  lastFrame: number;
  firstDate: string;
  lastDate: string;
  totalFrames: number;
  color: string;
}

export interface AnimatedTimelineData {
  frames: TimelineFrame[];
  concepts: {
    concept_id: string;
    display_name: string;
    color: string;
    total_value: number;
  }[];
  date_range: {
    start: string;
    end: string;
  };
}

// Filter/query parameters
export interface TrendQueryParams {
  hours?: number;  // Time window in hours
  days?: number;  // Time window in days
  anomaly_threshold?: number;  // Z-score threshold for anomalies
  top_n?: number;  // Limit number of results
  min_count?: number;  // Minimum activity count
  content_types?: ContentType[];
  concept_ids?: string[];
}

// Dashboard state
export interface TrendDashboardState {
  activeTab: 'overview' | 'heatmap' | 'bubble' | 'correlation' | 'network' | 'timeline';
  timeRange: number;  // hours
  contentTypes: ContentType[];
  loading: boolean;
  error: string | null;
}

// API Response wrappers
export interface TrendAPIResponse<T> {
  data: T;
  timestamp: string;
  cache_hit?: boolean;
}
