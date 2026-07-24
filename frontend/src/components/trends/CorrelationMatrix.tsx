/**
 * CorrelationMatrix Component
 * Shows co-occurrence patterns between concepts
 * Symmetric matrix with strength indicators
 */

import React, { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea, ScrollBar } from '@/components/ui/scroll-area';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Badge } from '@/components/ui/badge';
import { GitBranch, ArrowRightLeft, Layers } from 'lucide-react';
import { CooccurrenceData, CooccurrencePair } from '../../types/trends';

interface CorrelationMatrixProps {
  data: CooccurrenceData | null;
  loading?: boolean;
  onPairClick?: (conceptAId: string, conceptBId: string) => void;
}

const getCorrelationColor = (value: number, maxValue: number): string => {
  if (value === 0) return 'bg-gray-50';
  const intensity = Math.min(value / (maxValue || 1), 1);

  if (intensity < 0.2) return 'bg-purple-100';
  if (intensity < 0.4) return 'bg-purple-200';
  if (intensity < 0.6) return 'bg-purple-400';
  if (intensity < 0.8) return 'bg-purple-500';
  return 'bg-purple-600';
};

const getTextColor = (value: number, maxValue: number): string => {
  if (value === 0) return 'text-gray-300';
  const intensity = value / (maxValue || 1);
  return intensity > 0.5 ? 'text-white' : 'text-purple-900';
};

