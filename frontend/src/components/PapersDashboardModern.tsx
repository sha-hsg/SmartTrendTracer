import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { 
  FileText, 
  Upload, 
  Search, 
  Filter, 
  Calendar, 
  User, 
  Building2, 
  Tag as TagIcon, 
  Eye,
  Download,
  Plus,
  BookOpen,
  BarChart3,
  Users,
  Hash
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'

import PaperUploadModern from './PaperUploadModern'
import PaperViewerModern from './PaperViewerModern'

interface Paper {
  id: number
  title: string
  abstract?: string
  authors: Array<{ name: string; email?: string }>
  publication_date?: string
  conference?: string
  journal?: string
  arxiv_id?: string
  doi?: string
  page_count: number
  tags: string[]
  created_at: string
  processed: boolean
}

interface PapersStats {
  total_papers: number
  total_authors: number
  total_tags: number
  total_snippets: number
  recent_papers: Array<{ id: number; title: string; created_at: string }>
  top_tags: Array<{ tag: string; count: number }>
}

const PapersDashboardModern: React.FC = () => {
  const [activeTab, setActiveTab] = useState('browse')
  const [papers, setPapers] = useState<Paper[]>([])
  const [stats, setStats] = useState<PapersStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPaperId, setSelectedPaperId] = useState<number | null>(null)
  const [searchMode, setSearchMode] = useState<'standard' | 'semantic'>('standard')
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [authorFilter, setAuthorFilter] = useState('')
  const [tagFilter, setTagFilter] = useState('')
  const [conferenceFilter, setConferenceFilter] = useState('')
  const [yearFilter, setYearFilter] = useState('')
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPapers, setTotalPapers] = useState(0)
  const pageSize = 20

  useEffect(() => {
    loadStats()
    if (activeTab === 'browse') {
      loadPapers()
    }
  }, [activeTab, searchTerm, authorFilter, tagFilter, conferenceFilter, yearFilter, currentPage])

  const loadStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/papers/stats/overview')
      setStats(response.data)
    } catch (err: any) {
      console.error('Failed to load stats:', err)
    }
  }

  const loadPapers = async () => {
    setLoading(true)
    setError(null)
    
    try {
      if (searchMode === 'semantic' && searchTerm) {
        // Use semantic search
        const response = await axios.get(`http://localhost:8000/api/papers/search`, {
          params: { q: searchTerm, limit: pageSize }
        })
        
        // Convert search results to paper format
        const paperIds = response.data.results.map((r: any) => r.paper_id)
        if (paperIds.length > 0) {
          // Load full paper details for search results
          const papersPromises = paperIds.map((id: number) => 
            axios.get(`http://localhost:8000/api/papers/${id}`)
          )
          const papersResponses = await Promise.all(papersPromises)
          setPapers(papersResponses.map(r => r.data))
          setTotalPapers(papersResponses.length)
        } else {
          setPapers([])
          setTotalPapers(0)
        }
      } else {
        // Use standard filtering
        const params = new URLSearchParams({
          page: currentPage.toString(),
          page_size: pageSize.toString()
        })
        
        if (searchTerm) params.append('search', searchTerm)
        if (authorFilter) params.append('author', authorFilter)
        if (tagFilter) params.append('tag', tagFilter)
        if (conferenceFilter) params.append('conference', conferenceFilter)
        if (yearFilter) params.append('year', yearFilter)
        
        const response = await axios.get(`http://localhost:8000/api/papers?${params}`)
        setPapers(response.data.papers)
        setTotalPapers(response.data.total)
      }
    } catch (err: any) {
      setError('Failed to load papers: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const handleUploadComplete = (uploadedPapers: any[]) => {
    // Refresh the stats and papers list
    loadStats()
    if (activeTab === 'browse') {
      loadPapers()
    }
    // Switch to browse tab to see uploaded papers
    setActiveTab('browse')
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const clearFilters = () => {
    setSearchTerm('')
    setAuthorFilter('')
    setTagFilter('')
    setConferenceFilter('')
    setYearFilter('')
    setCurrentPage(1)
  }

  const totalPages = Math.ceil(totalPapers / pageSize)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Research Papers</h1>
          <p className="text-gray-600">Upload, analyze, and manage PDF research papers</p>
        </div>
        
        {stats && (
          <div className="grid grid-cols-4 gap-4 text-center">
            <div className="bg-white p-3 rounded-lg border">
              <div className="flex items-center justify-center mb-1">
                <FileText className="h-4 w-4 text-blue-600" />
              </div>
              <div className="text-lg font-bold text-gray-900">{stats.total_papers}</div>
              <div className="text-xs text-gray-500">Papers</div>
            </div>
            <div className="bg-white p-3 rounded-lg border">
              <div className="flex items-center justify-center mb-1">
                <Users className="h-4 w-4 text-green-600" />
              </div>
              <div className="text-lg font-bold text-gray-900">{stats.total_authors}</div>
              <div className="text-xs text-gray-500">Authors</div>
            </div>
            <div className="bg-white p-3 rounded-lg border">
              <div className="flex items-center justify-center mb-1">
                <Hash className="h-4 w-4 text-purple-600" />
              </div>
              <div className="text-lg font-bold text-gray-900">{stats.total_tags}</div>
              <div className="text-xs text-gray-500">Tags</div>
            </div>
            <div className="bg-white p-3 rounded-lg border">
              <div className="flex items-center justify-center mb-1">
                <BookOpen className="h-4 w-4 text-orange-600" />
              </div>
              <div className="text-lg font-bold text-gray-900">{stats.total_snippets}</div>
              <div className="text-xs text-gray-500">Snippets</div>
            </div>
          </div>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="upload" className="flex items-center gap-2">
            <Upload className="h-4 w-4" />
            Upload
          </TabsTrigger>
          <TabsTrigger value="browse" className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Browse
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <BarChart3 className="h-4 w-4" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload">
          <PaperUploadModern onUploadComplete={handleUploadComplete} />
        </TabsContent>

        <TabsContent value="browse">
          <div className="space-y-4">
            {/* Filters */}
            <Card>
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Filter Papers</CardTitle>
                  <div className="flex items-center gap-2">
                    <Select value={searchMode} onValueChange={(value: any) => setSearchMode(value)}>
                      <SelectTrigger className="w-40">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="standard">Standard Search</SelectItem>
                        <SelectItem value="semantic">AI Search</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button variant="ghost" size="sm" onClick={clearFilters}>
                      Clear Filters
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                  <div className="relative">
                    <Input
                      placeholder={searchMode === 'semantic' ? "Ask a question..." : "Search title, abstract..."}
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && loadPapers()}
                      className="w-full pr-10"
                    />
                    {searchMode === 'semantic' && (
                      <Badge variant="secondary" className="absolute right-2 top-1/2 -translate-y-1/2 text-xs">
                        AI
                      </Badge>
                    )}
                  </div>
                  <div>
                    <Input
                      placeholder="Author name..."
                      value={authorFilter}
                      onChange={(e) => setAuthorFilter(e.target.value)}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <Input
                      placeholder="Tag..."
                      value={tagFilter}
                      onChange={(e) => setTagFilter(e.target.value)}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <Input
                      placeholder="Conference..."
                      value={conferenceFilter}
                      onChange={(e) => setConferenceFilter(e.target.value)}
                      className="w-full"
                    />
                  </div>
                  <div>
                    <Input
                      placeholder="Year..."
                      type="number"
                      value={yearFilter}
                      onChange={(e) => setYearFilter(e.target.value)}
                      className="w-full"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Papers List */}
            {error && (
              <Alert className="border-red-200 bg-red-50">
                <AlertDescription className="text-red-800">
                  {error}
                </AlertDescription>
              </Alert>
            )}

            {loading ? (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-500">Loading papers...</p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="grid gap-4">
                  {papers.map((paper) => (
                    <Card key={paper.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-6">
                        <div className="flex justify-between items-start mb-3">
                          <div className="flex-1 min-w-0">
                            <h3 className="text-lg font-semibold text-gray-900 mb-2 line-clamp-2">
                              {paper.title}
                            </h3>
                            
                            {paper.abstract && (
                              <p className="text-sm text-gray-600 mb-3 line-clamp-3">
                                {paper.abstract}
                              </p>
                            )}
                            
                            <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 mb-3">
                              {paper.authors.length > 0 && (
                                <div className="flex items-center gap-1">
                                  <User className="h-3 w-3" />
                                  <span>{paper.authors.map(a => a.name).join(', ')}</span>
                                </div>
                              )}
                              
                              {paper.conference && (
                                <div className="flex items-center gap-1">
                                  <Building2 className="h-3 w-3" />
                                  <span>{paper.conference}</span>
                                </div>
                              )}
                              
                              {paper.publication_date && (
                                <div className="flex items-center gap-1">
                                  <Calendar className="h-3 w-3" />
                                  <span>{formatDate(paper.publication_date)}</span>
                                </div>
                              )}
                              
                              <div className="flex items-center gap-1">
                                <FileText className="h-3 w-3" />
                                <span>{paper.page_count} pages</span>
                              </div>
                            </div>
                            
                            {/* Tags */}
                            {paper.tags.length > 0 && (
                              <div className="flex flex-wrap gap-1 mb-3">
                                {paper.tags.slice(0, 5).map((tag, index) => (
                                  <Badge key={index} variant="secondary" className="text-xs">
                                    {tag}
                                  </Badge>
                                ))}
                                {paper.tags.length > 5 && (
                                  <Badge variant="outline" className="text-xs">
                                    +{paper.tags.length - 5} more
                                  </Badge>
                                )}
                              </div>
                            )}
                            
                            <div className="flex items-center gap-2 text-xs text-gray-400">
                              <span>Added {formatDate(paper.created_at)}</span>
                              {paper.processed && (
                                <Badge variant="secondary" className="bg-green-100 text-green-800">
                                  Processed
                                </Badge>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex flex-col gap-2 ml-4">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => setSelectedPaperId(paper.id)}
                            >
                              <Eye className="h-4 w-4 mr-2" />
                              View
                            </Button>
                            <Button size="sm" variant="ghost">
                              <TagIcon className="h-4 w-4 mr-2" />
                              Tag
                            </Button>
                          </div>
                        </div>
                        
                        {(paper.arxiv_id || paper.doi) && (
                          <div className="flex gap-4 pt-3 border-t">
                            {paper.arxiv_id && (
                              <a 
                                href={`https://arxiv.org/abs/${paper.arxiv_id}`} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-xs text-blue-600 hover:text-blue-800"
                              >
                                arXiv:{paper.arxiv_id}
                              </a>
                            )}
                            {paper.doi && (
                              <a 
                                href={`https://doi.org/${paper.doi}`} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="text-xs text-blue-600 hover:text-blue-800"
                              >
                                DOI:{paper.doi}
                              </a>
                            )}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-gray-500">
                      Showing {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalPapers)} of {totalPapers} papers
                    </p>
                    <div className="flex items-center gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                        disabled={currentPage === 1}
                      >
                        Previous
                      </Button>
                      <span className="text-sm">
                        Page {currentPage} of {totalPages}
                      </span>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                        disabled={currentPage === totalPages}
                      >
                        Next
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </TabsContent>

        <TabsContent value="analytics">
          <div className="grid gap-6">
            {stats && (
              <>
                {/* Recent Papers */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5" />
                      Recent Papers
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {stats.recent_papers.map((paper) => (
                        <div key={paper.id} className="flex items-center justify-between p-3 border rounded-lg">
                          <div>
                            <p className="font-medium line-clamp-1">{paper.title}</p>
                            <p className="text-sm text-gray-500">{formatDate(paper.created_at)}</p>
                          </div>
                          <Button size="sm" variant="ghost">
                            <Eye className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Top Tags */}
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                      <TagIcon className="h-5 w-5" />
                      Top Tags
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {stats.top_tags.map((tag, index) => (
                        <Badge 
                          key={index} 
                          variant="outline" 
                          className="cursor-pointer hover:bg-gray-100"
                          onClick={() => {
                            setTagFilter(tag.tag)
                            setActiveTab('browse')
                          }}
                        >
                          {tag.tag} ({tag.count})
                        </Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </div>
        </TabsContent>
      </Tabs>
      
      {/* Paper Viewer Modal */}
      {selectedPaperId && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-7xl max-h-[90vh] overflow-auto">
            <PaperViewerModern 
              paperId={selectedPaperId} 
              onClose={() => setSelectedPaperId(null)}
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default PapersDashboardModern