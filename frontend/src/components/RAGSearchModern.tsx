import React, { useState, useEffect, Suspense } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  Search,
  RefreshCw,
  ChevronRight,
  MessageSquare,
  TrendingUp,
  Newspaper,
  Twitter,
  User,
  Calendar,
  Hash,
  FileText,
  ExternalLink,
  Clock,
  Database,
  CheckCircle,
  AlertCircle,
  Loader2,
  GraduationCap,
  Copy,
  Check
} from 'lucide-react'
import UnifiedModelSelector from './UnifiedModelSelector'

// Lazy-loaded components for code-splitting (reduces initial bundle size)
const ArticleViewerModern = React.lazy(() => import('./ArticleViewerModern'))
import { useModelSelector } from '@/hooks/useModelSelector'
import { cn } from "@/lib/utils"

interface Source {
  type: 'tweet' | 'article' | 'snippet' | 'paper'
  id: string
  paper_id?: string
  score: number
  content_preview: string
  content?: string
  metadata: any
  navigate_to?: string
  display_title?: string
  url?: string
  author?: string
  created_at?: string
  published_at?: string
  tags?: string[]
  title?: string
  annotation?: string
  article_id?: string
  category?: string
  authors?: string[] | string
  conference?: string
}

interface RAGResponse {
  question: string
  answer: string
  sources: Source[]
  model_used?: string
  timestamp?: string
  search_intent?: {
    is_article_search: boolean
    is_tweet_search: boolean
    is_general_question: boolean
  }
  primary_results?: Source[]
  total_sources?: number
  index_stats?: {
    total_documents: number
    last_updated: string | null
  }
  is_trend_analysis?: boolean
  documents_analyzed?: number
  source_type?: string
}

interface IndexStats {
  indexed_documents: number
  is_ready: boolean
  is_building: boolean
  last_updated?: string
  current_step?: string
  progress_percent?: number
  error?: string
  tweets?: number
  articles?: number
  papers?: number
}

interface SampleQuestions {
  [key: string]: string[]
}

