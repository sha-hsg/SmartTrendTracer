import React, { useState, useEffect, useRef } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { VisuallyHidden } from "@radix-ui/react-visually-hidden"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { cn } from "@/lib/utils"
import EntityAnnotationReviewModern from './EntityAnnotationReviewModern'
import ModelBadge from './ModelBadge'
import { 
  X, 
  Download, 
  Edit2, 
  Save, 
  Link2, 
  Tags, 
  Sparkles,
  Hash,
  User,
  Clock,
  FileText,
  ChevronDown,
  ChevronUp,
  Palette,
  Type,
  StickyNote,
  AlertCircle,
  Loader2,
  ExternalLink,
  BookOpen,
  Edit3,
  Trash2
} from 'lucide-react'

interface ArticleViewerProps {
  articleId: number
  onClose: () => void
}

interface FullArticle {
  id: number
  title: string
  subtitle: string | null
  author: {
    name: string
    subdomain: string
    url: string
  }
  url: string | null
  content_markdown: string
  content_html: string
  word_count: number
  reading_time_minutes: number
  published_at: string | null
  summary: string | null
  tags: { id: number; tag: string; type: string }[]
  snippets: {
    id: number
    text: string
    annotation: string | null
    category: string | null
    importance: number
    start_offset?: number
    end_offset?: number
  }[]
}

