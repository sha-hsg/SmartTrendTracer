import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Skeleton } from '@/components/ui/skeleton'
import {
  TrendingUp,
  TrendingDown,
  Zap,
  BarChart3,
  Activity,
  Clock,
  Hash,
  ArrowUpIcon,
  ArrowDownIcon,
  Flame,
  Sparkles,
  AlertCircle,
  ChevronRight,
  Calendar,
  Target,
  Gauge
} from 'lucide-react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer
} from 'recharts'
import { format, parseISO } from 'date-fns'

interface ConceptTrend {
  concept_id: string
  display_name: string
  slug: string
  entity_type: string
  count?: number
  content_types?: string[]
  first_seen?: string
  last_seen?: string
  days_active?: number
  current_mentions?: number
  previous_mentions?: number
  growth_percent?: number
  decline_percent?: number
  velocity_percent?: number
  acceleration?: number
  trend?: string
  momentum?: string
  status?: string
  unique_sources?: number
  peak_day?: string
  peak_value?: number
}

interface TimelineData {
  concept_id: string
  name: string
  data: Array<{ date: string; value: number }>
  total: number
  peak_value: number
  peak_date: string
}

interface TrendOverview {
  period_days: number
  summary: {
    total_annotations: number
    unique_concepts: number
    content_distribution: Record<string, number>
    daily_average: number
  }
  top_concepts: ConceptTrend[]
  velocity_leaders: ConceptTrend[]
  rising: ConceptTrend[]
  declining: ConceptTrend[]
  recent_activity: Array<{ _id: string; count: number }>
}

const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316']

// Custom tooltip for the timeline chart
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const total = payload.reduce((sum: number, entry: any) => sum + (entry.value || 0), 0)
    return (
      <div className="bg-white p-3 border rounded-lg shadow-lg">
        <p className="font-medium mb-2">{label}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center gap-2 text-sm">
            <div 
              className="w-3 h-3 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            <span className="flex-1">{entry.name}:</span>
            <span className="font-medium">{entry.value}</span>
          </div>
        ))}
        <div className="mt-2 pt-2 border-t text-sm font-medium">
          Total: {total}
        </div>
      </div>
    )
  }
  return null
}

