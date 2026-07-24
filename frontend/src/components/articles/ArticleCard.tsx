import { useState } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  User,
  Calendar,
  Loader2,
  Sparkles,
  MessageSquare,
  Plus,
  Trash2,
  ExternalLink,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
  RotateCw,
  Edit2,
  X,
  Check
} from 'lucide-react'
import { Input } from "@/components/ui/input"
import { Concept } from '@/types/concept'
import conceptService from '@/services/conceptService'
import TagSuggestionModalModern from '../TagSuggestionModalModern'


export interface Article {
  id: number | string
  title: string
  subtitle?: string | null
  author?: {
    id?: number
    name: string
    email?: string
    subdomain?: string | null
  }
  published_at: string | null
  url?: string
  preview: string
  content?: string
  content_length: number
  snippet_count: number
  summary?: string | null
  created_at?: string
  concepts: Concept[]
  concept_ids: string[]
  metrics?: any
  summarized?: boolean
}

interface ArticleCardProps {
  article: Article
  expandedSummaries: Set<string | number>
  regeneratingPreviews: Set<string | number>
  selectedConcepts: string[]
  onOpenArticle: (article: Article) => void
  onToggleSummary: (articleId: string | number) => void
  onToggleConcept: (conceptId: string) => void
  onDeleteArticle: (articleId: string, title: string) => void
  onRegeneratePreview: (articleId: string) => void
  onRefreshArticles: () => void
  onConceptAdded?: (articleId: string | number, concept: Concept) => void
  onConceptRemoved?: (articleId: string | number, conceptId: string) => void
}

const formatDate = (dateString: string | null) => {
  if (!dateString) return 'Unknown date'
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }).format(date)
}

