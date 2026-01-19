import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions
} from 'chart.js'
import { Bar, Radar } from 'react-chartjs-2'
import {
  TrendingUp,
  TrendingDown,
  Clock,
  RefreshCw,
  Loader2,
  ArrowRight,
  Target,
  Link2,
  GitBranch,
  Twitter,
  FileText,
  Layers,
  Shuffle,
  CircleDot
} from 'lucide-react'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  RadialLinearScale,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface TagTrend {
  tag: string
  count: number
}

interface TagVelocity {
  tag: string
  total_count: number
  velocity: number
  trend: string
  first_half: number
  second_half: number
}

interface Cluster {
  cluster_id: number
  size: number
  theme: string
  keywords: string[]
  top_tags: { tag: string; count: number }[]
}

interface TrendData {
  top_tags?: TagTrend[]
  tag_velocities?: TagVelocity[]
  rising_tags?: TagVelocity[]
  falling_tags?: TagVelocity[]
  tag_relationships?: { tags: string[]; count: number }[]
}

interface ClusterData {
  clusters?: Cluster[]
  n_clusters: number
  total_tweets?: number
  total_articles?: number
  quality_rating: string
  silhouette_score: number
}

interface ComparisonData {
  summary?: {
    common_tag_count: number
    overlap_percentage: number
  }
  velocity_comparison?: Array<{
    tag: string
    tweet_velocity: number
    article_velocity: number
    tweet_trend: string
    article_trend: string
    alignment: string
  }>
  tweet_exclusive_tags?: string[]
  article_exclusive_tags?: string[]
}

