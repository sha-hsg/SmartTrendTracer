import { useState } from 'react'
import axios from 'axios'
import { X, Globe, AlertCircle, CheckCircle, Loader2, FileText, Download } from 'lucide-react'

interface DirectURLImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess?: (paperId: string) => void
}

export default function DirectURLImportModal({ isOpen, onClose, onImportSuccess }: DirectURLImportModalProps) {
  const [url, setUrl] = useState('')
  const [title, setTitle] = useState('')
  const [authors, setAuthors] = useState('')
  const [tags, setTags] = useState('')
  const [_isValidating, _setIsValidating] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [importedPaperId, setImportedPaperId] = useState<string | null>(null)

  if (!isOpen) return null

  const validateUrl = () => {
    if (!url) {
      setError('Please enter a URL')
      return false
    }

    // Basic URL validation
    try {
      new URL(url) // Validate URL format
      // Check if it's a PDF URL
      if (!url.toLowerCase().endsWith('.pdf')) {
        setError('URL must point directly to a PDF file')
        return false
      }
      return true
    } catch {
      setError('Please enter a valid URL')
      return false
    }
  }

  const handleImport = async () => {
    if (!validateUrl()) return
    if (!title.trim()) {
      setError('Please enter a title for the paper')
      return
    }

    setIsImporting(true)
    setError(null)

    try {
      const tagList = tags.split(',').map(t => t.trim()).filter(t => t)
      const authorList = authors.split(',').map(a => a.trim()).filter(a => a)
      
      const response = await axios.post('http://localhost:8000/api/papers/import-url', {
        url,
        title: title.trim(),
        authors: authorList.join(', '),
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
    setTitle('')
    setAuthors('')
    setTags('')
    setError(null)
    setSuccess(false)
    setImportedPaperId(null)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Globe className="w-6 h-6 text-green-600" />
            <h2 className="text-xl font-semibold">Import from Direct URL</h2>
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
              PDF URL <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://example.com/paper.pdf"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                disabled={isImporting}
              />
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Enter a direct URL to a PDF file
            </p>
          </div>

          {/* Title Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Paper Title <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Enter the paper title"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              disabled={isImporting}
            />
          </div>

          {/* Authors Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Authors (optional, comma-separated)
            </label>
            <input
              type="text"
              value={authors}
              onChange={(e) => setAuthors(e.target.value)}
              placeholder="John Doe, Jane Smith"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              disabled={isImporting}
            />
          </div>

          {/* Tags Input */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Tags (optional, comma-separated)
            </label>
            <input
              type="text"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
              placeholder="machine-learning, nlp, transformers"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
              disabled={isImporting}
            />
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

          {/* Info Box */}
          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-gray-700">
                <p className="font-medium mb-1">How to use:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>The URL must point directly to a PDF file</li>
                  <li>The PDF will be downloaded and stored locally</li>
                  <li>You can process the PDF content later to extract text and sections</li>
                  <li>Make sure you have permission to download the PDF</li>
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
            disabled={isImporting || !url || !title}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
          >
            {isImporting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <Download className="w-4 h-4" />
                Import Paper
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}