import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  TrendingUp,
  Users,
  BookOpen,
  GitBranch,
  Twitter,
  FileText,
  Calendar,
  Hash,
  Link2,
  BarChart3,
  Activity,
  Sparkles,
  Clock,
  AlertCircle,
  Loader2,
  ExternalLink,
  ChevronRight,
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface PopularPaper {
  id: number
  title: string
  abstract?: string
  publication_date?: string
  citation_count: number
  tag_count: number
  snippet_count: number
  popularity_score: number
  authors: Array<{ name: string; affiliation?: string }>
}

interface EmergingTopic {
  tag: string
  recent_count: number
  older_count: number
  growth_rate: number
  is_new: boolean
  sample_papers: Array<{ id: number; title: string }>
}

interface ActiveAuthor {
  name: string
  paper_count: number
  affiliations: string[]
  top_topics: Array<{ tag: string; count: number }>
  recent_papers: Array<{ id: number; title: string }>
}

interface TimelineItem {
  type: 'paper' | 'tweet' | 'article'
  id: string | number
  title?: string
  text?: string
  timestamp: string
  author?: string
  authors?: string[]
  publication_date?: string
}

interface PaperImpact {
  paper: {
    id: number
    title: string
    publication_date?: string
    citation_count?: number
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

export default function PaperTrendsDashboard() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('popular')
  
  // Data states
  const [popularPapers, setPopularPapers] = useState<PopularPaper[]>([])
  const [emergingTopics, setEmergingTopics] = useState<EmergingTopic[]>([])
  const [activeAuthors, setActiveAuthors] = useState<ActiveAuthor[]>([])
  const [timeline, setTimeline] = useState<TimelineItem[]>([])
  const [selectedPaperImpact, setSelectedPaperImpact] = useState<PaperImpact | null>(null)

  useEffect(() => {
    fetchDataForTab(activeTab)
  }, [activeTab])

  const fetchDataForTab = async (tab: string) => {
    setLoading(true)
    setError(null)
    
    try {
      switch (tab) {
        case 'popular':
          await fetchPopularPapers()
          break
        case 'emerging':
          await fetchEmergingTopics()
          break
        case 'authors':
          await fetchActiveAuthors()
          break
        case 'timeline':
          await fetchUnifiedTimeline()
          break
      }
    } catch (err: any) {
      setError(err.message || 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const fetchPopularPapers = async () => {
    const response = await axios.get('http://localhost:8000/api/papers/trends/popular')
    setPopularPapers(response.data.papers)
  }

  const fetchEmergingTopics = async () => {
    const response = await axios.get('http://localhost:8000/api/papers/trends/emerging-topics')
    setEmergingTopics(response.data.emerging_topics)
  }

  const fetchActiveAuthors = async () => {
    const response = await axios.get('http://localhost:8000/api/papers/trends/active-authors')
    setActiveAuthors(response.data.authors)
  }

  const fetchUnifiedTimeline = async () => {
    const response = await axios.get('http://localhost:8000/api/papers/trends/unified-timeline')
    setTimeline(response.data.timeline)
  }

  const fetchPaperImpact = async (paperId: number) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/papers/trends/research-impact/${paperId}`)
      setSelectedPaperImpact(response.data)
    } catch (err) {
      console.error('Failed to fetch paper impact:', err)
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const getGrowthBadgeColor = (rate: number) => {
    if (rate >= 5) return 'bg-red-500'
    if (rate >= 2) return 'bg-orange-500'
    if (rate >= 1) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getTimelineIcon = (type: string) => {
    switch (type) {
      case 'paper':
        return <BookOpen className="h-4 w-4" />
      case 'tweet':
        return <Twitter className="h-4 w-4" />
      case 'article':
        return <FileText className="h-4 w-4" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      {/* Header */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl flex items-center gap-2">
                <BarChart3 className="h-6 w-6" />
                Paper Trends & Analytics
              </CardTitle>
              <CardDescription>
                Analyze research trends, cross-source impact, and emerging topics
              </CardDescription>
            </div>
            <Badge variant="outline" className="text-sm">
              Phase 4: Cross-Source Integration
            </Badge>
          </div>
        </CardHeader>
      </Card>

      {error && (
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid grid-cols-4 w-full mb-6">
          <TabsTrigger value="popular">
            <TrendingUp className="h-4 w-4 mr-2" />
            Popular Papers
          </TabsTrigger>
          <TabsTrigger value="emerging">
            <Sparkles className="h-4 w-4 mr-2" />
            Emerging Topics
          </TabsTrigger>
          <TabsTrigger value="authors">
            <Users className="h-4 w-4 mr-2" />
            Active Authors
          </TabsTrigger>
          <TabsTrigger value="timeline">
            <Clock className="h-4 w-4 mr-2" />
            Unified Timeline
          </TabsTrigger>
        </TabsList>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin" />
          </div>
        ) : (
          <>
            {/* Popular Papers Tab */}
            <TabsContent value="popular" className="space-y-4">
              {popularPapers.map((paper) => (
                <Card 
                  key={paper.id} 
                  className="cursor-pointer hover:shadow-lg transition-shadow"
                  onClick={() => fetchPaperImpact(paper.id)}
                >
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-3">
                      <h3 className="text-lg font-semibold line-clamp-2 flex-1">
                        {paper.title}
                      </h3>
                      <Badge variant="secondary" className="ml-2">
                        Score: {paper.popularity_score}
                      </Badge>
                    </div>
                    
                    {paper.abstract && (
                      <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                        {paper.abstract}
                      </p>
                    )}
                    
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="h-3 w-3" />
                        {formatDate(paper.publication_date)}
                      </span>
                      <span className="flex items-center gap-1">
                        <Link2 className="h-3 w-3" />
                        {paper.citation_count} citations
                      </span>
                      <span className="flex items-center gap-1">
                        <Hash className="h-3 w-3" />
                        {paper.tag_count} tags
                      </span>
                      <span className="flex items-center gap-1">
                        <FileText className="h-3 w-3" />
                        {paper.snippet_count} snippets
                      </span>
                    </div>
                    
                    {paper.authors.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {paper.authors.map((author, idx) => (
                          <Badge key={idx} variant="outline" className="text-xs">
                            {author.name}
                            {author.affiliation && (
                              <span className="ml-1 text-gray-400">
                                ({author.affiliation})
                              </span>
                            )}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </TabsContent>

            {/* Emerging Topics Tab */}
            <TabsContent value="emerging" className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {emergingTopics.map((topic) => (
                  <Card key={topic.tag}>
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Badge>{topic.tag}</Badge>
                          {topic.is_new && (
                            <Badge variant="secondary" className="bg-green-100">
                              NEW
                            </Badge>
                          )}
                        </div>
                        <Badge 
                          className={cn(
                            "text-white",
                            getGrowthBadgeColor(topic.growth_rate)
                          )}
                        >
                          {topic.growth_rate === Infinity 
                            ? 'New!' 
                            : `${(topic.growth_rate * 100).toFixed(0)}% growth`}
                        </Badge>
                      </div>
                      
                      <div className="flex justify-between text-sm text-gray-600 mb-3">
                        <span>Recent: {topic.recent_count} papers</span>
                        <span>Previous: {topic.older_count} papers</span>
                      </div>
                      
                      {topic.sample_papers.length > 0 && (
                        <div className="space-y-1">
                          <p className="text-xs text-gray-500 font-medium">Sample papers:</p>
                          {topic.sample_papers.map((paper) => (
                            <div 
                              key={paper.id}
                              className="text-xs text-gray-600 truncate hover:text-blue-600 cursor-pointer"
                            >
                              <ChevronRight className="inline h-3 w-3" />
                              {paper.title}
                            </div>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            {/* Active Authors Tab */}
            <TabsContent value="authors" className="space-y-4">
              {activeAuthors.map((author) => (
                <Card key={author.name}>
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="text-lg font-semibold">{author.name}</h3>
                        {author.affiliations.length > 0 && (
                          <p className="text-sm text-gray-500">
                            {author.affiliations.join(', ')}
                          </p>
                        )}
                      </div>
                      <Badge>{author.paper_count} papers</Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">Top Topics</p>
                        <div className="flex flex-wrap gap-1">
                          {author.top_topics.map((topic) => (
                            <Badge 
                              key={topic.tag} 
                              variant="secondary"
                              className="text-xs"
                            >
                              {topic.tag} ({topic.count})
                            </Badge>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <p className="text-sm font-medium text-gray-700 mb-2">Recent Papers</p>
                        <div className="space-y-1">
                          {author.recent_papers.map((paper) => (
                            <div 
                              key={paper.id}
                              className="text-xs text-gray-600 truncate hover:text-blue-600 cursor-pointer"
                            >
                              {paper.title}
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </TabsContent>

            {/* Unified Timeline Tab */}
            <TabsContent value="timeline">
              <ScrollArea className="h-[600px]">
                <div className="space-y-3">
                  {timeline.map((item, idx) => (
                    <Card key={`${item.type}-${item.id}-${idx}`}>
                      <CardContent className="p-4">
                        <div className="flex items-start gap-3">
                          <div className={cn(
                            "p-2 rounded-full",
                            item.type === 'paper' && "bg-blue-100",
                            item.type === 'tweet' && "bg-green-100",
                            item.type === 'article' && "bg-purple-100"
                          )}>
                            {getTimelineIcon(item.type)}
                          </div>
                          
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline" className="text-xs">
                                {item.type}
                              </Badge>
                              <span className="text-xs text-gray-500">
                                {formatDate(item.timestamp)}
                              </span>
                            </div>
                            
                            {item.title && (
                              <p className="font-medium text-sm mb-1">{item.title}</p>
                            )}
                            {item.text && (
                              <p className="text-sm text-gray-600 line-clamp-2">{item.text}</p>
                            )}
                            
                            <div className="mt-2 text-xs text-gray-500">
                              {item.author && <span>By {item.author}</span>}
                              {item.authors && item.authors.length > 0 && (
                                <span>By {item.authors.join(', ')}</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          </>
        )}
      </Tabs>

      {/* Paper Impact Modal */}
      {selectedPaperImpact && (
        <Card className="fixed bottom-4 right-4 w-96 shadow-2xl z-50">
          <CardHeader className="pb-3">
            <div className="flex justify-between items-start">
              <CardTitle className="text-sm">Research Impact</CardTitle>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setSelectedPaperImpact(null)}
              >
                ×
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm font-medium line-clamp-2">
              {selectedPaperImpact.paper.title}
            </p>
            
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-1">
                <Activity className="h-3 w-3" />
                Impact Score: {selectedPaperImpact.impact_metrics.impact_score}
              </div>
              <div className="flex items-center gap-1">
                <Link2 className="h-3 w-3" />
                Citations: {selectedPaperImpact.impact_metrics.citation_count}
              </div>
              <div className="flex items-center gap-1">
                <Twitter className="h-3 w-3" />
                Tweets: {selectedPaperImpact.impact_metrics.tweet_mentions}
              </div>
              <div className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                Articles: {selectedPaperImpact.impact_metrics.article_mentions}
              </div>
            </div>
            
            {selectedPaperImpact.tags.length > 0 && (
              <div className="flex flex-wrap gap-1">
                {selectedPaperImpact.tags.slice(0, 5).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}