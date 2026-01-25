import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  ChartOptions
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'
import {
  TrendingUp,
  TrendingDown,
  Clock,
  RefreshCw,
  Loader2,
  Hash,
  Users,
  Timer,
  LineChart,
  Zap,
  Twitter,
  FileText
} from 'lucide-react'

// Register ChartJS components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
)

interface TrendData {
  daily: { date: string; count: number }[]
  hourly: { hour: string; count: number }[]
  by_account: { [key: string]: { date: string; count: number }[] }
}

interface TagTrendData {
  top_tags: { tag: string; count: number }[]
  timeline: { [key: string]: { date: string; count: number }[] }
}

interface QuickInsight {
  type: 'increase' | 'decrease' | 'stable' | 'peak' | 'low'
  title: string
  value: string
  description: string
  icon: React.ReactNode
}

interface Props {
  contentType?: 'tweets' | 'articles'
}

export default function TrendVisualizationModern({ contentType = 'tweets' }: Props) {
  // Initialize with safe default values
  const [trendData, setTrendData] = useState<TrendData>({
    daily: [],
    hourly: [],
    by_account: {}
  })
  const [tagData, setTagData] = useState<TagTrendData>({
    top_tags: [],
    timeline: {}
  })
  const [timeRange, setTimeRange] = useState('7')
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [quickInsights, setQuickInsights] = useState<QuickInsight[]>([])

  useEffect(() => {
    fetchTrendData()
  }, [timeRange, contentType])

  const fetchTrendData = async () => {
    setLoading(true)
    try {
      let trendsData: TrendData | null = null
      let tagsData: TagTrendData | null = null
      
      if (contentType === 'articles') {
        // For articles, use the substack trends endpoint
        const trendResponse = await axios.get(
          `http://localhost:8000/api/substack/trends?days=${timeRange}`
        )
        // Transform the data to match the expected format
        if (trendResponse.data) {
          const data = trendResponse.data
          // Create a simplified trend data structure with safe defaults
          trendsData = {
            daily: data.daily || [], // Use data if available
            hourly: data.hourly || [], // Use data if available
            by_account: data.by_account || {} // Use data if available
          }
          setTrendData(trendsData)
          
          // Transform tag data from topic_trends
          if (data.topic_trends) {
            tagsData = {
              top_tags: data.topic_trends.top_topics?.map((t: any) => ({
                tag: t.term,
                count: t.articles
              })) || [],
              timeline: {}
            }
            setTagData(tagsData)
          }
        }
      } else {
        // For tweets, use the regular analytics endpoints
        const trendResponse = await axios.get(
          `http://localhost:8000/api/analytics/trends/timeline?days=${timeRange}`
        )
        trendsData = trendResponse.data
        if (trendsData) setTrendData(trendsData)

        const tagResponse = await axios.get(
          `http://localhost:8000/api/analytics/trends/tags?days=${timeRange}`
        )
        tagsData = tagResponse.data
        if (tagsData) setTagData(tagsData)
      }

      // Generate quick insights
      if (trendsData && tagsData) {
        generateQuickInsights(trendsData, tagsData)
      }
    } catch (error) {
      console.error('Error fetching trends:', error)
      // Set safe defaults on error
      setTrendData({
        daily: [],
        hourly: [],
        by_account: {}
      })
      setTagData({
        top_tags: [],
        timeline: {}
      })
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const generateQuickInsights = (trends: TrendData, tags: TagTrendData) => {
    const insights: QuickInsight[] = []
    
    if (trends.daily && trends.daily.length > 1) {
      const latest = trends.daily[trends.daily.length - 1].count
      const previous = trends.daily[trends.daily.length - 2].count
      const change = ((latest - previous) / previous) * 100
      
      if (change > 20) {
        insights.push({
          type: 'increase',
          title: 'Activity Surge',
          value: `+${change.toFixed(0)}%`,
          description: 'Compared to yesterday',
          icon: <TrendingUp className="h-4 w-4" />
        })
      } else if (change < -20) {
        insights.push({
          type: 'decrease',
          title: 'Activity Drop',
          value: `${change.toFixed(0)}%`,
          description: 'Compared to yesterday',
          icon: <TrendingDown className="h-4 w-4" />
        })
      }
      
      // Find peak day
      const peak = Math.max(...trends.daily.map(d => d.count))
      const peakDay = trends.daily.find(d => d.count === peak)
      if (peakDay) {
        insights.push({
          type: 'peak',
          title: 'Peak Activity',
          value: peak.toString(),
          description: `on ${new Date(peakDay.date).toLocaleDateString()}`,
          icon: <Zap className="h-4 w-4" />
        })
      }
    }
    
    // Top trending tag
    if (tags.top_tags && tags.top_tags.length > 0) {
      insights.push({
        type: 'stable',
        title: 'Top Tag',
        value: tags.top_tags[0].tag,
        description: `${tags.top_tags[0].count} mentions`,
        icon: <Hash className="h-4 w-4" />
      })
    }
    
    setQuickInsights(insights)
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchTrendData()
  }

  // Prepare chart data for daily timeline with smart labeling based on time range
  const getTimelineLabels = (data: any[], timeRangeNum: number) => {
    if (!data || data.length === 0) return []
    
    if (timeRangeNum >= 180) {
      // For half-year and yearly views, show month/year format
      return data.map(d => new Date(d.date).toLocaleDateString('en-US', { 
        month: 'short', 
        year: timeRangeNum >= 365 ? '2-digit' : undefined 
      }))
    } else if (timeRangeNum >= 30) {
      // For monthly views, show month/day
      return data.map(d => new Date(d.date).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      }))
    } else {
      // For shorter periods, show day only or month/day
      return data.map(d => new Date(d.date).toLocaleDateString('en-US', { 
        month: timeRangeNum <= 7 ? undefined : 'short',
        day: 'numeric',
        weekday: timeRangeNum <= 3 ? 'short' : undefined
      }))
    }
  }

  const dailyChartData = {
    labels: getTimelineLabels(trendData?.daily || [], parseInt(timeRange)),
    datasets: [
      {
        label: `${contentType === 'articles' ? 'Articles' : 'Tweets'} per Day`,
        data: trendData?.daily?.map(d => d.count) || [],
        borderColor: contentType === 'articles' ? 'rgb(126, 34, 206)' : 'rgb(29, 161, 242)',
        backgroundColor: contentType === 'articles' ? 'rgba(126, 34, 206, 0.1)' : 'rgba(29, 161, 242, 0.1)',
        tension: 0.3,
        fill: true
      }
    ]
  }

  // Prepare chart data for hourly timeline
  const hourlyChartData = {
    labels: trendData?.hourly?.map(d => {
      const hour = d.hour.split(' ')[1] || d.hour
      return hour
    }) || [],
    datasets: [
      {
        label: `${contentType === 'articles' ? 'Articles' : 'Tweets'} per Hour`,
        data: trendData?.hourly?.map(d => d.count) || [],
        borderColor: 'rgb(255, 99, 132)',
        backgroundColor: 'rgba(255, 99, 132, 0.1)',
        tension: 0.3,
        fill: true
      }
    ]
  }

  // Prepare account comparison data
  const accountColors = [
    'rgb(29, 161, 242)',
    'rgb(126, 34, 206)',
    'rgb(16, 185, 129)',
    'rgb(251, 146, 60)',
    'rgb(244, 63, 94)',
    'rgb(99, 102, 241)',
    'rgb(236, 72, 153)'
  ]

  const accountChartData = {
    labels: getTimelineLabels(trendData?.daily || [], parseInt(timeRange)),
    datasets: Object.entries(trendData?.by_account || {}).slice(0, 7).map(([ account, data ], index) => ({
      label: `@${account}`,
      data: data.map(d => d.count),
      borderColor: accountColors[index],
      backgroundColor: accountColors[index] + '20',
      tension: 0.3
    }))
  }

  // Prepare tag trend data
  const tagChartData = {
    labels: tagData?.top_tags.slice(0, 10).map(t => t.tag) || [],
    datasets: [
      {
        label: 'Tag Frequency',
        data: tagData?.top_tags.slice(0, 10).map(t => t.count) || [],
        backgroundColor: contentType === 'articles' 
          ? 'rgba(126, 34, 206, 0.6)' 
          : 'rgba(29, 161, 242, 0.6)',
        borderColor: contentType === 'articles'
          ? 'rgb(126, 34, 206)'
          : 'rgb(29, 161, 242)',
        borderWidth: 1
      }
    ]
  }

  const chartOptions: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: true,
        position: 'top' as const,
      },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }

  const barChartOptions: ChartOptions<'bar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)'
        }
      },
      x: {
        grid: {
          display: false
        }
      }
    }
  }

  if (loading) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400 mr-3" />
          <span className="text-gray-500">Loading visualization data...</span>
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
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {contentType === 'articles' ? 'Article' : 'Tweet'} Trend Analysis
            </h1>
            <p className="text-gray-600">
              Visualize patterns and trends in {contentType === 'articles' ? 'newsletter' : 'social media'} activity
              {parseInt(timeRange) >= 180 && (
                <span className="text-sm text-amber-600 block mt-1">
                  📊 Long-term view: Data may take a moment to load
                </span>
              )}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-48">
                <Clock className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Last 24 hours</SelectItem>
                <SelectItem value="3">Last 3 days</SelectItem>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="14">Last 14 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last quarter (90 days)</SelectItem>
                <SelectItem value="180">Last half year (180 days)</SelectItem>
                <SelectItem value="365">Last year (365 days)</SelectItem>
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

      {/* Quick Insights */}
      {quickInsights.length > 0 && (
        <div className="mb-6">
          <h2 className="text-lg font-semibold mb-3">Quick Insights</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickInsights.map((insight, index) => (
              <Card key={index}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-xs text-gray-500 mb-1">{insight.title}</p>
                      <p className={cn(
                        "text-2xl font-bold",
                        insight.type === 'increase' && "text-green-600",
                        insight.type === 'decrease' && "text-red-600",
                        insight.type === 'peak' && "text-blue-600",
                        insight.type === 'stable' && "text-gray-700"
                      )}>
                        {insight.value}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">{insight.description}</p>
                    </div>
                    <div className={cn(
                      "p-2 rounded-full",
                      insight.type === 'increase' && "bg-green-100 text-green-600",
                      insight.type === 'decrease' && "bg-red-100 text-red-600",
                      insight.type === 'peak' && "bg-blue-100 text-blue-600",
                      insight.type === 'stable' && "bg-gray-100 text-gray-600"
                    )}>
                      {insight.icon}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Main Charts */}
      <Tabs defaultValue="timeline" className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="hourly">Hourly</TabsTrigger>
          <TabsTrigger value="tags">Concepts</TabsTrigger>
          <TabsTrigger value="accounts">By Account</TabsTrigger>
        </TabsList>

        <TabsContent value="timeline" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LineChart className="h-5 w-5" />
                Daily Activity Timeline
              </CardTitle>
              <CardDescription>
                {contentType === 'articles' ? 'Articles published' : 'Tweets posted'} per day over the selected period
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <Line data={dailyChartData} options={chartOptions} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="hourly" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Timer className="h-5 w-5" />
                Hourly Activity Pattern
              </CardTitle>
              <CardDescription>
                Activity distribution throughout the last 24 hours
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <Line data={hourlyChartData} options={chartOptions} />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="tags" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Hash className="h-5 w-5" />
                Top Concepts Distribution
              </CardTitle>
              <CardDescription>
                Most frequently used concepts in the selected period
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <Bar data={tagChartData} options={barChartOptions} />
              </div>
            </CardContent>
          </Card>

          {/* Tag Timeline */}
          {tagData?.timeline && Object.keys(tagData.timeline).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Concept Evolution Over Time</CardTitle>
                <CardDescription>Track how specific concepts trend over the period</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-[400px]">
                  <Line 
                    data={{
                      labels: Object.values(tagData.timeline)[0]?.map(d => d.date) ? 
                        getTimelineLabels(Object.values(tagData.timeline)[0] as any[], parseInt(timeRange)) : [],
                      datasets: Object.entries(tagData.timeline).slice(0, 5).map(([tag, data], index) => ({
                        label: tag,
                        data: data.map(d => d.count),
                        borderColor: accountColors[index],
                        backgroundColor: accountColors[index] + '20',
                        tension: 0.3
                      }))
                    }}
                    options={chartOptions}
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="accounts" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Activity by Account
              </CardTitle>
              <CardDescription>
                Compare activity levels across different accounts
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[400px]">
                <Line data={accountChartData} options={chartOptions} />
              </div>
            </CardContent>
          </Card>

          {/* Account Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.entries(trendData?.by_account || {}).slice(0, 6).map(([account, data]) => {
              const total = data.reduce((sum, d) => sum + d.count, 0)
              const avg = total / data.length
              const max = Math.max(...data.map(d => d.count))
              
              return (
                <Card key={account}>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      {contentType === 'articles' ? (
                        <FileText className="h-4 w-4" />
                      ) : (
                        <Twitter className="h-4 w-4" />
                      )}
                      @{account}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">Total</span>
                        <span className="text-sm font-semibold">{total}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">Daily Avg</span>
                        <span className="text-sm font-semibold">{avg.toFixed(1)}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-xs text-gray-500">Peak</span>
                        <span className="text-sm font-semibold">{max}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}