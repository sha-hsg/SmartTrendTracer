export interface Topic {
  id: string
  name: string
  slug?: string
  count: number
  content_types?: string[]
  entity_type?: string
  color?: string
}

export interface FrequencyDataPoint {
  date: string
  count: number
}

export interface FrequencySeries {
  concept_id: string
  concept_name: string
  color: string
  data: FrequencyDataPoint[]
  total: number
}

export interface FrequencyResponse {
  series: FrequencySeries[]
  time_range: { start: string; end: string }
  granularity: string
  source_types: string[]
}

export interface CorrelationResponse {
  topics: Topic[]
  correlations: {
    topic1_id: string
    topic1_name: string
    topic2_id: string
    topic2_name: string
    co_occurrence: number
    correlation: number
    topic1_count: number
    topic2_count: number
  }[]
  source_types: string[]
  time_range: { start: string; end: string }
}

export const DATE_PRESETS = [
  { label: 'Last 30 Days', days: 30 },
  { label: 'Last 90 Days', days: 90 },
  { label: 'Last 6 Months', days: 180 },
  { label: 'Last Year', days: 365 },
  { label: 'All Time', days: 3650 }
]
