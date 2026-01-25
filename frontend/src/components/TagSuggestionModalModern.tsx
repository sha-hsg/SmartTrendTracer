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
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card } from "@/components/ui/card"
import {
  Sparkles,
  Tag,
  Loader2,
  Check,
  X,
  Zap,
  Brain
} from 'lucide-react'
import { cn } from "@/lib/utils"
import UnifiedModelSelector from './UnifiedModelSelector'
import { useModelSelector } from '@/hooks/useModelSelector'

interface ConceptSuggestion {
  concept_id?: string
  slug: string
  display_name: string
  usage_count?: number
  type: 'existing' | 'new'
  model?: string
  auto_generated?: boolean
}

interface ConceptSuggestionResponse {
  tweet_id: string
  existing_suggestions: ConceptSuggestion[]
  new_suggestions: ConceptSuggestion[]
  already_tagged: ConceptSuggestion[]
  model_used?: string
  total_suggestions: number
}

interface TagSuggestionModalProps {
  tweet: any
  isOpen: boolean
  onClose: () => void
  onTagsUpdated: () => void
}

export default function TagSuggestionModalModern({
  tweet,
  isOpen,
  onClose,
  onTagsUpdated
}: TagSuggestionModalProps) {
  const [loading, setLoading] = useState(false)
  const [suggestions, setSuggestions] = useState<ConceptSuggestionResponse | null>(null)
  const [selectedConcepts, setSelectedConcepts] = useState<Map<string, ConceptSuggestion>>(new Map())
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [abortController, setAbortController] = useState<AbortController | null>(null)
  const [showModelSelector, setShowModelSelector] = useState(true)

  // Use unified model selector hook for tag_suggestion task
  const {
    selectedModel,
    loading: modelLoading,
    selectModel
  } = useModelSelector('tag_suggestion')

  useEffect(() => {
    if (isOpen && tweet) {
      // Reset state when modal opens
      setShowModelSelector(true)
      setSuggestions(null)
      setSelectedConcepts(new Map())
      setError(null)
    }
  }, [isOpen, tweet])

  const fetchSuggestions = async (model?: string) => {
    setLoading(true)
    setError(null)
    setShowModelSelector(false)
    
    // Create new abort controller for this request
    const controller = new AbortController()
    setAbortController(controller)
    
    try {
      const response = await axios.post<ConceptSuggestionResponse>(
        `http://localhost:8000/api/concepts/suggestions/tweets/${tweet.id}/suggest`,
        {
          model: model || selectedModel
        },
        {
          timeout: 120000, // 120 second timeout for GPT-5 processing
          signal: controller.signal
        }
      )
      
      setSuggestions(response.data)
      setSelectedConcepts(new Map())
      setAbortController(null)
    } catch (error: any) {
      console.error('Error fetching suggestions:', error)
      if (axios.isCancel(error)) {
        setError('Concept generation was cancelled.')
      } else if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        setError('Concept generation timed out after 2 minutes. The model may be overloaded. Please try again.')
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
      setError('Concept generation was cancelled.')
    }
  }

  const toggleConcept = (concept: ConceptSuggestion) => {
    setSelectedConcepts(prev => {
      const newMap = new Map(prev)
      if (newMap.has(concept.slug)) {
        newMap.delete(concept.slug)
      } else {
        newMap.set(concept.slug, concept)
      }
      return newMap
    })
  }

  const applySelectedConcepts = async () => {
    if (selectedConcepts.size === 0) return

    setApplying(true)
    let successCount = 0
    let failCount = 0
    
    // Convert selected concepts to array format expected by API
    const conceptsToApply = Array.from(selectedConcepts.values()).map(c => ({
      display_name: c.display_name,
      slug: c.slug
    }))
    
    try {
      const response = await axios.post(
        `http://localhost:8000/api/concepts/suggestions/tweets/${tweet.id}/apply-concepts`,
        conceptsToApply
      )
      
      successCount = response.data.success_count || 0
      failCount = response.data.fail_count || 0
      
      if (failCount > 0 && successCount > 0) {
        setError(`Applied ${successCount} concepts. ${failCount} concepts were already present or failed.`)
      } else if (failCount > 0) {
        setError(`Failed to apply concepts. They may already be present.`)
      }
      
      // Always update and close if at least one concept was applied
      if (successCount > 0) {
        onTagsUpdated()
        setTimeout(() => onClose(), failCount > 0 ? 2000 : 0) // Delay close if there were errors
      }
    } catch (error: any) {
      console.error('Error applying concepts:', error)
      setError(error.response?.data?.detail || 'Failed to apply concepts')
    }
    
    setApplying(false)
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI Concept Suggestions
          </DialogTitle>
          <DialogDescription>
            Select concepts to apply to this tweet. Green concepts are existing concepts that match, 
            purple concepts are new AI-generated suggestions.
          </DialogDescription>
        </DialogHeader>

        <ScrollArea className="flex-1 h-[500px] overflow-y-auto">
            {showModelSelector && !loading ? (
              <div className="flex flex-col items-center justify-center py-12 space-y-6">
                <div className="text-center space-y-2">
                  <Brain className="h-12 w-12 mx-auto text-purple-600" />
                  <h3 className="text-lg font-semibold">Choose AI Model</h3>
                  <p className="text-sm text-muted-foreground max-w-md">
                    Select the AI model to analyze this tweet and generate concept tags
                  </p>
                </div>

                <div className="w-full max-w-md space-y-4">
                  {/* Unified Model Selector */}
                  <UnifiedModelSelector
                    taskType="tag_suggestion"
                    value={selectedModel || ''}
                    onValueChange={selectModel}
                    label="AI Model"
                    description="Choose the model that best fits your tagging needs. Your preference will be saved for future use."
                    disabled={modelLoading}
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
                      onClick={() => fetchSuggestions(selectedModel || undefined)}
                      className="w-full bg-purple-600 hover:bg-purple-700"
                      disabled={!selectedModel || modelLoading}
                    >
                      <Sparkles className="h-4 w-4 mr-2" />
                      Generate Tags
                    </Button>
                  </div>
                </div>
              </div>
            ) : loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="text-center space-y-3">
                  <Loader2 className="h-10 w-10 animate-spin mx-auto text-purple-600" />
                  <div className="space-y-1">
                    <p className="text-sm font-medium text-gray-900">
                      Analyzing tweet with {
                        selectedModel === 'gpt-5' ? 'GPT-5' :
                        selectedModel === 'gpt-4o' ? 'GPT-4o' :
                        selectedModel === 'gemini-2.5-pro' ? 'Gemini 2.5 Pro' :
                        selectedModel === 'claude-3.5-sonnet' ? 'Claude 3.5 Sonnet' :
                        selectedModel === 'gpt-4o-mini' ? 'GPT-4o Mini' :
                        selectedModel
                      }...
                    </p>
                    <p className="text-xs text-muted-foreground">
                      This analysis may take 10-30 seconds
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Please wait while we generate concept suggestions
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
              {/* Tweet Preview */}
              <Card className="mb-4 p-4 bg-gray-50">
                <p className="text-sm text-gray-700 line-clamp-3">{tweet.text}</p>
              </Card>

              {/* Already Tagged - Show prominently */}
              {suggestions.already_tagged && suggestions.already_tagged.length > 0 && (
                <div className="mb-6 p-3 bg-green-50 rounded-lg border border-green-200">
                  <h3 className="text-sm font-semibold text-green-800 mb-2 flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-600" />
                    Already Applied Concepts ({suggestions.already_tagged.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.already_tagged.map(concept => (
                      <div 
                        key={concept.slug}
                        className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium"
                        style={{
                          backgroundColor: '#DBEAFE',
                          borderColor: '#3B82F6',
                          color: '#1E40AF',
                          border: '1px solid'
                        }}
                      >
                        <Check className="h-3 w-3" />
                        {concept.display_name}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Existing Concept Suggestions */}
              {suggestions.existing_suggestions && suggestions.existing_suggestions.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Tag className="h-4 w-4 text-green-600" />
                    Existing Concepts (Similar to content)
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.existing_suggestions.map((suggestion) => (
                      <button
                        key={suggestion.slug}
                        onClick={() => toggleConcept(suggestion)}
                        className="group relative"
                      >
                        <div
                          className={cn(
                            "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium cursor-pointer transition-all",
                            selectedConcepts.has(suggestion.slug) && "ring-2 ring-blue-500 ring-offset-2"
                          )}
                          style={{
                            backgroundColor: '#DBEAFE',
                            borderColor: '#3B82F6',
                            color: '#1E40AF',
                            border: '1px solid'
                          }}
                        >
                          {suggestion.display_name}
                          {suggestion.usage_count && suggestion.usage_count > 0 && (
                            <Badge variant="secondary" className="ml-1 px-1 py-0 text-[10px]">
                              {suggestion.usage_count}
                            </Badge>
                          )}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* New AI Suggestions */}
              {suggestions.new_suggestions && suggestions.new_suggestions.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Brain className="h-4 w-4 text-purple-600" />
                    New AI Suggestions
                    <Badge variant="outline" className="text-xs">
                      {suggestions.model_used}
                    </Badge>
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.new_suggestions.map((suggestion) => (
                      <button
                        key={suggestion.slug}
                        onClick={() => toggleConcept(suggestion)}
                        className="group"
                      >
                        <div
                          className={cn(
                            "inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-medium cursor-pointer transition-all",
                            selectedConcepts.has(suggestion.slug) && "ring-2 ring-purple-500 ring-offset-2"
                          )}
                          style={{
                            backgroundColor: '#E9D5FF',
                            borderColor: '#9333EA',
                            color: '#6B21A8',
                            border: '1px solid'
                          }}
                        >
                          <Zap className="h-3 w-3" />
                          {suggestion.display_name}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* No Suggestions */}
              {(!suggestions.existing_suggestions || suggestions.existing_suggestions.length === 0) && 
               (!suggestions.new_suggestions || suggestions.new_suggestions.length === 0) && (
                <div className="py-8 text-center text-gray-500">
                  <Sparkles className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p>No suggestions available for this tweet</p>
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
            {selectedConcepts.size > 0 && (
              <Badge variant="secondary">
                {selectedConcepts.size} concept{selectedConcepts.size !== 1 ? 's' : ''} selected
              </Badge>
            )}
          </div>
          <div className="flex gap-2">
            <Button onClick={onClose} variant="outline">
              Cancel
            </Button>
            <Button
              onClick={applySelectedConcepts}
              disabled={selectedConcepts.size === 0 || applying}
            >
              {applying ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Applying...
                </>
              ) : (
                <>
                  <Check className="h-4 w-4 mr-2" />
                  Apply Concepts ({selectedConcepts.size})
                </>
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}