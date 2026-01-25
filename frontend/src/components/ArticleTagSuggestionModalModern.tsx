import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { TagBadge } from "@/components/ui/tag-badge"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card } from "@/components/ui/card"
import {
  Sparkles,
  Tag,
  Loader2,
  Check,
  X,
  Brain,
  Lightbulb,
  Target,
  Zap,
  FileText
} from 'lucide-react'
import { cn } from "@/lib/utils"
import UnifiedModelSelector from './UnifiedModelSelector'
import { getDefaultModel } from '@/config/models'

interface TagSuggestion {
  tag: string
  score?: number
  type: 'existing' | 'new'
  model?: string
}

interface Article {
  id: string | number
  title: string
  subtitle?: string | null
  preview?: string
}

interface ArticleTagSuggestionModalProps {
  article: Article
  isOpen: boolean
  onClose: () => void
  onTagsUpdated: () => void
}

export default function ArticleTagSuggestionModalModern({
  article,
  isOpen,
  onClose,
  onTagsUpdated
}: ArticleTagSuggestionModalProps) {
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<{
    existing: TagSuggestion[]
    new: TagSuggestion[]
    already_tagged: string[]
    model_used?: string
  } | null>(null)
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set())
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  // Use centralized model config for default
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    return localStorage.getItem('preferredArticleTagModel') || getDefaultModel('articleSummarization')
  })
  const [showModelSelector, setShowModelSelector] = useState(true)

  // Save model preference to localStorage
  useEffect(() => {
    localStorage.setItem('preferredArticleTagModel', selectedModel)
  }, [selectedModel])

  useEffect(() => {
    if (isOpen && article) {
      // Reset state when modal opens
      setShowModelSelector(true)
      setSuggestions(null)
      setSelectedTags(new Set())
      setError(null)
    }
  }, [isOpen, article])

  const fetchSuggestions = async (model?: string) => {
    setLoading(true)
    setError(null)
    setShowModelSelector(false)
    
    // Create new abort controller for this request
    const controller = new AbortController()
    setAbortController(controller)
    
    try {
      const response = await axios.post(
        `http://localhost:8000/api/articles/${article.id}/tags/suggest`,
        {
          model: model || selectedModel
        },
        {
          timeout: 120000, // 120 second timeout for GPT-5 processing
          signal: controller.signal
        }
      )

      // Filter out already tagged items from suggestions
      const alreadyTagged = response.data.already_tagged || []
      const alreadyTaggedLower = alreadyTagged.map((t: string) => t.toLowerCase())

      // Map backend response format (display_name) to frontend format (tag)
      const filteredExisting = (response.data.existing_suggestions || [])
        .map((s: any) => ({ tag: s.display_name, score: s.score, type: 'existing' as const }))
        .filter((s: TagSuggestion) => !alreadyTaggedLower.includes(s.tag.toLowerCase()))

      const filteredNew = (response.data.new_suggestions || [])
        .map((s: any) => ({ tag: s.display_name, type: 'new' as const }))
        .filter((s: TagSuggestion) => !alreadyTaggedLower.includes(s.tag.toLowerCase()))
      
      setSuggestions({
        existing: filteredExisting,
        new: filteredNew,
        already_tagged: alreadyTagged,
        model_used: response.data.model_used
      })
      setSelectedTags(new Set())
      setAbortController(null)
    } catch (error: any) {
      console.error('Error fetching suggestions:', error)
      if (axios.isCancel(error)) {
        setError('Tag generation was cancelled.')
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        setError('Tag generation timed out after 2 minutes. The model may be overloaded. Please try again.')
      } else {
        setError(error.response?.data?.detail || 'Failed to fetch suggestions')
      }
    } finally {
      setLoading(false)
      setAbortController(null)
    }
  }

  const cancelFetch = () => {
    if (abortController) {
      abortController.abort()
      setAbortController(null)
      setLoading(false)
      setError('Tag generation was cancelled.')
    }
  }

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => {
      const newSet = new Set(prev)
      if (newSet.has(tag)) {
        newSet.delete(tag)
      } else {
        newSet.add(tag)
      }
      return newSet
    })
  }

  const applySelectedTags = async () => {
    if (selectedTags.size === 0) return

    setApplying(true)
    let successCount = 0
    let failCount = 0
    
    for (const tag of selectedTags) {
      try {
        // Use the concepts endpoint with text query parameter
        await axios.post(
          `http://localhost:8000/api/articles/${article.id}/concepts?text=${encodeURIComponent(tag)}`
        )
        successCount++
      } catch (error: any) {
        console.error(`Error applying tag "${tag}":`, error.response?.data?.detail || error.message)
        failCount++
        // Continue with next tag instead of stopping
      }
    }
    
    // Show appropriate message based on results
    if (failCount > 0 && successCount > 0) {
      setError(`Applied ${successCount} tags. ${failCount} tags were already present or failed.`)
    } else if (failCount > 0) {
      setError(`Failed to apply tags. They may already be present.`)
    }
    
    // Always update and close if at least one tag was applied
    if (successCount > 0) {
      onTagsUpdated()
      setTimeout(() => onClose(), failCount > 0 ? 2000 : 0) // Delay close if there were errors
    }
    
    setApplying(false)
  }

  const getScoreIcon = (score?: number) => {
    if (!score) return null
    if (score >= 0.8) return <Target className="h-3 w-3" />
    if (score >= 0.6) return <Lightbulb className="h-3 w-3" />
    return null
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI Tag Suggestions for Article
          </DialogTitle>
          <DialogDescription>
            Select tags to apply to this article. Green tags are existing tags that match, 
            purple tags are new AI-generated suggestions.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 h-[500px] overflow-y-auto">
            {showModelSelector && !loading ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-6">
                <div className="text-center space-y-2">
                  <Brain className="h-12 w-12 mx-auto text-purple-600" />
                  <h3 className="text-lg font-semibold">Choose AI Model</h3>
                  <p className="text-sm text-muted-foreground max-w-md">
                    Select the AI model to analyze this article and generate tags
                  </p>
                </div>
                
                <div className="w-full max-w-md space-y-4">
                  {/* Uses UnifiedModelSelector with centralized model config */}
                  <UnifiedModelSelector
                    taskType="tag_suggestion"
                    value={selectedModel}
                    onValueChange={setSelectedModel}
                    label="AI Model"
                    description="Select the AI model to analyze this article"
                  />

                  <div className="grid grid-cols-2 gap-3">
                    <Button
                      variant="outline"
                      onClick={onClose}
                      className="w-full"
                    >
                      Cancel
                    </Button>
                    <Button
                      onClick={() => fetchSuggestions(selectedModel)}
                      className="w-full bg-purple-600 hover:bg-purple-700"
                    >
                      <Sparkles className="h-4 w-4 mr-2" />
                      Generate Tags
                    </Button>
                  </div>

                  <div className="text-xs text-center text-muted-foreground space-y-1">
                    <p>• Advanced models: More comprehensive analysis (30-90s)</p>
                    <p>• Gemini 2.5 Pro: Large context window, fast processing</p>
                    <p>• Claude 3.5: Excellent for article analysis</p>
                  </div>
                </div>
              </div>
            ) : loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center space-y-3">
                  <Loader2 className="h-10 w-10 animate-spin mx-auto text-purple-600" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-gray-900">
                      Analyzing article with {
                        selectedModel === 'gpt-5' ? 'GPT-5' :
                        selectedModel === 'gpt-4o' ? 'GPT-4o' :
                        selectedModel === 'gemini-2.5-pro' ? 'Gemini 2.5 Pro' :
                        selectedModel === 'claude-3.5-sonnet' ? 'Claude 3.5 Sonnet' :
                        selectedModel === 'gpt-4o-mini' ? 'GPT-4o Mini' :
                        selectedModel
                      }...
                    </p>
                    <p className="text-xs text-muted-foreground">
                      This analysis may take 30-90 seconds for long articles
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Please wait while we generate tag suggestions
                    </p>
                  </div>
                  <div className="w-64 mx-auto bg-gray-200 rounded-full h-1.5">
                    <div className="bg-purple-600 h-1.5 rounded-full animate-pulse" style={{width: '60%'}}></div>
                  </div>
                  <Button
                    onClick={cancelFetch}
                    variant="outline"
                    size="sm"
                    className="mt-4"
                  >
                    <X className="h-4 w-4 mr-2" />
                    Cancel
                  </Button>
                </div>
              </div>
            ) : error ? (
            <div className="py-8 text-center">
              <X className="h-12 w-12 text-red-400 mx-auto mb-3" />
              <p className="text-red-600">{error}</p>
              <Button onClick={() => fetchSuggestions()} variant="outline" className="mt-4">
                Try Again
              </Button>
            </div>
          ) : suggestions ? (
            <div className="space-y-4 p-4">
              {/* Article Preview */}
              <Card className="mb-4 p-4 bg-gray-50">
                <div className="flex items-start gap-2 mb-2">
                  <FileText className="h-4 w-4 text-gray-400 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-sm">{article.title}</h3>
                    {article.subtitle && (
                      <p className="text-xs text-gray-500 mt-1">{article.subtitle}</p>
                    )}
                  </div>
                </div>
              </Card>

              {/* Already Tagged - Show prominently at the top */}
              {suggestions.already_tagged.length > 0 && (
                <div className="mb-6 p-3 bg-green-50 rounded-lg border border-green-200">
                  <h3 className="text-sm font-semibold text-green-800 mb-2 flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Already Applied Tags ({suggestions.already_tagged.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.already_tagged.map(tag => (
                      <TagBadge key={tag} variant="default" className="bg-green-100 text-green-800 border-green-300">
                        <Check className="h-3 w-3" />
                        {tag}
                      </TagBadge>
                    ))}
                  </div>
                </div>
              )}

              {/* Existing Tag Suggestions */}
              {suggestions.existing.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Tag className="h-4 w-4 text-green-600" />
                    Existing Tags (Similar to content)
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.existing.map((suggestion, idx) => (
                      <button
                        key={`existing-${idx}`}
                        onClick={() => toggleTag(suggestion.tag)}
                        className="group relative"
                      >
                        <TagBadge
                          variant="similar"
                          className={cn(
                            "cursor-pointer transition-all",
                            selectedTags.has(suggestion.tag) && "ring-2 ring-green-500 ring-offset-2"
                          )}
                        >
                          <div className="flex items-center gap-1">
                            {getScoreIcon(suggestion.score)}
                            <span>{suggestion.tag}</span>
                          </div>
                        </TagBadge>
                        {suggestion.score && (
                          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-black text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
                            {(suggestion.score * 100).toFixed(0)}% match
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* New AI Suggestions */}
              {suggestions.new.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Brain className="h-4 w-4 text-purple-600" />
                    New AI Suggestions
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.new.map((suggestion, idx) => (
                      <button
                        key={`new-${idx}`}
                        onClick={() => toggleTag(suggestion.tag)}
                        className="group"
                      >
                        <TagBadge
                          variant="ai"
                          className={cn(
                            "cursor-pointer transition-all",
                            selectedTags.has(suggestion.tag) && "ring-2 ring-purple-500 ring-offset-2"
                          )}
                          icon={<Zap className="h-3 w-3" />}
                        >
                          {suggestion.tag}
                        </TagBadge>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* No Suggestions */}
              {suggestions.existing.length === 0 && 
               suggestions.new.length === 0 && (
                <div className="py-8 text-center text-gray-500">
                  <Sparkles className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p>No suggestions available for this article</p>
                </div>
              )}

              {/* Model Info */}
              {suggestions.model_used && (
                <div className="mt-4 pt-4 border-t">
                  <p className="text-xs text-muted-foreground flex items-center gap-2">
                    <Brain className="h-3 w-3" />
                    Powered by {suggestions.model_used}
                  </p>
                </div>
              )}
            </div>
          ) : null}
        </ScrollArea>

        <DialogFooter className="mt-4 p-4 border-t flex items-center justify-between">
          <div className="flex items-center gap-2">
            {selectedTags.size > 0 && (
              <Badge variant="secondary">
                {selectedTags.size} tag{selectedTags.size !== 1 ? 's' : ''} selected
              </Badge>
            )}
          </div>
          <div className="flex gap-2">
            <Button onClick={onClose} variant="outline">
              Cancel
            </Button>
            <Button
              onClick={applySelectedTags}
              disabled={selectedTags.size === 0 || applying}
            >
              {applying ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Applying...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Apply Tags ({selectedTags.size})
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}