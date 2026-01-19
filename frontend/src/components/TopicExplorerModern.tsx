import { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import {
  LineChart,
  Line,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis
} from 'recharts'
import {
  TrendingUp,
  RefreshCw,
  Loader2,
  AlertCircle,
  Hash,
  Twitter,
  FileText,
  BookOpen,
  ChevronDown,
  Check,
  X,
  Download,
  GitCompare,
  Sparkles,
  Search
} from 'lucide-react'

// Types
interface Topic {
  id: string
  name: string
  slug?: string
  count: number
  content_types?: string[]
  entity_type?: string
  color?: string
}

interface FrequencyDataPoint {
  date: string
  count: number
}

interface FrequencySeries {
  concept_id: string
  concept_name: string
  color: string
  data: FrequencyDataPoint[]
  total: number
}

interface FrequencyResponse {
  series: FrequencySeries[]
  time_range: { start: string; end: string }
  granularity: string
  source_types: string[]
}

interface Correlation {
  topic1_id: string
  topic1_name: string
  topic2_id: string
  topic2_name: string
  co_occurrence: number
  correlation: number
  topic1_count: number
  topic2_count: number
}

interface CorrelationResponse {
  topics: Topic[]
  correlations: Correlation[]
  source_types: string[]
  time_range: { start: string; end: string }
}

// Quick date range presets
const DATE_PRESETS = [
  { label: 'Last 30 Days', days: 30 },
  { label: 'Last 90 Days', days: 90 },
  { label: 'Last 6 Months', days: 180 },
  { label: 'Last Year', days: 365 },
  { label: 'All Time', days: 3650 }
]

export default function TopicExplorerModern() {
  // State
  const [activeTab, setActiveTab] = useState<'frequency' | 'correlation'>('frequency')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [selectedTopics, setSelectedTopics] = useState<Topic[]>([])
  const [availableTopics, setAvailableTopics] = useState<Topic[]>([])
  const [topicsLoading, setTopicsLoading] = useState(false)
  const [topicSearchOpen, setTopicSearchOpen] = useState(false)
  const [topicSearchQuery, setTopicSearchQuery] = useState('')
  const [highlightedIndex, setHighlightedIndex] = useState(-1)

  const [sourceTweets, setSourceTweets] = useState(true)
  const [sourceArticles, setSourceArticles] = useState(true)
  const [sourcePapers, setSourcePapers] = useState(true)

  const [datePreset, setDatePreset] = useState('90')
  const [granularity, setGranularity] = useState('week')

  // Data
  const [frequencyData, setFrequencyData] = useState<FrequencyResponse | null>(null)
  const [correlationData, setCorrelationData] = useState<CorrelationResponse | null>(null)

  // Computed source types
  const sourceTypes = useMemo(() => {
    const types: string[] = []
    if (sourceTweets) types.push('tweet')
    if (sourceArticles) types.push('article')
    if (sourcePapers) types.push('paper')
    return types.join(',')
  }, [sourceTweets, sourceArticles, sourcePapers])

  // Load popular topics on mount
  useEffect(() => {
    loadPopularTopics()
  }, [])

  const loadPopularTopics = async () => {
    setTopicsLoading(true)
    try {
      const response = await axios.get<{ topics: Topic[] }>('http://localhost:8000/api/topics/popular', {
        params: { source_types: 'tweet,article,paper', days: 365, limit: 100 }
      })
      setAvailableTopics(response.data.topics)
    } catch (err) {
      console.error('Failed to load topics:', err)
    } finally {
      setTopicsLoading(false)
    }
  }

  // Fetch frequency data
  const fetchFrequencyData = async () => {
    if (selectedTopics.length === 0) {
      setError('Please select at least one topic')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - parseInt(datePreset))

      const response = await axios.get<FrequencyResponse>('http://localhost:8000/api/topics/frequency', {
        params: {
          concept_ids: selectedTopics.map(t => t.id).join(','),
          source_types: sourceTypes,
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0],
          granularity
        }
      })
      setFrequencyData(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load frequency data')
    } finally {
      setLoading(false)
    }
  }

  // Fetch correlation data
  const fetchCorrelationData = async () => {
    setLoading(true)
    setError(null)

    try {
      const endDate = new Date()
      const startDate = new Date()
      startDate.setDate(startDate.getDate() - parseInt(datePreset))

      const response = await axios.get<CorrelationResponse>('http://localhost:8000/api/topics/correlation', {
        params: {
          source_types: sourceTypes,
          min_count: 5,
          start_date: startDate.toISOString().split('T')[0],
          end_date: endDate.toISOString().split('T')[0],
          limit: 50
        }
      })
      setCorrelationData(response.data)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load correlation data')
    } finally {
      setLoading(false)
    }
  }

  // Handle tab change
  const handleTabChange = (tab: string) => {
    setActiveTab(tab as 'frequency' | 'correlation')
    setError(null)
    if (tab === 'frequency' && selectedTopics.length > 0 && !frequencyData) {
      fetchFrequencyData()
    } else if (tab === 'correlation' && !correlationData) {
      fetchCorrelationData()
    }
  }

  // Handle analyze button
  const handleAnalyze = () => {
    if (activeTab === 'frequency') {
      fetchFrequencyData()
    } else {
      fetchCorrelationData()
    }
  }

  // Toggle topic selection
  const toggleTopic = (topic: Topic) => {
    if (selectedTopics.find(t => t.id === topic.id)) {
      setSelectedTopics(selectedTopics.filter(t => t.id !== topic.id))
    } else if (selectedTopics.length < 10) {
      setSelectedTopics([...selectedTopics, topic])
    }
  }

  // Remove topic from selection
  const removeTopic = (topicId: string) => {
    setSelectedTopics(selectedTopics.filter(t => t.id !== topicId))
  }

  // Handle keyboard navigation in topic search
  const handleTopicSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>, topics: Topic[]) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev =>
          prev < topics.length - 1 ? prev + 1 : prev
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => prev > 0 ? prev - 1 : -1)
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0 && highlightedIndex < topics.length) {
          toggleTopic(topics[highlightedIndex])
        }
        break
      case 'Escape':
        e.preventDefault()
        setTopicSearchOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  // Reset highlighted index when search changes
  useEffect(() => {
    setHighlightedIndex(-1)
  }, [topicSearchQuery])

  // Filter available topics by search
  const filteredTopics = useMemo(() => {
    if (!topicSearchQuery) return availableTopics.slice(0, 20)
    const query = topicSearchQuery.toLowerCase()
    return availableTopics
      .filter(t => t.name.toLowerCase().includes(query))
      .slice(0, 20)
  }, [availableTopics, topicSearchQuery])

  // Format frequency data for LineChart
  const lineChartData = useMemo(() => {
    if (!frequencyData?.series?.length) return []

    // Get all unique dates
    const allDates = new Set<string>()
    frequencyData.series.forEach(s => {
      s.data.forEach(d => allDates.add(d.date))
    })

    // Sort dates
    const sortedDates = Array.from(allDates).sort()

    // Build data points
    return sortedDates.map(date => {
      const point: any = { date }
      frequencyData.series.forEach(s => {
        const dataPoint = s.data.find(d => d.date === date)
        point[s.concept_name] = dataPoint?.count || 0
      })
      return point
    })
  }, [frequencyData])

  // Format correlation data for scatter plot
  const scatterData = useMemo(() => {
    if (!correlationData?.correlations?.length) return []

    return correlationData.correlations.map(c => ({
      x: c.topic1_count,
      y: c.topic2_count,
      z: c.co_occurrence * 10, // Scale for visibility
      name: `${c.topic1_name} + ${c.topic2_name}`,
      correlation: c.correlation,
      coOccurrence: c.co_occurrence
    }))
  }, [correlationData])

  // Export frequency data as CSV
  const exportFrequencyCSV = () => {
    if (!frequencyData?.series?.length) return

    const headers = ['Date', ...frequencyData.series.map(s => s.concept_name)]
    const rows = lineChartData.map(row => {
      const values = [row.date]
      frequencyData.series.forEach(s => {
        values.push(row[s.concept_name] || 0)
      })
      return values.join(',')
    })

    const csv = [headers.join(','), ...rows].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `topic-frequency-${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <Sparkles className="h-8 w-8 text-indigo-600" />
            Topic Explorer
          </h1>
          <p className="text-muted-foreground mt-1">
            Analyze topic trends over time and discover correlations
          </p>
        </div>
        <div className="flex gap-2">
          {frequencyData && activeTab === 'frequency' && (
            <Button variant="outline" onClick={exportFrequencyCSV}>
              <Download className="h-4 w-4 mr-2" />
              Export CSV
            </Button>
          )}
          <Button onClick={handleAnalyze} disabled={loading}>
            {loading ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <RefreshCw className="h-4 w-4 mr-2" />
            )}
            Analyze
          </Button>
        </div>
      </div>

      {/* Filters Panel */}
      <Card>
        <CardHeader className="pb-4">
          <CardTitle className="text-lg">Filters</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Topic Selector */}
          <div className="space-y-2">
            <Label>Topics (select up to 10)</Label>
            <div className="flex flex-wrap gap-2 mb-2">
              {selectedTopics.map(topic => (
                <Badge
                  key={topic.id}
                  variant="secondary"
                  className="flex items-center gap-1 px-3 py-1"
                >
                  <span style={{ color: topic.color }}>{topic.name}</span>
                  <button
                    onClick={() => removeTopic(topic.id)}
                    className="ml-1 hover:text-destructive"
                  >
                    <X className="h-3 w-3" />
                  </button>
                </Badge>
              ))}
              {selectedTopics.length === 0 && (
                <span className="text-sm text-muted-foreground">No topics selected</span>
              )}
            </div>
            <Popover open={topicSearchOpen} onOpenChange={setTopicSearchOpen}>
              <PopoverTrigger asChild>
                <Button variant="outline" className="w-full justify-between">
                  <span className="flex items-center gap-2">
                    <Hash className="h-4 w-4" />
                    Add topics...
                  </span>
                  <ChevronDown className="h-4 w-4 opacity-50" />
                </Button>
              </PopoverTrigger>
              <PopoverContent className="w-[400px] p-0" align="start">
                <div className="flex flex-col">
                  {/* Search Input */}
                  <div className="flex items-center border-b px-3">
                    <Search className="mr-2 h-4 w-4 shrink-0 opacity-50" />
                    <input
                      type="text"
                      placeholder="Search topics... (↑↓ to navigate, Enter to select)"
                      value={topicSearchQuery}
                      onChange={(e) => setTopicSearchQuery(e.target.value)}
                      onKeyDown={(e) => handleTopicSearchKeyDown(e, filteredTopics)}
                      className="flex h-11 w-full rounded-md bg-transparent py-3 text-sm outline-none placeholder:text-muted-foreground"
                      autoFocus
                    />
                  </div>
                  {/* Topic List */}
                  <div className="max-h-[300px] overflow-y-auto p-1">
                    {topicsLoading ? (
                      <p className="py-6 text-center text-sm text-muted-foreground">Loading topics...</p>
                    ) : filteredTopics.length === 0 ? (
                      <p className="py-6 text-center text-sm text-muted-foreground">No topics found.</p>
                    ) : (
                      <>
                        <p className="px-2 py-1.5 text-xs font-medium text-muted-foreground">Popular Topics</p>
                        {filteredTopics.map((topic, index) => (
                          <div
                            key={topic.id}
                            onClick={() => toggleTopic(topic)}
                            className={`flex cursor-pointer items-center justify-between rounded-sm px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground ${
                              index === highlightedIndex ? 'bg-accent text-accent-foreground' : ''
                            }`}
                          >
                            <span className="flex items-center gap-2">
                              {selectedTopics.find(t => t.id === topic.id) ? (
                                <Check className="h-4 w-4 text-primary" />
                              ) : (
                                <Hash className="h-4 w-4 text-muted-foreground" />
                              )}
                              {topic.name}
                            </span>
                            <Badge variant="outline" className="ml-2">
                              {topic.count}
                            </Badge>
                          </div>
                        ))}
                      </>
                    )}
                  </div>
                </div>
              </PopoverContent>
            </Popover>
          </div>

          {/* Source Types */}
          <div className="space-y-2">
            <Label>Content Sources</Label>
            <div className="flex gap-4">
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="source-tweets"
                  checked={sourceTweets}
                  onCheckedChange={(checked) => setSourceTweets(checked as boolean)}
                />
                <label htmlFor="source-tweets" className="text-sm font-medium flex items-center gap-1 cursor-pointer">
                  <Twitter className="h-4 w-4 text-blue-500" />
                  Tweets
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="source-articles"
                  checked={sourceArticles}
                  onCheckedChange={(checked) => setSourceArticles(checked as boolean)}
                />
                <label htmlFor="source-articles" className="text-sm font-medium flex items-center gap-1 cursor-pointer">
                  <FileText className="h-4 w-4 text-purple-500" />
                  Articles
                </label>
              </div>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="source-papers"
                  checked={sourcePapers}
                  onCheckedChange={(checked) => setSourcePapers(checked as boolean)}
                />
                <label htmlFor="source-papers" className="text-sm font-medium flex items-center gap-1 cursor-pointer">
                  <BookOpen className="h-4 w-4 text-green-500" />
                  Papers
                </label>
              </div>
            </div>
          </div>

          {/* Date Range and Granularity */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Time Period</Label>
              <Select value={datePreset} onValueChange={setDatePreset}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {DATE_PRESETS.map(preset => (
                    <SelectItem key={preset.days} value={preset.days.toString()}>
                      {preset.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Granularity</Label>
              <Select value={granularity} onValueChange={setGranularity}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="day">Daily</SelectItem>
                  <SelectItem value="week">Weekly</SelectItem>
                  <SelectItem value="month">Monthly</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Message */}
      {error && (
        <Card className="border-destructive bg-destructive/10">
          <CardContent className="flex items-center gap-2 py-4">
            <AlertCircle className="h-5 w-5 text-destructive" />
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Visualization Tabs */}
      <Tabs value={activeTab} onValueChange={handleTabChange}>
        <TabsList className="grid w-full grid-cols-2 max-w-md">
          <TabsTrigger value="frequency" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Frequency Over Time
          </TabsTrigger>
          <TabsTrigger value="correlation" className="flex items-center gap-2">
            <GitCompare className="h-4 w-4" />
            Topic Correlations
          </TabsTrigger>
        </TabsList>

        {/* Frequency Tab */}
        <TabsContent value="frequency" className="space-y-4">
          {loading ? (
            <Card>
              <CardContent className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </CardContent>
            </Card>
          ) : frequencyData?.series?.length ? (
            <>
              {/* Line Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="h-5 w-5 text-blue-500" />
                    Topic Frequency Over Time
                  </CardTitle>
                  <CardDescription>
                    {frequencyData.time_range.start} to {frequencyData.time_range.end} ({granularity}ly)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <LineChart data={lineChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="date"
                        tick={{ fontSize: 12 }}
                        tickFormatter={(value) => {
                          const date = new Date(value)
                          return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                        }}
                      />
                      <YAxis tick={{ fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px'
                        }}
                        labelFormatter={(value) => new Date(value).toLocaleDateString()}
                      />
                      <Legend />
                      {frequencyData.series.map(series => (
                        <Line
                          key={series.concept_id}
                          type="monotone"
                          dataKey={series.concept_name}
                          stroke={series.color}
                          strokeWidth={2}
                          dot={{ fill: series.color, strokeWidth: 2, r: 4 }}
                          activeDot={{ r: 6 }}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Statistics Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {frequencyData.series.map(series => (
                  <Card key={series.concept_id}>
                    <CardContent className="pt-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Total mentions</p>
                          <p className="text-2xl font-bold" style={{ color: series.color }}>
                            {series.total}
                          </p>
                        </div>
                        <Badge
                          variant="secondary"
                          style={{ backgroundColor: `${series.color}20`, color: series.color }}
                        >
                          {series.concept_name}
                        </Badge>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </>
          ) : selectedTopics.length > 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-20 text-center">
                <TrendingUp className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  Click "Analyze" to generate the frequency chart
                </p>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-20 text-center">
                <Hash className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  Select topics above to analyze their frequency over time
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Correlation Tab */}
        <TabsContent value="correlation" className="space-y-4">
          {loading ? (
            <Card>
              <CardContent className="flex items-center justify-center py-20">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </CardContent>
            </Card>
          ) : correlationData?.correlations?.length ? (
            <>
              {/* Scatter Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <GitCompare className="h-5 w-5 text-purple-500" />
                    Topic Co-occurrence
                  </CardTitle>
                  <CardDescription>
                    Each point represents a pair of topics that appear together.
                    Size indicates how often they co-occur.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={400}>
                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        type="number"
                        dataKey="x"
                        name="Topic 1 Count"
                        tick={{ fontSize: 12 }}
                        label={{ value: 'Topic 1 Mentions', position: 'bottom', offset: 0 }}
                      />
                      <YAxis
                        type="number"
                        dataKey="y"
                        name="Topic 2 Count"
                        tick={{ fontSize: 12 }}
                        label={{ value: 'Topic 2 Mentions', angle: -90, position: 'left' }}
                      />
                      <ZAxis type="number" dataKey="z" range={[50, 400]} />
                      <Tooltip
                        cursor={{ strokeDasharray: '3 3' }}
                        contentStyle={{
                          backgroundColor: 'white',
                          border: '1px solid #e5e7eb',
                          borderRadius: '8px'
                        }}
                        formatter={(value: any, name: string) => {
                          if (name === 'Topic 1 Count' || name === 'Topic 2 Count') {
                            return [value, name]
                          }
                          return null
                        }}
                        labelFormatter={(label: any, payload: any) => {
                          if (payload?.[0]?.payload) {
                            const data = payload[0].payload
                            return (
                              <div>
                                <strong>{data.name}</strong>
                                <br />
                                Co-occurrences: {data.coOccurrence}
                                <br />
                                Correlation: {(data.correlation * 100).toFixed(1)}%
                              </div>
                            )
                          }
                          return label
                        }}
                      />
                      <Scatter
                        name="Topic Pairs"
                        data={scatterData}
                        fill="#8884d8"
                        fillOpacity={0.6}
                      />
                    </ScatterChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Top Correlations Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Top Topic Correlations</CardTitle>
                  <CardDescription>
                    Pairs of topics that frequently appear together
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-2">
                      {correlationData.correlations.slice(0, 20).map((corr, idx) => (
                        <div
                          key={`${corr.topic1_id}-${corr.topic2_id}`}
                          className="flex items-center justify-between p-3 rounded-lg border hover:bg-muted/50 transition-colors"
                        >
                          <div className="flex items-center gap-3">
                            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-purple-100 text-purple-700 font-semibold text-sm">
                              {idx + 1}
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <Badge variant="secondary">{corr.topic1_name}</Badge>
                                <span className="text-muted-foreground">+</span>
                                <Badge variant="secondary">{corr.topic2_name}</Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">
                                {corr.co_occurrence} co-occurrences
                              </p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-semibold text-purple-600">
                              {(corr.correlation * 100).toFixed(1)}%
                            </p>
                            <p className="text-xs text-muted-foreground">correlation</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-20 text-center">
                <GitCompare className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground mb-4">
                  Click "Analyze" to discover topic correlations
                </p>
                <p className="text-sm text-muted-foreground">
                  This analysis shows which topics frequently appear together in your content
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