export default function TrendAnalysisOverview() {
  const [loading, setLoading] = useState(true)
  const [overview, setOverview] = useState<TrendOverview | null>(null)
  const [topConcepts, setTopConcepts] = useState<ConceptTrend[]>([])
  const [velocityLeaders, setVelocityLeaders] = useState<ConceptTrend[]>([])
  const [risingTrends, setRisingTrends] = useState<ConceptTrend[]>([])
  const [decliningTrends, setDecliningTrends] = useState<ConceptTrend[]>([])
  const [timeline, setTimeline] = useState<TimelineData[]>([])
  const [selectedPeriod, setSelectedPeriod] = useState('7')
  const [selectedView, setSelectedView] = useState('overview')
  const [selectedConcepts, setSelectedConcepts] = useState<string[]>([])
  const [timelineGranularity, setTimelineGranularity] = useState('daily')
  const [loadingTimeline, setLoadingTimeline] = useState(false)
  const [availableConcepts, setAvailableConcepts] = useState<ConceptTrend[]>([])
  const [comparisonMode, setComparisonMode] = useState(false)

  useEffect(() => {
    loadTrendData()
  }, [selectedPeriod])

  // Remove the problematic useEffect that causes infinite loops

  const loadTrendData = async () => {
    setLoading(true)
    try {
      const days = parseInt(selectedPeriod)
      
      // Load overview
      const overviewRes = await axios.get(`http://localhost:8000/api/trends/analysis/overview?days=${days}`)
      setOverview(overviewRes.data)
      
      // Load detailed data for each view
      const [topRes, velocityRes, risingRes, decliningRes] = await Promise.all([
        axios.get(`http://localhost:8000/api/trends/analysis/top-concepts?days=${days}&limit=20`),
        axios.get(`http://localhost:8000/api/trends/analysis/velocity-leaders?days=${days}&limit=20`),
        axios.get(`http://localhost:8000/api/trends/analysis/rising?days=${days}&limit=20`),
        axios.get(`http://localhost:8000/api/trends/analysis/declining?days=${days}&limit=20`)
      ])
      
      setTopConcepts(topRes.data.concepts)
      setVelocityLeaders(velocityRes.data.velocity_leaders)
      setRisingTrends(risingRes.data.rising_concepts)
      setDecliningTrends(decliningRes.data.declining_concepts)
      
      // Store available concepts for timeline selection
      setAvailableConcepts(topRes.data.concepts)
    } catch (error) {
      console.error('Error loading trend data:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadTimelineData = async () => {
    setLoadingTimeline(true)
    try {
      const days = parseInt(selectedPeriod)
      
      // If concepts are selected, use them
      if (selectedConcepts.length > 0) {
        // Build URL with proper array parameter format
        const params = new URLSearchParams()
        selectedConcepts.forEach(id => params.append('concept_ids', id))
        params.append('days', days.toString())
        params.append('granularity', timelineGranularity)
        
        const timelineRes = await axios.get(
          `http://localhost:8000/api/trends/analysis/timeline?${params.toString()}`
        )
        setTimeline(timelineRes.data.timeline || [])
      } else {
        // Load top concepts overall (limited by backend)
        const timelineRes = await axios.get(`http://localhost:8000/api/trends/analysis/timeline`, {
          params: {
            days: days,
            granularity: timelineGranularity,
            max_concepts: 5  // Only show top 5 when none selected
          }
        })
        setTimeline(timelineRes.data.timeline || [])
      }
    } catch (error) {
      console.error('Error loading timeline:', error)
      setTimeline([])
      // Show error message to user
      alert('Failed to load timeline data. Please try again.')
    } finally {
      setLoadingTimeline(false)
    }
  }

  const getEntityIcon = (entityType: string) => {
    switch (entityType) {
      case 'person': return '👤'
      case 'organisation': return '🏢'
      case 'location': return '📍'
      case 'event': return '📅'
      case 'technology': return '💻'
      default: return '🏷️'
    }
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'explosive': return <Flame className="h-4 w-4 text-red-500" />
      case 'strong': return <TrendingUp className="h-4 w-4 text-green-500" />
      case 'moderate': return <ArrowUpIcon className="h-4 w-4 text-blue-500" />
      case 'emerging': return <Sparkles className="h-4 w-4 text-purple-500" />
      case 'declining': return <TrendingDown className="h-4 w-4 text-orange-500" />
      case 'fading': return <ArrowDownIcon className="h-4 w-4 text-red-500" />
      default: return <Activity className="h-4 w-4 text-gray-500" />
    }
  }

  const formatNumber = (num: number) => {
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`
    return num.toString()
  }

  if (loading) {
    return (
      <div className="space-y-6">
        {[1, 2, 3, 4].map(i => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-6 w-48" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-32 w-full" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with period selector */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl">Trend Analysis</CardTitle>
            <Select value={selectedPeriod} onValueChange={setSelectedPeriod}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="14">Last 14 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Stats */}
      {overview && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Activity</p>
                  <p className="text-2xl font-bold">{formatNumber(overview.summary.total_annotations)}</p>
                </div>
                <Activity className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Unique Concepts</p>
                  <p className="text-2xl font-bold">{overview.summary.unique_concepts}</p>
                </div>
                <Hash className="h-8 w-8 text-green-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Daily Average</p>
                  <p className="text-2xl font-bold">{Math.round(overview.summary.daily_average)}</p>
                </div>
                <Calendar className="h-8 w-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Top Source</p>
                  <p className="text-2xl font-bold">
                    {Object.entries(overview.summary.content_distribution)[0]?.[0] || 'N/A'}
                  </p>
                </div>
                <BarChart3 className="h-8 w-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Main Content Tabs */}
      <Tabs value={selectedView} onValueChange={setSelectedView}>
        <TabsList className="grid w-full grid-cols-6">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="top">Top Concepts</TabsTrigger>
          <TabsTrigger value="velocity">Velocity Leaders</TabsTrigger>
          <TabsTrigger value="rising">Rising</TabsTrigger>
          <TabsTrigger value="declining">Declining</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Concepts Mini View */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Top Concepts
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {overview?.top_concepts.map((concept, idx) => (
                    <div key={concept.concept_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">{idx + 1}.</span>
                        <span className="text-sm">{getEntityIcon(concept.entity_type)}</span>
                        <span className="font-medium">{concept.display_name}</span>
                      </div>
                      <Badge variant="secondary">{concept.count}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Velocity Leaders Mini View */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5" />
                  Velocity Leaders
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {overview?.velocity_leaders.map((concept, idx) => (
                    <div key={concept.concept_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">{idx + 1}.</span>
                        <span className="font-medium">{concept.display_name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {concept.velocity_percent && concept.velocity_percent > 0 ? (
                          <TrendingUp className="h-4 w-4 text-green-500" />
                        ) : (
                          <TrendingDown className="h-4 w-4 text-red-500" />
                        )}
                        <span className="text-sm font-medium">
                          {concept.velocity_percent?.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Rising Trends Mini View */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-500" />
                  Rising Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {overview?.rising.map((concept, idx) => (
                    <div key={concept.concept_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">{idx + 1}.</span>
                        <span className="font-medium">{concept.display_name}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {getTrendIcon(concept.momentum || '')}
                        <span className="text-sm font-medium text-green-600">
                          +{concept.growth_percent?.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Declining Trends Mini View */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-red-500" />
                  Declining Trends
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {overview?.declining.map((concept, idx) => (
                    <div key={concept.concept_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-500">{idx + 1}.</span>
                        <span className="font-medium">{concept.display_name}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        {getTrendIcon(concept.status || '')}
                        <span className="text-sm font-medium text-red-600">
                          -{concept.decline_percent?.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Activity Chart */}
          {overview?.recent_activity && overview.recent_activity.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <AreaChart data={overview.recent_activity}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="_id" 
                      tickFormatter={(value) => format(parseISO(value), 'MMM d')}
                    />
                    <YAxis />
                    <Tooltip 
                      labelFormatter={(value) => format(parseISO(value), 'MMM d, yyyy')}
                    />
                    <Area 
                      type="monotone" 
                      dataKey="count" 
                      stroke="#3B82F6" 
                      fill="#93C5FD" 
                      name="Activity"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Top Concepts Tab */}
        <TabsContent value="top" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Top Concepts by Usage</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-3">
                  {topConcepts.map((concept, idx) => (
                    <Card key={concept.concept_id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className="text-2xl font-bold text-gray-400">
                            #{idx + 1}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="text-lg">{getEntityIcon(concept.entity_type)}</span>
                              <span className="font-semibold text-lg">{concept.display_name}</span>
                              <Badge variant="outline">{concept.entity_type}</Badge>
                            </div>
                            <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                              <span>Used {concept.count} times</span>
                              <span>•</span>
                              <span>Active {concept.days_active} days</span>
                              {concept.content_types && (
                                <>
                                  <span>•</span>
                                  <span>In {concept.content_types.join(', ')}</span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-2xl font-bold">{concept.count}</div>
                          <div className="text-sm text-gray-500">mentions</div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Velocity Leaders Tab */}
        <TabsContent value="velocity" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Concepts with Highest Growth Velocity</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-3">
                  {velocityLeaders.map((concept, _idx) => (
                    <Card key={concept.concept_id} className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Gauge className="h-5 w-5 text-orange-500" />
                            <span className="font-semibold text-lg">{concept.display_name}</span>
                            <Badge 
                              variant={concept.trend === 'accelerating' ? 'default' : 'secondary'}
                            >
                              {concept.trend}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-6 mt-2">
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">Previous:</span>
                              <span className="font-medium">{concept.previous_mentions}</span>
                            </div>
                            <ChevronRight className="h-4 w-4 text-gray-400" />
                            <div className="flex items-center gap-2">
                              <span className="text-sm text-gray-500">Current:</span>
                              <span className="font-medium">{concept.current_mentions}</span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center gap-2">
                            {concept.velocity_percent && concept.velocity_percent > 0 ? (
                              <TrendingUp className="h-6 w-6 text-green-500" />
                            ) : (
                              <TrendingDown className="h-6 w-6 text-red-500" />
                            )}
                            <span className="text-2xl font-bold">
                              {(concept.velocity_percent ?? 0) > 0 ? '+' : ''}{concept.velocity_percent?.toFixed(0)}%
                            </span>
                          </div>
                          <div className="text-sm text-gray-500">velocity</div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Rising Tab */}
        <TabsContent value="rising" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Rising Concepts</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-3">
                  {risingTrends.map((concept) => (
                    <Card key={concept.concept_id} className="p-4 border-l-4 border-l-green-500">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{getEntityIcon(concept.entity_type)}</span>
                            <span className="font-semibold text-lg">{concept.display_name}</span>
                            {concept.momentum && (
                              <Badge 
                                variant="default"
                                className={
                                  concept.momentum === 'explosive' ? 'bg-red-500' :
                                  concept.momentum === 'strong' ? 'bg-orange-500' :
                                  concept.momentum === 'moderate' ? 'bg-yellow-500' :
                                  'bg-green-500'
                                }
                              >
                                {concept.momentum}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 mt-2 text-sm">
                            <span className="text-gray-500">
                              {concept.previous_mentions || 0} → {concept.current_mentions} mentions
                            </span>
                            {concept.unique_sources && (
                              <>
                                <span className="text-gray-400">•</span>
                                <span className="text-gray-500">
                                  {concept.unique_sources} unique sources
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center gap-2">
                            <Flame className="h-6 w-6 text-orange-500" />
                            <span className="text-2xl font-bold text-green-600">
                              +{concept.growth_percent?.toFixed(0)}%
                            </span>
                          </div>
                          <div className="text-sm text-gray-500">growth</div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Declining Tab */}
        <TabsContent value="declining" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Declining Concepts</CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-3">
                  {decliningTrends.map((concept) => (
                    <Card key={concept.concept_id} className="p-4 border-l-4 border-l-red-500">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="text-lg">{getEntityIcon(concept.entity_type)}</span>
                            <span className="font-semibold text-lg">{concept.display_name}</span>
                            {concept.status && (
                              <Badge 
                                variant="secondary"
                                className={
                                  concept.status === 'fading' ? 'bg-red-100 text-red-700' :
                                  concept.status === 'declining' ? 'bg-orange-100 text-orange-700' :
                                  'bg-yellow-100 text-yellow-700'
                                }
                              >
                                {concept.status}
                              </Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-4 mt-2 text-sm">
                            <span className="text-gray-500">
                              {concept.previous_mentions} → {concept.current_mentions || 0} mentions
                            </span>
                            {concept.peak_day && (
                              <>
                                <span className="text-gray-400">•</span>
                                <span className="text-gray-500">
                                  Peak: {format(parseISO(concept.peak_day), 'MMM d')}
                                </span>
                              </>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="flex items-center gap-2">
                            <AlertCircle className="h-6 w-6 text-red-500" />
                            <span className="text-2xl font-bold text-red-600">
                              -{concept.decline_percent?.toFixed(0)}%
                            </span>
                          </div>
                          <div className="text-sm text-gray-500">decline</div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-6">
          {/* Timeline Controls */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Timeline Configuration</span>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    variant={comparisonMode ? "default" : "outline"}
                    onClick={() => setComparisonMode(!comparisonMode)}
                  >
                    {comparisonMode ? (
                      <>
                        <BarChart3 className="h-4 w-4 mr-1" />
                        Area Chart
                      </>
                    ) : (
                      <>
                        <Activity className="h-4 w-4 mr-1" />
                        Line Chart
                      </>
                    )}
                  </Button>
                </div>
              </CardTitle>
              <CardDescription>
                Compare specific concepts by selecting them, or view the overall top trending concepts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center gap-4">
                <div className="flex-1">
                  <label className="text-sm font-medium mb-2 block">
                    {selectedConcepts.length === 0 
                      ? "Select specific concepts to compare (or load top trending)" 
                      : `Selected ${selectedConcepts.length} concept${selectedConcepts.length !== 1 ? 's' : ''} for comparison`}
                  </label>
                  <ScrollArea className="h-[100px] border rounded-md p-2 bg-gray-50">
                    <div className="flex flex-wrap gap-2">
                      {availableConcepts.map(concept => (
                        <Badge
                          key={concept.concept_id}
                          variant={selectedConcepts.includes(concept.concept_id) ? "default" : "outline"}
                          className="cursor-pointer hover:scale-105 transition-transform"
                          onClick={() => {
                            if (selectedConcepts.includes(concept.concept_id)) {
                              setSelectedConcepts(prev => prev.filter(id => id !== concept.concept_id))
                            } else if (selectedConcepts.length < 5) {
                              setSelectedConcepts(prev => [...prev, concept.concept_id])
                            }
                          }}
                        >
                          {getEntityIcon(concept.entity_type)} {concept.display_name}
                          {concept.count && (
                            <span className="ml-1 text-xs opacity-70">({concept.count})</span>
                          )}
                          {selectedConcepts.includes(concept.concept_id) && (
                            <span className="ml-1">✓</span>
                          )}
                        </Badge>
                      ))}
                    </div>
                  </ScrollArea>
                  {selectedConcepts.length >= 5 && (
                    <p className="text-xs text-orange-500 mt-2">Maximum 5 concepts selected</p>
                  )}
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium">Granularity</label>
                  <Select value={timelineGranularity} onValueChange={setTimelineGranularity}>
                    <SelectTrigger className="w-32">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="daily">Daily</SelectItem>
                      <SelectItem value="weekly">Weekly</SelectItem>
                      <SelectItem value="monthly">Monthly</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <div className="text-sm text-gray-500">
                  {selectedConcepts.length > 0 
                    ? `Compare ${selectedConcepts.length} selected concept${selectedConcepts.length !== 1 ? 's' : ''}`
                    : 'Show top 5 trending concepts overall'}
                </div>
                <div className="flex gap-2">
                  {selectedConcepts.length > 0 && (
                    <Button 
                      variant="outline"
                      onClick={() => setSelectedConcepts([])}
                    >
                      Clear Selection
                    </Button>
                  )}
                  <Button 
                    onClick={loadTimelineData}
                    disabled={loadingTimeline}
                    variant={selectedConcepts.length > 0 ? "default" : "secondary"}
                  >
                    {loadingTimeline ? (
                      <>
                        <Clock className="h-4 w-4 mr-2 animate-spin" />
                        Loading...
                      </>
                    ) : selectedConcepts.length > 0 ? (
                      <>
                        <Target className="h-4 w-4 mr-2" />
                        Compare Selected
                      </>
                    ) : (
                      <>
                        <TrendingUp className="h-4 w-4 mr-2" />
                        Load Top Trending
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Timeline Chart */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Concept Activity Timeline</span>
                {timeline.length > 0 && (
                  <Badge variant="secondary">
                    Showing {timeline.length} concept{timeline.length !== 1 ? 's' : ''}
                  </Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingTimeline ? (
                <div className="flex items-center justify-center h-[400px]">
                  <Clock className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : timeline.length > 0 ? (
                <>
                  {/* Merge all timeline data into a single dataset for multi-series chart */}
                  {(() => {
                    // Create a merged dataset with all dates
                    const allDates = new Set<string>()
                    timeline.forEach(series => {
                      series.data.forEach(point => allDates.add(point.date))
                    })
                    
                    const sortedDates = Array.from(allDates).sort()
                    const mergedData = sortedDates.map(date => {
                      const dataPoint: any = { date }
                      timeline.forEach(series => {
                        const point = series.data.find(p => p.date === date)
                        dataPoint[series.name] = point ? point.value : 0
                      })
                      return dataPoint
                    })

                    return comparisonMode ? (
                      <ResponsiveContainer width="100%" height={400}>
                        <AreaChart data={mergedData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="date"
                            tickFormatter={(value) => {
                              try {
                                if (typeof value === 'string' && value.includes('W')) {
                                  return `Week ${value.split('-W')[1]}`
                                }
                                return format(parseISO(value), 'MMM d')
                              } catch {
                                return value
                              }
                            }}
                          />
                          <YAxis />
                          <Tooltip 
                            content={<CustomTooltip />}
                          />
                          <Legend 
                            wrapperStyle={{ 
                              paddingTop: '10px',
                              maxHeight: '60px',
                              overflowY: 'auto'
                            }}
                            iconType="line"
                          />
                          {timeline.map((series, idx) => (
                            <Area
                              key={series.concept_id}
                              type="monotone"
                              dataKey={series.name}
                              stackId="1"
                              stroke={COLORS[idx % COLORS.length]}
                              fill={COLORS[idx % COLORS.length]}
                              fillOpacity={0.6}
                            />
                          ))}
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <ResponsiveContainer width="100%" height={400}>
                        <LineChart data={mergedData}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis 
                            dataKey="date"
                            tickFormatter={(value) => {
                              try {
                                if (typeof value === 'string' && value.includes('W')) {
                                  return `Week ${value.split('-W')[1]}`
                                }
                                return format(parseISO(value), 'MMM d')
                              } catch {
                                return value
                              }
                            }}
                          />
                          <YAxis />
                          <Tooltip 
                            content={<CustomTooltip />}
                          />
                          <Legend 
                            wrapperStyle={{ 
                              paddingTop: '10px',
                              maxHeight: '60px',
                              overflowY: 'auto'
                            }}
                            iconType="line"
                          />
                          {timeline.map((series, idx) => (
                            <Line
                              key={series.concept_id}
                              type="monotone"
                              dataKey={series.name}
                              stroke={COLORS[idx % COLORS.length]}
                              strokeWidth={2}
                              dot={false}
                              connectNulls
                              activeDot={{ r: 6 }}
                            />
                          ))}
                        </LineChart>
                      </ResponsiveContainer>
                    )
                  })()}
                </>
              ) : (
                <div className="text-center py-8">
                  <Activity className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                  <p className="text-gray-500 mb-4">
                    No timeline data loaded yet
                  </p>
                  <p className="text-sm text-gray-400">
                    Select concepts and click "Load Timeline" to visualize trends
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Timeline Stats */}
          {timeline.length > 0 && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {timeline.slice(0, 3).map((series) => (
                <Card key={series.concept_id}>
                  <CardContent className="p-4">
                    <div className="font-semibold mb-2">{series.name}</div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Total:</span>
                        <span className="font-medium">{series.total}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Peak:</span>
                        <span className="font-medium">{series.peak_value}</span>
                      </div>
                      {series.peak_date && (
                        <div className="flex justify-between">
                          <span className="text-gray-500">Peak Date:</span>
                          <span className="font-medium">
                            {series.peak_date.includes('W') 
                              ? `Week ${series.peak_date.split('-W')[1]}`
                              : format(parseISO(series.peak_date), 'MMM d')
                            }
                          </span>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}