import React, { useState, useEffect } from 'react'
import http from '@/services/http'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
  Search,
  User,
  Users,
  Globe,
  FileText,
  Calendar,
  Loader2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  GitMerge,
  BarChart3,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Eye
} from 'lucide-react'


interface Author {
  id: string
  name: string
  canonical_name?: string
  subdomain?: string
  email?: string
  article_count: number
  last_article_date?: string
  created_at?: string
  updated_at?: string
}

interface AuthorListResponse {
  authors: Author[]
  total: number
  page: number
  page_size: number
  pages: number
}

interface AuthorDetails {
  author: Author
  articles: {
    id: string
    title: string
    url?: string
    published_at?: string
    word_count: number
    preview: string
  }[]
  statistics: {
    total_articles: number
    total_words: number
    avg_words_per_article: number
    first_article_date?: string
    last_article_date?: string
  }
}

type SortField = 'name' | 'article_count' | 'last_article_date' | 'created_at'
type SortOrder = 'asc' | 'desc'

const AuthorManagementModern: React.FC = () => {
  const [authors, setAuthors] = useState<Author[]>([])
  const [totalAuthors, setTotalAuthors] = useState(0)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [pageSize, _setPageSize] = useState(50)
  const [isLoading, setIsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortField, setSortField] = useState<SortField>('article_count')
  const [sortOrder, setSortOrder] = useState<SortOrder>('desc')

  // Modal states
  const [selectedAuthor, setSelectedAuthor] = useState<Author | null>(null)
  const [authorDetails, setAuthorDetails] = useState<AuthorDetails | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isLoadingDetails, setIsLoadingDetails] = useState(false)

  // Fetch authors
  const fetchAuthors = async () => {
    setIsLoading(true)
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString(),
        sort_by: sortField,
        sort_order: sortOrder
      })

      if (searchQuery.trim()) {
        params.append('search', searchQuery.trim())
      }

      const response = await http.get<AuthorListResponse>(
        `/api/authors/?${params.toString()}`
      )

      setAuthors(response.data.authors)
      setTotalAuthors(response.data.total)
      setTotalPages(response.data.pages)
    } catch (error) {
      console.error('Error fetching authors:', error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    fetchAuthors()
  }, [currentPage, pageSize, sortField, sortOrder])

  // Handle search with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (currentPage !== 1) {
        setCurrentPage(1)
      } else {
        fetchAuthors()
      }
    }, 500)

    return () => clearTimeout(timer)
  }, [searchQuery])

  // Fetch author details
  const viewAuthorDetails = async (author: Author) => {
    setSelectedAuthor(author)
    setIsDetailModalOpen(true)
    setIsLoadingDetails(true)

    try {
      const response = await http.get<AuthorDetails>(
        `/api/authors/${author.id}`
      )
      setAuthorDetails(response.data)
    } catch (error) {
      console.error('Error fetching author details:', error)
    } finally {
      setIsLoadingDetails(false)
    }
  }

  // Toggle sort order
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortOrder('desc')
    }
  }

  // Format date
  const formatDate = (dateString?: string) => {
    if (!dateString) return 'Never'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  // Get sort icon
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 ml-1 opacity-30" />
    }
    return sortOrder === 'asc'
      ? <ArrowUp className="w-3 h-3 ml-1" />
      : <ArrowDown className="w-3 h-3 ml-1" />
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Users className="w-8 h-8 text-primary" />
            Author Management
          </h1>
          <p className="text-muted-foreground mt-1">
            Manage and organize article authors
          </p>
        </div>

        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchAuthors}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          <Button variant="default">
            <GitMerge className="w-4 h-4 mr-2" />
            Merge Authors
          </Button>
          <Button variant="default">
            <BarChart3 className="w-4 h-4 mr-2" />
            Analytics
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Authors</CardDescription>
            <CardTitle className="text-4xl">{totalAuthors}</CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Active Authors</CardDescription>
            <CardTitle className="text-4xl">
              {authors.filter(a => a.article_count > 0).length}
            </CardTitle>
          </CardHeader>
        </Card>
        <Card>
          <CardHeader className="pb-3">
            <CardDescription>Total Articles</CardDescription>
            <CardTitle className="text-4xl">
              {authors.reduce((sum, a) => sum + a.article_count, 0)}
            </CardTitle>
          </CardHeader>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input
                type="text"
                placeholder="Search authors by name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Author Table */}
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : authors.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Users className="w-12 h-12 mx-auto mb-4 opacity-20" />
              <p>No authors found</p>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Table Header */}
              <div className="grid grid-cols-12 gap-4 px-4 py-2 bg-muted/50 rounded-lg font-medium text-sm">
                <button
                  onClick={() => handleSort('name')}
                  className="col-span-4 flex items-center justify-start hover:text-primary transition-colors"
                >
                  Name
                  {getSortIcon('name')}
                </button>
                <div className="col-span-2 flex items-center">
                  Subdomain
                </div>
                <button
                  onClick={() => handleSort('article_count')}
                  className="col-span-2 flex items-center justify-center hover:text-primary transition-colors"
                >
                  Articles
                  {getSortIcon('article_count')}
                </button>
                <button
                  onClick={() => handleSort('last_article_date')}
                  className="col-span-3 flex items-center justify-start hover:text-primary transition-colors"
                >
                  Last Published
                  {getSortIcon('last_article_date')}
                </button>
                <div className="col-span-1 flex items-center justify-end">
                  Actions
                </div>
              </div>

              {/* Table Rows */}
              <ScrollArea className="h-[500px]">
                <div className="space-y-2">
                  {authors.map((author) => (
                    <div
                      key={author.id}
                      className="grid grid-cols-12 gap-4 px-4 py-3 border rounded-lg hover:bg-muted/50 transition-colors"
                    >
                      {/* Name */}
                      <div className="col-span-4 flex items-center gap-2">
                        <User className="w-4 h-4 text-muted-foreground flex-shrink-0" />
                        <div className="min-w-0 flex-1">
                          <p className="font-medium truncate">{author.name}</p>
                          {author.canonical_name && author.canonical_name !== author.name && (
                            <p className="text-xs text-muted-foreground truncate">
                              ({author.canonical_name})
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Subdomain */}
                      <div className="col-span-2 flex items-center text-sm">
                        {author.subdomain ? (
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <Globe className="w-3 h-3" />
                            <span className="truncate">{author.subdomain}</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </div>

                      {/* Article Count */}
                      <div className="col-span-2 flex items-center justify-center">
                        <Badge variant={author.article_count > 0 ? "default" : "secondary"}>
                          <FileText className="w-3 h-3 mr-1" />
                          {author.article_count}
                        </Badge>
                      </div>

                      {/* Last Published */}
                      <div className="col-span-3 flex items-center text-sm text-muted-foreground">
                        <Calendar className="w-3 h-3 mr-1" />
                        {formatDate(author.last_article_date)}
                      </div>

                      {/* Actions */}
                      <div className="col-span-1 flex items-center justify-end gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => viewAuthorDetails(author)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}
        </CardContent>

        {/* Pagination */}
        {!isLoading && authors.length > 0 && (
          <div className="px-6 py-4 border-t">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Showing {((currentPage - 1) * pageSize) + 1} to{' '}
                {Math.min(currentPage * pageSize, totalAuthors)} of {totalAuthors} authors
              </div>

              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>

                <span className="text-sm">
                  Page {currentPage} of {totalPages}
                </span>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* Author Detail Modal (placeholder) */}
      {isDetailModalOpen && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-3xl max-h-[90vh] overflow-hidden">
            <CardHeader className="border-b">
              <div className="flex items-start justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <User className="w-5 h-5" />
                    {selectedAuthor?.name}
                  </CardTitle>
                  {selectedAuthor?.canonical_name && (
                    <CardDescription>
                      Canonical: {selectedAuthor.canonical_name}
                    </CardDescription>
                  )}
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setIsDetailModalOpen(false)
                    setSelectedAuthor(null)
                    setAuthorDetails(null)
                  }}
                >
                  ✕
                </Button>
              </div>
            </CardHeader>

            <ScrollArea className="max-h-[calc(90vh-150px)]">
              <CardContent className="pt-6 space-y-6">
                {isLoadingDetails ? (
                  <div className="flex items-center justify-center py-12">
                    <Loader2 className="w-8 h-8 animate-spin text-primary" />
                  </div>
                ) : authorDetails ? (
                  <>
                    {/* Author Info */}
                    <div className="grid grid-cols-2 gap-4">
                      {authorDetails.author.subdomain && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Subdomain</p>
                          <p className="text-sm">{authorDetails.author.subdomain}</p>
                        </div>
                      )}
                      {authorDetails.author.email && (
                        <div>
                          <p className="text-sm font-medium text-muted-foreground">Email</p>
                          <p className="text-sm">{authorDetails.author.email}</p>
                        </div>
                      )}
                    </div>

                    <Separator />

                    {/* Statistics */}
                    <div>
                      <h3 className="font-semibold mb-3">Statistics</h3>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-3 border rounded-lg">
                          <p className="text-sm text-muted-foreground">Total Articles</p>
                          <p className="text-2xl font-bold">{authorDetails.statistics.total_articles}</p>
                        </div>
                        <div className="p-3 border rounded-lg">
                          <p className="text-sm text-muted-foreground">Total Words</p>
                          <p className="text-2xl font-bold">{authorDetails.statistics.total_words.toLocaleString()}</p>
                        </div>
                        <div className="p-3 border rounded-lg">
                          <p className="text-sm text-muted-foreground">Avg Words/Article</p>
                          <p className="text-2xl font-bold">{authorDetails.statistics.avg_words_per_article.toLocaleString()}</p>
                        </div>
                        <div className="p-3 border rounded-lg">
                          <p className="text-sm text-muted-foreground">First Article</p>
                          <p className="text-sm font-medium">{formatDate(authorDetails.statistics.first_article_date)}</p>
                        </div>
                      </div>
                    </div>

                    <Separator />

                    {/* Recent Articles */}
                    <div>
                      <h3 className="font-semibold mb-3">Recent Articles ({authorDetails.articles.length})</h3>
                      <div className="space-y-2">
                        {authorDetails.articles.map((article) => (
                          <div key={article.id} className="p-3 border rounded-lg hover:bg-muted/50 transition-colors">
                            <div className="flex items-start justify-between gap-2">
                              <div className="flex-1 min-w-0">
                                <p className="font-medium line-clamp-1">{article.title}</p>
                                <p className="text-xs text-muted-foreground mt-1">
                                  {formatDate(article.published_at)} • {article.word_count.toLocaleString()} words
                                </p>
                              </div>
                              {article.url && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => window.open(article.url, '_blank')}
                                >
                                  <Globe className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    Failed to load author details
                  </div>
                )}
              </CardContent>
            </ScrollArea>
          </Card>
        </div>
      )}
    </div>
  )
}

export default AuthorManagementModern
