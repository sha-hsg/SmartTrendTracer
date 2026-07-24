import React from 'react'
import {
  ArrowLeft,
  User,
  Building2,
  Calendar,
  Hash,
  Globe,
  Loader2,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'

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
  file_type: string
  file_size?: number
  file_url?: string | null
  file_name?: string | null
  processor?: string
  processing_method?: string
  processing_status?: string
  markdown_content?: string
  table_of_contents?: Array<{ chapter: string; page: number }>
  glossary_terms?: Array<{ term: string; definition: string }>
  concept_ids: string[]
  concepts?: Array<{ concept_id?: string; _id?: string; display_name?: string; name?: string; description?: string; slug?: string }>
  summary?: string
  key_themes: string[]
  reading_difficulty?: string
  uploaded_at: string
  created_at: string
  updated_at: string
}

const DIFFICULTY_COLORS = {
  'beginner': 'bg-green-100 text-green-800',
  'intermediate': 'bg-yellow-100 text-yellow-800',
  'advanced': 'bg-red-100 text-red-800',
  'expert': 'bg-purple-100 text-purple-800'
}

const FILE_TYPE_COLORS = {
  'pdf': 'bg-red-100 text-red-800',
  'epub': 'bg-blue-100 text-blue-800'
}

interface BookMetadataPanelProps {
  book: Book
  onBack: () => void
  bookConcepts: Array<{ concept_id?: string; _id?: string; display_name?: string; slug?: string; name?: string }>
  newConceptText: string
  onNewConceptTextChange: (text: string) => void
  onAddConcept: () => void
  onRemoveConcept: (conceptId: string) => void
  addingConcept: boolean
  conceptError: string | null
}

const formatFileSize = (bytes?: number) => {
  if (!bytes) return 'Unknown'
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}

const BookMetadataPanel: React.FC<BookMetadataPanelProps> = ({
  book,
  onBack,
  bookConcepts,
  newConceptText,
  onNewConceptTextChange,
  onAddConcept,
  onRemoveConcept,
  addingConcept,
  conceptError,
}) => {
  return (
    <div className="w-80 bg-white shadow-lg overflow-y-auto">
      <div className="p-4 border-b">
        <Button variant="ghost" onClick={onBack} className="mb-4">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Library
        </Button>

        <div className="space-y-3">
          <div className="flex items-start justify-between">
            <h1 className="text-lg font-bold leading-tight">{book.title}</h1>
            <Badge variant="outline" className={FILE_TYPE_COLORS[book.file_type as keyof typeof FILE_TYPE_COLORS]}>
              {book.file_type.toUpperCase()}
            </Badge>
          </div>

          {book.authors && book.authors.length > 0 && (
            <div className="flex items-center text-sm text-gray-600">
              <User className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>{book.authors.join(', ')}</span>
            </div>
          )}

          {book.publisher && (
            <div className="flex items-center text-sm text-gray-600">
              <Building2 className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>{book.publisher}</span>
            </div>
          )}

          {book.publication_year && (
            <div className="flex items-center text-sm text-gray-600">
              <Calendar className="w-4 h-4 mr-2 flex-shrink-0" />
              <span>{book.publication_year}</span>
            </div>
          )}

          {book.reading_difficulty && (
            <Badge className={DIFFICULTY_COLORS[book.reading_difficulty as keyof typeof DIFFICULTY_COLORS]}>
              {book.reading_difficulty}
            </Badge>
          )}
        </div>
      </div>

      {/* Book Metadata */}
      <div className="p-4 space-y-4">
        {book.isbn && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">ISBN</label>
            <p className="text-sm flex items-center">
              <Hash className="w-3 h-3 mr-1" />
              {book.isbn}
            </p>
          </div>
        )}

        {book.language && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Language</label>
            <p className="text-sm flex items-center">
              <Globe className="w-3 h-3 mr-1" />
              {book.language}
            </p>
          </div>
        )}

        {book.file_size && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">File Size</label>
            <p className="text-sm">{formatFileSize(book.file_size)}</p>
          </div>
        )}

        {book.page_count && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Pages</label>
            <p className="text-sm">{book.page_count.toLocaleString()}</p>
          </div>
        )}

        {book.genre && book.genre.length > 0 && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Genre</label>
            <div className="flex flex-wrap gap-1 mt-1">
              {book.genre.map((genre, idx) => (
                <Badge key={idx} variant="outline" className="text-xs bg-blue-50">
                  {genre}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {book.subject_areas && book.subject_areas.length > 0 && (
          <div>
            <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Subject Areas</label>
            <div className="flex flex-wrap gap-1 mt-1">
              {book.subject_areas.map((area, idx) => (
                <Badge key={idx} variant="outline" className="text-xs bg-green-50">
                  {area}
                </Badge>
              ))}
            </div>
          </div>
        )}

        <div>
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Concept Tags</label>
          {bookConcepts.length > 0 ? (
            <div className="flex flex-wrap gap-1 mt-1">
              {bookConcepts.map((concept, idx) => {
                const id = concept.concept_id || concept._id || concept.slug || `${idx}`
                const label = concept.display_name || concept.name || concept.slug || id
                return (
                  <Badge key={id} variant="outline" className="text-xs bg-purple-50 flex items-center gap-1">
                    {label}
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation()
                        if (concept.concept_id || concept._id) {
                          onRemoveConcept(concept.concept_id || concept._id!)
                        }
                      }}
                      className="text-purple-700 hover:text-purple-900"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                )
              })}
            </div>
          ) : (
            <p className="text-xs text-gray-500 mt-1">No concepts yet.</p>
          )}

          <div className="mt-2 flex items-center gap-2">
            <Input
              value={newConceptText}
              onChange={(e) => onNewConceptTextChange(e.target.value)}
              placeholder="Add concept"
              className="text-sm"
            />
            <Button
              variant="outline"
              size="sm"
              onClick={onAddConcept}
              disabled={addingConcept}
            >
              {addingConcept ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Add'}
            </Button>
          </div>
          {conceptError && <p className="text-xs text-red-600 mt-1">{conceptError}</p>}
        </div>

        <div>
          <label className="text-xs font-medium text-gray-500 uppercase tracking-wide">Uploaded</label>
          <p className="text-sm">{formatDate(book.uploaded_at)}</p>
        </div>
      </div>
    </div>
  )
}

export default BookMetadataPanel
