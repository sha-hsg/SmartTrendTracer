import React, { useState } from 'react'
import axios from 'axios'
import MetadataImportDialog from './MetadataImportDialog'
import { 
  FileText, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  ArrowRight,
  Users,
  Calendar,
  Hash,
  Link,
  RefreshCw,
  Sparkles,
  Copy,
  Download
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'

interface GROBIDMetadataPanelProps {
  paperId: number
  onMetadataUpdated?: () => void
  grobidProcessed?: boolean
  grobidProcessedAt?: string
}

interface GROBIDMetadata {
  title?: string
  abstract?: string
  authors?: Array<{
    name: string
    affiliation?: string
    email?: string
    department?: string
  }>
  keywords?: string[]
  publication_date?: string
  year?: number
  journal?: string
  volume?: string
  pages?: string
  eprint?: string
  doi?: string
  arxiv_id?: string
  dblp_key?: string
  bibtex_raw?: string
}

interface ProcessingResult {
  success: boolean
  metadata_extracted: boolean
  references_extracted: number
  sections_extracted: number
  citations_extracted: number
  metadata?: GROBIDMetadata
}

export default function GROBIDMetadataPanel({ paperId, onMetadataUpdated, grobidProcessed, grobidProcessedAt }: GROBIDMetadataPanelProps) {
  const [processing, setProcessing] = useState(false)
  const [loadingMetadata, setLoadingMetadata] = useState(false)
  const [result, setResult] = useState<ProcessingResult | null>(null)
  const [metadata, setMetadata] = useState<GROBIDMetadata | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [applyingMetadata, setApplyingMetadata] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)

  const processWithGROBID = async () => {
    setProcessing(true)
    setError(null)
    setResult(null)
    setMetadata(null)
    
    try {
      const response = await axios.post(
        `http://localhost:8000/api/papers/${paperId}/grobid/process`
      )
      
      if (response.data.success) {
        setResult(response.data)
        if (response.data.metadata) {
          setMetadata(response.data.metadata)
        }
      } else {
        setError('GROBID processing failed')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to process paper with GROBID')
      console.error('Error processing with GROBID:', err)
    } finally {
      setProcessing(false)
    }
  }

  const loadGROBIDMetadata = async () => {
    setLoadingMetadata(true)
    setError(null)
    
    try {
      const response = await axios.get(
        `http://localhost:8000/api/papers/${paperId}/grobid/metadata`
      )
      
      if (response.data.grobid_metadata) {
        setMetadata(response.data.grobid_metadata)
      }
    } catch (err: any) {
      setError('Failed to load GROBID metadata')
      console.error('Error loading GROBID metadata:', err)
    } finally {
      setLoadingMetadata(false)
    }
  }

  const handleMetadataImport = async (selectedFields: Record<string, any>) => {
    setApplyingMetadata(true)
    setError(null)
    
    try {
      // Use PUT endpoint for metadata update
      await axios.put(
        `http://localhost:8000/api/papers/${paperId}/metadata`,
        selectedFields
      )
      
      if (onMetadataUpdated) {
        onMetadataUpdated()
      }
      
      setShowImportDialog(false)
      // Show success message
      alert('Metadata successfully imported!')
    } catch (err: any) {
      setError('Failed to import metadata')
      console.error('Error importing metadata:', err)
      throw err
    } finally {
      setApplyingMetadata(false)
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <FileText className="h-5 w-5" />
              GROBID Metadata Extraction
            </CardTitle>
            <CardDescription>
              Extract structured metadata using machine learning
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={loadGROBIDMetadata}
              disabled={loadingMetadata}
            >
              {loadingMetadata ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  Loading...
                </>
              ) : (
                <>
                  <RefreshCw className="h-4 w-4 mr-1" />
                  Load Metadata
                </>
              )}
            </Button>
            <Button
              size="sm"
              onClick={processWithGROBID}
              disabled={processing}
            >
              {processing ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-1" />
                  Process with GROBID
                </>
              )}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {/* GROBID Processing Status */}
        <div className="mb-4">
          {grobidProcessed ? (
            <Alert className="bg-green-50 border-green-200">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertDescription className="text-green-800">
                <span className="font-semibold">✓ Processed with GROBID</span>
                {grobidProcessedAt && (
                  <span className="ml-2 text-sm">
                    at {new Date(grobidProcessedAt).toLocaleString()}
                  </span>
                )}
              </AlertDescription>
            </Alert>
          ) : (
            <Alert className="bg-gray-50 border-gray-200">
              <AlertCircle className="h-4 w-4 text-gray-600" />
              <AlertDescription className="text-gray-800">
                <span className="font-semibold">⚠ Not Processed</span>
                <span className="ml-2 text-sm">
                  Click "Process with GROBID" to extract structured metadata
                </span>
              </AlertDescription>
            </Alert>
          )}
        </div>

        {error && (
          <Alert className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {result && (
          <div className="mb-6 p-4 bg-green-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="font-semibold text-green-800">Processing Complete</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-sm text-green-700">
              <div>References extracted: {result.references_extracted}</div>
              <div>Sections extracted: {result.sections_extracted}</div>
              <div>Citations extracted: {result.citations_extracted}</div>
              <div>Metadata extracted: {result.metadata_extracted ? 'Yes' : 'No'}</div>
            </div>
          </div>
        )}
        
        {metadata && (
          <div className="space-y-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">Extracted Metadata</h3>
              <Button
                size="sm"
                onClick={() => setShowImportDialog(true)}
                disabled={!metadata}
              >
                <ArrowRight className="h-4 w-4 mr-1" />
                Review & Import
              </Button>
            </div>
            
            <Separator />
            
            {/* Title */}
            {metadata.title && (
              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Title</div>
                <div className="text-sm">{metadata.title}</div>
              </div>
            )}
            
            {/* Authors */}
            {metadata.authors && metadata.authors.length > 0 && (
              <div>
                <div className="flex items-center gap-1 text-xs font-semibold text-gray-500 mb-2">
                  <Users className="h-3 w-3" />
                  Authors ({metadata.authors.length})
                </div>
                <div className="space-y-2">
                  {metadata.authors.map((author, idx) => (
                    <div key={idx} className="pl-4 border-l-2 border-gray-200">
                      <div className="text-sm font-medium">
                        {typeof author === 'string' ? author : author.name}
                      </div>
                      {typeof author === 'object' && author.affiliation && (
                        <div className="text-xs text-gray-600">{author.affiliation}</div>
                      )}
                      {typeof author === 'object' && author.department && (
                        <div className="text-xs text-gray-500">{author.department}</div>
                      )}
                      {typeof author === 'object' && author.email && (
                        <div className="text-xs text-blue-600">{author.email}</div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            {/* Abstract */}
            {metadata.abstract && (
              <div>
                <div className="text-xs font-semibold text-gray-500 mb-1">Abstract</div>
                <div className="text-sm text-gray-700 line-clamp-3">{metadata.abstract}</div>
              </div>
            )}
            
            {/* Publication Info */}
            {(metadata.publication_date || metadata.year || metadata.journal || metadata.eprint) && (
              <div>
                <div className="text-xs font-semibold text-gray-500 mb-2">Publication Details</div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  {metadata.publication_date && (
                    <div>
                      <span className="text-gray-500">Date:</span> {metadata.publication_date}
                    </div>
                  )}
                  {!metadata.publication_date && metadata.year && (
                    <div>
                      <span className="text-gray-500">Year:</span> {metadata.year}
                    </div>
                  )}
                  {metadata.journal && (
                    <div>
                      <span className="text-gray-500">Journal:</span> {metadata.journal}
                    </div>
                  )}
                  {metadata.volume && (
                    <div>
                      <span className="text-gray-500">Volume:</span> {metadata.volume}
                    </div>
                  )}
                  {metadata.pages && (
                    <div>
                      <span className="text-gray-500">Pages:</span> {metadata.pages}
                    </div>
                  )}
                  {metadata.eprint && (
                    <div className="col-span-2">
                      <span className="text-gray-500">ePrint:</span> {metadata.eprint}
                    </div>
                  )}
                  {metadata.doi && (
                    <div className="col-span-2">
                      <span className="text-gray-500">DOI:</span> 
                      <a href={`https://doi.org/${metadata.doi}`} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline ml-1">
                        {metadata.doi}
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}
            
            {/* Keywords */}
            {metadata.keywords && metadata.keywords.length > 0 && (
              <div>
                <div className="text-xs font-semibold text-gray-500 mb-2">Keywords</div>
                <div className="flex flex-wrap gap-1">
                  {metadata.keywords.map((keyword, idx) => (
                    <Badge key={idx} variant="secondary" className="text-xs">
                      {keyword}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            
            {/* BibTeX Export */}
            {metadata.bibtex_raw && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="text-xs font-semibold text-gray-500">BibTeX Entry</div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        navigator.clipboard.writeText(metadata.bibtex_raw)
                          .then(() => alert('BibTeX copied to clipboard!'))
                          .catch(err => console.error('Failed to copy:', err))
                      }}
                    >
                      <Copy className="h-3 w-3 mr-1" />
                      Copy
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        const blob = new Blob([metadata.bibtex_raw], { type: 'text/plain' })
                        const url = URL.createObjectURL(blob)
                        const a = document.createElement('a')
                        a.href = url
                        a.download = `paper_${paperId}.bib`
                        a.click()
                        URL.revokeObjectURL(url)
                      }}
                    >
                      <Download className="h-3 w-3 mr-1" />
                      Export
                    </Button>
                  </div>
                </div>
                <pre className="bg-gray-50 p-3 rounded text-xs overflow-x-auto max-h-32">
                  {metadata.bibtex_raw}
                </pre>
              </div>
            )}
            
            {/* Identifiers */}
            <div className="flex items-center gap-4 text-xs">
              {metadata.doi && (
                <div className="flex items-center gap-1">
                  <Link className="h-3 w-3" />
                  <span className="text-gray-600">DOI:</span>
                  <span className="font-mono">{metadata.doi}</span>
                </div>
              )}
              {metadata.arxiv_id && (
                <div className="flex items-center gap-1">
                  <Hash className="h-3 w-3" />
                  <span className="text-gray-600">arXiv:</span>
                  <span className="font-mono">{metadata.arxiv_id}</span>
                </div>
              )}
              {metadata.publication_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  <span className="text-gray-600">Date:</span>
                  <span>{metadata.publication_date}</span>
                </div>
              )}
            </div>
          </div>
        )}
        
        {!metadata && !processing && !loadingMetadata && !result && (
          <div className="text-center py-8">
            <FileText className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-3">No metadata extracted yet</p>
            <p className="text-sm text-gray-400">
              Click "Process with GROBID" to extract structured metadata from the PDF
            </p>
          </div>
        )}
      </CardContent>
      
      {/* Metadata Import Dialog */}
      <MetadataImportDialog
        open={showImportDialog}
        onClose={() => setShowImportDialog(false)}
        paperId={paperId}
        grobidMetadata={metadata}
        onImport={handleMetadataImport}
      />
    </Card>
  )
}