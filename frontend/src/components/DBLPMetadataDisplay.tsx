import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { 
  Copy, 
  Download, 
  ExternalLink, 
  Calendar, 
  Users, 
  BookOpen, 
  FileText,
  Hash,
  Globe,
  Building,
  CheckCircle
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface DBLPMetadata {
  title?: string
  authors?: Array<{ name: string; dblp_url?: string; orcid?: string }>
  venue?: string
  year?: string
  month?: string
  volume?: string
  number?: string
  pages?: string
  doi?: string
  ee?: string
  publisher?: string
  series?: string
  type?: string
  dblp_key?: string
  dblp_url?: string
  bibtex?: string
  publication_date?: string
}

interface DBLPMetadataDisplayProps {
  paperId: number
  paper: any
  className?: string
}

export const DBLPMetadataDisplay: React.FC<DBLPMetadataDisplayProps> = ({ 
  paperId, 
  paper,
  className 
}) => {
  const [metadata, setMetadata] = useState<DBLPMetadata | null>(null)
  const [copiedBibtex, setCopiedBibtex] = useState(false)
  const [showFullBibtex, setShowFullBibtex] = useState(false)
  const [bibtex, setBibtex] = useState<string>('')
  const [_loadingBibtex, setLoadingBibtex] = useState(false)

  // Initialize with paper's existing metadata ONLY if it has DBLP data
  useEffect(() => {
    if (paper && paper.dblp_key) {
      // Only show metadata if paper has been linked to DBLP
      setMetadata({
        title: paper.title,
        authors: typeof paper.authors === 'string' 
          ? paper.authors.split(',').map((a: string) => ({ name: a.trim() })) 
          : paper.authors || [],
        venue: paper.conference || paper.journal,
        year: paper.publication_date ? new Date(paper.publication_date).getFullYear().toString() : '',
        doi: paper.doi,
        type: paper.conference ? 'inproceedings' : paper.journal ? 'article' : 'misc',
        pages: paper.pages,
        volume: paper.volume,
        number: paper.number,
        publisher: paper.publisher,
        dblp_key: paper.dblp_key,
        dblp_url: paper.dblp_url,
        bibtex: paper.bibtex  // Use existing BibTeX if available
      })
      
      // Only fetch BibTeX if we don't have it yet
      if (paper.dblp_key && !paper.bibtex) {
        generateBibtex()
      } else if (paper.bibtex) {
        setBibtex(paper.bibtex)
      }
    }
  }, [paper])

  // Generate BibTeX from current metadata
  const generateBibtex = async () => {
    if (!paperId) return
    
    setLoadingBibtex(true)
    try {
      const response = await axios.get(`http://localhost:8000/api/dblp/generate-bibtex/${paperId}`)
      setBibtex(response.data.bibtex || '')
    } catch (err) {
      console.error('Failed to generate BibTeX:', err)
      setBibtex('')
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
    if (bibtex) {
      const blob = new Blob([bibtex], { type: 'text/plain' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${metadata?.dblp_key?.replace('/', '_') || `paper_${paperId}`}.bib`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }
  }

  const formatBibtexForDisplay = (bibtex: string) => {
    // Add syntax highlighting to BibTeX
    return bibtex
      .replace(/(@\w+)\{([^,]+),/g, '<span class="text-purple-600 font-bold">$1</span>{<span class="text-blue-600">$2</span>,')
      .replace(/(\w+)\s*=\s*\{/g, '<span class="text-green-600">$1</span> = {')
      .replace(/\{([^}]+)\}/g, '{<span class="text-gray-700">$1</span>}')
  }

  // Only show if paper has DBLP metadata
  if (!metadata || !paper?.dblp_key) {
    return null
  }

  return (
    <Card className={cn("mt-4", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold flex items-center gap-2">
            <FileText className="h-4 w-4" />
            Citation & Metadata
          </CardTitle>
          <div className="flex items-center gap-2">
            {metadata?.dblp_url && (
              <a
                href={metadata.dblp_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-blue-600 hover:underline flex items-center gap-1"
              >
                <ExternalLink className="h-3 w-3" />
                DBLP
              </a>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {metadata && (
          <>
            {/* Metadata Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              {/* Authors */}
              {metadata.authors && metadata.authors.length > 0 && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-gray-500">
                    <Users className="h-3 w-3" />
                    <span className="text-xs">Authors</span>
                  </div>
                  <div className="text-gray-700">
                    {metadata.authors.map((author, idx) => (
                      <span key={idx}>
                        {author.dblp_url ? (
                          <a
                            href={author.dblp_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:underline hover:text-blue-600"
                          >
                            {author.name}
                          </a>
                        ) : (
                          author.name
                        )}
                        {idx < (metadata.authors?.length ?? 0) - 1 && ', '}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Venue */}
              {metadata.venue && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-gray-500">
                    <BookOpen className="h-3 w-3" />
                    <span className="text-xs">Venue</span>
                  </div>
                  <div className="text-gray-700">{metadata.venue}</div>
                </div>
              )}

              {/* Year */}
              {metadata.year && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-gray-500">
                    <Calendar className="h-3 w-3" />
                    <span className="text-xs">Year</span>
                  </div>
                  <div className="text-gray-700">{metadata.year}</div>
                </div>
              )}

              {/* Pages */}
              {metadata.pages && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-gray-500">
                    <FileText className="h-3 w-3" />
                    <span className="text-xs">Pages</span>
                  </div>
                  <div className="text-gray-700">{metadata.pages}</div>
                </div>
              )}

              {/* Volume/Number */}
              {(metadata.volume || metadata.number) && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-gray-500">
                    <Hash className="h-3 w-3" />
                    <span className="text-xs">Volume/Issue</span>
                  </div>
                  <div className="text-gray-700">
                    {metadata.volume && `Vol. ${metadata.volume}`}
                    {metadata.volume && metadata.number && ', '}
                    {metadata.number && `No. ${metadata.number}`}
                  </div>
                </div>
              )}

              {/* Publisher */}
              {metadata.publisher && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-gray-500">
                    <Building className="h-3 w-3" />
                    <span className="text-xs">Publisher</span>
                  </div>
                  <div className="text-gray-700">{metadata.publisher}</div>
                </div>
              )}

              {/* DOI */}
              {metadata.doi && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-gray-500">
                    <Globe className="h-3 w-3" />
                    <span className="text-xs">DOI</span>
                  </div>
                  <a
                    href={`https://doi.org/${metadata.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:underline text-xs break-all"
                  >
                    {metadata.doi}
                  </a>
                </div>
              )}

              {/* Type */}
              {metadata.type && (
                <div className="space-y-1">
                  <div className="flex items-center gap-1 text-gray-500">
                    <FileText className="h-3 w-3" />
                    <span className="text-xs">Type</span>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {metadata.type}
                  </Badge>
                </div>
              )}
            </div>

            {/* BibTeX Section */}
            {(bibtex || metadata.bibtex) && (
              <>
                <Separator />
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-medium">BibTeX Citation</h4>
                    <div className="flex gap-1">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setShowFullBibtex(!showFullBibtex)}
                        className="h-7 px-2 text-xs"
                      >
                        {showFullBibtex ? 'Collapse' : 'Expand'}
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleDownloadBibtex}
                        className="h-7 px-2"
                      >
                        <Download className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={handleCopyBibtex}
                        className="h-7 px-2"
                      >
                        {copiedBibtex ? (
                          <CheckCircle className="h-3 w-3 text-green-600" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </Button>
                    </div>
                  </div>
                  
                  <div className={cn(
                    "bg-gray-50 dark:bg-gray-900 rounded-md p-3 font-mono text-xs overflow-hidden transition-all",
                    showFullBibtex ? "max-h-96" : "max-h-24"
                  )}>
                    {showFullBibtex ? (
                      <ScrollArea className="h-full">
                        <pre className="whitespace-pre-wrap break-words">
                          <code 
                            dangerouslySetInnerHTML={{ 
                              __html: formatBibtexForDisplay(bibtex || metadata.bibtex || '') 
                            }}
                          />
                        </pre>
                      </ScrollArea>
                    ) : (
                      <pre className="whitespace-pre-wrap break-words line-clamp-3">
                        <code>{bibtex || metadata.bibtex || ''}</code>
                      </pre>
                    )}
                  </div>
                </div>
              </>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}