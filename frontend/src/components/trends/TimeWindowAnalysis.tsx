import React, { useState, useMemo, useCallback, useEffect } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Clock,
  TrendingUp,
  TrendingDown,
  CalendarDays,
  Activity,
  Filter,
  Calendar,
} from 'lucide-react';
import { useBubbleChartData } from './hooks/useTrendData';
import { BubbleDataPoint } from '../../types/trends';
import {
  LifecycleItem,
  DocumentItem,
  SortKey,
  SortDirection,
  formatFullDate,
  calculateDaysDiff,
  LifecycleTable,
  DocumentPreviewPanel,
} from './TimeWindowCharts';

interface TimeWindowAnalysisProps {
  onConceptClick?: (conceptId: string) => void;
}

const DATA_WINDOW_OPTIONS = [
  { value: 30, label: '30 Days' },
  { value: 60, label: '60 Days' },
  { value: 90, label: '90 Days' },
  { value: 180, label: '180 Days' },
  { value: 365, label: '1 Year' },
];

const TimeWindowAnalysis: React.FC<TimeWindowAnalysisProps> = ({ onConceptClick }) => {
  // Data loading window (how much data to fetch)
  const [dataWindowDays, setDataWindowDays] = useState<number>(90);

  // View filter range (0-100 representing percentage of the data window)
  const [rangeStart, setRangeStart] = useState<number>(0);
  const [rangeEnd, setRangeEnd] = useState<number>(100);

  const [sortKey, setSortKey] = useState<SortKey>('lastSeen');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  // Selected concept for document preview
  const [selectedConcept, setSelectedConcept] = useState<LifecycleItem | null>(null);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);

  // Fetch bubble chart data
  const { data, loading, error } = useBubbleChartData(dataWindowDays, 100);

  // Calculate date range based on slider positions
  const dateRange = useMemo(() => {
    const today = new Date();
    const startOfWindow = new Date(today);
    startOfWindow.setDate(startOfWindow.getDate() - dataWindowDays);

    const totalMs = today.getTime() - startOfWindow.getTime();

    const filterStartDate = new Date(startOfWindow.getTime() + (totalMs * rangeStart / 100));
    const filterEndDate = new Date(startOfWindow.getTime() + (totalMs * rangeEnd / 100));

    return {
      windowStart: startOfWindow,
      windowEnd: today,
      filterStart: filterStartDate,
      filterEnd: filterEndDate,
      filterDays: calculateDaysDiff(filterStartDate, filterEndDate),
    };
  }, [dataWindowDays, rangeStart, rangeEnd]);

  // Transform and filter bubble data to lifecycle items
  const { allItems, filteredItems } = useMemo(() => {
    if (!data?.data?.length) return { allItems: [], filteredItems: [] };

    const today = new Date();
    const threeDaysAgo = new Date(today);
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

    const allItems: LifecycleItem[] = data.data.map((item: BubbleDataPoint) => {
      const lastSeenDate = new Date(item.last_seen);
      const isActive = lastSeenDate >= threeDaysAgo;
      const duration = calculateDaysDiff(item.first_seen, item.last_seen);

      return {
        concept_id: item.concept_id,
        display_name: item.display_name,
        first_seen: item.first_seen,
        last_seen: item.last_seen,
        duration,
        volume: item.z,
        color: item.color,
        velocity: item.y,
        isActive,
      };
    });

    // Filter items that have activity within the selected date range
    const filteredItems = allItems.filter(item => {
      const firstSeen = new Date(item.first_seen);
      const lastSeen = new Date(item.last_seen);
      return firstSeen <= dateRange.filterEnd && lastSeen >= dateRange.filterStart;
    });

    return { allItems, filteredItems };
  }, [data, dateRange]);

  // Calculate statistics
  const stats = useMemo(() => {
    const total = allItems.length;
    const filtered = filteredItems.length;
    const active = filteredItems.filter(c => c.isActive).length;
    const inactive = filtered - active;

    const newInRange = filteredItems.filter(c => {
      const firstSeen = new Date(c.first_seen);
      return firstSeen >= dateRange.filterStart && firstSeen <= dateRange.filterEnd;
    }).length;

    const exitedInRange = filteredItems.filter(c => {
      const lastSeen = new Date(c.last_seen);
      return lastSeen >= dateRange.filterStart && lastSeen <= dateRange.filterEnd && !c.isActive;
    }).length;

    return { total, filtered, active, inactive, newInRange, exitedInRange };
  }, [allItems, filteredItems, dateRange]);

  // Sort lifecycle data
  const sortedLifecycle = useMemo(() => {
    const sorted = [...filteredItems];

    sorted.sort((a, b) => {
      let comparison = 0;

      switch (sortKey) {
        case 'firstSeen':
          comparison = new Date(a.first_seen).getTime() - new Date(b.first_seen).getTime();
          break;
        case 'lastSeen':
          comparison = new Date(a.last_seen).getTime() - new Date(b.last_seen).getTime();
          break;
        case 'duration':
          comparison = a.duration - b.duration;
          break;
        case 'volume':
          comparison = a.volume - b.volume;
          break;
        case 'name':
          comparison = a.display_name.localeCompare(b.display_name);
          break;
      }

      return sortDirection === 'desc' ? -comparison : comparison;
    });

    return sorted;
  }, [filteredItems, sortKey, sortDirection]);

  // Fetch documents when concept is selected
  useEffect(() => {
    if (!selectedConcept) {
      setDocuments([]);
      return;
    }

    const fetchDocuments = async () => {
      setDocumentsLoading(true);
      try {
        // Fetch tag instances for this concept
        const startDate = dateRange.filterStart.toISOString().split('T')[0];
        const endDate = dateRange.filterEnd.toISOString().split('T')[0];

        // Fetch from multiple endpoints in parallel
        const [tweetsRes, articlesRes, papersRes] = await Promise.allSettled([
          axios.get(`/api/tweets`, {
            params: {
              concept: selectedConcept.concept_id,
              start_date: startDate,
              end_date: endDate,
              limit: 20
            }
          }),
          axios.get(`/api/articles`, {
            params: {
              concept_id: selectedConcept.concept_id,
              page_size: 20
            }
          }),
          axios.get(`/api/papers`, {
            params: {
              concept_id: selectedConcept.concept_id,
              limit: 20
            }
          })
        ]);

        const docs: DocumentItem[] = [];

        // Process tweets
        if (tweetsRes.status === 'fulfilled' && tweetsRes.value.data) {
          const tweets = Array.isArray(tweetsRes.value.data) ? tweetsRes.value.data : tweetsRes.value.data.tweets || [];
          tweets.forEach((tweet: any) => {
            const tweetDate = new Date(tweet.created_at);
            if (tweetDate >= dateRange.filterStart && tweetDate <= dateRange.filterEnd) {
              docs.push({
                id: tweet.id || tweet._id,
                type: 'tweet',
                title: `@${tweet.author_username || tweet.author?.username || 'unknown'}`,
                preview: tweet.text?.substring(0, 150) + (tweet.text?.length > 150 ? '...' : '') || '',
                date: tweet.created_at,
                author: tweet.author_username || tweet.author?.username,
                url: tweet.url || `https://twitter.com/i/status/${tweet.id || tweet._id}`
              });
            }
          });
        }

        // Process articles
        if (articlesRes.status === 'fulfilled' && articlesRes.value.data) {
          const articles = Array.isArray(articlesRes.value.data) ? articlesRes.value.data : articlesRes.value.data.articles || [];
          articles.forEach((article: any) => {
            const articleDate = new Date(article.published_at || article.created_at);
            if (articleDate >= dateRange.filterStart && articleDate <= dateRange.filterEnd) {
              docs.push({
                id: article.id || article._id,
                type: 'article',
                title: article.title || 'Untitled Article',
                preview: article.subtitle || article.preview || article.summary?.substring(0, 150) || '',
                date: article.published_at || article.created_at,
                author: article.author_name || article.author,
                url: article.url
              });
            }
          });
        }

        // Process papers
        if (papersRes.status === 'fulfilled' && papersRes.value.data) {
          const papers = Array.isArray(papersRes.value.data) ? papersRes.value.data : papersRes.value.data.papers || [];
          papers.forEach((paper: any) => {
            const paperDate = new Date(paper.published_date || paper.created_at);
            if (paperDate >= dateRange.filterStart && paperDate <= dateRange.filterEnd) {
              docs.push({
                id: paper.id || paper._id,
                type: 'paper',
                title: paper.title || 'Untitled Paper',
                preview: paper.abstract?.substring(0, 150) + (paper.abstract?.length > 150 ? '...' : '') || '',
                date: paper.published_date || paper.created_at,
                author: paper.authors || paper.authors_string,
                url: paper.url || paper.pdf_url
              });
            }
          });
        }

        // Sort by date descending
        docs.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());

        setDocuments(docs);
      } catch (err) {
        console.error('Error fetching documents:', err);
        setDocuments([]);
      } finally {
        setDocumentsLoading(false);
      }
    };

    fetchDocuments();
  }, [selectedConcept, dateRange.filterStart, dateRange.filterEnd]);

  const handleSort = useCallback((key: SortKey) => {
    if (sortKey === key) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortDirection('desc');
    }
  }, [sortKey]);

  const handleStartChange = useCallback((values: number[]) => {
    // Start date cannot be after end date
    const newStart = Math.min(values[0], rangeEnd);
    setRangeStart(newStart);
  }, [rangeEnd]);

  const handleEndChange = useCallback((values: number[]) => {
    // End date cannot be before start date
    const newEnd = Math.max(values[0], rangeStart);
    setRangeEnd(newEnd);
  }, [rangeStart]);

  const handleResetRange = useCallback(() => {
    setRangeStart(0);
    setRangeEnd(100);
  }, []);

  const handleConceptSelect = useCallback((item: LifecycleItem) => {
    if (selectedConcept?.concept_id === item.concept_id) {
      setSelectedConcept(null); // Deselect if clicking same concept
    } else {
      setSelectedConcept(item);
    }
    onConceptClick?.(item.concept_id);
  }, [selectedConcept, onConceptClick]);

  if (loading) {
    return (
      <Card className="h-[700px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Concept Lifecycle Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[600px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading lifecycle data...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-[700px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5" />
            Concept Lifecycle Analysis
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[600px] flex items-center justify-center">
          <p className="text-destructive">
            Error: {typeof error === 'string' ? error : JSON.stringify(error)}
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-auto">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Concept Lifecycle Analysis
            </CardTitle>
            <p className="text-xs text-muted-foreground mt-1">
              Track when concepts first appeared and their last activity
            </p>
          </div>

          {/* Data Window Selector */}
          <div className="flex items-center gap-2">
            <CalendarDays className="w-4 h-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">Load:</span>
            <Select
              value={String(dataWindowDays)}
              onValueChange={(v) => setDataWindowDays(parseInt(v, 10))}
            >
              <SelectTrigger className="w-[100px] h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {DATA_WINDOW_OPTIONS.map(option => (
                  <SelectItem key={option.value} value={String(option.value)}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Date Range Slider */}
        <div className="p-4 bg-muted/30 rounded-lg border space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Filter Time Range</span>
            </div>
            <button
              onClick={handleResetRange}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Reset to full range
            </button>
          </div>

          {/* Start Date Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                Start Date
              </span>
              <span className="font-medium">{formatFullDate(dateRange.filterStart)}</span>
            </div>
            <Slider
              value={[rangeStart]}
              min={0}
              max={100}
              step={1}
              onValueChange={handleStartChange}
              className="cursor-pointer"
            />
          </div>

          {/* End Date Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                End Date
              </span>
              <span className="font-medium">{formatFullDate(dateRange.filterEnd)}</span>
            </div>
            <Slider
              value={[rangeEnd]}
              min={0}
              max={100}
              step={1}
              onValueChange={handleEndChange}
              className="cursor-pointer"
            />
          </div>

          {/* Summary Badge */}
          <div className="text-center">
            <Badge variant="outline" className="text-xs">
              {dateRange.filterDays} days selected
            </Badge>
          </div>

          {/* Impact indicator */}
          <div className="flex items-center justify-center gap-2 pt-1">
            <div className="h-2 flex-1 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-primary transition-all duration-300"
                style={{ width: `${stats.total > 0 ? (stats.filtered / stats.total) * 100 : 0}%` }}
              />
            </div>
            <span className="text-xs text-muted-foreground whitespace-nowrap">
              {stats.filtered} / {stats.total} concepts ({stats.total > 0 ? Math.round((stats.filtered / stats.total) * 100) : 0}%)
            </span>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="flex flex-wrap items-center gap-3 p-3 bg-muted/50 rounded-lg">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-muted-foreground" />
            <span className="text-sm font-medium">{stats.filtered} concepts in range</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-4 h-4 text-green-500" />
            <span className="text-sm">{stats.newInRange} emerged</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-1.5">
            <TrendingDown className="w-4 h-4 text-amber-500" />
            <span className="text-sm">{stats.exitedInRange} faded</span>
          </div>
          <div className="h-4 w-px bg-border" />
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-green-500" />
            <span className="text-sm">{stats.active} still active</span>
          </div>
        </div>

        <LifecycleTable
          sortedLifecycle={sortedLifecycle}
          selectedConcept={selectedConcept}
          sortKey={sortKey}
          sortDirection={sortDirection}
          onSort={handleSort}
          onConceptSelect={handleConceptSelect}
        />

        {/* Document Preview Panel */}
        {selectedConcept && (
          <DocumentPreviewPanel
            selectedConcept={selectedConcept}
            documents={documents}
            documentsLoading={documentsLoading}
            onClose={() => setSelectedConcept(null)}
          />
        )}

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 pt-2 text-xs text-muted-foreground">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-green-500" />
            <span>Active (activity in last 3 days)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-amber-500" />
            <span>Inactive (no recent activity)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default TimeWindowAnalysis;
