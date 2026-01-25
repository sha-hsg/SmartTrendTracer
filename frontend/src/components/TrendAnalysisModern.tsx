import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart
} from 'recharts'
import { 
  TrendingUp,
  TrendingDown,
  BarChart3,
  Activity,
  RefreshCw,
  Loader2,
  AlertCircle,
  Sparkles,
  Calendar,
  ArrowUp,
  ArrowDown,
  Zap,
  Flame,
  Users,
  FileText,
  BookOpen
} from 'lucide-react'

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
      const response = await axios.get(`http://localhost:8000/api/trends/analysis?days=${timeRange}`)
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

  const formatVelocity = (velocity: number): string => {
    if (velocity === 0) return '0%'
    const sign = velocity > 0 ? '+' : ''
    return `${sign}${velocity.toFixed(1)}%`
  }

  const getVelocityColor = (velocity: number) => {
    if (velocity > 20) return 'text-green-600 bg-green-50 border-green-200'
    if (velocity < -20) return 'text-red-600 bg-red-50 border-red-200'
    return 'text-gray-600 bg-gray-50 border-gray-200'
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

        <TabsContent value="overview" className="space-y-4">
          {/* Pie Chart for Content Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-purple-500" />
                Content Distribution
              </CardTitle>
              <CardDescription>Breakdown of content types analyzed</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={[
                      { name: 'Tweets', value: trendData.content_distribution.tweets, fill: '#3B82F6' },
                      { name: 'Articles', value: trendData.content_distribution.articles, fill: '#A855F7' },
                      { name: 'Papers', value: trendData.content_distribution.papers, fill: '#10B981' }
                    ]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {[
                      { fill: '#3B82F6' },
                      { fill: '#A855F7' },
                      { fill: '#10B981' }
                    ].map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Concepts with Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Zap className="h-5 w-5 text-yellow-500" />
                  Top Concepts
                </CardTitle>
                <CardDescription>Most mentioned concepts</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart 
                    data={trendData.top_concepts.slice(0, 5)}
                    layout="horizontal"
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis type="number" tick={{ fontSize: 12 }} />
                    <YAxis 
                      dataKey="display_name" 
                      type="category" 
                      tick={{ fontSize: 11 }}
                      width={120}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    />
                    <Bar dataKey="count" fill="#FBBF24" radius={[0, 8, 8, 0]} />
                  </BarChart>
                </ResponsiveContainer>
                
                <ScrollArea className="h-[200px] mt-4">
                  <div className="space-y-2">
                    {trendData.top_concepts.map((concept, index) => (
                      <div
                        key={concept.concept_id}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className="flex items-center justify-center w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-semibold text-sm">
                            {index + 1}
                          </div>
                          <div>
                            <p className="font-medium">{concept.display_name}</p>
                            {concept.entity_type && (
                              <p className="text-xs text-gray-500">{concept.entity_type}</p>
                            )}
                          </div>
                        </div>
                        <Badge variant="secondary">
                          {concept.count} mentions
                        </Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Velocity Leaders with Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Flame className="h-5 w-5 text-orange-500" />
                  Velocity Leaders
                </CardTitle>
                <CardDescription>Fastest changing concepts</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart 
                    data={trendData.concept_velocity.slice(0, 5)}
                    layout="horizontal"
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis type="number" tick={{ fontSize: 12 }} />
                    <YAxis 
                      dataKey="display_name" 
                      type="category" 
                      tick={{ fontSize: 11 }}
                      width={120}
                    />
                    <Tooltip 
                      contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    />
                    <Bar dataKey="velocity" radius={[0, 8, 8, 0]}>
                      {trendData.concept_velocity.slice(0, 5).map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`}
                          fill={entry.velocity > 0 ? '#10B981' : '#EF4444'}
                        />
                      ))}
                    </Bar>
                  </ComposedChart>
                </ResponsiveContainer>

                <ScrollArea className="h-[200px] mt-4">
                  <div className="space-y-2">
                    {trendData.concept_velocity.map((concept, _index) => (
                      <div
                        key={concept.concept_id}
                        className="flex items-center justify-between p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "h-8 w-8 rounded-full flex items-center justify-center",
                            concept.velocity > 0 ? "bg-green-100" : "bg-red-100"
                          )}>
                            {concept.velocity > 0 ? (
                              <ArrowUp className="h-4 w-4 text-green-600" />
                            ) : (
                              <ArrowDown className="h-4 w-4 text-red-600" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium">{concept.display_name}</p>
                            <p className="text-xs text-gray-500">
                              {concept.previous_count} → {concept.current_count}
                            </p>
                          </div>
                        </div>
                        <Badge className={cn(getVelocityColor(concept.velocity))}>
                          {formatVelocity(concept.velocity)}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="rising" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-green-500" />
                  Rising Concepts
                </CardTitle>
                <Badge variant="secondary" className="bg-green-50 text-green-700">
                  {trendData.trends.rising.length} concepts
                </Badge>
              </div>
              <CardDescription>Concepts gaining momentum</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {trendData.trends.rising.map((concept, index) => (
                  <div
                    key={concept.concept_id}
                    className="flex items-center justify-between p-4 rounded-lg border border-green-200 bg-green-50/50 hover:bg-green-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-green-100 text-green-700 font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-semibold">{concept.display_name}</p>
                        <p className="text-sm text-gray-600">
                          {concept.previous_count} → {concept.current_count} mentions
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-green-100 text-green-700 border-green-300">
                        {formatVelocity(concept.velocity)}
                      </Badge>
                      <TrendingUp className="h-5 w-5 text-green-600" />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="declining" className="space-y-4">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <TrendingDown className="h-5 w-5 text-red-500" />
                  Declining Concepts
                </CardTitle>
                <Badge variant="secondary" className="bg-red-50 text-red-700">
                  {trendData.trends.declining.length} concepts
                </Badge>
              </div>
              <CardDescription>Concepts losing traction</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {trendData.trends.declining.map((concept, index) => (
                  <div
                    key={concept.concept_id}
                    className="flex items-center justify-between p-4 rounded-lg border border-red-200 bg-red-50/50 hover:bg-red-50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-red-100 text-red-700 font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-semibold">{concept.display_name}</p>
                        <p className="text-sm text-gray-600">
                          {concept.previous_count} → {concept.current_count} mentions
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-red-100 text-red-700 border-red-300">
                        {formatVelocity(concept.velocity)}
                      </Badge>
                      <TrendingDown className="h-5 w-5 text-red-600" />
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="timeline" className="space-y-4">
          {/* Area Chart for Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-500" />
                Content Activity Over Time
              </CardTitle>
              <CardDescription>Daily distribution of tweets, articles, and papers</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={350}>
                <AreaChart data={trendData.timeline}>
                  <defs>
                    <linearGradient id="colorTweets" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorArticles" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#A855F7" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#A855F7" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorPapers" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    labelStyle={{ fontWeight: 'bold' }}
                  />
                  <Legend />
                  <Area type="monotone" dataKey="tweets" stackId="1" stroke="#3B82F6" fillOpacity={1} fill="url(#colorTweets)" />
                  <Area type="monotone" dataKey="articles" stackId="1" stroke="#A855F7" fillOpacity={1} fill="url(#colorArticles)" />
                  <Area type="monotone" dataKey="papers" stackId="1" stroke="#10B981" fillOpacity={1} fill="url(#colorPapers)" />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Line Chart for Unique Concepts */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-yellow-500" />
                Concept Diversity Trend
              </CardTitle>
              <CardDescription>Number of unique concepts used per day</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={trendData.timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    labelStyle={{ fontWeight: 'bold' }}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="unique_concepts" 
                    stroke="#FBBF24" 
                    strokeWidth={3}
                    dot={{ fill: '#F59E0B', r: 4 }}
                    activeDot={{ r: 6 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Bar Chart for Total Activity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-indigo-500" />
                Daily Activity Comparison
              </CardTitle>
              <CardDescription>Total content volume per day</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={trendData.timeline}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis 
                    dataKey="date" 
                    tick={{ fontSize: 12 }}
                    angle={-45}
                    textAnchor="end"
                    height={60}
                  />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px' }}
                    labelStyle={{ fontWeight: 'bold' }}
                  />
                  <Bar dataKey="total" fill="#6366F1" radius={[8, 8, 0, 0]}>
                    {trendData.timeline.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`}
                        fill={entry.total > (trendData.insights.total_content / trendData.timeline.length) ? '#10B981' : '#6366F1'}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Original Table View */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-blue-500" />
                Detailed Timeline
              </CardTitle>
              <CardDescription>Day-by-day breakdown</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-3">
                  {trendData.timeline.map((day) => (
                    <div
                      key={day.date}
                      className="p-4 rounded-lg border hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-3">
                        <p className="font-semibold">{day.date}</p>
                        <Badge variant="secondary">
                          {day.total} total items
                        </Badge>
                      </div>
                      <div className="grid grid-cols-3 gap-4 text-sm">
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-1">
                            <Users className="h-3 w-3 text-blue-500" />
                            Tweets
                          </span>
                          <span className="font-medium">{day.tweets}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-1">
                            <FileText className="h-3 w-3 text-purple-500" />
                            Articles
                          </span>
                          <span className="font-medium">{day.articles}</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="flex items-center gap-1">
                            <BookOpen className="h-3 w-3 text-green-500" />
                            Papers
                          </span>
                          <span className="font-medium">{day.papers}</span>
                        </div>
                      </div>
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-sm text-gray-500">
                          {day.unique_concepts} unique concepts used
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}