function ArticleViewerModern({ articleId, onClose }: ArticleViewerProps) {
  const [article, setArticle] = useState<FullArticle | null>(null)
  const [loading, setLoading] = useState(true)
  const [showSummary, setShowSummary] = useState(false)
  const [selectedText, setSelectedText] = useState('')
  const [showContextMenu, setShowContextMenu] = useState(false)
  const [showHighlightForm, setShowHighlightForm] = useState(false)
  const [showAnnotationForm, setShowAnnotationForm] = useState(false)
  const [showTagCreation, setShowTagCreation] = useState(false)
  const [exportingPDF, setExportingPDF] = useState(false)
  const [tagEditText, setTagEditText] = useState('')
  const [showEntityAnnotation, setShowEntityAnnotation] = useState(false)
  const [annotation, setAnnotation] = useState('')
  const [snippetCategory, setSnippetCategory] = useState('insight')
  const [highlightColor, setHighlightColor] = useState('yellow')
  const [selectionCoords, setSelectionCoords] = useState({ x: 0, y: 0 })
  const [hasSelectedText, setHasSelectedText] = useState(false)
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [keyPoints, setKeyPoints] = useState<string[]>([])
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editedTitle, setEditedTitle] = useState('')
  const [isEditingContent, setIsEditingContent] = useState(false)
  const [editedContent, setEditedContent] = useState('')
  const [savingEdits, setSavingEdits] = useState(false)
  const [selectionRange, setSelectionRange] = useState<{ start: number; end: number } | null>(null)
  const [summaryModel, setSummaryModel] = useState<string>('')
  const [isEditingUrl, setIsEditingUrl] = useState(false)
  const [editedUrl, setEditedUrl] = useState('')
  const [tagError, setTagError] = useState<string>('')
  const contentRef = useRef<HTMLDivElement>(null)
  const selectedTextRef = useRef<string>('')

  useEffect(() => {
    fetchArticle()
  }, [articleId])

  useEffect(() => {
    if (article) {
      setEditedTitle(article.title)
      setEditedContent(article.content_markdown)
    }
  }, [article])

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element
      
      // Don't close if clicking on the menu itself
      if (target.closest('.context-menu')) {
        return
      }
      
      // Close menu if it's open
      if (showContextMenu) {
        setShowContextMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [showContextMenu])

  const fetchArticle = async () => {
    try {
      // Use v2 endpoint for article fetching
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${articleId}`)
      
      if (!response.ok) {
        console.error('Failed to fetch article:', response.status)
        setArticle(null)
        setLoading(false)
        return
      }
      
      const data = await response.json()
      setArticle(data)
      
      // Extract key points from summary if available
      if (data.summary) {
        const points = data.summary
          .split('\n')
          .filter((line: string) => line.trim().startsWith('•') || line.trim().startsWith('-'))
          .map((line: string) => line.replace(/^[•\-]\s*/, '').trim())
          .filter((point: string) => point.length > 0)
        setKeyPoints(points)
        
        // Extract model info from summary
        const modelMatch = data.summary.match(/\[Model: ([^\]]+)\]/i)
        if (modelMatch) {
          setSummaryModel(modelMatch[1])
        }
      }
    } catch (error) {
      console.error('Error fetching article:', error)
      setArticle(null)
    } finally {
      setLoading(false)
    }
  }

  const generateSummary = async () => {
    if (!article) return
    
    setGeneratingSummary(true)
    try {
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${article.id}/summarize`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const data = await response.json()
        setArticle(prev => prev ? { ...prev, summary: data.summary } : null)
        
        // Extract key points
        const points = data.summary
          .split('\n')
          .filter((line: string) => line.trim().startsWith('•') || line.trim().startsWith('-'))
          .map((line: string) => line.replace(/^[•\-]\s*/, '').trim())
          .filter((point: string) => point.length > 0)
        setKeyPoints(points)
        
        // Extract model info
        const modelMatch = data.summary.match(/\[Model: ([^\]]+)\]/i)
        if (modelMatch) {
          setSummaryModel(modelMatch[1])
        }
        
        setShowSummary(true)
      }
    } catch (error) {
      console.error('Error generating summary:', error)
    } finally {
      setGeneratingSummary(false)
    }
  }

  const saveTitle = async () => {
    if (!article || editedTitle === article.title) {
      setIsEditingTitle(false)
      return
    }
    
    setSavingEdits(true)
    try {
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${article.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: editedTitle })
      })
      
      if (response.ok) {
        setArticle(prev => prev ? { ...prev, title: editedTitle } : null)
        setIsEditingTitle(false)
      }
    } catch (error) {
      console.error('Error saving title:', error)
    } finally {
      setSavingEdits(false)
    }
  }

  const saveContent = async () => {
    if (!article || editedContent === article.content_markdown) {
      setIsEditingContent(false)
      return
    }
    
    setSavingEdits(true)
    try {
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${article.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ content_markdown: editedContent })
      })
      
      if (response.ok) {
        setArticle(prev => prev ? { ...prev, content_markdown: editedContent } : null)
        setIsEditingContent(false)
      }
    } catch (error) {
      console.error('Error saving content:', error)
    } finally {
      setSavingEdits(false)
    }
  }

  const saveUrl = async () => {
    if (!article || editedUrl === article.url) {
      setIsEditingUrl(false)
      return
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${article.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: editedUrl || null })
      })
      
      if (response.ok) {
        setArticle(prev => prev ? { ...prev, url: editedUrl || null } : null)
        setIsEditingUrl(false)
      }
    } catch (error) {
      console.error('Error saving URL:', error)
    }
  }

  const exportToPDF = async () => {
    if (!article) return
    
    setExportingPDF(true)
    try {
      const response = await fetch(`http://localhost:8000/api/pdf/article/${article.id}`)
      
      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `${article.title.replace(/[^a-z0-9]/gi, '_')}.pdf`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
      } else {
        console.error('Failed to export PDF:', response.status)
      }
    } catch (error) {
      console.error('Error exporting to PDF:', error)
    } finally {
      setExportingPDF(false)
    }
  }

  const removeTag = async (tagId: number) => {
    if (!article) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${article.id}/tags/${tagId}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setArticle(prev => prev ? {
          ...prev,
          tags: prev.tags.filter(t => t.id !== tagId)
        } : null)
      }
    } catch (error) {
      console.error('Error removing tag:', error)
    }
  }

  const handleContextMenu = (e: React.MouseEvent) => {
    const selection = window.getSelection()
    if (!selection || selection.toString().trim() === '') return
    
    e.preventDefault()
    const text = selection.toString().trim()
    setSelectedText(text)
    selectedTextRef.current = text
    setTagEditText(text.replace(/\s+/g, '-'))
    setHasSelectedText(true)
    
    // Get selection coordinates
    const range = selection.getRangeAt(0)
    const rect = range.getBoundingClientRect()
    
    // Position context menu
    setSelectionCoords({
      x: rect.left + rect.width / 2,
      y: rect.bottom + window.scrollY + 10
    })
    
    setShowContextMenu(true)
  }

  const startTagCreation = () => {
    setShowContextMenu(false)
    setShowTagCreation(true)
  }

  const saveTagFromSelection = async () => {
    if (!tagEditText || !article) return
    
    // Clear any previous error
    setTagError('')
    
    // Check if tag already exists on article (case-insensitive)
    if (article.tags?.some(tag => tag.tag.toLowerCase() === tagEditText.toLowerCase())) {
      setTagError(`Tag "${tagEditText}" already exists on this article`)
      setTimeout(() => setTagError(''), 3000)
      return
    }
    
    try {
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${article.id}/tags`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          tag: tagEditText,
          tag_type: 'manual'
        })
      })
      
      if (response.ok) {
        console.log(`Tag "${tagEditText}" created and added to article`)
        // Refresh article to get new tag
        fetchArticle()
        // Reset form
        cancelSelection()
      } else if (response.status === 400) {
        const error = await response.json()
        if (error.detail?.includes('already exists')) {
          setTagError(`Tag "${tagEditText}" already exists`)
          setTimeout(() => setTagError(''), 3000)
        } else {
          setTagError(error.detail || 'Error adding tag')
          setTimeout(() => setTagError(''), 5000)
        }
      }
    } catch (error) {
      console.error('Error creating tag:', error)
      setTagError('Network error: Could not add tag')
      setTimeout(() => setTagError(''), 5000)
    }
  }

  const cancelSelection = () => {
    setShowContextMenu(false)
    setShowHighlightForm(false)
    setShowAnnotationForm(false)
    setShowTagCreation(false)
    setShowEntityAnnotation(false)
    setSelectedText('')
    setAnnotation('')
    setTagEditText('')
    setTagError('')
    setSelectionRange(null)
    setHasSelectedText(false)
  }

  const saveHighlight = async () => {
    if (!selectedText || !article) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${article.id}/snippets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: selectedText,
          category: highlightColor,
          annotation: `Highlighted in ${highlightColor}`
        })
      })
      
      if (response.ok) {
        fetchArticle()
        cancelSelection()
      }
    } catch (error) {
      console.error('Error saving highlight:', error)
    }
  }

  const saveAnnotation = async () => {
    if (!selectedText || !article) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/v2/substack/articles/${article.id}/snippets`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          text: selectedText,
          category: snippetCategory,
          annotation: annotation || null
        })
      })
      
      if (response.ok) {
        fetchArticle()
        cancelSelection()
      }
    } catch (error) {
      console.error('Error saving snippet:', error)
    }
  }

  const highlightSnippets = (text: string) => {
    if (!article || !article.snippets || article.snippets.length === 0) {
      return text
    }
    
    let highlightedText = text
    article.snippets.forEach(snippet => {
      const color = snippet.category === 'yellow' ? '#fff59d' :
                   snippet.category === 'green' ? '#a5d6a7' :
                   snippet.category === 'blue' ? '#90caf9' :
                   snippet.category === 'pink' ? '#f48fb1' : '#ffeb3b'
      
      const regex = new RegExp(`(${snippet.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi')
      highlightedText = highlightedText.replace(
        regex,
        `<mark style="background-color: ${color}; padding: 2px 0; border-radius: 2px;">$1</mark>`
      )
    })
    
    return highlightedText
  }

  if (loading) {
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-6xl max-h-[90vh]">
          <VisuallyHidden>
            <DialogTitle>Loading Article</DialogTitle>
            <DialogDescription>Please wait while the article is being loaded.</DialogDescription>
          </VisuallyHidden>
          <div className="flex items-center justify-center p-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        </DialogContent>
      </Dialog>
    )
  }

  if (!article) {
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Article Not Found</DialogTitle>
            <DialogDescription>
              The requested article could not be loaded.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={onClose}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }

  return (
    <>
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent className="max-w-6xl max-h-[90vh] p-0 overflow-hidden">
          <VisuallyHidden>
            <DialogTitle>{article.title || 'Article Viewer'}</DialogTitle>
            <DialogDescription>View and edit article content, manage tags, and generate summaries.</DialogDescription>
          </VisuallyHidden>
          <ScrollArea className="h-[90vh]">
            {/* Header */}
            <div className="sticky top-0 z-10 bg-background border-b">
              <div className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1 pr-8">
                    {isEditingTitle ? (
                      <div className="flex items-center gap-2">
                        <Input
                          value={editedTitle}
                          onChange={(e) => setEditedTitle(e.target.value)}
                          onBlur={saveTitle}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') saveTitle()
                            if (e.key === 'Escape') {
                              setEditedTitle(article.title)
                              setIsEditingTitle(false)
                            }
                          }}
                          className="text-2xl font-bold"
                          autoFocus
                        />
                        <Button 
                          size="sm" 
                          onClick={saveTitle}
                          disabled={savingEdits}
                        >
                          {savingEdits ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                        </Button>
                      </div>
                    ) : (
                      <h2 
                        className="text-2xl font-bold cursor-pointer hover:text-primary transition-colors flex items-center gap-2"
                        onClick={() => setIsEditingTitle(true)}
                      >
                        {article.title}
                        <Edit3 className="h-4 w-4 opacity-50" />
                      </h2>
                    )}
                    {article.subtitle && (
                      <p className="text-muted-foreground mt-1">{article.subtitle}</p>
                    )}
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={onClose}
                    className="rounded-full"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Metadata */}
                <div className="flex flex-wrap items-center gap-4 mt-4 text-sm text-muted-foreground">
                  {article.author && (
                    <div className="flex items-center gap-1">
                      <User className="h-4 w-4" />
                      {article.author.name}
                    </div>
                  )}
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {article.reading_time_minutes} min read
                  </div>
                  <div className="flex items-center gap-1">
                    <FileText className="h-4 w-4" />
                    {article.word_count} words
                  </div>
                  {isEditingUrl ? (
                    <div className="flex items-center gap-2">
                      <Input
                        type="url"
                        value={editedUrl}
                        onChange={(e) => setEditedUrl(e.target.value)}
                        onBlur={saveUrl}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') saveUrl()
                          if (e.key === 'Escape') {
                            setIsEditingUrl(false)
                            setEditedUrl(article.url || '')
                          }
                        }}
                        placeholder="Enter article URL"
                        className="h-8"
                      />
                    </div>
                  ) : (
                    <>
                      {article.url && (
                        <a 
                          href={article.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-primary hover:underline"
                        >
                          <ExternalLink className="h-4 w-4" />
                          View on Substack
                        </a>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditedUrl(article.url || '')
                          setIsEditingUrl(true)
                        }}
                        className="h-8 px-2"
                      >
                        <Link2 className="h-4 w-4 mr-1" />
                        {article.url ? 'Edit' : 'Add'} URL
                      </Button>
                    </>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowEntityAnnotation(true)}
                    className="bg-gradient-to-r from-purple-500/10 to-purple-600/10 hover:from-purple-500/20 hover:to-purple-600/20"
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Automatic Annotation
                  </Button>
                  
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => {
                      if (article.summary) {
                        setShowSummary(!showSummary)
                      } else {
                        generateSummary()
                      }
                    }}
                    disabled={generatingSummary}
                  >
                    {generatingSummary ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Generating...
                      </>
                    ) : article.summary ? (
                      <>
                        <BookOpen className="h-4 w-4 mr-2" />
                        {showSummary ? 'Hide' : 'View'} Summary
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4 mr-2" />
                        Generate Summary
                      </>
                    )}
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setIsEditingContent(!isEditingContent)}
                  >
                    <Edit2 className="h-4 w-4 mr-2" />
                    {isEditingContent ? 'View' : 'Edit'} Content
                  </Button>

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={exportToPDF}
                    disabled={exportingPDF}
                  >
                    {exportingPDF ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Exporting...
                      </>
                    ) : (
                      <>
                        <Download className="h-4 w-4 mr-2" />
                        Export PDF
                      </>
                    )}
                  </Button>
                </div>
              </div>

              {/* Tags */}
              {article.tags && article.tags.length > 0 && (
                <div className="px-6 pb-4">
                  <div className="flex flex-wrap gap-2">
                    {article.tags.map(tag => (
                      <Badge
                        key={tag.id}
                        variant="outline"
                        className="cursor-pointer bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100 hover:text-blue-800 group"
                      >
                        <Hash className="h-3 w-3 mr-1" />
                        {tag.tag}
                        <button
                          onClick={() => removeTag(tag.id)}
                          className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity hover:text-blue-900"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Content */}
            <div className="p-6">
              {/* Summary */}
              {showSummary && article.summary && (
                <Card className="mb-6">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">AI Summary</CardTitle>
                      {summaryModel && <ModelBadge model={summaryModel} size="medium" />}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeRaw]}
                        components={{
                          p: ({ children, ...props }) => {
                            const hasCodeBlock = React.Children.toArray(children).some(
                              child => React.isValidElement(child) && (
                                child.type === 'pre' || 
                                child.props?.node?.tagName === 'pre'
                              )
                            )
                            
                            if (hasCodeBlock) {
                              return <div className="mb-4" {...props}>{children}</div>
                            }
                            
                            return <p className="mb-4" {...props}>{children}</p>
                          }
                        }}
                      >
                        {article.summary
                          ?.replace(/<think>/gi, '')
                          .replace(/<\/think>/gi, '')
                          .replace(/<think[^>]*>/gi, '')
                        }
                      </ReactMarkdown>
                    </div>
                    {keyPoints.length > 0 && (
                      <>
                        <Separator className="my-4" />
                        <div>
                          <h4 className="font-semibold mb-2">📌 Key Points:</h4>
                          <ul className="space-y-2">
                            {keyPoints.map((point, index) => (
                              <li key={index} className="text-sm flex items-start">
                                <span className="mr-2 mt-1">•</span>
                                <div className="prose prose-sm max-w-none flex-1">
                                  <ReactMarkdown
                                    remarkPlugins={[remarkGfm]}
                                    components={{
                                      p: ({ children }) => <span>{children}</span>,
                                      strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                                      em: ({ children }) => <em className="italic">{children}</em>,
                                      code: ({ children }) => (
                                        <code className="bg-muted px-1 py-0.5 rounded text-xs">{children}</code>
                                      ),
                                      a: ({ href, children }) => (
                                        <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                                          {children}
                                        </a>
                                      )
                                    }}
                                  >
                                    {point}
                                  </ReactMarkdown>
                                </div>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Article Content */}
              {isEditingContent ? (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle>Edit Content</CardTitle>
                      <div className="flex gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setEditedContent(article.content_markdown)
                            setIsEditingContent(false)
                          }}
                        >
                          Cancel
                        </Button>
                        <Button
                          size="sm"
                          onClick={saveContent}
                          disabled={savingEdits}
                        >
                          {savingEdits ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <>
                              <Save className="h-4 w-4 mr-2" />
                              Save
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <Textarea
                      value={editedContent}
                      onChange={(e) => setEditedContent(e.target.value)}
                      className="min-h-[500px] font-mono text-sm"
                    />
                  </CardContent>
                </Card>
              ) : (
                <div 
                  className="prose prose-lg max-w-none"
                  onContextMenu={handleContextMenu}
                  ref={contentRef}
                >
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw]}
                    components={{
                      p: ({ children, ...props }) => {
                        const hasCodeBlock = React.Children.toArray(children).some(
                          child => React.isValidElement(child) && (
                            child.type === 'pre' || 
                            child.props?.node?.tagName === 'pre' ||
                            (child.props && child.props.children && React.isValidElement(child.props.children) && child.props.children.type === 'pre')
                          )
                        )
                        
                        if (hasCodeBlock) {
                          return <div className="mb-4" {...props}>{children}</div>
                        }
                        
                        const content = String(children)
                        const hasSnippets = article.snippets.some(s => 
                          s.start_offset !== undefined && 
                          s.end_offset !== undefined && 
                          content.includes(s.text)
                        )
                        
                        if (hasSnippets) {
                          return (
                            <p 
                              className="mb-4 leading-relaxed"
                              {...props}
                              dangerouslySetInnerHTML={{ 
                                __html: highlightSnippets(content) 
                              }}
                            />
                          )
                        }
                        
                        return <p className="mb-4 leading-relaxed" {...props}>{children}</p>
                      },
                      h1: ({node, ...props}) => (
                        <h1 className="text-3xl font-bold mt-8 mb-4" {...props} />
                      ),
                      h2: ({node, ...props}) => (
                        <h2 className="text-2xl font-bold mt-6 mb-3" {...props} />
                      ),
                      h3: ({node, ...props}) => (
                        <h3 className="text-xl font-semibold mt-5 mb-2" {...props} />
                      ),
                      h4: ({node, ...props}) => (
                        <h4 className="text-lg font-semibold mt-4 mb-2" {...props} />
                      ),
                      h5: ({node, ...props}) => (
                        <h5 className="text-base font-semibold mt-3 mb-1" {...props} />
                      ),
                      h6: ({node, ...props}) => (
                        <h6 className="text-sm font-semibold mt-3 mb-1" {...props} />
                      ),
                      ul: ({node, ...props}) => (
                        <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />
                      ),
                      ol: ({node, ...props}) => (
                        <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />
                      ),
                      li: ({node, ...props}) => (
                        <li className="leading-relaxed" {...props} />
                      ),
                      img: ({node, ...props}) => (
                        <img
                          {...props}
                          className="rounded-lg shadow-md my-6 max-w-full h-auto"
                          loading="lazy"
                        />
                      ),
                      a: ({node, ...props}) => (
                        <a
                          {...props}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-primary hover:underline font-medium"
                        />
                      ),
                      blockquote: ({node, ...props}) => (
                        <blockquote
                          {...props}
                          className="border-l-4 border-primary/30 pl-4 italic my-6 text-muted-foreground"
                        />
                      ),
                      hr: ({node, ...props}) => (
                        <hr className="my-8 border-t border-border" {...props} />
                      ),
                      table: ({node, ...props}) => (
                        <div className="overflow-x-auto my-6">
                          <table className="min-w-full divide-y divide-border" {...props} />
                        </div>
                      ),
                      thead: ({node, ...props}) => (
                        <thead className="bg-muted/50" {...props} />
                      ),
                      tbody: ({node, ...props}) => (
                        <tbody className="divide-y divide-border" {...props} />
                      ),
                      tr: ({node, ...props}) => (
                        <tr className="hover:bg-muted/30 transition-colors" {...props} />
                      ),
                      th: ({node, ...props}) => (
                        <th className="px-4 py-2 text-left font-semibold" {...props} />
                      ),
                      td: ({node, ...props}) => (
                        <td className="px-4 py-2" {...props} />
                      ),
                      strong: ({node, ...props}) => (
                        <strong className="font-semibold" {...props} />
                      ),
                      em: ({node, ...props}) => (
                        <em className="italic" {...props} />
                      ),
                      del: ({node, ...props}) => (
                        <del className="line-through text-muted-foreground" {...props} />
                      ),
                      code: ({node, inline, ...props}) => (
                        inline ? (
                          <code
                            {...props}
                            className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
                          />
                        ) : (
                          <pre className="bg-muted p-4 rounded-lg overflow-auto my-4">
                            <code className="font-mono text-sm" {...props} />
                          </pre>
                        )
                      )
                    }}
                  >
                    {article.content_markdown
                      .replace(/<think>/gi, '')
                      .replace(/<\/think>/gi, '')
                      .replace(/<think[^>]*>/gi, '')
                    }
                  </ReactMarkdown>
                </div>
              )}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>

      {/* Context Menu */}
      {showContextMenu && (
        <div 
          className="context-menu fixed z-50 bg-background border rounded-lg shadow-lg py-1 min-w-[160px]"
          style={{
            left: `${selectionCoords.x}px`,
            top: `${selectionCoords.y}px`,
            transform: 'translateX(-50%)'
          }}
        >
          <button
            onClick={() => {
              setShowContextMenu(false)
              setShowHighlightForm(true)
            }}
            className="w-full px-3 py-2 text-left hover:bg-accent flex items-center gap-2 text-sm"
          >
            <Palette className="h-4 w-4" />
            Highlighting
          </button>
          <button
            onClick={() => {
              setShowContextMenu(false)
              setShowAnnotationForm(true)
            }}
            className="w-full px-3 py-2 text-left hover:bg-accent flex items-center gap-2 text-sm"
          >
            <StickyNote className="h-4 w-4" />
            Create Snippet
          </button>
          <Separator />
          <button
            onClick={startTagCreation}
            className="w-full px-3 py-2 text-left hover:bg-accent flex items-center gap-2 text-sm"
          >
            <Tags className="h-4 w-4" />
            Tag Creation
          </button>
          <Separator />
          <button
            onClick={cancelSelection}
            className="w-full px-3 py-2 text-left hover:bg-accent flex items-center gap-2 text-sm"
          >
            <X className="h-4 w-4" />
            Cancel
          </button>
        </div>
      )}

      {/* Highlight Form */}
      {showHighlightForm && (
        <Card className="fixed z-50 w-80" style={{
          left: `${selectionCoords.x}px`,
          top: `${selectionCoords.y}px`,
          transform: 'translateX(-50%)'
        }}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">🎨 Highlighting</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={cancelSelection}
                className="h-6 w-6"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm text-muted-foreground">
              "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"
            </div>
            
            <div>
              <Label className="text-sm">Choose highlight color:</Label>
              <div className="flex gap-2 mt-2">
                {[
                  { value: 'yellow', emoji: '🟡' },
                  { value: 'green', emoji: '🟢' },
                  { value: 'blue', emoji: '🔵' },
                  { value: 'pink', emoji: '🩷' }
                ].map(color => (
                  <Button
                    key={color.value}
                    variant={highlightColor === color.value ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setHighlightColor(color.value)}
                    className="flex-1"
                  >
                    {color.emoji}
                  </Button>
                ))}
              </div>
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={cancelSelection}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={saveHighlight}
                className="flex-1"
              >
                Mark in {highlightColor.charAt(0).toUpperCase() + highlightColor.slice(1)}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Annotation Form */}
      {showAnnotationForm && (
        <Card className="fixed z-50 w-96" style={{
          left: `${selectionCoords.x}px`,
          top: `${selectionCoords.y}px`,
          transform: 'translateX(-50%)'
        }}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">Create Annotation</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={cancelSelection}
                className="h-6 w-6"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm text-muted-foreground">
              "{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}"
            </div>
            
            <Select value={snippetCategory} onValueChange={setSnippetCategory}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="insight">💡 Insight</SelectItem>
                <SelectItem value="question">❓ Question</SelectItem>
                <SelectItem value="critique">🤔 Critique</SelectItem>
                <SelectItem value="todo">✅ Todo</SelectItem>
                <SelectItem value="quote">💬 Quote</SelectItem>
              </SelectContent>
            </Select>
            
            <Textarea
              placeholder="Add a note (optional)..."
              value={annotation}
              onChange={(e) => setAnnotation(e.target.value)}
              rows={3}
            />
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={cancelSelection}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={saveAnnotation}
                className="flex-1"
              >
                Save Snippet
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tag Creation Form */}
      {showTagCreation && (
        <Card className="fixed z-50 w-96" style={{
          left: `${selectionCoords.x}px`,
          top: `${selectionCoords.y}px`,
          transform: 'translateX(-50%)'
        }}>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">🏷️ Create Tag from Selection</CardTitle>
              <Button
                variant="ghost"
                size="icon"
                onClick={cancelSelection}
                className="h-6 w-6"
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="text-sm text-muted-foreground">
              Original text: "{selectedText.substring(0, 50)}{selectedText.length > 50 ? '...' : ''}"
            </div>
            
            <div>
              <Label htmlFor="tag-edit">Edit tag name:</Label>
              <Input
                id="tag-edit"
                value={tagEditText}
                onChange={(e) => setTagEditText(e.target.value.replace(/\s+/g, '-'))}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    saveTagFromSelection()
                  } else if (e.key === 'Escape') {
                    cancelSelection()
                  }
                }}
                autoFocus
              />
              <p className="text-xs text-muted-foreground mt-1">
                Spaces will be converted to hyphens. Capital letters are preserved for proper nouns.
              </p>
              {tagError && (
                <Alert variant="destructive" className="mt-2">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{tagError}</AlertDescription>
                </Alert>
              )}
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={cancelSelection}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                onClick={saveTagFromSelection}
                disabled={!tagEditText}
                className="flex-1"
              >
                Create Tag
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Entity Annotation Review Dialog */}
      {showEntityAnnotation && (
        <Dialog open={showEntityAnnotation} onOpenChange={setShowEntityAnnotation}>
          <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
            <VisuallyHidden>
              <DialogTitle>Entity Annotation Review</DialogTitle>
              <DialogDescription>Review and manage entity annotations for this article</DialogDescription>
            </VisuallyHidden>
            <EntityAnnotationReviewModern
              articleId={article.id}
              onComplete={() => {
                setShowEntityAnnotation(false)
                fetchArticle()
              }}
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  )
}

export default ArticleViewerModern