const TopPairsSection: React.FC<{
  pairs: CooccurrencePair[];
  onPairClick?: (aId: string, bId: string) => void;
}> = ({ pairs, onPairClick }) => {
  return (
    <div className="space-y-2">
      <h4 className="text-sm font-medium flex items-center gap-2">
        <ArrowRightLeft className="w-4 h-4" />
        Top Co-occurring Pairs
      </h4>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
        {pairs.slice(0, 12).map((pair, idx) => (
          <button
            key={`${pair.concept_a_id}-${pair.concept_b_id}`}
            className="flex items-center justify-between p-2 rounded-lg border bg-white hover:bg-purple-50 transition-colors text-left"
            onClick={() => onPairClick?.(pair.concept_a_id, pair.concept_b_id)}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1 text-xs">
                <span className="truncate font-medium">{pair.concept_a}</span>
                <span className="text-muted-foreground">↔</span>
                <span className="truncate font-medium">{pair.concept_b}</span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <Badge variant="secondary" className="text-[10px]">
                  {pair.count}×
                </Badge>
                <span className="text-[10px] text-muted-foreground">
                  Strength: {(pair.strength * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div
              className="w-2 h-8 rounded-full ml-2 flex-shrink-0"
              style={{
                background: `linear-gradient(to top, rgb(147, 51, 234) ${pair.strength * 100}%, rgb(243, 232, 255) ${pair.strength * 100}%)`,
              }}
            />
          </button>
        ))}
      </div>
    </div>
  );
};

const CorrelationMatrix: React.FC<CorrelationMatrixProps> = ({ data, loading, onPairClick }) => {
  const [hoveredCell, setHoveredCell] = useState<{ row: string; col: string; value: number } | null>(null);

  const maxValue = useMemo(() => {
    if (!data?.matrix) return 0;
    return Math.max(...data.matrix.flat().filter(v => v > 0), 1);
  }, [data]);

  if (loading) {
    return (
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-5 h-5" />
            Concept Correlation
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[500px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading correlation data...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data || !data.concepts.length) {
    return (
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-5 h-5" />
            Concept Correlation
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[500px] flex items-center justify-center">
          <p className="text-muted-foreground">No correlation data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2">
          <Layers className="w-5 h-5" />
          Concept Correlation Matrix
        </CardTitle>
        <p className="text-xs text-muted-foreground">
          Co-occurrence frequency between concepts. Higher values indicate concepts that appear together more often.
        </p>
      </CardHeader>
      <CardContent>
        <TooltipProvider>
          {/* Matrix Grid */}
          <ScrollArea className="w-full">
            <div className="min-w-max mb-4">
              {/* Header row */}
              <div className="flex">
                <div className="w-24 flex-shrink-0" />
                {data.concepts.map((concept) => (
                  <div
                    key={`header-${concept}`}
                    className="w-8 flex-shrink-0 p-0.5"
                  >
                    <div
                      className="text-[9px] font-medium text-muted-foreground transform -rotate-45 origin-left whitespace-nowrap overflow-hidden"
                      style={{ width: '60px' }}
                      title={concept}
                    >
                      {concept.length > 10 ? concept.slice(0, 10) + '...' : concept}
                    </div>
                  </div>
                ))}
              </div>

              {/* Add space for rotated labels */}
              <div className="h-12" />

              {/* Data rows */}
              {data.concepts.map((rowConcept, rowIdx) => (
                <div key={rowConcept} className="flex items-center">
                  <div
                    className="w-24 flex-shrink-0 p-0.5 text-[10px] truncate font-medium text-right pr-2"
                    title={rowConcept}
                  >
                    {rowConcept.length > 12 ? rowConcept.slice(0, 12) + '...' : rowConcept}
                  </div>
                  {data.concepts.map((colConcept, colIdx) => {
                    const value = data.matrix[rowIdx]?.[colIdx] || 0;
                    const isDiagonal = rowIdx === colIdx;

                    return (
                      <Tooltip key={`${rowConcept}-${colConcept}`}>
                        <TooltipTrigger asChild>
                          <button
                            className={`w-8 h-6 flex-shrink-0 text-[9px] font-medium transition-all
                              ${isDiagonal ? 'bg-gray-200' : getCorrelationColor(value, maxValue)}
                              ${isDiagonal ? 'text-gray-400' : getTextColor(value, maxValue)}
                              hover:ring-1 hover:ring-purple-400 hover:z-10 rounded-[2px] m-[1px]
                              ${isDiagonal ? 'cursor-default' : 'cursor-pointer'}`}
                            onClick={() => {
                              if (!isDiagonal && value > 0) {
                                onPairClick?.(
                                  data.concept_ids[rowIdx],
                                  data.concept_ids[colIdx]
                                );
                              }
                            }}
                            onMouseEnter={() => !isDiagonal && setHoveredCell({ row: rowConcept, col: colConcept, value })}
                            onMouseLeave={() => setHoveredCell(null)}
                            disabled={isDiagonal}
                          >
                            {isDiagonal ? '-' : value > 0 ? value : ''}
                          </button>
                        </TooltipTrigger>
                        {!isDiagonal && value > 0 && (
                          <TooltipContent>
                            <div className="text-xs">
                              <p className="font-semibold">{rowConcept}</p>
                              <p className="text-muted-foreground">co-occurs with</p>
                              <p className="font-semibold">{colConcept}</p>
                              <p className="mt-1">{value} times</p>
                            </div>
                          </TooltipContent>
                        )}
                      </Tooltip>
                    );
                  })}
                </div>
              ))}
            </div>
            <ScrollBar orientation="horizontal" />
          </ScrollArea>

          {/* Legend */}
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground">Co-occurrence:</span>
              <div className="flex items-center gap-1">
                <div className="w-4 h-4 bg-gray-50 rounded" title="0" />
                <div className="w-4 h-4 bg-purple-100 rounded" />
                <div className="w-4 h-4 bg-purple-200 rounded" />
                <div className="w-4 h-4 bg-purple-400 rounded" />
                <div className="w-4 h-4 bg-purple-500 rounded" />
                <div className="w-4 h-4 bg-purple-600 rounded" title={`${maxValue}`} />
              </div>
              <span className="text-xs text-muted-foreground">0 → {maxValue}</span>
            </div>
            <Badge variant="outline" className="text-xs">
              {data.total_documents} documents analyzed
            </Badge>
          </div>

          {/* Top Pairs */}
          {data.pairs.length > 0 && (
            <TopPairsSection pairs={data.pairs} onPairClick={onPairClick} />
          )}
        </TooltipProvider>
      </CardContent>
    </Card>
  );
};

export default CorrelationMatrix;
