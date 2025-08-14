import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
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
  TrendingUp,
  BarChart3,
  AlertCircle,
  CheckCircle,
  Wand2
} from 'lucide-react'

interface SummaryData {
  summary: string
  stats: {
    tweet_count: number
    unique_authors: number
    total_likes: number
    total_retweets: number
    time_range: {
      start: string | null
      end: string | null
    }
  }
  filters: {
    period: string | null
    tags: string[] | null
    author: string | null
  }
  model_used?: string
}

export default function SummarizationModern() {
  const [period, setPeriod] = useState<string>('today')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedAuthor, setSelectedAuthor] = useState<string>('all')
  const [availableTags, setAvailableTags] = useState<string[]>([])
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null)
  const [loading, setLoading] = useState(false)
  const [tagInput, setTagInput] = useState('')
  const [showTagSuggestions, setShowTagSuggestions] = useState(false)

  useEffect(() => {
    fetchAvailableTags()
  }, [])

  const fetchAvailableTags = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tags')
      setAvailableTags(response.data.map((tag: any) => tag.tag))
    } catch (error) {
      console.error('Error fetching tags:', error)
    }
  }

  const generateSummary = async () => {
    setLoading(true)
    setSummaryData(null)
    
    try {
      const params = new URLSearchParams()
      if (period !== 'all') params.append('period', period)
      if (selectedAuthor && selectedAuthor !== 'all') params.append('author', selectedAuthor)
      selectedTags.forEach(tag => params.append('tags', tag))
      
      const response = await axios.post(
        `http://localhost:8000/api/analytics/summarize?${params}`
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
        <p className="text-gray-600">Generate intelligent summaries of tweet collections</p>
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
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
                  <SelectItem value="all">All Authors</SelectItem>
                  <SelectItem value="OpenAI">@OpenAI</SelectItem>
                  <SelectItem value="emollick">@emollick</SelectItem>
                  <SelectItem value="stanfordnlp">@stanfordnlp</SelectItem>
                  <SelectItem value="AnthropicAI">@AnthropicAI</SelectItem>
                  <SelectItem value="GoogleDeepMind">@GoogleDeepMind</SelectItem>
                  <SelectItem value="huggingface">@huggingface</SelectItem>
                  <SelectItem value="sama">@sama</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Tag Filter */}
            <div className="space-y-2">
              <Label>Filter by Tags</Label>
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
                  placeholder="Type tag and press Enter"
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

          {/* Generate Button */}
          <div className="mt-6">
            <Button
              onClick={generateSummary}
              disabled={loading}
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
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-xs text-gray-500">Tweets</p>
                    <p className="text-2xl font-bold">{summaryData.stats.tweet_count}</p>
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
              <div className="prose prose-sm max-w-none">
                {summaryData.summary.split('\n').map((paragraph, index) => (
                  paragraph.trim() && (
                    <p key={index} className="mb-3 text-gray-700 leading-relaxed">
                      {paragraph}
                    </p>
                  )
                ))}
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