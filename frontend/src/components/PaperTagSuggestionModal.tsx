import React, { useState, useEffect } from 'react'
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
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { 
  Sparkles, 
  Tag, 
  Loader2, 
  Check, 
  X,
  TrendingUp,
  Lightbulb,
  Brain,
  Search,
  Hash
} from 'lucide-react'
import { cn } from "@/lib/utils"
import ModelSelector from './ModelSelector'

interface TagSuggestion {
  tag?: string  // For backward compatibility
  display_name?: string  // For concepts
  slug?: string
  concept_id?: string
  score?: number
  usage_count?: number
  type: 'existing' | 'new'
  model?: string
  is_new?: boolean
}

interface TagSuggestionResponse {
  paper_id: number
  existing_suggestions: TagSuggestion[]
  new_suggestions: TagSuggestion[]
  already_tagged: string[]
  model_used: string
  total_suggestions: number
}

interface PaperTagSuggestionModalProps {
  paper: any
  isOpen: boolean
  onClose: () => void
  onTagsUpdated: () => void
}

export default function PaperTagSuggestionModal({
  paper,
  isOpen,
  onClose,
  onTagsUpdated
}: PaperTagSuggestionModalProps) {
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<TagSuggestionResponse | null>(null)
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set())
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [existingTags, setExistingTags] = useState<string[]>([])
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')
  const [showModelSelector, setShowModelSelector] = useState(true)

  useEffect(() => {
    if (isOpen && paper) {
      loadExistingTags()
      // Reset state when modal opens
      setShowModelSelector(true)
      setSuggestions(null)
      setSelectedTags(new Set())
      setError(null)
    }
  }, [isOpen, paper])

  const loadExistingTags = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/papers/${paper.id}`)
      setExistingTags(response.data.tags || [])
    } catch (error) {
      console.error('Error loading existing tags:', error)
    }
  }

  const fetchSuggestions = async (model?: string) => {
    setLoading(true)
    setError(null)
    setShowModelSelector(false)
    
    // Create new abort controller for this request
    const controller = new AbortController()
    setAbortController(controller)
    
    try {
      const response = await axios.post<TagSuggestionResponse>(
        `http://localhost:8000/api/papers/${paper.id}/tags/suggest`,
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
      
      const filteredExisting = (response.data.existing_suggestions || []).filter(
        (s: any) => {
          const tagName = s.tag || s.display_name
          return tagName && !alreadyTaggedLower.includes(tagName.toLowerCase())
        }
      )
      
      const filteredNew = (response.data.new_suggestions || []).filter(
        (s: any) => {
          const tagName = s.tag || s.display_name
          return tagName && !alreadyTaggedLower.includes(tagName.toLowerCase())
        }
      )
      
      setSuggestions({
        ...response.data,
        existing_suggestions: filteredExisting,
        new_suggestions: filteredNew
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
        setError('Failed to generate tag suggestions. Please try again.')
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

  const toggleTag = (suggestion: TagSuggestion) => {
    // Use display_name for concepts, fall back to tag for backward compatibility
    const identifier = suggestion.display_name || suggestion.tag || ''
    const newSelected = new Set(selectedTags)
    if (newSelected.has(identifier)) {
      newSelected.delete(identifier)
    } else {
      newSelected.add(identifier)
    }
    setSelectedTags(newSelected)
  }

  // Keyboard navigation handler
  const handleKeyPress = (event: React.KeyboardEvent, suggestion: TagSuggestion) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      toggleTag(suggestion)
    }
  }

  const applyTags = async () => {
    if (selectedTags.size === 0) return
    
    setApplying(true)
    setError(null)
    
    const tagsToApply = [...selectedTags]
    
    try {
      // Apply each tag
      for (const tag of tagsToApply) {
        await axios.post(`http://localhost:8000/api/papers/${paper.id}/tags`, {
          tag: tag
        })
      }
      
      // Get updated tags from the server
      const response = await axios.get(`http://localhost:8000/api/papers/${paper.id}`)
      const updatedTags = response.data.tags || []
      
      onTagsUpdated(updatedTags)
      onClose()
    } catch (error: any) {
      console.error('Error applying tags:', error)
      setError('Failed to apply tags. Please try again.')
    } finally {
      setApplying(false)
    }
  }

  const removeTag = async (tag: string) => {
    try {
      await axios.delete(`http://localhost:8000/api/papers/${paper.id}/tags/${encodeURIComponent(tag)}`)
      const newTags = existingTags.filter(t => t !== tag)
      setExistingTags(newTags)
      onTagsUpdated(newTags)
    } catch (error) {
      console.error('Error removing tag:', error)
    }
  }

  if (!paper) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            Tag Suggestions for Paper
          </DialogTitle>
          <DialogDescription className="line-clamp-2">
            {paper.title}
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 h-[500px] overflow-y-auto" role="main" aria-label="Tag suggestions content">
            {showModelSelector && !loading ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-6">
                <div className="text-center space-y-2">
                  <Brain className="h-12 w-12 mx-auto text-purple-600" />
                  <h3 className="text-lg font-semibold">Choose AI Model</h3>
                  <p className="text-sm text-muted-foreground max-w-md">
                    Select the AI model to analyze this paper and generate concept tags
                  </p>
                </div>
                
                <div className="w-full max-w-md space-y-4">
                  <ModelSelector
                    value={selectedModel}
                    onValueChange={setSelectedModel}
                    task="paperTagSuggestion"
                    label="AI Model"
                    description="Select the AI model to analyze this paper"
                    persist={true}
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
                    <p>• GPT-5: Most comprehensive analysis (30-60s)</p>
                    <p>• Gemini 2.5 Pro: Large context window, fast processing</p>
                    <p>• Claude 3.5: Excellent for academic papers</p>
                  </div>
                </div>
              </div>
            ) : loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center space-y-3">
                  <Loader2 className="h-10 w-10 animate-spin mx-auto text-purple-600" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-gray-900">
                      Analyzing paper with {
                        selectedModel === 'gpt-5' ? 'GPT-5' :
                        selectedModel === 'gpt-4o' ? 'GPT-4o' :
                        selectedModel === 'gemini-2.5-pro' ? 'Gemini 2.5 Pro' :
                        selectedModel === 'claude-3.5-sonnet' ? 'Claude 3.5 Sonnet' :
                        selectedModel === 'gpt-4o-mini' ? 'GPT-4o Mini' :
                        selectedModel
                      }...
                    </p>
                    <p className="text-xs text-muted-foreground">
                      This advanced analysis may take 30-60 seconds
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Please wait while we generate comprehensive tag suggestions
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
            ) : suggestions ? (
              <div className="space-y-4 p-4">
                {/* Existing Tags Section */}
                {suggestions.existing_suggestions.length > 0 && (
                  <div className="mb-6">
                    <div className="mb-4 p-3 bg-green-50 rounded-lg border border-green-200">
                      <h3 className="text-sm font-semibold mb-2 flex items-center gap-2 text-green-800">
                        <Search className="h-4 w-4" />
                        <span>Existing Tags</span>
                        <Badge variant="secondary" className="bg-green-100 text-green-800">
                          {suggestions.existing_suggestions.length}
                        </Badge>
                      </h3>
                      <p className="text-xs text-green-700 mb-3">
                        These tags already exist in your system and are similar to this paper's content
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-3" role="group" aria-label="Existing tag suggestions">
                      {suggestions.existing_suggestions.map((suggestion, index) => {
                        const displayName = suggestion.display_name || suggestion.tag || ''
                        const isSelected = selectedTags.has(displayName)
                        const usageCount = suggestion.usage_count || 0
                        const similarity = suggestion.score ? Math.round(suggestion.score * 100) : 0
                        
                        return (
                          <button
                            key={suggestion.concept_id || displayName}
                            onClick={() => toggleTag(suggestion)}
                            onKeyDown={(e) => handleKeyPress(e, suggestion)}
                            tabIndex={0}
                            className={cn(
                              "group relative inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2",
                              isSelected 
                                ? "bg-green-600 text-white shadow-md scale-105" 
                                : "bg-white border-2 border-green-300 text-green-800 hover:bg-green-50 hover:border-green-400 hover:scale-102"
                            )}
                            role="checkbox"
                            aria-checked={isSelected}
                            aria-label={`${displayName}${usageCount > 0 ? `. Used ${usageCount} times` : ''}${similarity > 0 ? `. ${similarity}% similarity match` : ''}. Press Enter or Space to ${isSelected ? 'remove' : 'add'}.`}
                          >
                            {isSelected && (
                              <Check className="h-3 w-3 shrink-0" aria-hidden="true" />
                            )}
                            <span className="truncate max-w-[150px]">{displayName}</span>
                            <div className="flex items-center gap-1 text-xs" aria-hidden="true">
                              {usageCount > 0 && (
                                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/20">
                                  <Hash className="h-2.5 w-2.5" />
                                  <span>{usageCount}</span>
                                </div>
                              )}
                              {similarity > 0 && (
                                <div className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/20">
                                  <TrendingUp className="h-2.5 w-2.5" />
                                  <span>{similarity}%</span>
                                </div>
                              )}
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {/* AI-Generated Tags Section */}
                {suggestions.new_suggestions.length > 0 && (
                  <div className="mb-6">
                    <div className="mb-4 p-3 bg-purple-50 rounded-lg border border-purple-200">
                      <h3 className="text-sm font-semibold mb-2 flex items-center gap-2 text-purple-800">
                        <Sparkles className="h-4 w-4" />
                        <span>AI-Generated Tags</span>
                        <Badge variant="secondary" className="bg-purple-100 text-purple-800">
                          {suggestions.new_suggestions.length}
                        </Badge>
                      </h3>
                      <p className="text-xs text-purple-700 mb-3">
                        New concept tags suggested by AI analysis of this paper's content
                      </p>
                    </div>
                    <div className="flex flex-wrap gap-3" role="group" aria-label="AI-generated tag suggestions">
                      {suggestions.new_suggestions.map((suggestion, index) => {
                        const displayName = suggestion.display_name || suggestion.tag || ''
                        const isSelected = selectedTags.has(displayName)
                        
                        return (
                          <button
                            key={suggestion.concept_id || displayName}
                            onClick={() => toggleTag(suggestion)}
                            onKeyDown={(e) => handleKeyPress(e, suggestion)}
                            tabIndex={0}
                            className={cn(
                              "group relative inline-flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2",
                              isSelected 
                                ? "bg-purple-600 text-white shadow-md scale-105" 
                                : "bg-white border-2 border-purple-300 text-purple-800 hover:bg-purple-50 hover:border-purple-400 hover:scale-102"
                            )}
                            role="checkbox"
                            aria-checked={isSelected}
                            aria-label={`${displayName}. AI-generated suggestion. Press Enter or Space to ${isSelected ? 'remove' : 'add'}.`}
                          >
                            {isSelected && (
                              <Check className="h-3 w-3 shrink-0" aria-hidden="true" />
                            )}
                            <span className="truncate max-w-[180px]">{displayName}</span>
                            <Lightbulb className="h-3 w-3 shrink-0 opacity-60" aria-hidden="true" />
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}

                {suggestions.existing_suggestions.length === 0 && 
                 suggestions.new_suggestions.length === 0 && (
                  <div className="text-center py-12 px-4">
                    <div className="max-w-md mx-auto">
                      <Search className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">No Suggestions Found</h3>
                      <p className="text-sm text-gray-600 mb-4">
                        The AI couldn't generate relevant tag suggestions for this paper. This might happen if:
                      </p>
                      <ul className="text-xs text-gray-500 text-left space-y-1 mb-4">
                        <li>• The paper content is very technical or niche</li>
                        <li>• The abstract or content is incomplete</li>
                        <li>• All relevant tags are already applied</li>
                      </ul>
                      <p className="text-xs text-gray-600">
                        You can still add custom tags manually or try again later.
                      </p>
                    </div>
                  </div>
                )}

                {/* Model Info */}
                {suggestions.model_used && (
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <div className="flex items-center gap-2">
                        <Brain className="h-3 w-3" />
                        <span>Analysis by {suggestions.model_used}</span>
                      </div>
                      <div className="flex items-center gap-4">
                        <span>{suggestions.existing_suggestions.length} existing</span>
                        <span>{suggestions.new_suggestions.length} new</span>
                        <span>{selectedTags.size} selected</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ) : error ? (
              <div className="text-center py-8">
                <X className="h-12 w-12 text-red-500 mx-auto mb-3" />
                <p className="text-sm text-red-600">{error}</p>
                <Button
                  onClick={fetchSuggestions}
                  variant="outline"
                  size="sm"
                  className="mt-4"
                >
                  Try Again
                </Button>
              </div>
            ) : null}
        </ScrollArea>

        <DialogFooter className="mt-4 p-4 border-t bg-gray-50">
          {/* Selection Summary */}
          {selectedTags.size > 0 && (
            <div className="w-full mb-3 p-3 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Tag className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-medium text-blue-900">
                    {selectedTags.size} tag{selectedTags.size !== 1 ? 's' : ''} selected
                  </span>
                </div>
                <button
                  onClick={() => setSelectedTags(new Set())}
                  className="text-xs text-blue-600 hover:text-blue-700 underline"
                  aria-label="Clear all selected tags"
                >
                  Clear all
                </button>
              </div>
              <div className="mt-2 flex flex-wrap gap-1">
                {Array.from(selectedTags).slice(0, 5).map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs bg-blue-100 text-blue-800">
                    {tag.length > 20 ? `${tag.slice(0, 20)}...` : tag}
                  </Badge>
                ))}
                {selectedTags.size > 5 && (
                  <Badge variant="secondary" className="text-xs bg-blue-100 text-blue-800">
                    +{selectedTags.size - 5} more
                  </Badge>
                )}
              </div>
            </div>
          )}
          
          <div className="flex justify-between w-full">
            <Button variant="outline" onClick={onClose} aria-label="Cancel and close dialog">
              Cancel
            </Button>
            <Button
              onClick={applyTags}
              disabled={selectedTags.size === 0 || applying}
              className={selectedTags.size > 0 ? 'bg-blue-600 hover:bg-blue-700' : ''}
              aria-label={applying ? 'Applying tags to paper' : `Apply ${selectedTags.size} selected tags to paper`}
            >
              {applying ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" aria-hidden="true" />
                  Applying...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" aria-hidden="true" />
                  Apply {selectedTags.size} Tag{selectedTags.size !== 1 ? 's' : ''}
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}