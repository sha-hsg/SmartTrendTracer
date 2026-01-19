import React, { useState, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import { useModelSelector } from '@/hooks/useModelSelector'
import UnifiedModelSelector from './UnifiedModelSelector'
import {
  Loader2,
  Sparkles,
  FileText,
  User,
  Heart,
  Repeat2,
  Calendar,
  Hash,
  X,
  Clock,
  AlertCircle,
  Wand2,
  Twitter,
  BookOpen,
  Check,
  Settings,
  ChevronDown,
  ChevronUp
} from 'lucide-react'

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
    return saved ? parseInt(saved, 10) : 100
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

  // Save limits to localStorage when they change
  useEffect(() => {
    localStorage.setItem('summarization_max_tweets', maxTweets.toString())
  }, [maxTweets])
  useEffect(() => {
    localStorage.setItem('summarization_max_articles', maxArticles.toString())
  }, [maxArticles])
  useEffect(() => {
    localStorage.setItem('summarization_max_papers', maxPapers.toString())
  }, [maxPapers])

  // Model selection with unified model selector (same as RAG Search)
  const {
    selectedModel,
    loading: modelLoading,
    selectModel
  } = useModelSelector('articleSummarization')

  useEffect(() => {
    fetchAvailableTags()
    fetchAvailableAuthors()
  }, [])

  const fetchAvailableAuthors = async () => {
    try {
      // Fetch authors from tweets faceted-search endpoint
      const response = await axios.get('http://localhost:8000/api/tweets/faceted-search?page=1&page_size=1')
      const authors = response.data.facets?.authors || []
      // Sort by count (most tweets first)
      const sortedAuthors = authors
        .filter((a: any) => a.username)
        .sort((a: any, b: any) => (b.count || 0) - (a.count || 0))
      setAvailableAuthors(sortedAuthors)
    } catch (error) {
      console.error('Error fetching authors:', error)
      setAvailableAuthors([])
    }
  }

  const fetchAvailableTags = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/statistics/concepts/detailed')
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

      // Add model selection
      if (selectedModel) params.append('model', selectedModel)

      const response = await axios.post(
        `http://localhost:8000/api/analytics/trends/summarize?${params}`
      )
      
      const data = response.data
      
      if (!data.summary || data.summary.trim() === '') {
        data.summary = 'No summary available. Please try different filters.'
      }
      
      setSummaryData(data)
    } catch (error) {
      console.error('Error generating summary:', error)
      setSummaryData({
        summary: `Error generating summary: ${error}`,
        stats: {
          tweet_count: 0,
          article_count: 0,
          paper_count: 0,
          unique_authors: 0,
          total_likes: 0,
          total_retweets: 0,
          time_range: { start: null, end: null }
        },
        filters: { period, tags: selectedTags, author: selectedAuthor }
      })
    } finally {
      setLoading(false)
    }
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

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'N/A'
    return new Date(dateStr).toLocaleString()
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

  const getModelIcon = (model?: string) => {
    if (!model) return null
    if (model.includes('gpt')) return '🤖'
    if (model.includes('claude')) return '🎭'
    if (model.includes('gemini')) return '💎'
    return '✨'
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">AI-Powered Summarization</h1>
        <p className="text-gray-600">Generate intelligent summaries across all content: tweets, articles, and research papers</p>
      </div>

      {/* Controls */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wand2 className="h-5 w-5" />
            Summary Configuration
          </CardTitle>
          <CardDescription>Select filters to focus your summary</CardDescription>
        </CardHeader>
        <CardContent>
          {/* Source Selection */}
          <div className="mb-6">
            <Label className="mb-3 block">Content Sources</Label>
            <div className="flex flex-wrap gap-4">
              <button
                onClick={() => setIncludeTweets(!includeTweets)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all",
                  includeTweets 
                    ? "bg-blue-50 border-blue-500 text-blue-700" 
                    : "bg-white border-gray-300 text-gray-600 hover:border-gray-400"
                )}
              >
                <div className={cn(
                  "w-5 h-5 rounded border-2 flex items-center justify-center",
                  includeTweets 
                    ? "bg-blue-500 border-blue-500" 
                    : "bg-white border-gray-300"
                )}>
                  {includeTweets && <Check className="h-3 w-3 text-white" />}
                </div>
                <Twitter className="h-4 w-4" />
                <span className="font-medium">Twitter/X</span>
              </button>
              
              <button
                onClick={() => setIncludeArticles(!includeArticles)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all",
                  includeArticles 
                    ? "bg-purple-50 border-purple-500 text-purple-700" 
                    : "bg-white border-gray-300 text-gray-600 hover:border-gray-400"
                )}
              >
                <div className={cn(
                  "w-5 h-5 rounded border-2 flex items-center justify-center",
                  includeArticles 
                    ? "bg-purple-500 border-purple-500" 
                    : "bg-white border-gray-300"
                )}>
                  {includeArticles && <Check className="h-3 w-3 text-white" />}
                </div>
                <FileText className="h-4 w-4" />
                <span className="font-medium">Articles</span>
              </button>
              
              <button
                onClick={() => setIncludePapers(!includePapers)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg border-2 transition-all",
                  includePapers 
                    ? "bg-orange-50 border-orange-500 text-orange-700" 
                    : "bg-white border-gray-300 text-gray-600 hover:border-gray-400"
                )}
              >
                <div className={cn(
                  "w-5 h-5 rounded border-2 flex items-center justify-center",
                  includePapers 
                    ? "bg-orange-500 border-orange-500" 
                    : "bg-white border-gray-300"
                )}>
                  {includePapers && <Check className="h-3 w-3 text-white" />}
                </div>
                <BookOpen className="h-4 w-4" />
                <span className="font-medium">Papers</span>
              </button>
            </div>
            {!includeTweets && !includeArticles && !includePapers && (
              <p className="text-sm text-amber-600 mt-2 flex items-center gap-1">
                <AlertCircle className="h-4 w-4" />
                Please select at least one content source
              </p>
            )}

            {/* Paper Date Type Selector - only show when Papers are included */}
            {includePapers && (
              <div className="mt-4 p-3 bg-orange-50 rounded-lg border border-orange-200">
                <Label className="text-sm text-orange-700 mb-2 block">Paper Date Filter</Label>
                <div className="flex gap-2">
                  <button
                    onClick={() => setPaperDateType('created')}
                    className={cn(
                      "px-3 py-1.5 rounded text-sm font-medium transition-all",
                      paperDateType === 'created'
                        ? "bg-orange-500 text-white"
                        : "bg-white text-orange-700 border border-orange-300 hover:border-orange-400"
                    )}
                  >
                    Import Date
                  </button>
                  <button
                    onClick={() => setPaperDateType('published')}
                    className={cn(
                      "px-3 py-1.5 rounded text-sm font-medium transition-all",
                      paperDateType === 'published'
                        ? "bg-orange-500 text-white"
                        : "bg-white text-orange-700 border border-orange-300 hover:border-orange-400"
                    )}
                  >
                    Publication Date
                  </button>
                </div>
                <p className="text-xs text-orange-600 mt-1">
                  {paperDateType === 'created'
                    ? "Filter by when paper was added to system"
                    : "Filter by paper's publication date (with year fallback)"}
                </p>
              </div>
            )}
          </div>

          <Separator className="mb-4" />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Time Period */}
            <div className="space-y-2">
              <Label>Time Period</Label>
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger>
                  <Clock className="h-4 w-4 mr-2" />
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="3days">Last 3 Days</SelectItem>
                  <SelectItem value="week">Last Week</SelectItem>
                  <SelectItem value="14days">Last 2 Weeks</SelectItem>
                  <SelectItem value="30days">Last 30 Days</SelectItem>
                  <SelectItem value="60days">Last 60 Days</SelectItem>
                  <SelectItem value="90days">Last 90 Days</SelectItem>
                  <SelectItem value="120days">Last 120 Days</SelectItem>
                  <SelectItem value="200days">Last 200 Days</SelectItem>
                  <SelectItem value="365days">Last Year</SelectItem>
                  <SelectItem value="all">All Time</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Author Filter */}
            <div className="space-y-2">
              <Label>Filter by Author</Label>
              <Select value={selectedAuthor} onValueChange={setSelectedAuthor}>
                <SelectTrigger>
                  <User className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="All Authors" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Authors ({availableAuthors.reduce((sum, a) => sum + (a.count || 0), 0)} tweets)</SelectItem>
                  {availableAuthors.map(author => (
                    <SelectItem key={author.username} value={author.username}>
                      @{author.username} ({author.count} tweets)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Model Selection - Unified Model Selector (same as RAG Search) */}
            <UnifiedModelSelector
              taskType="articleSummarization"
              value={selectedModel || ''}
              onValueChange={selectModel}
              label="AI Model"
              description="Choose the AI model for generating summaries"
              disabled={modelLoading || loading}
              compact={false}
            />

            {/* Concept Filter */}
            <div className="space-y-2">
              <Label>Filter by Concepts</Label>
              <div className="relative">
                <Input
                  type="text"
                  value={tagInput}
                  onChange={(e) => {
                    setTagInput(e.target.value)
                    setShowTagSuggestions(true)
                  }}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      addTag(tagInput)
                    }
                  }}
                  onFocus={() => setShowTagSuggestions(true)}
                  placeholder="Type concept and press Enter"
                  className="pr-8"
                />
                <Hash className="absolute right-2 top-2.5 h-4 w-4 text-gray-400" />
                
                {/* Tag Suggestions Dropdown */}
                {showTagSuggestions && getFilteredTagSuggestions().length > 0 && (
                  <Card className="absolute z-10 w-full mt-1 max-h-48 overflow-auto">
                    <CardContent className="p-0">
                      {getFilteredTagSuggestions().map(tag => (
                        <button
                          key={tag}
                          onClick={() => addTag(tag)}
                          className="w-full text-left px-3 py-2 hover:bg-gray-100 text-sm"
                        >
                          {tag}
                        </button>
                      ))}
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>

          {/* Selected Tags */}
          {selectedTags.length > 0 && (
            <div className="mt-4">
              <Label className="text-xs text-gray-500">Selected Tags</Label>
              <div className="flex flex-wrap gap-2 mt-2">
                {selectedTags.map(tag => (
                  <Badge key={tag} variant="secondary" className="pl-2 pr-1 py-1">
                    <Hash className="h-3 w-3 mr-1" />
                    {tag}
                    <button
                      onClick={() => removeTag(tag)}
                      className="ml-2 hover:bg-gray-300 rounded-full p-0.5"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Data Limits Settings (Collapsible) */}
          <div className="mt-4 border rounded-lg">
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="w-full flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <Settings className="h-4 w-4" />
                Data Limits
                <Badge variant="outline" className="text-xs font-normal">
                  {maxTweets} / {maxArticles} / {maxPapers}
                </Badge>
              </div>
              {showSettings ? (
                <ChevronUp className="h-4 w-4 text-gray-500" />
              ) : (
                <ChevronDown className="h-4 w-4 text-gray-500" />
              )}
            </button>

            {showSettings && (
              <div className="p-4 border-t bg-gray-50 space-y-4">
                <p className="text-xs text-gray-500">
                  Configure maximum items to include in the summary. Higher limits provide more context but increase processing time.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-2">
                    <Label className="text-xs">Max Tweets (10-500)</Label>
                    <Input
                      type="number"
                      min={10}
                      max={500}
                      value={maxTweets}
                      onChange={(e) => setMaxTweets(Math.max(10, Math.min(500, parseInt(e.target.value) || 100)))}
                      className="h-9"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs">Max Articles (5-200)</Label>
                    <Input
                      type="number"
                      min={5}
                      max={200}
                      value={maxArticles}
                      onChange={(e) => setMaxArticles(Math.max(5, Math.min(200, parseInt(e.target.value) || 50)))}
                      className="h-9"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-xs">Max Papers (5-200)</Label>
                    <Input
                      type="number"
                      min={5}
                      max={200}
                      value={maxPapers}
                      onChange={(e) => setMaxPapers(Math.max(5, Math.min(200, parseInt(e.target.value) || 50)))}
                      className="h-9"
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Generate Button */}
          <div className="mt-6">
            <Button
              onClick={generateSummary}
              disabled={loading || modelLoading || !selectedModel || (!includeTweets && !includeArticles && !includePapers)}
              className="w-full md:w-auto"
              size="lg"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Generating Summary...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Generate Summary
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {summaryData && (
        <div className="space-y-4">
          {/* Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Tweets</p>
                    <p className="text-2xl font-bold">{summaryData.stats.tweet_count}</p>
                  </div>
                  <Twitter className="h-8 w-8 text-blue-400 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Articles</p>
                    <p className="text-2xl font-bold">{summaryData.stats.article_count || 0}</p>
                  </div>
                  <FileText className="h-8 w-8 text-purple-500 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Papers</p>
                    <p className="text-2xl font-bold">{summaryData.stats.paper_count || 0}</p>
                  </div>
                  <BookOpen className="h-8 w-8 text-orange-500 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Authors</p>
                    <p className="text-2xl font-bold">{summaryData.stats.unique_authors}</p>
                  </div>
                  <User className="h-8 w-8 text-green-500 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Total Likes</p>
                    <p className="text-2xl font-bold">{summaryData.stats.total_likes.toLocaleString()}</p>
                  </div>
                  <Heart className="h-8 w-8 text-red-500 opacity-20" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Retweets</p>
                    <p className="text-2xl font-bold">{summaryData.stats.total_retweets.toLocaleString()}</p>
                  </div>
                  <Repeat2 className="h-8 w-8 text-purple-500 opacity-20" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Summary Content */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5" />
                  AI Summary
                </CardTitle>
                {summaryData.model_used && (
                  <Badge variant="outline" className="font-mono text-xs">
                    {getModelIcon(summaryData.model_used)} {summaryData.model_used}
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent>
              {/* Truncation Warning */}
              {summaryData.data_truncated && summaryData.truncation_warning && (
                <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-2">
                  <AlertCircle className="h-5 w-5 text-amber-500 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-amber-800">
                    <p className="font-medium">Data Limit Reached</p>
                    <p className="text-amber-700">{summaryData.truncation_warning}</p>
                  </div>
                </div>
              )}
              <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg prose-strong:text-gray-900 prose-ul:list-disc prose-ol:list-decimal prose-li:text-gray-700 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100">
                <ReactMarkdown
                  components={{
                    h1: ({children}) => <h1 className="text-2xl font-bold mt-4 mb-3 text-gray-900">{children}</h1>,
                    h2: ({children}) => <h2 className="text-xl font-semibold mt-3 mb-2 text-gray-800">{children}</h2>,
                    h3: ({children}) => <h3 className="text-lg font-semibold mt-2 mb-2 text-gray-800">{children}</h3>,
                    p: ({children}) => <p className="mb-3 text-gray-700 leading-relaxed">{children}</p>,
                    ul: ({children}) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                    ol: ({children}) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                    li: ({children}) => <li className="text-gray-700">{children}</li>,
                    strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                    em: ({children}) => <em className="italic text-gray-700">{children}</em>,
                    blockquote: ({children}) => (
                      <blockquote className="border-l-4 border-blue-500 pl-3 py-1 my-3 italic bg-blue-50 rounded-r">
                        {children}
                      </blockquote>
                    ),
                    code: ({inline, children}) => {
                      if (inline) {
                        return <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono text-gray-800">{children}</code>;
                      }
                      return (
                        <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto mb-3">
                          <code className="text-sm font-mono">{children}</code>
                        </pre>
                      );
                    },
                    hr: () => <hr className="my-4 border-gray-300" />,
                    a: ({href, children}) => (
                      <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
                        {children}
                      </a>
                    ),
                  }}
                >
                  {summaryData.summary}
                </ReactMarkdown>
              </div>

              <Separator className="my-4" />

              {/* Metadata */}
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  <span className="font-medium">Time Range:</span>
                  <span>
                    {formatDate(summaryData.stats.time_range.start)} to {formatDate(summaryData.stats.time_range.end)}
                  </span>
                </div>
                
                {summaryData.filters.tags && summaryData.filters.tags.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Hash className="h-4 w-4" />
                    <span className="font-medium">Filtered Tags:</span>
                    <div className="flex flex-wrap gap-1">
                      {summaryData.filters.tags.map(tag => (
                        <Badge key={tag} variant="secondary" className="text-xs">
                          {tag}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                {summaryData.filters.author && (
                  <div className="flex items-center gap-2">
                    <User className="h-4 w-4" />
                    <span className="font-medium">Author:</span>
                    <Badge variant="outline" className="text-xs">
                      @{summaryData.filters.author}
                    </Badge>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State */}
      {!summaryData && !loading && (
        <Card>
          <CardContent className="py-12 text-center">
            <Sparkles className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Ready to Generate Summary</h3>
            <p className="text-gray-600 mb-2">
              Select your filters and click "Generate Summary" to create an AI-powered summary of tweets.
            </p>
            <p className="text-gray-500 text-sm">
              You can filter by time period, specific authors, or tag combinations.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}