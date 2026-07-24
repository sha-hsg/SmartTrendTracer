import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  ArrowRight,
  CheckCircle,
  AlertCircle,
  Loader2,
  GitCompare,
  FileText,
  Users,
  Calendar,
  Hash,
  Link
} from 'lucide-react'

interface MetadataField {
  key: string
  label: string
  current: any
  grobid: any
  selected: boolean
  hasChanges: boolean
}

interface MetadataImportDialogProps {
  open: boolean
  onClose: () => void
  paperId: string
  grobidMetadata: any
  onImport: (selectedFields: Record<string, any>) => void
}

export default function MetadataImportDialog({
  open,
  onClose,
  paperId,
  grobidMetadata,
  onImport
}: MetadataImportDialogProps) {
  const [_currentPaper, setCurrentPaper] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [importing, setImporting] = useState(false)
  const [fields, setFields] = useState<MetadataField[]>([])
  const [selectAll, setSelectAll] = useState(false)

  useEffect(() => {
    if (open && paperId) {
      loadCurrentPaper()
    }
  }, [open, paperId])

  const loadCurrentPaper = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`/api/papers/${paperId}`)
      setCurrentPaper(response.data)
      compareMetadata(response.data)
    } catch (error) {
      console.error('Failed to load current paper:', error)
    } finally {
      setLoading(false)
    }
  }

  const compareMetadata = (paper: any) => {
    const fieldsToCompare: MetadataField[] = []
    
    // Extract the actual metadata from the nested structure
    const metadata = grobidMetadata?.metadata || grobidMetadata
    
    // Title
    if (metadata?.title) {
      fieldsToCompare.push({
        key: 'title',
        label: 'Title',
        current: paper.title,
        grobid: metadata.title,
        selected: paper.title !== metadata.title,
        hasChanges: paper.title !== metadata.title
      })
    }

    // Authors
    if (metadata?.authors) {
      // Handle paper.authors - it could be a string or array
      let currentAuthorsStr = ''
      if (typeof paper.authors === 'string') {
        currentAuthorsStr = paper.authors
      } else if (Array.isArray(paper.authors)) {
        currentAuthorsStr = paper.authors.join(', ')
      } else if (paper.authors_detailed && Array.isArray(paper.authors_detailed)) {
        // Fallback to authors_detailed if authors is not available
        currentAuthorsStr = paper.authors_detailed.map((a: any) => a.name || '').filter(Boolean).join(', ')
      }
      
      const grobidAuthorsStr = metadata.authors.join(', ')
      fieldsToCompare.push({
        key: 'authors',
        label: 'Authors',
        current: currentAuthorsStr ? currentAuthorsStr.split(', ') : [],
        grobid: metadata.authors,
        selected: currentAuthorsStr !== grobidAuthorsStr,
        hasChanges: currentAuthorsStr !== grobidAuthorsStr
      })
    }

    // Abstract
    if (metadata?.abstract) {
      fieldsToCompare.push({
        key: 'abstract',
        label: 'Abstract',
        current: paper.abstract,
        grobid: metadata.abstract,
        selected: paper.abstract !== metadata.abstract,
        hasChanges: paper.abstract !== metadata.abstract
      })
    }

    // Publication Date
    if (metadata?.publication_date) {
      fieldsToCompare.push({
        key: 'publication_date',
        label: 'Publication Date',
        current: paper.publication_date,
        grobid: metadata.publication_date,
        selected: paper.publication_date !== metadata.publication_date,
        hasChanges: paper.publication_date !== metadata.publication_date
      })
    }

    // Year
    if (metadata?.year) {
      fieldsToCompare.push({
        key: 'year',
        label: 'Year',
        current: paper.year,
        grobid: parseInt(metadata.year),
        selected: paper.year !== parseInt(metadata.year),
        hasChanges: paper.year !== parseInt(metadata.year)
      })
    }

    // Journal
    if (metadata?.journal) {
      fieldsToCompare.push({
        key: 'journal',
        label: 'Journal/Venue',
        current: paper.venue || paper.journal,
        grobid: metadata.journal,
        selected: (paper.venue || paper.journal) !== metadata.journal,
        hasChanges: (paper.venue || paper.journal) !== metadata.journal
      })
    }

    // DOI
    if (metadata?.doi) {
      fieldsToCompare.push({
        key: 'doi',
        label: 'DOI',
        current: paper.doi,
        grobid: metadata.doi,
        selected: paper.doi !== metadata.doi,
        hasChanges: paper.doi !== metadata.doi
      })
    }

    // ArXiv ID
    if (metadata?.eprint) {
      const arxivId = metadata.eprint.replace('arXiv:', '').replace('[cs.CL]', '').trim()
      fieldsToCompare.push({
        key: 'arxiv_id',
        label: 'ArXiv ID',
        current: paper.arxiv_id,
        grobid: arxivId,
        selected: paper.arxiv_id !== arxivId,
        hasChanges: paper.arxiv_id !== arxivId
      })
    }

    // Volume
    if (metadata?.volume) {
      fieldsToCompare.push({
        key: 'volume',
        label: 'Volume',
        current: paper.volume,
        grobid: metadata.volume,
        selected: paper.volume !== metadata.volume,
        hasChanges: paper.volume !== metadata.volume
      })
    }

    // Pages
    if (metadata?.pages) {
      fieldsToCompare.push({
        key: 'pages',
        label: 'Pages',
        current: paper.pages,
        grobid: metadata.pages,
        selected: paper.pages !== metadata.pages,
        hasChanges: paper.pages !== metadata.pages
      })
    }

    // BibTeX
    if (metadata?.bibtex_raw || metadata?.bibtex) {
      const bibtexValue = metadata.bibtex_raw || metadata.bibtex
      fieldsToCompare.push({
        key: 'bibtex',
        label: 'BibTeX Entry',
        current: paper.bibtex,
        grobid: bibtexValue,
        selected: !paper.bibtex || paper.bibtex !== bibtexValue,
        hasChanges: paper.bibtex !== bibtexValue
      })
    }

    setFields(fieldsToCompare)
  }

  const toggleField = (key: string) => {
    setFields(fields.map(field =>
      field.key === key ? { ...field, selected: !field.selected } : field
    ))
  }

  const toggleSelectAll = () => {
    const newSelectAll = !selectAll
    setSelectAll(newSelectAll)
    setFields(fields.map(field => ({ ...field, selected: newSelectAll && field.hasChanges })))
  }

  const handleImport = async () => {
    setImporting(true)
    
    // Build the update object with only selected fields
    const updateData: Record<string, any> = {}
    fields.forEach(field => {
      if (field.selected && field.hasChanges) {
        if (field.key === 'year' && field.grobid) {
          updateData[field.key] = parseInt(field.grobid)
        } else if (field.key === 'journal' && field.grobid) {
          updateData['venue'] = field.grobid
        } else {
          updateData[field.key] = field.grobid
        }
      }
    })

    try {
      await onImport(updateData)
      onClose()
    } catch (error) {
      console.error('Failed to import metadata:', error)
    } finally {
      setImporting(false)
    }
  }

  const renderFieldValue = (value: any, key: string) => {
    if (value === null || value === undefined || value === '') {
      return <span className="text-gray-400 italic">Not set</span>
    }
    
    if (key === 'authors' && Array.isArray(value)) {
      return (
        <div className="space-y-1">
          {value.map((author, idx) => (
            <div key={idx} className="text-xs">{author}</div>
          ))}
        </div>
      )
    }
    
    if (key === 'abstract' || key === 'bibtex') {
      return (
        <div className="text-xs max-h-20 overflow-y-auto">
          {value.length > 100 ? value.substring(0, 100) + '...' : value}
        </div>
      )
    }
    
    return <span className="text-sm">{value}</span>
  }

  const getFieldIcon = (key: string) => {
    switch (key) {
      case 'title': return <FileText className="h-4 w-4" />
      case 'authors': return <Users className="h-4 w-4" />
      case 'publication_date': return <Calendar className="h-4 w-4" />
      case 'year': return <Calendar className="h-4 w-4" />
      case 'doi': return <Link className="h-4 w-4" />
      case 'arxiv_id': return <Hash className="h-4 w-4" />
      default: return null
    }
  }

  const changedFieldsCount = fields.filter(f => f.selected && f.hasChanges).length
  const totalChanges = fields.filter(f => f.hasChanges).length

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GitCompare className="h-5 w-5" />
            Import GROBID Metadata
          </DialogTitle>
          <DialogDescription>
            Compare and select which metadata fields to import from GROBID extraction
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading current metadata...</span>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Badge variant="outline">{totalChanges} changes available</Badge>
                <Badge variant="default">{changedFieldsCount} selected</Badge>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={toggleSelectAll}
              >
                {selectAll ? 'Deselect All' : 'Select All Changes'}
              </Button>
            </div>

            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-4">
                {fields.map((field) => (
                  <div key={field.key} className="border rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <Checkbox
                        checked={field.selected}
                        onCheckedChange={() => toggleField(field.key)}
                        disabled={!field.hasChanges}
                        className="mt-1"
                      />
                      
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          {getFieldIcon(field.key)}
                          <span className="font-medium text-sm">{field.label}</span>
                          {field.hasChanges ? (
                            <Badge variant="outline" className="text-xs">
                              <AlertCircle className="h-3 w-3 mr-1" />
                              Different
                            </Badge>
                          ) : (
                            <Badge variant="secondary" className="text-xs">
                              <CheckCircle className="h-3 w-3 mr-1" />
                              Same
                            </Badge>
                          )}
                        </div>
                        
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <div className="text-xs font-semibold text-gray-500 mb-1">Current</div>
                            <div className="p-2 bg-gray-50 rounded">
                              {renderFieldValue(field.current, field.key)}
                            </div>
                          </div>
                          
                          <div>
                            <div className="text-xs font-semibold text-gray-500 mb-1">
                              GROBID {field.selected && field.hasChanges && (
                                <span className="text-green-600">(will import)</span>
                              )}
                            </div>
                            <div className={`p-2 rounded ${
                              field.selected && field.hasChanges 
                                ? 'bg-green-50 border border-green-200' 
                                : 'bg-gray-50'
                            }`}>
                              {renderFieldValue(field.grobid, field.key)}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {totalChanges === 0 && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  All metadata fields are already up to date. No changes to import.
                </AlertDescription>
              </Alert>
            )}
          </>
        )}

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={importing}>
            Cancel
          </Button>
          <Button
            onClick={handleImport}
            disabled={importing || loading || changedFieldsCount === 0}
          >
            {importing ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Importing...
              </>
            ) : (
              <>
                <ArrowRight className="h-4 w-4 mr-2" />
                Import {changedFieldsCount} Field{changedFieldsCount !== 1 ? 's' : ''}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}