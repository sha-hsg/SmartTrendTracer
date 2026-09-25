export interface SystemStats {
  tweets: {
    total: number
    today: number
    this_week: number
    this_month: number
    with_media: number
    with_tags: number
    retweets: number
    quotes: number
  }
  articles: {
    total: number
    this_week: number
    this_month: number
    with_summaries: number
    with_snippets: number
    avg_reading_time: number
    total_word_count: number
  }
  tags: {
    total: number
    unique: number
    organized: number
    unorganized: number
    most_used: Array<{ tag: string; count: number; sources?: string[] }>
    recently_added: Array<{ tag: string; date: string }>
  }
  authors: {
    twitter: Array<{ username: string; tweet_count: number; latest_tweet: string }>
    articles: Array<{ name: string; article_count: number; latest_article: string }>
  }
  system: {
    database_size: string
    index_status: {
      rag_documents: number
      last_updated: string
      is_ready: boolean
    }
    collection_status: {
      last_tweet_collection: string
      last_article_collection: string
      next_scheduled: string
    }
  }
  trends: {
    hot_topics: Array<{ topic: string; mentions: number; trend: 'up' | 'down' | 'stable' }>
    emerging_tags: Array<{ tag: string; growth_rate: number }>
  }
  timeline: {
    tweets_per_day: Array<{ date: string; count: number }>
    articles_per_week: Array<{ week: string; count: number }>
  }
  papers?: {
    total: number
    this_week: number
    this_month: number
    with_tags: number
    tag_coverage: number
  }
  cross_source?: {
    content_coverage: {
      tags_in_all_sources: number
      tags_in_tweets_articles: number
      tags_in_tweets_papers: number
      tags_in_articles_papers: number
      tweets_only_tags: number
      articles_only_tags: number
      papers_only_tags: number
    }
    tag_distribution: {
      tweets: { unique_tags: number; total_applications: number; avg_tags_per_item: number }
      articles: { unique_tags: number; total_applications: number; avg_tags_per_item: number }
      papers: { unique_tags: number; total_applications: number; avg_tags_per_item: number }
    }
    universal_tags: string[]
  }
  llm_usage?: {
    last_used: {
      model: string
      task_type: string
      timestamp: string
      status: string
    } | null
    recent_calls: Array<{
      model: string
      task_type: string
      timestamp: string
      status: string
      duration_ms: number
      tokens_used: number
    }>
    model_distribution: Array<{ _id: string; count: number }>
    task_distribution: Array<{ _id: string; count: number }>
    usage_last_24h: number
    total_calls: number
    success_rate: number
    token_usage: {
      total: number
      average_per_call: number
      total_calls: number
    }
    performance: Array<{ _id: string; avg_duration: number }>
  }
}
