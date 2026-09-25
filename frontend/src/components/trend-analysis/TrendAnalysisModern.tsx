import { useState, useEffect } from 'react'
import http from '@/services/http'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { cn } from "@/lib/utils"
import {
  RefreshCw,
  Loader2,
  AlertCircle,
  Activity,
  Users,
  FileText,
  BookOpen
} from 'lucide-react'
import TrendChartPanel from './TrendChartPanel'

interface ConceptTrend {
  concept_id: string
  display_name: string
  current_count: number
  previous_count: number
  velocity: number
}

interface TrendAnalysisData {
  period_days: number
  start_date: string
  end_date: string
  trends: {
    rising: ConceptTrend[]
    stable: ConceptTrend[]
    declining: ConceptTrend[]
  }
  top_concepts: Array<{
    concept_id: string
    display_name: string
    count: number
    entity_type?: string
  }>
  concept_velocity: ConceptTrend[]
  content_distribution: {
    tweets: number
    articles: number
    papers: number
  }
  timeline: Array<{
    date: string
    tweets: number
    articles: number
    papers: number
    unique_concepts: number
    total: number
  }>
  insights: {
    most_active_day?: string
    most_active_concept?: {
      name: string
      count: number
    }
    fastest_rising?: ConceptTrend
    fastest_declining?: ConceptTrend
    total_content: number
    unique_concepts_used: number
  }
}

export default function TrendAnalysisModern() {
  const [trendData, setTrendData] = useState<TrendAnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState('7')
  const [refreshing, setRefreshing] = useState(false)
  const [selectedTab, setSelectedTab] = useState('overview')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchTrends()
  }, [timeRange])

  const fetchTrends = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await http.get(`/api/trends/analysis?days=${timeRange}`)
      setTrendData(response.data)
    } catch (error) {
      console.error('Error fetching trends:', error)
      setError('Failed to load trend analysis')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchTrends()
  }

  const getContentIcon = (type: string) => {
    switch(type) {
      case 'tweets': return <Users className="h-4 w-4 text-blue-500" />
      case 'articles': return <FileText className="h-4 w-4 text-purple-500" />
      case 'papers': return <BookOpen className="h-4 w-4 text-green-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
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

  if (error) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <Card className="border-red-200 bg-red-50">
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="h-5 w-5" />
              <span>{error}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!trendData) {
    return null
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-3xl font-bold">Trend Analysis</h1>
            <p className="text-gray-500 mt-1">
              Analyzing {trendData.insights.total_content} items across {trendData.period_days} days
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">7 days</SelectItem>
                <SelectItem value="14">14 days</SelectItem>
                <SelectItem value="30">30 days</SelectItem>
                <SelectItem value="90">90 days</SelectItem>
              </SelectContent>
            </Select>
            <Button
              onClick={handleRefresh}
              variant="outline"
              disabled={refreshing}
              className="gap-2"
            >
              <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {/* Content Distribution */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Content Distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {Object.entries(trendData.content_distribution).map(([type, count]) => (
                <div key={type} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getContentIcon(type)}
                    <span className="text-sm capitalize">{type}</span>
                  </div>
                  <span className="font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Unique Concepts */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Unique Concepts</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{trendData.insights.unique_concepts_used}</p>
            <p className="text-xs text-gray-500 mt-1">Across all content</p>
          </CardContent>
        </Card>

        {/* Most Active Day */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Peak Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-lg font-semibold">
              {trendData.insights.most_active_day || 'N/A'}
            </p>
            <p className="text-xs text-gray-500 mt-1">Most active day</p>
          </CardContent>
        </Card>

        {/* Top Concept */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-gray-500">Top Concept</CardTitle>
          </CardHeader>
          <CardContent>
            {trendData.insights.most_active_concept ? (
              <>
                <p className="text-lg font-semibold truncate">
                  {trendData.insights.most_active_concept.name}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {trendData.insights.most_active_concept.count} mentions
                </p>
              </>
            ) : (
              <p className="text-gray-400">No data</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs value={selectedTab} onValueChange={setSelectedTab} className="space-y-4">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="rising">Rising</TabsTrigger>
          <TabsTrigger value="declining">Declining</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <TrendChartPanel trendData={trendData} selectedTab="overview" />
        </TabsContent>

        <TabsContent value="rising">
          <TrendChartPanel trendData={trendData} selectedTab="rising" />
        </TabsContent>

        <TabsContent value="declining">
          <TrendChartPanel trendData={trendData} selectedTab="declining" />
        </TabsContent>

        <TabsContent value="timeline">
          <TrendChartPanel trendData={trendData} selectedTab="timeline" />
        </TabsContent>
      </Tabs>
    </div>
  )
}
