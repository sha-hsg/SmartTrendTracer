import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import {
  TrendingUp,
  TrendingDown,
  Zap,
  BarChart3,
  Activity,
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
import { format, parseISO } from 'date-fns'

export interface ConceptTrend {
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

export interface TrendOverview {
  summary: {
    total_annotations: number
    unique_concepts: number
    daily_average: number
    content_distribution: Record<string, number>
  }
  top_concepts: ConceptTrend[]
  velocity_leaders: ConceptTrend[]
  rising: ConceptTrend[]
  declining: ConceptTrend[]
  recent_activity: Array<{ _id: string; count: number }>
}

export const getEntityIcon = (entityType: string) => {
  switch (entityType) {
    case 'person': return '👤'
    case 'organisation': return '🏢'
    case 'location': return '📍'
    case 'event': return '📅'
    case 'technology': return '💻'
    default: return '🏷️'
  }
}

export const getTrendIcon = (trend: string) => {
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

export const formatNumber = (num: number) => {
  if (num >= 1000) return `${(num / 1000).toFixed(1)}k`
  return num.toString()
}

export function SummaryStatsCards({ overview }: { overview: TrendOverview }) {
  return (
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
  )
}

export function OverviewMiniCards({ overview }: { overview: TrendOverview | null }) {
  return (
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
  )
}

export function TopConceptsTab({ topConcepts }: { topConcepts: ConceptTrend[] }) {
  return (
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
  )
}

export function VelocityLeadersTab({ velocityLeaders }: { velocityLeaders: ConceptTrend[] }) {
  return (
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
  )
}

export function RisingTab({ risingTrends }: { risingTrends: ConceptTrend[] }) {
  return (
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
  )
}

export function DecliningTab({ decliningTrends }: { decliningTrends: ConceptTrend[] }) {
  return (
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
  )
}
