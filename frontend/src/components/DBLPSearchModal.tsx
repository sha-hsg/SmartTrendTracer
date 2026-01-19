import React, { useState } from 'react'
import axios from 'axios'
import { 
  Dialog, 
  DialogContent, 
  DialogHeader, 
  DialogTitle,
  DialogDescription 
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Loader2, Search, Copy, Download, ExternalLink, FileText, CheckCircle, Save } from 'lucide-react'
import { cn } from '@/lib/utils'

interface DBLPResult {
  title: string
  authors: string[]
  author_string: string
  venue: string | null
  year: string | null
  type: string
  dblp_url: string | null
  pdf_url: string | null
  doi: string | null
  dblp_key: string | null
  citation_string: string
  metadata?: any  // Complete metadata from SPARQL
}

interface DBLPSearchModalProps {
  isOpen: boolean
  onClose: () => void
  initialTitle?: string
  paperId?: number
  hasExistingMetadata?: boolean  // To know if paper already has metadata
}

export const DBLPSearchModal: React.FC<DBLPSearchModalProps> = ({ 
  isOpen, 
  onClose, 
  initialTitle = '',
  paperId,
  hasExistingMetadata = false 
}) => {
  const [searchQuery, setSearchQuery] = useState(initialTitle)
  const [searching, setSearching] = useState(false)
  const [results, setResults] = useState<DBLPResult[]>([])
  const [selectedResult, setSelectedResult] = useState<DBLPResult | null>(null)
  const [bibtex, setBibtex] = useState<string>('')
  const [loadingBibtex, setLoadingBibtex] = useState(false)
  const [copiedBibtex, setCopiedBibtex] = useState(false)
  const [error, setError] = useState<string>('')
  const [attachingMetadata, setAttachingMetadata] = useState(false)
  const [metadataAttached, setMetadataAttached] = useState(false)

  const handleSearch = async () => {
    if (!searchQuery.trim()) return

    setSearching(true)
    setError('')
    setResults([])
    setSelectedResult(null)
    setBibtex('')

    try {
      const response = await axios.get('http://localhost:8000/api/papers/dblp/search', {
        params: { title: searchQuery, max_results: 20 }
      })

      if (response.data.results && response.data.results.length > 0) {
        setResults(response.data.results)
      } else {
        setError('No results found on DBLP. Try adjusting your search terms.')
      }
    } catch (err) {
      console.error('DBLP search error:', err)
      setError('Failed to search DBLP. Please try again.')
    } finally {
      setSearching(false)
    }
  }

  const handleSelectResult = async (result: DBLPResult) => {
    setSelectedResult(result)
    setLoadingBibtex(true)
    setBibtex('')
    setCopiedBibtex(false)

    try {
      // Fetch complete metadata using SPARQL
      if (result.dblp_key) {
        const response = await axios.get(`http://localhost:8000/api/dblp/metadata/${result.dblp_key}`)
        
        if (response.data.bibtex) {
          setBibtex(response.data.bibtex)
          
          // Store the metadata for later use
          setSelectedResult({
            ...result,
            metadata: response.data
          })
        }
      } else if (result.dblp_url) {
        // Fallback to old method if no key but URL exists
        const response = await axios.get('http://localhost:8000/api/dblp/bibtex', {
          params: { dblp_url: result.dblp_url }
        })
        
        if (response.data.bibtex) {
          setBibtex(response.data.bibtex)
        }
      } else {
        // No key or URL available
        setBibtex('BibTeX citation not available - no DBLP key or URL found')
      }
    } catch (err) {
      console.error('Failed to fetch metadata/BibTeX:', err)
      setBibtex('Failed to fetch BibTeX citation')
    } finally {
      setLoadingBibtex(false)
    }
  }

  const handleCopyBibtex = () => {
    if (bibtex) {
      navigator.clipboard.writeText(bibtex)
      setCopiedBibtex(true)
      setTimeout(() => setCopiedBibtex(false), 2000)
    }
  }

  const handleDownloadBibtex = () => {
    if (bibtex && selectedResult) {
      const blob = new Blob([bibtex], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${selectedResult.dblp_key?.replace('/', '_') || 'paper'}.bib`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  const handleAttachMetadata = async () => {
    if (!selectedResult || !paperId) return

    // Confirm if overwriting existing metadata
    if (hasExistingMetadata) {
      const confirmed = window.confirm(
        'This paper already has metadata. Do you want to replace it with the selected DBLP entry?\n\n' +
        `Selected: ${selectedResult.title}\n` +
        `Venue: ${selectedResult.venue || 'N/A'}\n` +
        `Year: ${selectedResult.year || 'N/A'}`
      )
      if (!confirmed) return
    }

    setAttachingMetadata(true)
    setMetadataAttached(false)

    try {
      const response = await axios.post(
        `http://localhost:8000/api/dblp/attach-metadata/${paperId}`,
        null,
        { params: { 
          dblp_key: selectedResult.dblp_key,
          overwrite: hasExistingMetadata  // Only overwrite if user confirmed
        } }
      )

      if (response.data.success) {
        setMetadataAttached(true)
        // Close modal and notify parent component
        setTimeout(() => {
          onClose()
          // If parent provided a callback, use it instead of reloading
          if ((window as any).refreshPaperData) {
            (window as any).refreshPaperData()
          }
        }, 1500)
      }
    } catch (err) {
      console.error('Failed to attach metadata:', err)
      setError('Failed to attach metadata to paper')
    } finally {
      setAttachingMetadata(false)
    }
  }

  const getVenueColor = (type: string) => {
    switch (type) {
      case 'Conference and Workshop Papers':
      case 'inproceedings':
        return 'bg-blue-100 text-blue-800'
      case 'Journal Articles':
      case 'article':
        return 'bg-green-100 text-green-800'
      case 'Informal and Other Publications':
      case 'informal':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-purple-100 text-purple-800'
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Search DBLP Bibliography</DialogTitle>
          <DialogDescription>
            Search for paper versions on DBLP to get BibTeX citations and download links.
            {results.length > 1 && (
              <span className="text-orange-600 font-medium block mt-1">
                Multiple versions found - select the most appropriate one.
              </span>
            )}
          </DialogDescription>
        </DialogHeader>

        {/* Search Input */}
        <div className="flex gap-2 mt-4">
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            placeholder="Enter paper title to search..."
            className="flex-1"
          />
          <Button 
            onClick={handleSearch} 
            disabled={searching || !searchQuery.trim()}
          >
            {searching ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            <span className="ml-2">Search</span>
          </Button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-md text-sm">
            {error}
          </div>
        )}

        {/* Results List */}
        {results.length > 0 && (
          <div className="mt-4 flex-1 overflow-auto">
            <div className="space-y-2">
              {results.map((result, idx) => (
                <div
                  key={idx}
                  className={cn(
                    "p-3 border rounded-lg cursor-pointer transition-colors",
                    selectedResult === result 
                      ? "border-blue-500 bg-blue-50" 
                      : "hover:bg-gray-50"
                  )}
                  onClick={() => handleSelectResult(result)}
                >
                  {/* Title */}
                  <h4 className="font-medium text-sm mb-1">{result.title}</h4>
                  
                  {/* Authors */}
                  <p className="text-xs text-gray-600 mb-2">
                    {result.author_string}
                  </p>
                  
                  {/* Venue and Year */}
                  <div className="flex items-center gap-2 mb-2">
                    {result.venue && (
                      <Badge variant="outline" className="text-xs">
                        {result.venue}
                      </Badge>
                    )}
                    {result.year && (
                      <Badge variant="outline" className="text-xs">
                        {result.year}
                      </Badge>
                    )}
                    <Badge className={cn("text-xs", getVenueColor(result.type))}>
                      {result.type}
                    </Badge>
                  </div>
                  
                  {/* Links */}
                  <div className="flex items-center gap-3">
                    {result.dblp_url && (
                      <a
                        href={result.dblp_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                      >
                        <ExternalLink className="h-3 w-3" />
                        DBLP
                      </a>
                    )}
                    {result.pdf_url && (
                      <a
                        href={result.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-green-600 hover:underline flex items-center gap-1"
                      >
                        <Download className="h-3 w-3" />
                        PDF
                      </a>
                    )}
                    {result.doi && (
                      <a
                        href={`https://doi.org/${result.doi}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="text-xs text-purple-600 hover:underline flex items-center gap-1"
                      >
                        <FileText className="h-3 w-3" />
                        DOI
                      </a>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Selected Result BibTeX */}
        {selectedResult && (
          <div className="mt-4 border-t pt-4">
            <div className="flex items-center justify-between mb-2">
              <h4 className="font-medium text-sm">BibTeX Citation</h4>
              <div className="flex gap-2">
                {paperId && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleAttachMetadata}
                    disabled={!selectedResult.dblp_key || attachingMetadata || metadataAttached}
                  >
                    {metadataAttached ? (
                      <>
                        <CheckCircle className="h-4 w-4 text-green-600" />
                        <span className="ml-2">Attached!</span>
                      </>
                    ) : attachingMetadata ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        <span className="ml-2">Attaching...</span>
                      </>
                    ) : (
                      <>
                        <Save className="h-4 w-4" />
                        <span className="ml-2">Attach to Paper</span>
                      </>
                    )}
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleDownloadBibtex}
                  disabled={!bibtex || loadingBibtex}
                >
                  <Download className="h-4 w-4" />
                  <span className="ml-2">Download</span>
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyBibtex}
                  disabled={!bibtex || loadingBibtex}
                >
                  {copiedBibtex ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <span className="ml-2">Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      <span className="ml-2">Copy</span>
                    </>
                  )}
                </Button>
              </div>
            </div>
            
            {loadingBibtex ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                <span className="text-sm text-gray-500">Loading BibTeX...</span>
              </div>
            ) : (
              <pre className="bg-gray-50 p-3 rounded text-xs font-mono overflow-x-auto max-h-40">
                {bibtex || 'BibTeX not available'}
              </pre>
            )}
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}