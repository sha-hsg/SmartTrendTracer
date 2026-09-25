import { useState, useEffect } from 'react'
import http from '@/services/http'
import {
  BookOpen, 
  ExternalLink, 
  Search, 
  Loader2, 
  AlertCircle,
  Calendar,
  Users,
  FileText
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'

interface Reference {
  id?: string
  title: string
  authors?: string[]
  year?: string
  venue?: string
  doi?: string
  arxiv?: string
  pages?: string
}

interface PaperReferencesProps {
  paperId: string | number
  paperTitle?: string
}

export default function PaperReferences({ paperId, paperTitle: _paperTitle }: PaperReferencesProps) {
  const [references, setReferences] = useState<Reference[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [processingGrobid, setProcessingGrobid] = useState(false)

  const loadReferences = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await http.get(
        `/api/papers/${paperId}/references`
      )
      setReferences(response.data.references || [])
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError('References not available. Process the paper with GROBID first.')
      } else {
        setError('Failed to load references')
      }
      console.error('Error loading references:', err)
    } finally {
      setLoading(false)
    }
  }

  const processWithGrobid = async () => {
    setProcessingGrobid(true)
    setError(null)
    
    try {
      const response = await http.post(
        `/api/papers/${paperId}/grobid/process`
      )
      
      if (response.data.success) {
        // Reload references after processing
        await loadReferences()
      }
    } catch (err: any) {
      setError('Failed to process paper with GROBID')
      console.error('Error processing with GROBID:', err)
    } finally {
      setProcessingGrobid(false)
    }
  }

  const filteredReferences = references.filter(ref => {
    if (!searchTerm) return true
    const searchLower = searchTerm.toLowerCase()
    return (
      ref.title?.toLowerCase().includes(searchLower) ||
      ref.authors?.join(' ').toLowerCase().includes(searchLower) ||
      ref.venue?.toLowerCase().includes(searchLower) ||
      ref.year?.includes(searchTerm)
    )
  })

  const openGoogleScholar = (ref: Reference) => {
    const query = encodeURIComponent(`${ref.title} ${ref.authors?.join(' ') || ''}`)
    window.open(`https://scholar.google.com/scholar?q=${query}`, '_blank')
  }

  const openDoi = (doi: string) => {
    window.open(`https://doi.org/${doi}`, '_blank')
  }

  const openArxiv = (arxivId: string) => {
    window.open(`https://arxiv.org/abs/${arxivId}`, '_blank')
  }

  useEffect(() => {
    loadReferences()
  }, [paperId])

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <BookOpen className="h-5 w-5" />
              References ({references.length})
            </CardTitle>
            <CardDescription>
              Extracted bibliography and citations
            </CardDescription>
          </div>
          {references.length === 0 && !loading && (
            <Button
              size="sm"
              onClick={processWithGrobid}
              disabled={processingGrobid}
            >
              {processingGrobid ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  Processing...
                </>
              ) : (
                <>
                  <FileText className="h-4 w-4 mr-1" />
                  Extract with GROBID
                </>
              )}
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent>
        {loading && (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-500" />
            <span className="ml-2 text-gray-600">Loading references...</span>
          </div>
        )}
        
        {error && (
          <Alert className="mb-4">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {references.length > 0 && !loading && (
          <>
            <div className="mb-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
                <Input
                  type="text"
                  placeholder="Search references..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-3">
                {filteredReferences.map((ref, idx) => (
                  <Card key={idx} className="hover:shadow-md transition-shadow">
                    <CardContent className="pt-4">
                      <div className="space-y-2">
                        {/* Title */}
                        <h4 className="font-semibold text-sm leading-tight">
                          [{idx + 1}] {ref.title || 'Untitled'}
                        </h4>
                        
                        {/* Authors */}
                        {ref.authors && ref.authors.length > 0 && (
                          <div className="flex items-center gap-1 text-xs text-gray-600">
                            <Users className="h-3 w-3" />
                            <span>{Array.isArray(ref.authors) ? ref.authors.join(', ') : ref.authors}</span>
                          </div>
                        )}
                        
                        {/* Venue and Year */}
                        <div className="flex items-center gap-3 text-xs text-gray-600">
                          {ref.venue && (
                            <div className="flex items-center gap-1">
                              <BookOpen className="h-3 w-3" />
                              <span>{ref.venue}</span>
                            </div>
                          )}
                          {ref.year && (
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3" />
                              <span>{ref.year}</span>
                            </div>
                          )}
                          {ref.pages && (
                            <span className="text-gray-500">pp. {ref.pages}</span>
                          )}
                        </div>
                        
                        {/* Links */}
                        <div className="flex items-center gap-2 mt-2">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => openGoogleScholar(ref)}
                            className="h-7 px-2 text-xs"
                          >
                            <Search className="h-3 w-3 mr-1" />
                            Google Scholar
                          </Button>
                          
                          {ref.doi && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openDoi(ref.doi!)}
                              className="h-7 px-2 text-xs"
                            >
                              <ExternalLink className="h-3 w-3 mr-1" />
                              DOI
                            </Button>
                          )}
                          
                          {ref.arxiv && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openArxiv(ref.arxiv!)}
                              className="h-7 px-2 text-xs"
                            >
                              <ExternalLink className="h-3 w-3 mr-1" />
                              arXiv
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </ScrollArea>
            
            {filteredReferences.length === 0 && searchTerm && (
              <div className="text-center py-8 text-gray-500">
                No references found matching "{searchTerm}"
              </div>
            )}
          </>
        )}
        
        {references.length === 0 && !loading && !error && (
          <div className="text-center py-8">
            <BookOpen className="h-12 w-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-500 mb-3">No references extracted yet</p>
            <p className="text-sm text-gray-400">
              Click "Extract with GROBID" to process the paper and extract references
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}