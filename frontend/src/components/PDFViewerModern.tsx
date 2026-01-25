import React, { useState, useCallback, useEffect, useRef, useMemo } from 'react'
import ReactDOM from 'react-dom'
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
  Maximize2,
  Minimize2,
  Loader2,
  Highlighter,
  Tag,
  Copy,
  MessageSquare
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

// PDF viewing without worker - simpler and avoids CORS issues

interface PDFViewerModernProps {
  pdfUrl: string
  paperId: string | number  // Support both MongoDB ObjectId strings and legacy integer IDs
  onTextSelect?: (text: string, pageNumber: number) => void
  onTagCreate?: (tag: string) => Promise<void>
  className?: string
}

const PDFViewerModern: React.FC<PDFViewerModernProps> = React.memo(({
  pdfUrl,
  // paperId is in props for interface compatibility but not currently used inside component
  onTextSelect,
  onTagCreate,
  className
}) => {
  const [numPages, setNumPages] = useState<number | null>(null)
  const [pageNumber, setPageNumber] = useState(1)
  const [scale, setScale] = useState(1.0)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [_loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [pageInput, setPageInput] = useState('1')
  const [selectedText, setSelectedText] = useState('')
  const [showContextMenu, setShowContextMenu] = useState(false)
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 })
  const [showTagDialog, setShowTagDialog] = useState(false)
  const [tagText, setTagText] = useState('')
  const [creatingTag, setCreatingTag] = useState(false)
  const selectedTextRef = useRef<string>('')

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages)
    setLoading(false)
    setError(null)
  }, [])

  const onDocumentLoadError = useCallback((error: any) => {
    // Ignore fake worker warnings and still try to load
    if (error.message?.includes('fake worker') || error.message?.includes('Setting up fake worker')) {
      console.info('Using fallback PDF rendering (no worker)')
      // Don't set error for worker issues, PDF can still render
    } else if (error.status === 404 || error.message?.includes('404')) {
      setError('PDF file not available for this paper. The paper may need to be re-imported or the PDF file may not have been uploaded.')
    } else if (error.message?.includes('Invalid PDF structure')) {
      setError('This PDF file appears to be corrupted or invalid. This can happen when the PDF download failed or the file is not actually a PDF. Please try re-importing this paper.')
    } else {
      console.error('Error loading PDF:', error)
      setError('Failed to load PDF. Please try again.')
    }
    setLoading(false)
  }, [])

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

  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    
    // Get current selection
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      return
    }
    
    const text = selection.toString().trim()
    setSelectedText(text)
    selectedTextRef.current = text
    
    // Set context menu position
    const viewportHeight = window.innerHeight
    const menuHeight = 200 // Approximate menu height
    
    let menuY = e.clientY
    if (e.clientY + menuHeight > viewportHeight) {
      menuY = e.clientY - menuHeight
    }
    
    setContextMenuPosition({ x: e.clientX, y: menuY })
    setShowContextMenu(true)
  }, [])

  const handleMenuAction = (action: string) => {
    const text = selectedTextRef.current
    if (!text) return
    
    switch (action) {
      case 'copy':
        navigator.clipboard.writeText(text)
        break
      case 'snippet':
        if (onTextSelect) {
          onTextSelect(text, pageNumber)
        }
        break
      case 'highlight':
        // Could be extended to highlight in PDF
        console.log('Highlight:', text)
        break
      case 'tag':
        setTagText(text.trim())
        setShowTagDialog(true)
        break
    }
    
    setShowContextMenu(false)
  }

  const handleCreateTag = async () => {
    if (!tagText.trim() || !onTagCreate) return
    
    setCreatingTag(true)
    try {
      await onTagCreate(tagText.trim())
      setShowTagDialog(false)
      setTagText('')
    } catch (error) {
      console.error('Error creating tag:', error)
    } finally {
      setCreatingTag(false)
    }
  }

  const handleTagDialogClose = () => {
    setShowTagDialog(false)
    setTagText('')
    setCreatingTag(false)
  }

  // Close context menu on click outside
  useEffect(() => {
    const handleClickOutside = (_e: MouseEvent) => {
      if (showContextMenu) {
        setShowContextMenu(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showContextMenu])

  const toggleFullscreen = () => {
    setIsFullscreen(prev => !prev)
  }

  const handleDownload = () => {
    window.open(pdfUrl, '_blank')
  }

  // Memoize Document options to prevent "options" prop changed warnings
  const documentOptions = useMemo(() => ({
    cMapUrl: 'cmaps/',
    cMapPacked: true,
  }), [])

  // Memoize loading component
  const loadingComponent = useMemo(() => (
    <div className="flex flex-col items-center justify-center py-12">
      <Loader2 className="h-8 w-8 animate-spin text-blue-600 mb-4" />
      <p className="text-gray-600">Loading PDF...</p>
    </div>
  ), [])

  const documentComponent = useMemo(() => (
    <Document
      file={pdfUrl}
      onLoadSuccess={onDocumentLoadSuccess}
      onLoadError={onDocumentLoadError}
      loading={loadingComponent}
      options={documentOptions}
    >
      <Page 
        pageNumber={pageNumber} 
        scale={scale}
        renderTextLayer={true}
        renderAnnotationLayer={true}
        className="shadow-lg"
        loading=""
      />
    </Document>
  ), [pdfUrl, pageNumber, scale, onDocumentLoadSuccess, onDocumentLoadError, loadingComponent, documentOptions])

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
        onContextMenu={handleContextMenu}
      >
        {error ? (
          <Alert className="m-4 bg-red-50 border-red-200">
            <AlertDescription className="text-red-800">
              {error}
            </AlertDescription>
          </Alert>
        ) : (
          <div className="flex justify-center p-4">
            {documentComponent}
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

      {/* Context Menu Portal */}
      {showContextMenu && ReactDOM.createPortal(
        <div
          className="fixed z-[9999] bg-white rounded-lg shadow-2xl border border-gray-200 py-1 min-w-[180px]"
          style={{
            left: `${contextMenuPosition.x}px`,
            top: `${contextMenuPosition.y}px`,
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-blue-50 flex items-center gap-2 transition-colors"
            onClick={() => handleMenuAction('copy')}
          >
            <Copy className="h-4 w-4 text-blue-600" />
            <span>Copy Text</span>
          </button>
          
          <div className="border-t border-gray-100 my-1" />
          
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-green-50 flex items-center gap-2 transition-colors"
            onClick={() => handleMenuAction('snippet')}
          >
            <MessageSquare className="h-4 w-4 text-green-600" />
            <span>Create Snippet</span>
          </button>
          
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-yellow-50 flex items-center gap-2 transition-colors"
            onClick={() => handleMenuAction('highlight')}
          >
            <Highlighter className="h-4 w-4 text-yellow-600" />
            <span>Highlight</span>
          </button>
          
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-purple-50 flex items-center gap-2 transition-colors"
            onClick={() => handleMenuAction('tag')}
          >
            <Tag className="h-4 w-4 text-purple-600" />
            <span>Create Tag</span>
          </button>
        </div>,
        document.body
      )}

      {/* Tag Creation Dialog */}
      <Dialog open={showTagDialog} onOpenChange={handleTagDialogClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Tag className="h-5 w-5 text-purple-600" />
              Create Tag
            </DialogTitle>
            <DialogDescription>
              Edit the selected text and create a tag for this paper.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label htmlFor="tagText" className="block text-sm font-medium text-gray-700 mb-2">
                Tag Text
              </label>
              <Input
                id="tagText"
                value={tagText}
                onChange={(e) => setTagText(e.target.value)}
                placeholder="Enter tag text..."
                className="w-full"
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !creatingTag) {
                    handleCreateTag()
                  }
                }}
                disabled={creatingTag}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={handleTagDialogClose}
                disabled={creatingTag}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateTag}
                disabled={!tagText.trim() || creatingTag}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {creatingTag ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Tag'
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
})

PDFViewerModern.displayName = 'PDFViewerModern'

export default PDFViewerModern