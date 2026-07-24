/**
 * TopicHeatmap Component
 * Matrix visualization: Concepts (rows) × Dates (columns)
 * Color intensity represents activity level
 */

import React, { useMemo, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Grid3X3, Calendar, Hash } from 'lucide-react';
import { HeatmapData } from '../../types/trends';

interface TopicHeatmapProps {
  data: HeatmapData | null;
  loading?: boolean;
  onCellClick?: (conceptId: string, date: string) => void;
}

const getHeatColor = (value: number, maxValue: number): string => {
  if (value === 0) return 'bg-gray-50';
  const intensity = Math.min(value / (maxValue || 1), 1);

  if (intensity < 0.2) return 'bg-blue-100';
  if (intensity < 0.4) return 'bg-blue-200';
  if (intensity < 0.6) return 'bg-blue-400';
  if (intensity < 0.8) return 'bg-blue-500';
  return 'bg-blue-600';
};

const getTextColor = (value: number, maxValue: number): string => {
  if (value === 0) return 'text-gray-400';
  const intensity = value / (maxValue || 1);
  return intensity > 0.5 ? 'text-white' : 'text-blue-900';
};

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const TopicHeatmap: React.FC<TopicHeatmapProps> = ({ data, loading, onCellClick }) => {
  const [hoveredCell, setHoveredCell] = useState<{ concept: string; date: string; value: number } | null>(null);

  const maxValue = useMemo(() => data?.max_value || 0, [data]);

  if (loading) {
    return (
      <Card className="h-[500px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Grid3X3 className="w-5 h-5" />
            Activity Heatmap
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading heatmap...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.concepts.length || !data.dates.length) {
    return (
      <Card className="h-[500px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Grid3X3 className="w-5 h-5" />
            Activity Heatmap
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[400px] flex items-center justify-center">
          <p className="text-muted-foreground">No heatmap data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2">
          <Grid3X3 className="w-5 h-5" />
          Activity Heatmap
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Concept activity over time. Darker = more activity. Click cells for details.
        </p>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          <ScrollArea className="w-full">
            <div className="min-w-max">
              {/* Header row with dates */}
              <div className="flex">
                <div className="w-32 flex-shrink-0 p-1 text-xs font-medium text-muted-foreground flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  Concept
                </div>
                {data.dates.map((date) => (
                  <div
                    key={date}
                    className="w-10 flex-shrink-0 p-1 text-[10px] font-medium text-muted-foreground text-center"
                    title={date}
                  >
                    {formatDate(date).split(' ')[1]}
                  </div>
                ))}
              </div>

              {/* Month indicators */}
              <div className="flex mb-1">
                <div className="w-32 flex-shrink-0" />
                {data.dates.map((date, idx) => {
                  const currentMonth = new Date(date).getMonth();
                  const prevMonth = idx > 0 ? new Date(data.dates[idx - 1]).getMonth() : -1;
                  const showMonth = idx === 0 || currentMonth !== prevMonth;
                  return (
                    <div key={`month-${date}`} className="w-10 flex-shrink-0 text-[9px] text-muted-foreground text-center">
                      {showMonth ? new Date(date).toLocaleDateString('en-US', { month: 'short' }) : ''}
                    </div>
                  );
                })}
              </div>

              {/* Data rows */}
              {data.concepts.map((concept, rowIdx) => (
                <div key={concept} className="flex items-center">
                  <div
                    className="w-32 flex-shrink-0 p-1 text-xs truncate font-medium"
                    title={concept}
                  >
                    {concept}
                  </div>
                  {data.dates.map((date, colIdx) => {
                    const value = data.matrix[rowIdx]?.[colIdx] || 0;
                    const conceptId = data.concept_ids?.[rowIdx] || '';

                    return (
                      <Tooltip key={`${concept}-${date}`}>
                        <TooltipTrigger asChild>
                          <button
                            className={`w-10 h-8 flex-shrink-0 text-[10px] font-medium transition-all
                              ${getHeatColor(value, maxValue)} ${getTextColor(value, maxValue)}
                              hover:ring-2 hover:ring-blue-400 hover:z-10 rounded-sm m-[1px]`}
                            onClick={() => onCellClick?.(conceptId, date)}
                            onMouseEnter={() => setHoveredCell({ concept, date, value })}
                            onMouseLeave={() => setHoveredCell(null)}
                          >
                            {value > 0 ? value : ''}
                          </button>
                        </TooltipTrigger>
                        <TooltipContent>
                          <div className="text-xs">
                            <p className="font-semibold">{concept}</p>
                            <p className="text-muted-foreground">{formatDate(date)}</p>
                            <p className="mt-1">{value} {value === 1 ? 'mention' : 'mentions'}</p>
                          </div>
                        </TooltipContent>
                      </Tooltip>
                    );
                  })}
                </div>
              ))}
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
        </TooltipProvider>

        {/* Legend */}
        <div className="mt-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs text-muted-foreground">Activity level:</span>
            <div className="flex items-center gap-1">
              <div className="w-4 h-4 bg-gray-50 rounded" title="0" />
              <div className="w-4 h-4 bg-blue-100 rounded" />
              <div className="w-4 h-4 bg-blue-200 rounded" />
              <div className="w-4 h-4 bg-blue-400 rounded" />
              <div className="w-4 h-4 bg-blue-500 rounded" />
              <div className="w-4 h-4 bg-blue-600 rounded" title={`${maxValue}`} />
            </div>
            <span className="text-xs text-muted-foreground">0 → {maxValue}</span>
          </div>

          {hoveredCell && (
            <div className="text-xs text-muted-foreground">
              Selected: <span className="font-medium">{hoveredCell.concept}</span> on {formatDate(hoveredCell.date)} ({hoveredCell.value})
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default TopicHeatmap;
