import React, { useState, useEffect, useCallback, Suspense } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { decodeHtmlEntities } from '@/utils/htmlDecoder'
import remarkGfm from 'remark-gfm'
import conceptService from '@/services/conceptService'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import ArticleViewerErrorBoundary from './ArticleViewerErrorBoundary'

// Lazy-loaded components for code-splitting (reduces initial bundle size)
const ArticleViewerModern = React.lazy(() => import('./ArticleViewerModern'))
import ArticleTagSuggestionModalModern from './ArticleTagSuggestionModalModern'
import ArticleImportModal from './ArticleImportModal'
import ArticleImportEnhancedModal from './ArticleImportEnhancedModal'
import {
  Search,
  FileText,
  User,
  Tag,
  Calendar,
  Loader2,
  ChevronLeft,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Clock,
  BookOpen,
  Sparkles,
  Eye,
  EyeOff,
  MessageSquare,
  Bookmark,
  X,
  Plus,
  Trash2,
  Download,
  ExternalLink
} from 'lucide-react'
import { cn } from "@/lib/utils"

interface AuthorFacet {
  id: number
  name: string
  count: number
}

interface ConceptFacet {
  concept_id: string
  slug: string
  display_name: string
  count: number
}

interface ArticleConcept {
  concept_id: string
  display_name: string
  slug: string
}

interface Article {
  id: string  // MongoDB ObjectId as string
  title: string
  subtitle: string | null
  author?: {
    name: string
    subdomain: string
  }
  published_at: string | null
  word_count?: number
  reading_time_minutes?: number
  preview: string
  summary?: string | null
  has_summary?: boolean
  concepts: ArticleConcept[]  // Updated to use concepts
  snippet_count?: number
  url?: string
}

interface FacetedSearchResponse {
  articles: Article[]
  facets: {
    authors: AuthorFacet[]
    concepts: ConceptFacet[]
  }
  total: number
  page: number
  page_size: number
}

