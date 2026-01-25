import React, { useState } from 'react'
import axios from 'axios'
import {
  Upload,
  X,
  FileText,
  BookOpen,
  User,
  Building2,
  Calendar,
  Hash,
  Globe,
  Library,
  Loader2,
  Check,
  AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

interface BookUploadModalProps {
  onClose: () => void
  onUpload: () => void
}

const BookUploadModal: React.FC<BookUploadModalProps> = ({ onClose, onUpload }) => {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [uploaded, setUploaded] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [dragOver, setDragOver] = useState(false)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})

  // Metadata fields
  const [title, setTitle] = useState('')
  const [authors, setAuthors] = useState('')
  const [publisher, setPublisher] = useState('')
  const [publicationYear, setPublicationYear] = useState<number | undefined>()
  const [isbn, setIsbn] = useState('')
  const [genre, setGenre] = useState('none')
  const [subjectAreas, setSubjectAreas] = useState('')
  const [language, setLanguage] = useState('English')

  // Real-time validation function
  const validateField = (field: string, value: any) => {
    const errors: Record<string, string> = {}

    switch (field) {
      case 'title':
        if (!value?.trim()) {
          errors.title = 'Title is required'
        } else if (value.length > 200) {
          errors.title = 'Title too long (max 200 characters)'
        }
        break
      case 'isbn':
        if (value && !/^[\d-]{10,17}$/.test(value.replace(/[-\s]/g, ''))) {
          errors.isbn = 'Invalid ISBN format (10 or 13 digits)'
        }
        break
      case 'publicationYear':
        const currentYear = new Date().getFullYear()
        if (value && (value < 1000 || value > currentYear)) {
          errors.publicationYear = `Invalid publication year (1000-${currentYear})`
        }
        break
      case 'authors':
        if (value && value.length > 500) {
          errors.authors = 'Authors field too long (max 500 characters)'
        }
        break
      case 'publisher':
        if (value && value.length > 200) {
          errors.publisher = 'Publisher name too long (max 200 characters)'
        }
        break
    }

    setFieldErrors(prev => ({ ...prev, [field]: errors[field] || '' }))
    return !errors[field]
  }

  // Validate all fields
  const validateAllFields = () => {
    const fields = ['title', 'isbn', 'publicationYear', 'authors', 'publisher']
    let isValid = true

    fields.forEach(field => {
      const value = field === 'title' ? title :
                   field === 'isbn' ? isbn :
                   field === 'publicationYear' ? publicationYear :
                   field === 'authors' ? authors :
                   field === 'publisher' ? publisher : ''

      if (!validateField(field, value)) {
        isValid = false
      }
    })

    return isValid
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragOver(false)

    const files = Array.from(e.dataTransfer.files)
    const validFile = files.find(f =>
      f.name.toLowerCase().endsWith('.pdf') || f.name.toLowerCase().endsWith('.epub')
    )

    if (validFile) {
      setFile(validFile)
      // Auto-fill title from filename if not set
      if (!title) {
        setTitle(validFile.name.replace(/\.(pdf|epub)$/i, ''))
      }
    } else {
      setError('Please select a valid PDF or EPUB file')
    }
  }

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0]
    if (selectedFile) {
      const isValid = selectedFile.name.toLowerCase().endsWith('.pdf') ||
                     selectedFile.name.toLowerCase().endsWith('.epub')

      if (isValid) {
        setFile(selectedFile)
        setError(null)
        // Auto-fill title from filename if not set
        if (!title) {
          setTitle(selectedFile.name.replace(/\.(pdf|epub)$/i, ''))
        }
      } else {
        setError('Please select a valid PDF or EPUB file')
      }
    }
  }

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload')
      return
    }

    if (!validateAllFields()) {
      setError('Please fix the validation errors before uploading')
      return
    }

    try {
      setUploading(true)
      setError(null)

      const formData = new FormData()
      formData.append('file', file)
      formData.append('title', title.trim())
      if (authors.trim()) formData.append('authors', authors.trim())
      if (publisher.trim()) formData.append('publisher', publisher.trim())
      if (publicationYear) formData.append('publication_year', publicationYear.toString())
      if (isbn.trim()) formData.append('isbn', isbn.trim())
      if (genre.trim()) formData.append('genre', genre.trim())
      if (subjectAreas.trim()) formData.append('subject_areas', subjectAreas.trim())
      if (language) formData.append('language', language)

      await axios.post('/api/books/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setUploaded(true)
      setTimeout(() => {
        onUpload()
      }, 1500)

    } catch (err: any) {
      console.error('Error uploading book:', err)
      setError(err.response?.data?.detail || 'Failed to upload book. Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(1024))
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
  }

  const getFileTypeIcon = (filename: string) => {
    return filename.toLowerCase().endsWith('.epub') ? BookOpen : FileText
  }

  if (uploaded) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mb-4">
              <Check className="w-6 h-6 text-green-600" />
            </div>
            <CardTitle>Upload Successful!</CardTitle>
            <CardDescription>
              Your book has been uploaded successfully and is ready for processing.
            </CardDescription>
          </CardHeader>
        </Card>
      </div>
    )
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <div>
            <CardTitle className="flex items-center">
              <Upload className="w-5 h-5 mr-2" />
              Upload Book
            </CardTitle>
            <CardDescription>
              Upload a PDF or EPUB book with metadata
            </CardDescription>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* File Upload Area */}
          <div>
            <Label className="text-sm font-medium mb-2 block">Book File *</Label>
            <div
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
                dragOver
                  ? 'border-blue-400 bg-blue-50'
                  : file
                  ? 'border-green-400 bg-green-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              {file ? (
                <div className="space-y-2">
                  <div className="mx-auto w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
                    {React.createElement(getFileTypeIcon(file.name), { className: "w-6 h-6 text-green-600" })}
                  </div>
                  <div>
                    <p className="text-sm font-medium">{file.name}</p>
                    <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                  </div>
                  <Button variant="outline" size="sm" onClick={() => setFile(null)}>
                    Remove
                  </Button>
                </div>
              ) : (
                <div className="space-y-2">
                  <Upload className="w-8 h-8 text-gray-400 mx-auto" />
                  <div>
                    <p className="text-sm text-gray-600">
                      Drag and drop your book file here, or{' '}
                      <label className="text-blue-600 hover:text-blue-700 cursor-pointer underline">
                        browse
                        <input
                          type="file"
                          className="hidden"
                          accept=".pdf,.epub"
                          onChange={handleFileSelect}
                        />
                      </label>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      Supports PDF and EPUB files (max 100MB)
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Basic Metadata */}
          <div className="space-y-4">
            <h3 className="font-medium text-sm">Book Information</h3>

            <div>
              <Label htmlFor="title" className="flex items-center justify-between mb-2">
                <span className="flex items-center">
                  <BookOpen className="w-4 h-4 mr-1" />
                  Title *
                </span>
                <span className="text-xs text-gray-500">
                  {title.length}/200
                </span>
              </Label>
              <Input
                id="title"
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value)
                  validateField('title', e.target.value)
                }}
                onBlur={() => validateField('title', title)}
                placeholder="Enter book title..."
                className={`w-full ${fieldErrors.title ? 'border-red-500 focus:border-red-500' : ''}`}
                aria-describedby={fieldErrors.title ? 'title-error' : undefined}
              />
              {fieldErrors.title && (
                <p id="title-error" className="text-xs text-red-600 mt-1 flex items-center">
                  <AlertCircle className="w-3 h-3 mr-1" />
                  {fieldErrors.title}
                </p>
              )}
            </div>

            <div>
              <Label htmlFor="authors" className="flex items-center justify-between mb-2">
                <span className="flex items-center">
                  <User className="w-4 h-4 mr-1" />
                  Authors
                </span>
                <span className="text-xs text-gray-500">
                  {authors.length}/500
                </span>
              </Label>
              <Input
                id="authors"
                value={authors}
                onChange={(e) => {
                  setAuthors(e.target.value)
                  validateField('authors', e.target.value)
                }}
                onBlur={() => validateField('authors', authors)}
                placeholder="Author names (comma-separated)..."
                className={`w-full ${fieldErrors.authors ? 'border-red-500 focus:border-red-500' : ''}`}
                aria-describedby={fieldErrors.authors ? 'authors-error' : undefined}
              />
              {fieldErrors.authors && (
                <p id="authors-error" className="text-xs text-red-600 mt-1 flex items-center">
                  <AlertCircle className="w-3 h-3 mr-1" />
                  {fieldErrors.authors}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="publisher" className="flex items-center justify-between mb-2">
                  <span className="flex items-center">
                    <Building2 className="w-4 h-4 mr-1" />
                    Publisher
                  </span>
                  <span className="text-xs text-gray-500">
                    {publisher.length}/200
                  </span>
                </Label>
                <Input
                  id="publisher"
                  value={publisher}
                  onChange={(e) => {
                    setPublisher(e.target.value)
                    validateField('publisher', e.target.value)
                  }}
                  onBlur={() => validateField('publisher', publisher)}
                  placeholder="Publisher name..."
                  className={fieldErrors.publisher ? 'border-red-500 focus:border-red-500' : ''}
                  aria-describedby={fieldErrors.publisher ? 'publisher-error' : undefined}
                />
                {fieldErrors.publisher && (
                  <p id="publisher-error" className="text-xs text-red-600 mt-1 flex items-center">
                    <AlertCircle className="w-3 h-3 mr-1" />
                    {fieldErrors.publisher}
                  </p>
                )}
              </div>

              <div>
                <Label htmlFor="year" className="flex items-center mb-2">
                  <Calendar className="w-4 h-4 mr-1" />
                  Publication Year
                </Label>
                <Input
                  id="year"
                  type="number"
                  min="1000"
                  max={new Date().getFullYear()}
                  value={publicationYear || ''}
                  onChange={(e) => {
                    const year = e.target.value ? parseInt(e.target.value) : undefined
                    setPublicationYear(year)
                    validateField('publicationYear', year)
                  }}
                  onBlur={() => validateField('publicationYear', publicationYear)}
                  placeholder="YYYY"
                  className={fieldErrors.publicationYear ? 'border-red-500 focus:border-red-500' : ''}
                  aria-describedby={fieldErrors.publicationYear ? 'year-error' : undefined}
                />
                {fieldErrors.publicationYear && (
                  <p id="year-error" className="text-xs text-red-600 mt-1 flex items-center">
                    <AlertCircle className="w-3 h-3 mr-1" />
                    {fieldErrors.publicationYear}
                  </p>
                )}
              </div>
            </div>

            <div>
              <Label htmlFor="isbn" className="flex items-center mb-2">
                <Hash className="w-4 h-4 mr-1" />
                ISBN
              </Label>
              <Input
                id="isbn"
                value={isbn}
                onChange={(e) => {
                  setIsbn(e.target.value)
                  validateField('isbn', e.target.value)
                }}
                onBlur={() => validateField('isbn', isbn)}
                placeholder="ISBN (10 or 13 digits)..."
                className={fieldErrors.isbn ? 'border-red-500 focus:border-red-500' : ''}
                aria-describedby={fieldErrors.isbn ? 'isbn-error' : undefined}
              />
              {fieldErrors.isbn && (
                <p id="isbn-error" className="text-xs text-red-600 mt-1 flex items-center">
                  <AlertCircle className="w-3 h-3 mr-1" />
                  {fieldErrors.isbn}
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label htmlFor="genre" className="flex items-center mb-2">
                  <Library className="w-4 h-4 mr-1" />
                  Genre
                </Label>
                <Select value={genre} onValueChange={setGenre}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select genre..." />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No Genre</SelectItem>
                    <SelectItem value="Fiction">Fiction</SelectItem>
                    <SelectItem value="Non-Fiction">Non-Fiction</SelectItem>
                    <SelectItem value="Technical">Technical</SelectItem>
                    <SelectItem value="Academic">Academic</SelectItem>
                    <SelectItem value="Biography">Biography</SelectItem>
                    <SelectItem value="History">History</SelectItem>
                    <SelectItem value="Science">Science</SelectItem>
                    <SelectItem value="Technology">Technology</SelectItem>
                    <SelectItem value="Business">Business</SelectItem>
                    <SelectItem value="Self-Help">Self-Help</SelectItem>
                    <SelectItem value="Reference">Reference</SelectItem>
                    <SelectItem value="Textbook">Textbook</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="language" className="flex items-center mb-2">
                  <Globe className="w-4 h-4 mr-1" />
                  Language
                </Label>
                <Select value={language} onValueChange={setLanguage}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="English">English</SelectItem>
                    <SelectItem value="Spanish">Spanish</SelectItem>
                    <SelectItem value="French">French</SelectItem>
                    <SelectItem value="German">German</SelectItem>
                    <SelectItem value="Italian">Italian</SelectItem>
                    <SelectItem value="Chinese">Chinese</SelectItem>
                    <SelectItem value="Japanese">Japanese</SelectItem>
                    <SelectItem value="Other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="subject-areas">Subject Areas</Label>
              <Input
                id="subject-areas"
                value={subjectAreas}
                onChange={(e) => setSubjectAreas(e.target.value)}
                placeholder="Subject areas (comma-separated)..."
              />
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="w-4 h-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-2 pt-4">
            <Button variant="outline" onClick={onClose} disabled={uploading}>
              Cancel
            </Button>
            <Button
              onClick={handleUpload}
              disabled={!file || !title.trim() || uploading}
              className="bg-blue-600 hover:bg-blue-700"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4 mr-2" />
                  Upload Book
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default BookUploadModal
