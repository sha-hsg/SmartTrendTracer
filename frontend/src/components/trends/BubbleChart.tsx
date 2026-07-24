/**
 * BubbleChart Component
 * Scatter chart showing concepts:
 * X = Days since first occurrence
 * Y = Velocity (% change)
 * Size = Volume (total count)
 * Color = Entity type
 */

import React, { useMemo, useState } from 'react';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ZoomIn, ZoomOut, RotateCcw, TrendingUp } from 'lucide-react';
import { BubbleDataPoint, BubbleChartData } from '../../types/trends';

interface BubbleChartProps {
  data: BubbleChartData | null;
  loading?: boolean;
  onBubbleClick?: (conceptId: string) => void;
}

interface TooltipPayload {
  payload: BubbleDataPoint;
}

const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: TooltipPayload[];
}> = ({ active, payload }) => {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0].payload;

  return (
    <div className="bg-white p-3 rounded-lg shadow-lg border max-w-xs">
      <div className="font-semibold text-sm">{data.display_name}</div>
      <div className="mt-2 space-y-1 text-xs text-muted-foreground">
        <div>Age: <span className="font-medium text-foreground">{data.x} days</span></div>
        <div>Velocity: <span className={`font-medium ${data.y > 0 ? 'text-green-600' : data.y < 0 ? 'text-red-600' : 'text-foreground'}`}>
          {data.y > 0 ? '+' : ''}{data.y}%
        </span></div>
        <div>Volume: <span className="font-medium text-foreground">{data.z} mentions</span></div>
        <div className="flex items-center">Type: <Badge variant="outline" className="text-[10px] ml-1">{data.entity_type}</Badge></div>
        <div className="text-[10px] mt-1">First seen: {new Date(data.first_seen).toLocaleDateString()}</div>
      </div>
    </div>
  );
};

const BubbleChart: React.FC<BubbleChartProps> = ({ data, loading, onBubbleClick }) => {
  const [zoomLevel, setZoomLevel] = useState(1);

  const chartData = useMemo(() => {
    if (!data?.data) return [];
    return data.data.map(d => ({
      ...d,
      // Normalize for better visualization
      x: d.x,
      y: d.y,
      z: Math.max(d.z, 5), // Minimum size for visibility
    }));
  }, [data]);

  const handleZoomIn = () => setZoomLevel(prev => Math.min(prev + 0.25, 2));
  const handleZoomOut = () => setZoomLevel(prev => Math.max(prev - 0.25, 0.5));
  const handleReset = () => setZoomLevel(1);

  if (loading) {
    return (
      <Card className="h-[500px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Concept Growth Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading chart data...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data || chartData.length === 0) {
    return (
      <Card className="h-[500px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Concept Growth Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <p className="text-muted-foreground">No data available</p>
        </CardContent>
      </Card>
    );
  }

  // Calculate axis ranges with zoom
  const xDomain = [
    Math.floor((data.x_range.min || 0) / zoomLevel),
    Math.ceil((data.x_range.max || 100) * zoomLevel),
  ];
  const yDomain = [
    Math.floor((data.y_range.min || -100) / zoomLevel),
    Math.ceil((data.y_range.max || 100) * zoomLevel),
  ];

  return (
    <Card className="h-[500px]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Concept Growth Analysis
          </CardTitle>
          <div className="flex items-center gap-1">
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleReset}>
              <RotateCcw className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <p className="text-xs text-muted-foreground">
          X: Days since first seen | Y: Growth velocity (%) | Size: Total mentions | Color: Entity type
        </p>
      </CardHeader>
      <CardContent className="h-[400px] min-h-[400px]">
        <ResponsiveContainer width="100%" height="100%" debounce={50}>
          <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 10 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              type="number"
              dataKey="x"
              name="Days"
              domain={xDomain}
              label={{ value: 'Days Since First Seen', position: 'bottom', offset: 0, fontSize: 12 }}
              tick={{ fontSize: 11 }}
            />
            <YAxis
              type="number"
              dataKey="y"
              name="Velocity"
              domain={yDomain}
              label={{ value: 'Velocity (%)', angle: -90, position: 'insideLeft', fontSize: 12 }}
              tick={{ fontSize: 11 }}
            />
            <ZAxis
              type="number"
              dataKey="z"
              range={[50, 400]}
              name="Volume"
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              formatter={(value) => value}
              wrapperStyle={{ paddingTop: '10px' }}
            />
            <Scatter
              data={chartData}
              onClick={(dataPoint) => {
                if (dataPoint && onBubbleClick) {
                  onBubbleClick(dataPoint.concept_id);
                }
              }}
            >
              {chartData.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={entry.color}
                  fillOpacity={0.7}
                  stroke={entry.color}
                  strokeWidth={1}
                  cursor="pointer"
                />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
};

export default BubbleChart;
