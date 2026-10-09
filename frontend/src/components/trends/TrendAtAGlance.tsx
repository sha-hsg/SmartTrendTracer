/**
 * TrendAtAGlance Component
 * 4-column grid showing Hot Topics, Declining Topics, Stable (Evergreens), and Anomalies
 */

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { TooltipProvider } from '@/components/ui/tooltip';
import {
  Flame,
  TrendingDown,
  Target,
  AlertTriangle,
  ArrowUp,
  ArrowDown,
  Minus,
} from 'lucide-react';
import { ConceptTrend, AnomalyAlert } from '../../types/trends';

interface TrendAtAGlanceProps {
  hotTopics: ConceptTrend[];
  declining: ConceptTrend[];
  stable: ConceptTrend[];
  anomalies: AnomalyAlert[];
  loading?: boolean;
  onConceptClick?: (conceptId: string) => void;
}

const SparklineChart: React.FC<{ data: number[]; color: string }> = ({ data, color }) => {
  if (!data || data.length === 0) return null;

  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const width = 60;
  const height = 24;
  const padding = 2;

  const points = data.map((value, index) => {
    const x = padding + (index / (data.length - 1 || 1)) * (width - 2 * padding);
    const y = height - padding - ((value - min) / range) * (height - 2 * padding);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg width={width} height={height} className="inline-block">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

const TrendCard: React.FC<{
  trend: ConceptTrend;
  type: 'hot' | 'declining' | 'stable';
  onClick?: () => void;
}> = ({ trend, type, onClick }) => {
  const colors = {
    hot: { bg: 'bg-red-50 hover:bg-red-100', border: 'border-red-200', text: 'text-red-700', spark: '#EF4444' },
    declining: { bg: 'bg-orange-50 hover:bg-orange-100', border: 'border-orange-200', text: 'text-orange-700', spark: '#F97316' },
    stable: { bg: 'bg-green-50 hover:bg-green-100', border: 'border-green-200', text: 'text-green-700', spark: '#10B981' },
  };

  const style = colors[type];

  return (
    <div
      className={`p-2 rounded-lg border ${style.bg} ${style.border} cursor-pointer transition-colors`}
      onClick={onClick}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-sm truncate flex-1">{trend.display_name}</span>
        <SparklineChart data={trend.sparkline} color={style.spark} />
      </div>
      <div className="flex items-center justify-between mt-1">
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <span title="items now · usual level for a window of this length">{trend.count} items · usual {trend.previous_count}</span>
          {trend.content_breakdown && (
            <span className="text-[10px]">
              ({trend.content_breakdown.tweets}T/{trend.content_breakdown.articles}A/{trend.content_breakdown.papers}P)
            </span>
          )}
        </div>
        <Badge variant="outline" className={`text-xs ${style.text}`}>
          {trend.velocity > 0 ? '+' : ''}{trend.velocity}%
          {trend.velocity > 0 ? <ArrowUp className="w-3 h-3 ml-0.5" /> : trend.velocity < 0 ? <ArrowDown className="w-3 h-3 ml-0.5" /> : <Minus className="w-3 h-3 ml-0.5" />}
        </Badge>
      </div>
    </div>
  );
};

const AnomalyCard: React.FC<{
  anomaly: AnomalyAlert;
  onClick?: () => void;
}> = ({ anomaly, onClick }) => {
  return (
    <div
      className="p-2 rounded-lg border bg-purple-50 hover:bg-purple-100 border-purple-200 cursor-pointer transition-colors dark:bg-purple-950/40 dark:border-purple-800"
      onClick={onClick}
    >
      <div className="flex items-center justify-between gap-2">
        <span className="font-medium text-sm truncate flex-1">{anomaly.display_name}</span>
        <Badge variant="outline" className="text-purple-700 text-xs dark:text-purple-300">
          Z: {anomaly.z_score.toFixed(1)}
        </Badge>
      </div>
      <div className="flex items-center justify-between mt-1 text-xs text-muted-foreground">
        <span>Spike: +{Math.round(anomaly.spike_magnitude)}</span>
        <span>Baseline: {anomaly.baseline_avg.toFixed(1)}/day</span>
      </div>
    </div>
  );
};

const TrendAtAGlance: React.FC<TrendAtAGlanceProps> = ({
  hotTopics,
  declining,
  stable,
  anomalies,
  loading,
  onConceptClick,
}) => {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <Card key={i} className="animate-pulse">
            <CardHeader className="pb-2">
              <div className="h-6 bg-muted rounded w-32" />
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {[1, 2, 3].map((j) => (
                  <div key={j} className="h-16 bg-muted rounded" />
                ))}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Hot Topics */}
        <Card className="border-red-200 bg-gradient-to-br from-red-50 to-white dark:from-red-950/40 dark:border-red-800">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-red-700 dark:text-red-300">
              <Flame className="w-5 h-5" />
              Hot Topics
              <Badge variant="secondary" className="ml-auto">{hotTopics.length}</Badge>
            </CardTitle>
            <p className="text-xs text-muted-foreground">≥2× its usual level · z ≥ 3 · ≥5 items</p>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[240px]">
              <div className="space-y-2 pr-2">
                {hotTopics.length > 0 ? (
                  hotTopics.map((trend) => (
                    <TrendCard
                      key={trend.concept_id}
                      trend={trend}
                      type="hot"
                      onClick={() => onConceptClick?.(trend.concept_id)}
                    />
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No hot topics detected
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Declining Topics */}
        <Card className="border-orange-200 bg-gradient-to-br from-orange-50 to-white dark:from-orange-950/40 dark:border-orange-800">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-orange-700 dark:text-orange-300">
              <TrendingDown className="w-5 h-5" />
              Declining
              <Badge variant="secondary" className="ml-auto">{declining.length}</Badge>
            </CardTitle>
            <p className="text-xs text-muted-foreground">≤½ its usual level · z ≤ −2</p>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[240px]">
              <div className="space-y-2 pr-2">
                {declining.length > 0 ? (
                  declining.map((trend) => (
                    <TrendCard
                      key={trend.concept_id}
                      trend={trend}
                      type="declining"
                      onClick={() => onConceptClick?.(trend.concept_id)}
                    />
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No declining topics
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Stable Evergreens */}
        <Card className="border-green-200 bg-gradient-to-br from-green-50 to-white dark:from-green-950/40 dark:border-green-800">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-green-700 dark:text-green-300">
              <Target className="w-5 h-5" />
              Stable
              <Badge variant="secondary" className="ml-auto">{stable.length}</Badge>
            </CardTitle>
            <p className="text-xs text-muted-foreground">At its usual level, present every period</p>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[240px]">
              <div className="space-y-2 pr-2">
                {stable.length > 0 ? (
                  stable.map((trend) => (
                    <TrendCard
                      key={trend.concept_id}
                      trend={trend}
                      type="stable"
                      onClick={() => onConceptClick?.(trend.concept_id)}
                    />
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No stable topics
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Anomalies */}
        <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-white dark:from-purple-950/40 dark:border-purple-800">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-purple-700 dark:text-purple-300">
              <AlertTriangle className="w-5 h-5" />
              Anomalies
              <Badge variant="secondary" className="ml-auto">{anomalies.length}</Badge>
            </CardTitle>
            <p className="text-xs text-muted-foreground">Single-day spikes against the baseline days</p>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[240px]">
              <div className="space-y-2 pr-2">
                {anomalies.length > 0 ? (
                  anomalies.map((anomaly) => (
                    <AnomalyCard
                      key={anomaly.concept_id}
                      anomaly={anomaly}
                      onClick={() => onConceptClick?.(anomaly.concept_id)}
                    />
                  ))
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-4">
                    No anomalies detected
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  );
};

export default TrendAtAGlance;
