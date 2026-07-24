/**
 * TrendDashboardMain Component
 * Main orchestrating container for all trend visualizations
 * Provides tab-based navigation between different views
 */

import React, { useState, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import {
  RefreshCw,
  AlertCircle,
  Flame,
  Grid3X3,
  TrendingUp,
  Layers,
  Network,
  BarChart3,
  Settings,
  Clock,
  History,
} from 'lucide-react';

import TrendAtAGlance from './TrendAtAGlance';
import TopicHeatmap from './TopicHeatmap';
import BubbleChart from './BubbleChart';
import CorrelationMatrix from './CorrelationMatrix';
import TrendNetworkGraph from './TrendNetworkGraph';
import AnimatedTimeline from './AnimatedTimeline';
import TimeWindowAnalysis from './TimeWindowAnalysis';
import {
  useAtAGlanceData,
  useHeatmapData,
  useBubbleChartData,
  useCooccurrenceData,
  useNetworkGraphData,
  useAnimatedTimelineData,
} from './hooks/useTrendData';

interface TrendDashboardMainProps {
  onConceptClick?: (conceptId: string) => void;
}

type TabValue = 'overview' | 'heatmap' | 'bubble' | 'correlation' | 'network' | 'timeline' | 'lifecycle';

const TrendDashboardMain: React.FC<TrendDashboardMainProps> = ({ onConceptClick }) => {
  const [activeTab, setActiveTab] = useState<TabValue>('overview');
  const [timeRange, setTimeRange] = useState<number>(48); // hours for at-a-glance
  const [days, setDays] = useState<number>(30); // days for other views
  const [topN, setTopN] = useState<number>(20);
  const [showSettings, setShowSettings] = useState(false);

  // Fetch data for each view
  const atAGlance = useAtAGlanceData(timeRange, 2.5, 10);
  const heatmap = useHeatmapData(Math.min(days, 30), topN);
  const bubbleChart = useBubbleChartData(days, 50);
  const cooccurrence = useCooccurrenceData(days, 25, 2);
  const network = useNetworkGraphData(days, 2, 40);
  const timeline = useAnimatedTimelineData(days, 15);

  const handleRefresh = useCallback(() => {
    atAGlance.refetch();
    if (activeTab === 'heatmap') heatmap.refetch();
    if (activeTab === 'bubble') bubbleChart.refetch();
    if (activeTab === 'correlation') cooccurrence.refetch();
    if (activeTab === 'network') network.refetch();
    if (activeTab === 'timeline') timeline.refetch();
    // Lifecycle tab manages its own data refresh
  }, [activeTab, atAGlance, heatmap, bubbleChart, cooccurrence, network, timeline]);

  const handleRefreshAll = useCallback(async () => {
    await Promise.all([
      atAGlance.refetch(),
      heatmap.refetch(),
      bubbleChart.refetch(),
      cooccurrence.refetch(),
      network.refetch(),
      timeline.refetch(),
    ]);
  }, [atAGlance, heatmap, bubbleChart, cooccurrence, network, timeline]);

  const isLoading = atAGlance.loading || heatmap.loading || bubbleChart.loading ||
                    cooccurrence.loading || network.loading || timeline.loading;

  const errors = [
    atAGlance.error,
    heatmap.error,
    bubbleChart.error,
    cooccurrence.error,
    network.error,
    timeline.error,
  ].filter(Boolean);

  return (
    <div className="space-y-4 p-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Flame className="w-6 h-6 text-orange-500" />
            Trend Detection Dashboard
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Real-time analysis of trending topics across all content sources
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Time Range Selector */}
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <Select
              value={String(days)}
              onValueChange={(v) => setDays(Number(v))}
            >
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">7 days</SelectItem>
                <SelectItem value="14">14 days</SelectItem>
                <SelectItem value="30">30 days</SelectItem>
                <SelectItem value="60">60 days</SelectItem>
                <SelectItem value="90">90 days</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Settings Toggle */}
          <Button
            variant="outline"
            size="icon"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="w-4 h-4" />
          </Button>

          {/* Refresh Button */}
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Settings Panel */}
      {showSettings && (
        <Card className="bg-muted/50">
          <CardContent className="pt-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label>At-a-Glance Window (hours)</Label>
                <Select
                  value={String(timeRange)}
                  onValueChange={(v) => setTimeRange(Number(v))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="24">24 hours</SelectItem>
                    <SelectItem value="48">48 hours</SelectItem>
                    <SelectItem value="72">72 hours</SelectItem>
                    <SelectItem value="168">7 days</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label>Top N Concepts</Label>
                <Select
                  value={String(topN)}
                  onValueChange={(v) => setTopN(Number(v))}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="10">10 concepts</SelectItem>
                    <SelectItem value="20">20 concepts</SelectItem>
                    <SelectItem value="30">30 concepts</SelectItem>
                    <SelectItem value="50">50 concepts</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="flex items-end">
                <Button variant="secondary" onClick={handleRefreshAll} className="w-full">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Refresh All Data
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {errors.length > 0 && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error loading data</AlertTitle>
          <AlertDescription>{errors[0]}</AlertDescription>
        </Alert>
      )}

      {/* Main Content with Tabs */}
      <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as TabValue)}>
        <TabsList className="grid grid-cols-7 w-full max-w-4xl">
          <TabsTrigger value="overview" className="flex items-center gap-1">
            <Flame className="w-4 h-4" />
            <span className="hidden sm:inline">Overview</span>
          </TabsTrigger>
          <TabsTrigger value="heatmap" className="flex items-center gap-1">
            <Grid3X3 className="w-4 h-4" />
            <span className="hidden sm:inline">Heatmap</span>
          </TabsTrigger>
          <TabsTrigger value="bubble" className="flex items-center gap-1">
            <TrendingUp className="w-4 h-4" />
            <span className="hidden sm:inline">Bubble</span>
          </TabsTrigger>
          <TabsTrigger value="correlation" className="flex items-center gap-1">
            <Layers className="w-4 h-4" />
            <span className="hidden sm:inline">Correlation</span>
          </TabsTrigger>
          <TabsTrigger value="network" className="flex items-center gap-1">
            <Network className="w-4 h-4" />
            <span className="hidden sm:inline">Network</span>
          </TabsTrigger>
          <TabsTrigger value="timeline" className="flex items-center gap-1">
            <BarChart3 className="w-4 h-4" />
            <span className="hidden sm:inline">Timeline</span>
          </TabsTrigger>
          <TabsTrigger value="lifecycle" className="flex items-center gap-1">
            <History className="w-4 h-4" />
            <span className="hidden sm:inline">Lifecycle</span>
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-4">
          <TrendAtAGlance
            hotTopics={atAGlance.data?.hot_topics || []}
            declining={atAGlance.data?.declining || []}
            stable={atAGlance.data?.stable || []}
            anomalies={atAGlance.data?.anomalies || []}
            loading={atAGlance.loading}
            onConceptClick={onConceptClick}
          />

          {/* Summary Stats */}
          {atAGlance.data && (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardContent className="pt-4">
                  <div className="text-center">
                    <p className="text-3xl font-bold">{atAGlance.data.statistics.total_content}</p>
                    <p className="text-sm text-muted-foreground">Content items in {timeRange}h</p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-center">
                    <p className="text-3xl font-bold">{atAGlance.data.statistics.unique_concepts}</p>
                    <p className="text-sm text-muted-foreground">Active concepts</p>
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="pt-4">
                  <div className="text-center">
                    <p className={`text-3xl font-bold ${atAGlance.data.statistics.avg_velocity > 0 ? 'text-green-600' : atAGlance.data.statistics.avg_velocity < 0 ? 'text-red-600' : ''}`}>
                      {atAGlance.data.statistics.avg_velocity > 0 ? '+' : ''}{atAGlance.data.statistics.avg_velocity}%
                    </p>
                    <p className="text-sm text-muted-foreground">Average velocity</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        {/* Heatmap Tab */}
        <TabsContent value="heatmap" className="mt-4">
          <TopicHeatmap
            data={heatmap.data}
            loading={heatmap.loading}
            onCellClick={(conceptId, date) => {
              console.log('Heatmap cell clicked:', conceptId, date);
              onConceptClick?.(conceptId);
            }}
          />
        </TabsContent>

        {/* Bubble Chart Tab */}
        <TabsContent value="bubble" className="mt-4">
          <BubbleChart
            data={bubbleChart.data}
            loading={bubbleChart.loading}
            onBubbleClick={onConceptClick}
          />
        </TabsContent>

        {/* Correlation Tab */}
        <TabsContent value="correlation" className="mt-4">
          <CorrelationMatrix
            data={cooccurrence.data}
            loading={cooccurrence.loading}
            onPairClick={(aId, bId) => {
              console.log('Correlation pair clicked:', aId, bId);
              // Could filter to show content with both concepts
            }}
          />
        </TabsContent>

        {/* Network Tab */}
        <TabsContent value="network" className="mt-4">
          <TrendNetworkGraph
            data={network.data}
            loading={network.loading}
            onNodeClick={onConceptClick}
          />
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="mt-4">
          <AnimatedTimeline
            data={timeline.data}
            loading={timeline.loading}
            onConceptClick={onConceptClick}
          />
        </TabsContent>

        {/* Lifecycle Tab */}
        <TabsContent value="lifecycle" className="mt-4">
          <TimeWindowAnalysis
            onConceptClick={onConceptClick}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default TrendDashboardMain;