export default function UnifiedTrendsModern() {
  const [contentType, setContentType] = useState<'tweets' | 'articles' | 'comparison'>('tweets')
  const [viewType, setViewType] = useState<'trends' | 'clusters'>('trends')
  const [days, setDays] = useState('7')
  const [tweetTrends, setTweetTrends] = useState<TrendData | null>(null)
  const [articleTrends, setArticleTrends] = useState<TrendData | null>(null)
  const [tweetClusters, setTweetClusters] = useState<ClusterData | null>(null)
  const [articleClusters, setArticleClusters] = useState<ClusterData | null>(null)
  const [comparison, setComparison] = useState<ComparisonData | null>(null)
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchData()
  }, [contentType, viewType, days])

  const fetchData = async () => {
    setLoading(true)
    try {
      if (viewType === 'trends') {
        if (contentType === 'tweets') {
          const response = await axios.get(`http://localhost:8000/api/unified/tweets/tags?days=${days}`)
          setTweetTrends(response.data)
        } else if (contentType === 'articles') {
          const response = await axios.get(`http://localhost:8000/api/unified/articles/tags?days=${days}`)
          setArticleTrends(response.data)
        } else {
          const response = await axios.get(`http://localhost:8000/api/unified/comparison?days=${days}`)
          setComparison(response.data)
        }
      } else {
        if (contentType === 'tweets') {
          const response = await axios.get(`http://localhost:8000/api/unified/tweets/clusters?days=${days}`)
          setTweetClusters(response.data)
        } else if (contentType === 'articles') {
          const response = await axios.get(`http://localhost:8000/api/unified/articles/clusters?days=${days}`)
          setArticleClusters(response.data)
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchData()
  }

  const getTrendIcon = (trend: string) => {
    switch(trend) {
      case 'rising': return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'falling': return <TrendingDown className="h-4 w-4 text-red-500" />
      default: return <ArrowRight className="h-4 w-4 text-gray-500" />
    }
  }

  const getAlignmentColor = (alignment: string) => {
    switch(alignment) {
      case 'aligned': return 'bg-green-100 text-green-700 border-green-200'
      case 'opposite': return 'bg-red-100 text-red-700 border-red-200'
      default: return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  const renderTrendCharts = (trends: TrendData | null, type: string) => {
    if (!trends) return null

    const barData = {
      labels: trends.top_tags?.slice(0, 10).map(t => t.tag) || [],
      datasets: [
        {
          label: `${type} Tag Frequency`,
          data: trends.top_tags?.slice(0, 10).map(t => t.count) || [],
          backgroundColor: type === 'Tweet' ? 'rgba(29, 161, 242, 0.6)' : 'rgba(126, 34, 206, 0.6)',
          borderColor: type === 'Tweet' ? 'rgb(29, 161, 242)' : 'rgb(126, 34, 206)',
          borderWidth: 1
        }
      ]
    }

    const velocityData = {
      labels: trends.tag_velocities?.slice(0, 8).map(t => t.tag) || [],
      datasets: [
        {
          label: 'First Half',
          data: trends.tag_velocities?.slice(0, 8).map(t => t.first_half) || [],
          backgroundColor: 'rgba(255, 99, 132, 0.6)',
        },
        {
          label: 'Second Half',
          data: trends.tag_velocities?.slice(0, 8).map(t => t.second_half) || [],
          backgroundColor: 'rgba(54, 162, 235, 0.6)',
        }
      ]
    }

    const barOptions: ChartOptions<'bar'> = {
      responsive: true,
      plugins: {
        legend: { display: false },
        title: {
          display: true,
          text: `Top ${type} Tags`
        }
      }
    }

    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Tag Frequency</CardTitle>
              <CardDescription>Most used tags in {type.toLowerCase()}s</CardDescription>
            </CardHeader>
            <CardContent>
              <Bar data={barData} options={barOptions} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Tag Velocity</CardTitle>
              <CardDescription>Growth comparison over time</CardDescription>
            </CardHeader>
            <CardContent>
              <Bar data={velocityData} options={{ 
                responsive: true,
                plugins: {
                  title: {
                    display: true,
                    text: 'Tag Growth Comparison'
                  }
                }
              }} />
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-500" />
                Rising Tags
              </CardTitle>
              <CardDescription>Gaining momentum</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[200px]">
                <div className="space-y-2">
                  {trends.rising_tags?.slice(0, 5).map(tag => (
                    <div key={tag.tag} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{tag.tag}</span>
                      <Badge className="bg-green-100 text-green-700">
                        +{Math.round(tag.velocity)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-red-500" />
                Declining Tags
              </CardTitle>
              <CardDescription>Losing traction</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[200px]">
                <div className="space-y-2">
                  {trends.falling_tags?.slice(0, 5).map(tag => (
                    <div key={tag.tag} className="flex items-center justify-between">
                      <span className="text-sm font-medium">{tag.tag}</span>
                      <Badge className="bg-red-100 text-red-700">
                        {Math.round(tag.velocity)}%
                      </Badge>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link2 className="h-5 w-5 text-blue-500" />
                Tag Relationships
              </CardTitle>
              <CardDescription>Co-occurring tags</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[200px]">
                <div className="space-y-2">
                  {trends.tag_relationships?.slice(0, 5).map((rel, idx) => (
                    <div key={idx} className="text-sm">
                      <span className="font-medium">{rel.tags.join(' ↔ ')}</span>
                      <Badge variant="outline" className="ml-2 text-xs">
                        {rel.count}
                      </Badge>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  const renderClusters = (clusters: ClusterData | null, type: string) => {
    if (!clusters || !clusters.clusters) return null

    const getQualityColor = (rating: string) => {
      switch(rating.toLowerCase()) {
        case 'excellent': return 'text-green-600 bg-green-50 border-green-200'
        case 'good': return 'text-blue-600 bg-blue-50 border-blue-200'
        case 'fair': return 'text-yellow-600 bg-yellow-50 border-yellow-200'
        default: return 'text-gray-600 bg-gray-50 border-gray-200'
      }
    }

    return (
      <div className="space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Clusters</p>
                  <p className="text-2xl font-bold">{clusters.n_clusters}</p>
                </div>
                <Layers className="h-8 w-8 text-blue-500 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Total {type}s</p>
                  <p className="text-2xl font-bold">
                    {clusters.total_tweets || clusters.total_articles}
                  </p>
                </div>
                {type === 'Tweet' ? (
                  <Twitter className="h-8 w-8 text-blue-400 opacity-20" />
                ) : (
                  <FileText className="h-8 w-8 text-purple-500 opacity-20" />
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Quality</p>
                  <Badge className={cn("mt-1", getQualityColor(clusters.quality_rating))}>
                    {clusters.quality_rating}
                  </Badge>
                </div>
                <Target className="h-8 w-8 text-green-500 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-gray-500">Silhouette Score</p>
                  <p className="text-2xl font-bold">
                    {(clusters.silhouette_score * 100).toFixed(1)}%
                  </p>
                </div>
                <CircleDot className="h-8 w-8 text-purple-500 opacity-20" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Clusters Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clusters.clusters?.slice(0, 6).map(cluster => (
            <Card key={cluster.cluster_id}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Cluster {cluster.cluster_id + 1}
                  </CardTitle>
                  <Badge variant="secondary">{cluster.size} items</Badge>
                </div>
                <CardDescription className="font-medium">
                  {cluster.theme}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500 mb-2">Keywords</p>
                    <div className="flex flex-wrap gap-1">
                      {cluster.keywords.map(keyword => (
                        <Badge key={keyword} variant="outline" className="text-xs">
                          {keyword}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  
                  {cluster.top_tags && cluster.top_tags.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 mb-2">Top Tags</p>
                      <div className="space-y-1">
                        {cluster.top_tags.slice(0, 3).map(tag => (
                          <div key={tag.tag} className="flex items-center justify-between">
                            <span className="text-xs">{tag.tag}</span>
                            <Badge variant="secondary" className="text-xs">
                              {tag.count}
                            </Badge>
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
      </div>
    )
  }

  const renderComparison = () => {
    if (!comparison) return null

    const commonTags = comparison.velocity_comparison?.slice(0, 8) || []
    const radarData = {
      labels: commonTags.map(t => t.tag),
      datasets: [
        {
          label: 'Tweet Velocity',
          data: commonTags.map(t => Math.abs(t.tweet_velocity)),
          borderColor: 'rgb(29, 161, 242)',
          backgroundColor: 'rgba(29, 161, 242, 0.2)',
        },
        {
          label: 'Article Velocity',
          data: commonTags.map(t => Math.abs(t.article_velocity)),
          borderColor: 'rgb(126, 34, 206)',
          backgroundColor: 'rgba(126, 34, 206, 0.2)',
        }
      ]
    }

    return (
      <div className="space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Common Tags</p>
                  <p className="text-3xl font-bold">{comparison.summary?.common_tag_count || 0}</p>
                </div>
                <GitBranch className="h-10 w-10 text-purple-500 opacity-20" />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Content Overlap</p>
                  <p className="text-3xl font-bold">
                    {comparison.summary?.overlap_percentage?.toFixed(1) || 0}%
                  </p>
                </div>
                <Shuffle className="h-10 w-10 text-green-500 opacity-20" />
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Radar Chart */}
          <Card>
            <CardHeader>
              <CardTitle>Velocity Comparison</CardTitle>
              <CardDescription>Tag momentum across content types</CardDescription>
            </CardHeader>
            <CardContent>
              <Radar data={radarData} options={{
                responsive: true,
                plugins: {
                  title: {
                    display: true,
                    text: 'Tag Velocity: Tweets vs Articles'
                  }
                }
              }} />
            </CardContent>
          </Card>

          {/* Exclusive Tags */}
          <div className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Twitter className="h-5 w-5 text-blue-400" />
                  Tweet-Only Tags
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {comparison.tweet_exclusive_tags?.slice(0, 10).map(tag => (
                    <Badge key={tag} variant="secondary" className="bg-blue-50 text-blue-700">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5 text-purple-500" />
                  Article-Only Tags
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-2">
                  {comparison.article_exclusive_tags?.slice(0, 10).map(tag => (
                    <Badge key={tag} variant="secondary" className="bg-purple-50 text-purple-700">
                      {tag}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Velocity Alignment Table */}
        <Card>
          <CardHeader>
            <CardTitle>Velocity Alignment</CardTitle>
            <CardDescription>How tag trends align between tweets and articles</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2">Tag</th>
                    <th className="text-center py-2">Tweet Trend</th>
                    <th className="text-center py-2">Article Trend</th>
                    <th className="text-center py-2">Alignment</th>
                  </tr>
                </thead>
                <tbody>
                  {comparison.velocity_comparison?.slice(0, 10).map(item => (
                    <tr key={item.tag} className="border-b">
                      <td className="py-2 font-medium">{item.tag}</td>
                      <td className="py-2 text-center">
                        <Badge variant="outline" className={cn(
                          item.tweet_trend === 'rising' && 'text-green-600 border-green-200',
                          item.tweet_trend === 'falling' && 'text-red-600 border-red-200',
                          item.tweet_trend === 'stable' && 'text-gray-600 border-gray-200'
                        )}>
                          {getTrendIcon(item.tweet_trend)}
                          <span className="ml-1">{item.tweet_trend}</span>
                        </Badge>
                      </td>
                      <td className="py-2 text-center">
                        <Badge variant="outline" className={cn(
                          item.article_trend === 'rising' && 'text-green-600 border-green-200',
                          item.article_trend === 'falling' && 'text-red-600 border-red-200',
                          item.article_trend === 'stable' && 'text-gray-600 border-gray-200'
                        )}>
                          {getTrendIcon(item.article_trend)}
                          <span className="ml-1">{item.article_trend}</span>
                        </Badge>
                      </td>
                      <td className="py-2 text-center">
                        <Badge className={cn(getAlignmentColor(item.alignment))}>
                          {item.alignment}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mr-3" />
          <span className="text-gray-500">Loading analysis...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Unified Trends & Clustering</h1>
            <p className="text-gray-600">Cross-platform content analysis and pattern discovery</p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={days} onValueChange={setDays}>
              <SelectTrigger className="w-32">
                <Clock className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="3">3 Days</SelectItem>
                <SelectItem value="7">1 Week</SelectItem>
                <SelectItem value="14">2 Weeks</SelectItem>
                <SelectItem value="30">1 Month</SelectItem>
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

      {/* Main Content */}
      <Tabs 
        value={contentType === 'comparison' ? 'comparison' : `${contentType}-${viewType}`}
        onValueChange={(value) => {
          if (value === 'comparison') {
            setContentType('comparison')
            setViewType('trends')
          } else {
            const [content, view] = value.split('-') as ['tweets' | 'articles', 'trends' | 'clusters']
            setContentType(content)
            setViewType(view)
          }
        }}
        className="space-y-4"
      >
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="tweets-trends">Tweet Trends</TabsTrigger>
          <TabsTrigger value="tweets-clusters">Tweet Clusters</TabsTrigger>
          <TabsTrigger value="articles-trends">Article Trends</TabsTrigger>
          <TabsTrigger value="articles-clusters">Article Clusters</TabsTrigger>
          <TabsTrigger value="comparison">Compare</TabsTrigger>
        </TabsList>

        <TabsContent value="tweets-trends">
          {renderTrendCharts(tweetTrends, 'Tweet')}
        </TabsContent>

        <TabsContent value="tweets-clusters">
          {renderClusters(tweetClusters, 'Tweet')}
        </TabsContent>

        <TabsContent value="articles-trends">
          {renderTrendCharts(articleTrends, 'Article')}
        </TabsContent>

        <TabsContent value="articles-clusters">
          {renderClusters(articleClusters, 'Article')}
        </TabsContent>

        <TabsContent value="comparison">
          {renderComparison()}
        </TabsContent>
      </Tabs>
    </div>
  )
}