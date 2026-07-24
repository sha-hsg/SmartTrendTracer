import { useMemo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ZAxis
} from 'recharts'
import {
  Loader2,
  GitCompare
} from 'lucide-react'
import { CorrelationResponse } from './types'

interface TopicDetailPanelProps {
  loading: boolean
  correlationData: CorrelationResponse | null
}

export default function TopicDetailPanel({ loading, correlationData }: TopicDetailPanelProps) {
  const scatterData = useMemo(() => {
    if (!correlationData?.correlations?.length) return []

    return correlationData.correlations.map(c => ({
      x: c.topic1_count,
      y: c.topic2_count,
      z: c.co_occurrence * 10,
      name: `${c.topic1_name} + ${c.topic2_name}`,
      correlation: c.correlation,
      coOccurrence: c.co_occurrence
    }))
  }, [correlationData])

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-20">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    )
  }

  if (!correlationData?.correlations?.length) {
    return (
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
    )
  }

  return (
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
                formatter={(value: any, name?: string) => {
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
  )
}
