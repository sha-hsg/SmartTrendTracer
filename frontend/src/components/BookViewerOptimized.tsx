import React, { useState, useCallback, useMemo, useRef, useEffect } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import JSZip from 'jszip'
import remarkGfm from 'remark-gfm'
import {
  ArrowLeft,
  Download,
  User,
  Building2,
  Calendar,
  Hash,
  Globe,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertTriangle,
  PlayCircle,
  ExternalLink,
  X,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

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

interface BookViewerOptimizedProps {
  book: Book
  onBack: () => void
  onBookUpdate?: (book: Book) => void
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

// Enhanced Processing Status Component
interface ProcessingStatusBarProps {
  status: string
  processor?: string
  processingError?: string
  processingMessage?: string
  isProcessingAction: boolean
  onQueueProcessing: (method: 'marker' | 'mineru') => void
  onDirectProcessing: (method: 'marker' | 'mineru') => void
}

const ProcessingStatusBar: React.FC<ProcessingStatusBarProps> = ({
  status,
  processor,
  processingError,
  processingMessage,
  isProcessingAction,
  onQueueProcessing,
  onDirectProcessing
}) => {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          color: 'bg-green-50 border-green-200',
          icon: <CheckCircle className="w-5 h-5 text-green-600" />,
          message: 'Content extraction completed',
          priority: 'low',
          actions: null
        }
      case 'processing':
        return {
          color: 'bg-blue-50 border-blue-200',
          icon: <Loader2 className="w-5 h-5 animate-spin text-blue-600" />,
          message: 'Processing in progress...',
          priority: 'high',
          actions: null
        }
      case 'queued':
        return {
          color: 'bg-purple-50 border-purple-200',
          icon: <Clock className="w-5 h-5 text-purple-600" />,
          message: 'Queued for processing',
          priority: 'medium',
          actions: null
        }
      case 'failed':
        return {
          color: 'bg-red-50 border-red-200',
          icon: <XCircle className="w-5 h-5 text-red-600" />,
          message: 'Processing failed',
          priority: 'high',
          actions: (
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => onQueueProcessing('marker')}>
                <PlayCircle className="w-4 h-4 mr-1" />
                Retry with Marker
              </Button>
              <Button size="sm" variant="outline" onClick={() => onQueueProcessing('mineru')}>
                <PlayCircle className="w-4 h-4 mr-1" />
                Retry with MinerU
              </Button>
            </div>
          )
        }
      case 'pending':
      default:
        return {
          color: 'bg-yellow-50 border-yellow-200',
          icon: <AlertCircle className="w-5 h-5 text-yellow-600" />,
          message: 'Content extraction needed',
          priority: 'high',
          actions: (
            <div className="flex gap-2">
              <Button size="sm" onClick={() => onDirectProcessing('marker')}>
                <PlayCircle className="w-4 h-4 mr-1" />
                Process with Marker
              </Button>
              <Button size="sm" variant="outline" onClick={() => onQueueProcessing('marker')}>
                Queue Marker
              </Button>
            </div>
          )
        }
    }
  }

  const config = getStatusConfig(status)

  return (
    <div className={`border rounded-lg p-4 mb-4 ${config.color}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          {config.icon}
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-1">
              <span className="font-medium text-sm">{config.message}</span>
              {processor && (
                <Badge variant="outline" className="text-xs">
                  {processor.toUpperCase()}
                </Badge>
              )}
            </div>

            {processingMessage && (
              <p className="text-xs text-blue-600 mb-2">{processingMessage}</p>
            )}

            {processingError && (
              <p className="text-xs text-red-600 mb-2 flex items-center">
                <AlertTriangle className="w-3 h-3 mr-1" />
                {processingError}
              </p>
            )}
          </div>
        </div>

        {config.actions && !isProcessingAction && (
          <div className="ml-4">
            {config.actions}
          </div>
        )}
      </div>

      {isProcessingAction && (
        <div className="mt-2 flex items-center text-xs text-gray-500">
          <Loader2 className="w-3 h-3 animate-spin mr-1" />
          Processing action...
        </div>
      )}
    </div>
  )
}

const BookViewerOptimized: React.FC<BookViewerOptimizedProps> = ({ book, onBack, onBookUpdate }) => {
  const [activeTab, setActiveTab] = useState('details')
  const [bookContent, setBookContent] = useState<string | null>(null)
  const [loadingContent, setLoadingContent] = useState(false)
  const [contentError, setContentError] = useState<string | null>(null)
  const [processingStatus, setProcessingStatus] = useState<string>(book.processing_status || 'uploaded')
  const [processorUsed, setProcessorUsed] = useState<string | undefined>(book.processing_method || book.processor)
  const [bookConcepts, setBookConcepts] = useState<Array<{ concept_id?: string; _id?: string; display_name?: string; slug?: string; name?: string }>>(book.concepts || [])
  const [conceptIds, setConceptIds] = useState<string[]>(book.concept_ids || [])
  const [processingMessage, setProcessingMessage] = useState<string | null>(null)
  const [processingError, setProcessingError] = useState<string | null>(null)
  const [isProcessingAction, setIsProcessingAction] = useState(false)
  const [newConceptText, setNewConceptText] = useState('')
  const [conceptError, setConceptError] = useState<string | null>(null)
  const [addingConcept, setAddingConcept] = useState(false)

  // Paging system for large markdown
  const [markdownPages, setMarkdownPages] = useState<string[]>([])
  const [currentPage, setCurrentPage] = useState(0)
  const [isChangingPage, setIsChangingPage] = useState(false)

  const markdownContainerRef = useRef<HTMLDivElement>(null)

  const refreshBookDetails = useCallback(async (retryCount = 0) => {
    try {
      const response = await axios.get(`/api/books/${book._id}`)
      const updated: Book = response.data
      setProcessingStatus(updated.processing_status || 'uploaded')
      setProcessorUsed(updated.processing_method || updated.processor)
      setBookConcepts(updated.concepts || [])
      setConceptIds(updated.concept_ids || [])
      onBookUpdate?.(updated)
    } catch (error) {
      console.error('Failed to refresh book details', error)
      // Exponential backoff: don't retry immediately if server is busy during analysis
      if (retryCount < 2) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 5000) // Max 5s delay
        setTimeout(() => refreshBookDetails(retryCount + 1), delay)
      }
    }
  }, [book._id, onBookUpdate])

  useEffect(() => {
    // Only update state if values have actually changed to prevent infinite loops
    const newProcessingStatus = book.processing_status || 'uploaded'
    const newProcessorUsed = book.processing_method || book.processor
    const newBookConcepts = book.concepts || []
    const newConceptIds = book.concept_ids || []

    if (newProcessingStatus !== processingStatus) {
      setProcessingStatus(newProcessingStatus)
    }
    if (newProcessorUsed !== processorUsed) {
      setProcessorUsed(newProcessorUsed)
    }
    // Compare arrays by length and content
    if (JSON.stringify(newBookConcepts) !== JSON.stringify(bookConcepts)) {
      setBookConcepts(newBookConcepts)
    }
    if (JSON.stringify(newConceptIds) !== JSON.stringify(conceptIds)) {
      setConceptIds(newConceptIds)
    }
  }, [book.processing_status, book.processing_method, book.processor, book.concepts, book.concept_ids, processingStatus, processorUsed, bookConcepts, conceptIds])

  useEffect(() => {
    // Only call onBookUpdate if this component changed state locally (not from props)
    // Skip the update if we're just syncing from incoming props
    if (onBookUpdate) {
      const updatedBook = {
        ...book,
        processing_status: processingStatus,
        processing_method: processorUsed,
        processor: processorUsed,
        concepts: bookConcepts,
        concept_ids: conceptIds,
      }

      // Only update if something actually changed from the original book
      const hasChanges =
        processingStatus !== book.processing_status ||
        processorUsed !== (book.processing_method || book.processor) ||
        JSON.stringify(bookConcepts) !== JSON.stringify(book.concepts || []) ||
        JSON.stringify(conceptIds) !== JSON.stringify(book.concept_ids || [])

      if (hasChanges) {
        onBookUpdate(updatedBook)
      }
    }
  }, [processingStatus, processorUsed, bookConcepts, conceptIds, book, onBookUpdate])

  useEffect(() => {
    if (['queued', 'processing'].includes(processingStatus)) {
      const interval = setInterval(() => {
        refreshBookDetails()
      }, 15000) // Reduced frequency: 15s instead of 5s for better performance
      return () => {
        clearInterval(interval)
        console.log('Cleared book polling interval')
      }
    }
  }, [processingStatus, refreshBookDetails])

  // Create pages with smart overlap for better context
  const createPages = useCallback((content: string) => {
    if (!content || content.length < 15000) {
      // For small content, just use as single page
      setMarkdownPages([content])
      setCurrentPage(0)
      return
    }

    const pages = []
    const lines = content.split('\n')
    let currentPageContent = ''
    let currentPageSize = 0
    const targetPageSize = 15000 // ~15KB per page for books (larger than papers)
    const overlapSize = 3000 // ~3KB overlap between pages for context

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      const lineSize = line.length + 1 // +1 for newline

      // If adding this line would exceed page size, create new page
      if (currentPageSize + lineSize > targetPageSize && currentPageContent.trim()) {
        // Try to break at a logical point (heading, paragraph, etc.)
        if (line.startsWith('#') || line.trim() === '' || line.startsWith('---')) {
          pages.push(currentPageContent)

          // Create overlap by including last ~3KB of previous page
          const pageLines = currentPageContent.split('\n')
          let overlapContent = ''
          let overlapBytes = 0

          for (let j = pageLines.length - 1; j >= 0 && overlapBytes < overlapSize; j--) {
            const overlapLine = pageLines[j] + '\n'
            if (overlapBytes + overlapLine.length <= overlapSize) {
              overlapContent = overlapLine + overlapContent
              overlapBytes += overlapLine.length
            } else {
              break
            }
          }

          currentPageContent = overlapContent + line + '\n'
          currentPageSize = overlapContent.length + lineSize
        } else {
          currentPageContent += line + '\n'
          currentPageSize += lineSize
        }
      } else {
        currentPageContent += line + '\n'
        currentPageSize += lineSize
      }
    }

    // Add remaining content as final page
    if (currentPageContent.trim()) {
      pages.push(currentPageContent)
    }

    setMarkdownPages(pages)
    setCurrentPage(0) // Start with first page
  }, [])

  // Initialize pages when book content changes
  useEffect(() => {
    if (bookContent) {
      createPages(bookContent)
    }
  }, [bookContent, createPages])

  // Page navigation functions
  const goToNextPage = useCallback(() => {
    if (currentPage < markdownPages.length - 1) {
      setIsChangingPage(true)
      setCurrentPage(prev => prev + 1)

      // Scroll to top of content for new page
      setTimeout(() => {
        if (markdownContainerRef.current) {
          markdownContainerRef.current.scrollTop = 0
        }
        setIsChangingPage(false)
      }, 100)
    }
  }, [currentPage, markdownPages.length])

  const goToPreviousPage = useCallback(() => {
    if (currentPage > 0) {
      setIsChangingPage(true)
      setCurrentPage(prev => prev - 1)

      // Scroll to top of content for new page
      setTimeout(() => {
        if (markdownContainerRef.current) {
          markdownContainerRef.current.scrollTop = 0
        }
        setIsChangingPage(false)
      }, 100)
    }
  }, [currentPage])

  const goToPage = useCallback((pageNumber: number) => {
    if (pageNumber >= 0 && pageNumber < markdownPages.length && pageNumber !== currentPage) {
      setIsChangingPage(true)
      setCurrentPage(pageNumber)

      // Scroll to top of content for new page
      setTimeout(() => {
        if (markdownContainerRef.current) {
          markdownContainerRef.current.scrollTop = 0
        }
        setIsChangingPage(false)
      }, 100)
    }
  }, [currentPage, markdownPages.length])

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (markdownPages.length <= 1) return

      if (e.key === 'ArrowLeft' || e.key === 'PageUp') {
        e.preventDefault()
        goToPreviousPage()
      } else if (e.key === 'ArrowRight' || e.key === 'PageDown') {
        e.preventDefault()
        goToNextPage()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [goToNextPage, goToPreviousPage, markdownPages.length])

  // Load book content
  const loadBookContent = async () => {
    if (processingStatus !== 'completed') {
      setContentError('Book content is not available - processing may be pending')
      return
    }

    try {
      setLoadingContent(true)
      setContentError(null)
      const response = await axios.get(`/api/books/${book._id}/content`)
      setBookContent(response.data.content)
    } catch (error) {
      console.error('Error loading book content:', error)
      setContentError('Failed to load book content')
    } finally {
      setLoadingContent(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'content' && !bookContent) {
      loadBookContent()
    }
  }, [activeTab, bookContent, book._id, processingStatus])

  // Download markdown with images as ZIP
  const resolveApiUrl = useCallback((maybeRelativeUrl: string) => {
    if (!maybeRelativeUrl) return ''

    try {
      const base = axios.defaults.baseURL
        ? new URL(axios.defaults.baseURL, window.location.origin).toString()
        : window.location.origin
      return new URL(maybeRelativeUrl, base).toString()
    } catch (error) {
      return maybeRelativeUrl
    }
  }, [])

  const downloadMarkdownWithImages = async () => {
    if (!bookContent) return

    try {
      const zip = new JSZip()
      // Add markdown file
      const filename = `${book.title.replace(/[^a-zA-Z0-9]/g, '_')}.md`

      // Process markdown to use relative image paths
      let processedMarkdown = bookContent
      const imageRegex = /!\[([^\]]*)\]\((https?:\/\/[^)]+\/api\/books\/[^)]+)\)/g
      const images: Array<{url: string; filename: string}> = []

      // Extract image URLs and replace with relative paths
      processedMarkdown = processedMarkdown.replace(imageRegex, (match, alt, url) => {
        const imagePath = url.split('/').pop()
        const relativeImagePath = `images/${imagePath}`
        images.push({url, filename: imagePath})
        return `![${alt}](${relativeImagePath})`
      })

      zip.file(filename, processedMarkdown)

      // Download and add images to ZIP
      if (images.length > 0) {
        const imagesFolder = zip.folder('images')
        let successCount = 0
        let errorCount = 0

        for (const img of images) {
          try {
            const imageUrl = resolveApiUrl(img.url)
            if (!imageUrl) {
              console.warn(`Skipping image with empty URL: ${img.filename}`)
              errorCount++
              continue
            }

            const response = await axios.get(imageUrl, {
              responseType: 'blob',
              withCredentials: true
            })

            imagesFolder?.file(img.filename, response.data as Blob)
            successCount++
          } catch (error) {
            console.warn(`Error downloading image ${img.url}:`, error)
            errorCount++
          }
        }

        console.log(`Download summary: ${successCount} images successful, ${errorCount} failed`)
      }

      // Generate and download ZIP
      const content = await zip.generateAsync({ type: 'blob' })
      const downloadUrl = URL.createObjectURL(content)
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `${book.title.replace(/[^a-zA-Z0-9]/g, '_')}_with_images.zip`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(downloadUrl)

    } catch (error) {
      console.error('Error creating download:', error)
    }
  }

  const handleOpenOriginal = useCallback(() => {
    if (!book.file_url) return
    const resolved = resolveApiUrl(book.file_url)
    if (resolved) {
      window.open(resolved, '_blank', 'noopener')
    }
  }, [book.file_url, resolveApiUrl])

  const htmlTagComponents = useMemo(() => ({
    original: ({ children, ...props }: any) => (
      <span {...props} className={`font-semibold ${props.className ?? ''}`.trim()}>{children}</span>
    ),
    topic: ({ children, ...props }: any) => (
      <span {...props} className={`italic text-blue-600 ${props.className ?? ''}`.trim()}>{children}</span>
    ),
  } as any), [])

  const handleQueueProcessing = async (method: 'marker' | 'mineru') => {
    try {
      setIsProcessingAction(true)
      setProcessingError(null)
      setProcessingMessage(null)
      await axios.post(`/api/books/${book._id}/process`, {
        preferred_processor: method
      })
      setProcessingStatus('queued')
      setProcessorUsed(method)
      setProcessingMessage(`Book queued for ${method.toUpperCase()}. Ensure the background worker is running.`)
      await refreshBookDetails()
    } catch (error: any) {
      console.error('Failed to queue processing', error)
      setProcessingError(error.response?.data?.detail || 'Failed to queue processing')
    } finally {
      setIsProcessingAction(false)
    }
  }

  const handleProcessDirect = async (method: 'marker' | 'mineru' | 'auto') => {
    try {
      setIsProcessingAction(true)
      setProcessingError(null)
      setProcessingMessage('Processing started...')
      await axios.post(`/api/books/${book._id}/process-direct`, null, {
        params: { preferred_processor: method }
      })
      setProcessingStatus('processing')
      setProcessorUsed(method)
      await refreshBookDetails()
    } catch (error: any) {
      console.error('Failed to process book', error)
      setProcessingError(error.response?.data?.detail || 'Failed to start direct processing')
      setProcessingMessage(null)
    } finally {
      setIsProcessingAction(false)
    }
  }

  const handleAddConcept = async () => {
    const text = newConceptText.trim()
    if (!text) {
      setConceptError('Enter a concept name')
      return
    }
    try {
      setConceptError(null)
      setAddingConcept(true)
      await axios.post(`/api/books/${book._id}/concepts`, {
        concept_name: text
      })
      setNewConceptText('')
      await refreshBookDetails()
    } catch (error: any) {
      console.error('Failed to add concept', error)
      setConceptError(error.response?.data?.detail || 'Failed to add concept')
    } finally {
      setAddingConcept(false)
    }
  }

  const handleRemoveConcept = async (conceptId: string) => {
    try {
      await axios.delete(`/api/books/${book._id}/concepts/${conceptId}`)
      await refreshBookDetails()
    } catch (error) {
      console.error('Failed to remove concept', error)
    }
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

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Book Details */}
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
                            handleRemoveConcept(concept.concept_id || concept._id!)
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
                onChange={(e) => setNewConceptText(e.target.value)}
                placeholder="Add concept"
                className="text-sm"
              />
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddConcept}
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

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full flex flex-col">
          <div className="border-b bg-white px-4">
            <TabsList>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="content">Content</TabsTrigger>
              {book.summary && <TabsTrigger value="summary">Summary</TabsTrigger>}
              {book.table_of_contents && book.table_of_contents.length > 0 && (
                <TabsTrigger value="toc">Table of Contents</TabsTrigger>
              )}
            </TabsList>
          </div>

          <div className="flex-1 overflow-hidden">
            <TabsContent value="details" className="h-full p-4">
              <Card>
                <CardHeader>
                  <CardTitle>Book Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {book.summary && (
                      <div>
                        <h3 className="font-medium mb-2">Summary</h3>
                        <p className="text-sm text-gray-700">{book.summary}</p>
                      </div>
                    )}

                    {book.key_themes && book.key_themes.length > 0 && (
                      <div>
                        <h3 className="font-medium mb-2">Key Themes</h3>
                        <div className="flex flex-wrap gap-2">
                          {book.key_themes.map((theme, idx) => (
                            <Badge key={idx} variant="outline" className="bg-orange-50">
                              {theme}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}


                    {book.file_url && (
                      <div>
                        <h3 className="font-medium mb-2">Original File</h3>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={handleOpenOriginal}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          View {book.file_type?.toUpperCase() || 'File'}
                        </Button>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="content" className="h-full">
              <div className="h-full flex flex-col">
                {/* Enhanced Processing Status */}
                <div className="px-4 pt-4">
                  <ProcessingStatusBar
                    status={processingStatus}
                    processor={processorUsed}
                    processingError={processingError ?? undefined}
                    processingMessage={processingMessage ?? undefined}
                    isProcessingAction={isProcessingAction}
                    onQueueProcessing={handleQueueProcessing}
                    onDirectProcessing={handleProcessDirect}
                  />
                </div>

                {bookContent && markdownPages.length > 1 && (
                  <div className="bg-blue-50 border-b px-4 py-2">
                    <div className="flex items-center justify-between text-sm text-blue-700">
                      <span>Large Document Mode - Page {currentPage + 1} of {markdownPages.length}</span>
                      <span className="text-xs">Use ← → keys or buttons to navigate</span>
                    </div>
                  </div>
                )}

                <div
                  ref={markdownContainerRef}
                  className="h-full w-full bg-gray-50 overflow-y-auto"
                >
                  {loadingContent ? (
                    <div className="flex items-center justify-center h-64">
                      <Loader2 className="w-6 h-6 animate-spin mr-2" />
                      <span>Loading book content...</span>
                    </div>
                  ) : contentError ? (
                    <div className="flex flex-col items-center justify-center h-64 text-center p-8">
                      <AlertTriangle className="w-12 h-12 text-yellow-500 mb-4" />
                      <h3 className="text-lg font-medium text-gray-900 mb-2">Content Not Available</h3>
                      <p className="text-gray-600 mb-4">{contentError}</p>
                      {(processingStatus === 'pending' || processingStatus === 'queued') && (
                        <div className="flex items-center text-sm text-blue-600">
                          <PlayCircle className="w-4 h-4 mr-1" />
                          Processing may be in progress
                        </div>
                      )}
                      {book.file_url && (
                        <Button
                          className="mt-4"
                          variant="outline"
                          size="sm"
                          onClick={handleOpenOriginal}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Open Original {book.file_type?.toUpperCase() || 'File'}
                        </Button>
                      )}
                    </div>
                  ) : markdownPages.length > 0 ? (
                    <div className="p-6 max-w-4xl mx-auto">
                      <div className="bg-white rounded-lg shadow-sm p-6">
                        <div className="flex items-center justify-between mb-6">
                          <h2 className="text-xl font-bold">{book.title}</h2>
                          <Button onClick={downloadMarkdownWithImages} variant="outline" size="sm">
                            <Download className="w-4 h-4 mr-2" />
                            Download
                          </Button>
                        </div>

                        <div className="prose prose-sm max-w-none">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={htmlTagComponents}
                          >
                            {markdownPages[currentPage] || ''}
                          </ReactMarkdown>

                          {/* Page loading indicator */}
                          {isChangingPage && (
                            <div className="flex items-center justify-center py-8">
                              <Loader2 className="h-6 w-6 animate-spin text-blue-500" />
                              <span className="ml-2 text-gray-600">Loading page...</span>
                            </div>
                          )}
                        </div>

                        {/* Page Navigation */}
                        {markdownPages.length > 1 && (
                          <div className="mt-8 pt-6 border-t border-gray-200">
                            <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                              <span>
                                Page {currentPage + 1} of {markdownPages.length}
                              </span>
                              <span className="text-xs text-gray-400">
                                Use ← → keys or buttons to navigate
                              </span>
                            </div>

                            {/* Page progress bar */}
                            <div className="bg-gray-200 rounded-full h-2 mb-6">
                              <div
                                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                                style={{
                                  width: `${((currentPage + 1) / markdownPages.length) * 100}%`,
                                }}
                              />
                            </div>

                            {/* Navigation buttons */}
                            <div className="flex items-center justify-between gap-4">
                              <Button
                                onClick={goToPreviousPage}
                                disabled={currentPage === 0 || isChangingPage}
                                variant="outline"
                                className="flex-1 max-w-40"
                              >
                                {isChangingPage ? (
                                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                ) : (
                                  <ChevronLeft className="h-4 w-4 mr-2" />
                                )}
                                Previous
                              </Button>

                              {/* Page selector */}
                              <div className="flex items-center gap-1 flex-shrink-0">
                                {markdownPages.map((_, index) => {
                                  // Show page dots for small numbers, or abbreviated for large
                                  if (markdownPages.length <= 7) {
                                    return (
                                      <button
                                        key={index}
                                        onClick={() => goToPage(index)}
                                        disabled={isChangingPage}
                                        className={`w-8 h-8 rounded-full text-xs font-medium transition-colors ${
                                          index === currentPage
                                            ? 'bg-blue-600 text-white'
                                            : 'bg-gray-200 text-gray-600 hover:bg-gray-300'
                                        }`}
                                      >
                                        {index + 1}
                                      </button>
                                    )
                                  } else {
                                    // For many pages, show dots with current page
                                    if (index === currentPage) {
                                      return (
                                        <span
                                          key={index}
                                          className="w-8 h-8 rounded-full bg-blue-600 text-white text-xs font-medium flex items-center justify-center"
                                        >
                                          {index + 1}
                                        </span>
                                      )
                                    } else if (
                                      index === 0 ||
                                      index === markdownPages.length - 1 ||
                                      Math.abs(index - currentPage) <= 1
                                    ) {
                                      return (
                                        <button
                                          key={index}
                                          onClick={() => goToPage(index)}
                                          disabled={isChangingPage}
                                          className="w-8 h-8 rounded-full bg-gray-200 text-gray-600 hover:bg-gray-300 text-xs font-medium transition-colors"
                                        >
                                          {index + 1}
                                        </button>
                                      )
                                    } else if (Math.abs(index - currentPage) === 2) {
                                      return <span key={index} className="text-gray-400">...</span>
                                    }
                                    return null
                                  }
                                })}
                              </div>

                              <Button
                                onClick={goToNextPage}
                                disabled={currentPage === markdownPages.length - 1 || isChangingPage}
                                variant="outline"
                                className="flex-1 max-w-40"
                              >
                                Next
                                {isChangingPage ? (
                                  <Loader2 className="h-4 w-4 ml-2 animate-spin" />
                                ) : (
                                  <ChevronRight className="h-4 w-4 ml-2" />
                                )}
                              </Button>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-center h-64">
                      <span>No content available</span>
                    </div>
                  )}
                </div>
              </div>
            </TabsContent>

            {book.summary && (
              <TabsContent value="summary" className="h-full p-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Book Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm max-w-none">
                      {book.summary}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            )}

            {book.table_of_contents && book.table_of_contents.length > 0 && (
              <TabsContent value="toc" className="h-full p-4">
                <Card>
                  <CardHeader>
                    <CardTitle>Table of Contents</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {book.table_of_contents.map((item, idx) => (
                        <div key={idx} className="flex justify-between items-center py-2 border-b border-gray-100 last:border-b-0">
                          <span className="font-medium">{item.chapter}</span>
                          <span className="text-sm text-gray-500">Page {item.page}</span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </TabsContent>
            )}
          </div>
        </Tabs>
      </div>
    </div>
  )
}

export default BookViewerOptimized