export default function ArticleCard({
  article,
  expandedSummaries,
  regeneratingPreviews,
  selectedConcepts,
  onOpenArticle,
  onToggleSummary,
  onToggleConcept,
  onDeleteArticle,
  onRegeneratePreview,
  onRefreshArticles,
  onConceptAdded,
  onConceptRemoved,
}: ArticleCardProps) {
  const [selectedTextForConcept, setSelectedTextForConcept] = useState<{ articleId: string | number; text: string } | null>(null)
  const [isAddingConcept, setIsAddingConcept] = useState(false)
  const [newConceptText, setNewConceptText] = useState('')
  const [addingConceptLoading, setAddingConceptLoading] = useState(false)
  const [showSuggestModal, setShowSuggestModal] = useState(false)
  const [removingConceptId, setRemovingConceptId] = useState<string | null>(null)

  return (
    <Card className="hover:shadow-lg transition-all duration-200">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg mb-2 line-clamp-2">
              {article.title}
            </CardTitle>
            <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              {article.author && (
                <span className="flex items-center gap-1">
                  <User className="h-3 w-3" />
                  {article.author.name}
                </span>
              )}
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(article.published_at)}
              </span>
              {article.snippet_count > 0 && (
                <span className="flex items-center gap-1">
                  <MessageSquare className="h-3 w-3" />
                  {article.snippet_count} snippets
                </span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onOpenArticle(article)
              }}
              title="View/Edit Article"
            >
              <Edit2 className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onRegeneratePreview(article.id.toString())
              }}
              disabled={regeneratingPreviews.has(article.id)}
              title="Regenerate Preview"
              className="text-blue-500 hover:text-blue-700 hover:bg-blue-50 dark:bg-blue-950"
            >
              {regeneratingPreviews.has(article.id) ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <RotateCw className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation()
                onDeleteArticle(article.id.toString(), article.title)
              }}
              title="Delete Article"
              className="text-red-500 hover:text-red-700 hover:bg-red-50 dark:bg-red-950"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            {article.url && (
              <Button
                variant="ghost"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation()
                  window.open(article.url, '_blank')
                }}
                title="Open Original"
              >
                <ExternalLink className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {article.preview && (
          <div className="prose prose-sm max-w-none line-clamp-3 text-gray-600 dark:text-gray-400">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {article.preview}
            </ReactMarkdown>
          </div>
        )}

        {article.summary && (
          <div className="mt-3">
            <div
              className="flex items-center gap-2 mb-2 cursor-pointer hover:opacity-80 transition-opacity select-none"
              onClick={() => onToggleSummary(article.id)}
            >
              <div className="flex items-center gap-2 flex-1">
                {expandedSummaries.has(article.id) ? (
                  <ChevronDown className="h-4 w-4 text-blue-600" />
                ) : (
                  <ChevronRightIcon className="h-4 w-4 text-blue-600" />
                )}
                <Sparkles className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium text-blue-900">AI Summary</span>
              </div>
            </div>

            {expandedSummaries.has(article.id) && (
              <div
                className="p-4 rounded-lg relative"
                style={{
                  background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0f9ff 100%)',
                  border: '1px solid #bfdbfe',
                  boxShadow: 'inset 0 1px 3px rgba(147, 197, 253, 0.2)'
                }}
                onMouseUp={() => {
                  const selection = window.getSelection()
                  const text = selection?.toString().trim()
                  if (text && text.length > 2) {
                    setSelectedTextForConcept({ articleId: article.id, text })
                  }
                }}
              >
                {selectedTextForConcept?.articleId === article.id && (
                  <div className="absolute top-2 right-2 z-10">
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={async (e) => {
                        e.stopPropagation()
                        if (!selectedTextForConcept) return

                        try {
                          const response = await axios.post(
                            `/api/articles/${article.id}/concepts?text=${encodeURIComponent(selectedTextForConcept.text)}`
                          )
                          if (response.data.success) {
                            await onRefreshArticles()
                            setSelectedTextForConcept(null)
                            window.getSelection()?.removeAllRanges()
                          }
                        } catch (error) {
                          console.error('Error creating concept:', error)
                          alert('Failed to create concept')
                        }
                      }}
                      className="text-xs shadow-md"
                    >
                      <Plus className="h-3 w-3 mr-1" />
                      Create Concept
                    </Button>
                  </div>
                )}
                <div className="prose prose-sm max-w-none text-gray-700 dark:text-gray-300 dark:text-gray-600">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {article.summary}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-0">
        <div className="flex flex-wrap gap-2 items-center">
          {article.concepts.map(concept => (
            <Badge
              key={concept.concept_id}
              variant="outline"
              className="cursor-pointer group"
              style={{
                backgroundColor: '#DBEAFE',
                color: '#1E40AF'
              }}
              onClick={(e) => {
                e.stopPropagation()
                if (!selectedConcepts.includes(concept.concept_id)) {
                  onToggleConcept(concept.concept_id)
                }
              }}
            >
              <span className="mr-1">{conceptService.getConceptIcon(concept)}</span>
              {concept.display_name}
              <button
                onClick={async (e) => {
                  e.stopPropagation()
                  setRemovingConceptId(concept.concept_id)
                  const success = await conceptService.removeConceptFromContent('article', article.id.toString(), concept.concept_id)
                  if (success) {
                    onConceptRemoved?.(article.id, concept.concept_id)
                    onRefreshArticles()
                  }
                  setRemovingConceptId(null)
                }}
                className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity hover:text-red-600"
                disabled={removingConceptId === concept.concept_id}
              >
                {removingConceptId === concept.concept_id ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <X className="h-3 w-3" />
                )}
              </button>
            </Badge>
          ))}

          {/* Inline Add Concept */}
          {isAddingConcept ? (
            <div className="flex items-center gap-1">
              <Input
                value={newConceptText}
                onChange={(e) => setNewConceptText(e.target.value)}
                onKeyDown={async (e) => {
                  if (e.key === 'Enter' && newConceptText.trim()) {
                    e.preventDefault()
                    setAddingConceptLoading(true)
                    const concept = await conceptService.addConceptToContent('article', article.id.toString(), newConceptText.trim())
                    if (concept) {
                      onConceptAdded?.(article.id, concept)
                      onRefreshArticles()
                    }
                    setNewConceptText('')
                    setIsAddingConcept(false)
                    setAddingConceptLoading(false)
                  } else if (e.key === 'Escape') {
                    setNewConceptText('')
                    setIsAddingConcept(false)
                  }
                }}
                placeholder="Concept name..."
                className="h-7 w-40 text-xs"
                autoFocus
                disabled={addingConceptLoading}
              />
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0"
                disabled={!newConceptText.trim() || addingConceptLoading}
                onClick={async () => {
                  if (!newConceptText.trim()) return
                  setAddingConceptLoading(true)
                  const concept = await conceptService.addConceptToContent('article', article.id.toString(), newConceptText.trim())
                  if (concept) {
                    onConceptAdded?.(article.id, concept)
                    onRefreshArticles()
                  }
                  setNewConceptText('')
                  setIsAddingConcept(false)
                  setAddingConceptLoading(false)
                }}
              >
                {addingConceptLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="h-7 w-7 p-0"
                onClick={() => { setNewConceptText(''); setIsAddingConcept(false) }}
              >
                <X className="h-3 w-3" />
              </Button>
            </div>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              className="h-7 px-2 text-xs text-muted-foreground hover:text-foreground"
              onClick={(e) => { e.stopPropagation(); setIsAddingConcept(true) }}
            >
              <Plus className="h-3 w-3 mr-1" />Add Concept
            </Button>
          )}

          {/* Suggest button */}
          <Button
            size="sm"
            variant="ghost"
            className="h-7 px-2 text-xs text-purple-600 hover:text-purple-800 hover:bg-purple-50"
            onClick={(e) => { e.stopPropagation(); setShowSuggestModal(true) }}
          >
            <Sparkles className="h-3 w-3 mr-1" />Suggest
          </Button>
        </div>
      </CardFooter>

      {/* Tag Suggestion Modal */}
      {showSuggestModal && (
        <TagSuggestionModalModern
          contentId={article.id}
          contentType="article"
          contentTitle={article.title}
          contentPreview={article.preview}
          isOpen={showSuggestModal}
          onClose={() => setShowSuggestModal(false)}
          onTagsUpdated={() => {
            onRefreshArticles()
            setShowSuggestModal(false)
          }}
        />
      )}
    </Card>
  )
}
