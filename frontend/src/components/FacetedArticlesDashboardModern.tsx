import React, { useState, useEffect, Suspense } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import ArticleViewerErrorBoundary from './ArticleViewerErrorBoundary'

// Lazy-loaded components for code-splitting (reduces initial bundle size)
const ArticleViewerModern = React.lazy(() => import('./ArticleViewerModern'))
import ArticleImportModal from './ArticleImportModal'
import ArticleImportEnhancedModal from './ArticleImportEnhancedModal'
import AuthorManagementModal from './AuthorManagementModal'
import { 
  Search, 
  FileText, 
  User, 
  Tag, 
  Calendar,
  Loader2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Sparkles,
  Eye,
  EyeOff,
  MessageSquare,
  X,
  Plus,
  Trash2,
  ExternalLink,
  GitBranch,
  Layers,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
  RotateCw,
  Edit2
} from 'lucide-react'
import { cn } from "@/lib/utils"
import { Concept } from '@/types/concept'
import conceptService from '@/services/conceptService'

interface AuthorFacet {
  name: string
  count: number
}

interface ConceptFacet extends Concept {
  count: number
  children?: ConceptFacet[]
}

interface Article {
  id: number | string  // Support both MongoDB string IDs and old numeric IDs
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
  content?: string  // Full article content
  content_length: number
  snippet_count: number
  summary?: string | null
  created_at?: string
  concepts: Concept[]
  concept_ids: string[]
  metrics?: any
  summarized?: boolean
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

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  const [showEnhancedImportModal, setShowEnhancedImportModal] = useState(false)
  const [showAuthorManagementModal, setShowAuthorManagementModal] = useState(false)
  const [showHierarchy, setShowHierarchy] = useState(false)
  const [hierarchyFacets, setHierarchyFacets] = useState<ConceptFacet[]>([])
  const [expandedConcepts, setExpandedConcepts] = useState<Set<string>>(new Set())
  const [regeneratingPreviews, setRegeneratingPreviews] = useState<Set<string | number>>(new Set())
  const [expandedSummaries, setExpandedSummaries] = useState<Set<string | number>>(new Set())
  const [selectedTextForConcept, setSelectedTextForConcept] = useState<{ articleId: string | number; text: string } | null>(null)

  // Fetch faceted data
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
      
