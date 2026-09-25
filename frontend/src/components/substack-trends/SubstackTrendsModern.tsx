import { useState, useEffect } from 'react'
import http from '@/services/http'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { cn } from "@/lib/utils"
import {
  TrendingUp,
  Clock,
  Users,
  FileText,
  Hash,
  RefreshCw,
  AlertCircle,
  Sparkles,
  Flame,
  BookOpen,
  Lightbulb,
  Rocket,
  MessageSquare,
  ChevronRight,
} from 'lucide-react'
import type { TrendData } from './types'
import { formatDate } from './helpers'
import {
  TopicsTabPanel,
  AuthorsTabPanel,
  VelocityTabPanel,
  ClustersTabPanel,
} from './TabPanels'

export default function SubstackTrendsModern() {
  const [trends, setTrends] = useState<TrendData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [days, setDays] = useState('7')
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    fetchTrends()
  }, [days])

  const fetchTrends = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await http.get(`/api/substack/trends?days=${days}`)
      setTrends(response.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  const handleRefresh = () => {
    setRefreshing(true)
    fetchTrends()
  }

  if (loading || !trends) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading trend analysis...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="container mx-auto p-4 max-w-7xl">
        <Alert className="bg-red-50 border-red-200">
          <AlertCircle className="h-4 w-4 text-red-600" />
          <AlertDescription className="text-red-800">
            Failed to load trends: {error}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Newsletter Trend Analysis</h1>
            <p className="text-gray-600">
              Analyzing {trends?.total_articles || 0} articles from {formatDate(trends?.date_range?.start || '')} to {formatDate(trends?.date_range?.end || '')}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Select value={days} onValueChange={setDays}>
              <SelectTrigger className="w-40">
                <Clock className="h-4 w-4 mr-2" />
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="3">Last 3 days</SelectItem>
                <SelectItem value="7">Last week</SelectItem>
                <SelectItem value="14">Last 2 weeks</SelectItem>
                <SelectItem value="30">Last month</SelectItem>
              </SelectContent>
            </Select>
            <Button
              onClick={handleRefresh}
              disabled={refreshing}
              variant="outline"
            >
              <RefreshCw className={cn("h-4 w-4 mr-2", refreshing && "animate-spin")} />
              Refresh
            </Button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Articles</p>
                <p className="text-2xl font-bold">{trends?.total_articles || 0}</p>
              </div>
              <FileText className="h-8 w-8 text-blue-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Authors</p>
                <p className="text-2xl font-bold">{trends?.author_trends?.total_authors || 0}</p>
              </div>
              <Users className="h-8 w-8 text-green-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Unique Tags</p>
                <p className="text-2xl font-bold">{trends?.tag_trends?.unique_tags || 0}</p>
              </div>
              <Hash className="h-8 w-8 text-purple-500 opacity-20" />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-gray-500">Highlights</p>
                <p className="text-2xl font-bold">{trends?.snippet_insights?.total_snippets || 0}</p>
              </div>
              <MessageSquare className="h-8 w-8 text-orange-500 opacity-20" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Content */}
      <Tabs defaultValue="overview" className="space-y-4">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="topics">Topics</TabsTrigger>
          <TabsTrigger value="authors">Authors</TabsTrigger>
          <TabsTrigger value="velocity">Velocity</TabsTrigger>
          <TabsTrigger value="clusters">Clusters</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Key Insights */}
            {trends?.summary?.key_insights?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-yellow-500" />
                    Key Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {(trends?.summary?.key_insights || []).map((insight, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <ChevronRight className="h-4 w-4 text-gray-400 mt-0.5 flex-shrink-0" />
                        <span className="text-sm">{insight}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            )}

            {/* Emerging Themes */}
            {trends?.emerging_themes?.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Rocket className="h-5 w-5 text-purple-500" />
                    Emerging Themes
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {(trends?.emerging_themes || []).slice(0, 5).map((theme, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50">
                        <div className="flex items-center gap-2">
                          {theme.type === 'new' ? (
                            <Sparkles className="h-4 w-4 text-purple-500" />
                          ) : (
                            <TrendingUp className="h-4 w-4 text-green-500" />
                          )}
                          <span className="text-sm font-medium">{theme.theme}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant={theme.type === 'new' ? 'secondary' : 'outline'}>
                            {theme.type === 'new' ? 'New' : 'Growing'}
                          </Badge>
                          <span className="text-xs text-gray-500">{theme.growth}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Hot Topics */}
          {trends?.topic_trends?.top_topics?.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Flame className="h-5 w-5 text-red-500" />
                  Hot Topics
                </CardTitle>
                <CardDescription>Most discussed topics in newsletters</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {(trends?.topic_trends?.top_topics || []).slice(0, 10).map((topic, idx) => {
                    const maxScore = trends?.topic_trends?.top_topics?.[0]?.score || 1
                    const percentage = (topic.score / maxScore) * 100

                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium">{topic.term}</span>
                          <Badge variant="secondary" className="text-xs">
                            {topic.articles} articles
                          </Badge>
                        </div>
                        <Progress value={percentage} className="h-2" />
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="topics" className="space-y-4">
          <TopicsTabPanel trends={trends} />
        </TabsContent>

        <TabsContent value="authors" className="space-y-4">
          <AuthorsTabPanel trends={trends} />
        </TabsContent>

        <TabsContent value="velocity" className="space-y-4">
          <VelocityTabPanel trends={trends} />
        </TabsContent>

        <TabsContent value="clusters" className="space-y-4">
          <ClustersTabPanel trends={trends} />
        </TabsContent>
      </Tabs>

      {/* Important Snippets */}
      {trends?.snippet_insights?.important_highlights?.length > 0 && (
        <Card className="mt-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-5 w-5" />
              Important Highlights
            </CardTitle>
            <CardDescription>Key insights from article snippets</CardDescription>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[400px]">
              <div className="space-y-3">
                {(trends?.snippet_insights?.important_highlights || []).slice(0, 5).map((snippet, idx) => (
                  <Card key={idx}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-2">
                        <Badge variant="outline">{snippet.category}</Badge>
                        <span className="text-xs text-gray-500">{snippet.article}</span>
                      </div>
                      <blockquote className="border-l-4 border-gray-200 pl-4 italic text-gray-700">
                        "{snippet.text}"
                      </blockquote>
                      {snippet.annotation && (
                        <div className="mt-2 text-sm text-gray-600 flex items-start gap-2">
                          <BookOpen className="h-4 w-4 mt-0.5 flex-shrink-0" />
                          <span>{snippet.annotation}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
