import { useState } from 'react'
import http from '@/services/http'
import { X, AlertCircle, CheckCircle, Loader2, BookOpen, FileText, Users, Calendar, Link, Tag } from 'lucide-react'

interface JAIRImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess?: (paperId: number | string) => void
}

interface JAIRMetadata {
  title?: string
  authors?: string
  authors_list?: string[]
  authors_detailed?: { name: string; affiliation: string }[]
  abstract?: string
  journal?: string
  volume?: string
  year?: number
  doi?: string
  keywords?: string[]
  pdf_url?: string
}

export default function JAIRImportModal({ isOpen, onClose, onImportSuccess }: JAIRImportModalProps) {
  const [url, setUrl] = useState('')
  const [isValidating, setIsValidating] = useState(false)
  const [isImporting, setIsImporting] = useState(false)
  const [metadata, setMetadata] = useState<JAIRMetadata | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const [importedPaperId, setImportedPaperId] = useState<string | null>(null)

  if (!isOpen) return null

  const validateUrl = async () => {
    if (!url) {
      setError('Please enter a URL')
      return
    }
    if (!url.includes('jair.org')) {
      setError('URL must be from jair.org')
      return
    }

    setIsValidating(true)
    setError(null)
    setMetadata(null)

    try {
      const response = await http.post('/api/jair/parse', { url })
      if (response.data.success) {
        setMetadata(response.data.metadata)
      } else {
        setError('Could not parse JAIR page')
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
      const response = await http.post('/api/jair/import', { url })

      if (response.data.success) {
        setSuccess(true)
        setImportedPaperId(response.data.paper_id)
        if (onImportSuccess) {
          onImportSuccess(response.data.paper_id)
        }
        setTimeout(() => handleClose(), 2000)
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
    setImportedPaperId(null)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-3xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <FileText className="w-6 h-6 text-amber-600" />
            <h2 className="text-xl font-semibold">Import from JAIR</h2>
          </div>
          <button onClick={handleClose} className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          {/* URL Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              JAIR Article URL
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://www.jair.org/index.php/jair/article/view/19490"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500"
                disabled={isValidating || isImporting}
                onKeyDown={(e) => e.key === 'Enter' && validateUrl()}
              />
              <button
                onClick={validateUrl}
                disabled={!url || isValidating || isImporting}
                className="px-4 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
              >
                {isValidating ? (
                  <><Loader2 className="w-4 h-4 animate-spin" /> Validating...</>
                ) : (
                  <><FileText className="w-4 h-4" /> Parse</>
                )}
              </button>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Enter a URL from jair.org (e.g., https://www.jair.org/index.php/jair/article/view/19490)
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-800">{error}</p>
                {importedPaperId && (
                  <p className="mt-1 text-sm text-red-600">Paper ID: {importedPaperId}</p>
                )}
              </div>
            </div>
          )}

          {/* Success */}
          {success && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <p className="text-green-800">Paper imported successfully!</p>
            </div>
          )}

          {/* Metadata Preview */}
          {metadata && !success && (
            <div className="space-y-4">
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
                <h3 className="font-semibold text-lg mb-3">{metadata.title}</h3>

                {metadata.authors_detailed && metadata.authors_detailed.length > 0 && (
                  <div className="flex items-start gap-2 mb-2">
                    <Users className="w-4 h-4 text-gray-500 mt-1 flex-shrink-0" />
                    <div className="text-sm text-gray-700">
                      {metadata.authors_detailed.map((a, i) => (
                        <span key={i}>
                          {i > 0 && ', '}
                          <span className="font-medium">{a.name}</span>
                          {a.affiliation && (
                            <span className="text-gray-500"> ({a.affiliation})</span>
                          )}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {metadata.journal && (
                  <div className="flex items-start gap-2 mb-2">
                    <BookOpen className="w-4 h-4 text-gray-500 mt-1" />
                    <p className="text-sm text-gray-700">
                      {metadata.journal}
                      {metadata.volume && `, Vol. ${metadata.volume}`}
                    </p>
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

                {metadata.keywords && metadata.keywords.length > 0 && (
                  <div className="flex items-start gap-2 mb-2">
                    <Tag className="w-4 h-4 text-gray-500 mt-1 flex-shrink-0" />
                    <div className="flex flex-wrap gap-1">
                      {metadata.keywords.map((kw, i) => (
                        <span key={i} className="text-xs bg-amber-100 text-amber-800 px-2 py-0.5 rounded-full">
                          {kw}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {metadata.abstract && (
                <div>
                  <h4 className="font-medium mb-2">Abstract</h4>
                  <p className="text-sm text-gray-600 leading-relaxed max-h-32 overflow-y-auto">
                    {metadata.abstract}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t flex justify-between">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
          >
            Cancel
          </button>
          {metadata && !success && (
            <button
              onClick={handleImport}
              disabled={isImporting}
              className="px-6 py-2 bg-amber-600 text-white rounded-lg hover:bg-amber-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
            >
              {isImporting ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Importing...</>
              ) : (
                <><BookOpen className="w-4 h-4" /> Import Paper</>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
