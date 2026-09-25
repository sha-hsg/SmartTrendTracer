import { useState, useEffect, useMemo } from 'react'
import http from '@/services/http'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts'
import {
  TrendingUp,
  RefreshCw,
  Loader2,
  AlertCircle,
  Hash,
  Download,
  GitCompare,
  Sparkles,
} from 'lucide-react'
import TopicDetailPanel from './TopicDetailPanel'
import TopicFiltersPanel from './TopicFiltersPanel'
import { Topic, FrequencyResponse, CorrelationResponse } from './types'

export default function TopicExplorerModern() {
  // State
  const [activeTab, setActiveTab] = useState<'frequency' | 'correlation'>('frequency')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Filters
  const [selectedTopics, setSelectedTopics] = useState<Topic[]>([])
  const [availableTopics, setAvailableTopics] = useState<Topic[]>([])
  const [topicsLoading, setTopicsLoading] = useState(false)

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
      const response = await http.get<{ topics: Topic[] }>('/api/topics/popular', {
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

      const response = await http.get<FrequencyResponse>('/api/topics/frequency', {
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

      const response = await http.get<CorrelationResponse>('/api/topics/correlation', {
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

  // Format frequency data for LineChart
  const lineChartData = useMemo(() => {
    if (!frequencyData?.series?.length) return []

    const allDates = new Set<string>()
    frequencyData.series.forEach(s => {
      s.data.forEach(d => allDates.add(d.date))
    })

    const sortedDates = Array.from(allDates).sort()

    return sortedDates.map(date => {
      const point: any = { date }
      frequencyData.series.forEach(s => {
        const dataPoint = s.data.find(d => d.date === date)
        point[s.concept_name] = dataPoint?.count || 0
      })
      return point
    })
  }, [frequencyData])

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
      <TopicFiltersPanel
        selectedTopics={selectedTopics}
        availableTopics={availableTopics}
        topicsLoading={topicsLoading}
        sourceTweets={sourceTweets}
        sourceArticles={sourceArticles}
        sourcePapers={sourcePapers}
        datePreset={datePreset}
        granularity={granularity}
        onToggleTopic={toggleTopic}
        onRemoveTopic={removeTopic}
        onSourceTweetsChange={setSourceTweets}
        onSourceArticlesChange={setSourceArticles}
        onSourcePapersChange={setSourcePapers}
        onDatePresetChange={setDatePreset}
        onGranularityChange={setGranularity}
      />

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
          <TopicDetailPanel loading={loading} correlationData={correlationData} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
