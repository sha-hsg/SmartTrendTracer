import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import ArticleViewerModern from './ArticleViewerModern'
import ArticleTagSuggestionModalModern from './ArticleTagSuggestionModalModern'
import { 
  Search, 
  FileText, 
  User, 
  Hash, 
  Calendar,
  Loader2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Tag,
  Clock,
  BookOpen,
  Sparkles,
  Eye,
  EyeOff,
  MessageSquare,
  Bookmark,
  TrendingUp,
  Filter,
  X,
  Plus
} from 'lucide-react'
import { cn } from "@/lib/utils"

interface AuthorFacet {
  id: number
  name: string
  count: number
}

interface TagFacet {
  tag: string
  count: number
}

interface Article {
  id: number
  title: string
  subtitle: string | null
  author?: {
    id: number
    name: string
    subdomain: string
  }
  published_at: string | null
  word_count: number
  reading_time_minutes: number
  preview: string
  summary?: string | null
  has_summary?: boolean
  tags: any[]  // Can be string[] or {tag: string, type: string}[]
  snippet_count: number
}

interface FacetedSearchResponse {
  articles: Article[]
  facets: {
    authors: AuthorFacet[]
    tags: TagFacet[]
  }
  total: number
  page: number
  page_size: number
}

export default function FacetedSubstackDashboardModern() {
  const [articles, setArticles] = useState<Article[]>([])
  const [facets, setFacets] = useState<{ authors: AuthorFacet[]; tags: TagFacet[] }>({
    authors: [],
    tags: []
  })
  const [selectedAuthors, setSelectedAuthors] = useState<number[]>([])
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [hasSummary, setHasSummary] = useState<boolean | null>(null)
  const [hasSnippets, setHasSnippets] = useState<boolean | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalArticles, setTotalArticles] = useState(0)
  const [loading, setLoading] = useState(false)
  const [selectedArticleId, setSelectedArticleId] = useState<number | null>(null)
  const [selectedArticleForTags, setSelectedArticleForTags] = useState<Article | null>(null)
  const [showAllTags, setShowAllTags] = useState(false)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [addingTagForArticle, setAddingTagForArticle] = useState<number | null>(null)
  const [newTag, setNewTag] = useState('')

  const pageSize = 20
  const totalPages = Math.ceil(totalArticles / pageSize)

  useEffect(() => {
    fetchArticles()
  }, [selectedAuthors, selectedTags, searchTerm, hasSummary, hasSnippets, currentPage])

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
      
      selectedAuthors.forEach(authorId => params.append('author_ids', authorId.toString()))
      selectedTags.forEach(tag => params.append('tags', tag))
      
      const response = await axios.get<FacetedSearchResponse>(
        `http://localhost:8000/api/v2/substack/articles/faceted-search?${params.toString()}`
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

  const toggleAuthor = (authorId: number) => {
    if (!authorId) return // Prevent undefined IDs
    setSelectedAuthors(prev => {
      if (prev.includes(authorId)) {
        return prev.filter(id => id !== authorId)
      }
      return [...prev, authorId]
    })
    setCurrentPage(1)
  }

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => {
      if (prev.includes(tag)) {
        return prev.filter(t => t !== tag)
      }
      return [...prev, tag]
    })
    setCurrentPage(1)
  }

  const clearFilters = () => {
    setSelectedAuthors([])
    setSelectedTags([])
    setSearchTerm('')
    setHasSummary(null)
    setHasSnippets(null)
    setCurrentPage(1)
  }

  const handleAddTag = async (articleId: number, tag: string) => {
    try {
      await axios.post(`http://localhost:8000/api/v2/substack/articles/${articleId}/tags`, {
        tag: tag,
        tag_type: 'manual'
      })
      fetchArticles() // Refresh to show new tag
      setNewTag('')
      setAddingTagForArticle(null)
    } catch (error) {
      console.error('Error adding tag:', error)
    }
  }

  const handleRemoveTag = async (articleId: number, tag: string) => {
    try {
      await axios.delete(`http://localhost:8000/api/v2/substack/articles/${articleId}/tags/${tag}`)
      fetchArticles() // Refresh to update tags
    } catch (error) {
      console.error('Error removing tag:', error)
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

  const renderArticleCard = (article: Article) => (
    <Card 
      className="h-full flex flex-col hover:shadow-lg transition-all duration-200 cursor-pointer"
      onClick={() => setSelectedArticleId(article.id)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-lg line-clamp-2">
            {article.title}
          </CardTitle>
          <div className="flex gap-1 shrink-0">
            {article.has_summary && (
              <Badge variant="outline" className="border-purple-200 bg-purple-50" title="Has AI Summary">
                <Sparkles className="h-3 w-3 text-purple-600" />
              </Badge>
            )}
            {article.snippet_count > 0 && (
              <Badge variant="outline" className="border-blue-200 bg-blue-50" title={`${article.snippet_count} snippet${article.snippet_count !== 1 ? 's' : ''}`}>
                <MessageSquare className="h-3 w-3 text-blue-600 mr-1" />
                {article.snippet_count}
              </Badge>
            )}
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
        
        {article.has_summary && article.summary ? (
          <p className="text-sm text-gray-600 line-clamp-4">
            {article.summary}
          </p>
        ) : (
          <p className="text-sm text-gray-600 line-clamp-5">
            {article.preview}
          </p>
        )}
      </CardContent>
      
      <CardFooter className="pt-0">
        <div className="w-full space-y-2">
          {/* Tags Display */}
          {article.tags && article.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {article.tags.map((tag, idx) => {
                const tagText = typeof tag === 'string' ? tag : tag.tag
                const tagType = typeof tag === 'string' ? 'manual' : tag.type
                return (
                  <TagBadge 
                    key={`${article.id}-tag-${idx}`} 
                    variant={tagType === 'ai' || tagType === 'llm' ? 'ai' : 'default'} 
                    size="sm"
                    removable
                    onRemove={() => handleRemoveTag(article.id, tagText)}
                  >
                    {tagText}
                  </TagBadge>
                )
              })}
            </div>
          )}
          
          {/* Tag Management UI */}
          <div className="flex gap-2">
            {addingTagForArticle === article.id ? (
              <>
                <Input
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && newTag.trim()) {
                      e.stopPropagation()
                      handleAddTag(article.id, newTag.trim())
                    }
                  }}
                  placeholder="Enter tag name..."
                  className="flex-1 h-8"
                  onClick={(e) => e.stopPropagation()}
                  autoFocus
                />
                <Button 
                  onClick={(e) => {
                    e.stopPropagation()
                    if (newTag.trim()) {
                      handleAddTag(article.id, newTag.trim())
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
                  Suggest Tags
                </Button>
              </>
            )}
          </div>
        </div>
      </CardFooter>
    </Card>
  )

  const displayedTags = showAllTags ? facets.tags : facets.tags.slice(0, 20)

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Newsletter Articles</h1>
        <p className="text-gray-600">Browse and analyze Substack newsletters with AI insights</p>
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
              <div className="flex items-center gap-2">
                <Checkbox
                  id="has-summary"
                  checked={hasSummary === true}
                  onCheckedChange={(checked) => {
                    setHasSummary(checked === true ? true : null)
                    setCurrentPage(1)
                  }}
                />
                <label htmlFor="has-summary" className="text-sm cursor-pointer">
                  Has Summary
                </label>
              </div>
              
              <div className="flex items-center gap-2">
                <Checkbox
                  id="has-snippets"
                  checked={hasSnippets === true}
                  onCheckedChange={(checked) => {
                    setHasSnippets(checked === true ? true : null)
                    setCurrentPage(1)
                  }}
                />
                <label htmlFor="has-snippets" className="text-sm cursor-pointer">
                  Has Snippets
                </label>
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button onClick={fetchArticles} variant="outline" disabled={loading}>
                <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
                Refresh
              </Button>
              {(selectedAuthors.length > 0 || selectedTags.length > 0 || searchTerm) && (
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
                  {facets.authors.filter(author => author.id).map(author => (
                    <div
                      key={`author-${author.id}`}
                      className={cn(
                        "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 cursor-pointer transition-colors mb-1",
                        selectedAuthors.includes(author.id) && "bg-blue-50"
                      )}
                      onClick={() => toggleAuthor(author.id)}
                    >
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={selectedAuthors.includes(author.id)}
                          onCheckedChange={() => toggleAuthor(author.id)}
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

          {/* Tags Filter */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Hash className="h-4 w-4" />
                Tags
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[350px]">
                <div className="px-4 pb-4 space-y-1">
                  {displayedTags.map(tag => (
                    <div
                      key={`tag-${tag.tag}`}
                      className={cn(
                        "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 cursor-pointer transition-colors",
                        selectedTags.includes(tag.tag) && "bg-blue-50"
                      )}
                      onClick={() => toggleTag(tag.tag)}
                    >
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={selectedTags.includes(tag.tag)}
                          onCheckedChange={() => toggleTag(tag.tag)}
                          onClick={(e) => e.stopPropagation()}
                        />
                        <TagBadge variant="default" size="sm">
                          {tag.tag}
                        </TagBadge>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {tag.count}
                      </Badge>
                    </div>
                  ))}
                </div>
                {facets.tags.length > 20 && (
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
                        Show All ({facets.tags.length})
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
              {selectedTags.length > 0 && (
                <Badge variant="secondary" className="py-1.5 px-3">
                  {selectedTags.length} tag{selectedTags.length !== 1 ? 's' : ''} selected
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

      {/* Article Viewer Modal */}
      {selectedArticleId && (
        <ArticleViewerModern
          articleId={selectedArticleId}
          onClose={() => {
            setSelectedArticleId(null)
            fetchArticles() // Refresh to show updated tags
          }}
        />
      )}

      {/* Tag Suggestion Modal */}
      {selectedArticleForTags && (
        <ArticleTagSuggestionModalModern
          article={selectedArticleForTags}
          isOpen={!!selectedArticleForTags}
          onClose={() => setSelectedArticleForTags(null)}
          onTagsUpdated={fetchArticles}
        />
      )}
    </div>
  )
}