import React, { useMemo } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import {
  Download,
  ChevronLeft,
  ChevronRight,
  Loader2,
  AlertTriangle,
  PlayCircle,
  ExternalLink,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
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

interface BookContentViewerProps {
  book: Book
  activeTab: string
  onActiveTabChange: (tab: string) => void
  bookContent: string | null
  loadingContent: boolean
  contentError: string | null
  processingStatus: string
  processorUsed?: string
  processingError: string | null
  processingMessage: string | null
  isProcessingAction: boolean
  onQueueProcessing: (method: 'marker' | 'mineru') => void
  onDirectProcessing: (method: 'marker' | 'mineru') => void
  onOpenOriginal: () => void
  onDownloadMarkdown: () => void
  markdownPages: string[]
  currentPage: number
  isChangingPage: boolean
  markdownContainerRef: React.Ref<HTMLDivElement>
  goToNextPage: () => void
  goToPreviousPage: () => void
  goToPage: (page: number) => void
}

const BookContentViewer: React.FC<BookContentViewerProps> = ({
  book,
  activeTab,
  onActiveTabChange,
  bookContent,
  loadingContent,
  contentError,
  processingStatus,
  processorUsed,
  processingError,
  processingMessage,
  isProcessingAction,
  onQueueProcessing,
  onDirectProcessing,
  onOpenOriginal,
  onDownloadMarkdown,
  markdownPages,
  currentPage,
  isChangingPage,
  markdownContainerRef,
  goToNextPage,
  goToPreviousPage,
  goToPage,
}) => {
  const htmlTagComponents = useMemo(() => ({
    original: ({ children, ...props }: any) => (
      <span {...props} className={`font-semibold ${props.className ?? ''}`.trim()}>{children}</span>
    ),
    topic: ({ children, ...props }: any) => (
      <span {...props} className={`italic text-blue-600 ${props.className ?? ''}`.trim()}>{children}</span>
    ),
  } as any), [])

  return (
    <div className="flex-1 flex flex-col">
      <Tabs value={activeTab} onValueChange={onActiveTabChange} className="h-full flex flex-col">
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
                        onClick={onOpenOriginal}
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
                  onQueueProcessing={onQueueProcessing}
                  onDirectProcessing={onDirectProcessing}
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
                        onClick={onOpenOriginal}
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
                        <Button onClick={onDownloadMarkdown} variant="outline" size="sm">
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
  )
}

export default BookContentViewer
