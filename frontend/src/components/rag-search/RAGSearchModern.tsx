import React, { useState, useEffect, Suspense } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { toast } from 'sonner'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import {
  Search,
  RefreshCw,
  TrendingUp,
  Newspaper,
  Twitter,
  Database,
  CheckCircle,
  AlertCircle,
  Loader2,
  Copy,
  Check
} from 'lucide-react'
import { useModelSelector } from '@/hooks/useModelSelector'
import SearchControls from './SearchControls'
import SearchResultCard, { Source } from './SearchResultCard'

const ArticleViewerModern = React.lazy(() => import('../article-viewer/ArticleViewerModern'))
const PaperViewerOptimized = React.lazy(() => import('../PaperViewerOptimized'))

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
  needs_rebuild?: boolean
}

interface IndexStats {
  indexed_documents: number
  is_ready: boolean
  last_updated?: string
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
  const [selectedPaperId, setSelectedPaperId] = useState<string | null>(null)

  const [includeTweets, setIncludeTweets] = useState(true)
  const [includeArticles, setIncludeArticles] = useState(true)
  const [includePapers, setIncludePapers] = useState(true)

  const [answerCopied, setAnswerCopied] = useState(false)

  const copyAnswerToClipboard = async () => {
    if (response?.answer) {
      await navigator.clipboard.writeText(response.answer)
      setAnswerCopied(true)
      setTimeout(() => setAnswerCopied(false), 2000)
    }
  }

