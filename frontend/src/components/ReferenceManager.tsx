import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Copy,
  BookOpen,
  ChevronDown,
  ChevronRight,
  FileText,
  Users,
  Calendar,
  Link as LinkIcon,
  CheckCircle,
  Loader2,
  GraduationCap,
  Database,
  Import,
  FileDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter
} from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger
} from '@/components/ui/tooltip'

interface Reference {
  _id: string
  title: string
  authors: string[]
  year: number
  venue: string
  doi: string
  arxiv_id: string
  citation_count: number
  is_in_system: boolean
  paper_id?: string
  cited_by: string[]
  reference_hash: string
  bibtex?: string
}

interface ReferenceWithPapers extends Reference {
  citing_papers_sample?: Array<{
    id: string
    title: string
  }>
}

interface ImportableReferences {
  arxiv: Reference[]
  doi: Reference[]
  total: number
}

interface Statistics {
  total_references: number
  unique_titles: number
  references_with_doi: number
  references_with_arxiv: number
  references_in_system: number
  importable_references: number
  top_cited: Array<{
    title: string
    citation_count: number
    year: number
  }>
  citation_distribution: {
    '1_citation': number
    '2-5_citations': number
    '6-10_citations': number
    'over_10_citations': number
  }
}

export default function ReferenceManager() {
  const [references, setReferences] = useState<Reference[]>([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedReferences, setSelectedReferences] = useState<Set<string>>(new Set())
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set())
  const [activeTab, setActiveTab] = useState('all')
  const [statistics, setStatistics] = useState<Statistics | null>(null)
  const [importableRefs, setImportableRefs] = useState<ImportableReferences | null>(null)
  const [topCited, setTopCited] = useState<ReferenceWithPapers[]>([])
  
  // Filters
  const [yearFilter, setYearFilter] = useState<string>('all')
  const [hasDoiFilter, _setHasDoiFilter] = useState<boolean | null>(null)
  const [inSystemFilter, _setInSystemFilter] = useState<boolean | null>(null)
  const [minCitations, _setMinCitations] = useState<number>(0)
  
  // Dialogs
  const [showBibtexDialog, setShowBibtexDialog] = useState(false)
  const [selectedBibtex, setSelectedBibtex] = useState('')
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [importProgress, setImportProgress] = useState(0)
  const [importing, setImporting] = useState(false)
  
  // Pagination
  const [offset, setOffset] = useState(0)
  const [limit] = useState(50)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    loadStatistics()
    loadReferences()
  }, [])

  useEffect(() => {
    if (activeTab === 'all') {
      loadReferences()
    } else if (activeTab === 'top-cited') {
      loadTopCited()
    } else if (activeTab === 'importable') {
      loadImportable()
    }
  }, [activeTab, searchQuery, yearFilter, hasDoiFilter, inSystemFilter, minCitations, offset])

  const loadStatistics = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/references/statistics')
      setStatistics(response.data)
    } catch (error) {
      console.error('Failed to load statistics:', error)
    }
  }

  const loadReferences = async () => {
    setLoading(true)
    try {
      const params: any = { limit, offset }
      if (searchQuery) params.search = searchQuery
      if (yearFilter && yearFilter !== 'all') params.year = parseInt(yearFilter)
      if (hasDoiFilter !== null) params.has_doi = hasDoiFilter
      if (inSystemFilter !== null) params.in_system = inSystemFilter
      if (minCitations > 0) params.min_citations = minCitations

      const response = await axios.get('http://localhost:8000/api/references/', { params })
      setReferences(response.data.references)
      setTotal(response.data.total)
    } catch (error) {
      console.error('Failed to load references:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadTopCited = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/references/top-cited', {
        params: { limit: 50 }
      })
      setTopCited(response.data)
    } catch (error) {
      console.error('Failed to load top cited:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadImportable = async () => {
    setLoading(true)
    try {
      const response = await axios.get('http://localhost:8000/api/references/importable', {
        params: { limit: 100 }
      })
      setImportableRefs(response.data)
    } catch (error) {
      console.error('Failed to load importable references:', error)
    } finally {
      setLoading(false)
    }
  }

  const toggleRowExpansion = (id: string) => {
    const newExpanded = new Set(expandedRows)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedRows(newExpanded)
  }

  const toggleSelection = (id: string) => {
    const newSelected = new Set(selectedReferences)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedReferences(newSelected)
  }

  const selectAll = () => {
    if (selectedReferences.size === references.length) {
      setSelectedReferences(new Set())
    } else {
      setSelectedReferences(new Set(references.map(r => r._id)))
    }
  }

  const generateBibtex = async (ref: Reference) => {
    try {
      const response = await axios.post(
        `http://localhost:8000/api/references/${ref._id}/generate-bibtex`
      )
      return response.data.bibtex
    } catch (error) {
      console.error('Failed to generate BibTeX:', error)
      return null
    }
  }

  const showBibtex = async (ref: Reference) => {
    if (ref.bibtex) {
      setSelectedBibtex(ref.bibtex)
    } else {
      const bibtex = await generateBibtex(ref)
      if (bibtex) {
        setSelectedBibtex(bibtex)
      }
    }
    setShowBibtexDialog(true)
  }

  const copyBibtex = () => {
    navigator.clipboard.writeText(selectedBibtex)
  }

  const exportSelectedBibtex = async () => {
    const bibtexEntries: string[] = []
    
    for (const id of selectedReferences) {
      const ref = references.find(r => r._id === id)
      if (ref) {
        if (ref.bibtex) {
          bibtexEntries.push(ref.bibtex)
        } else {
          const bibtex = await generateBibtex(ref)
          if (bibtex) {
            bibtexEntries.push(bibtex)
          }
        }
      }
    }

    const blob = new Blob([bibtexEntries.join('\n\n')], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'references.bib'
    a.click()
    URL.revokeObjectURL(url)
  }

  const importReference = async (ref: Reference) => {
    try {
      const response = await axios.post(
        `http://localhost:8000/api/references/${ref._id}/import`
      )
      
      if (response.data.success) {
        // Update the reference to mark it as in system
        const updatedRefs = references.map(r => 
          r._id === ref._id ? { ...r, is_in_system: true, paper_id: response.data.paper_id } : r
        )
        setReferences(updatedRefs)
        
        // Open the paper in a new tab
        window.open(`/papers/${response.data.paper_id}`, '_blank')
      }
    } catch (error: any) {
      console.error('Failed to import reference:', error)
      alert(error.response?.data?.detail || 'Failed to import reference')
    }
  }

  const batchImport = async () => {
    setImporting(true)
    setShowImportDialog(true)
    setImportProgress(0)
    
    const selectedRefs = Array.from(selectedReferences)
    const total = selectedRefs.length
    
    for (let i = 0; i < selectedRefs.length; i++) {
      const ref = references.find(r => r._id === selectedRefs[i])
      if (ref && !ref.is_in_system) {
        try {
          await importReference(ref)
        } catch (error) {
          console.error(`Failed to import ${ref.title}:`, error)
        }
      }
      setImportProgress(((i + 1) / total) * 100)
    }
    
    setImporting(false)
    setTimeout(() => {
      setShowImportDialog(false)
      setImportProgress(0)
      loadReferences() // Refresh the list
    }, 2000)
  }

  const openExternalSearch = (ref: Reference, service: string) => {
    let url = ''
    const query = encodeURIComponent(`${ref.title} ${ref.authors?.[0] || ''} ${ref.year || ''}`)
    
    switch (service) {
      case 'google-scholar':
        url = `https://scholar.google.com/scholar?q=${query}`
        break
      case 'arxiv':
        if (ref.arxiv_id) {
          url = `https://arxiv.org/abs/${ref.arxiv_id}`
        } else {
          url = `https://arxiv.org/search/?query=${query}&searchtype=all`
        }
        break
      case 'doi':
        if (ref.doi) {
          url = `https://doi.org/${ref.doi}`
        }
        break
      case 'semantic-scholar':
        url = `https://www.semanticscholar.org/search?q=${query}`
        break
      case 'pubmed':
        url = `https://pubmed.ncbi.nlm.nih.gov/?term=${query}`
        break
    }
    
    if (url) {
      window.open(url, '_blank')
    }
  }

  const renderReferenceRow = (ref: Reference | ReferenceWithPapers) => {
    const isExpanded = expandedRows.has(ref._id)
    const isSelected = selectedReferences.has(ref._id)
    
    return (
      <div key={ref._id} className="border rounded-lg mb-2">
        <div className="p-4">
          <div className="flex items-start gap-3">
            <Checkbox
              checked={isSelected}
              onCheckedChange={() => toggleSelection(ref._id)}
              className="mt-1"
            />
            
            <button
              onClick={() => toggleRowExpansion(ref._id)}
              className="mt-1 text-gray-500 hover:text-gray-700"
            >
              {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </button>
            
            <div className="flex-1">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <h3 className="font-semibold text-sm mb-1">{ref.title || 'Untitled'}</h3>
                  
                  <div className="flex flex-wrap gap-2 mb-2">
                    {ref.authors && ref.authors.length > 0 && (
                      <div className="flex items-center gap-1 text-xs text-gray-600">
                        <Users className="h-3 w-3" />
                        <span>{ref.authors.slice(0, 3).join(', ')}{ref.authors.length > 3 && ' et al.'}</span>
                      </div>
                    )}
                    
                    {ref.year && (
                      <div className="flex items-center gap-1 text-xs text-gray-600">
                        <Calendar className="h-3 w-3" />
                        <span>{ref.year}</span>
                      </div>
                    )}
                    
                    {ref.venue && (
                      <div className="flex items-center gap-1 text-xs text-gray-600">
                        <BookOpen className="h-3 w-3" />
                        <span>{ref.venue}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="flex flex-wrap gap-2">
                    {ref.is_in_system && (
                      <Badge variant="default" className="text-xs">
                        <CheckCircle className="h-3 w-3 mr-1" />
                        In Library
                      </Badge>
                    )}
                    
                    {ref.doi && (
                      <Badge variant="outline" className="text-xs">
                        DOI
                      </Badge>
                    )}
                    
                    {ref.arxiv_id && (
                      <Badge variant="outline" className="text-xs">
                        ArXiv
                      </Badge>
                    )}
                    
                    <Badge variant="secondary" className="text-xs">
                      {ref.citation_count} citation{ref.citation_count !== 1 ? 's' : ''}
                    </Badge>
                  </div>
                </div>
                
                <div className="flex gap-1">
                  <TooltipProvider>
                    {/* External Search Links */}
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openExternalSearch(ref, 'google-scholar')}
                        >
                          <GraduationCap className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Google Scholar</TooltipContent>
                    </Tooltip>
                    
                    {ref.doi && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openExternalSearch(ref, 'doi')}
                          >
                            <LinkIcon className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Open DOI</TooltipContent>
                      </Tooltip>
                    )}
                    
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openExternalSearch(ref, 'arxiv')}
                        >
                          <Database className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>Search ArXiv</TooltipContent>
                    </Tooltip>
                    
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => showBibtex(ref)}
                        >
                          <FileText className="h-4 w-4" />
                        </Button>
                      </TooltipTrigger>
                      <TooltipContent>View BibTeX</TooltipContent>
                    </Tooltip>
                    
                    {!ref.is_in_system && (ref.doi || ref.arxiv_id) && (
                      <Tooltip>
                        <TooltipTrigger asChild>
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => importReference(ref)}
                          >
                            <Import className="h-4 w-4" />
                          </Button>
                        </TooltipTrigger>
                        <TooltipContent>Import to Library</TooltipContent>
                      </Tooltip>
                    )}
                  </TooltipProvider>
                </div>
              </div>
              
              {isExpanded && (
                <div className="mt-4 pt-4 border-t">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <h4 className="text-sm font-medium mb-2">Details</h4>
                      <div className="space-y-1 text-xs">
                        {ref.doi && (
                          <div>
                            <span className="font-medium">DOI:</span> {ref.doi}
                          </div>
                        )}
                        {ref.arxiv_id && (
                          <div>
                            <span className="font-medium">ArXiv:</span> {ref.arxiv_id}
                          </div>
                        )}
                        <div>
                          <span className="font-medium">Reference ID:</span> {ref._id}
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h4 className="text-sm font-medium mb-2">Cited By</h4>
                      <div className="space-y-1">
                        {'citing_papers_sample' in ref && ref.citing_papers_sample ? (
                          ref.citing_papers_sample.map(paper => (
                            <div key={paper.id} className="text-xs">
                              <a
                                href={`/papers/${paper.id}`}
                                className="text-blue-600 hover:underline"
                                target="_blank"
                                rel="noopener noreferrer"
                              >
                                {paper.title}
                              </a>
                            </div>
                          ))
                        ) : (
                          <div className="text-xs text-gray-500">
                            {ref.cited_by.length} paper{ref.cited_by.length !== 1 ? 's' : ''}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Reference Manager</h1>
        <p className="text-gray-600">
          Manage and explore all references from your research papers
        </p>
      </div>

      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Total References</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_references.toLocaleString()}</div>
              <p className="text-xs text-gray-500">{statistics.unique_titles} unique titles</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">With Identifiers</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.references_with_doi}</div>
              <p className="text-xs text-gray-500">DOI available</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">In Library</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.references_in_system}</div>
              <p className="text-xs text-gray-500">Already imported</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm">Importable</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.importable_references}</div>
              <p className="text-xs text-gray-500">Ready to import</p>
            </CardContent>
          </Card>
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <div className="flex justify-between items-center mb-4">
          <TabsList>
            <TabsTrigger value="all">All References</TabsTrigger>
            <TabsTrigger value="top-cited">Top Cited</TabsTrigger>
            <TabsTrigger value="importable">Importable</TabsTrigger>
          </TabsList>
          
          {selectedReferences.size > 0 && (
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={exportSelectedBibtex}
              >
                <FileDown className="h-4 w-4 mr-2" />
                Export BibTeX ({selectedReferences.size})
              </Button>
              
              {activeTab === 'importable' && (
                <Button
                  variant="default"
                  size="sm"
                  onClick={batchImport}
                >
                  <Import className="h-4 w-4 mr-2" />
                  Import Selected ({selectedReferences.size})
                </Button>
              )}
            </div>
          )}
        </div>

        <TabsContent value="all">
          <Card>
            <CardHeader>
              <div className="flex justify-between items-center">
                <CardTitle>All References</CardTitle>
                <div className="flex gap-2">
                  <Input
                    placeholder="Search references..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-64"
                  />
                  
                  <Select value={yearFilter} onValueChange={setYearFilter}>
                    <SelectTrigger className="w-32">
                      <SelectValue placeholder="Year" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Years</SelectItem>
                      {[2024, 2023, 2022, 2021, 2020].map(year => (
                        <SelectItem key={year} value={year.toString()}>{year}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={selectAll}
                  >
                    {selectedReferences.size === references.length ? 'Deselect All' : 'Select All'}
                  </Button>
                </div>
              </div>
            </CardHeader>
            
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading references...</span>
                </div>
              ) : (
                <>
                  <ScrollArea className="h-[600px]">
                    {references.map(ref => renderReferenceRow(ref))}
                  </ScrollArea>
                  
                  {total > limit && (
                    <div className="flex justify-between items-center mt-4">
                      <div className="text-sm text-gray-500">
                        Showing {offset + 1}-{Math.min(offset + limit, total)} of {total} references
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setOffset(Math.max(0, offset - limit))}
                          disabled={offset === 0}
                        >
                          Previous
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setOffset(offset + limit)}
                          disabled={offset + limit >= total}
                        >
                          Next
                        </Button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="top-cited">
          <Card>
            <CardHeader>
              <CardTitle>Most Cited References</CardTitle>
              <CardDescription>
                Papers referenced most frequently across your library
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading top cited...</span>
                </div>
              ) : (
                <ScrollArea className="h-[600px]">
                  {topCited.map(ref => renderReferenceRow(ref))}
                </ScrollArea>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="importable">
          <Card>
            <CardHeader>
              <CardTitle>Importable References</CardTitle>
              <CardDescription>
                References with DOI or ArXiv ID that can be imported as papers
              </CardDescription>
            </CardHeader>
            
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin" />
                  <span className="ml-2">Loading importable references...</span>
                </div>
              ) : importableRefs ? (
                <div className="space-y-6">
                  {importableRefs.arxiv.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <Database className="h-4 w-4" />
                        ArXiv Papers ({importableRefs.arxiv.length})
                      </h3>
                      <ScrollArea className="h-[300px]">
                        {importableRefs.arxiv.map(ref => renderReferenceRow(ref))}
                      </ScrollArea>
                    </div>
                  )}
                  
                  {importableRefs.doi.length > 0 && (
                    <div>
                      <h3 className="font-semibold mb-3 flex items-center gap-2">
                        <LinkIcon className="h-4 w-4" />
                        Papers with DOI ({importableRefs.doi.length})
                      </h3>
                      <ScrollArea className="h-[300px]">
                        {importableRefs.doi.map(ref => renderReferenceRow(ref))}
                      </ScrollArea>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No importable references found
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* BibTeX Dialog */}
      <Dialog open={showBibtexDialog} onOpenChange={setShowBibtexDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>BibTeX Citation</DialogTitle>
            <DialogDescription>
              Copy this BibTeX entry to use in your LaTeX documents
            </DialogDescription>
          </DialogHeader>
          
          <Textarea
            value={selectedBibtex}
            readOnly
            className="font-mono text-sm h-64"
          />
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowBibtexDialog(false)}>
              Close
            </Button>
            <Button onClick={copyBibtex}>
              <Copy className="h-4 w-4 mr-2" />
              Copy to Clipboard
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Import Progress Dialog */}
      <Dialog open={showImportDialog} onOpenChange={setShowImportDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Importing References</DialogTitle>
            <DialogDescription>
              Importing selected references as papers...
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <Progress value={importProgress} className="mb-2" />
            <p className="text-sm text-center text-gray-500">
              {Math.round(importProgress)}% complete
            </p>
          </div>
          
          {!importing && importProgress === 100 && (
            <Alert>
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>
                Import completed successfully!
              </AlertDescription>
            </Alert>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}