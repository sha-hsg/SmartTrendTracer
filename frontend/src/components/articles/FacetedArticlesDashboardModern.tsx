import React, { useState, useEffect, useCallback, Suspense } from 'react'
import http from '@/services/http'
import { cn } from '@/lib/utils'
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import ArticleViewerErrorBoundary from '../ArticleViewerErrorBoundary'

const ArticleViewerModern = React.lazy(() => import('../article-viewer/ArticleViewerModern'))
import ArticleImportModal from '../ArticleImportModal'
import AuthorManagementModal from '../AuthorManagementModal'
import ArticleCard from './ArticleCard'
import ArticleFilterPanel from './ArticleFilterPanel'
import type { Article } from './ArticleCard'
import {
  Search,
  FileText,
  Loader2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Eye,
  EyeOff,
  Plus,
  Sparkles,
  X,
} from 'lucide-react'
import { Concept } from '@/types/concept'

interface AuthorFacet {
  name: string
  count: number
}

interface ConceptFacet extends Concept {
  count: number
  children?: ConceptFacet[]
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


export default function FacetedArticlesDashboardModern() {
  const [articles, setArticles] = useState<Article[]>([])
  const [facets, setFacets] = useState<{ authors: AuthorFacet[]; concepts: ConceptFacet[] }>({
    authors: [],
    concepts: []
  })
  const [selectedAuthors, setSelectedAuthors] = useState<string[]>([])
  const [selectedConcepts, setSelectedConcepts] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [totalArticles, setTotalArticles] = useState(0)
  const [pageSize] = useState(50)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(null)
  const [showViewer, setShowViewer] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [showAuthorManagementModal, setShowAuthorManagementModal] = useState(false)
  const [showHierarchy, setShowHierarchy] = useState(false)
  const [hierarchyFacets, setHierarchyFacets] = useState<ConceptFacet[]>([])
  const [expandedConcepts, setExpandedConcepts] = useState<Set<string>>(new Set())
  const [regeneratingPreviews, setRegeneratingPreviews] = useState<Set<string | number>>(new Set())
  const [expandedSummaries, setExpandedSummaries] = useState<Set<string | number>>(new Set())

  // Batch annotation state
  const [batchAnnotating, setBatchAnnotating] = useState(false)
  const [batchProgress, setBatchProgress] = useState<{
    total: number
    completed: number
    failed: number
    current: string
  } | null>(null)
  const [batchCancelRef] = useState<{ cancelled: boolean }>({ cancelled: false })

  const fetchArticles = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('page', currentPage.toString())
      params.append('page_size', pageSize.toString())

      if (searchTerm) {
        params.append('search', searchTerm)
      }

      selectedAuthors.forEach(author => params.append('authors', author))
      selectedConcepts.forEach(conceptId => params.append('concept_ids', conceptId))

      const response = await http.get<FacetedSearchResponse>(
        `/api/articles/faceted-search?${params}`
      )

      setArticles(response.data.articles)
      setFacets(response.data.facets)
      setTotalArticles(response.data.total)
    } catch (error) {
      console.error('Error fetching articles:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const fetchHierarchy = async () => {
    try {
      const response = await http.get(`/api/articles/concepts/hierarchy`)
      setHierarchyFacets(response.data)
    } catch (error) {
      console.error('Error fetching concept hierarchy:', error)
    }
  }

  useEffect(() => {
    fetchArticles()
  }, [currentPage, selectedAuthors, selectedConcepts, searchTerm])

  // DEF-001: Refresh list when the article viewer is closed.
  // The viewer dispatches 'articleViewerClosed' (article-viewer/ArticleViewerModern.tsx);
  // in addition, the onClose prop below triggers a refresh (robust, prop-based).
  const handleViewerClosed = useCallback(() => {
    fetchArticles()
  }, [currentPage, selectedAuthors, selectedConcepts, searchTerm])

  useEffect(() => {
    window.addEventListener('articleViewerClosed', handleViewerClosed)
    return () => window.removeEventListener('articleViewerClosed', handleViewerClosed)
  }, [handleViewerClosed])

  useEffect(() => {
    if (showHierarchy) {
      fetchHierarchy()
    }
  }, [showHierarchy])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    setCurrentPage(1)
    fetchArticles()
  }

  const toggleAuthor = (authorName: string) => {
    setSelectedAuthors(prev =>
      prev.includes(authorName)
        ? prev.filter(a => a !== authorName)
        : [...prev, authorName]
    )
    setCurrentPage(1)
  }

  const toggleConcept = (conceptId: string) => {
    setSelectedConcepts(prev =>
      prev.includes(conceptId)
        ? prev.filter(c => c !== conceptId)
        : [...prev, conceptId]
    )
    setCurrentPage(1)
  }

  const toggleConceptExpansion = (conceptId: string) => {
    setExpandedConcepts(prev => {
      const newSet = new Set(prev)
      if (newSet.has(conceptId)) {
        newSet.delete(conceptId)
      } else {
        newSet.add(conceptId)
      }
      return newSet
    })
  }