export default function FacetedSubstackDashboardModern() {
  const [articles, setArticles] = useState<Article[]>([])
  const [facets, setFacets] = useState<{ authors: AuthorFacet[]; concepts: ConceptFacet[] }>({
    authors: [],
    concepts: []
  })
  const [selectedAuthors, setSelectedAuthors] = useState<string[]>([])  // Now uses author names
  const [selectedConcepts, setSelectedConcepts] = useState<string[]>([])  // Now uses concept_ids
  const [searchTerm, setSearchTerm] = useState('')
  const [hasSummary, setHasSummary] = useState<boolean | null>(null)
  const [hasSnippets, setHasSnippets] = useState<boolean | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalArticles, setTotalArticles] = useState(0)
  const [loading, setLoading] = useState(false)
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null)
  const [selectedArticleForTags, setSelectedArticleForTags] = useState<Article | null>(null)
  const [showAllTags, setShowAllTags] = useState(false)
  const [viewMode, _setViewMode] = useState<'grid' | 'list'>('grid')
  const [addingTagForArticle, setAddingTagForArticle] = useState<string | null>(null)
  const [newTag, setNewTag] = useState('')
  const [showImportModal, setShowImportModal] = useState(false)
  const [showEnhancedImportModal, setShowEnhancedImportModal] = useState(false)
  const [expandedSummaries, setExpandedSummaries] = useState<Set<string>>(new Set())

  const pageSize = 20
  const totalPages = Math.ceil(totalArticles / pageSize)

  useEffect(() => {
    fetchArticles()
  }, [selectedAuthors, selectedConcepts, searchTerm, hasSummary, hasSnippets, currentPage])

  // Listen for snippet updates from ArticleViewerModern
  useEffect(() => {
    const handleSnippetsUpdated = (event: CustomEvent) => {
      const { articleId } = event.detail
      // Increment snippet_count locally
      setArticles(prev => prev.map(article =>
        article.id === articleId
          ? { ...article, snippet_count: (article.snippet_count || 0) + 1 }
          : article
      ))
    }

    window.addEventListener('articleSnippetsUpdated', handleSnippetsUpdated as EventListener)
    return () => {
      window.removeEventListener('articleSnippetsUpdated', handleSnippetsUpdated as EventListener)
    }
  }, [])

  // Handler for article viewer close - extracted to useCallback for stable reference
  const handleViewerClosed = useCallback(async (event: CustomEvent) => {
    const { articleId } = event.detail
    console.log('🟠 articleViewerClosed event received for:', articleId)

    try {
      const response = await axios.get(`http://localhost:8000/api/articles/${articleId}`)
      const updatedArticle = response.data
      console.log('🟠 Fetched updated article:', {
        snippet_count: updatedArticle.snippets?.length,
        has_summary: !!updatedArticle.summary
      })

      setArticles(prev => prev.map(article =>
        article.id === articleId
          ? {
              ...article,
              concepts: updatedArticle.concepts,
              snippet_count: updatedArticle.snippets?.length || 0,
              summary: updatedArticle.summary,
              has_summary: !!updatedArticle.summary
            }
          : article
      ))
    } catch (error) {
      console.error('🟠 Error fetching updated article:', error)
    }
  }, [])

  // Listen for article viewer close to refresh article data
  useEffect(() => {
    window.addEventListener('articleViewerClosed', handleViewerClosed as unknown as EventListener)
    return () => {
      window.removeEventListener('articleViewerClosed', handleViewerClosed as unknown as EventListener)
    }
  }, [handleViewerClosed])

  const fetchArticles = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('page', currentPage.toString())
      params.append('page_size', pageSize.toString())

      if (searchTerm) {
        params.append('search', searchTerm)
      }

      if (hasSummary !== null) {
        params.append('has_summary', hasSummary.toString())
      }

      if (hasSnippets !== null) {
        params.append('has_snippets', hasSnippets.toString())
      }

      // Use author names for filtering
      selectedAuthors.forEach(authorName => params.append('authors', authorName))
      // Use concept_ids for filtering
      selectedConcepts.forEach(conceptId => params.append('concept_ids', conceptId))

      const response = await axios.get<FacetedSearchResponse>(
        `http://localhost:8000/api/articles/faceted-search?${params.toString()}`
      )

      setArticles(response.data.articles)
      setFacets(response.data.facets)
      setTotalArticles(response.data.total)
    } catch (error) {
      console.error('Error fetching articles:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleAuthor = (authorName: string) => {
    if (!authorName) return
    setSelectedAuthors(prev => {
      if (prev.includes(authorName)) {
        return prev.filter(name => name !== authorName)
      }
      return [...prev, authorName]
    })
    setCurrentPage(1)
  }

  const toggleConcept = (conceptId: string) => {
    setSelectedConcepts(prev => {
      if (prev.includes(conceptId)) {
        return prev.filter(id => id !== conceptId)
      }
      return [...prev, conceptId]
    })
    setCurrentPage(1)
  }

  const clearFilters = () => {
    setSelectedAuthors([])
    setSelectedConcepts([])
    setSearchTerm('')
    setHasSummary(null)
    setHasSnippets(null)
    setCurrentPage(1)
  }

  const handleAddConcept = async (articleId: string, text: string) => {
    try {
      const concept = await conceptService.addConceptToContent('article', articleId, text)
      if (concept) {
        // Local state update - no full refresh needed
        setArticles(prev => prev.map(article =>
          article.id === articleId
            ? { ...article, concepts: [...(article.concepts || []), concept] }
            : article
        ))
      }
      setNewTag('')
      setAddingTagForArticle(null)
    } catch (error) {
      console.error('Error adding concept:', error)
    }
  }

  const handleRemoveConcept = async (articleId: string, conceptId: string) => {
    try {
      const success = await conceptService.removeConceptFromContent('article', articleId, conceptId)
      if (success) {
        // Local state update - no full refresh needed
        setArticles(prev => prev.map(article =>
          article.id === articleId
            ? { ...article, concepts: article.concepts?.filter(c => c.concept_id !== conceptId) }
            : article
        ))
      }
    } catch (error) {
      console.error('Error removing concept:', error)
    }
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

  const handleDeleteArticle = async (articleId: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent opening the article

    if (!window.confirm('Are you sure you want to delete this article?')) {
      return
    }

    try {
      await axios.delete(`http://localhost:8000/api/articles/${articleId}`)
      fetchArticles() // Refresh the list
    } catch (error) {
      console.error('Error deleting article:', error)
      alert('Failed to delete article')
    }
  }

  const toggleSummary = (articleId: string, e: React.MouseEvent) => {
    e.stopPropagation() // Prevent opening the article
    setExpandedSummaries(prev => {
      const newSet = new Set(prev)
      if (newSet.has(articleId)) {
        newSet.delete(articleId)
      } else {
        newSet.add(articleId)
      }
      return newSet
    })
  }

  const renderArticleCard = (article: Article) => (
    <Card 
      className="h-full flex flex-col hover:shadow-lg transition-all duration-200 cursor-pointer"
      onClick={() => setSelectedArticleId(article.id)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg line-clamp-2">
            {decodeHtmlEntities(article.title)}
          </CardTitle>
          <div className="flex gap-1 shrink-0 items-start">
            {article.url && (
              <Badge 
                variant="outline" 
                className="border-green-200 bg-green-50 cursor-pointer hover:bg-green-100" 
                title="Has external URL - Click to open"
                onClick={(e) => {
                  e.stopPropagation()
                  window.open(article.url, '_blank')
                }}
              >
                <ExternalLink className="h-3 w-3 text-green-600" />
              </Badge>
            )}
            {article.has_summary && (
              <Badge variant="outline" className="border-purple-200 bg-purple-50" title="Has AI Summary">
                <Sparkles className="h-3 w-3 text-purple-600" />
              </Badge>
            )}
            {(article.snippet_count ?? 0) > 0 && (
              <Badge variant="outline" className="border-blue-200 bg-blue-50" title={`${article.snippet_count} snippet${article.snippet_count !== 1 ? 's' : ''}`}>
                <MessageSquare className="h-3 w-3 text-blue-600 mr-1" />
                {article.snippet_count}
              </Badge>
            )}
            <Button
              size="sm"
              variant="ghost"
              className="h-6 w-6 p-0 hover:bg-red-100 hover:text-red-600"
              onClick={(e) => handleDeleteArticle(article.id, e)}
              title="Delete article"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </div>
        {article.subtitle && (
          <CardDescription className="text-sm line-clamp-2 mt-1">
            {article.subtitle}
          </CardDescription>
        )}
      </CardHeader>
      
      <CardContent className="flex-1 pb-3">
        <div className="flex items-center gap-4 text-xs text-gray-500 mb-3">
          <div className="flex items-center gap-1">
            <User className="h-3 w-3" />
            <span>{article.author?.name || 'Unknown Author'}</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="h-3 w-3" />
            <span>{formatDate(article.published_at)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>{article.reading_time_minutes} min</span>
          </div>
        </div>

        {/* Preview text (always shown) */}
        <div className="text-sm text-gray-600 line-clamp-3 prose prose-sm max-w-none mb-2">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              p: ({children}) => <p className="mb-2">{children}</p>,
              a: ({children}) => <span className="text-blue-600">{children}</span>,
              strong: ({children}) => <strong className="font-semibold">{children}</strong>,
              em: ({children}) => <em className="italic">{children}</em>,
              ul: ({children}) => <ul className="list-disc ml-4">{children}</ul>,
              ol: ({children}) => <ol className="list-decimal ml-4">{children}</ol>,
              li: ({children}) => <li className="mb-1">{children}</li>,
              h1: ({children}) => <span className="font-bold">{children}</span>,
              h2: ({children}) => <span className="font-bold">{children}</span>,
              h3: ({children}) => <span className="font-semibold">{children}</span>,
              blockquote: ({children}) => <span className="italic">{children}</span>,
              code: ({children}) => <code className="bg-gray-100 px-1 rounded">{children}</code>,
            }}
          >
            {article.preview}
          </ReactMarkdown>
        </div>

        {/* Expandable AI Summary Section */}
        {article.has_summary && article.summary && (
          <div className="mt-2">
            <button
              onClick={(e) => toggleSummary(article.id, e)}
              className="flex items-center gap-2 text-sm font-medium text-green-700 hover:text-green-800 transition-colors"
            >
              {expandedSummaries.has(article.id) ? (
                <ChevronUp className="h-4 w-4" />
              ) : (
                <ChevronDown className="h-4 w-4" />
              )}
              <Sparkles className="h-3 w-3" />
              AI Summary
            </button>

            {expandedSummaries.has(article.id) && (
              <div className="mt-2 p-3 rounded-lg border border-green-200 bg-green-50">
                <div className="text-sm text-gray-700 prose prose-sm max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      p: ({children}) => <p className="mb-2">{children}</p>,
                      a: ({children}) => <span className="text-green-700 underline">{children}</span>,
                      strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                      em: ({children}) => <em className="italic">{children}</em>,
                      ul: ({children}) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
                      li: ({children}) => <li className="mb-1">{children}</li>,
                      h1: ({children}) => <span className="font-bold text-green-800">{children}</span>,
                      h2: ({children}) => <span className="font-bold text-green-800">{children}</span>,
                      h3: ({children}) => <span className="font-semibold text-green-700">{children}</span>,
                      blockquote: ({children}) => <blockquote className="border-l-2 border-green-300 pl-3 italic">{children}</blockquote>,
                      code: ({children}) => <code className="bg-green-100 px-1 rounded text-green-800">{children}</code>,
                    }}
                  >
                    {article.summary}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
      
      <CardFooter className="pt-0">
        <div className="w-full space-y-2">
          {/* Concepts Display */}
          {article.concepts && article.concepts.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {article.concepts.map((concept) => (
                <TagBadge
                  key={`${article.id}-concept-${concept.concept_id}`}
                  variant="default"
                  size="sm"
                  removable
                  onRemove={() => handleRemoveConcept(article.id, concept.concept_id)}
                >
                  {concept.display_name}
                </TagBadge>
              ))}
            </div>
          )}

          {/* Concept Management UI */}
          <div className="flex gap-2">
            {addingTagForArticle === article.id ? (
              <>
                <Input
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && newTag.trim()) {
                      e.stopPropagation()
                      handleAddConcept(article.id, newTag.trim())
                    }
                  }}
                  placeholder="Enter concept name..."
                  className="flex-1 h-8"
                  onClick={(e) => e.stopPropagation()}
                  autoFocus
                />
                <Button
                  onClick={(e) => {
                    e.stopPropagation()
                    if (newTag.trim()) {
                      handleAddConcept(article.id, newTag.trim())
                    }
                  }}
                  size="sm"
                  variant="default"
                >
                  <Plus className="h-3 w-3" />
                </Button>
                <Button 
                  onClick={(e) => {
                    e.stopPropagation()
                    setAddingTagForArticle(null)
                    setNewTag('')
                  }} 
                  size="sm" 
                  variant="ghost"
                >
                  <X className="h-3 w-3" />
                </Button>
              </>
            ) : (
              <>
                <Button 
                  size="sm" 
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation()
                    setAddingTagForArticle(article.id)
                  }}
                >
                  <Tag className="h-3 w-3 mr-1" />
                  Add Tag
                </Button>
                <Button 
                  size="sm" 
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedArticleForTags(article)
                  }}
                >
                  <Sparkles className="h-3 w-3 mr-1" />
                  Suggest Concept Tags
                </Button>
              </>
            )}
          </div>
        </div>
      </CardFooter>
    </Card>
  )

  const displayedConcepts = showAllTags ? facets.concepts : facets.concepts.slice(0, 20)

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Newsletter Articles
              {totalArticles > 0 && (
                <span className="ml-3 text-lg font-normal text-gray-500">
                  ({totalArticles} {totalArticles === 1 ? 'article' : 'articles'})
                </span>
              )}
            </h1>
            <p className="text-gray-600">
              Browse and analyze Substack newsletters with AI insights
              {(hasSummary !== null || hasSnippets !== null) && (
                <span className="ml-2 text-sm">
                  • Filtering: 
                  {hasSummary === true && " With summaries"}
                  {hasSummary === false && " Without summaries"}
                  {hasSummary !== null && hasSnippets !== null && " and"}
                  {hasSnippets === true && " With snippets"}
                  {hasSnippets === false && " Without snippets"}
                </span>
              )}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setShowImportModal(true)}
              variant="outline"
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Import from URL
            </Button>
            <Button
              onClick={() => setShowEnhancedImportModal(true)}
              variant="default"
              className="flex items-center gap-2"
            >
              <ExternalLink className="h-4 w-4" />
              Import (Subscriber)
            </Button>
          </div>
        </div>
      </div>

      {/* Search Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                type="text"
                placeholder="Search articles..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setCurrentPage(1)
                }}
                className="pl-10"
              />
            </div>
            
            <div className="flex items-center gap-4">
              <div className="flex gap-2">
                <Button
                  variant={hasSummary === true ? "default" : hasSummary === false ? "destructive" : "outline"}
                  size="sm"
                  onClick={() => {
                    // Cycle through: null -> true -> false -> null
                    if (hasSummary === null) {
                      setHasSummary(true)
                    } else if (hasSummary === true) {
                      setHasSummary(false)
                    } else {
                      setHasSummary(null)
                    }
                    setCurrentPage(1)
                  }}
                  className="flex items-center gap-1"
                >
                  {hasSummary === true ? (
                    <><Sparkles className="h-3 w-3" /> With Summary</>
                  ) : hasSummary === false ? (
                    <><X className="h-3 w-3" /> No Summary</>
                  ) : (
                    <><Sparkles className="h-3 w-3" /> Summary Filter</>
                  )}
                </Button>
                
                <Button
                  variant={hasSnippets === true ? "default" : hasSnippets === false ? "destructive" : "outline"}
                  size="sm"
                  onClick={() => {
                    // Cycle through: null -> true -> false -> null
                    if (hasSnippets === null) {
                      setHasSnippets(true)
                    } else if (hasSnippets === true) {
                      setHasSnippets(false)
                    } else {
                      setHasSnippets(null)
                    }
                    setCurrentPage(1)
                  }}
                  className="flex items-center gap-1"
                >
                  {hasSnippets === true ? (
                    <><Bookmark className="h-3 w-3" /> With Snippets</>
                  ) : hasSnippets === false ? (
                    <><X className="h-3 w-3" /> No Snippets</>
                  ) : (
                    <><Bookmark className="h-3 w-3" /> Snippet Filter</>
                  )}
                </Button>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button onClick={fetchArticles} variant="outline" disabled={loading}>
                <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                Refresh
              </Button>
              {(selectedAuthors.length > 0 || selectedConcepts.length > 0 || searchTerm) && (
                <Button onClick={clearFilters} variant="outline">
                  <X className="h-4 w-4 mr-2" />
                  Clear
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Filters */}
        <div className="lg:col-span-1 space-y-4">
          {/* Authors Filter */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="h-4 w-4" />
                Authors
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[250px]">
                <div className="px-4 pb-4">
                  {facets.authors.filter(author => author.name).map(author => (
                    <div
                      key={`author-${author.name}`}
                      className={cn(
                        "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 cursor-pointer transition-colors mb-1",
                        selectedAuthors.includes(author.name) && "bg-blue-50"
                      )}
                      onClick={() => toggleAuthor(author.name)}
                    >
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={selectedAuthors.includes(author.name)}
                          onCheckedChange={() => toggleAuthor(author.name)}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <span className="text-sm font-medium text-gray-900">{author.name || 'Unknown Author'}</span>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {author.count}
                      </Badge>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Concepts Filter */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Concepts
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[350px]">
                <div className="px-4 pb-4 space-y-1">
                  {displayedConcepts.map(concept => (
                    <div
                      key={`concept-${concept.concept_id}`}
                      className={cn(
                        "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 cursor-pointer transition-colors",
                        selectedConcepts.includes(concept.concept_id) && "bg-blue-50"
                      )}
                      onClick={() => toggleConcept(concept.concept_id)}
                    >
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={selectedConcepts.includes(concept.concept_id)}
                          onCheckedChange={() => toggleConcept(concept.concept_id)}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <TagBadge variant="default" size="sm">
                          {concept.display_name}
                        </TagBadge>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {concept.count}
                      </Badge>
                    </div>
                  ))}
                </div>
                {facets.concepts.length > 20 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full mt-2"
                    onClick={() => setShowAllTags(!showAllTags)}
                  >
                    {showAllTags ? (
                      <>
                        <EyeOff className="h-3 w-3 mr-2" />
                        Show Less
                      </>
                    ) : (
                      <>
                        <Eye className="h-3 w-3 mr-2" />
                        Show All ({facets.concepts.length})
                      </>
                    )}
                  </Button>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {/* Stats Bar */}
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="py-1.5 px-3">
                <FileText className="h-3 w-3 mr-1" />
                {totalArticles} articles
              </Badge>
              {selectedAuthors.length > 0 && (
                <Badge variant="secondary" className="py-1.5 px-3">
                  {selectedAuthors.length} author{selectedAuthors.length !== 1 ? 's' : ''} selected
                </Badge>
              )}
              {selectedConcepts.length > 0 && (
                <Badge variant="secondary" className="py-1.5 px-3">
                  {selectedConcepts.length} concept{selectedConcepts.length !== 1 ? 's' : ''} selected
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">
                Page {currentPage} of {totalPages}
              </span>
            </div>
          </div>

          {/* Articles Grid/List */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : articles.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <BookOpen className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No articles found matching your filters</p>
              </CardContent>
            </Card>
          ) : (
            <div className={cn(
              "grid gap-4",
              viewMode === 'grid' ? "grid-cols-1 md:grid-cols-2" : "grid-cols-1"
            )}>
              {articles.map(article => (
                <div key={article.id}>
                  {renderArticleCard(article)}
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <Button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1 || loading}
                variant="outline"
                size="sm"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              
              <div className="flex gap-1">
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  let pageNum: number
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }
                  
                  return (
                    <Button
                      key={`page-${pageNum}`}
                      onClick={() => setCurrentPage(pageNum)}
                      variant={currentPage === pageNum ? "default" : "outline"}
                      size="sm"
                      className="w-10"
                    >
                      {pageNum}
                    </Button>
                  )
                })}
              </div>
              
              <Button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages || loading}
                variant="outline"
                size="sm"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Article Viewer Modal - Lazy loaded for code splitting */}
      {selectedArticleId && (
        <ArticleViewerErrorBoundary>
          <Suspense fallback={
            <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
              <div className="bg-white rounded-lg p-8 flex items-center">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="ml-2 text-gray-600">Loading Article Viewer...</span>
              </div>
            </div>
          }>
            <ArticleViewerModern
              articleId={selectedArticleId}
              onClose={() => {
                // Article data update handled by articleViewerClosed event
                setSelectedArticleId(null)
              }}
            />
          </Suspense>
        </ArticleViewerErrorBoundary>
      )}

      {/* Tag Suggestion Modal */}
      {selectedArticleForTags && (
        <ArticleTagSuggestionModalModern
          article={selectedArticleForTags}
          isOpen={!!selectedArticleForTags}
          onClose={() => setSelectedArticleForTags(null)}
          onTagsUpdated={async () => {
            // Fetch only the updated article's concepts - no full refresh needed
            try {
              const response = await axios.get(`http://localhost:8000/api/articles/${selectedArticleForTags.id}`)
              const updatedArticle = response.data
              setArticles(prev => prev.map(article =>
                article.id === selectedArticleForTags.id
                  ? { ...article, concepts: updatedArticle.concepts }
                  : article
              ))
            } catch (error) {
              console.error('Error fetching updated article:', error)
            }
          }}
        />
      )}

      {/* Article Import Modal */}
      <ArticleImportModal
        isOpen={showImportModal}
        onClose={() => setShowImportModal(false)}
        onImportSuccess={() => {
          fetchArticles()
          setShowImportModal(false)
        }}
      />

      {/* Enhanced Article Import Modal */}
      <ArticleImportEnhancedModal
        isOpen={showEnhancedImportModal}
        onClose={() => setShowEnhancedImportModal(false)}
        onImportSuccess={() => {
          fetchArticles()
          setShowEnhancedImportModal(false)
        }}
      />
    </div>
  )
}