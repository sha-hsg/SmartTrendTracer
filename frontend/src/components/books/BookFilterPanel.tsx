import React from 'react'
import {
  Search,
  Filter,
  Calendar,
  User,
  Building2,
  Tag as TagIcon,
  Plus,
  X,
  ChevronDown,
  ChevronRight,
  FilterX,
  GraduationCap,
  FileCode,
  Library,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Checkbox } from '@/components/ui/checkbox'
import { DIFFICULTY_COLORS, FILE_TYPE_COLORS } from './BookCard'

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

interface BookFilterPanelProps {
  stats: BooksStats | null
  showFilters: boolean
  setShowFilters: (show: boolean) => void
  searchTerm: string
  setSearchTerm: (term: string) => void
  specialFilter: string
  setSpecialFilter: (filter: string) => void
  selectedFileTypes: string[]
  setSelectedFileTypes: (types: string[]) => void
  selectedConceptIds: string[]
  setSelectedConceptIds: (ids: string[]) => void
  selectedAuthors: string[]
  setSelectedAuthors: (authors: string[]) => void
  selectedPublishers: string[]
  setSelectedPublishers: (publishers: string[]) => void
  selectedGenres: string[]
  setSelectedGenres: (genres: string[]) => void
  selectedDifficulties: string[]
  setSelectedDifficulties: (difficulties: string[]) => void
  selectedYears: number[]
  setSelectedYears: (years: number[]) => void
  collapsedSections: Record<string, boolean>
  toggleSection: (section: string) => void
  clearAllFilters: () => void
  onUploadClick: () => void
}

const BookFilterPanel: React.FC<BookFilterPanelProps> = ({
  stats,
  showFilters,
  setShowFilters,
  searchTerm,
  setSearchTerm,
  specialFilter,
  setSpecialFilter,
  selectedFileTypes,
  setSelectedFileTypes,
  selectedConceptIds,
  setSelectedConceptIds,
  selectedAuthors,
  setSelectedAuthors,
  selectedPublishers,
  setSelectedPublishers,
  selectedGenres,
  setSelectedGenres,
  selectedDifficulties,
  setSelectedDifficulties,
  selectedYears,
  setSelectedYears,
  collapsedSections,
  toggleSection,
  clearAllFilters,
  onUploadClick,
}) => {
  if (!showFilters) return null

  return (
    <aside
      className={`
        w-80 bg-white dark:bg-gray-950 shadow-lg overflow-y-auto z-40
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
          onClick={onUploadClick}
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
                    <Badge variant="outline" className={FILE_TYPE_COLORS[type as keyof typeof FILE_TYPE_COLORS] || 'bg-gray-100 dark:bg-gray-800'}>
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
          <div className="border-b border-gray-200 dark:border-gray-700 pb-3">
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
                          <span className="text-gray-500 dark:text-gray-400 ml-2" aria-label={`${concept.count} books`}>
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
          <div className="border-b border-gray-200 dark:border-gray-700 pb-3">
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
          <div className="border-b border-gray-200 dark:border-gray-700 pb-3">
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
          <div className="border-b border-gray-200 dark:border-gray-700 pb-3">
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
                    <Badge variant="outline" className={DIFFICULTY_COLORS[difficulty as keyof typeof DIFFICULTY_COLORS] || 'bg-gray-100 dark:bg-gray-800'}>
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
  )
}

export type { BooksStats }
export default BookFilterPanel