  const openArticle = (article: Article) => {
    setSelectedArticle(article)
    setShowViewer(true)
  }

  const handleDeleteArticle = async (articleId: string, articleTitle: string) => {
    if (!window.confirm(`Are you sure you want to delete "${articleTitle}"?`)) {
      return
    }

    try {
      await http.delete(`/api/articles/${articleId}`)
      fetchArticles()
    } catch (error) {
      console.error('Error deleting article:', error)
      alert('Failed to delete article')
    }
  }

  const handleRegeneratePreview = async (articleId: string) => {
    const numericId = parseInt(articleId)
    setRegeneratingPreviews(prev => new Set(prev).add(numericId))

    try {
      const response = await http.post(`/api/article-preview/regenerate/${articleId}`)

      if (response.data.success) {
        setArticles(prev => prev.map(article =>
          article.id.toString() === articleId
            ? { ...article, preview: response.data.preview }
            : article
        ))

        if (response.data.removed_cdn) {
          console.log(`Preview regenerated and CDN images removed for article ${articleId}`)
          alert('✓ Preview regenerated successfully\nCDN images have been removed')
        } else if (response.data.changed) {
          console.log(`Preview regenerated for article ${articleId}`)
          alert('✓ Preview regenerated successfully')
        } else {
          console.log(`Preview unchanged for article ${articleId}`)
          alert('ℹ️ Preview is already up-to-date\nNo changes needed')
        }
      }
    } catch (error: any) {
      console.error('Error regenerating preview:', error)
      const errorMessage = error.response?.data?.detail || error.message || 'Unknown error'
      alert(`❌ Failed to regenerate preview\n\n${errorMessage}`)
    } finally {
      setRegeneratingPreviews(prev => {
        const newSet = new Set(prev)
        newSet.delete(numericId)
        return newSet
      })
    }
  }

  const handleRefreshArticles = () => {
    fetchArticles()
  }

