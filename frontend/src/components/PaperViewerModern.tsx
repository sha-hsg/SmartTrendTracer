import React, { useState, useEffect } from 'react'
import axios from 'axios'
import {
  FileText,
  User,
  Calendar,
  Building2,
  BookOpen,
  Tag as TagIcon,
  ExternalLink,
  Download,
  Search,
  Plus,
  X,
  ChevronDown,
  ChevronRight,
  Copy,
  CheckCircle,
  Loader2,
  MessageSquare,
  Hash,
  FileCode
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Alert, AlertDescription } from '@/components/ui/alert'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'
import PDFViewerModern from './PDFViewerModern'

interface PaperSection {
  id: number
  section_type: string
  title: string
  content: string
  position: number
}

interface PaperSnippet {
  id: number
  content: string
  annotation?: string
  category?: string
  created_at: string
  page_number?: number
}

interface PaperAuthor {
  name: string
  email?: string
}

interface Paper {
  id: number
  title: string
  abstract?: string
  content?: string
  authors: PaperAuthor[]
  publication_date?: string
  conference?: string
  journal?: string
  arxiv_id?: string
  doi?: string
  page_count: number
  tags: string[]
  created_at: string
  processed: boolean
  sections?: PaperSection[]
  snippets?: PaperSnippet[]
}

interface PaperViewerModernProps {
  paperId: number
  onClose?: () => void
}

