export interface TrendData {
  period: string
  total_articles: number
  date_range: {
    start: string
    end: string
  }
  topic_trends: {
    top_topics: Array<{
      term: string
      score: number
      articles: number
    }>
    trending_up: Array<{
      term: string
      growth: number
      current_count: number
    }>
  }
  author_trends: {
    most_active: Array<{
      author: string
      articles: number
      avg_words: number
      avg_reading_time: number
      total_snippets: number
      topics: string[]
      productivity: string
    }>
    total_authors: number
    avg_articles_per_author: number
  }
  tag_trends: {
    top_tags: Array<{
      tag: string
      count: number
    }>
    tag_relationships: Array<{
      tag: string
      related: Array<{
        tag: string
        strength: number
      }>
    }>
    unique_tags: number
  }
  snippet_insights: {
    categories: Record<string, number>
    important_highlights: Array<{
      text: string
      category: string
      article: string
      annotation: string | null
    }>
    total_snippets: number
  }
  velocity_trends: Array<{
    topic: string
    velocity: number
    first_period: number
    second_period: number
    trend: 'rising' | 'falling' | 'stable'
  }>
  content_clusters: Array<{
    cluster_id: number
    size: number
    theme: string
    keywords: string[]
    articles: Array<{
      title: string
      author: string
    }>
  }>
  emerging_themes: Array<{
    theme: string
    type: 'new' | 'growing'
    occurrences: number
    growth: string
  }>
  summary: {
    key_insights: string[]
    recommendations: string[]
  }
}
