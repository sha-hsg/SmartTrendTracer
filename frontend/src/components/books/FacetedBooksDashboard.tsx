import React, { useState, useEffect, useCallback, Suspense } from 'react'
import axios from 'axios'
import {
  BookOpen,
  Filter,
  Plus,
  Users,
  Loader2,
  XCircle,
  Building2,
  Cpu,
  Library,
  RefreshCw
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn } from '@/lib/utils'

import BookUploadModal from '../BookUploadModal'
import BookCard from './BookCard'
import type { Book } from './BookCard'
import BookFilterPanel from './BookFilterPanel'
import type { BooksStats } from './BookFilterPanel'

const BookViewerOptimized = React.lazy(() => import('../book-viewer'))

interface BooksResponse {
  books: Book[]
  pagination: {
    page: number
    page_size: number
    total: number
    total_pages: number
    has_next: boolean
    has_prev: boolean
  }
}

const FacetedBooksDashboard: React.FC = () => {
  const [books, setBooks] = useState<Book[]>([])
  const [stats, setStats] = useState<BooksStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filtering and pagination
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedAuthors, setSelectedAuthors] = useState<string[]>([])
  const [selectedPublishers, setSelectedPublishers] = useState<string[]>([])
  const [selectedGenres, setSelectedGenres] = useState<string[]>([])
  const [selectedSubjectAreas, setSelectedSubjectAreas] = useState<string[]>([])
  const [selectedLanguages, setSelectedLanguages] = useState<string[]>([])
  const [selectedDifficulties, setSelectedDifficulties] = useState<string[]>([])
  const [selectedProcessors, setSelectedProcessors] = useState<string[]>([])
  const [selectedFileTypes, setSelectedFileTypes] = useState<string[]>([])
  const [selectedYears, setSelectedYears] = useState<number[]>([])
  const [selectedConceptIds, setSelectedConceptIds] = useState<string[]>([])
  const [specialFilter, setSpecialFilter] = useState<string>('all')

  const [currentPage, setCurrentPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [pageSize, _setPageSize] = useState(20)

  // UI state
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showFilters, setShowFilters] = useState(true)
  const [_sortBy, _setSortBy] = useState('uploaded_at')
  const [_sortOrder, _setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Progressive disclosure state for filter sections
  const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({
    concepts: false,
    authors: true,
    publishers: true,
    genres: true,
    subjects: true,
    languages: true,
    difficulty: false,
    fileTypes: false,
    processors: true,
    years: true
  })

  const toggleSection = (section: string) => {
    setCollapsedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  // Load books data
  const loadBooks = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString()
      })

      if (searchTerm) params.append('search', searchTerm)
      if (specialFilter && specialFilter !== 'all') params.append('special_filter', specialFilter)

      // Add array filters
      selectedAuthors.forEach(author => params.append('authors', author))
      selectedPublishers.forEach(pub => params.append('publishers', pub))
      selectedGenres.forEach(genre => params.append('genres', genre))
      selectedSubjectAreas.forEach(area => params.append('subject_areas', area))
      selectedLanguages.forEach(lang => params.append('languages', lang))
      selectedDifficulties.forEach(diff => params.append('difficulty_levels', diff))
      selectedProcessors.forEach(proc => params.append('processors', proc))
      selectedFileTypes.forEach(type => params.append('file_types', type))
      selectedYears.forEach(year => params.append('years', year.toString()))
      selectedConceptIds.forEach(id => params.append('concept_ids', id))

      const response = await axios.get<BooksResponse>(`/api/books/?${params}`)
      setBooks(response.data.books)
      setCurrentPage(response.data.pagination.page)
      setTotalPages(response.data.pagination.total_pages)

    } catch (err) {
      console.error('Error loading books:', err)
      setError('Failed to load books. Please try again.')
    } finally {
      setLoading(false)
    }
  }, [
    currentPage, pageSize, searchTerm, specialFilter,
    selectedAuthors, selectedPublishers, selectedGenres, selectedSubjectAreas,
    selectedLanguages, selectedDifficulties, selectedProcessors, selectedFileTypes,
    selectedYears, selectedConceptIds
  ])

  // Load stats and facets with current filters
  const loadStats = useCallback(async () => {
    try {
      const params = new URLSearchParams()

      if (searchTerm) params.append('search', searchTerm)
      selectedAuthors.forEach(author => params.append('authors', author))
      selectedPublishers.forEach(pub => params.append('publishers', pub))
      selectedGenres.forEach(genre => params.append('genres', genre))
      selectedSubjectAreas.forEach(area => params.append('subject_areas', area))
      selectedLanguages.forEach(lang => params.append('languages', lang))
      selectedDifficulties.forEach(diff => params.append('difficulty_levels', diff))
      selectedProcessors.forEach(proc => params.append('processors', proc))
      selectedFileTypes.forEach(type => params.append('file_types', type))
      selectedYears.forEach(year => params.append('years', year.toString()))
      selectedConceptIds.forEach(id => params.append('concept_ids', id))
      if (specialFilter) params.append('special_filter', specialFilter)

      const response = await axios.get<BooksStats>(`/api/books/facets?${params}`)
      setStats(response.data)
    } catch (err) {
      console.error('Error loading book stats:', err)
    }
  }, [
    searchTerm, selectedAuthors, selectedPublishers, selectedGenres,
    selectedSubjectAreas, selectedLanguages, selectedDifficulties, selectedProcessors,
    selectedFileTypes, selectedYears, selectedConceptIds, specialFilter
  ])

  useEffect(() => {
    loadBooks()
  }, [loadBooks])

  useEffect(() => {
    loadStats()
  }, [loadStats])

  const clearAllFilters = () => {
    setSearchTerm('')
    setSelectedAuthors([])
    setSelectedPublishers([])
    setSelectedGenres([])
    setSelectedSubjectAreas([])
    setSelectedLanguages([])
    setSelectedDifficulties([])
    setSelectedProcessors([])
    setSelectedFileTypes([])
    setSelectedYears([])
    setSelectedConceptIds([])
    setSpecialFilter('all')
    setCurrentPage(1)
  }

  const handleBookUpload = () => {
    setShowUploadModal(false)
    loadBooks()
    loadStats()
  }

  if (selectedBook) {
    return (
      <Suspense fallback={
        <div className="flex items-center justify-center h-screen">
          <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          <span className="ml-2 text-gray-600 dark:text-gray-400">Loading Book Viewer...</span>
        </div>
      }>
        <BookViewerOptimized
          book={selectedBook}
          onBack={() => setSelectedBook(null)}
          onBookUpdate={(updated) => {
            setSelectedBook(updated)
            setBooks(prev => prev.map(book => (book._id === updated._id ? updated : book)))
          }}
        />
      </Suspense>
    )
  }

  return (
    <>
      {/* Skip Navigation Link */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-blue-600 text-white px-4 py-2 rounded-md z-50"
      >
        Skip to main content
      </a>

      <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
        {/* Mobile Overlay Background */}
        {showFilters && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
            onClick={() => setShowFilters(false)}
            aria-hidden="true"
          />
        )}

        {/* Left Sidebar - Filters */}
        <BookFilterPanel
          stats={stats}
          showFilters={showFilters}
          setShowFilters={setShowFilters}
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          specialFilter={specialFilter}
          setSpecialFilter={setSpecialFilter}
          selectedFileTypes={selectedFileTypes}
          setSelectedFileTypes={setSelectedFileTypes}
          selectedConceptIds={selectedConceptIds}
          setSelectedConceptIds={setSelectedConceptIds}
          selectedAuthors={selectedAuthors}
          setSelectedAuthors={setSelectedAuthors}
          selectedPublishers={selectedPublishers}
          setSelectedPublishers={setSelectedPublishers}
          selectedGenres={selectedGenres}
          setSelectedGenres={setSelectedGenres}
          selectedDifficulties={selectedDifficulties}
          setSelectedDifficulties={setSelectedDifficulties}
          selectedYears={selectedYears}
          setSelectedYears={setSelectedYears}
          collapsedSections={collapsedSections}
          toggleSection={toggleSection}
          clearAllFilters={clearAllFilters}
          onUploadClick={() => setShowUploadModal(true)}
        />

        {/* Main Content */}
        <main
          id="main-content"
          className={`
            flex-1 flex flex-col overflow-hidden transition-all duration-300
            ${showFilters ? 'lg:ml-0' : 'ml-0'}
          `}
          role="main"
          aria-label="Book library content"
        >
          {/* Header */}
          <header className="bg-white dark:bg-gray-950 shadow-sm border-b p-4" role="banner">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center space-x-2 md:space-x-4">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowFilters(!showFilters)}
                  className="lg:hidden"
                >
                  <Filter className="w-4 h-4 mr-1" />
                  <span className="sr-only sm:not-sr-only">Filters</span>
                </Button>

                <h1 className="text-lg md:text-2xl font-bold flex items-center">
                  <BookOpen className="w-5 h-5 md:w-6 md:h-6 mr-1 md:mr-2 text-blue-600" />
                  <span className="hidden sm:inline">Book Library</span>
                  <span className="sm:hidden">Books</span>
                </h1>
                {stats && (
                  <Badge variant="outline" className="bg-blue-50 dark:bg-blue-950 text-xs md:text-sm">
                    {stats.total_books}
                  </Badge>
                )}
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  onClick={() => setShowUploadModal(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-sm md:text-base"
                  size="sm"
                >
                  <Plus className="w-4 h-4 mr-1 md:mr-2" />
                  <span className="hidden sm:inline">Upload Book</span>
                  <span className="sm:hidden">Upload</span>
                </Button>
                <Button
                  onClick={() => loadBooks()}
                  variant="outline"
                  disabled={loading}
                  size="sm"
                >
                  <RefreshCw className={cn("w-4 h-4 mr-1 md:mr-2", loading && "animate-spin")} />
                  <span className="hidden sm:inline">Refresh</span>
                </Button>
              </div>
            </div>
          </header>

          {/* Stats Cards */}
          {stats && (
            <div className="bg-white dark:bg-gray-950 border-b p-2 md:p-4">
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 md:gap-4">
                <Card className="p-2 md:p-4">
                  <div className="flex items-center">
                    <BookOpen className="w-6 h-6 md:w-8 md:h-8 text-blue-600 mr-2 md:mr-3" />
                    <div>
                      <p className="text-lg md:text-2xl font-bold">{stats.total_books}</p>
                      <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">Total Books</p>
                    </div>
                  </div>
                </Card>
                <Card className="p-2 md:p-4">
                  <div className="flex items-center">
                    <Users className="w-6 h-6 md:w-8 md:h-8 text-green-600 mr-2 md:mr-3" />
                    <div>
                      <p className="text-lg md:text-2xl font-bold">{stats.facets.authors.length}</p>
                      <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">Authors</p>
                    </div>
                  </div>
                </Card>
                <Card className="p-2 md:p-4">
                  <div className="flex items-center">
                    <Building2 className="w-6 h-6 md:w-8 md:h-8 text-purple-600 mr-2 md:mr-3" />
                    <div>
                      <p className="text-lg md:text-2xl font-bold">{stats.facets.publishers.length}</p>
                      <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">Publishers</p>
                    </div>
                  </div>
                </Card>
                <Card className="p-2 md:p-4">
                  <div className="flex items-center">
                    <Cpu className="w-6 h-6 md:w-8 md:h-8 text-orange-600 mr-2 md:mr-3" />
                    <div>
                      <p className="text-lg md:text-2xl font-bold">{stats.processing_stats.completed}</p>
                      <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">Processed</p>
                    </div>
                  </div>
                </Card>
                <Card className="p-2 md:p-4 col-span-2 md:col-span-1">
                  <div className="flex items-center">
                    <Library className="w-6 h-6 md:w-8 md:h-8 text-red-600 mr-2 md:mr-3" />
                    <div>
                      <p className="text-lg md:text-2xl font-bold">{stats.facets.genres.length}</p>
                      <p className="text-xs md:text-sm text-gray-600 dark:text-gray-400">Genres</p>
                    </div>
                  </div>
                </Card>
              </div>
            </div>
          )}

          {/* Books Grid */}
          <div className="flex-1 overflow-y-auto p-2 md:p-4">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                <span className="ml-2">Loading books...</span>
              </div>
            ) : error ? (
              <Alert className="max-w-md mx-auto">
                <XCircle className="w-4 h-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            ) : books.length === 0 ? (
              <div className="text-center py-12">
                <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">No books found</h3>
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {(() => {
                    const filters = {
                      searchTerm, selectedAuthors, selectedPublishers, selectedGenres,
                      selectedSubjectAreas, selectedLanguages, selectedDifficulties,
                      selectedProcessors, selectedFileTypes, selectedYears
                    }
                    const hasActiveFilter = Object.values(filters).some(value =>
                      Array.isArray(value) ? value.length > 0 : Boolean(value)
                    )
                    return hasActiveFilter ? 'Try adjusting your filters.' : 'Upload your first book to get started.'
                  })()}
                </p>
                <Button onClick={() => setShowUploadModal(true)} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Upload Book
                </Button>
              </div>
            ) : (
              <>
                {/* Books Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 md:gap-6 mb-4 md:mb-6">
                  {books.map((book) => (
                    <BookCard
                      key={book._id}
                      book={book}
                      onClick={setSelectedBook}
                    />
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      Page {currentPage} of {totalPages}
                    </p>
                    <div className="flex space-x-2">
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={currentPage === 1}
                        onClick={() => setCurrentPage(currentPage - 1)}
                      >
                        Previous
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        disabled={currentPage === totalPages}
                        onClick={() => setCurrentPage(currentPage + 1)}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </main>

        {/* Upload Modal */}
        {showUploadModal && (
          <BookUploadModal
            onClose={() => setShowUploadModal(false)}
            onUpload={handleBookUpload}
          />
        )}
      </div>
    </>
  )
}

export default FacetedBooksDashboard
