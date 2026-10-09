/**
 * BubbleChart Component
 * Concept age against growth (data: /bubble-chart, app.services.trend_core):
 * X = days since the concept first occurred (log)
 * Y = growth factor of the window against the concept's own baseline (log, 1 = usual)
 * Size = items in the window, colour = dominant channel
 * Top left = young and growing.
 */

import React, { useMemo } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp } from 'lucide-react';
import { BubbleDataPoint, BubbleChartData } from '../../types/trends';

interface BubbleChartProps {
  data: BubbleChartData | null;
  loading?: boolean;
  onBubbleClick?: (conceptId: string) => void;
}

const CHANNELS: { key: 'tweet' | 'article' | 'paper'; label: string; color: string }[] = [
  { key: 'tweet', label: 'mostly tweets', color: '#3b82f6' },
  { key: 'article', label: 'mostly articles', color: '#f59e0b' },
  { key: 'paper', label: 'mostly papers', color: '#10b981' },
];

const CustomTooltip: React.FC<{ active?: boolean; payload?: { payload: BubbleDataPoint }[] }> = ({ active, payload }) => {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0].payload;
  return (
    <div className="bg-popover text-popover-foreground p-3 rounded-lg shadow-lg border max-w-xs">
      <div className="font-semibold text-sm">{d.display_name}</div>
      <div className="mt-2 space-y-1 text-xs text-muted-foreground">
        <div>Growth: <span className="font-medium text-foreground">×{d.y}</span> its usual level
          {d.expected !== undefined && ` (usual ${d.expected}, now ${d.z})`}</div>
        <div>Age: <span className="font-medium text-foreground">{d.x} days</span> (first seen {d.first_seen})</div>
        <div>Items in window: <span className="font-medium text-foreground">{d.z}</span>
          {d.channel && ` · ${CHANNELS.find(c => c.key === d.channel)?.label}`}</div>
      </div>
    </div>
  );
};

const BubbleChart: React.FC<BubbleChartProps> = ({ data, loading, onBubbleClick }) => {
  const chartData = useMemo(() => (data?.data || []).map(d => ({ ...d, y: Math.max(d.y, 0.05) })), [data]);
  // label the clearest risers and the biggest bubbles
  const labelled = useMemo(() => {
    const byZ = [...chartData].sort((a, b) => (b.z_score ?? 0) - (a.z_score ?? 0)).slice(0, 8);
    const bySize = [...chartData].sort((a, b) => b.z - a.z).slice(0, 4);
    return new Set([...byZ, ...bySize].map(d => d.concept_id));
  }, [chartData]);

  const title = (
    <CardTitle className="flex items-center gap-2">
      <TrendingUp className="w-5 h-5" />
      Concept Growth Analysis
    </CardTitle>
  );

  if (loading) {
    return (
      <Card className="h-[540px]">
        <CardHeader>{title}</CardHeader>
        <CardContent className="h-[440px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading chart data...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data || chartData.length === 0) {
    return (
      <Card className="h-[540px]">
        <CardHeader>{title}</CardHeader>
        <CardContent className="h-[440px] flex items-center justify-center">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  const yMax = Math.max(4, ...chartData.map(d => d.y)) * 1.3;
  const yMin = Math.min(0.25, ...chartData.map(d => d.y)) / 1.3;
  const xMax = Math.max(30, ...chartData.map(d => d.x)) * 1.3;
  const zMax = Math.max(1, ...chartData.map(d => d.z));

  return (
    <Card className="h-[540px]">
      <CardHeader className="pb-2">
        {title}
        <p className="text-xs text-muted-foreground">
          X: age (days since first seen, log) · Y: growth against the concept's own usual level (log; dashed line = usual)
          · Size: items in the window · Top left = young and growing{data.data_through ? ` · data through ${data.data_through}` : ''}
        </p>
        <div className="flex gap-3 text-xs text-muted-foreground">
          {CHANNELS.map(c => (
            <span key={c.key} className="flex items-center gap-1">
              <span className="inline-block w-3 h-3 rounded-full" style={{ background: c.color }} />{c.label}
            </span>
          ))}
        </div>
      </CardHeader>
      <CardContent className="h-[420px] min-h-[420px]">
        <ResponsiveContainer width="100%" height="100%" debounce={50}>
          <ScatterChart margin={{ top: 20, right: 40, bottom: 24, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis type="number" dataKey="x" name="Age" scale="log" domain={[1, xMax]} allowDataOverflow
              ticks={[1, 7, 30, 90, 365, 1000, 3000].filter(t => t <= xMax)}
              label={{ value: 'Days since first seen', position: 'bottom', offset: 4, fontSize: 12 }}
              tick={{ fontSize: 11 }} />
            <YAxis type="number" dataKey="y" name="Growth" scale="log" domain={[yMin, yMax]} allowDataOverflow
              ticks={[0.25, 0.5, 1, 2, 4, 8, 16, 32, 64].filter(t => t >= yMin && t <= yMax)}
              tickFormatter={v => `×${v}`}
              label={{ value: 'Growth vs. usual', angle: -90, position: 'insideLeft', fontSize: 12 }}
              tick={{ fontSize: 11 }} />
            <ReferenceLine y={1} stroke="#8c959f" strokeDasharray="4 4" />
            <Tooltip content={<CustomTooltip />} />
            <Scatter data={chartData} onClick={(p) => p && onBubbleClick?.(p.concept_id)}
              shape={(props: any) => {
                const d = props.payload as BubbleDataPoint;
                const r = 4 + 18 * Math.sqrt(d.z / zMax);
                return (
                  <g cursor="pointer">
                    <circle cx={props.cx} cy={props.cy} r={r} fill={d.color} fillOpacity={0.6} stroke={d.color} />
                    {labelled.has(d.concept_id) && (
                      <text x={props.cx + r + 3} y={props.cy + 3} fontSize={10} className="fill-foreground">{d.display_name}</text>
                    )}
                  </g>
                );
              }} />
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default BubbleChart;
