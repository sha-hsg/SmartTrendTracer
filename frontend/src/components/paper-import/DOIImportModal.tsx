import { useState } from 'react'
import http, { apiErrorMessage } from '@/services/http'
import { X, Link2, AlertCircle, AlertTriangle, CheckCircle, Loader2, FileText, Download } from 'lucide-react'

interface DOIImportModalProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess?: (paperId: string) => void
}

interface DOIImportResult {
  success: boolean
  existing?: boolean
  paper_id: string
  title?: string
  has_pdf?: boolean
  message: string
}

export default function DOIImportModal({ isOpen, onClose, onImportSuccess }: DOIImportModalProps) {
  const [identifier, setIdentifier] = useState('')
  const [isImporting, setIsImporting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<DOIImportResult | null>(null)

  if (!isOpen) return null

  const handleImport = async () => {
    if (!identifier.trim()) {
      setError('Please enter a DOI or a paper link')
      return
    }
    setIsImporting(true)
    setError(null)
    setResult(null)
    try {
      const response = await http.post<DOIImportResult>('/api/papers/import-doi', {
        identifier: identifier.trim()
      })
      setResult(response.data)
      // Close automatically only when nothing needs the user's attention
      if (response.data.success && response.data.has_pdf) {
        onImportSuccess?.(response.data.paper_id)
        setTimeout(() => handleClose(), 2000)
      }
    } catch (err) {
      setError(apiErrorMessage(err, 'Failed to import paper'))
    } finally {
      setIsImporting(false)
    }
  }

  const handleClose = () => {
    if (result?.success && !result.has_pdf) {
      onImportSuccess?.(result.paper_id)
    }
    setIdentifier('')
    setError(null)
    setResult(null)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg w-full max-w-2xl max-h-[90vh] overflow-hidden">
        <div className="p-6 border-b flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link2 className="w-6 h-6 text-sky-600" />
            <h2 className="text-xl font-semibold">Import by DOI or Paper Link</h2>
          </div>
          <button
            onClick={handleClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
          <div className="mb-4">
            <label htmlFor="doi-identifier" className="block text-sm font-medium text-gray-700 mb-2">
              DOI or link <span className="text-red-500">*</span>
            </label>
            <input
              id="doi-identifier"
              type="text"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !isImporting) handleImport() }}
              placeholder="10.1145/3442188.3445922 or https://papers.ssrn.com/…"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sky-500"
              disabled={isImporting}
              autoFocus
            />
            <p className="mt-1 text-sm text-gray-500">
              Title, authors, date and abstract are filled in automatically
            </p>
          </div>

          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {result?.existing && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <p className="text-red-800">{result.message}</p>
                <button
                  onClick={() => window.open(`/api/papers/${result.paper_id}/pdf`, '_blank')}
                  className="mt-2 text-sm text-red-600 hover:underline"
                >
                  View existing paper →
                </button>
              </div>
            </div>
          )}

          {result?.success && result.has_pdf && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-green-800">Imported with PDF: {result.title}</p>
                <button
                  onClick={() => window.open(`/api/papers/${result.paper_id}/pdf`, '_blank')}
                  className="mt-2 text-sm text-green-600 hover:underline"
                >
                  View imported paper →
                </button>
              </div>
            </div>
          )}

          {result?.success && !result.has_pdf && (
            <div className="mb-4 p-4 bg-amber-50 border border-amber-200 rounded-lg flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 mt-0.5" />
              <div>
                <p className="text-amber-900 font-medium">Imported without PDF: {result.title}</p>
                <p className="mt-1 text-sm text-amber-800">
                  No freely downloadable PDF was found (publishers such as SSRN and ACM block
                  automatic downloads). Download the PDF in your browser and upload it to this
                  paper.
                </p>
              </div>
            </div>
          )}

          <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
              <div className="text-sm text-gray-700">
                <p className="font-medium mb-1">Accepted input:</p>
                <ul className="list-disc list-inside space-y-1 text-gray-600">
                  <li>A DOI, e.g. 10.1609/aaai.v38i16.29728</li>
                  <li>A doi.org, SSRN or publisher link that contains a DOI</li>
                  <li>An arXiv link or id (uses the arXiv import)</li>
                  <li>Metadata from Crossref, open-access PDFs found via OpenAlex</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        <div className="p-6 border-t flex justify-end gap-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            disabled={isImporting}
          >
            {result?.success ? 'Close' : 'Cancel'}
          </button>
          <button
            onClick={handleImport}
            disabled={isImporting || !identifier.trim()}
            className="px-4 py-2 bg-sky-600 text-white rounded-lg hover:bg-sky-700 disabled:bg-gray-300 transition-colors flex items-center gap-2"
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
