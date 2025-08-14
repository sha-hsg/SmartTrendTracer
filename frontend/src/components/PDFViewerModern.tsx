import React, { useState, useCallback, useEffect } from 'react'
import { Document, Page, pdfjs } from 'react-pdf'
import 'react-pdf/dist/Page/AnnotationLayer.css'
import 'react-pdf/dist/Page/TextLayer.css'

// Configure PDF.js worker - use the version that matches react-pdf
pdfjs.GlobalWorkerOptions.workerSrc = `//unpkg.com/pdfjs-dist@${pdfjs.version}/build/pdf.worker.min.mjs`
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Download,
  FileText,
  Maximize2,
  Minimize2,
  Loader2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { cn } from '@/lib/utils'

// PDF viewing without worker - simpler and avoids CORS issues

interface PDFViewerModernProps {
  pdfUrl: string
  paperId: number
  onTextSelect?: (text: string, pageNumber: number) => void
  className?: string
}

const PDFViewerModern: React.FC<PDFViewerModernProps> = ({
  pdfUrl,
  paperId,
  onTextSelect,
  className
}) => {
  const [numPages, setNumPages] = useState<number | null>(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [scale, setScale] = useState(1.0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pageInput, setPageInput] = useState('1')
  const [selectedText, setSelectedText] = useState('')

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setLoading(false)
    setError(null)
  }

  const onDocumentLoadError = (error: Error) => {
    // Ignore fake worker warnings and still try to load
    if (error.message?.includes('fake worker') || error.message?.includes('Setting up fake worker')) {
      console.info('Using fallback PDF rendering (no worker)')
      // Don't set error for worker issues, PDF can still render
    } else {
      console.error('Error loading PDF:', error)
      setError('Failed to load PDF. Please try again.')
    }
    setLoading(false)
  }

  const changePage = (offset: number) => {
    const newPage = pageNumber + offset
    if (newPage >= 1 && newPage <= (numPages || 1)) {
      setPageNumber(newPage)
      setPageInput(newPage.toString())
    }
  }

  const goToPage = () => {
    const page = parseInt(pageInput)
    if (!isNaN(page) && page >= 1 && page <= (numPages || 1)) {
      setPageNumber(page)
    } else {
      setPageInput(pageNumber.toString())
    }
  }

  const handleZoomIn = () => {
    setScale(prev => Math.min(prev + 0.25, 3.0))
  }

  const handleZoomOut = () => {
    setScale(prev => Math.max(prev - 0.25, 0.5))
  }

  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection()
    if (selection && selection.toString().trim()) {
      const text = selection.toString().trim()
      setSelectedText(text)
      
      if (onTextSelect) {
        onTextSelect(text, pageNumber)
      }
    }
  }, [pageNumber, onTextSelect])

  const toggleFullscreen = () => {
    setIsFullscreen(prev => !prev)
  }

  const handleDownload = () => {
    window.open(pdfUrl, '_blank')
  }

  return (
    <div 
      className={cn(
        "flex flex-col h-full",
        isFullscreen && "fixed inset-0 z-50 bg-white",
        className
      )}
    >
      {/* Toolbar */}
      <Card className="p-3 mb-4 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => changePage(-1)}
            disabled={pageNumber <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          
          <div className="flex items-center gap-1">
            <Input
              type="text"
              value={pageInput}
              onChange={(e) => setPageInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && goToPage()}
              className="w-12 h-8 text-center"
            />
            <span className="text-sm text-gray-500">
              / {numPages || '?'}
            </span>
          </div>
          
          <Button
            size="sm"
            variant="outline"
            onClick={() => changePage(1)}
            disabled={pageNumber >= (numPages || 1)}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={handleZoomOut}
            disabled={scale <= 0.5}
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          
          <span className="text-sm text-gray-600 min-w-[60px] text-center">
            {Math.round(scale * 100)}%
          </span>
          
          <Button
            size="sm"
            variant="outline"
            onClick={handleZoomIn}
            disabled={scale >= 3.0}
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={toggleFullscreen}
          >
            {isFullscreen ? (
              <Minimize2 className="h-4 w-4" />
            ) : (
              <Maximize2 className="h-4 w-4" />
            )}
          </Button>
          
          <Button
            size="sm"
            variant="outline"
            onClick={handleDownload}
          >
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </Card>

      {/* PDF Content */}
      <div 
        className="flex-1 overflow-auto bg-gray-100 rounded-lg"
        onMouseUp={handleTextSelection}
      >
        {error ? (
          <Alert className="m-4 bg-red-50 border-red-200">
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        ) : (
          <div className="flex justify-center p-4">
            <Document
              file={pdfUrl}
              onLoadSuccess={onDocumentLoadSuccess}
              onLoadError={onDocumentLoadError}
              loading={
                <div className="flex flex-col items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
                  <p className="text-gray-600">Loading PDF...</p>
                </div>
              }
            >
              <Page 
                pageNumber={pageNumber} 
                scale={scale}
                renderTextLayer={true}
                renderAnnotationLayer={true}
                className="shadow-lg"
              />
            </Document>
          </div>
        )}
      </div>

      {/* Selected Text Display */}
      {selectedText && (
        <Card className="mt-2 p-2 bg-yellow-50 border-yellow-200">
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-700 truncate flex-1">
              Selected: {selectedText.substring(0, 100)}...
            </p>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setSelectedText('')}
            >
              Clear
            </Button>
          </div>
        </Card>
      )}
    </div>
  )
}

export default PDFViewerModern