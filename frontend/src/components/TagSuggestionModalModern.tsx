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
import { TagBadge } from "@/components/ui/tag-badge"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Card } from "@/components/ui/card"
import { 
  Sparkles, 
  Hash, 
  Loader2, 
  Check, 
  X,
  TrendingUp,
  Lightbulb,
  Target,
  Zap,
  Brain
} from 'lucide-react'
import { cn } from "@/lib/utils"

interface TagSuggestion {
  tag: string
  score?: number
  usage_count?: number
  type: 'existing' | 'new'
  model?: string
}

interface TagSuggestionResponse {
  tweet_id: string
  existing_suggestions: TagSuggestion[]
  new_suggestions: TagSuggestion[]
  already_tagged: string[]
  model_used: string
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
  const [suggestions, setSuggestions] = useState<TagSuggestionResponse | null>(null)
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set())
  const [applying, setApplying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (isOpen && tweet) {
      fetchSuggestions()
    }
  }, [isOpen, tweet])

  const fetchSuggestions = async () => {
    setLoading(true)
    setError(null)
    try {
      const response = await axios.post<TagSuggestionResponse>(
        `http://localhost:8000/api/tags/suggest/${tweet.id}`
      )
      setSuggestions(response.data)
      setSelectedTags(new Set())
    } catch (error: any) {
      console.error('Error fetching suggestions:', error)
      setError(error.response?.data?.detail || 'Failed to fetch suggestions')
    } finally {
      setLoading(false)
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
    try {
      for (const tag of selectedTags) {
        await axios.post(`http://localhost:8000/api/tags/tweet/${tweet.id}`, {
          tag: tag,
          tag_type: 'manual'
        })
      }
      onTagsUpdated()
      onClose()
    } catch (error) {
      console.error('Error applying tags:', error)
      setError('Failed to apply some tags')
    } finally {
      setApplying(false)
    }
  }

  const getScoreColor = (score?: number) => {
    if (!score) return 'text-gray-500'
    if (score >= 0.8) return 'text-green-600'
    if (score >= 0.6) return 'text-blue-600'
    if (score >= 0.4) return 'text-yellow-600'
    return 'text-gray-500'
  }

  const getScoreIcon = (score?: number) => {
    if (!score) return null
    if (score >= 0.8) return <Target className="h-3 w-3" />
    if (score >= 0.6) return <TrendingUp className="h-3 w-3" />
    return <Lightbulb className="h-3 w-3" />
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-purple-500" />
            AI Tag Suggestions
          </DialogTitle>
          <DialogDescription>
            Select tags to apply to this tweet. Green tags are existing tags that match, 
            purple tags are new AI-generated suggestions.
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-hidden">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
              <span className="ml-3 text-gray-500">Analyzing tweet content...</span>
            </div>
          ) : error ? (
            <div className="py-8 text-center">
              <X className="h-12 w-12 text-red-400 mx-auto mb-3" />
              <p className="text-red-600">{error}</p>
              <Button onClick={fetchSuggestions} variant="outline" className="mt-4">
                Try Again
              </Button>
            </div>
          ) : suggestions ? (
            <ScrollArea className="h-[400px] pr-4">
              {/* Tweet Preview */}
              <Card className="mb-4 p-4 bg-gray-50">
                <p className="text-sm text-gray-700 line-clamp-3">{tweet.text}</p>
              </Card>

              {/* Already Tagged */}
              {suggestions.already_tagged.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-2 flex items-center gap-2">
                    <Check className="h-4 w-4 text-green-500" />
                    Already Tagged
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.already_tagged.map(tag => (
                      <TagBadge key={tag} variant="default" className="opacity-60">
                        <Hash className="h-3 w-3" />
                        {tag}
                      </TagBadge>
                    ))}
                  </div>
                </div>
              )}

              {/* Existing Tag Suggestions */}
              {suggestions.existing_suggestions.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Hash className="h-4 w-4 text-green-600" />
                    Existing Tags (Similar to content)
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.existing_suggestions.map((suggestion, idx) => (
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
                            {suggestion.usage_count && suggestion.usage_count > 0 && (
                              <Badge variant="secondary" className="ml-1 px-1 py-0 text-[10px]">
                                {suggestion.usage_count}
                              </Badge>
                            )}
                          </div>
                        </TagBadge>
                        {suggestion.score && (
                          <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-black text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                            {(suggestion.score * 100).toFixed(0)}% match
                          </div>
                        )}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* New AI Suggestions */}
              {suggestions.new_suggestions.length > 0 && (
                <div className="mb-6">
                  <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                    <Brain className="h-4 w-4 text-purple-600" />
                    New AI Suggestions
                    <Badge variant="outline" className="text-xs">
                      {suggestions.model_used}
                    </Badge>
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {suggestions.new_suggestions.map((suggestion, idx) => (
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
              {suggestions.existing_suggestions.length === 0 && 
               suggestions.new_suggestions.length === 0 && (
                <div className="py-8 text-center text-gray-500">
                  <Sparkles className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p>No suggestions available for this tweet</p>
                </div>
              )}
            </ScrollArea>
          ) : null}
        </div>

        <Separator className="my-4" />

        <DialogFooter className="flex items-center justify-between">
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