import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { 
  TrendingUp,
  TrendingDown,
  Clock,
  BarChart3,
  Activity,
  RefreshCw,
  Loader2,
  AlertCircle,
  Sparkles,
  Hash,
  Calendar,
  ArrowUp,
  ArrowDown,
  Minus,
  Timer,
  ChevronRight,
  Zap,
  Target,
  Flame
} from 'lucide-react'

interface TagTrend {
  tag: string
  count: number
  growth?: number
  decline?: number
  trend?: 'up' | 'down' | 'stable' | 'new'
  previous_count?: number
}

interface PeriodData {
  tweet_count: number
  unique_tags: number
  top_tags: TagTrend[]
  most_active_user?: string
  avg_engagement?: number
}

interface TrendData {
  last_hour?: PeriodData
  last_6_hours?: PeriodData
  last_24_hours?: PeriodData
  last_7_days?: PeriodData
  trending_up?: TagTrend[]
  trending_down?: TagTrend[]
  emerging_tags?: TagTrend[]
  dying_tags?: TagTrend[]
  timeline?: Array<{
    date: string
    tweet_count: number
    tag_count: number
  }>
}

export default function TrendAnalysisModern() {
  const [trends, setTrends] = useState<TrendData>({})
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('24h')
  const [refreshing, setRefreshing] = useState(false)
  const [selectedTab, setSelectedTab] = useState('overview')

  useEffect(() => {
    fetchTrends()
  }, [timeRange])

  const fetchTrends = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/trends/analysis')
      setTrends(response.data)
    } catch (error) {
      console.error('Error fetching trends:', error)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchTrends()
  }

  const getTrendIcon = (trend?: string) => {
    switch(trend) {
      case 'up': return <ArrowUp className="h-4 w-4 text-green-500" />
      case 'down': return <ArrowDown className="h-4 w-4 text-red-500" />
      case 'new': return <Sparkles className="h-4 w-4 text-purple-500" />
      default: return <Minus className="h-4 w-4 text-gray-400" />
    }
  }

  const getTrendColor = (trend?: string) => {
    switch(trend) {
      case 'up': return 'text-green-600 bg-green-50 border-green-200'
      case 'down': return 'text-red-600 bg-red-50 border-red-200'
      case 'new': return 'text-purple-600 bg-purple-50 border-purple-200'
      default: return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const formatGrowth = (growth?: number) => {
    if (!growth) return '0%'
    return growth > 0 ? `+${growth.toFixed(0)}%` : `${growth.toFixed(0)}%`
  }

  const getPeriodIcon = (period: string) => {
    switch(period) {
      case 'hour': return <Timer className="h-4 w-4" />
      case '6hours': return <Clock className="h-4 w-4" />
      case '24hours': return <Calendar className="h-4 w-4" />
      default: return <Activity className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mr-3" />
          <span className="text-gray-500">Analyzing trends...</span>
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Trend Analysis</h1>
            <p className="text-gray-600">Track emerging topics and declining discussions</p>
          </div>
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

      {/* Time Period Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        {[
          { key: 'last_hour', label: 'Last Hour', icon: <Timer /> },
          { key: 'last_6_hours', label: 'Last 6 Hours', icon: <Clock /> },
          { key: 'last_24_hours', label: 'Last 24 Hours', icon: <Calendar /> },
          { key: 'last_7_days', label: 'Last 7 Days', icon: <BarChart3 /> }
        ].map(period => {
          const data = trends[period.key as keyof TrendData] as PeriodData
          if (!data) return null
          
          return (
            <Card key={period.key}>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium">{period.label}</CardTitle>
                  {period.icon}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Tweets</span>
                    <span className="text-2xl font-bold">{data.tweet_count || 0}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-gray-500">Unique Tags</span>
                    <span className="text-lg font-semibold">{data.unique_tags || 0}</span>
                  </div>
                  {data.most_active_user && (
                    <div className="pt-2 border-t">
                      <p className="text-xs text-gray-500">Most Active</p>
                      <p className="text-sm font-medium">@{data.most_active_user}</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>

      {/* Main Content Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trending">Trending</TabsTrigger>
          <TabsTrigger value="emerging">Emerging</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Trending Up */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-green-500" />
                    Trending Up
                  </CardTitle>
                  <Badge variant="secondary" className="bg-green-50 text-green-700">
                    {trends.trending_up?.length || 0} tags
                  </Badge>
                </div>
                <CardDescription>Topics gaining momentum</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  <div className="space-y-2">
                    {trends.trending_up?.slice(0, 10).map((item, index) => (
                      <div
                        key={item.tag}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-700 font-semibold text-sm">
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium">{item.tag}</p>
                            <p className="text-xs text-gray-500">{item.count} mentions</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-green-100 text-green-700 border-green-200">
                            {formatGrowth(item.growth)}
                          </Badge>
                          <TrendingUp className="h-4 w-4 text-green-500" />
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Trending Down */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <TrendingDown className="h-5 w-5 text-red-500" />
                    Trending Down
                  </CardTitle>
                  <Badge variant="secondary" className="bg-red-50 text-red-700">
                    {trends.trending_down?.length || 0} tags
                  </Badge>
                </div>
                <CardDescription>Topics losing traction</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  <div className="space-y-2">
                    {trends.trending_down?.slice(0, 10).map((item, index) => (
                      <div
                        key={item.tag}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 text-red-700 font-semibold text-sm">
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium">{item.tag}</p>
                            <p className="text-xs text-gray-500">{item.count} mentions</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-red-100 text-red-700 border-red-200">
                            {formatGrowth(item.decline)}
                          </Badge>
                          <TrendingDown className="h-4 w-4 text-red-500" />
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="trending" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Hot Topics</CardTitle>
              <CardDescription>Most discussed topics across all time periods</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {['last_hour', 'last_6_hours', 'last_24_hours'].map(period => {
                  const data = trends[period as keyof TrendData] as PeriodData
                  if (!data || !data.top_tags) return null
                  
                  return (
                    <div key={period}>
                      <h3 className="text-sm font-semibold mb-2 flex items-center gap-2">
                        {getPeriodIcon(period.replace('last_', '').replace('_', ''))}
                        {period.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {data.top_tags.slice(0, 10).map(tag => (
                          <Badge
                            key={tag.tag}
                            variant="secondary"
                            className={cn(getTrendColor(tag.trend))}
                          >
                            <Hash className="h-3 w-3 mr-1" />
                            {tag.tag}
                            <span className="ml-2 font-semibold">{tag.count}</span>
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="emerging" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Emerging Tags */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-purple-500" />
                    Emerging Topics
                  </CardTitle>
                  <Badge variant="secondary" className="bg-purple-50 text-purple-700">
                    New
                  </Badge>
                </div>
                <CardDescription>Newly appearing discussions</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  <div className="space-y-2">
                    {trends.emerging_tags?.map((item, index) => (
                      <div
                        key={item.tag}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-purple-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <Sparkles className="h-4 w-4 text-purple-500" />
                          <div>
                            <p className="font-medium">{item.tag}</p>
                            <p className="text-xs text-gray-500">First appearance</p>
                          </div>
                        </div>
                        <Badge variant="outline" className="border-purple-200 text-purple-700">
                          {item.count} mentions
                        </Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Dying Tags */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-gray-500" />
                    Fading Topics
                  </CardTitle>
                  <Badge variant="secondary" className="bg-gray-50 text-gray-700">
                    Declining
                  </Badge>
                </div>
                <CardDescription>Topics losing relevance</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[300px]">
                  <div className="space-y-2">
                    {trends.dying_tags?.map((item, index) => (
                      <div
                        key={item.tag}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <Activity className="h-4 w-4 text-gray-400" />
                          <div>
                            <p className="font-medium text-gray-600">{item.tag}</p>
                            <p className="text-xs text-gray-400">Fading out</p>
                          </div>
                        </div>
                        <Badge variant="outline" className="border-gray-200 text-gray-500">
                          {item.count} mentions
                        </Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Activity Timeline</CardTitle>
              <CardDescription>Tweet and tag activity over time</CardDescription>
            </CardHeader>
            <CardContent>
              {trends.timeline && trends.timeline.length > 0 ? (
                <div className="space-y-4">
                  <div className="h-64 relative">
                    <div className="absolute inset-0 flex items-end gap-1">
                      {trends.timeline.map((point, index) => {
                        const maxTweets = Math.max(...trends.timeline!.map(p => p.tweet_count))
                        const height = maxTweets > 0 ? (point.tweet_count / maxTweets) * 100 : 0
                        
                        return (
                          <div
                            key={index}
                            className="flex-1 flex flex-col justify-end"
                          >
                            <div
                              className="bg-blue-500 rounded-t hover:bg-blue-600 transition-colors cursor-pointer"
                              style={{ height: `${height}%` }}
                              title={`${point.date}: ${point.tweet_count} tweets, ${point.tag_count} tags`}
                            />
                            <span className="text-xs text-gray-400 mt-1 rotate-45 origin-left">
                              {new Date(point.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                    <div className="text-center">
                      <p className="text-xs text-gray-500">Total Tweets</p>
                      <p className="text-2xl font-bold text-blue-600">
                        {trends.timeline.reduce((sum, p) => sum + p.tweet_count, 0)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500">Unique Tags</p>
                      <p className="text-2xl font-bold text-purple-600">
                        {new Set(trends.timeline.flatMap(p => p.tag_count)).size}
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No timeline data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}