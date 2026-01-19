import React, { useState } from 'react'
import { X, FileDown, BookOpen, GraduationCap, Globe, ChevronRight, FileText, Search, BookMarked, MessageSquare } from 'lucide-react'
import { ArxivImportModal } from './ArxivImportModal'
import ACLAnthologyImportModal from './ACLAnthologyImportModal'
import DirectURLImportModal from './DirectURLImportModal'
import { ACMImportModal } from './ACMImportModal'
import OpenReviewImportModal from './OpenReviewImportModal'

interface UnifiedImportDialogProps {
  isOpen: boolean
  onClose: () => void
  onImportSuccess?: (paperId: number | string) => void
}

type ImportSource = 'selection' | 'arxiv' | 'acl' | 'acm' | 'url' | 'dblp' | 'openreview'

interface ImportOption {
  id: ImportSource
  name: string
  description: string
  icon: React.ReactNode
  available: boolean
  comingSoon?: boolean
}

export default function UnifiedImportDialog({ isOpen, onClose, onImportSuccess }: UnifiedImportDialogProps) {
  const [selectedSource, setSelectedSource] = useState<ImportSource>('selection')
  
  if (!isOpen) return null

  const importOptions: ImportOption[] = [
    {
      id: 'arxiv',
      name: 'ArXiv',
      description: 'Import papers from ArXiv.org using paper ID or URL',
      icon: <GraduationCap className="w-8 h-8 text-orange-600" />,
      available: true
    },
    {
      id: 'acl',
      name: 'ACL Anthology',
      description: 'Import papers from ACL Anthology with full metadata',
      icon: <BookOpen className="w-8 h-8 text-blue-600" />,
      available: true
    },
    {
      id: 'acm',
      name: 'ACM Digital Library',
      description: 'Import papers from ACM DL with BibTeX metadata',
      icon: <BookMarked className="w-8 h-8 text-indigo-600" />,
      available: true
    },
    {
      id: 'openreview',
      name: 'OpenReview',
      description: 'Import conference papers with reviews and discussions',
      icon: <MessageSquare className="w-8 h-8 text-purple-600" />,
      available: true
    },
    {
      id: 'dblp',
      name: 'DBLP',
      description: 'Search and import papers from DBLP computer science bibliography',
      icon: <Search className="w-8 h-8 text-teal-600" />,
      available: false,
      comingSoon: true
    },
    {
      id: 'url',
      name: 'Direct URL',
      description: 'Import PDF from any direct URL',
      icon: <Globe className="w-8 h-8 text-green-600" />,
      available: true,
      comingSoon: false
    }
  ]

  const handleBack = () => {
    setSelectedSource('selection')
  }

  const handleClose = () => {
    setSelectedSource('selection')
    onClose()
  }

  const handleImportSuccess = (paperId: number | string) => {
    handleClose()
    if (onImportSuccess) {
      onImportSuccess(paperId)
    }
  }

  // Show source selection
  if (selectedSource === 'selection') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg w-full max-w-2xl">
          <div className="p-6 border-b flex items-center justify-between">
            <div className="flex items-center gap-3">
              <FileDown className="w-6 h-6 text-gray-700" />
              <h2 className="text-xl font-semibold">Import Paper</h2>
            </div>
            <button
              onClick={handleClose}
              className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          <div className="p-6">
            <p className="text-gray-600 mb-6">
              Choose a source to import your research paper from:
            </p>

            <div className="grid grid-cols-2 gap-4">
              {importOptions.map((option) => (
                <button
                  key={option.id}
                  onClick={() => option.available && setSelectedSource(option.id)}
                  disabled={!option.available}
                  className={`
                    p-4 rounded-lg border-2 text-left transition-all
                    ${option.available 
                      ? 'hover:border-blue-500 hover:bg-blue-50 cursor-pointer border-gray-200' 
                      : 'border-gray-100 bg-gray-50 cursor-not-allowed opacity-60'}
                  `}
                >
                  <div className="flex items-start gap-3">
                    <div className="mt-1">{option.icon}</div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{option.name}</h3>
                        {option.comingSoon && (
                          <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded-full">
                            Coming Soon
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">{option.description}</p>
                    </div>
                    {option.available && (
                      <ChevronRight className="w-5 h-5 text-gray-400 mt-2" />
                    )}
                  </div>
                </button>
              ))}
            </div>

            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <div className="flex items-start gap-2">
                <FileText className="w-5 h-5 text-gray-500 mt-0.5" />
                <div className="text-sm text-gray-600">
                  <p className="font-medium mb-1">Direct PDF Upload</p>
                  <p>
                    You can also upload PDF files directly using the{' '}
                    <button
                      onClick={() => {
                        handleClose()
                        // This will trigger the parent to switch to upload tab
                        const event = new CustomEvent('switchToUpload')
                        window.dispatchEvent(event)
                      }}
                      className="text-blue-600 hover:text-blue-800 underline"
                    >
                      Upload PDF
                    </button>{' '}
                    feature.
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="p-6 border-t flex justify-end">
            <button
              onClick={handleClose}
              className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    )
  }

  // Show ArXiv import modal
  if (selectedSource === 'arxiv') {
    return (
      <>
        <ArxivImportModal
          isOpen={true}
          onClose={handleBack}
          onImportSuccess={handleImportSuccess}
        />
      </>
    )
  }

  // Show ACL Anthology import modal
  if (selectedSource === 'acl') {
    return (
      <ACLAnthologyImportModal
        isOpen={true}
        onClose={handleBack}
        onImportSuccess={handleImportSuccess}
      />
    )
  }

  // Show ACM import modal
  if (selectedSource === 'acm') {
    return (
      <ACMImportModal
        isOpen={true}
        onClose={handleBack}
        onImportSuccess={(paperId: string) => handleImportSuccess(paperId)}
      />
    )
  }

  // Show OpenReview import modal
  if (selectedSource === 'openreview') {
    return (
      <OpenReviewImportModal
        isOpen={true}
        onClose={handleBack}
        onImportSuccess={handleImportSuccess}
      />
    )
  }

  // Show Direct URL import modal
  if (selectedSource === 'url') {
    return (
      <DirectURLImportModal
        isOpen={true}
        onClose={handleBack}
        onImportSuccess={handleImportSuccess}
      />
    )
  }

  return null
}