      const response = await axios.get<FacetedSearchResponse>(
        `${API_BASE_URL}/api/articles/faceted-search?${params}`
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

  // Fetch hierarchy data for concepts
  const fetchHierarchy = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/articles/concepts/hierarchy`)
      setHierarchyFacets(response.data)
    } catch (error) {
      console.error('Error fetching concept hierarchy:', error)
    }
  }

  useEffect(() => {
    fetchArticles()
  }, [currentPage, selectedAuthors, selectedConcepts, searchTerm])

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
      await axios.delete(`http://localhost:8000/api/articles/${articleId}`)
      // Refresh the articles list after deletion
      fetchArticles()
    } catch (error) {
      console.error('Error deleting article:', error)
      alert('Failed to delete article')
    }
  }

  const handleRegeneratePreview = async (articleId: string) => {
    // Add to regenerating set (convert string to number for the set)
    const numericId = parseInt(articleId)
    setRegeneratingPreviews(prev => new Set(prev).add(numericId))
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/article-preview/regenerate/${articleId}`)
      
      if (response.data.success) {
        // Update the article preview in the local state
        setArticles(prev => prev.map(article => 
          article.id.toString() === articleId 
            ? { ...article, preview: response.data.preview }
            : article
        ))
        
        // Show success feedback
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
      // Remove from regenerating set
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

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown date'
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }).format(date)
  }

  const renderHierarchicalConcept = (concept: ConceptFacet, level: number = 0) => {
    const isExpanded = expandedConcepts.has(concept.concept_id)
    const hasChildren = concept.children && concept.children.length > 0
    const isSelected = selectedConcepts.includes(concept.concept_id)

    return (
      <div className="w-full">
        <div 
          className={cn(
            "flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-gray-50 cursor-pointer transition-colors",
            isSelected && "bg-blue-50",
            level > 0 && "ml-4"
          )}
          onClick={() => toggleConcept(concept.concept_id)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleConceptExpansion(concept.concept_id)
              }}
              className="p-0.5 hover:bg-gray-200 rounded"
            >
              {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRightIcon className="h-3 w-3" />}
            </button>
          )}
          {!hasChildren && <div className="w-4" />}
          
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => toggleConcept(concept.concept_id)}
            onClick={(e) => e.stopPropagation()}
            className="h-3 w-3"
          />
          
          <TagBadge 
            variant={isSelected ? "default" : "system"}
            className="flex-1 justify-between cursor-pointer"
            style={{
              backgroundColor: isSelected ? '#93C5FD' : '#DBEAFE',
              color: '#1E40AF'
            }}
          >
            <span className="flex items-center gap-1">
              <span>{conceptService.getConceptIcon(concept)}</span>
              <span>{concept.display_name}</span>
            </span>
            <Badge variant="secondary" className="ml-auto text-xs py-0 px-1">
              {concept.count}
            </Badge>
          </TagBadge>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="ml-2">
            {concept.children!.map((child, childIndex) => (
              <React.Fragment key={child.concept_id || `child-${level}-${childIndex}`}>
                {renderHierarchicalConcept(child, level + 1)}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>
    )
  }

  const displayedConcepts = showHierarchy ? hierarchyFacets : facets.concepts

  const totalPages = Math.ceil(totalArticles / pageSize)

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Articles</h1>
        <p className="text-gray-600">Browse and analyze web articles with advanced filtering</p>
      </div>

      {/* Search Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-3">
            <form onSubmit={handleSearch} className="flex-1 flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
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
                onClick={() => setShowEnhancedImportModal(true)}
                title="Enhanced import with authentication"
              >
                <Plus className="h-4 w-4 mr-2" />
                Enhanced Import
              </Button>
              <Button
                variant="outline"
                onClick={handleRefreshArticles}
                title="Refresh articles"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Main Content Grid - 12 column layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Authors Filter - Left */}
        <div className="lg:col-span-2">
          <Card className="sticky top-4">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Authors
                </CardTitle>
                <div className="flex gap-1">
                  {selectedAuthors.length > 0 && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setSelectedAuthors([])}
                      className="h-7 px-2 text-xs"
                    >
                      <X className="h-3 w-3 mr-1" />
                      Clear
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setShowAuthorManagementModal(true)}
                    className="h-7 px-2 text-xs"
                    title="Manage Authors"
                  >
                    ⚙️
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[600px] px-4 pb-4">
                <div className="space-y-1">
                  {facets.authors.map((author, index) => (
                    <div
                      key={`${author.name}-${index}`}
                      className={cn(
                        "flex items-center justify-between py-2 px-2 rounded-md hover:bg-gray-50 cursor-pointer transition-colors",
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
                        <span className="text-sm font-medium">{author.name}</span>
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
        </div>

        {/* Concepts Filter - Right */}
        <div className="lg:col-span-3 order-last lg:order-last">
          <Card className="sticky top-4">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Tag className="h-4 w-4" />
                  Concepts
                </CardTitle>
                <div className="flex gap-1">
                  {selectedConcepts.length > 0 && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setSelectedConcepts([])}
                      className="h-7 px-2 text-xs"
                    >
                      <X className="h-3 w-3 mr-1" />
                      Clear
                    </Button>
                  )}
                  <Button
                    size="sm"
                    variant={showHierarchy ? "default" : "outline"}
                    onClick={() => setShowHierarchy(!showHierarchy)}
                    className="h-7 px-2"
                    title={showHierarchy ? "Show flat list" : "Show hierarchy"}
                  >
                    {showHierarchy ? <GitBranch className="h-3 w-3" /> : <Layers className="h-3 w-3" />}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[1200px] px-4 pb-4">
                {showHierarchy ? (
                  <div className="space-y-1">
                    {hierarchyFacets && hierarchyFacets.map((concept, index) => (
                      <React.Fragment key={concept.concept_id || `hierarchy-${index}`}>
                        {renderHierarchicalConcept(concept)}
                      </React.Fragment>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-1">
                    {displayedConcepts.map(concept => (
                      <div
                        key={concept.concept_id}
                        className={cn(
                          "flex items-center justify-between py-1 px-2 rounded-md hover:bg-gray-50 cursor-pointer transition-colors",
                          selectedConcepts.includes(concept.concept_id) && "bg-blue-50"
                        )}
                        onClick={() => toggleConcept(concept.concept_id)}
                      >
                        <div className="flex items-center gap-2">
                          <Checkbox
                            checked={selectedConcepts.includes(concept.concept_id)}
                            onCheckedChange={() => toggleConcept(concept.concept_id)}
                            onClick={(e) => e.stopPropagation()}
                            className="h-3 w-3"
                          />
                          <div
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-xs font-medium"
                            style={{
                              backgroundColor: selectedConcepts.includes(concept.concept_id) ? '#93C5FD' : '#DBEAFE',
                              color: '#1E40AF'
                            }}
                          >
                            <span className="text-xs">{conceptService.getConceptIcon(concept)}</span>
                            <span>{concept.display_name}</span>
                          </div>
                        </div>
                        <Badge variant="secondary" className="text-xs py-0 px-1">
                          {concept.count}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

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
              
              {/* Pagination */}
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
                <span className="text-sm text-gray-600">
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
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : articles.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12 text-gray-500">
                <FileText className="h-12 w-12 mb-4 text-gray-300" />
                <p className="text-lg font-medium">No articles found</p>
                <p className="text-sm mt-2">Try adjusting your filters or search terms</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {articles.map(article => (
                <Card 
                  key={article.id} 
                  className="hover:shadow-lg transition-all duration-200"
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <CardTitle className="text-lg mb-2 line-clamp-2">
                          {article.title}
                        </CardTitle>
                        <div className="flex items-center gap-4 text-sm text-gray-500">
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
                            openArticle(article)
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
                            handleRegeneratePreview(article.id.toString())
                          }}
                          disabled={regeneratingPreviews.has(article.id)}
                          title="Regenerate Preview"
                          className="text-blue-500 hover:text-blue-700 hover:bg-blue-50"
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
                            handleDeleteArticle(article.id.toString(), article.title)
                          }}
                          title="Delete Article"
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
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
                      <div className="prose prose-sm max-w-none line-clamp-3 text-gray-600">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {article.preview}
                        </ReactMarkdown>
                      </div>
                    )}
                    
                    {article.summary && (
                      <div className="mt-3">
                        <div 
                          className="flex items-center gap-2 mb-2 cursor-pointer hover:opacity-80 transition-opacity select-none"
                          onClick={() => {
                            setExpandedSummaries(prev => {
                              const newSet = new Set(prev)
                              if (newSet.has(article.id)) {
                                newSet.delete(article.id)
                              } else {
                                newSet.add(article.id)
                              }
                              return newSet
                            })
                          }}
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
                                        `${API_BASE_URL}/api/articles/${article.id}/concepts?text=${encodeURIComponent(selectedTextForConcept.text)}`
                                      )
                                      if (response.data.success) {
                                        // Refresh the article to show the new concept
                                        await fetchArticles()
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
                            <div className="prose prose-sm max-w-none text-gray-700">
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
                    <div className="flex flex-wrap gap-2">
                      {article.concepts.map(concept => (
                        <Badge
                          key={concept.concept_id}
                          variant="outline"
                          className="cursor-pointer"
                          style={{
                            backgroundColor: '#DBEAFE',
                            color: '#1E40AF'
                          }}
                          onClick={(e) => {
                            e.stopPropagation()
                            if (!selectedConcepts.includes(concept.concept_id)) {
                              toggleConcept(concept.concept_id)
                            }
                          }}
                        >
                          <span className="mr-1">{conceptService.getConceptIcon(concept)}</span>
                          {concept.display_name}
                        </Badge>
                      ))}
                    </div>
                  </CardFooter>
                </Card>
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
              <div className="bg-white rounded-lg p-8 flex items-center">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="ml-2 text-gray-600">Loading Article Viewer...</span>
              </div>
            </div>
          }>
            <ArticleViewerModern
              articleId={selectedArticle?.id}
              onClose={() => {
                setShowViewer(false)
                setSelectedArticle(null)
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
      
      {showEnhancedImportModal && (
        <ArticleImportEnhancedModal
          isOpen={showEnhancedImportModal}
          onClose={() => setShowEnhancedImportModal(false)}
          onImportSuccess={() => {
            setShowEnhancedImportModal(false)
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