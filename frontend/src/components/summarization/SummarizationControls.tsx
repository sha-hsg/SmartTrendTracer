import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { cn } from "@/lib/utils"
import UnifiedModelSelector from '../UnifiedModelSelector'
import {
  Loader2,
  Sparkles,
  FileText,
  User,
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
  ChevronUp,
  AlignLeft,
} from 'lucide-react'

interface SummarizationControlsProps {
  period: string
  setPeriod: (v: string) => void
  selectedTags: string[]
  selectedAuthor: string
  setSelectedAuthor: (v: string) => void
  availableAuthors: {username: string, count: number}[]
  articleAuthors: {name: string, count: number}[]
  includeTweets: boolean
  setIncludeTweets: (v: boolean) => void
  includeArticles: boolean
  setIncludeArticles: (v: boolean) => void
  includePapers: boolean
  setIncludePapers: (v: boolean) => void
  paperDateType: 'created' | 'published'
  setPaperDateType: (v: 'created' | 'published') => void
  tagInput: string
  setTagInput: (v: string) => void
  showTagSuggestions: boolean
  setShowTagSuggestions: (v: boolean) => void
  addTag: (tag: string) => void
  removeTag: (tag: string) => void
  getFilteredTagSuggestions: () => string[]
  maxTweets: number
  setMaxTweets: (v: number) => void
  maxArticles: number
  setMaxArticles: (v: number) => void
  maxPapers: number
  setMaxPapers: (v: number) => void
  showSettings: boolean
  setShowSettings: (v: boolean) => void
  selectedModel: string | null
  selectModel: (v: string) => void
  modelLoading: boolean
  loading: boolean
  generateSummary: () => void
  detailLevel: string
  setDetailLevel: (v: string) => void
  elapsedSeconds: number
}

