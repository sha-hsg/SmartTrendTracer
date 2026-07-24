import React from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Search,
  ChevronRight,
  MessageSquare,
  TrendingUp,
  Newspaper,
  Twitter,
  Clock,
  Loader2,
  GraduationCap,
} from 'lucide-react'
import UnifiedModelSelector from '../UnifiedModelSelector'
import { cn } from "@/lib/utils"

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

interface SearchControlsProps {
  question: string
  setQuestion: (q: string) => void
  loading: boolean
  includeTweets: boolean
  setIncludeTweets: (v: boolean) => void
  includeArticles: boolean
  setIncludeArticles: (v: boolean) => void
  includePapers: boolean
  setIncludePapers: (v: boolean) => void
  indexStats: IndexStats | null
  searchHistory: string[]
  showHistory: boolean
  setShowHistory: (v: boolean) => void
  sampleQuestions: SampleQuestions | null
  activeCategory: string
  setActiveCategory: (c: string) => void
  ragModel: string | null
  modelLoading: boolean
  selectRagModel: (m: string) => void
  hasResponse: boolean
  onSearch: (q?: string) => void
  onKeyPress: (e: React.KeyboardEvent) => void
  getSearchingMessage: () => string
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

export default function SearchControls({
  question,
  setQuestion,
  loading,
  includeTweets,
  setIncludeTweets,
  includeArticles,
  setIncludeArticles,
  includePapers,
  setIncludePapers,
  indexStats,
  searchHistory,
  showHistory,
  setShowHistory,
  sampleQuestions,
  activeCategory,
  setActiveCategory,
  ragModel,
  modelLoading,
  selectRagModel,
  hasResponse,
  onSearch,
  onKeyPress,
  getSearchingMessage,
}: SearchControlsProps) {
  return (
    <>
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
                  setTimeout(() => onSearch("What are the key trends on Twitter?"), 100)
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
                  setTimeout(() => onSearch("What are the key trends in research papers?"), 100)
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
                  setTimeout(() => onSearch("What are the hot topics in articles?"), 100)
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
                onKeyPress={onKeyPress}
              />
              <Button
                onClick={() => onSearch()}
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
                            onSearch(q)
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
      {!hasResponse && sampleQuestions && (
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
                      onSearch(q)
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
    </>
  )
}
