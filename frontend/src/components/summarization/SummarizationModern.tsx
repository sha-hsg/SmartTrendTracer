import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { toast } from 'sonner'
import { Card, CardContent } from "@/components/ui/card"
import { useModelSelector } from '@/hooks/useModelSelector'
import { Sparkles, Loader2 } from 'lucide-react'
import { Button } from "@/components/ui/button"
import SummarizationControls from './SummarizationControls'
import SummarizationResult from './SummarizationResult'

interface SummaryData {
  summary: string
  stats: {
    tweet_count: number
    article_count: number
    paper_count: number
    unique_authors: number
    total_likes: number
    total_retweets: number
    time_range: {
      start: string | null
      end: string | null
    }
    total_available?: {
      tweets: number
      articles: number
      papers: number
    }
  }
  filters: {
    period: string | null
    tags: string[] | null
    author: string | null
  }
  model_used?: string
  data_truncated?: boolean
  truncation_warning?: string | null
}

export default function SummarizationModern() {
  const [period, setPeriod] = useState<string>('today')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedAuthor, setSelectedAuthor] = useState<string>('all')
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [availableAuthors, setAvailableAuthors] = useState<{username: string, count: number}[]>([])
  const [articleAuthors, setArticleAuthors] = useState<{name: string, count: number}[]>([])
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null)
  const [loading, setLoading] = useState(false)
  const [tagInput, setTagInput] = useState('')
  const [showTagSuggestions, setShowTagSuggestions] = useState(false)

  // Source selection states
  const [includeTweets, setIncludeTweets] = useState(true)
  const [includeArticles, setIncludeArticles] = useState(true)
  const [includePapers, setIncludePapers] = useState(true)

  // Paper date type selection (for time period filtering)
  const [paperDateType, setPaperDateType] = useState<'created' | 'published'>('created')

  // Configurable limits with localStorage persistence
  const [maxTweets, setMaxTweets] = useState<number>(() => {
    const saved = localStorage.getItem('summarization_max_tweets')
    return saved ? parseInt(saved, 10) : 1000
  })
  const [maxArticles, setMaxArticles] = useState<number>(() => {
    const saved = localStorage.getItem('summarization_max_articles')
    return saved ? parseInt(saved, 10) : 50
  })
  const [maxPapers, setMaxPapers] = useState<number>(() => {
    const saved = localStorage.getItem('summarization_max_papers')
    return saved ? parseInt(saved, 10) : 50
  })
  const [showSettings, setShowSettings] = useState(false)
  const [copied, setCopied] = useState(false)

  // Detail level with localStorage persistence
  const [detailLevel, setDetailLevel] = useState<string>(() => {
    return localStorage.getItem('summarization_detail_level') || 'standard'
  })

  // Elapsed timer
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  // Copy summary to clipboard
  const copyToClipboard = async () => {
    if (summaryData?.summary) {
      await navigator.clipboard.writeText(summaryData.summary)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  // Save limits and detail level to localStorage when they change
  useEffect(() => {
    localStorage.setItem('summarization_max_tweets', maxTweets.toString())
    localStorage.setItem('summarization_max_articles', maxArticles.toString())
    localStorage.setItem('summarization_max_papers', maxPapers.toString())
  }, [maxTweets, maxArticles, maxPapers])

  useEffect(() => {
    localStorage.setItem('summarization_detail_level', detailLevel)
  }, [detailLevel])

  // Elapsed timer effect
  useEffect(() => {
    if (loading) {
      setElapsedSeconds(0)
      timerRef.current = setInterval(() => {
        setElapsedSeconds(prev => prev + 1)
      }, 1000)
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [loading])

  // Model selection with unified model selector (same as RAG Search)
  const {
    selectedModel,
    loading: modelLoading,
    selectModel
  } = useModelSelector('articleSummarization')

  useEffect(() => {
    fetchAvailableTags()
    fetchTwitterAuthors()
    fetchArticleAuthors()
  }, [])

  // Reset author selection when content source changes
  useEffect(() => {
    setSelectedAuthor('all')
  }, [includeTweets, includeArticles, includePapers])

  const fetchTwitterAuthors = async () => {
    try {
      // Fetch authors from tweets faceted-search endpoint
      const response = await axios.get(`/api/tweets/faceted-search?page=1&page_size=1`)
      const authors = response.data.facets?.authors || []
      // Sort by count (most tweets first)
      const sortedAuthors = authors
        .filter((a: any) => a.username)
        .sort((a: any, b: any) => (b.count || 0) - (a.count || 0))
      setAvailableAuthors(sortedAuthors)
    } catch (error) {
      console.error('Error fetching Twitter authors:', error)
      setAvailableAuthors([])
    }
  }

  const fetchArticleAuthors = async () => {
    try {
      // Fetch authors from articles faceted-search endpoint
      const response = await axios.get(`/api/articles/faceted-search?page=1&page_size=1`)
      const authors = response.data.facets?.authors || []
      // Sort by count (most articles first)
      const sortedAuthors = authors
        .filter((a: any) => a.name)
        .sort((a: any, b: any) => (b.count || 0) - (a.count || 0))
      setArticleAuthors(sortedAuthors)
    } catch (error) {
      console.error('Error fetching Article authors:', error)
      setArticleAuthors([])
    }
  }

  const fetchAvailableTags = async () => {
    try {
      const response = await axios.get(`/api/statistics/concepts/detailed`)
      // Extract concept names from the response
      const concepts = response.data.concepts || []
      // Sort by usage and take top 50 most used concepts for the dropdown
      const topConcepts = concepts
        .sort((a: any, b: any) => (b.usage?.total || 0) - (a.usage?.total || 0))
        .slice(0, 50)
        .map((concept: any) => concept.display_name)
      setAvailableTags(topConcepts)
    } catch (error) {
      console.error('Error fetching tags:', error)
      // Fallback to empty array if fetch fails
      setAvailableTags([])
    }
  }

  const generateSummary = async () => {
    // Validate at least one source is selected
    if (!includeTweets && !includeArticles && !includePapers) {
      return // Don't generate if no sources selected
    }

    setLoading(true)
    setSummaryData(null)

    try {
      const params = new URLSearchParams()
      params.append('period', period)  // Always send period, including 'all'
      if (selectedAuthor && selectedAuthor !== 'all') params.append('author', selectedAuthor)
      selectedTags.forEach(tag => params.append('tags', tag))

      // Add source filters
      params.append('include_tweets', includeTweets.toString())
      params.append('include_articles', includeArticles.toString())
      params.append('include_papers', includePapers.toString())

      // Add paper date type (only relevant when papers are included)
      if (includePapers) {
        params.append('paper_date_type', paperDateType)
      }

      // Add configurable limits
      params.append('max_tweets', maxTweets.toString())
      params.append('max_articles', maxArticles.toString())
      params.append('max_papers', maxPapers.toString())

      // Add detail level
      params.append('detail_level', detailLevel)

      // Add model selection
      if (selectedModel) params.append('model', selectedModel)

      abortRef.current = new AbortController()
      const response = await axios.post(
        `/api/analytics/trends/summarize?${params}`,
        undefined,
        { signal: abortRef.current.signal }
      )

      const data = response.data

      if (!data.summary || data.summary.trim() === '') {
        data.summary = 'No summary available. Please try different filters.'
      }

      setSummaryData(data)
    } catch (error: any) {
      if (axios.isCancel(error) || error?.code === 'ERR_CANCELED') {
        // User cancelled — quietly return to the ready state
        return
      }
      console.error('Error generating summary:', error)
      const detail = error?.response?.data?.detail
      toast.error('Summary generation failed', {
        description: detail || error?.message || 'Please try again.',
      })
    } finally {
      abortRef.current = null
      setLoading(false)
    }
  }

  const cancelGeneration = () => {
    abortRef.current?.abort()
  }

  const addTag = (tag: string) => {
    if (tag && !selectedTags.includes(tag)) {
      setSelectedTags([...selectedTags, tag])
      setTagInput('')
      setShowTagSuggestions(false)
    }
  }

  const removeTag = (tag: string) => {
    setSelectedTags(selectedTags.filter(t => t !== tag))
  }

  const getFilteredTagSuggestions = () => {
    if (!tagInput) return []
    return availableTags
      .filter(tag =>
        tag.toLowerCase().includes(tagInput.toLowerCase()) &&
        !selectedTags.includes(tag)
      )
      .slice(0, 10)
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">AI-Powered Summarization</h1>
        <p className="text-gray-600 dark:text-gray-400">Generate intelligent summaries across all content: tweets, articles, and research papers</p>
      </div>

      {/* Controls */}
      <SummarizationControls
        period={period}
        setPeriod={setPeriod}
        selectedTags={selectedTags}
        selectedAuthor={selectedAuthor}
        setSelectedAuthor={setSelectedAuthor}
        availableAuthors={availableAuthors}
        articleAuthors={articleAuthors}
        includeTweets={includeTweets}
        setIncludeTweets={setIncludeTweets}
        includeArticles={includeArticles}
        setIncludeArticles={setIncludeArticles}
        includePapers={includePapers}
        setIncludePapers={setIncludePapers}
        paperDateType={paperDateType}
        setPaperDateType={setPaperDateType}
        tagInput={tagInput}
        setTagInput={setTagInput}
        showTagSuggestions={showTagSuggestions}
        setShowTagSuggestions={setShowTagSuggestions}
        addTag={addTag}
        removeTag={removeTag}
        getFilteredTagSuggestions={getFilteredTagSuggestions}
        maxTweets={maxTweets}
        setMaxTweets={setMaxTweets}
        maxArticles={maxArticles}
        setMaxArticles={setMaxArticles}
        maxPapers={maxPapers}
        setMaxPapers={setMaxPapers}
        showSettings={showSettings}
        setShowSettings={setShowSettings}
        selectedModel={selectedModel}
        selectModel={selectModel}
        modelLoading={modelLoading}
        loading={loading}
        generateSummary={generateSummary}
        detailLevel={detailLevel}
        setDetailLevel={setDetailLevel}
        elapsedSeconds={elapsedSeconds}
      />

      {/* Results */}
      {summaryData && (
        <SummarizationResult
          summaryData={summaryData}
          copied={copied}
          copyToClipboard={copyToClipboard}
          onRegenerate={generateSummary}
          loading={loading}
        />
      )}

      {/* Generating State */}
      {loading && (
        <Card>
          <CardContent className="py-12 text-center">
            <Loader2 className="h-10 w-10 text-indigo-500 animate-spin mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-1">Generating summary&hellip; ({elapsedSeconds}s)</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm" role="status">
              {selectedModel ? `Using ${selectedModel.includes('/') ? selectedModel.split('/').slice(1).join('/') : selectedModel}` : 'Preparing model'}
              {' · '}{detailLevel} detail
            </p>
            <Button variant="outline" size="sm" onClick={cancelGeneration}>
              Cancel
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {!summaryData && !loading && (
        <Card>
          <CardContent className="py-12 text-center">
            <Sparkles className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Ready to Generate Summary</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-2">
              Select your filters and click "Generate Summary" to create an AI-powered summary across tweets, articles, and papers.
            </p>
            <p className="text-gray-500 dark:text-gray-500 text-sm">
              You can filter by time period, specific authors, or tag combinations.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
