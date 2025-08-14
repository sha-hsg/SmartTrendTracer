import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Calendar,
  FileText,
  Twitter,
  BookOpen,
  Clock,
  User,
  Filter,
  ChevronRight,
  ArrowUpRight,
  Loader2,
  TrendingUp,
  Hash
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

interface TimelineItem {
  type: 'paper' | 'tweet' | 'article'
  id: number
  title?: string
  text?: string
  timestamp: string
  publication_date?: string
  author?: string
  authors?: string[]
}

interface TimelineData {
  timeline: TimelineItem[]
  counts: {
    papers: number
    tweets: number
    articles: number
  }
  time_window_days: number
}

const UnifiedTimelineView: React.FC = () => {
  const [timeline, setTimeline] = useState<TimelineData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeWindow, setTimeWindow] = useState('30')
  const [filterType, setFilterType] = useState<'all' | 'paper' | 'tweet' | 'article'>('all')
  const [refreshing, setRefreshing] = useState(false)

  const fetchTimeline = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.get(`http://localhost:8000/api/papers/trends/unified-timeline`, {
        params: { days: parseInt(timeWindow) }
      })
      setTimeline(response.data)
    } catch (err) {
      setError('Failed to load timeline')
      console.error('Error fetching timeline:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTimeline()
  }, [timeWindow])

  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchTimeline()
    setRefreshing(false)
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    
    if (diffHours < 1) {
      return `${Math.floor(diffHours * 60)} minutes ago`
    } else if (diffHours < 24) {
      return `${Math.floor(diffHours)} hours ago`
    } else if (diffHours < 168) {
      return `${Math.floor(diffHours / 24)} days ago`
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
    }
  }

  const getItemIcon = (type: string) => {
    switch (type) {
      case 'paper':
        return <FileText className="h-4 w-4" />
      case 'tweet':
        return <Twitter className="h-4 w-4" />
      case 'article':
        return <BookOpen className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const getItemColor = (type: string) => {
    switch (type) {
      case 'paper':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      case 'tweet':
        return 'text-green-600 bg-green-50 border-green-200'
      case 'article':
        return 'text-purple-600 bg-purple-50 border-purple-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const filteredTimeline = timeline?.timeline.filter(item => 
    filterType === 'all' || item.type === filterType
  ) || []

  const renderTimelineItem = (item: TimelineItem) => {
    return (
      <div
        key={`${item.type}-${item.id}`}
        className={cn(
          "relative pl-8 pb-6 border-l-2 border-gray-200 last:border-l-0",
          "hover:border-l-gray-400 transition-colors"
        )}
      >
        <div className={cn(
          "absolute -left-2 top-0 w-4 h-4 rounded-full border-2 bg-white",
          getItemColor(item.type).split(' ')[1].replace('bg-', 'border-')
        )} />
        
        <div className="flex items-start gap-3">
          <div className={cn(
            "p-2 rounded-lg",
            getItemColor(item.type)
          )}>
            {getItemIcon(item.type)}
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge variant="outline" className="text-xs">
                {item.type}
              </Badge>
              <span className="text-xs text-gray-500">
                {formatDate(item.timestamp)}
              </span>
            </div>
            
            {item.type === 'paper' && (
              <>
                <h4 className="font-medium text-sm mb-1 line-clamp-2">
                  {item.title}
                </h4>
                {item.authors && item.authors.length > 0 && (
                  <p className="text-xs text-gray-600 flex items-center gap-1">
                    <User className="h-3 w-3" />
                    {item.authors.join(', ')}
                  </p>
                )}
              </>
            )}
            
            {item.type === 'tweet' && (
              <>
                <p className="text-sm text-gray-700 line-clamp-3 mb-1">
                  {item.text}
                </p>
                <p className="text-xs text-gray-600 flex items-center gap-1">
                  <User className="h-3 w-3" />
                  @{item.author}
                </p>
              </>
            )}
            
            {item.type === 'article' && (
              <>
                <h4 className="font-medium text-sm mb-1 line-clamp-2">
                  {item.title}
                </h4>
                {item.author && (
                  <p className="text-xs text-gray-600 flex items-center gap-1">
                    <User className="h-3 w-3" />
                    {item.author}
                  </p>
                )}
              </>
            )}
            
            <Button
              variant="ghost"
              size="sm"
              className="mt-2 h-6 text-xs"
              onClick={() => {
                // Navigate to item detail
                console.log(`Navigate to ${item.type} ${item.id}`)
              }}
            >
              View Details
              <ArrowUpRight className="h-3 w-3 ml-1" />
            </Button>
          </div>
        </div>
      </div>
    )
  }

  if (loading && !timeline) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-64">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Unified Research Timeline
              </CardTitle>
              <CardDescription>
                Track papers, tweets, and articles in one timeline
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Select value={timeWindow} onValueChange={setTimeWindow}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="7">Last 7 days</SelectItem>
                  <SelectItem value="14">Last 14 days</SelectItem>
                  <SelectItem value="30">Last 30 days</SelectItem>
                  <SelectItem value="60">Last 60 days</SelectItem>
                  <SelectItem value="90">Last 90 days</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                {refreshing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Refresh'
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {/* Statistics */}
          <div className="grid grid-cols-3 gap-4 mb-6">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Papers</p>
                    <p className="text-2xl font-bold">{timeline?.counts.papers || 0}</p>
                  </div>
                  <FileText className="h-8 w-8 text-blue-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Tweets</p>
                    <p className="text-2xl font-bold">{timeline?.counts.tweets || 0}</p>
                  </div>
                  <Twitter className="h-8 w-8 text-green-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Articles</p>
                    <p className="text-2xl font-bold">{timeline?.counts.articles || 0}</p>
                  </div>
                  <BookOpen className="h-8 w-8 text-purple-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Filter Tabs */}
          <Tabs value={filterType} onValueChange={(v) => setFilterType(v as any)}>
            <TabsList className="mb-4">
              <TabsTrigger value="all">
                All ({filteredTimeline.length})
              </TabsTrigger>
              <TabsTrigger value="paper">
                Papers ({timeline?.timeline.filter(i => i.type === 'paper').length || 0})
              </TabsTrigger>
              <TabsTrigger value="tweet">
                Tweets ({timeline?.timeline.filter(i => i.type === 'tweet').length || 0})
              </TabsTrigger>
              <TabsTrigger value="article">
                Articles ({timeline?.timeline.filter(i => i.type === 'article').length || 0})
              </TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Timeline */}
          <ScrollArea className="h-[600px] pr-4">
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            
            {filteredTimeline.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                No items found in the selected time window
              </div>
            ) : (
              <div className="space-y-2">
                {filteredTimeline.map(renderTimelineItem)}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>
    </div>
  )
}

export default UnifiedTimelineView