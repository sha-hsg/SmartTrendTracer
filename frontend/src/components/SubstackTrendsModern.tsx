import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { cn } from "@/lib/utils"
import {
  TrendingUp,
  TrendingDown,
  Clock,
  Users,
  FileText,
  Hash,
  BarChart3,
  Activity,
  RefreshCw,
  Loader2,
  AlertCircle,
  Sparkles,
  Calendar,
  ArrowUp,
  ArrowDown,
  ArrowRight,
  Zap,
  Target,
  Flame,
  Link2,
  BookOpen,
  PenTool,
  Lightbulb,
  Rocket,
  MessageSquare,
  ChevronRight,
  Timer
} from 'lucide-react'

interface TrendData {
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

export default function SubstackTrendsModern() {
  const [trends, setTrends] = useState<TrendData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState('7')
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchTrends()
  }, [days])

  const fetchTrends = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`http://localhost:8000/api/substack/trends?days=${days}`)
      setTrends(response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchTrends()
  }

  const getProductivityIcon = (productivity: string) => {
    switch(productivity) {
      case 'very_high': return <Flame className="h-4 w-4 text-red-500" />
      case 'high': return <Zap className="h-4 w-4 text-orange-500" />
      case 'moderate': return <PenTool className="h-4 w-4 text-blue-500" />
      case 'low': return <Timer className="h-4 w-4 text-gray-500" />
      default: return <Activity className="h-4 w-4 text-gray-400" />
    }
  }

  const getProductivityColor = (productivity: string) => {
    switch(productivity) {
      case 'very_high': return 'bg-red-50 text-red-700 border-red-200'
      case 'high': return 'bg-orange-50 text-orange-700 border-orange-200'
      case 'moderate': return 'bg-blue-50 text-blue-700 border-blue-200'
      case 'low': return 'bg-gray-50 text-gray-700 border-gray-200'
      default: return 'bg-gray-50 text-gray-500 border-gray-200'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch(trend) {
      case 'rising': return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'falling': return <TrendingDown className="h-4 w-4 text-red-500" />
      default: return <ArrowRight className="h-4 w-4 text-gray-500" />
    }
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    })
  }

  if (loading || !trends) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading trend analysis...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <Alert className="bg-red-50 border-red-200">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            Failed to load trends: {error}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Newsletter Trend Analysis</h1>
            <p className="text-gray-600">
              Analyzing {trends.total_articles} articles from {formatDate(trends.date_range.start)} to {formatDate(trends.date_range.end)}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={days} onValueChange={setDays}>
              <SelectTrigger className="w-40">
                <Clock className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="3">Last 3 days</SelectItem>
                <SelectItem value="7">Last week</SelectItem>
                <SelectItem value="14">Last 2 weeks</SelectItem>
                <SelectItem value="30">Last month</SelectItem>
              </SelectContent>
            </Select>
            <Button 
              onClick={handleRefresh}
              disabled={refreshing}
              variant="outline"
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Articles</p>
                <p className="text-2xl font-bold">{trends.total_articles}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Authors</p>
                <p className="text-2xl font-bold">{trends.author_trends.total_authors}</p>
              </div>
              <Users className="h-8 w-8 text-green-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Unique Tags</p>
                <p className="text-2xl font-bold">{trends.tag_trends.unique_tags}</p>
              </div>
              <Hash className="h-8 w-8 text-purple-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Highlights</p>
                <p className="text-2xl font-bold">{trends.snippet_insights.total_snippets}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-orange-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="topics">Topics</TabsTrigger>
          <TabsTrigger value="authors">Authors</TabsTrigger>
          <TabsTrigger value="velocity">Velocity</TabsTrigger>
          <TabsTrigger value="clusters">Clusters</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Key Insights */}
            {trends.summary.key_insights.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-yellow-500" />
                    Key Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {trends.summary.key_insights.map((insight, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <ChevronRight className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{insight}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Emerging Themes */}
            {trends.emerging_themes.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Rocket className="h-5 w-5 text-purple-500" />
                    Emerging Themes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {trends.emerging_themes.slice(0, 5).map((theme, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                        <div className="flex items-center gap-2">
                          {theme.type === 'new' ? (
                            <Sparkles className="h-4 w-4 text-purple-500" />
                          ) : (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          )}
                          <span className="text-sm font-medium">{theme.theme}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={theme.type === 'new' ? 'secondary' : 'outline'}>
                            {theme.type === 'new' ? 'New' : 'Growing'}
                          </Badge>
                          <span className="text-xs text-gray-500">{theme.growth}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Hot Topics */}
          {trends.topic_trends.top_topics.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Flame className="h-5 w-5 text-red-500" />
                  Hot Topics
                </CardTitle>
                <CardDescription>Most discussed topics in newsletters</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {trends.topic_trends.top_topics.slice(0, 10).map((topic, idx) => {
                    const maxScore = trends.topic_trends.top_topics[0].score
                    const percentage = (topic.score / maxScore) * 100
                    
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{topic.term}</span>
                          <Badge variant="secondary" className="text-xs">
                            {topic.articles} articles
                          </Badge>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="topics" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Trending Up */}
            {trends.topic_trends.trending_up.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-500" />
                    Trending Up
                  </CardTitle>
                  <CardDescription>Topics gaining momentum</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {trends.topic_trends.trending_up.map((topic, idx) => (
                        <div key={idx} className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50">
                          <span className="font-medium">{topic.term}</span>
                          <div className="flex items-center gap-2">
                            <Badge className="bg-green-100 text-green-700 border-green-200">
                              +{topic.growth} articles
                            </Badge>
                            <ArrowUp className="h-4 w-4 text-green-500" />
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}

            {/* Tag Relationships */}
            {trends.tag_trends.tag_relationships.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Link2 className="h-5 w-5 text-blue-500" />
                    Related Tags
                  </CardTitle>
                  <CardDescription>Commonly co-occurring tags</CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-3">
                      {trends.tag_trends.tag_relationships.slice(0, 5).map((rel, idx) => (
                        <div key={idx} className="space-y-2">
                          <div className="font-medium text-sm">{rel.tag}</div>
                          <div className="flex flex-wrap gap-1">
                            {rel.related.map((r, ridx) => (
                              <Badge key={ridx} variant="outline" className="text-xs">
                                {r.tag}
                                <span className="ml-1 text-gray-400">({r.strength})</span>
                              </Badge>
                            ))}
                          </div>
                          {idx < trends.tag_trends.tag_relationships.length - 1 && (
                            <Separator className="mt-2" />
                          )}
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        <TabsContent value="authors" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Most Active Authors
              </CardTitle>
              <CardDescription>Author productivity and focus areas</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {trends.author_trends.most_active.map((author, idx) => (
                  <Card key={idx}>
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-semibold">{author.author}</h4>
                          <Badge 
                            variant="outline" 
                            className={cn("mt-1", getProductivityColor(author.productivity))}
                          >
                            {getProductivityIcon(author.productivity)}
                            <span className="ml-1">{author.productivity.replace('_', ' ')}</span>
                          </Badge>
                        </div>
                      </div>

                      <div className="grid grid-cols-2 gap-2 mb-3 text-sm">
                        <div>
                          <span className="text-gray-500">Articles:</span>
                          <span className="ml-2 font-medium">{author.articles}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Avg words:</span>
                          <span className="ml-2 font-medium">{author.avg_words.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Reading time:</span>
                          <span className="ml-2 font-medium">{author.avg_reading_time.toFixed(1)} min</span>
                        </div>
                        <div>
                          <span className="text-gray-500">Snippets:</span>
                          <span className="ml-2 font-medium">{author.total_snippets}</span>
                        </div>
                      </div>

                      {author.topics.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                          {author.topics.map((topic, tidx) => (
                            <Badge key={tidx} variant="secondary" className="text-xs">
                              {topic}
                            </Badge>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="velocity" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Topic Velocity Analysis
              </CardTitle>
              <CardDescription>Rate of change in topic discussion</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {trends.velocity_trends.map((item, idx) => (
                  <div 
                    key={idx} 
                    className={cn(
                      "flex items-center justify-between p-3 rounded-lg border",
                      item.trend === 'rising' && "bg-green-50 border-green-200",
                      item.trend === 'falling' && "bg-red-50 border-red-200",
                      item.trend === 'stable' && "bg-gray-50 border-gray-200"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      {getTrendIcon(item.trend)}
                      <span className="font-medium">{item.topic}</span>
                    </div>
                    <div className="flex items-center gap-3 text-sm">
                      <span className="text-gray-600">
                        {item.first_period} → {item.second_period}
                      </span>
                      <Badge 
                        variant={item.velocity > 0 ? "default" : "secondary"}
                        className={cn(
                          item.velocity > 0 && "bg-green-100 text-green-700",
                          item.velocity < 0 && "bg-red-100 text-red-700"
                        )}
                      >
                        {item.velocity > 0 ? '+' : ''}{(item.velocity * 100).toFixed(0)}%
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="clusters" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Content Clusters
              </CardTitle>
              <CardDescription>Articles grouped by similar themes</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {trends.content_clusters.map((cluster, idx) => (
                  <Card key={idx}>
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">
                          Cluster {cluster.cluster_id + 1}: {cluster.theme}
                        </CardTitle>
                        <Badge variant="secondary">{cluster.size} articles</Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div>
                          <p className="text-xs text-gray-500 mb-1">Keywords</p>
                          <div className="flex flex-wrap gap-1">
                            {cluster.keywords.map((keyword, kidx) => (
                              <Badge key={kidx} variant="outline" className="text-xs">
                                {keyword}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        
                        {cluster.articles.length > 0 && (
                          <div>
                            <p className="text-xs text-gray-500 mb-1">Sample Articles</p>
                            <div className="space-y-1">
                              {cluster.articles.slice(0, 2).map((article, aidx) => (
                                <div key={aidx} className="text-xs">
                                  <span className="font-medium">{article.title}</span>
                                  <span className="text-gray-500 ml-1">by {article.author}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Important Snippets */}
      {trends.snippet_insights.important_highlights.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Important Highlights
            </CardTitle>
            <CardDescription>Key insights from article snippets</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {trends.snippet_insights.important_highlights.slice(0, 5).map((snippet, idx) => (
                  <Card key={idx}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline">{snippet.category}</Badge>
                        <span className="text-xs text-gray-500">{snippet.article}</span>
                      </div>
                      <blockquote className="border-l-4 border-gray-200 pl-4 italic text-gray-700">
                        "{snippet.text}"
                      </blockquote>
                      {snippet.annotation && (
                        <div className="mt-2 text-sm text-gray-600 flex items-start gap-2">
                          <BookOpen className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          <span>{snippet.annotation}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  )
}