export default function SummarizationControls({
  period,
  setPeriod,
  selectedTags,
  selectedAuthor,
  setSelectedAuthor,
  availableAuthors,
  articleAuthors,
  includeTweets,
  setIncludeTweets,
  includeArticles,
  setIncludeArticles,
  includePapers,
  setIncludePapers,
  paperDateType,
  setPaperDateType,
  tagInput,
  setTagInput,
  showTagSuggestions,
  setShowTagSuggestions,
  addTag,
  removeTag,
  getFilteredTagSuggestions,
  maxTweets,
  setMaxTweets,
  maxArticles,
  setMaxArticles,
  maxPapers,
  setMaxPapers,
  showSettings,
  setShowSettings,
  selectedModel,
  selectModel,
  modelLoading,
  loading,
  generateSummary,
  detailLevel,
  setDetailLevel,
  elapsedSeconds,
}: SummarizationControlsProps) {
  const detailLevels = [
    { value: 'brief', label: 'Brief', desc: '2-3 paragraphs, ~300 words' },
    { value: 'standard', label: 'Standard', desc: '4 sections, ~500-800 words' },
    { value: 'detailed', label: 'Detailed', desc: '6 sections with examples, ~1000-1500 words' },
    { value: 'executive', label: 'Executive Report', desc: '8 sections, comprehensive, 2000+ words' },
  ]

  const getEstimatedTime = () => {
    const estimates: Record<string, string> = {
      brief: '~10-15s',
      standard: '~15-30s',
      detailed: '~30-60s',
      executive: '~45-90s',
    }
    return estimates[detailLevel] || '~15-30s'
  }
  return (
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
                  ? "bg-blue-50 dark:bg-blue-950 border-blue-500 text-blue-700 dark:text-blue-300"
                  : "bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-400"
              )}
            >
              <div className={cn(
                "w-5 h-5 rounded border-2 flex items-center justify-center",
                includeTweets
                  ? "bg-blue-500 border-blue-500"
                  : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600"
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
                  ? "bg-purple-50 dark:bg-purple-950 border-purple-500 text-purple-700 dark:text-purple-300"
                  : "bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-400"
              )}
            >
              <div className={cn(
                "w-5 h-5 rounded border-2 flex items-center justify-center",
                includeArticles
                  ? "bg-purple-500 border-purple-500"
                  : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600"
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
                  ? "bg-orange-50 dark:bg-orange-950 border-orange-500 text-orange-700 dark:text-orange-300"
                  : "bg-white dark:bg-gray-900 border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:border-gray-400"
              )}
            >
              <div className={cn(
                "w-5 h-5 rounded border-2 flex items-center justify-center",
                includePapers
                  ? "bg-orange-500 border-orange-500"
                  : "bg-white dark:bg-gray-800 border-gray-300 dark:border-gray-600"
              )}>
                {includePapers && <Check className="h-3 w-3 text-white" />}
              </div>
              <BookOpen className="h-4 w-4" />
              <span className="font-medium">Papers</span>
            </button>
          </div>
          {!includeTweets && !includeArticles && !includePapers && (
            <p className="text-sm text-amber-600 dark:text-amber-400 mt-2 flex items-center gap-1">
              <AlertCircle className="h-4 w-4" />
              Please select at least one content source
            </p>
          )}

          {/* Paper Date Type Selector - only show when Papers are included */}
          {includePapers && (
            <div className="mt-4 p-3 bg-orange-50 dark:bg-orange-950/50 rounded-lg border border-orange-200 dark:border-orange-800">
              <Label className="text-sm text-orange-700 dark:text-orange-300 mb-2 block">Paper Date Filter</Label>
              <div className="flex gap-2">
                <button
                  onClick={() => setPaperDateType('created')}
                  className={cn(
                    "px-3 py-1.5 rounded text-sm font-medium transition-all",
                    paperDateType === 'created'
                      ? "bg-orange-500 text-white"
                      : "bg-white dark:bg-gray-800 text-orange-700 dark:text-orange-300 border border-orange-300 dark:border-orange-700 hover:border-orange-400"
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
                      : "bg-white dark:bg-gray-800 text-orange-700 dark:text-orange-300 border border-orange-300 dark:border-orange-700 hover:border-orange-400"
                  )}
                >
                  Publication Date
                </button>
              </div>
              <p className="text-xs text-orange-600 dark:text-orange-400 mt-1">
                {paperDateType === 'created'
                  ? "Filter by when paper was added to system"
                  : "Filter by paper's publication date (with year fallback)"}
              </p>
            </div>
          )}
        </div>

        {/* Summary Detail Level */}
        <div className="mb-6">
          <Label className="mb-3 block flex items-center gap-2">
            <AlignLeft className="h-4 w-4" />
            Summary Detail
          </Label>
          <div className="flex flex-wrap gap-2">
            {detailLevels.map(level => (
              <button
                key={level.value}
                onClick={() => setDetailLevel(level.value)}
                className={cn(
                  "px-3 py-1.5 rounded text-sm font-medium transition-all",
                  detailLevel === level.value
                    ? "bg-indigo-500 text-white"
                    : "bg-white dark:bg-gray-800 text-indigo-700 dark:text-indigo-300 border border-indigo-300 dark:border-indigo-700 hover:border-indigo-400"
                )}
                title={level.desc}
              >
                {level.label}
              </button>
            ))}
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {detailLevels.find(l => l.value === detailLevel)?.desc}
          </p>
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

          {/* Author Filter - Only show when exactly one source type is selected (Tweets or Articles) */}
          {((includeTweets && !includeArticles && !includePapers) ||
            (!includeTweets && includeArticles && !includePapers)) && (
            <div className="space-y-2">
              <Label>Filter by Author {includeTweets ? '(Twitter)' : '(Substack)'}</Label>
              <Select value={selectedAuthor} onValueChange={setSelectedAuthor}>
                <SelectTrigger>
                  <User className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="All Authors" />
                </SelectTrigger>
                <SelectContent>
                  {includeTweets && !includeArticles && (
                    <>
                      <SelectItem value="all">All Authors ({availableAuthors.reduce((sum, a) => sum + (a.count || 0), 0)} tweets)</SelectItem>
                      {availableAuthors.map(author => (
                        <SelectItem key={author.username} value={author.username}>
                          @{author.username} ({author.count} tweets)
                        </SelectItem>
                      ))}
                    </>
                  )}
                  {includeArticles && !includeTweets && (
                    <>
                      <SelectItem value="all">All Authors ({articleAuthors.reduce((sum, a) => sum + (a.count || 0), 0)} articles)</SelectItem>
                      {articleAuthors.map(author => (
                        <SelectItem key={author.name} value={author.name}>
                          {author.name} ({author.count} articles)
                        </SelectItem>
                      ))}
                    </>
                  )}
                </SelectContent>
              </Select>
            </div>
          )}

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
              <Hash className="absolute right-2 top-2.5 h-4 w-4 text-gray-400 dark:text-gray-500" />

              {/* Tag Suggestions Dropdown */}
              {showTagSuggestions && getFilteredTagSuggestions().length > 0 && (
                <Card className="absolute z-10 w-full mt-1 max-h-48 overflow-auto">
                  <CardContent className="p-0">
                    {getFilteredTagSuggestions().map(tag => (
                      <button
                        key={tag}
                        onClick={() => addTag(tag)}
                        className="w-full text-left px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-800 text-sm"
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
            <Label className="text-xs text-gray-500 dark:text-gray-400">Selected Tags</Label>
            <div className="flex flex-wrap gap-2 mt-2">
              {selectedTags.map(tag => (
                <Badge key={tag} variant="secondary" className="pl-2 pr-1 py-1">
                  <Hash className="h-3 w-3 mr-1" />
                  {tag}
                  <button
                    onClick={() => removeTag(tag)}
                    className="ml-2 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-full p-0.5"
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
            className="w-full flex items-center justify-between p-3 hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg"
          >
            <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300">
              <Settings className="h-4 w-4" />
              Data Limits
              <Badge variant="outline" className="text-xs font-normal">
                {maxTweets} tweets · {maxArticles} articles · {maxPapers} papers
              </Badge>
            </div>
            {showSettings ? (
              <ChevronUp className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            ) : (
              <ChevronDown className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            )}
          </button>

          {showSettings && (
            <div className="p-4 border-t bg-gray-50 dark:bg-gray-900 space-y-4">
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Configure maximum items to include in the summary. Higher limits provide more context but increase processing time.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="space-y-2">
                  <Label className="text-xs">Max Tweets (10-1000)</Label>
                  <Input
                    type="number"
                    min={10}
                    max={1000}
                    value={maxTweets}
                    onChange={(e) => setMaxTweets(Math.max(10, Math.min(1000, parseInt(e.target.value) || 100)))}
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
                Generating... ({elapsedSeconds}s)
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-2" />
                Generate Summary
              </>
            )}
          </Button>
          {!loading && !includeTweets && !includeArticles && !includePapers && (
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400" role="status">
              Select at least one content source to generate a summary.
            </p>
          )}
          {!loading && (includeTweets || includeArticles || includePapers) && (modelLoading || !selectedModel) && (
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-400" role="status">
              Waiting for the AI model to load&hellip;
            </p>
          )}
          {loading && (
            <span className="ml-3 text-sm text-gray-500 dark:text-gray-400">
              Estimated: {getEstimatedTime()}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