  const handleToggleSummary = (articleId: string | number) => {
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

  // Count unannotated articles
  const unannotatedCount = articles.filter(a => !a.concepts || a.concepts.length === 0).length

  const handleBatchAnnotate = async () => {
    const unannotated = articles.filter(a => !a.concepts || a.concepts.length === 0)
    if (unannotated.length === 0) return

    setBatchAnnotating(true)
    batchCancelRef.cancelled = false
    setBatchProgress({ total: unannotated.length, completed: 0, failed: 0, current: '' })

    let completed = 0
    let failed = 0

    for (const article of unannotated) {
      if (batchCancelRef.cancelled) break

      setBatchProgress(prev => prev ? { ...prev, current: article.title } : null)

      try {
        // Get suggestions
        const suggestRes = await http.post(`/api/articles/${article.id}/tags/suggest`, {})
        const suggestions = suggestRes.data

        // Collect all suggestions (existing + new)
        const allSuggestions = [
          ...(suggestions.existing_suggestions || []),
          ...(suggestions.new_suggestions || [])
        ]

        if (allSuggestions.length > 0) {
          // Apply all suggestions
          const conceptsToApply = allSuggestions.map((c: any) => ({
            display_name: c.display_name,
            slug: c.slug
          }))

          await http.post(`/api/articles/${article.id}/apply-concepts`, conceptsToApply)
          completed++
        } else {
          completed++ // Count as completed even with no suggestions
        }
      } catch (error) {
        console.error(`Failed to annotate article ${article.id}:`, error)
        failed++
      }

      setBatchProgress(prev => prev ? { ...prev, completed: completed + failed, failed } : null)
    }

    setBatchAnnotating(false)
    fetchArticles() // Refresh to show new concepts
  }

  const totalPages = Math.ceil(totalArticles / pageSize)

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Articles</h1>
        <p className="text-gray-600 dark:text-gray-400">Browse and analyze web articles with advanced filtering</p>
      </div>

      {/* Search Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-3">
            <form onSubmit={handleSearch} className="flex-1 flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 h-4 w-4" />
                <Input
                  type="text"
                  placeholder="Search articles..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Button type="submit" disabled={isLoading}>
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
              </Button>
            </form>

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={() => setShowImportModal(true)}
                title="Import article from URL"
              >
                <Plus className="h-4 w-4 mr-2" />
                Import
              </Button>
              <Button
                variant="outline"
                onClick={handleRefreshArticles}
                disabled={isLoading}
              >
                <RefreshCw className={cn("h-4 w-4 mr-2", isLoading && "animate-spin")} />
                Refresh
              </Button>

              {unannotatedCount > 0 && (
                <Button
                  variant="outline"
                  onClick={handleBatchAnnotate}
                  disabled={batchAnnotating}
                  className="text-purple-600 border-purple-200 hover:bg-purple-50"
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  {batchAnnotating ? 'Annotating...' : `Annotate All (${unannotatedCount})`}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Batch Annotation Progress Banner */}
      {batchProgress && batchAnnotating && (
        <Card className="mb-6 border-purple-200 bg-purple-50/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-purple-600 animate-pulse" />
                <span className="text-sm font-medium text-purple-800">
                  Annotating Articles with AI...
                </span>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => { batchCancelRef.cancelled = true }}
                className="h-7 text-xs text-purple-600 hover:text-purple-800"
              >
                <X className="h-3 w-3 mr-1" />Cancel
              </Button>
            </div>
            <div className="w-full bg-purple-200 rounded-full h-2 mb-2">
              <div
                className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(batchProgress.completed / batchProgress.total) * 100}%` }}
              />
            </div>
            <div className="flex items-center justify-between text-xs text-purple-700">
              <span>{batchProgress.completed} / {batchProgress.total} completed{batchProgress.failed > 0 ? ` (${batchProgress.failed} failed)` : ''}</span>
              {batchProgress.current && (
                <span className="truncate max-w-xs">Processing: {batchProgress.current}</span>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content Grid - 12 column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <ArticleFilterPanel
          facets={facets}
          selectedAuthors={selectedAuthors}
          selectedConcepts={selectedConcepts}
          showHierarchy={showHierarchy}
          hierarchyFacets={hierarchyFacets}
          expandedConcepts={expandedConcepts}
          onToggleAuthor={toggleAuthor}
          onClearAuthors={() => setSelectedAuthors([])}
          onToggleConcept={toggleConcept}
          onClearConcepts={() => setSelectedConcepts([])}
          onToggleHierarchy={() => setShowHierarchy(!showHierarchy)}
          onToggleConceptExpansion={toggleConceptExpansion}
          onShowAuthorManagement={() => setShowAuthorManagementModal(true)}
        />

        {/* Main Content - Center */}
        <div className="lg:col-span-7 order-2 lg:order-2">
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
              {articles.some(a => a.summary) && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (expandedSummaries.size === articles.filter(a => a.summary).length) {
                      setExpandedSummaries(new Set())
                    } else {
                      setExpandedSummaries(new Set(articles.filter(a => a.summary).map(a => a.id)))
                    }
                  }}
                  className="text-xs"
                >
                  {expandedSummaries.size === articles.filter(a => a.summary).length ? (
                    <><EyeOff className="h-3 w-3 mr-1" /> Collapse All</>
                  ) : (
                    <><Eye className="h-3 w-3 mr-1" /> Expand All</>
                  )}
                </Button>
              )}

              {totalPages > 1 && (
                <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="h-4 w-4" />
                </Button>
                </div>
              )}
            </div>
          </div>

          {/* Articles List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400 dark:text-gray-500" />
            </div>
          ) : articles.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-gray-500 dark:text-gray-400">
                <FileText className="h-12 w-12 mb-4 text-gray-300 dark:text-gray-600" />
                <p className="text-lg font-medium">No articles found</p>
                <p className="text-sm mt-2">Try adjusting your filters or search terms</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {articles.map(article => (
                <ArticleCard
                  key={article.id}
                  article={article}
                  expandedSummaries={expandedSummaries}
                  regeneratingPreviews={regeneratingPreviews}
                  selectedConcepts={selectedConcepts}
                  onOpenArticle={openArticle}
                  onToggleSummary={handleToggleSummary}
                  onToggleConcept={toggleConcept}
                  onDeleteArticle={handleDeleteArticle}
                  onRegeneratePreview={handleRegeneratePreview}
                  onRefreshArticles={handleRefreshArticles}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Article Viewer Modal - Lazy loaded for code splitting */}
      {showViewer && selectedArticle && (
        <ArticleViewerErrorBoundary
          onClose={() => {
            setShowViewer(false)
            setSelectedArticle(null)
          }}
        >
          <Suspense fallback={
            <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center">
              <div className="bg-white dark:bg-gray-950 rounded-lg p-8 flex items-center">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading Article Viewer...</span>
              </div>
            </div>
          }>
            <ArticleViewerModern
              articleId={selectedArticle?.id}
              onClose={() => {
                setShowViewer(false)
                setSelectedArticle(null)
                // DEF-001: always refresh the list after the viewer closes
                fetchArticles()
              }}
              onArticleUpdated={handleRefreshArticles}
            />
          </Suspense>
        </ArticleViewerErrorBoundary>
      )}

      {/* Import Modals */}
      {showImportModal && (
        <ArticleImportModal
          isOpen={showImportModal}
          onClose={() => setShowImportModal(false)}
          onImportSuccess={() => {
            setShowImportModal(false)
            handleRefreshArticles()
          }}
        />
      )}


      {showAuthorManagementModal && (
        <AuthorManagementModal
          isOpen={showAuthorManagementModal}
          onClose={() => setShowAuthorManagementModal(false)}
          onAuthorsUpdated={() => {
            fetchArticles()
          }}
        />
      )}
    </div>
  )
}
