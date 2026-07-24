import React from 'react'
import {
  Building2,
  Calendar,
  Tag as TagIcon,
} from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

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
  'beginner': 'bg-green-200 text-green-900 border-green-400 dark:bg-green-900 dark:text-green-200 dark:border-green-600',
  'intermediate': 'bg-yellow-200 text-yellow-900 border-yellow-400 dark:bg-yellow-900 dark:text-yellow-200 dark:border-yellow-600',
  'advanced': 'bg-red-200 text-red-900 border-red-400 dark:bg-red-900 dark:text-red-200 dark:border-red-600',
  'expert': 'bg-purple-200 text-purple-900 border-purple-400 dark:bg-purple-900 dark:text-purple-200 dark:border-purple-600'
}

const FILE_TYPE_COLORS = {
  'pdf': 'bg-red-200 text-red-900 border-red-400 dark:bg-red-900 dark:text-red-200 dark:border-red-600',
  'epub': 'bg-blue-200 text-blue-900 border-blue-400 dark:bg-blue-900 dark:text-blue-200 dark:border-blue-600'
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

interface BookCardProps {
  book: Book
  onClick: (book: Book) => void
}

const BookCard: React.FC<BookCardProps> = ({ book, onClick }) => {
  return (
    <Card
      className="cursor-pointer hover:shadow-lg transition-shadow"
      onClick={() => onClick(book)}
    >
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-sm font-semibold line-clamp-2 mb-1">
              {book.title}
            </CardTitle>
            <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">
              {Array.isArray(book.authors) ? book.authors.join(', ') : 'Unknown Author'}
            </p>
          </div>
          <Badge variant="outline" className={FILE_TYPE_COLORS[book.file_type as keyof typeof FILE_TYPE_COLORS] || 'bg-gray-100 dark:bg-gray-800'}>
            {book.file_type.toUpperCase()}
          </Badge>
        </div>

        {book.publisher && (
          <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
            <Building2 className="w-3 h-3 mr-1" />
            {book.publisher}
          </p>
        )}

        {book.publication_year && (
          <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center">
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
                <Badge key={idx} variant="outline" className="text-xs bg-blue-50 dark:bg-blue-950 text-blue-700">
                  {genre}
                </Badge>
              ))}
              {book.genre.length > 3 && (
                <Badge variant="outline" className="text-xs bg-gray-50 dark:bg-gray-900">
                  +{book.genre.length - 3} more
                </Badge>
              )}
            </div>
          )}

          {/* Reading difficulty */}
          {book.reading_difficulty && (
            <Badge variant="outline" className={`text-xs ${DIFFICULTY_COLORS[book.reading_difficulty as keyof typeof DIFFICULTY_COLORS] || 'bg-gray-100 dark:bg-gray-800'}`}>
              {book.reading_difficulty}
            </Badge>
          )}

          {/* Processing status */}
          <div className="flex items-center justify-between">
            {getProcessingStatusBadge(book.processing_status)}
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatFileSize(book.file_size)}
            </span>
          </div>

          {/* Concept tags count */}
          {book.concept_ids && book.concept_ids.length > 0 && (
            <div className="flex items-center text-xs text-gray-500 dark:text-gray-400">
              <TagIcon className="w-3 h-3 mr-1" />
              {book.concept_ids.length} concept{book.concept_ids.length !== 1 ? 's' : ''}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export type { Book }
export { DIFFICULTY_COLORS, FILE_TYPE_COLORS }
export default BookCard