  const {
    selectedModel: ragModel,
    loading: modelLoading,
    selectModel: selectRagModel
  } = useModelSelector('rag_answer')

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
  }, [])

  const loadSampleQuestions = async () => {
    try {
      const response = await axios.get('/api/rag/sample-questions')

      if (Array.isArray(response.data)) {
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

      const updatedHistory = [queryText, ...searchHistory.filter(q => q !== queryText)].slice(0, 10)
      setSearchHistory(updatedHistory)
      localStorage.setItem('rag_search_history', JSON.stringify(updatedHistory))
    } catch (error: any) {
      console.error('Error searching:', error)
      const detail = error?.response?.data?.detail
      toast.error('Search failed', {
        description: detail
          ? String(detail)
          : 'The server could not answer the question. Please try again.'
      })
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
    setRebuildingIndex(true)
    const rebuild = axios.post('/api/rag/rebuild').finally(() => {
      setRebuildingIndex(false)
      loadIndexStats()
    })

    toast.promise(rebuild, {
      loading: 'Rebuilding search index — this can take a few minutes…',
      success: (result) => {
        const docs = result.data?.stats?.total_documents
        return docs
          ? `Index rebuilt — ${docs} documents indexed.`
          : (result.data?.message || 'Index rebuilt successfully.')
      },
      error: (error: any) => {
        const detail = error?.response?.data?.detail
        return detail
          ? `Index rebuild failed: ${detail}`
          : 'Index rebuild failed — is the backend running?'
      }
    })
  }

  const navigateToSource = (source: Source) => {
    if (source.type === 'tweet') {
      const tweetUrl = source.url || source.metadata?.url || source.navigate_to
      if (tweetUrl) {
        window.open(tweetUrl, '_blank')
      } else if (source.metadata?.id || source.id) {
        const tweetId = source.metadata?.id || source.id
        const authorUsername = source.metadata?.author || source.author || 'x'
        const constructedUrl = `https://twitter.com/${authorUsername}/status/${tweetId}`
        window.open(constructedUrl, '_blank')
      }
    }
    else if (source.type === 'article') {
      const articleId = source.id?.replace('article_', '') ||
                       source.article_id ||
                       source.metadata?.id?.replace('article_', '') ||
                       (source.metadata?.url && source.metadata.url.split('/').pop()) ||
                       (source.url && source.url.split('/').pop()) || ''
      if (articleId) {
        setSelectedArticleId(articleId)
      } else if (source.metadata?.url || source.url) {
        window.open(source.metadata?.url || source.url, '_blank')
      }
    }
    else if (source.type === 'paper') {
      const paperId = source.id?.replace('paper_', '') ||
                     source.paper_id ||
                     source.metadata?.id?.replace('paper_', '') ||
                     source.metadata?.paper_id
      if (paperId) {
        setSelectedPaperId(paperId)
      } else if (source.metadata?.arxiv_id) {
        window.open(`https://arxiv.org/abs/${source.metadata.arxiv_id}`, '_blank')
      } else if (source.metadata?.doi) {
        window.open(`https://doi.org/${source.metadata.doi}`, '_blank')
      }
    }
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
              <p className="text-sm text-muted-foreground">
                Ask questions about tweets, articles, and research papers using natural language
              </p>
            </div>
            {indexStats && (
              <div className="flex items-center gap-4">
                <div className="text-sm text-muted-foreground space-y-1">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4" />
                    <span>{indexStats.indexed_documents || 0} documents</span>
                  </div>
                  <div className="flex items-center gap-2">
                    {rebuildingIndex ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin text-yellow-500" />
                        <span>Rebuilding…</span>
                      </>
                    ) : indexStats.is_ready ? (
                      <>
                        <CheckCircle className="w-4 h-4 text-green-500" />
                        <span>Ready</span>
                      </>
                    ) : (
                      <>
                        <AlertCircle className="w-4 h-4 text-red-500" />
                        <span>Not Ready</span>
                      </>
                    )}
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={rebuildIndex}
                  disabled={rebuildingIndex}
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

      <SearchControls
        question={question}
        setQuestion={setQuestion}
        loading={loading}
        includeTweets={includeTweets}
        setIncludeTweets={setIncludeTweets}
        includeArticles={includeArticles}
        setIncludeArticles={setIncludeArticles}
        includePapers={includePapers}
        setIncludePapers={setIncludePapers}
        indexStats={indexStats}
        searchHistory={searchHistory}
        showHistory={showHistory}
        setShowHistory={setShowHistory}
        sampleQuestions={sampleQuestions}
        activeCategory={activeCategory}
        setActiveCategory={setActiveCategory}
        ragModel={ragModel}
        modelLoading={modelLoading}
        selectRagModel={selectRagModel}
        hasResponse={!!response}
        onSearch={handleSearch}
        onKeyPress={handleKeyPress}
        getSearchingMessage={getSearchingMessage}
      />

      {/* Empty index: actionable hint instead of a fake answer */}
      {response?.needs_rebuild && (
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Search index is empty</AlertTitle>
          <AlertDescription className="flex items-center justify-between gap-4">
            <span>Nothing has been indexed yet, so there is nothing to search. Build the index once — after that it stays up to date.</span>
            <Button size="sm" onClick={rebuildIndex} disabled={rebuildingIndex}>
              {rebuildingIndex ? (
                <><Loader2 className="w-4 h-4 mr-2 animate-spin" />Rebuilding…</>
              ) : (
                <><RefreshCw className="w-4 h-4 mr-2" />Rebuild Index</>
              )}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Results */}
      {response && !response.needs_rebuild && (
        <div className="space-y-6">
          {/* Answer */}
          <Card className={response.is_trend_analysis ? "border-blue-300 dark:border-blue-700 bg-blue-50/50 dark:bg-blue-950/30" : ""}>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  {response.is_trend_analysis && (
                    <TrendingUp className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                  )}
                  {response.is_trend_analysis ? "Trend Analysis" : "Answer"}
                </CardTitle>
                <div className="flex items-center gap-2">
                  {response.is_trend_analysis && response.documents_analyzed && (
                    <Badge variant="outline" className="bg-blue-100 dark:bg-blue-900/50 text-blue-700 dark:text-blue-300 border-blue-300 dark:border-blue-700">
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
              <div className="prose prose-sm max-w-none dark:prose-invert">
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
                  <SearchResultCard
                    key={i}
                    source={source}
                    onNavigate={() => navigateToSource(source)}
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
            <div className="bg-white dark:bg-gray-900 rounded-lg p-8 flex items-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
              <span className="ml-2 text-gray-600 dark:text-gray-300">Loading Article Viewer...</span>
            </div>
          </div>
        }>
          <ArticleViewerModern
            articleId={selectedArticleId}
            onClose={() => setSelectedArticleId(null)}
          />
        </Suspense>
      )}

      {/* Paper Viewer Modal - same pattern as FacetedPapersDashboard */}
      {selectedPaperId && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-950 rounded-lg w-full max-w-7xl max-h-[90vh] overflow-auto shadow-2xl">
            <Suspense fallback={
              <div className="flex items-center justify-center h-96">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading Paper Viewer...</span>
              </div>
            }>
              <PaperViewerOptimized
                paperId={selectedPaperId}
                onClose={() => setSelectedPaperId(null)}
              />
            </Suspense>
          </div>
        </div>
      )}
    </div>
  )
}
