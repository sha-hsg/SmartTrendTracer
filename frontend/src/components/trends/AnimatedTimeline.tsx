/**
 * AnimatedTimeline Component
 * Bar chart race style animation showing concept rankings over time
 */

import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  FastForward,
  Rewind,
  Calendar,
  BarChart3,
} from 'lucide-react';
import { AnimatedTimelineData, TimelineRanking } from '../../types/trends';

interface AnimatedTimelineProps {
  data: AnimatedTimelineData | null;
  loading?: boolean;
  onConceptClick?: (conceptId: string) => void;
}

const formatDate = (dateStr: string): string => {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

interface BarItemProps {
  ranking: TimelineRanking;
  maxValue: number;
  onClick?: () => void;
}

const BarItem = React.forwardRef<HTMLDivElement, BarItemProps>(
  ({ ranking, maxValue, onClick }, ref) => {
    const widthPercent = Math.max((ranking.value / (maxValue || 1)) * 100, 5);

    return (
      <motion.div
        ref={ref}
        layout
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: 20 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="flex items-center gap-2 h-10 cursor-pointer group"
        onClick={onClick}
      >
        {/* Rank */}
        <div className="w-6 text-right text-sm font-medium text-muted-foreground">
          {ranking.rank}
        </div>

        {/* Name */}
        <div className="w-28 text-sm font-medium truncate text-right pr-2">
          {ranking.display_name}
        </div>

        {/* Bar */}
        <div className="flex-1 h-7 relative">
          <motion.div
            className="h-full rounded-r-md transition-colors group-hover:brightness-110"
            style={{ backgroundColor: ranking.color }}
            initial={{ width: 0 }}
            animate={{ width: `${widthPercent}%` }}
            transition={{ type: 'spring', stiffness: 100, damping: 15 }}
          >
            {/* Value label inside bar */}
            <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs font-bold text-white drop-shadow">
              {ranking.value}
            </span>
          </motion.div>
        </div>
      </motion.div>
    );
  }
);

BarItem.displayName = 'BarItem';

const AnimatedTimeline: React.FC<AnimatedTimelineProps> = ({
  data,
  loading,
  onConceptClick,
}) => {
  const [currentFrameIndex, setCurrentFrameIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const frames = useMemo(() => data?.frames || [], [data]);
  const currentFrame = frames[currentFrameIndex];

  const maxValue = useMemo(() => {
    if (!frames.length) return 0;
    return Math.max(
      ...frames.flatMap(f => f.rankings.map(r => r.value)),
      1
    );
  }, [frames]);

  // Reset frame index when data changes
  useEffect(() => {
    setCurrentFrameIndex(0);
    setIsPlaying(false);
  }, [data]);

  // Playback control
  useEffect(() => {
    if (isPlaying && frames.length > 0) {
      intervalRef.current = setInterval(() => {
        setCurrentFrameIndex(prev => {
          if (prev >= frames.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000 / speed);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isPlaying, speed, frames.length]);

  const handlePlayPause = useCallback(() => {
    if (currentFrameIndex >= frames.length - 1) {
      setCurrentFrameIndex(0);
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying, currentFrameIndex, frames.length]);

  const handleSkipBack = useCallback(() => {
    setIsPlaying(false);
    setCurrentFrameIndex(0);
  }, []);

  const handleSkipForward = useCallback(() => {
    setIsPlaying(false);
    setCurrentFrameIndex(frames.length - 1);
  }, [frames.length]);

  const handleStepBack = useCallback(() => {
    setIsPlaying(false);
    setCurrentFrameIndex(prev => Math.max(0, prev - 1));
  }, []);

  const handleStepForward = useCallback(() => {
    setIsPlaying(false);
    setCurrentFrameIndex(prev => Math.min(frames.length - 1, prev + 1));
  }, [frames.length]);

  const handleSliderChange = useCallback((value: number[]) => {
    setCurrentFrameIndex(value[0]);
  }, []);

  if (loading) {
    return (
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Trending Concepts Over Time
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[500px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading timeline data...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data || frames.length === 0) {
    return (
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Trending Concepts Over Time
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[500px] flex items-center justify-center">
          <p className="text-muted-foreground">No timeline data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-auto min-h-[600px]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Trending Concepts Over Time
          </CardTitle>
          {/* Current Date Badge */}
          {currentFrame && (
            <Badge variant="outline" className="text-sm flex items-center gap-1">
              <Calendar className="w-3 h-3" />
              {formatDate(currentFrame.date)}
            </Badge>
          )}
        </div>
        <p className="text-xs text-muted-foreground">
          Watch concepts rise and fall in popularity over the selected time period.
        </p>
      </CardHeader>
      <CardContent>
        {/* Controls */}
        <div className="flex items-center justify-center gap-2 mb-4">
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleSkipBack} title="Go to start">
            <SkipBack className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleStepBack} title="Previous frame">
            <Rewind className="h-4 w-4" />
          </Button>
          <Button
            variant={isPlaying ? "default" : "outline"}
            size="icon"
            className="h-10 w-10"
            onClick={handlePlayPause}
            title={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleStepForward} title="Next frame">
            <FastForward className="h-4 w-4" />
          </Button>
          <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleSkipForward} title="Go to end">
            <SkipForward className="h-4 w-4" />
          </Button>

          {/* Speed control */}
          <div className="flex items-center gap-2 ml-4">
            <span className="text-xs text-muted-foreground">Speed:</span>
            <Badge variant="secondary" className="text-xs min-w-[32px] justify-center">
              {speed}x
            </Badge>
            <div className="w-20">
              <Slider
                value={[speed]}
                min={0.5}
                max={3}
                step={0.5}
                onValueChange={([v]) => setSpeed(v)}
              />
            </div>
          </div>
        </div>

        {/* Timeline scrubber */}
        <div className="mb-4 px-2">
          <Slider
            value={[currentFrameIndex]}
            min={0}
            max={frames.length - 1}
            step={1}
            onValueChange={handleSliderChange}
            className="cursor-pointer"
          />
          <div className="flex justify-between text-xs text-muted-foreground mt-1">
            <span>{formatDate(frames[0]?.date || '')}</span>
            <span>Frame {currentFrameIndex + 1} of {frames.length}</span>
            <span>{formatDate(frames[frames.length - 1]?.date || '')}</span>
          </div>
        </div>

        {/* Bar chart race */}
        <div className="space-y-1 px-2">
          <AnimatePresence mode="popLayout">
            {currentFrame?.rankings.slice(0, 15).map((ranking) => (
              <BarItem
                key={ranking.concept_id}
                ranking={ranking}
                maxValue={maxValue}
                onClick={() => onConceptClick?.(ranking.concept_id)}
              />
            ))}
          </AnimatePresence>
        </div>

        {/* Legend */}
        <div className="mt-4 pt-4 border-t">
          <p className="text-xs text-muted-foreground mb-2">Top performers over entire period:</p>
          <div className="flex flex-wrap gap-2">
            {data.concepts.slice(0, 10).map((concept) => (
              <Badge
                key={concept.concept_id}
                variant="outline"
                className="text-xs cursor-pointer hover:bg-accent"
                style={{ borderColor: concept.color }}
                onClick={() => onConceptClick?.(concept.concept_id)}
              >
                <span className="w-2 h-2 rounded-full mr-1" style={{ backgroundColor: concept.color }} />
                {concept.display_name}
                <span className="ml-1 text-muted-foreground">({concept.total_value})</span>
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AnimatedTimeline;
