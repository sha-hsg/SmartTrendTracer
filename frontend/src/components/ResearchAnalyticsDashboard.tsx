import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  TrendingUp,
  Users,
  FileText,
  Network,
  BarChart3,
  Calendar,
  Hash,
  ArrowUpRight,
  ArrowDownRight,
  Loader2,
  AlertCircle,
  Sparkles,
  GitBranch,
  Target,
  Activity,
  MessageSquare
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { cn } from '@/lib/utils'

interface PopularPaper {
  id: number
  title: string
  abstract?: string
  citation_count: number
  tag_count: number
  snippet_count: number
  popularity_score: number
  authors: { name: string; affiliation?: string }[]
}

interface EmergingTopic {
  tag: string
  recent_count: number
  older_count: number
  growth_rate: number
  is_new: boolean
  sample_papers: { id: number; title: string }[]
}

interface ActiveAuthor {
  name: string
  paper_count: number
  affiliations: string[]
  top_topics: { tag: string; count: number }[]
  recent_papers: { id: number; title: string }[]
}

interface ResearchImpact {
  paper: {
    id: number
    title: string
    citation_count: number
  }
  impact_metrics: {
    impact_score: number
    citation_count: number
    tweet_mentions: number
    article_mentions: number
    tag_count: number
    snippet_count: number
  }
  tags: string[]
}

const ResearchAnalyticsDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // Data states
  const [popularPapers, setPopularPapers] = useState<PopularPaper[]>([])
  const [emergingTopics, setEmergingTopics] = useState<EmergingTopic[]>([])
  const [activeAuthors, setActiveAuthors] = useState<ActiveAuthor[]>([])
  const [selectedPaperImpact, setSelectedPaperImpact] = useState<ResearchImpact | null>(null)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const [papersRes, topicsRes, authorsRes] = await Promise.all([
        axios.get('http://localhost:8000/api/papers/trends/popular'),
        axios.get('http://localhost:8000/api/papers/trends/emerging-topics'),
        axios.get('http://localhost:8000/api/papers/trends/active-authors')
      ])
      
      setPopularPapers(papersRes.data.papers)
      setEmergingTopics(topicsRes.data.emerging_topics)
      setActiveAuthors(authorsRes.data.authors)
    } catch (err) {
      setError('Failed to load analytics data')
      console.error('Error fetching analytics:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchPaperImpact = async (paperId: number) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/papers/trends/research-impact/${paperId}`)
      setSelectedPaperImpact(response.data)
    } catch (err) {
      console.error('Error fetching paper impact:', err)
    }
  }

  const getGrowthIcon = (rate: number) => {
    if (rate > 1) return <ArrowUpRight className="h-4 w-4 text-green-500" />
    if (rate < -0.2) return <ArrowDownRight className="h-4 w-4 text-red-500" />
    return <Activity className="h-4 w-4 text-yellow-500" />
  }

  const formatGrowthRate = (rate: number) => {
    if (rate === 10) return 'New!'
    if (rate > 1) return `+${Math.round(rate * 100)}%`
    return `${Math.round(rate * 100)}%`
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="h-6 w-6" />
            Research Analytics & Trends
          </CardTitle>
          <CardDescription>
            Comprehensive analysis of research papers, trends, and impact across all sources
          </CardDescription>
        </CardHeader>
      </Card>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="trends">Emerging Trends</TabsTrigger>
          <TabsTrigger value="authors">Active Authors</TabsTrigger>
          <TabsTrigger value="impact">Impact Analysis</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Papers</p>
                    <p className="text-2xl font-bold">{popularPapers.length}</p>
                  </div>
                  <FileText className="h-8 w-8 text-blue-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Emerging Topics</p>
                    <p className="text-2xl font-bold">{emergingTopics.filter(t => t.is_new).length}</p>
                  </div>
                  <Sparkles className="h-8 w-8 text-yellow-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Active Authors</p>
                    <p className="text-2xl font-bold">{activeAuthors.length}</p>
                  </div>
                  <Users className="h-8 w-8 text-green-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Avg Citations</p>
                    <p className="text-2xl font-bold">
                      {Math.round(
                        popularPapers.reduce((acc, p) => acc + (p.citation_count || 0), 0) / 
                        (popularPapers.length || 1)
                      )}
                    </p>
                  </div>
                  <Target className="h-8 w-8 text-purple-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Popular Papers */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Most Popular Papers
              </CardTitle>
              <CardDescription>Papers with highest engagement and citations</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[400px]">
                <div className="space-y-4">
                  {popularPapers.map((paper, idx) => (
                    <div key={paper.id} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <Badge variant="outline">#{idx + 1}</Badge>
                            <Badge className="bg-blue-100 text-blue-700">
                              Score: {paper.popularity_score}
                            </Badge>
                          </div>
                          <h4 className="font-medium text-sm mb-1">{paper.title}</h4>
                          {paper.abstract && (
                            <p className="text-xs text-gray-600 line-clamp-2 mb-2">
                              {paper.abstract}
                            </p>
                          )}
                          <div className="flex items-center gap-4 text-xs text-gray-500">
                            <span className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              {paper.citation_count} citations
                            </span>
                            <span className="flex items-center gap-1">
                              <Hash className="h-3 w-3" />
                              {paper.tag_count} tags
                            </span>
                            <span className="flex items-center gap-1">
                              <MessageSquare className="h-3 w-3" />
                              {paper.snippet_count} snippets
                            </span>
                          </div>
                          {paper.authors.length > 0 && (
                            <div className="mt-2 text-xs text-gray-600">
                              Authors: {paper.authors.map(a => a.name).join(', ')}
                            </div>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => fetchPaperImpact(paper.id)}
                        >
                          View Impact
                          <ArrowUpRight className="h-3 w-3 ml-1" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="trends" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Emerging Research Topics
              </CardTitle>
              <CardDescription>Topics showing significant growth in recent activity</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {emergingTopics.map((topic) => (
                    <Card key={topic.tag} className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-medium">{topic.tag}</h4>
                            {topic.is_new && (
                              <Badge className="bg-green-100 text-green-700">New</Badge>
                            )}
                            <div className="flex items-center gap-1">
                              {getGrowthIcon(topic.growth_rate)}
                              <span className={cn(
                                "text-sm font-medium",
                                topic.growth_rate > 1 ? "text-green-600" : 
                                topic.growth_rate < -0.2 ? "text-red-600" : "text-yellow-600"
                              )}>
                                {formatGrowthRate(topic.growth_rate)}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-gray-600">Recent: {topic.recent_count}</p>
                          <p className="text-xs text-gray-500">Previous: {topic.older_count}</p>
                        </div>
                      </div>
                      
                      {/* Growth Visualization */}
                      <div className="mb-3">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-gray-500">Growth Rate</span>
                        </div>
                        <Progress 
                          value={Math.min(100, Math.max(0, topic.growth_rate * 10))} 
                          className="h-2"
                        />
                      </div>
                      
                      {/* Sample Papers */}
                      {topic.sample_papers.length > 0 && (
                        <div>
                          <p className="text-xs text-gray-600 mb-2">Recent papers:</p>
                          <div className="space-y-1">
                            {topic.sample_papers.map((paper) => (
                              <div key={paper.id} className="text-xs text-gray-700 pl-2 border-l-2 border-gray-200">
                                {paper.title}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="authors" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Most Active Researchers
              </CardTitle>
              <CardDescription>Authors with multiple papers and their research focus</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4">
                  {activeAuthors.map((author) => (
                    <Card key={author.name} className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div>
                          <h4 className="font-medium">{author.name}</h4>
                          {author.affiliations.length > 0 && (
                            <p className="text-xs text-gray-600">
                              {author.affiliations.join(' • ')}
                            </p>
                          )}
                        </div>
                        <Badge variant="outline">
                          {author.paper_count} papers
                        </Badge>
                      </div>
                      
                      {/* Research Topics */}
                      {author.top_topics.length > 0 && (
                        <div className="mb-3">
                          <p className="text-xs text-gray-600 mb-2">Research areas:</p>
                          <div className="flex flex-wrap gap-1">
                            {author.top_topics.map((topic) => (
                              <Badge key={topic.tag} variant="secondary" className="text-xs">
                                {topic.tag} ({topic.count})
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Recent Papers */}
                      {author.recent_papers.length > 0 && (
                        <div>
                          <p className="text-xs text-gray-600 mb-2">Recent papers:</p>
                          <div className="space-y-1">
                            {author.recent_papers.map((paper) => (
                              <div key={paper.id} className="text-xs text-gray-700 pl-2 border-l-2 border-gray-200">
                                {paper.title}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="impact" className="space-y-6">
          {selectedPaperImpact ? (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Target className="h-5 w-5" />
                  Research Impact Analysis
                </CardTitle>
                <CardDescription>{selectedPaperImpact.paper.title}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-6">
                  {/* Impact Score */}
                  <div>
                    <h4 className="font-medium mb-3">Impact Metrics</h4>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span className="text-sm">Overall Impact Score</span>
                        <Badge className="bg-blue-100 text-blue-700 text-lg px-3 py-1">
                          {selectedPaperImpact.impact_metrics.impact_score}
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Citations</span>
                          <span className="font-medium">{selectedPaperImpact.impact_metrics.citation_count}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Tweet Mentions</span>
                          <span className="font-medium">{selectedPaperImpact.impact_metrics.tweet_mentions}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Article Mentions</span>
                          <span className="font-medium">{selectedPaperImpact.impact_metrics.article_mentions}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Tags</span>
                          <span className="font-medium">{selectedPaperImpact.impact_metrics.tag_count}</span>
                        </div>
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-gray-600">Snippets</span>
                          <span className="font-medium">{selectedPaperImpact.impact_metrics.snippet_count}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  {/* Tags and Topics */}
                  <div>
                    <h4 className="font-medium mb-3">Research Topics</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedPaperImpact.tags.map((tag) => (
                        <Badge key={tag} variant="outline">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center h-64 text-gray-500">
                <AlertCircle className="h-12 w-12 mb-3 opacity-50" />
                <p>Select a paper from the Overview tab to view its impact analysis</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </div>
  )
}

export default ResearchAnalyticsDashboard