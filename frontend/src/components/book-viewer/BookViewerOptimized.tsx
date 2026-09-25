import React, { useState, useCallback, useEffect } from 'react'
import http from '@/services/http'
import JSZip from 'jszip'
import { useBookPagination } from '../BookViewer/hooks/useBookPagination'
import BookMetadataPanel from './BookMetadataPanel'
import BookContentViewer from './BookContentViewer'

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

  const {
    markdownPages,
    currentPage,
    isChangingPage,
    markdownContainerRef,
    goToNextPage,
    goToPreviousPage,
    goToPage,
  } = useBookPagination({ bookContent })

  const refreshBookDetails = useCallback(async (retryCount = 0) => {
    try {
      const response = await http.get(`/api/books/${book._id}`)
      const updated: Book = response.data
      setProcessingStatus(updated.processing_status || 'uploaded')
      setProcessorUsed(updated.processing_method || updated.processor)
      setBookConcepts(updated.concepts || [])
      setConceptIds(updated.concept_ids || [])
      onBookUpdate?.(updated)
    } catch (error) {
      console.error('Failed to refresh book details', error)
      if (retryCount < 2) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 5000)
        setTimeout(() => refreshBookDetails(retryCount + 1), delay)
      }
    }
  }, [book._id, onBookUpdate])

  useEffect(() => {
    const newProcessingStatus = book.processing_status || 'uploaded'
    const newProcessorUsed = book.processing_method || book.processor
    const newBookConcepts = book.concepts || []
    const newConceptIds = book.concept_ids || []

    let changed = false

    if (newProcessingStatus !== processingStatus) {
      setProcessingStatus(newProcessingStatus)
      changed = true
    }
    if (newProcessorUsed !== processorUsed) {
      setProcessorUsed(newProcessorUsed)
      changed = true
    }
    if (JSON.stringify(newBookConcepts) !== JSON.stringify(bookConcepts)) {
      setBookConcepts(newBookConcepts)
      changed = true
    }
    if (JSON.stringify(newConceptIds) !== JSON.stringify(conceptIds)) {
      setConceptIds(newConceptIds)
      changed = true
    }

    if (!changed && onBookUpdate) {
      const hasLocalChanges =
        processingStatus !== (book.processing_status || 'uploaded') ||
        processorUsed !== (book.processing_method || book.processor) ||
        JSON.stringify(bookConcepts) !== JSON.stringify(book.concepts || []) ||
        JSON.stringify(conceptIds) !== JSON.stringify(book.concept_ids || [])

      if (hasLocalChanges) {
        onBookUpdate({
          ...book,
          processing_status: processingStatus,
          processing_method: processorUsed,
          processor: processorUsed,
          concepts: bookConcepts,
          concept_ids: conceptIds,
        })
      }
    }
  }, [book.processing_status, book.processing_method, book.processor, book.concepts, book.concept_ids, processingStatus, processorUsed, bookConcepts, conceptIds, onBookUpdate])

  useEffect(() => {
    if (['queued', 'processing'].includes(processingStatus)) {
      const interval = setInterval(() => {
        refreshBookDetails()
      }, 15000)
      return () => {
        clearInterval(interval)
        console.log('Cleared book polling interval')
      }
    }
  }, [processingStatus, refreshBookDetails])

  const loadBookContent = async () => {
    if (processingStatus !== 'completed') {
      setContentError('Book content is not available - processing may be pending')
      return
    }

    try {
      setLoadingContent(true)
      setContentError(null)
      const response = await http.get(`/api/books/${book._id}/content`)
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

  const resolveApiUrl = useCallback((maybeRelativeUrl: string) => {
    if (!maybeRelativeUrl) return ''

    try {
      const base = http.defaults.baseURL
        ? new URL(http.defaults.baseURL, window.location.origin).toString()
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
      const filename = `${book.title.replace(/[^a-zA-Z0-9]/g, '_')}.md`

      let processedMarkdown = bookContent
      const imageRegex = /!\[([^\]]*)\]\((https?:\/\/[^)]+\/api\/books\/[^)]+)\)/g
      const images: Array<{url: string; filename: string}> = []

      processedMarkdown = processedMarkdown.replace(imageRegex, (_match, alt, url) => {
        const imagePath = url.split('/').pop()
        const relativeImagePath = `images/${imagePath}`
        images.push({url, filename: imagePath})
        return `![${alt}](${relativeImagePath})`
      })

      zip.file(filename, processedMarkdown)

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

            const response = await http.get(imageUrl, {
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

  const handleQueueProcessing = async (method: 'marker' | 'mineru') => {
    try {
      setIsProcessingAction(true)
      setProcessingError(null)
      setProcessingMessage(null)
      await http.post(`/api/books/${book._id}/process`, {
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
      await http.post(`/api/books/${book._id}/process-direct`, null, {
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
      await http.post(`/api/books/${book._id}/concepts`, {
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
      await http.delete(`/api/books/${book._id}/concepts/${conceptId}`)
      await refreshBookDetails()
    } catch (error) {
      console.error('Failed to remove concept', error)
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      <BookMetadataPanel
        book={book}
        onBack={onBack}
        bookConcepts={bookConcepts}
        newConceptText={newConceptText}
        onNewConceptTextChange={setNewConceptText}
        onAddConcept={handleAddConcept}
        onRemoveConcept={handleRemoveConcept}
        addingConcept={addingConcept}
        conceptError={conceptError}
      />

      <BookContentViewer
        book={book}
        activeTab={activeTab}
        onActiveTabChange={setActiveTab}
        bookContent={bookContent}
        loadingContent={loadingContent}
        contentError={contentError}
        processingStatus={processingStatus}
        processorUsed={processorUsed}
        processingError={processingError}
        processingMessage={processingMessage}
        isProcessingAction={isProcessingAction}
        onQueueProcessing={handleQueueProcessing}
        onDirectProcessing={handleProcessDirect}
        onOpenOriginal={handleOpenOriginal}
        onDownloadMarkdown={downloadMarkdownWithImages}
        markdownPages={markdownPages}
        currentPage={currentPage}
        isChangingPage={isChangingPage}
        markdownContainerRef={markdownContainerRef}
        goToNextPage={goToNextPage}
        goToPreviousPage={goToPreviousPage}
        goToPage={goToPage}
      />
    </div>
  )
}

export default BookViewerOptimized
