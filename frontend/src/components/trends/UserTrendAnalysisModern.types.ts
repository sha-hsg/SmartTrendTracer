export interface UserData {
  username: string
  tweet_count: number
  unique_concepts: number
  total_likes: number
  total_retweets: number
  engagement_rate: number
  top_concepts: Array<{
    name: string
    count: number
  }>
}

export interface CrossUserConcept {
  concept: string
  user_count: number
  users: string[]
}

export interface TimelinePoint {
  time: string
  users: Record<string, number>
}

export interface UserTrendsResponse {
  period_hours: number
  start_date: string
  end_date: string
  users: UserData[]
  top_concepts_by_user: Record<string, Array<{ name: string; count: number }>>
  activity_by_user: Record<string, {
    total_tweets: number
    engagement_rate: number
    unique_concepts: number
  }>
  cross_user_concepts: CrossUserConcept[]
  user_statistics: {
    most_active: { username: string; tweet_count: number } | null
    most_diverse_concepts: { username: string; unique_concepts: number } | null
    highest_engagement: { username: string; engagement_rate: number } | null
  }
  timeline: TimelinePoint[]
}

export interface UserDetails {
  username: string
  period_days: number
  start_date: string
  end_date: string
  tweet_count: number
  concepts_used: string[]
  top_concepts: Array<{ concept: string; count: number }>
  posting_patterns: {
    by_hour: Array<{ hour: number; count: number }>
    by_day: Array<{ day: string; count: number }>
    peak_times: string[]
  }
  engagement_metrics: {
    avg_retweets: number
    avg_likes: number
    total_reach: number
  }
  concept_evolution: Array<{ date: string; concepts: Record<string, number> }>
  similar_users: string[]
}
