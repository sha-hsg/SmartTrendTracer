import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  TrendingUp,
  BarChart3,
  Activity,
  Clock,
  Target
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
import { ConceptTrend, TrendOverview, getEntityIcon } from './TrendCards'

export interface TimelineData {
  concept_id: string
  name: string
  data: Array<{ date: string; value: number }>
  total: number
  peak_value: number
  peak_date: string
}

const COLORS = [
  '#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6',
  '#EC4899', '#06B6D4', '#F97316', '#6366F1', '#14B8A6'
]

function CustomTooltip({ active, payload, label }: any) {
  if (active && payload && payload.length) {
    const total = payload.reduce((sum: number, entry: any) => sum + (entry.value || 0), 0)
    return (
      <div className="bg-white p-3 border rounded-lg shadow-lg max-w-xs">
        <p className="font-medium mb-2">
          {(() => {
            try {
              if (typeof label === 'string' && label.includes('W')) {
                return `Week ${label.split('-W')[1]}`
              }
              return format(parseISO(label), 'MMM d, yyyy')
            } catch {
              return label
            }
          })()}
        </p>
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

export function ActivityChart({ overview }: { overview: TrendOverview }) {
  if (!overview.recent_activity || overview.recent_activity.length === 0) {
    return null
  }

  return (
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
  )
}

interface TimelineTabProps {
  timeline: TimelineData[]
  loadingTimeline: boolean
  comparisonMode: boolean
  setComparisonMode: (v: boolean) => void
  selectedConcepts: string[]
  setSelectedConcepts: (v: string[] | ((prev: string[]) => string[])) => void
  availableConcepts: ConceptTrend[]
  timelineGranularity: string
  setTimelineGranularity: (v: string) => void
  loadTimelineData: () => void
}

export function TimelineTab({
  timeline,
  loadingTimeline,
  comparisonMode,
  setComparisonMode,
  selectedConcepts,
  setSelectedConcepts,
  availableConcepts,
  timelineGranularity,
  setTimelineGranularity,
  loadTimelineData
}: TimelineTabProps) {
  return (
    <div className="space-y-6">
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
                          setSelectedConcepts((prev: string[]) => prev.filter(id => id !== concept.concept_id))
                        } else if (selectedConcepts.length < 5) {
                          setSelectedConcepts((prev: string[]) => [...prev, concept.concept_id])
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
              {(() => {
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

                const tickFormatter = (value: string) => {
                  try {
                    if (typeof value === 'string' && value.includes('W')) {
                      return `Week ${value.split('-W')[1]}`
                    }
                    return format(parseISO(value), 'MMM d')
                  } catch {
                    return value
                  }
                }

                const legendStyle = {
                  paddingTop: '10px',
                  maxHeight: '60px',
                  overflowY: 'auto' as const
                }

                return comparisonMode ? (
                  <ResponsiveContainer width="100%" height={400}>
                    <AreaChart data={mergedData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tickFormatter={tickFormatter} />
                      <YAxis />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={legendStyle} iconType="line" />
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
                      <XAxis dataKey="date" tickFormatter={tickFormatter} />
                      <YAxis />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={legendStyle} iconType="line" />
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
    </div>
  )
}
