import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import {
  BookOpen,
  Search,
  Filter,
  Calendar,
  User,
  Building2,
  Tag as TagIcon,
  Plus,
  Users,
  Loader2,
  X,
  XCircle,
  ChevronDown,
  ChevronRight,
  FilterX,
  Cpu,
  GraduationCap,
  FileCode,
  Library
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Checkbox } from '@/components/ui/checkbox'

import BookViewerOptimized from './BookViewerOptimized'
import BookUploadModal from './BookUploadModal'

interface Book {
  _id: string
  title: string
  authors: string[]
  authors_detailed?: Array<{ name: string; institution?: string }>
  publisher?: string
  publication_year?: number
  isbn?: string
  edition?: string
  language?: string
  genre: string[]
  subject_areas: string[]
  page_count?: number
  file_type: string // 'pdf' or 'epub'
  file_size?: number
  file_url?: string
  file_name?: string
  processor?: string
  processing_status?: string
  markdown_content?: string
  table_of_contents?: Array<{ chapter: string; page: number }>
  glossary_terms?: Array<{ term: string; definition: string }>
  concept_ids: string[]
  concepts?: Array<{ _id: string; name: string; description?: string }>
  summary?: string
  key_themes: string[]
  reading_difficulty?: string
  uploaded_at: string
  created_at: string
  updated_at: string
}

interface BooksStats {
  total_books: number
  facets: {
    authors: string[]
    publishers: string[]
    genres: string[]
    subject_areas: string[]
    languages: string[]
    reading_difficulties: string[]
    processors: string[]
    file_types: string[]
    years: number[]
    concepts: Array<{ concept_id: string; display_name: string; count: number }>
  }
  missing_data: {
    no_processor: number
    no_year: number
    no_publisher: number
    no_isbn: number
    no_annotations: number
  }
  processing_stats: {
    completed: number
    processing: number
    failed: number
    pending: number
  }
}

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

const DIFFICULTY_COLORS = {
  'beginner': 'bg-green-200 text-green-900 border-green-400',
  'intermediate': 'bg-yellow-200 text-yellow-900 border-yellow-400',
  'advanced': 'bg-red-200 text-red-900 border-red-400',
  'expert': 'bg-purple-200 text-purple-900 border-purple-400'
}

