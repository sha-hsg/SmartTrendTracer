import { useState, useEffect } from 'react'
import http from '@/services/http'
import {
  Link as LinkIcon,
  Loader2,
  Database,
  Import,
  FileDown
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ReferenceCard } from './ReferenceCard'
import type { Reference, ReferenceWithPapers } from './ReferenceCard'
import { StatisticsCards } from './StatisticsCards'
import type { Statistics } from './StatisticsCards'
import { BibtexDialog, ImportProgressDialog } from './ReferenceDialogs'

interface ImportableReferences {
  arxiv: Reference[]
  doi: Reference[]
  total: number
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
      const response = await http.get(`/api/references/statistics`)
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

      const response = await http.get(`/api/references/`, { params })
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
      const response = await http.get(`/api/references/top-cited`, {
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
      const response = await http.get(`/api/references/importable`, {
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
      const response = await http.post(
        `/api/references/${ref._id}/generate-bibtex`
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
      const response = await http.post(
        `/api/references/${ref._id}/import`
      )

      if (response.data.success) {
        const updatedRefs = references.map(r =>
          r._id === ref._id ? { ...r, is_in_system: true, paper_id: response.data.paper_id } : r
        )
        setReferences(updatedRefs)

        window.open(`/api/papers/${response.data.paper_id}/pdf`, '_blank')
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
    return (
      <ReferenceCard
        key={ref._id}
        ref_data={ref}
        isExpanded={expandedRows.has(ref._id)}
        isSelected={selectedReferences.has(ref._id)}
        onToggleExpansion={toggleRowExpansion}
        onToggleSelection={toggleSelection}
        onShowBibtex={showBibtex}
        onImportReference={importReference}
        onOpenExternalSearch={openExternalSearch}
      />
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

      {statistics && <StatisticsCards statistics={statistics} />}

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

      <BibtexDialog
        open={showBibtexDialog}
        onOpenChange={setShowBibtexDialog}
        bibtex={selectedBibtex}
      />

      <ImportProgressDialog
        open={showImportDialog}
        onOpenChange={setShowImportDialog}
        progress={importProgress}
        importing={importing}
      />
    </div>
  )
}