export default function RAGSearchModern() {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [response, setResponse] = useState<RAGResponse | null>(null)
  const [sampleQuestions, setSampleQuestions] = useState<SampleQuestions | null>(null)
  const [activeCategory, setActiveCategory] = useState<string>('general')
  const [searchHistory, setSearchHistory] = useState<string[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [rebuildingIndex, setRebuildingIndex] = useState(false)
  const [indexStats, setIndexStats] = useState<IndexStats | null>(null)
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null)
  
  // Content type filters
  const [includeTweets, setIncludeTweets] = useState(true)
  const [includeArticles, setIncludeArticles] = useState(true)
  const [includePapers, setIncludePapers] = useState(true)

  // Copy to clipboard state
  const [answerCopied, setAnswerCopied] = useState(false)

  // Copy answer to clipboard
  const copyAnswerToClipboard = async () => {
    if (response?.answer) {
      await navigator.clipboard.writeText(response.answer)
      setAnswerCopied(true)
      setTimeout(() => setAnswerCopied(false), 2000)
    }
  }

  // Use unified model selector hook for RAG search
  const {
    selectedModel: ragModel,
    loading: modelLoading,
    selectModel: selectRagModel
  } = useModelSelector('rag_answer')

  // Helper function to generate search message based on selected content types
  const getSearchingMessage = () => {
    const types: string[] = []
    if (includeTweets) types.push('tweets')
    if (includeArticles) types.push('articles')
    if (includePapers) types.push('research papers')
    
    if (types.length === 0) {
      return 'Please select at least one content type to search...'
    } else if (types.length === 1) {
      return `Searching through ${types[0]}...`
    } else if (types.length === 2) {
      return `Searching through ${types[0]} and ${types[1]}...`
    } else {
      return `Searching through ${types.slice(0, -1).join(', ')}, and ${types[types.length - 1]}...`
    }
  }

  useEffect(() => {
    loadSampleQuestions()
    loadSearchHistory()
    loadIndexStats()
    
    // Refresh index stats every 5 seconds if building
    const interval = setInterval(() => {
      if (indexStats && indexStats.is_building) {
        loadIndexStats()
      }
    }, 5000)
    
    return () => clearInterval(interval)
  }, [indexStats?.is_building])

  const loadSampleQuestions = async () => {
    try {
      const response = await axios.get('/api/rag/sample-questions')
      
      if (Array.isArray(response.data)) {
        // Convert array to categorized object
        const questions = response.data
        setSampleQuestions({
          general: questions.slice(0, 3),
          trends: questions.slice(3, 6),
          articles: questions.slice(6, 9),
          tweets: questions.slice(9, 12)
        })
      } else {
        setSampleQuestions(response.data)
      }
    } catch (error) {
      console.error('Error loading sample questions:', error)
      // Set default questions
      setSampleQuestions({
        general: [
          'What are the latest developments in AI?',
          'Which articles discuss Claude and Anthropic?',
          'What did Sam Altman tweet about recently?'
        ],
        papers: [
          'What are the state-of-the-art methods in LLM research?',
          'Which papers discuss transformer architectures?',
          'What research has been done on AI safety and alignment?',
          'Find papers about multimodal learning',
          'What are the latest papers on reinforcement learning?',
          'Which papers cite GPT-4 or Claude?'
        ],
        trends: [
          'What are the key trends in machine learning?',
          'Show me emerging topics in AI',
          'What are the hot topics this week?'
        ],
        articles: [
          'Which newsletters talk about AI safety?',
          'Find articles about GPT models',
          "Show me Ethan Mollick's latest insights"
        ],
        tweets: [
          'Find tweets about open source LLMs',
          'What are people saying about AI regulation?',
          'Show recent tweets from AI researchers'
        ]
      })
    }
  }

  const loadSearchHistory = () => {
    const history = localStorage.getItem('rag_search_history')
    if (history) {
      setSearchHistory(JSON.parse(history))
    }
  }

  const loadIndexStats = async () => {
    try {
      const response = await axios.get('/api/rag/stats')
      setIndexStats(response.data)
    } catch (error) {
      console.error('Error loading index stats:', error)
    }
  }

  const handleSearch = async (searchQuestion?: string) => {
    const queryText = searchQuestion || question
    if (!queryText.trim()) return

    setLoading(true)
    setResponse(null)

    // Build content types filter
    const contentTypes = []
    if (includeTweets) contentTypes.push('tweet')
    if (includeArticles) contentTypes.push('article')
    if (includePapers) contentTypes.push('paper')

    try {
      const result = await axios.post('/api/rag/ask', {
        question: queryText,
        k: 10,
        content_types: contentTypes.length > 0 ? contentTypes : null,
        model: ragModel || undefined
      })

      setResponse(result.data)

      // Update search history
      const updatedHistory = [queryText, ...searchHistory.filter(q => q !== queryText)].slice(0, 10)
      setSearchHistory(updatedHistory)
      localStorage.setItem('rag_search_history', JSON.stringify(updatedHistory))
    } catch (error) {
      console.error('Error searching:', error)
      alert('Failed to search. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  const rebuildIndex = async () => {
    if (!confirm('Rebuild the RAG index? This may take a few minutes.')) return

    setRebuildingIndex(true)
    try {
      const result = await axios.post('/api/rag/rebuild')
      alert(result.data.message || 'Index rebuild started successfully!')
      setTimeout(() => loadIndexStats(), 2000)
    } catch (error) {
      console.error('Error rebuilding index:', error)
      alert('Failed to rebuild index. Make sure the server is running.')
    } finally {
      setRebuildingIndex(false)
    }
  }

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'general': return <MessageSquare className="w-4 h-4" />
      case 'papers': return <GraduationCap className="w-4 h-4" />
      case 'trends': return <TrendingUp className="w-4 h-4" />
      case 'articles': return <Newspaper className="w-4 h-4" />
      case 'tweets': return <Twitter className="w-4 h-4" />
      default: return <Search className="w-4 h-4" />
    }
  }

  const getCategoryLabel = (category: string) => {
    return category.charAt(0).toUpperCase() + category.slice(1)
  }

  const getSourceIcon = (type: string) => {
    switch (type) {
      case 'tweet': return <Twitter className="w-4 h-4" />
      case 'article': return <Newspaper className="w-4 h-4" />
      case 'paper': return <GraduationCap className="w-4 h-4" />
      case 'snippet': return <FileText className="w-4 h-4" />
      default: return <FileText className="w-4 h-4" />
    }
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return ''
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric'
    })
  }

  const getRelevanceColor = (score: number) => {
    if (score > 0.8) return 'bg-green-500'
    if (score > 0.6) return 'bg-blue-500'
    if (score > 0.4) return 'bg-yellow-500'
    return 'bg-gray-500'
  }

  const getRelevanceLabel = (score: number) => {
    if (score > 0.8) return 'Very High'
    if (score > 0.6) return 'High'
    if (score > 0.4) return 'Medium'
    return 'Low'
  }

  const navigateToSource = (source: Source) => {
    // Handle tweets - open in Twitter/X
    if (source.type === 'tweet') {
      // Check for URL in various places
      const tweetUrl = source.url || source.metadata?.url || source.navigate_to
      if (tweetUrl) {
        window.open(tweetUrl, '_blank')
      } else if (source.metadata?.id || source.id) {
        // Construct Twitter URL if we have the tweet ID
        const tweetId = source.metadata?.id || source.id
        const authorUsername = source.metadata?.author || source.author || 'x'
        const constructedUrl = `https://twitter.com/${authorUsername}/status/${tweetId}`
        window.open(constructedUrl, '_blank')
      }
    } 
    // Handle articles - open in ArticleViewer modal
    else if (source.type === 'article') {
      // Extract article ID from various sources
      const articleId = source.id?.replace('article_', '') || 
                       source.article_id || 
                       source.metadata?.id?.replace('article_', '') ||
                       (source.metadata?.url && source.metadata.url.split('/').pop()) ||
                       (source.url && source.url.split('/').pop()) || ''
      if (articleId) {
        setSelectedArticleId(articleId)
      } else if (source.metadata?.url || source.url) {
        // If we have a URL but no ID, try to open it directly
        window.open(source.metadata?.url || source.url, '_blank')
      }
    } 
    // Handle papers - navigate to paper viewer
    else if (source.type === 'paper') {
      const paperId = source.id?.replace('paper_', '') || 
                     source.paper_id || 
                     source.metadata?.id?.replace('paper_', '') ||
                     source.metadata?.paper_id
      if (paperId) {
        // Navigate to the papers dashboard with the specific paper selected
        window.location.href = `/papers?id=${paperId}`
      } else if (source.metadata?.arxiv_id) {
        // If we have an arXiv ID, open it on arXiv
        window.open(`https://arxiv.org/abs/${source.metadata.arxiv_id}`, '_blank')
      } else if (source.metadata?.doi) {
        // If we have a DOI, open it
        window.open(`https://doi.org/${source.metadata.doi}`, '_blank')
      }
    }
    // Handle snippets - open the parent article
    else if (source.type === 'snippet') {
      const articleId = source.article_id || 
                       source.metadata?.article_id ||
                       source.id?.replace('snippet_', '').split('_')[0]
      if (articleId) {
        setSelectedArticleId(articleId)
      }
    }
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <CardTitle className="text-2xl flex items-center gap-2">
                <Search className="w-6 h-6" />
                AI-Powered Search
              </CardTitle>
              <CardDescription>
                Ask questions about tweets, articles, and research papers using natural language
              </CardDescription>
            </div>
            {indexStats && (
              <div className="flex items-center gap-4">
                <div className="text-sm text-muted-foreground space-y-1">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    <span>{indexStats.indexed_documents || 0} documents</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {indexStats.is_ready ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Ready</span>
                      </>
                    ) : indexStats.is_building ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-yellow-500" />
                        <span>Building...</span>
                        {indexStats.progress_percent !== undefined && (
                          <span>({indexStats.progress_percent}%)</span>
                        )}
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-4 h-4 text-red-500" />
                        <span>Not Ready</span>
                      </>
                    )}
                  </div>
                  {indexStats.current_step && (
                    <div className="text-xs">{indexStats.current_step}</div>
                  )}
                  {indexStats.progress_percent !== undefined && indexStats.progress_percent < 100 && !indexStats.is_ready && (
                    <div className="text-xs">
                      Progress: {indexStats.progress_percent}%
                    </div>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={rebuildIndex}
                  disabled={rebuildingIndex || indexStats.is_building}
                >
                  {rebuildingIndex ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Rebuilding...
                    </>
                  ) : (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2" />
                      Rebuild Index
                    </>
                  )}
                </Button>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Search Input */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {/* Content Type Filters */}
            <div className="flex items-center gap-6 pb-2">
              <span className="text-sm font-medium text-muted-foreground">Search in:</span>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeTweets}
                  onChange={(e) => setIncludeTweets(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm flex items-center gap-1">
                  <Twitter className="h-3 w-3" />
                  Tweets ({indexStats?.tweets || 0})
                </span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includeArticles}
                  onChange={(e) => setIncludeArticles(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm flex items-center gap-1">
                  <Newspaper className="h-3 w-3" />
                  Articles ({indexStats?.articles || 0})
                </span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={includePapers}
                  onChange={(e) => setIncludePapers(e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="text-sm flex items-center gap-1">
                  <GraduationCap className="h-3 w-3" />
                  Papers ({indexStats?.papers || 0})
                </span>
              </label>
            </div>

            {/* Trend Quick Actions */}
            <div className="flex flex-wrap gap-2 pt-2 border-t">
              <span className="text-xs font-medium text-muted-foreground mr-2 self-center">Quick Actions:</span>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIncludeTweets(true)
                  setIncludeArticles(false)
                  setIncludePapers(false)
                  setQuestion("What are the key trends on Twitter?")
                  setTimeout(() => handleSearch("What are the key trends on Twitter?"), 100)
                }}
                className="flex items-center gap-1.5"
                disabled={loading}
              >
                <TrendingUp className="w-3.5 h-3.5" />
                <Twitter className="w-3.5 h-3.5" />
                Trending on Twitter
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIncludeTweets(false)
                  setIncludeArticles(false)
                  setIncludePapers(true)
                  setQuestion("What are the key trends in research papers?")
                  setTimeout(() => handleSearch("What are the key trends in research papers?"), 100)
                }}
                className="flex items-center gap-1.5"
                disabled={loading}
              >
                <TrendingUp className="w-3.5 h-3.5" />
                <GraduationCap className="w-3.5 h-3.5" />
                Trending in Papers
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setIncludeTweets(false)
                  setIncludeArticles(true)
                  setIncludePapers(false)
                  setQuestion("What are the hot topics in articles?")
                  setTimeout(() => handleSearch("What are the hot topics in articles?"), 100)
                }}
                className="flex items-center gap-1.5"
                disabled={loading}
              >
                <TrendingUp className="w-3.5 h-3.5" />
                <Newspaper className="w-3.5 h-3.5" />
                Hot Topics in Articles
              </Button>
            </div>

            {/* AI Model Selection for RAG Search */}
            <div className="pt-2 border-t">
              <UnifiedModelSelector
                taskType="rag_answer"
                value={ragModel || ''}
                onValueChange={selectRagModel}
                label="AI Model for Answer Generation"
                description="Choose the AI model to generate answers from retrieved content"
                disabled={modelLoading || loading}
                compact={false}
              />
            </div>

            <div className="flex gap-2">
              <textarea
                className="flex-1 min-h-[80px] px-3 py-2 text-sm rounded-md border border-input bg-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring resize-none"
                placeholder="Ask a question... (e.g., 'Which articles talk about Claude?' or 'What are the latest GPT-5 developments?')"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyPress={handleKeyPress}
              />
              <Button
                onClick={() => handleSearch()}
                disabled={loading || !question.trim() || (!includeTweets && !includeArticles && !includePapers) || !ragModel}
                size="lg"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2" />
                    Search
                  </>
                )}
              </Button>
            </div>

            {/* Search History */}
            {searchHistory.length > 0 && (
              <div className="space-y-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowHistory(!showHistory)}
                  className="flex items-center gap-2"
                >
                  <Clock className="w-4 h-4" />
                  Recent Searches
                  <ChevronRight className={cn(
                    "w-4 h-4 transition-transform",
                    showHistory && "rotate-90"
                  )} />
                </Button>
                {showHistory && (
                  <ScrollArea className="h-32 rounded-md border p-2">
                    <div className="space-y-1">
                      {searchHistory.map((q, i) => (
                        <Button
                          key={i}
                          variant="ghost"
                          size="sm"
                          className="w-full justify-start text-left"
                          onClick={() => {
                            setQuestion(q)
                            handleSearch(q)
                          }}
                        >
                          {q}
                        </Button>
                      ))}
                    </div>
                  </ScrollArea>
                )}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Sample Questions */}
      {!response && sampleQuestions && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Try these sample questions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-2 flex-wrap">
                {Object.keys(sampleQuestions).map((category) => (
                  <Button
                    key={category}
                    variant={activeCategory === category ? "default" : "outline"}
                    size="sm"
                    onClick={() => setActiveCategory(category)}
                    className="flex items-center gap-2"
                  >
                    {getCategoryIcon(category)}
                    {getCategoryLabel(category)}
                  </Button>
                ))}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                {sampleQuestions[activeCategory]?.map((q, i) => (
                  <Button
                    key={i}
                    variant="outline"
                    className="text-left justify-start h-auto p-3"
                    onClick={() => {
                      setQuestion(q)
                      handleSearch(q)
                    }}
                  >
                    <span className="line-clamp-2">{q}</span>
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Loading State */}
      {loading && (
        <Card>
          <CardContent className="py-12">
            <div className="flex flex-col items-center justify-center space-y-4">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
              <p className="text-muted-foreground">{getSearchingMessage()}</p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {response && (
        <div className="space-y-6">
          {/* Answer */}
          <Card className={response.is_trend_analysis ? "border-blue-300 bg-blue-50/50" : ""}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  {response.is_trend_analysis && (
                    <TrendingUp className="w-5 h-5 text-blue-600" />
                  )}
                  {response.is_trend_analysis ? "Trend Analysis" : "Answer"}
                </CardTitle>
                <div className="flex items-center gap-2">
                  {response.is_trend_analysis && response.documents_analyzed && (
                    <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300">
                      Analyzed {response.documents_analyzed} {response.source_type || 'documents'}
                    </Badge>
                  )}
                  {response.model_used && (
                    <Badge variant="secondary">{response.model_used}</Badge>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={copyAnswerToClipboard}
                    className="h-8 w-8 p-0"
                    title="Copy to clipboard"
                  >
                    {answerCopied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="prose prose-sm max-w-none">
                <ReactMarkdown>{response.answer}</ReactMarkdown>
              </div>
            </CardContent>
          </Card>

          {/* Sources */}
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                {response.search_intent?.is_article_search ? (
                  <>
                    <Newspaper className="w-5 h-5" />
                    Articles Found
                  </>
                ) : response.search_intent?.is_tweet_search ? (
                  <>
                    <Twitter className="w-5 h-5" />
                    Tweets Found
                  </>
                ) : (
                  <>
                    <Database className="w-5 h-5" />
                    Sources
                  </>
                )}
                {response.total_sources && (
                  <Badge variant="outline">{response.total_sources}</Badge>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {response.sources.map((source, i) => (
                  <SourceCard
                    key={i}
                    source={source}
                    onNavigate={() => navigateToSource(source)}
                    formatDate={formatDate}
                    getSourceIcon={getSourceIcon}
                    getRelevanceColor={getRelevanceColor}
                    getRelevanceLabel={getRelevanceLabel}
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Article Viewer Modal - Lazy loaded for code splitting */}
      {selectedArticleId && (
        <Suspense fallback={
          <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
            <div className="bg-white rounded-lg p-8 flex items-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600">Loading Article Viewer...</span>
            </div>
          </div>
        }>
          <ArticleViewerModern
            articleId={selectedArticleId}
            onClose={() => setSelectedArticleId(null)}
          />
        </Suspense>
      )}
    </div>
  )
}

interface SourceCardProps {
  source: Source
  onNavigate: () => void
  formatDate: (date?: string) => string
  getSourceIcon: (type: string) => React.ReactNode
  getRelevanceColor: (score: number) => string
  getRelevanceLabel: (score: number) => string
}

function SourceCard({ 
  source, 
  onNavigate, 
  formatDate, 
  getSourceIcon,
  getRelevanceColor,
  getRelevanceLabel
}: SourceCardProps) {
  return (
    <Card 
      className="cursor-pointer hover:shadow-lg transition-shadow hover:border-blue-300"
      onClick={(e) => {
        // Only navigate if clicking the card itself, not child buttons
        if (e.target === e.currentTarget || 
            !e.currentTarget.contains(e.target as Node) ||
            (e.target as HTMLElement).closest('button') === null) {
          onNavigate()
        }
      }}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-center gap-2 flex-1">
            {getSourceIcon(source.type)}
            <span className="font-medium text-sm">
              {source.type === 'paper' 
                ? (source.metadata?.title || source.title || 'Research Paper')
                : (source.display_title || source.title || source.type)}
            </span>
          </div>
          <Badge 
            className={cn(
              "text-xs text-white",
              getRelevanceColor(source.score)
            )}
          >
            {getRelevanceLabel(source.score)}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="text-sm text-muted-foreground line-clamp-3">
          {source.type === 'article' ? (
            <div className="prose prose-sm">
              <ReactMarkdown>
                {source.content_preview || source.content || 'No preview available'}
              </ReactMarkdown>
            </div>
          ) : (
            source.content_preview || source.content || 'No preview available'
          )}
        </div>
        
        <div className="flex items-center gap-2 text-xs text-muted-foreground flex-wrap">
          {source.type === 'tweet' && (
            <>
              {source.author && (
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  @{source.author}
                </div>
              )}
              {source.created_at && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(source.created_at)}
                </div>
              )}
              {source.tags && source.tags.length > 0 && (
                <div className="flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  {source.tags.slice(0, 3).join(', ')}
                </div>
              )}
            </>
          )}
          
          {source.type === 'article' && (
            <>
              {source.author && (
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {source.author}
                </div>
              )}
              {source.published_at && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(source.published_at)}
                </div>
              )}
            </>
          )}
          
          {source.type === 'paper' && (
            <>
              {(source.metadata?.authors || source.authors) && (
                <div className="flex items-center gap-1">
                  <User className="w-3 h-3" />
                  {Array.isArray(source.metadata?.authors) 
                    ? source.metadata.authors.slice(0, 2).join(', ') 
                    : Array.isArray(source.authors)
                    ? source.authors.slice(0, 2).join(', ')
                    : source.metadata?.authors || source.authors}
                  {((source.metadata?.authors?.length || source.authors?.length) > 2) && ' et al.'}
                </div>
              )}
              {(source.metadata?.publication_date || source.published_at) && (
                <div className="flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(source.metadata?.publication_date || source.published_at)}
                </div>
              )}
              {(source.metadata?.conference || source.conference) && (
                <div className="flex items-center gap-1">
                  <GraduationCap className="w-3 h-3" />
                  {source.metadata?.conference || source.conference}
                </div>
              )}
              {(source.metadata?.tags || source.tags) && (source.metadata?.tags || source.tags).length > 0 && (
                <div className="flex items-center gap-1">
                  <Hash className="w-3 h-3" />
                  {(source.metadata?.tags || source.tags).slice(0, 3).join(', ')}
                </div>
              )}
            </>
          )}
          
          {source.type === 'snippet' && source.annotation && (
            <div className="flex items-center gap-1">
              <FileText className="w-3 h-3" />
              {source.annotation}
            </div>
          )}
        </div>
        
        <div className="flex justify-end">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button 
                  variant="ghost" 
                  size="sm" 
                  className="flex items-center gap-1 text-blue-600 hover:text-blue-700"
                  onClick={(e) => {
                    e.stopPropagation()
                    onNavigate()
                  }}
                >
                  {source.type === 'tweet' ? (
                    <>
                      <Twitter className="w-3 h-3" />
                      View on X
                    </>
                  ) : source.type === 'article' ? (
                    <>
                      <FileText className="w-3 h-3" />
                      Read Article
                    </>
                  ) : (
                    <>
                      <Newspaper className="w-3 h-3" />
                      View Snippet
                    </>
                  )}
                  <ExternalLink className="w-3 h-3" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p className="text-xs">
                  {source.type === 'tweet' ? 'Open tweet in X/Twitter' :
                   source.type === 'article' ? 'Open article in viewer' :
                   'View snippet in article context'}
                </p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </CardContent>
    </Card>
  )
}