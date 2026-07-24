import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { CardContent } from '@/components/ui/card'
import {
  ConceptTrend,
  TrendOverview,
  SummaryStatsCards,
  OverviewMiniCards,
  TopConceptsTab,
  VelocityLeadersTab,
  RisingTab,
  DecliningTab
} from './TrendCards'
import { TimelineData, ActivityChart, TimelineTab } from './TrendCharts'

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
      const overviewRes = await axios.get(`/api/trends/analysis/overview?days=${days}`)
      setOverview(overviewRes.data)

      // Load detailed data for each view
      const [topRes, velocityRes, risingRes, decliningRes] = await Promise.all([
        axios.get(`/api/trends/analysis/top-concepts?days=${days}&limit=20`),
        axios.get(`/api/trends/analysis/velocity-leaders?days=${days}&limit=20`),
        axios.get(`/api/trends/analysis/rising?days=${days}&limit=20`),
        axios.get(`/api/trends/analysis/declining?days=${days}&limit=20`)
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
          `/api/trends/analysis/timeline?${params.toString()}`
        )
        setTimeline(timelineRes.data.timeline || [])
      } else {
        // Load top concepts overall (limited by backend)
        const timelineRes = await axios.get(`/api/trends/analysis/timeline`, {
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
      {overview && <SummaryStatsCards overview={overview} />}

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
          <OverviewMiniCards overview={overview} />
          {overview && <ActivityChart overview={overview} />}
        </TabsContent>

        {/* Top Concepts Tab */}
        <TabsContent value="top" className="space-y-6">
          <TopConceptsTab topConcepts={topConcepts} />
        </TabsContent>

        {/* Velocity Leaders Tab */}
        <TabsContent value="velocity" className="space-y-6">
          <VelocityLeadersTab velocityLeaders={velocityLeaders} />
        </TabsContent>

        {/* Rising Tab */}
        <TabsContent value="rising" className="space-y-6">
          <RisingTab risingTrends={risingTrends} />
        </TabsContent>

        {/* Declining Tab */}
        <TabsContent value="declining" className="space-y-6">
          <DecliningTab decliningTrends={decliningTrends} />
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline">
          <TimelineTab
            timeline={timeline}
            loadingTimeline={loadingTimeline}
            comparisonMode={comparisonMode}
            setComparisonMode={setComparisonMode}
            selectedConcepts={selectedConcepts}
            setSelectedConcepts={setSelectedConcepts}
            availableConcepts={availableConcepts}
            timelineGranularity={timelineGranularity}
            setTimelineGranularity={setTimelineGranularity}
            loadTimelineData={loadTimelineData}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}