const PaperViewerModern: React.FC<PaperViewerModernProps> = ({ paperId, onClose }) => {
  const [paper, setPaper] = useState<Paper | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set())
  const [copiedText, setCopiedText] = useState<string | null>(null)
  
  // Snippet creation
  const [selectedText, setSelectedText] = useState('')
  const [snippetAnnotation, setSnippetAnnotation] = useState('')
  const [snippetCategory, setSnippetCategory] = useState('')
  const [creatingSnippet, setCreatingSnippet] = useState(false)
  
  // Tag management
  const [newTag, setNewTag] = useState('')
  const [addingTag, setAddingTag] = useState(false)
  const [tagSuggestions, setTagSuggestions] = useState<any[]>([])
  const [loadingSuggestions, setLoadingSuggestions] = useState(false)

  useEffect(() => {
    loadPaperDetails()
    loadTagSuggestions()
  }, [paperId])

  const loadPaperDetails = async () => {
    setLoading(true)
    setError(null)
    
    try {
      // Load paper details
      const paperResponse = await axios.get(`http://localhost:8000/api/papers/${paperId}`)
      
      // Load content and sections
      const contentResponse = await axios.get(`http://localhost:8000/api/papers/${paperId}/content`)
      
      // Load snippets
      const snippetsResponse = await axios.get(`http://localhost:8000/api/papers/${paperId}/snippets`)
      
      setPaper({
        ...paperResponse.data,
        sections: contentResponse.data.sections,
        snippets: snippetsResponse.data
      })
    } catch (err: any) {
      setError('Failed to load paper details: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }

  const loadTagSuggestions = async () => {
    setLoadingSuggestions(true)
    try {
      const response = await axios.get(`http://localhost:8000/api/papers/${paperId}/tags/suggestions`)
      setTagSuggestions(response.data.suggestions || [])
    } catch (err: any) {
      console.error('Failed to load tag suggestions:', err)
    } finally {
      setLoadingSuggestions(false)
    }
  }

  const handleAddTag = async () => {
    if (!newTag.trim() || !paper) return
    
    setAddingTag(true)
    try {
      await axios.post(`http://localhost:8000/api/papers/${paperId}/tags`, {
        tag: newTag.trim(),
        tag_type: 'manual'
      })
      
      // Reload paper to get updated tags
      await loadPaperDetails()
      setNewTag('')
    } catch (err: any) {
      console.error('Failed to add tag:', err)
    } finally {
      setAddingTag(false)
    }
  }

  const handleRemoveTag = async (tag: string) => {
    try {
      await axios.delete(`http://localhost:8000/api/papers/${paperId}/tags/${encodeURIComponent(tag)}`)
      await loadPaperDetails()
    } catch (err: any) {
      console.error('Failed to remove tag:', err)
    }
  }

  const handleCreateSnippet = async () => {
    if (!selectedText.trim() || !paper) return
    
    setCreatingSnippet(true)
    try {
      await axios.post(`http://localhost:8000/api/papers/${paperId}/snippets`, {
        content: selectedText.trim(),
        annotation: snippetAnnotation.trim() || null,
        category: snippetCategory.trim() || null
      })
      
      // Reload snippets
      await loadPaperDetails()
      
      // Clear form
      setSelectedText('')
      setSnippetAnnotation('')
      setSnippetCategory('')
    } catch (err: any) {
      console.error('Failed to create snippet:', err)
    } finally {
      setCreatingSnippet(false)
    }
  }

  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text)
    setCopiedText(text)
    setTimeout(() => setCopiedText(null), 2000)
  }

  const toggleSection = (sectionId: number) => {
    const newExpanded = new Set(expandedSections)
    if (newExpanded.has(sectionId)) {
      newExpanded.delete(sectionId)
    } else {
      newExpanded.add(sectionId)
    }
    setExpandedSections(newExpanded)
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  const getSectionIcon = (type: string | undefined) => {
    if (!type) return <FileText className="h-4 w-4" />
    
    switch(type.toLowerCase()) {
      case 'introduction': return <BookOpen className="h-4 w-4" />
      case 'methods': 
      case 'methodology': return <FileCode className="h-4 w-4" />
      case 'results': return <Hash className="h-4 w-4" />
      case 'discussion': return <MessageSquare className="h-4 w-4" />
      case 'conclusion': return <CheckCircle className="h-4 w-4" />
      default: return <FileText className="h-4 w-4" />
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading paper details...</p>
        </div>
      </div>
    )
  }

  if (error || !paper) {
    return (
      <Alert className="bg-red-50 border-red-200">
        <AlertDescription className="text-red-800">
          {error || 'Paper not found'}
        </AlertDescription>
      </Alert>
    )
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg border p-6">
        <div className="flex justify-between items-start mb-4">
          <div className="flex-1">
            <h1 className="text-2xl font-bold text-gray-900 mb-3">{paper.title}</h1>
            
            {/* Authors */}
            {paper.authors.length > 0 && (
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <User className="h-4 w-4 text-gray-500" />
                {paper.authors.map((author, index) => (
                  <span key={index} className="text-sm text-gray-700">
                    {author.name}
                    {author.email && (
                      <span className="text-gray-500 ml-1">({author.email})</span>
                    )}
                    {index < paper.authors.length - 1 && ','}
                  </span>
                ))}
              </div>
            )}
            
            {/* Metadata */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500">
              {paper.publication_date && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-3 w-3" />
                  {formatDate(paper.publication_date)}
                </div>
              )}
              
              {paper.conference && (
                <div className="flex items-center gap-1">
                  <Building2 className="h-3 w-3" />
                  {paper.conference}
                </div>
              )}
              
              {paper.journal && (
                <div className="flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  {paper.journal}
                </div>
              )}
              
              <div className="flex items-center gap-1">
                <FileText className="h-3 w-3" />
                {paper.page_count} pages
              </div>
            </div>
            
            {/* External Links */}
            <div className="flex gap-2 mt-4">
              {paper.arxiv_id && (
                <a
                  href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-red-50 text-red-700 rounded-md hover:bg-red-100"
                >
                  <ExternalLink className="h-3 w-3" />
                  arXiv
                </a>
              )}
              
              {paper.doi && (
                <a
                  href={`https://doi.org/${paper.doi}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 px-3 py-1 text-sm bg-blue-50 text-blue-700 rounded-md hover:bg-blue-100"
                >
                  <ExternalLink className="h-3 w-3" />
                  DOI
                </a>
              )}
            </div>
          </div>
          
          {onClose && (
            <Button variant="ghost" size="sm" onClick={onClose}>
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        
        {/* Tags */}
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {paper.tags.map((tag, index) => (
              <Badge key={index} variant="secondary" className="group">
                {tag}
                <button
                  onClick={() => handleRemoveTag(tag)}
                  className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity"
                >
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          
            <div className="flex items-center gap-2">
              <Input
                placeholder="Add tag..."
                value={newTag}
                onChange={(e) => setNewTag(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                className="h-7 w-32"
              />
              <Button
                size="sm"
                variant="outline"
                onClick={handleAddTag}
                disabled={addingTag || !newTag.trim()}
              >
                {addingTag ? <Loader2 className="h-3 w-3 animate-spin" /> : <Plus className="h-3 w-3" />}
              </Button>
            </div>
          </div>
          
          {/* Tag Suggestions */}
          {tagSuggestions.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 pt-2 border-t">
              <span className="text-xs text-gray-500">Suggestions:</span>
              {tagSuggestions.map((suggestion, index) => (
                <Badge 
                  key={index} 
                  variant="outline" 
                  className="cursor-pointer hover:bg-gray-100"
                  onClick={() => {
                    setNewTag(suggestion.tag)
                    handleAddTag()
                  }}
                >
                  {suggestion.tag}
                  {suggestion.usage_count > 0 && (
                    <span className="ml-1 text-xs text-gray-400">({suggestion.usage_count})</span>
                  )}
                </Badge>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Content Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="pdf">PDF</TabsTrigger>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="sections">Sections</TabsTrigger>
          <TabsTrigger value="snippets">
            Snippets
            {paper.snippets && paper.snippets.length > 0 && (
              <Badge variant="secondary" className="ml-2 h-5 px-1">
                {paper.snippets.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="search">Search</TabsTrigger>
        </TabsList>

        {/* PDF Tab */}
        <TabsContent value="pdf">
          <Card>
            <CardContent className="p-4">
              <PDFViewerModern
                pdfUrl={`http://localhost:8000/api/papers/${paperId}/pdf`}
                paperId={paperId}
                onTextSelect={(text, pageNumber) => {
                  setSelectedText(text)
                  setActiveTab('snippets')
                }}
                className="h-[700px]"
              />
            </CardContent>
          </Card>
        </TabsContent>

        {/* Overview Tab */}
        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Abstract</CardTitle>
            </CardHeader>
            <CardContent>
              {paper.abstract ? (
                <div className="prose max-w-none">
                  <p className="text-gray-700 leading-relaxed">{paper.abstract}</p>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleCopyText(paper.abstract || '')}
                    className="mt-2"
                  >
                    {copiedText === paper.abstract ? (
                      <>
                        <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-2" />
                        Copy Abstract
                      </>
                    )}
                  </Button>
                </div>
              ) : (
                <p className="text-gray-500 italic">No abstract available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Sections Tab */}
        <TabsContent value="sections">
          <Card>
            <CardHeader>
              <CardTitle>Paper Sections</CardTitle>
              <CardDescription>
                {paper.sections ? `${paper.sections.length} sections extracted` : 'No sections available'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-3">
                  {paper.sections?.map((section) => (
                    <div key={section.id} className="border rounded-lg">
                      <button
                        onClick={() => toggleSection(section.id)}
                        className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          {getSectionIcon(section.section_type)}
                          <span className="font-medium">{section.title}</span>
                          {section.section_type && (
                            <Badge variant="outline" className="text-xs">
                              {section.section_type}
                            </Badge>
                          )}
                        </div>
                        {expandedSections.has(section.id) ? (
                          <ChevronDown className="h-4 w-4" />
                        ) : (
                          <ChevronRight className="h-4 w-4" />
                        )}
                      </button>
                      
                      {expandedSections.has(section.id) && (
                        <div className="px-4 pb-4 pt-2 border-t">
                          <div className="prose max-w-none">
                            <p className="text-sm text-gray-700 whitespace-pre-wrap">
                              {section.content}
                            </p>
                          </div>
                          <div className="mt-3 flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => {
                                setSelectedText(section.content)
                                setActiveTab('snippets')
                              }}
                            >
                              <MessageSquare className="h-4 w-4 mr-2" />
                              Create Snippet
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleCopyText(section.content)}
                            >
                              {copiedText === section.content ? (
                                <>
                                  <CheckCircle className="h-4 w-4 mr-2 text-green-600" />
                                  Copied!
                                </>
                              ) : (
                                <>
                                  <Copy className="h-4 w-4 mr-2" />
                                  Copy
                                </>
                              )}
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Snippets Tab */}
        <TabsContent value="snippets">
          <div className="space-y-4">
            {/* Create Snippet */}
            <Card>
              <CardHeader>
                <CardTitle>Create Snippet</CardTitle>
                <CardDescription>
                  Select text from the paper or paste content to create a snippet
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Content</label>
                    <Textarea
                      placeholder="Paste or type the content you want to save as a snippet..."
                      value={selectedText}
                      onChange={(e) => setSelectedText(e.target.value)}
                      className="mt-1"
                      rows={4}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700">Annotation (optional)</label>
                    <Textarea
                      placeholder="Add your notes or thoughts about this snippet..."
                      value={snippetAnnotation}
                      onChange={(e) => setSnippetAnnotation(e.target.value)}
                      className="mt-1"
                      rows={2}
                    />
                  </div>
                  
                  <div>
                    <label className="text-sm font-medium text-gray-700">Category (optional)</label>
                    <Input
                      placeholder="e.g., methodology, finding, limitation..."
                      value={snippetCategory}
                      onChange={(e) => setSnippetCategory(e.target.value)}
                      className="mt-1"
                    />
                  </div>
                  
                  <Button
                    onClick={handleCreateSnippet}
                    disabled={creatingSnippet || !selectedText.trim()}
                  >
                    {creatingSnippet ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <Plus className="h-4 w-4 mr-2" />
                        Create Snippet
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Existing Snippets */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Saved Snippets</CardTitle>
                    <CardDescription>
                      {paper.snippets ? `${paper.snippets.length} snippets saved` : 'No snippets yet'}
                    </CardDescription>
                  </div>
                  {paper.snippets && paper.snippets.length > 0 && (
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(`http://localhost:8000/api/papers/${paperId}/snippets/export?format=markdown`, '_blank')}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Export MD
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => window.open(`http://localhost:8000/api/papers/${paperId}/snippets/export?format=json`, '_blank')}
                      >
                        <Download className="h-4 w-4 mr-2" />
                        Export JSON
                      </Button>
                    </div>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-96">
                  <div className="space-y-3">
                    {paper.snippets?.map((snippet) => (
                      <div key={snippet.id} className="border rounded-lg p-4 space-y-2">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <p className="text-sm text-gray-700">{snippet.content}</p>
                            
                            {snippet.annotation && (
                              <div className="mt-2 p-2 bg-yellow-50 rounded-md">
                                <p className="text-sm text-gray-600">
                                  <span className="font-medium">Note:</span> {snippet.annotation}
                                </p>
                              </div>
                            )}
                            
                            <div className="flex items-center gap-2 mt-2">
                              {snippet.category && (
                                <Badge variant="outline">{snippet.category}</Badge>
                              )}
                              {snippet.page_number && (
                                <span className="text-xs text-gray-500">
                                  Page {snippet.page_number}
                                </span>
                              )}
                              <span className="text-xs text-gray-500">
                                {formatDate(snippet.created_at)}
                              </span>
                            </div>
                          </div>
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleCopyText(snippet.content)}
                          >
                            {copiedText === snippet.content ? (
                              <CheckCircle className="h-4 w-4 text-green-600" />
                            ) : (
                              <Copy className="h-4 w-4" />
                            )}
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Search Tab */}
        <TabsContent value="search">
          <Card>
            <CardHeader>
              <CardTitle>Search in Paper</CardTitle>
              <CardDescription>
                Search for specific terms or concepts within this paper
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Input
                    placeholder="Enter search terms..."
                    className="flex-1"
                  />
                  <Button>
                    <Search className="h-4 w-4 mr-2" />
                    Search
                  </Button>
                </div>
                
                <Alert>
                  <AlertDescription>
                    Search functionality will highlight matching sections and allow you to navigate through results.
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

export default PaperViewerModern