const FILE_TYPE_COLORS = {
  'pdf': 'bg-red-200 text-red-900 border-red-400',
  'epub': 'bg-blue-200 text-blue-900 border-blue-400'
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
  const [pageSize, setPageSize] = useState(20)

  // UI state
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showFilters, setShowFilters] = useState(true)
  const [sortBy, setSortBy] = useState('uploaded_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

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

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return 'Unknown'
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getProcessingStatusBadge = (status?: string) => {
    switch (status) {
      case 'completed':
        return <Badge variant="outline" className="bg-green-100 text-green-800">Completed</Badge>
      case 'processing':
        return <Badge variant="outline" className="bg-blue-100 text-blue-800">Processing</Badge>
      case 'queued':
        return <Badge variant="outline" className="bg-purple-100 text-purple-800">Queued</Badge>
      case 'failed':
        return <Badge variant="outline" className="bg-red-100 text-red-800">Failed</Badge>
      case 'pending':
        return <Badge variant="outline" className="bg-yellow-100 text-yellow-800">Pending</Badge>
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  if (selectedBook) {
    return (
      <BookViewerOptimized
        book={selectedBook}
        onBack={() => setSelectedBook(null)}
        onBookUpdate={(updated) => {
          setSelectedBook(updated)
          setBooks(prev => prev.map(book => (book._id === updated._id ? updated : book)))
        }}
      />
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

      <div className="flex h-screen bg-gray-50">
        {/* Mobile Overlay Background */}
        {showFilters && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
            onClick={() => setShowFilters(false)}
            aria-hidden="true"
          />
        )}

        {/* Left Sidebar - Filters */}
        {showFilters && (
          <aside
            className={`
              w-80 bg-white shadow-lg overflow-y-auto z-40
              fixed left-0 top-0 h-full lg:relative lg:z-auto
              transform transition-transform duration-300 ease-in-out
              ${showFilters ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
            `}
            role="complementary"
            aria-label="Book filters and search options"
          >
            <div className="p-4 border-b">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-lg font-semibold flex items-center">
                  <Filter className="w-5 h-5 mr-2" />
                  Book Filters
                </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFilters(false)}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={clearAllFilters}
                className="flex-1"
              >
                <FilterX className="w-4 h-4 mr-1" />
                Clear All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowUploadModal(true)}
                className="flex-1"
              >
                <Plus className="w-4 h-4 mr-1" />
                Upload
              </Button>
            </div>
          </div>

          <ScrollArea className="flex-1">
            <div className="p-4 space-y-4">
              {/* Search */}
              <div>
                <label className="text-sm font-medium mb-2 block">Search Books</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <Input
                    placeholder="Search title, authors, content..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              {/* Special Filters */}
              <div>
                <label className="text-sm font-medium mb-2 block">Quick Filters</label>
                <Select value={specialFilter} onValueChange={setSpecialFilter}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select filter..." />
                  </SelectTrigger>
                  <SelectContent>
                <SelectItem value="all">All Books</SelectItem>
                    <SelectItem value="recently_uploaded">Recently Uploaded</SelectItem>
                    <SelectItem value="processing_failed">Processing Failed</SelectItem>
                    <SelectItem value="large_books">Large Books (500+ pages)</SelectItem>
                    <SelectItem value="epub_only">EPUB Only</SelectItem>
                    <SelectItem value="pdf_only">PDF Only</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* File Type Filter */}
              {stats?.facets?.file_types && stats.facets.file_types.length > 0 && (
                <div>
                  <label id="file-type-filter-label" className="text-sm font-medium mb-2 block flex items-center">
                    <FileCode className="w-4 h-4 mr-1" />
                    File Type
                  </label>
                  <div className="space-y-2" role="group" aria-labelledby="file-type-filter-label">
                    {stats.facets.file_types.map((type) => (
                      <div key={type} className="flex items-center space-x-2">
                        <Checkbox
                          id={`file-type-${type}`}
                          checked={selectedFileTypes.includes(type)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedFileTypes([...selectedFileTypes, type])
                            } else {
                              setSelectedFileTypes(selectedFileTypes.filter(t => t !== type))
                            }
                          }}
                          aria-describedby={`file-type-${type}-description`}
                        />
                        <label
                          htmlFor={`file-type-${type}`}
                          className="text-sm flex items-center cursor-pointer"
                        >
                          <Badge variant="outline" className={FILE_TYPE_COLORS[type as keyof typeof FILE_TYPE_COLORS] || 'bg-gray-100'}>
                            {type.toUpperCase()}
                          </Badge>
                          <span className="sr-only" id={`file-type-${type}-description`}>
                            Filter by {type} files
                          </span>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Concept Filter */}
              {stats?.facets?.concepts && stats.facets.concepts.length > 0 && (
                <div className="border-b border-gray-200 pb-3">
                  <button
                    onClick={() => toggleSection('concepts')}
                    className="w-full flex items-center justify-between text-sm font-medium mb-2 hover:text-blue-600 transition-colors"
                    aria-expanded={!collapsedSections.concepts}
                    aria-controls="concepts-filter-content"
                  >
                    <span className="flex items-center">
                      <TagIcon className="w-4 h-4 mr-1" />
                      Concepts ({stats.facets.concepts.length})
                      {selectedConceptIds.length > 0 && (
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {selectedConceptIds.length}
                        </Badge>
                      )}
                    </span>
                    {collapsedSections.concepts ? (
                      <ChevronRight className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>

                  {!collapsedSections.concepts && (
                    <div id="concepts-filter-content">
                      <ScrollArea className="max-h-32">
                        <div className="space-y-1" role="group" aria-labelledby="concepts-filter-label">
                          {stats.facets.concepts.slice(0, 25).map((concept) => (
                            <div key={concept.concept_id} className="flex items-center space-x-2">
                              <Checkbox
                                id={`concept-${concept.concept_id}`}
                                checked={selectedConceptIds.includes(concept.concept_id)}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    setSelectedConceptIds([...selectedConceptIds, concept.concept_id])
                                  } else {
                                    setSelectedConceptIds(selectedConceptIds.filter(id => id !== concept.concept_id))
                                  }
                                }}
                                aria-describedby={`concept-${concept.concept_id}-description`}
                              />
                              <label
                                htmlFor={`concept-${concept.concept_id}`}
                                className="text-xs flex-1 flex items-center justify-between cursor-pointer"
                              >
                                <span>{concept.display_name}</span>
                                <span className="text-gray-500 ml-2" aria-label={`${concept.count} books`}>
                                  {concept.count}
                                </span>
                                <span className="sr-only" id={`concept-${concept.concept_id}-description`}>
                                  Filter by {concept.display_name} concept, {concept.count} books
                                </span>
                              </label>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}
                </div>
              )}

              {/* Authors Filter */}
              {stats?.facets?.authors && stats.facets.authors.length > 0 && (
                <div className="border-b border-gray-200 pb-3">
                  <button
                    onClick={() => toggleSection('authors')}
                    className="w-full flex items-center justify-between text-sm font-medium mb-2 hover:text-blue-600 transition-colors"
                    aria-expanded={!collapsedSections.authors}
                    aria-controls="authors-filter-content"
                  >
                    <span className="flex items-center">
                      <User className="w-4 h-4 mr-1" />
                      Authors ({stats.facets.authors.length})
                      {selectedAuthors.length > 0 && (
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {selectedAuthors.length}
                        </Badge>
                      )}
                    </span>
                    {collapsedSections.authors ? (
                      <ChevronRight className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>

                  {!collapsedSections.authors && (
                    <div id="authors-filter-content">
                      <ScrollArea className="max-h-32">
                        <div className="space-y-1">
                          {stats.facets.authors.slice(0, 20).map((author) => (
                            <div key={author} className="flex items-center space-x-2">
                              <Checkbox
                                checked={selectedAuthors.includes(author)}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    setSelectedAuthors([...selectedAuthors, author])
                                  } else {
                                    setSelectedAuthors(selectedAuthors.filter(a => a !== author))
                                  }
                                }}
                              />
                              <label className="text-xs">{author}</label>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}
                </div>
              )}

              {/* Publishers Filter */}
              {stats?.facets?.publishers && stats.facets.publishers.length > 0 && (
                <div className="border-b border-gray-200 pb-3">
                  <button
                    onClick={() => toggleSection('publishers')}
                    className="w-full flex items-center justify-between text-sm font-medium mb-2 hover:text-blue-600 transition-colors"
                    aria-expanded={!collapsedSections.publishers}
                    aria-controls="publishers-filter-content"
                  >
                    <span className="flex items-center">
                      <Building2 className="w-4 h-4 mr-1" />
                      Publishers ({stats.facets.publishers.length})
                      {selectedPublishers.length > 0 && (
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {selectedPublishers.length}
                        </Badge>
                      )}
                    </span>
                    {collapsedSections.publishers ? (
                      <ChevronRight className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>

                  {!collapsedSections.publishers && (
                    <div id="publishers-filter-content">
                      <ScrollArea className="max-h-32">
                        <div className="space-y-1">
                          {stats.facets.publishers.slice(0, 20).map((publisher) => (
                            <div key={publisher} className="flex items-center space-x-2">
                              <Checkbox
                                checked={selectedPublishers.includes(publisher)}
                                onCheckedChange={(checked) => {
                                  if (checked) {
                                    setSelectedPublishers([...selectedPublishers, publisher])
                                  } else {
                                    setSelectedPublishers(selectedPublishers.filter(p => p !== publisher))
                                  }
                                }}
                              />
                              <label className="text-xs">{publisher}</label>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}
                </div>
              )}

              {/* Genre Filter */}
              {stats?.facets?.genres && stats.facets.genres.length > 0 && (
                <div className="border-b border-gray-200 pb-3">
                  <button
                    onClick={() => toggleSection('genres')}
                    className="w-full flex items-center justify-between text-sm font-medium mb-2 hover:text-blue-600 transition-colors"
                    aria-expanded={!collapsedSections.genres}
                    aria-controls="genres-filter-content"
                  >
                    <span className="flex items-center">
                      <Library className="w-4 h-4 mr-1" />
                      Genres ({stats.facets.genres.length})
                      {selectedGenres.length > 0 && (
                        <Badge variant="secondary" className="ml-2 text-xs">
                          {selectedGenres.length}
                        </Badge>
                      )}
                    </span>
                    {collapsedSections.genres ? (
                      <ChevronRight className="w-4 h-4" />
                    ) : (
                      <ChevronDown className="w-4 h-4" />
                    )}
                  </button>

                  {!collapsedSections.genres && (
                    <div id="genres-filter-content">
                      <div className="space-y-1">
                        {stats.facets.genres.map((genre) => (
                          <div key={genre} className="flex items-center space-x-2">
                            <Checkbox
                              checked={selectedGenres.includes(genre)}
                              onCheckedChange={(checked) => {
                                if (checked) {
                                  setSelectedGenres([...selectedGenres, genre])
                                } else {
                                  setSelectedGenres(selectedGenres.filter(g => g !== genre))
                                }
                              }}
                            />
                            <label className="text-xs">{genre}</label>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Reading Difficulty Filter */}
              {stats?.facets?.reading_difficulties && stats.facets.reading_difficulties.length > 0 && (
                <div>
                  <label className="text-sm font-medium mb-2 block flex items-center">
                    <GraduationCap className="w-4 h-4 mr-1" />
                    Reading Difficulty
                  </label>
                  <div className="space-y-1">
                    {stats.facets.reading_difficulties.map((difficulty) => (
                      <div key={difficulty} className="flex items-center space-x-2">
                        <Checkbox
                          checked={selectedDifficulties.includes(difficulty)}
                          onCheckedChange={(checked) => {
                            if (checked) {
                              setSelectedDifficulties([...selectedDifficulties, difficulty])
                            } else {
                              setSelectedDifficulties(selectedDifficulties.filter(d => d !== difficulty))
                            }
                          }}
                        />
                        <label className="text-xs flex items-center">
                          <Badge variant="outline" className={DIFFICULTY_COLORS[difficulty as keyof typeof DIFFICULTY_COLORS] || 'bg-gray-100'}>
                            {difficulty}
                          </Badge>
                        </label>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Years Filter */}
              {stats?.facets?.years && stats.facets.years.length > 0 && (
                <div>
                  <label className="text-sm font-medium mb-2 block flex items-center">
                    <Calendar className="w-4 h-4 mr-1" />
                    Publication Years
                  </label>
                  <ScrollArea className="max-h-32">
                    <div className="space-y-1">
                      {stats.facets.years.slice(0, 15).map((year) => (
                        <div key={year} className="flex items-center space-x-2">
                          <Checkbox
                            checked={selectedYears.includes(year)}
                            onCheckedChange={(checked) => {
                              if (checked) {
                                setSelectedYears([...selectedYears, year])
                              } else {
                                setSelectedYears(selectedYears.filter(y => y !== year))
                              }
                            }}
                          />
                          <label className="text-xs">{year}</label>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </div>
          </ScrollArea>
        </aside>
      )}

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
        <header className="bg-white shadow-sm border-b p-4" role="banner">
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
                <Badge variant="outline" className="bg-blue-50 text-xs md:text-sm">
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
            </div>
          </div>
        </header>

        {/* Stats Cards */}
        {stats && (
          <div className="bg-white border-b p-2 md:p-4">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2 md:gap-4">
              <Card className="p-2 md:p-4">
                <div className="flex items-center">
                  <BookOpen className="w-6 h-6 md:w-8 md:h-8 text-blue-600 mr-2 md:mr-3" />
                  <div>
                    <p className="text-lg md:text-2xl font-bold">{stats.total_books}</p>
                    <p className="text-xs md:text-sm text-gray-600">Total Books</p>
                  </div>
                </div>
              </Card>
              <Card className="p-2 md:p-4">
                <div className="flex items-center">
                  <Users className="w-6 h-6 md:w-8 md:h-8 text-green-600 mr-2 md:mr-3" />
                  <div>
                    <p className="text-lg md:text-2xl font-bold">{stats.facets.authors.length}</p>
                    <p className="text-xs md:text-sm text-gray-600">Authors</p>
                  </div>
                </div>
              </Card>
              <Card className="p-2 md:p-4">
                <div className="flex items-center">
                  <Building2 className="w-6 h-6 md:w-8 md:h-8 text-purple-600 mr-2 md:mr-3" />
                  <div>
                    <p className="text-lg md:text-2xl font-bold">{stats.facets.publishers.length}</p>
                    <p className="text-xs md:text-sm text-gray-600">Publishers</p>
                  </div>
                </div>
              </Card>
              <Card className="p-2 md:p-4">
                <div className="flex items-center">
                  <Cpu className="w-6 h-6 md:w-8 md:h-8 text-orange-600 mr-2 md:mr-3" />
                  <div>
                    <p className="text-lg md:text-2xl font-bold">{stats.processing_stats.completed}</p>
                    <p className="text-xs md:text-sm text-gray-600">Processed</p>
                  </div>
                </div>
              </Card>
              <Card className="p-2 md:p-4 col-span-2 md:col-span-1">
                <div className="flex items-center">
                  <Library className="w-6 h-6 md:w-8 md:h-8 text-red-600 mr-2 md:mr-3" />
                  <div>
                    <p className="text-lg md:text-2xl font-bold">{stats.facets.genres.length}</p>
                    <p className="text-xs md:text-sm text-gray-600">Genres</p>
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
              <h3 className="text-lg font-medium text-gray-900 mb-2">No books found</h3>
              <p className="text-gray-600 mb-4">
                {Object.keys({
                  searchTerm, selectedAuthors, selectedPublishers, selectedGenres,
                  selectedSubjectAreas, selectedLanguages, selectedDifficulties,
                  selectedProcessors, selectedFileTypes, selectedYears
                }).some(key => {
                  const value = eval(key)
                  return Array.isArray(value) ? value.length > 0 : Boolean(value)
                }) ? 'Try adjusting your filters.' : 'Upload your first book to get started.'}
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
                  <Card
                    key={book._id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => setSelectedBook(book)}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <CardTitle className="text-sm font-semibold line-clamp-2 mb-1">
                            {book.title}
                          </CardTitle>
                          <p className="text-xs text-gray-600 mb-2">
                            {Array.isArray(book.authors) ? book.authors.join(', ') : 'Unknown Author'}
                          </p>
                        </div>
                        <Badge variant="outline" className={FILE_TYPE_COLORS[book.file_type as keyof typeof FILE_TYPE_COLORS] || 'bg-gray-100'}>
                          {book.file_type.toUpperCase()}
                        </Badge>
                      </div>

                      {book.publisher && (
                        <p className="text-xs text-gray-500 flex items-center">
                          <Building2 className="w-3 h-3 mr-1" />
                          {book.publisher}
                        </p>
                      )}

                      {book.publication_year && (
                        <p className="text-xs text-gray-500 flex items-center">
                          <Calendar className="w-3 h-3 mr-1" />
                          {book.publication_year}
                        </p>
                      )}
                    </CardHeader>

                    <CardContent className="pt-2">
                      <div className="space-y-2">
                        {/* Genre tags */}
                        {book.genre && book.genre.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {book.genre.slice(0, 3).map((genre, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs bg-blue-50 text-blue-700">
                                {genre}
                              </Badge>
                            ))}
                            {book.genre.length > 3 && (
                              <Badge variant="outline" className="text-xs bg-gray-50">
                                +{book.genre.length - 3} more
                              </Badge>
                            )}
                          </div>
                        )}

                        {/* Reading difficulty */}
                        {book.reading_difficulty && (
                          <Badge variant="outline" className={`text-xs ${DIFFICULTY_COLORS[book.reading_difficulty as keyof typeof DIFFICULTY_COLORS] || 'bg-gray-100'}`}>
                            {book.reading_difficulty}
                          </Badge>
                        )}

                        {/* Processing status */}
                        <div className="flex items-center justify-between">
                          {getProcessingStatusBadge(book.processing_status)}
                          <span className="text-xs text-gray-500">
                            {formatFileSize(book.file_size)}
                          </span>
                        </div>

                        {/* Concept tags count */}
                        {book.concept_ids && book.concept_ids.length > 0 && (
                          <div className="flex items-center text-xs text-gray-500">
                            <TagIcon className="w-3 h-3 mr-1" />
                            {book.concept_ids.length} concept{book.concept_ids.length !== 1 ? 's' : ''}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-600">
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
