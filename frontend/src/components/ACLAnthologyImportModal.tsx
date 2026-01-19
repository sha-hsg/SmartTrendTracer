import React, { useState } from 'react'
import axios from 'axios'
import { X, Upload, AlertCircle, CheckCircle, Loader2, BookOpen, FileText, Users, Calendar, Link } from 'lucide-react'

interface ACLAnthologyImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess?: (paperId: number) => void
}

interface ACLMetadata {
  title?: string
  authors?: string[]
  abstract?: string
  venue?: string
  year?: number
  doi?: string
  pages?: string
  proceedings?: string
  anthology_id?: string
  pdf_url?: string
}

export default function ACLAnthologyImportModal({ isOpen, onClose, onImportSuccess }: ACLAnthologyImportModalProps) {
  const [url, setUrl] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [metadata, setMetadata] = useState<ACLMetadata | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [tags, setTags] = useState<string>('')
  const [importedPaperId, setImportedPaperId] = useState<number | null>(null)

  if (!isOpen) return null

  const validateUrl = async () => {
    if (!url) {
      setError('Please enter a URL')
      return
    }

    if (!url.includes('aclanthology.org')) {
      setError('URL must be from aclanthology.org')
      return
    }

    setIsValidating(true)
    setError(null)
    setMetadata(null)

    try {
      const response = await axios.post('http://localhost:8000/api/acl-anthology/parse', { url })
      if (response.data.success) {
        setMetadata(response.data.metadata)
      } else {
        setError('Could not parse ACL Anthology page')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to validate URL')
    } finally {
      setIsValidating(false)
    }
  }

  const handleImport = async () => {
    if (!url || !metadata) return

    setIsImporting(true)
    setError(null)

    try {
      const tagList = tags.split(',').map(t => t.trim()).filter(t => t)
      
      const response = await axios.post('http://localhost:8000/api/acl-anthology/import', {
        url,
        process_pdf: false,
        add_tags: tagList.length > 0 ? tagList : undefined
      })

      if (response.data.success) {
        setSuccess(true)
        setImportedPaperId(response.data.paper_id)
        
        if (onImportSuccess) {
          onImportSuccess(response.data.paper_id)
        }
        
        // Auto-close after 2 seconds
        setTimeout(() => {
          handleClose()
        }, 2000)
      } else if (response.data.existing) {
        setError('This paper already exists in the database')
        setImportedPaperId(response.data.paper_id)
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to import paper')
    } finally {
      setIsImporting(false)
    }
  }

  const handleClose = () => {
    setUrl('')
    setMetadata(null)
    setError(null)
    setSuccess(false)
    setTags('')
    setImportedPaperId(null)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-3xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <BookOpen className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold">Import from ACL Anthology</h2>
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
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              ACL Anthology URL
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://aclanthology.org/2025.acl-long.5/"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={isValidating || isImporting}
              />
              <button
                onClick={validateUrl}
                disabled={!url || isValidating || isImporting}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
              >
                {isValidating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Validating...
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    Parse
                  </>
                )}
              </button>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Enter a URL from aclanthology.org (e.g., https://aclanthology.org/2025.acl-long.5/)
            </p>
          </div>

          {/* Error Display */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-800">{error}</p>
                {importedPaperId && (
                  <button
                    onClick={() => window.open(`/papers/${importedPaperId}`, '_blank')}
                    className="mt-2 text-sm text-red-600 hover:underline"
                  >
                    View existing paper →
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Success Display */}
          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-green-800">Paper imported successfully!</p>
                {importedPaperId && (
                  <button
                    onClick={() => window.open(`/papers/${importedPaperId}`, '_blank')}
                    className="mt-2 text-sm text-green-600 hover:underline"
                  >
                    View imported paper →
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Metadata Display */}
          {metadata && !success && (
            <div className="space-y-4">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-semibold text-lg mb-3">{metadata.title}</h3>
                
                {metadata.authors && metadata.authors.length > 0 && (
                  <div className="flex items-start gap-2 mb-2">
                    <Users className="w-4 h-4 text-gray-500 mt-1" />
                    <p className="text-sm text-gray-700">
                      {metadata.authors.join(', ')}
                    </p>
                  </div>
                )}

                {metadata.venue && (
                  <div className="flex items-start gap-2 mb-2">
                    <BookOpen className="w-4 h-4 text-gray-500 mt-1" />
                    <p className="text-sm text-gray-700">{metadata.venue}</p>
                  </div>
                )}

                {metadata.year && (
                  <div className="flex items-start gap-2 mb-2">
                    <Calendar className="w-4 h-4 text-gray-500 mt-1" />
                    <p className="text-sm text-gray-700">{metadata.year}</p>
                  </div>
                )}

                {metadata.doi && (
                  <div className="flex items-start gap-2 mb-2">
                    <Link className="w-4 h-4 text-gray-500 mt-1" />
                    <p className="text-sm text-gray-700">DOI: {metadata.doi}</p>
                  </div>
                )}

                {metadata.pages && (
                  <div className="flex items-start gap-2 mb-2">
                    <FileText className="w-4 h-4 text-gray-500 mt-1" />
                    <p className="text-sm text-gray-700">Pages: {metadata.pages}</p>
                  </div>
                )}
              </div>

              {metadata.abstract && (
                <div>
                  <h4 className="font-medium mb-2">Abstract</h4>
                  <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-lg max-h-32 overflow-y-auto">
                    {metadata.abstract}
                  </p>
                </div>
              )}

              {/* Import Options */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tags (optional, comma-separated)
                </label>
                <input
                  type="text"
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="nlp, fairness, llm"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={isImporting}
                />
              </div>
            </div>
          )}
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
          {metadata && !success && (
            <button
              onClick={handleImport}
              disabled={isImporting}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
            >
              {isImporting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Importing...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" />
                  Import Paper
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}