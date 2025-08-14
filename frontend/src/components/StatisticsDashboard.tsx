import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  Twitter,
  FileText,
  Tags,
  Users,
  TrendingUp,
  Database,
  Calendar,
  Clock,
  Activity,
  BarChart3,
  PieChart,
  Hash,
  Newspaper,
  BookOpen,
  MessageSquare,
  Eye,
  ThumbsUp,
  Share2,
  GitBranch,
  Layers,
  Zap,
  AlertCircle,
  CheckCircle,
  XCircle,
  Info,
  Search,
  Image
} from 'lucide-react'
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart as RePieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area,
  AreaChart
} from 'recharts'

interface SystemStats {
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
    most_used: Array<{ tag: string; count: number }>
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
}

const COLORS = ['#3b82f6', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#6366f1', '#14b8a6']

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
      const response = await axios.get('/api/statistics/overview')
      
      // Check if there's an error in the response
      if (response.data.error) {
        console.error('Statistics API error:', response.data.error)
        setError(`Error: ${response.data.error}`)
      }
      
      setStats(response.data)
    } catch (err: any) {
      console.error('Error fetching statistics:', err)
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to load statistics'
      setError(errorMessage)
      
      // Don't use mock data - show real error
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

  // Error display for debugging
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

      {/* Main Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Tweets</CardTitle>
            <Twitter className="h-4 w-4 text-blue-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.tweets.total.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              +{stats.tweets.today} today
            </p>
            <Progress value={85} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Articles</CardTitle>
            <FileText className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.articles.total}</div>
            <p className="text-xs text-muted-foreground">
              +{stats.articles.this_week} this week
            </p>
            <Progress value={65} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Unique Tags</CardTitle>
            <Tags className="h-4 w-4 text-purple-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.tags.unique}</div>
            <p className="text-xs text-muted-foreground">
              {stats.tags.organized} organized
            </p>
            <Progress value={(stats.tags.organized / stats.tags.unique) * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">RAG Index</CardTitle>
            <Database className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.system.index_status.rag_documents.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              {stats.system.index_status.is_ready ? (
                <span className="flex items-center gap-1">
                  <CheckCircle className="h-3 w-3 text-green-500" />
                  Ready
                </span>
              ) : (
                <span className="flex items-center gap-1">
                  <AlertCircle className="h-3 w-3 text-yellow-500" />
                  Building
                </span>
              )}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Tabbed Content */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="content">Content</TabsTrigger>
          <TabsTrigger value="authors">Authors</TabsTrigger>
          <TabsTrigger value="trends">Trends</TabsTrigger>
          <TabsTrigger value="system">System</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Tweet Timeline */}
            <Card>
              <CardHeader>
                <CardTitle>Tweet Activity (7 Days)</CardTitle>
                <CardDescription>Daily tweet collection statistics</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={stats.timeline.tweets_per_day}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Area type="monotone" dataKey="count" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.6} />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Tag Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Top Tags</CardTitle>
                <CardDescription>Most frequently used tags</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={stats.tags.most_used}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="tag" angle={-45} textAnchor="end" height={100} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#8b5cf6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Tweets with Media</p>
                    <p className="text-xl font-semibold">{stats.tweets.with_media}</p>
                  </div>
                  <Image className="h-8 w-8 text-blue-500 opacity-50" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Articles with Summaries</p>
                    <p className="text-xl font-semibold">{stats.articles.with_summaries}</p>
                  </div>
                  <BookOpen className="h-8 w-8 text-green-500 opacity-50" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Total Snippets</p>
                    <p className="text-xl font-semibold">{stats.articles.with_snippets}</p>
                  </div>
                  <MessageSquare className="h-8 w-8 text-purple-500 opacity-50" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">Database Size</p>
                    <p className="text-xl font-semibold">{stats.system.database_size}</p>
                  </div>
                  <Database className="h-8 w-8 text-orange-500 opacity-50" />
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="content" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Tweet Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Total Tweets</span>
                    <span className="font-medium">{stats.tweets.total.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Today</span>
                    <span className="font-medium text-green-600">+{stats.tweets.today}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">This Week</span>
                    <span className="font-medium">{stats.tweets.this_week}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">This Month</span>
                    <span className="font-medium">{stats.tweets.this_month}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Retweets</span>
                    <span className="font-medium">{stats.tweets.retweets}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Quote Tweets</span>
                    <span className="font-medium">{stats.tweets.quotes}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">With Tags</span>
                    <span className="font-medium">{stats.tweets.with_tags}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">With Media</span>
                    <span className="font-medium">{stats.tweets.with_media}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Article Statistics</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Total Articles</span>
                    <span className="font-medium">{stats.articles.total}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">This Week</span>
                    <span className="font-medium text-green-600">+{stats.articles.this_week}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">This Month</span>
                    <span className="font-medium">{stats.articles.this_month}</span>
                  </div>
                  <Separator />
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">With Summaries</span>
                    <span className="font-medium">{stats.articles.with_summaries}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Total Snippets</span>
                    <span className="font-medium">{stats.articles.with_snippets}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Avg Reading Time</span>
                    <span className="font-medium">{stats.articles.avg_reading_time} min</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Total Words</span>
                    <span className="font-medium">{stats.articles.total_word_count.toLocaleString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="authors" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Top Twitter Authors</CardTitle>
                <CardDescription>Most active Twitter accounts</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  <div className="space-y-4">
                    {stats.authors.twitter.map((author, i) => (
                      <div key={author.username} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-600 font-semibold text-sm">
                            {i + 1}
                          </div>
                          <div>
                            <p className="font-medium">{author.username}</p>
                            <p className="text-sm text-muted-foreground">Last: {author.latest_tweet}</p>
                          </div>
                        </div>
                        <Badge variant="secondary">{author.tweet_count} tweets</Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Newsletter Authors</CardTitle>
                <CardDescription>Most prolific article authors</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  <div className="space-y-4">
                    {stats.authors.articles.map((author, i) => (
                      <div key={author.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-600 font-semibold text-sm">
                            {i + 1}
                          </div>
                          <div>
                            <p className="font-medium">{author.name}</p>
                            <p className="text-sm text-muted-foreground">Last: {author.latest_article}</p>
                          </div>
                        </div>
                        <Badge variant="secondary">{author.article_count} articles</Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trends" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Hot Topics</CardTitle>
                <CardDescription>Currently trending discussions</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats.trends.hot_topics.map((topic) => (
                    <div key={topic.topic} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {topic.trend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
                        {topic.trend === 'down' && <TrendingUp className="h-4 w-4 text-red-500 rotate-180" />}
                        {topic.trend === 'stable' && <Activity className="h-4 w-4 text-gray-500" />}
                        <span className="font-medium">{topic.topic}</span>
                      </div>
                      <Badge variant={topic.trend === 'up' ? 'default' : topic.trend === 'down' ? 'destructive' : 'secondary'}>
                        {topic.mentions} mentions
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Emerging Tags</CardTitle>
                <CardDescription>Fastest growing tags</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {stats.trends.emerging_tags.map((tag) => (
                    <div key={tag.tag} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{tag.tag}</span>
                        <span className="text-sm text-green-600">+{tag.growth_rate}%</span>
                      </div>
                      <Progress value={Math.min(tag.growth_rate, 100)} className="h-2" />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Recently Added Tags</CardTitle>
              <CardDescription>Newest tags in the system</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {stats.tags.recently_added.map((tag) => (
                  <Badge key={tag.tag} variant="outline" className="py-1">
                    <Hash className="h-3 w-3 mr-1" />
                    {tag.tag}
                    <span className="ml-2 text-xs text-muted-foreground">{tag.date}</span>
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="system" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>System Health</CardTitle>
                <CardDescription>Overall system status</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="h-4 w-4" />
                      <span>Database</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <span className="text-sm">{stats.system.database_size}</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Search className="h-4 w-4" />
                      <span>RAG Index</span>
                    </div>
                    <div className="flex items-center gap-2">
                      {stats.system.index_status.is_ready ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                      <span className="text-sm">{stats.system.index_status.rag_documents} docs</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Tags className="h-4 w-4" />
                      <span>Tag Organization</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Info className="h-4 w-4 text-blue-500" />
                      <span className="text-sm">
                        {((stats.tags.organized / stats.tags.unique) * 100).toFixed(1)}% organized
                      </span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Collection Status</CardTitle>
                <CardDescription>Data collection schedule</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">Last Tweet Collection</span>
                      <Badge variant="outline">
                        {new Date(stats.system.collection_status.last_tweet_collection).toLocaleTimeString()}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">Last Article Collection</span>
                      <Badge variant="outline">
                        {new Date(stats.system.collection_status.last_article_collection).toLocaleTimeString()}
                      </Badge>
                    </div>
                  </div>
                  <Separator />
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">Next Scheduled</span>
                      <Badge>
                        {new Date(stats.system.collection_status.next_scheduled).toLocaleTimeString()}
                      </Badge>
                    </div>
                  </div>
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm text-muted-foreground">Index Last Updated</span>
                      <Badge variant="outline">
                        {new Date(stats.system.index_status.last_updated).toLocaleDateString()}
                      </Badge>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}