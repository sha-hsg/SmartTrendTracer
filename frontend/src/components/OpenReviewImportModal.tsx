import React, { useState, useEffect } from 'react'
import http from '@/services/http'
import { X, BookOpen, AlertCircle, CheckCircle, Loader2, FileText, ExternalLink, Tag, Users, Calendar, Globe } from 'lucide-react'

interface OpenReviewImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess?: (paperId: string) => void
}

interface PaperMetadata {
  title: string
  authors: string[]
  venue: string
  year: number | null
  keywords: string[]
  abstract: string
  tldr: string
  supplementary: Array<{ type: string; url: string }>
  openreview_url: string
}

const OpenReviewImportModal: React.FC<OpenReviewImportModalProps> = ({ 
  isOpen, 
  onClose, 
  onImportSuccess 
}) => {
  const [url, setUrl] = useState('')
  const [tags, setTags] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [validatedUrl, setValidatedUrl] = useState<string | null>(null)
  const [metadata, setMetadata] = useState<PaperMetadata | null>(null)
  const [fetchingMetadata, setFetchingMetadata] = useState(false)

  useEffect(() => {
    if (!isOpen) {
      // Reset state when modal closes
      setUrl('')
      setTags('')
      setError(null)
      setSuccess(false)
      setValidatedUrl(null)
      setMetadata(null)
    }
  }, [isOpen])

  const validateUrl = async () => {
    if (!url) {
      setError('Please enter an OpenReview URL')
      return
    }

    setIsValidating(true)
    setError(null)
    setMetadata(null)

    try {
      // Validate URL format
      const response = await http.post('/api/openreview/validate-url', { url })
      
      if (response.data.valid) {
        setValidatedUrl(response.data.normalized_url)
        
        // Fetch metadata
        setFetchingMetadata(true)
        try {
          const metadataResponse = await http.get(
            `/api/openreview/metadata/${response.data.forum_id}`
          )
          setMetadata(metadataResponse.data)
        } catch (err) {
          console.error('Failed to fetch metadata:', err)
          // Continue anyway - metadata fetch is optional
        } finally {
          setFetchingMetadata(false)
        }
      } else {
        setError(response.data.error || 'Invalid OpenReview URL')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to validate URL')
    } finally {
      setIsValidating(false)
    }
  }

  const handleImport = async () => {
    if (!validatedUrl && !url) {
      setError('Please enter and validate an OpenReview URL')
      return
    }

    setIsImporting(true)
    setError(null)

    try {
      const tagList = tags.split(',').map(t => t.trim()).filter(t => t)
      
      const response = await http.post('/api/openreview/import', {
        url: validatedUrl || url,
        add_tags: tagList.length > 0 ? tagList : undefined,
        process_pdf: true
      })

      if (response.data.success) {
        setSuccess(true)
        
        if (onImportSuccess) {
          onImportSuccess(response.data.paper_id)
        }
        
        // Auto-close after 2 seconds
        setTimeout(() => {
          handleClose()
        }, 2000)
      } else if (response.data.existing) {
        setError('This paper already exists in the database')
        if (onImportSuccess && response.data.paper_id) {
          setTimeout(() => {
            onImportSuccess(response.data.paper_id)
            handleClose()
          }, 1500)
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import paper')
    } finally {
      setIsImporting(false)
    }
  }

  const handleClose = () => {
    setUrl('')
    setTags('')
    setError(null)
    setSuccess(false)
    setValidatedUrl(null)
    setMetadata(null)
    onClose()
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-3xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-purple-600" />
            <h2 className="text-xl font-semibold">Import from OpenReview</h2>
          </div>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* URL Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              OpenReview URL
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://openreview.net/forum?id=..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
                disabled={isImporting}
              />
              <button
                onClick={validateUrl}
                disabled={isValidating || !url || isImporting}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
              >
                {isValidating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Validate
                  </>
                )}
              </button>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Enter the OpenReview forum URL (e.g., https://openreview.net/forum?id=ZZ4tcxJvux)
            </p>
          </div>

          {/* Metadata Display */}
          {fetchingMetadata && (
            <div className="mb-4 p-4 bg-gray-50 rounded-lg flex items-center gap-3">
              <Loader2 className="w-5 h-5 animate-spin text-gray-600" />
              <span className="text-gray-700">Fetching paper metadata...</span>
            </div>
          )}

          {metadata && !fetchingMetadata && (
            <div className="mb-4 p-4 bg-purple-50 border border-purple-200 rounded-lg">
              <h3 className="font-semibold text-lg mb-3">{metadata.title}</h3>
              
              {metadata.authors && metadata.authors.length > 0 && (
                <div className="flex items-start gap-2 mb-2">
                  <Users className="w-4 h-4 text-purple-600 mt-1" />
                  <div className="flex-1">
                    <span className="text-sm text-gray-700">
                      {metadata.authors.slice(0, 3).join(', ')}
                      {metadata.authors.length > 3 && ` +${metadata.authors.length - 3} more`}
                    </span>
                  </div>
                </div>
              )}

              {metadata.venue && (
                <div className="flex items-center gap-2 mb-2">
                  <Globe className="w-4 h-4 text-purple-600" />
                  <span className="text-sm text-gray-700">{metadata.venue}</span>
                  {metadata.year && (
                    <>
                      <Calendar className="w-4 h-4 text-purple-600 ml-2" />
                      <span className="text-sm text-gray-700">{metadata.year}</span>
                    </>
                  )}
                </div>
              )}

              {metadata.keywords && metadata.keywords.length > 0 && (
                <div className="flex items-start gap-2 mb-2">
                  <Tag className="w-4 h-4 text-purple-600 mt-1" />
                  <div className="flex-1 flex flex-wrap gap-1">
                    {metadata.keywords.map((keyword, idx) => (
                      <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {metadata.tldr && (
                <div className="mt-3 p-3 bg-white rounded border border-purple-100">
                  <p className="text-sm font-medium text-gray-700 mb-1">TL;DR</p>
                  <p className="text-sm text-gray-600">{metadata.tldr}</p>
                </div>
              )}

              {metadata.abstract && (
                <details className="mt-3">
                  <summary className="cursor-pointer text-sm font-medium text-purple-600 hover:text-purple-700">
                    View Abstract
                  </summary>
                  <div className="mt-2 p-3 bg-white rounded border border-purple-100">
                    <p className="text-sm text-gray-600 whitespace-pre-wrap">{metadata.abstract}</p>
                  </div>
                </details>
              )}

              {metadata.supplementary && metadata.supplementary.length > 0 && (
                <div className="mt-3 pt-3 border-t border-purple-200">
                  <p className="text-sm font-medium text-gray-700 mb-2">Supplementary Materials</p>
                  <div className="space-y-1">
                    {metadata.supplementary.map((item, idx) => (
                      <a
                        key={idx}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-sm text-purple-600 hover:text-purple-700"
                      >
                        <ExternalLink className="w-3 h-3" />
                        {item.type}
                      </a>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Tags Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags (optional, comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="machine-learning, conference-papers, neural-networks"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              disabled={isImporting}
            />
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-800">{error}</p>
              </div>
            </div>
          )}

          {/* Success Display */}
          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <p className="text-green-800">Paper imported successfully!</p>
            </div>
          )}

          {/* Info Box */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-gray-700">
                <p className="font-medium mb-1">OpenReview Import Features:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>Automatically fetches paper metadata and abstract</li>
                  <li>Downloads PDF if available</li>
                  <li>Extracts keywords and supplementary materials</li>
                  <li>Generates BibTeX citation</li>
                  <li>Processes PDF with Marker for full-text extraction</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t flex justify-end gap-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            disabled={isImporting}
          >
            Cancel
          </button>
          <button
            onClick={handleImport}
            disabled={isImporting || (!validatedUrl && !url)}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
          >
            {isImporting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <BookOpen className="w-4 h-4" />
                Import Paper
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default OpenReviewImportModal