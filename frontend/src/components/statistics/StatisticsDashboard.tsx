import { useState, useEffect } from 'react'
import axios from 'axios'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Activity } from 'lucide-react'
import { StatsOverviewCards } from './StatsOverviewCards'
import { StatsCharts } from './StatsCharts'

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

export default function StatisticsDashboard() {
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchStatistics()
  }, [])

  const fetchStatistics = async () => {
    try {
      setLoading(true)
      setError(null)

      const [summaryRes, contentRes, authorsRes, trendsRes, crossRes, llmRes] = await Promise.all([
        axios.get('/api/system/statistics/summary'),
        axios.get('/api/system/statistics/content'),
        axios.get('/api/system/statistics/authors'),
        axios.get('/api/system/statistics/trends'),
        axios.get('/api/system/statistics/cross-source'),
        axios.get('/api/system/statistics/llm')
      ])

      const summary = summaryRes.data
      const content = contentRes.data
      const authors = authorsRes.data
      const trends = trendsRes.data
      const crossSource = crossRes.data

      const transformedStats: SystemStats = {
        tweets: {
          total: content.tweets.total || 0,
          today: content.tweets.today || 0,
          this_week: content.tweets.this_week || 0,
          this_month: content.tweets.this_month || 0,
          with_media: content.tweets.with_media || 0,
          with_tags: content.tweets.with_tags || 0,
          retweets: content.tweets.retweets || 0,
          quotes: content.tweets.quotes || 0
        },
        articles: {
          total: content.articles.total || 0,
          this_week: content.articles.this_week || 0,
          this_month: content.articles.this_month || 0,
          with_summaries: content.articles.with_summaries || 0,
          with_snippets: content.articles.with_snippets || 0,
          avg_reading_time: content.articles.avg_reading_time || 0,
          total_word_count: content.articles.total_word_count || 0
        },
        papers: {
          total: content.papers.total || 0,
          this_week: content.papers.this_week || 0,
          this_month: content.papers.this_month || 0,
          with_tags: content.papers.with_tags || 0,
          tag_coverage: content.papers.tag_coverage || 0
        },
        tags: {
          total: summary.tags.total_concepts || 0,
          unique: summary.tags.unique_tags || 0,
          organized: summary.tags.organized || 0,
          unorganized: summary.tags.unorganized || 0,
          most_used: summary.tags.most_used || [],
          recently_added: summary.tags.recently_added || []
        },
        authors: {
          twitter: authors.twitter_authors || [],
          articles: authors.article_authors || []
        },
        system: {
          database_size: summary.system.database_size || 'N/A',
          index_status: {
            rag_documents: summary.rag.indexed_documents || 0,
            last_updated: summary.rag.last_rebuild || 'N/A',
            is_ready: summary.rag.status === 'ready'
          },
          collection_status: {
            last_tweet_collection: summary.system.collection_status?.last_tweet_collection || 'N/A',
            last_article_collection: summary.system.collection_status?.last_article_collection || 'N/A',
            next_scheduled: 'Manual collection only'
          }
        },
        trends: {
          hot_topics: trends.hot_topics || [],
          emerging_tags: trends.emerging_tags || []
        },
        timeline: {
          tweets_per_day: trends.timeline?.tweets_per_day || [],
          articles_per_week: trends.timeline?.articles_per_week || []
        },
        cross_source: {
          content_coverage: crossSource.content_coverage || {},
          tag_distribution: crossSource.tag_distribution || {},
          universal_tags: crossSource.universal_tags || []
        },
        llm_usage: llmRes.data
      }

      setStats(transformedStats)
    } catch (err: any) {
      console.error('Error fetching statistics:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load statistics'
      setError(errorMessage)

      setStats(null)
    } finally {
      setLoading(false)
    }
  }

  const refreshStats = async () => {
    setRefreshing(true)
    await fetchStatistics()
    setRefreshing(false)
  }

  if (error && !stats) {
    return (
      <div className="container mx-auto p-6">
        <Card className="border-red-200">
          <CardHeader>
            <CardTitle className="text-red-600">Error Loading Statistics</CardTitle>
            <CardDescription>{error}</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground mb-4">
              Please ensure the backend server is running and the database is accessible.
            </p>
            <Button onClick={fetchStatistics} variant="outline">
              <Activity className="mr-2 h-4 w-4" />
              Retry
            </Button>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="text-muted-foreground">Loading statistics...</p>
        </div>
      </div>
    )
  }


  if (!stats) return null

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">System Statistics</h1>
          <p className="text-muted-foreground">
            Comprehensive overview of SmartTrendTracer metrics
          </p>
        </div>
        <Button
          onClick={refreshStats}
          disabled={refreshing}
          variant="default"
        >
          <Activity className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh'}
        </Button>
      </div>

      <StatsOverviewCards stats={stats} />

      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="cross-source">Cross-Source</TabsTrigger>
          <TabsTrigger value="authors">Authors</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="llm">LLM Usage</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        {['overview', 'content', 'cross-source', 'authors', 'trends', 'llm', 'system'].map((tab) => (
          <TabsContent key={tab} value={tab} className="space-y-4">
            <StatsCharts stats={stats} tabValue={tab} />
          </TabsContent>
        ))}
      </Tabs>
    </div>
  )
}
