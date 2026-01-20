import React, { useState, useEffect, useRef } from 'react'
import ReactDOM from 'react-dom'
import ReactMarkdown from 'react-markdown'
import { decodeHtmlEntities } from '@/utils/htmlDecoder'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { VisuallyHidden } from "@radix-ui/react-visually-hidden"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"




import EntityAnnotationReviewModern from './EntityAnnotationReviewModern'
import ModelBadge from './ModelBadge'
import UnifiedModelSelector from './UnifiedModelSelector'
import { useModelSelector } from '@/hooks/useModelSelector'
import { 
  X, 
  Download, 
  Edit2, 
  Save, 
  Link2, 
  Tags, 
  Sparkles,
  User,
  Clock,
  FileText,
  Palette,
  StickyNote,
  AlertCircle,
  Loader2,
  ExternalLink,
  BookOpen,
  Edit3,
  Trash2,
  Calendar,
  Plus,
  Wand2,
  RefreshCw
} from 'lucide-react'

interface ArticleViewerProps {
  articleId: string | number
  onClose: () => void
  onArticleUpdated?: () => void
}

interface FullArticle {
  id: number
  title: string
  subtitle: string | null
  author: {
    id?: number
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

function ArticleViewerModern({ articleId, onClose, onArticleUpdated }: ArticleViewerProps) {
  try {
  const [article, setArticle] = useState<FullArticle | null>(null)
  const [hasChanges, setHasChanges] = useState(false)  // Track if article was modified
  const [loading, setLoading] = useState(true)
  const [showSummary, setShowSummary] = useState(false)
  const [selectedText, setSelectedText] = useState('')
  const [selectedSummaryText, setSelectedSummaryText] = useState('')
  const [preservedSelection, setPreservedSelection] = useState<{text: string, rangeData: any} | null>(null)
  const [showContextMenu, setShowContextMenu] = useState(false)
  const [showHighlightForm, setShowHighlightForm] = useState(false)
  const [showAnnotationForm, setShowAnnotationForm] = useState(false)
  const [showTagCreation, setShowTagCreation] = useState(false)
  const [exportingPDF, setExportingPDF] = useState(false)
  const [beautifyingMarkdown, setBeautifyingMarkdown] = useState(false)
  const [tagEditText, setTagEditText] = useState('')
  const [showEntityAnnotation, setShowEntityAnnotation] = useState(false)
  const [annotation, setAnnotation] = useState('')
  const [snippetCategory, setSnippetCategory] = useState('insight')
  const [highlightColor, setHighlightColor] = useState('yellow')
  const [selectionCoords, setSelectionCoords] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [hasSelectedText, setHasSelectedText] = useState(false)
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [recollecting, setRecollecting] = useState(false)
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
  const [isEditingDate, setIsEditingDate] = useState(false)
  const [editedDate, setEditedDate] = useState('')
  const [isEditingAuthor, setIsEditingAuthor] = useState(false)
  const [selectedAuthorId, setSelectedAuthorId] = useState<number | null>(null)
  const [authors, setAuthors] = useState<Array<{id: number, name: string, subdomain?: string, url?: string}>>([])
  const [authorInput, setAuthorInput] = useState('')
  const [showAuthorSuggestions, setShowAuthorSuggestions] = useState(false)
  const [filteredAuthors, setFilteredAuthors] = useState<Array<{id: number, name: string}>>([])
  const [extractingMetadata, setExtractingMetadata] = useState(false)
  const [summaryError, setSummaryError] = useState<string>('')
  const contentRef = useRef<HTMLDivElement>(null)
  const selectedTextRef = useRef<string>('')
  const selectionRangeRef = useRef<Range | null>(null)
  const lastSelectionRef = useRef<{text: string, time: number} | null>(null)
  const isInteractingWithMenu = useRef(false)

  // Use unified model selector hook for article summarization
  const {
    selectedModel: summarizerModel,
    loading: modelLoading,
    selectModel: selectSummarizerModel
  } = useModelSelector('article_summarizer')

  useEffect(() => {
    fetchArticle()
    fetchAuthors()
  }, [articleId])
  
  // Handle context menu flag
  useEffect(() => {
    if (showContextMenu || showHighlightForm || showAnnotationForm || showTagCreation) {
      isInteractingWithMenu.current = true
      console.log('Setting isInteractingWithMenu to true due to:', {
        showContextMenu,
        showHighlightForm, 
        showAnnotationForm,
        showTagCreation
      })
    } else {
      // Clear flag after all menus are closed with longer delay
      const timer = setTimeout(() => {
        isInteractingWithMenu.current = false
        console.log('Setting isInteractingWithMenu to false - all menus closed')
      }, 500) // Increased delay
      return () => clearTimeout(timer)
    }
  }, [showContextMenu, showHighlightForm, showAnnotationForm, showTagCreation])
  
  // Capture selection on mouseup/selectionchange
  useEffect(() => {
    const handleSelectionChange = () => {
      const selection = window.getSelection()
      if (selection && selection.toString().trim() !== '') {
        // Store the selection immediately
        const text = selection.toString().trim()
        lastSelectionRef.current = {
          text: text,
          time: Date.now()
        }
        // Removed verbose logging - was firing on every character
      }
    }
    
    // Listen for selection changes
    document.addEventListener('selectionchange', handleSelectionChange)
    document.addEventListener('mouseup', handleSelectionChange)
    
    return () => {
      document.removeEventListener('selectionchange', handleSelectionChange)
      document.removeEventListener('mouseup', handleSelectionChange)
    }
  }, [])

  const fetchAuthors = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/articles/authors/all')
      if (response.ok) {
        const data = await response.json()
        setAuthors(data)
      }
    } catch (error) {
      console.error('Error fetching authors:', error)
    }
  }

  useEffect(() => {
    if (article) {
      setEditedTitle(article.title)
      setEditedContent(article.content_markdown)
      setEditedDate(article.published_at ? article.published_at.split('T')[0] : '')
      setSelectedAuthorId(article.author?.id || null)
    }
  }, [article])

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element
      
      // Don't close if clicking on the menu itself or any of the forms
      if (target.closest('.context-menu') || 
          target.closest('.highlight-form') ||
          target.closest('.annotation-form') ||
          target.closest('.tag-creation-form')) {
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
  
  // Restore selection when forms are shown
  useEffect(() => {
    if ((showHighlightForm || showAnnotationForm || showTagCreation) && preservedSelection) {
      // Use the preserved selection text
      if (!selectedText && preservedSelection.text) {
        setSelectedText(preservedSelection.text)
        selectedTextRef.current = preservedSelection.text
      }
    }
  }, [showHighlightForm, showAnnotationForm, showTagCreation, preservedSelection])

  const fetchArticle = async () => {
    try {
      // Use MongoDB articles endpoint
      const response = await fetch(`http://localhost:8000/api/articles/${articleId}`)
      
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
          .filter((line: string) => {
            const trimmed = line.trim()
            // Must start with bullet point
            if (!trimmed.startsWith('•') && !trimmed.startsWith('-')) return false
            // Exclude horizontal rules (lines that are only dashes)
            if (/^-+$/.test(trimmed)) return false
            // Must have actual content after the bullet
            const content = trimmed.replace(/^[•\-]\s*/, '').trim()
            return content.length > 0
          })
          .map((line: string) => line.replace(/^[•\-]\s*/, '').trim())
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
    setSummaryError('')  // Clear previous errors

    try {
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}/summarize`, {
        method: 'POST'
      })

      if (response.ok) {
        const data = await response.json()
        setArticle(prev => prev ? { ...prev, summary: data.summary } : null)

        // Extract key points
        const points = data.summary
          .split('\n')
          .filter((line: string) => {
            const trimmed = line.trim()
            // Must start with bullet point
            if (!trimmed.startsWith('•') && !trimmed.startsWith('-')) return false
            // Exclude horizontal rules (lines that are only dashes)
            if (/^-+$/.test(trimmed)) return false
            // Must have actual content after the bullet
            const content = trimmed.replace(/^[•\-]\s*/, '').trim()
            return content.length > 0
          })
          .map((line: string) => line.replace(/^[•\-]\s*/, '').trim())
        setKeyPoints(points)

        // Extract model info
        const modelMatch = data.summary.match(/\[Model: ([^\]]+)\]/i)
        if (modelMatch) {
          setSummaryModel(modelMatch[1])
        }

        setShowSummary(true)
      } else {
        // Handle error responses
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        const errorMessage = errorData.detail || 'Failed to generate summary'

        if (response.status === 400 && errorMessage.includes('content')) {
          setSummaryError('Article content is too short to summarize (minimum 50 characters)')
        } else if (response.status === 500 && errorMessage.includes('API key')) {
          setSummaryError('LLM API key not configured. Please check server configuration.')
        } else if (response.status === 504 || errorMessage.includes('timeout')) {
          setSummaryError('Summary generation timed out. Please try again.')
        } else {
          setSummaryError(`Failed to generate summary: ${errorMessage}`)
        }
        console.error('Summary generation failed:', response.status, errorMessage)
      }
    } catch (error) {
      console.error('Error generating summary:', error)
      if (error instanceof TypeError && error.message.includes('fetch')) {
        setSummaryError('Cannot connect to server. Please check if the backend is running.')
      } else {
        setSummaryError('An unexpected error occurred. Please try again.')
      }
    } finally {
      setGeneratingSummary(false)
    }
  }

  const recollectArticle = async () => {
    if (!article) return

    setRecollecting(true)
    try {
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}/recollect`, {
        method: 'POST'
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          // Refresh the article to show new content
          fetchArticle()
          setHasChanges(true)
          alert(`Article recollected successfully!\nWord count: ${data.word_count}\nReading time: ${data.reading_time_minutes} min`)
        } else {
          alert(`Failed to recollect: ${data.error}`)
        }
      } else {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }))
        alert(`Failed to recollect article: ${errorData.detail}`)
      }
    } catch (error) {
      console.error('Error recollecting article:', error)
      alert('Failed to recollect article. Please check if the backend is running.')
    } finally {
      setRecollecting(false)
    }
  }

  const beautifyMarkdown = async () => {
    if (!article) return
    
    setBeautifyingMarkdown(true)
    try {
      const response = await fetch(`http://localhost:8000/api/article-preview/beautify/${article.id}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const data = await response.json()
        
        if (data.changed) {
          // Reload the article to get the beautified content
          const articleResponse = await fetch(`http://localhost:8000/api/articles/${article.id}`)
          if (articleResponse.ok) {
            const updatedArticle = await articleResponse.json()
            setArticle(updatedArticle)
            
            // If in edit mode, update the edited content too
            if (isEditingContent) {
              setEditedContent(updatedArticle.content_markdown)
            }
            
            alert('Markdown beautified successfully!')
          }
        } else {
          alert('Markdown is already well-formatted')
        }
      }
    } catch (error) {
      console.error('Error beautifying markdown:', error)
      alert('Failed to beautify markdown')
    } finally {
      setBeautifyingMarkdown(false)
    }
  }

  const saveTitle = async () => {
    if (!article || editedTitle === article.title) {
      setIsEditingTitle(false)
      return
    }
    
    setSavingEdits(true)
    try {
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}`, {
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
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}`, {
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
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}`, {
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

  const removeTag = async (tagId: number, tagName: string) => {
    if (!article) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}/tags/${encodeURIComponent(tagName)}`, {
        method: 'DELETE'
      })
      
      if (response.ok) {
        setArticle(prev => prev ? {
          ...prev,
          tags: prev.tags.filter(t => t.id !== tagId)
        } : null)
        setHasChanges(true)  // Mark as changed for list refresh
      }
    } catch (error) {
      console.error('Error removing tag:', error)
    }
  }

  const saveEditedDate = async () => {
    if (!article) return
    
    setSavingEdits(true)
    try {
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          published_at: editedDate ? new Date(editedDate).toISOString() : null 
        })
      })
      
      if (response.ok) {
        setArticle({
          ...article,
          published_at: editedDate ? new Date(editedDate).toISOString() : null
        })
        setIsEditingDate(false)
      }
    } catch (error) {
      console.error('Error saving date:', error)
    } finally {
      setSavingEdits(false)
    }
  }

  const saveEditedAuthor = async () => {
    if (!article) return
    
    setSavingEdits(true)
    try {
      // Check if we're using an existing author or creating a new one
      const existingAuthor = authors.find(a => a.name.toLowerCase() === authorInput.toLowerCase())
      
      let requestBody: any = {}
      if (existingAuthor) {
        requestBody.author_id = existingAuthor.id.toString()
      } else if (authorInput.trim()) {
        requestBody.author_name = authorInput.trim()
      } else if (selectedAuthorId) {
        requestBody.author_id = selectedAuthorId.toString()
      } else {
        requestBody.author_id = null // Clear author
      }

      const response = await fetch(`http://localhost:8000/api/articles/${article.id}/author`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })
      
      if (response.ok) {
        // Update the article with the new author
        if (authorInput.trim() || selectedAuthorId) {
          const authorToUse = existingAuthor || authors.find(a => a.id === selectedAuthorId)
          setArticle({
            ...article,
            author: {
              id: authorToUse?.id || 0,
              name: authorInput.trim() || authorToUse?.name || '',
              subdomain: authorToUse?.subdomain || '',
              url: authorToUse?.url || ''
            }
          })
          
          // If it's a new author, refresh the authors list
          if (!existingAuthor && authorInput.trim()) {
            fetchAuthors()
          }
        } else {
          setArticle({
            ...article,
            author: undefined
          })
        }
        setIsEditingAuthor(false)
        setShowAuthorSuggestions(false)
        setAuthorInput('')
      }
    } catch (error) {
      console.error('Error saving author:', error)
    } finally {
      setSavingEdits(false)
    }
  }

  const handleExtractMetadata = async () => {
    if (!article) return

    setExtractingMetadata(true)
    try {
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}/extract-metadata`, {
        method: 'POST'
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Extracted metadata:', result)

        // Refresh the article to get updated data
        await fetchArticle()

        // Show success message
        alert(`Successfully extracted:\n${result.updated_fields.includes('author_name') ? '✓ Author: ' + result.extracted.author : ''}\n${result.updated_fields.includes('published_at') ? '✓ Date: ' + result.extracted.date : ''}`)
      } else {
        const error = await response.json()
        alert('Failed to extract metadata: ' + (error.detail || 'Unknown error'))
      }
    } catch (error) {
      console.error('Error extracting metadata:', error)
      alert('Error extracting metadata. Check console for details.')
    } finally {
      setExtractingMetadata(false)
    }
  }

  // Add effect to filter authors based on input
  useEffect(() => {
    if (authorInput) {
      const filtered = authors.filter(a => 
        a.name.toLowerCase().includes(authorInput.toLowerCase())
      )
      setFilteredAuthors(filtered)
    } else {
      setFilteredAuthors(authors)
    }
  }, [authorInput, authors])

  const handleContextMenu = (e: React.MouseEvent) => {
    try {
      e.preventDefault()
      e.stopPropagation()
      
      console.log('=== CONTEXT MENU DEBUG ===')
      console.log('Event type:', e.type)
      console.log('Mouse position:', { x: e.clientX, y: e.clientY })
      
      // Get current selection
      const selection = window.getSelection()
      if (!selection || selection.rangeCount === 0 || selection.isCollapsed) {
        console.log('❌ No text selected')
        return
      }
      
      const text = selection.toString().trim()
      if (!text) {
        console.log('❌ Selected text is empty')
        return
      }
      
      console.log('✅ Selected text:', text)
      
      // Store the selection text only (not DOM nodes which can cause React issues)
      setSelectedText(text)
      selectedTextRef.current = text
      
      // Simple preserved selection without DOM references
      setPreservedSelection({
        text: text,
        rangeData: null  // Don't store DOM nodes in state
      })
      
      // Prepare tag text
      const tagText = text.replace(/\s+/g, '-')
      setTagEditText(tagText)
      setHasSelectedText(true)
      
      // Set context menu position
      const coords = { x: e.clientX, y: e.clientY }
      if (coords.y + 200 > window.innerHeight) {
        coords.y = e.clientY - 150
      }
      setSelectionCoords(coords)
      console.log('Menu coordinates:', coords)
      
      // Set flag to prevent dialog from closing
      isInteractingWithMenu.current = true
      
      // Show context menu
      setShowContextMenu(true)
      console.log('✅ Context menu should be showing now')
      console.log('=========================')
    } catch (error) {
      console.error('❌ Error in handleContextMenu:', error)
      console.error('Stack trace:', (error as Error).stack)
      // Don't crash the component
      setShowContextMenu(false)
      setSelectedText('')
      selectedTextRef.current = ''
    }
  }

  const startTagCreation = () => {
    try {
      console.log('=== START TAG CREATION ===')
      console.log('selectedTextRef.current:', selectedTextRef.current)
      console.log('selectedText state:', selectedText)
      console.log('tagEditText:', tagEditText)
      console.log('selectionCoords:', selectionCoords)
      console.log('showTagCreation before:', showTagCreation)
      
      // Use the preserved text
      if (!selectedTextRef.current) {
        console.error('No text available for tag creation!')
        return
      }
      
      console.log('Starting tag creation with text:', selectedTextRef.current)
      
      // Show tag creation form FIRST, then hide context menu
      setShowTagCreation(true)
      console.log('Tag creation form set to show')
      
      // Hide context menu after a short delay
      setTimeout(() => {
        setShowContextMenu(false)
        console.log('Context menu hidden')
      }, 100)
      
      console.log('==========================')
    } catch (error) {
      console.error('Error in startTagCreation:', error)
      console.error('Stack:', (error as Error).stack)
      // Reset states to safe values
      setShowContextMenu(false)
      setShowTagCreation(false)
    }
  }

  const saveTagFromSelection = async () => {
    console.log('=== CONCEPT CREATION DEBUG ===')
    console.log('Concept text:', tagEditText)
    console.log('Article ID:', article?.id)
    console.log('Selected text stored:', selectedText)
    console.log('Preserved selection:', preservedSelection)
    
    if (!tagEditText || !article) {
      console.error('Missing required data:', { tagEditText, articleId: article?.id })
      return
    }
    
    // Clear any previous error
    setTagError('')
    
    // Check if concept already exists on article (case-insensitive)
    // Note: We'll need to update this when article structure is updated to use concepts
    if (article.tags?.some(tag => tag.tag.toLowerCase() === tagEditText.toLowerCase())) {
      console.warn(`Concept "${tagEditText}" already exists on article`)
      setTagError(`Concept "${tagEditText}" already exists on this article`)
      setTimeout(() => setTagError(''), 3000)
      return
    }
    
    try {
      // Use query parameter for concepts endpoint
      const params = new URLSearchParams({ text: tagEditText })
      console.log('Sending request with text:', tagEditText)
      console.log('URL:', `http://localhost:8000/api/articles/${article.id}/concepts?${params}`)
      
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}/concepts?${params}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      console.log('Response status:', response.status)
      const responseText = await response.text()
      console.log('Response body:', responseText)
      
      if (response.ok) {
        console.log(`✅ Concept "${tagEditText}" created and added to article`)
        // Refresh article to get new concepts
        fetchArticle()
        setHasChanges(true)  // Mark as changed for list refresh
        // Reset form
        cancelSelection()
      } else if (response.status === 400) {
        let error
        try {
          error = JSON.parse(responseText)
        } catch {
          error = { detail: responseText }
        }
        console.error('400 Error:', error)
        
        if (error.detail?.includes('already exists')) {
          setTagError(`Concept "${tagEditText}" already exists`)
          setTimeout(() => setTagError(''), 3000)
        } else {
          setTagError(error.detail || 'Error adding concept')
          setTimeout(() => setTagError(''), 5000)
        }
      } else {
        console.error('Unexpected response:', response.status, responseText)
        setTagError(`Server error: ${response.status}`)
        setTimeout(() => setTagError(''), 5000)
      }
    } catch (error) {
      console.error('Network error creating concept:', error)
      setTagError('Network error: Could not add concept')
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
    // Reset the interaction flag to allow dialog to close
    isInteractingWithMenu.current = false
    setHasSelectedText(false)
    setPreservedSelection(null)
    selectedTextRef.current = ''
    selectionRangeRef.current = null
    // Clear the flag after a small delay to allow any pending operations to complete
    setTimeout(() => {
      isInteractingWithMenu.current = false
    }, 100)
  }

  const saveHighlight = async () => {
    if (!selectedText || !article) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}/snippets`, {
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
        // Notify parent that snippets changed
        window.dispatchEvent(new CustomEvent('articleSnippetsUpdated', {
          detail: { articleId: article.id }
        }))
      }
    } catch (error) {
      console.error('Error saving highlight:', error)
    }
  }

  const saveAnnotation = async () => {
    if (!selectedText || !article) return
    
    try {
      const response = await fetch(`http://localhost:8000/api/articles/${article.id}/snippets`, {
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
        // Notify parent that snippets changed
        window.dispatchEvent(new CustomEvent('articleSnippetsUpdated', {
          detail: { articleId: article.id }
        }))
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
    
    // Filter and sort snippets by length (longest first) to avoid nested replacements
    const highlightableSnippets = article.snippets
      .filter(s => ['yellow', 'green', 'blue', 'pink'].includes(s.category))
      .sort((a, b) => b.text.length - a.text.length)
    
    highlightableSnippets.forEach(snippet => {
      const color = snippet.category === 'yellow' ? '#fff59d' :
                   snippet.category === 'green' ? '#a5d6a7' :
                   snippet.category === 'blue' ? '#90caf9' :
                   snippet.category === 'pink' ? '#f48fb1' : '#ffeb3b'
      
      // Escape special regex characters and create case-insensitive pattern
      const escapedText = snippet.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`(${escapedText})`, 'gi')
      
      highlightedText = highlightedText.replace(
        regex,
        `<mark style="background-color: ${color}; padding: 2px 4px; border-radius: 3px; font-weight: 500;">$1</mark>`
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
      <Dialog open={true} onOpenChange={(open) => {
        console.log('🟣 Dialog onOpenChange called with:', open)
        console.log('🟣 isInteractingWithMenu:', isInteractingWithMenu.current)
        if (!open) {
          // Don't close if we're interacting with the context menu
          if (isInteractingWithMenu.current) {
            console.log('🟣 Preventing dialog close - interacting with context menu')
            return
          }
          console.log('🟣 Dialog is being closed, calling onClose')
          // Refresh list if changes were made
          if (hasChanges && onArticleUpdated) {
            console.log('🟣 Changes detected, refreshing list')
            onArticleUpdated()
          }
          onClose()
        }
      }}>
        <DialogContent className="max-w-6xl max-h-[90vh] p-0 overflow-hidden">
          <VisuallyHidden>
            <DialogTitle>{decodeHtmlEntities(article.title) || 'Article Viewer'}</DialogTitle>
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
                        {decodeHtmlEntities(article.title)}
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
                    onClick={() => {
                      console.log('🔵 X-Button clicked, dispatching articleViewerClosed event')
                      // Dispatch event with article data for parent to update
                      window.dispatchEvent(new CustomEvent('articleViewerClosed', {
                        detail: { articleId: article.id }
                      }))
                      // Refresh list if changes were made
                      if (hasChanges && onArticleUpdated) {
                        console.log('🔵 Changes detected, refreshing list')
                        onArticleUpdated()
                      }
                      onClose()
                    }}
                    className="rounded-full"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>

                {/* Metadata */}
                <div className="flex flex-wrap items-center gap-4 mt-4 text-sm text-muted-foreground">
                  {/* Author */}
                  {isEditingAuthor ? (
                    <div className="flex items-center gap-2">
                      <User className="h-4 w-4" />
                      <div className="relative">
                        <Input
                          value={authorInput}
                          onChange={(e) => {
                            setAuthorInput(e.target.value)
                            setShowAuthorSuggestions(true)
                          }}
                          onFocus={() => setShowAuthorSuggestions(true)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') {
                              saveEditedAuthor()
                            }
                          }}
                          placeholder="Type author name or select..."
                          className="h-8 w-48"
                        />
                        {showAuthorSuggestions && filteredAuthors.length > 0 && authorInput && (
                          <div className="absolute top-full mt-1 w-full bg-background border rounded-md shadow-md z-50 max-h-48 overflow-y-auto">
                            {filteredAuthors.map(author => (
                              <button
                                key={author.id}
                                className="w-full px-3 py-2 text-left hover:bg-muted transition-colors text-sm"
                                onClick={() => {
                                  setAuthorInput(author.name)
                                  setSelectedAuthorId(author.id)
                                  setShowAuthorSuggestions(false)
                                }}
                              >
                                {author.name}
                              </button>
                            ))}
                            {!filteredAuthors.find(a => a.name.toLowerCase() === authorInput.toLowerCase()) && authorInput.trim() && (
                              <div className="px-3 py-2 text-sm text-muted-foreground border-t">
                                <span className="text-xs">Press Enter to create:</span>
                                <div className="font-medium">{authorInput}</div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={saveEditedAuthor}
                        disabled={savingEdits}
                        className="h-8 px-2"
                        title={filteredAuthors.find(a => a.name.toLowerCase() === authorInput.toLowerCase()) ? "Use existing author" : "Create new author"}
                      >
                        <Save className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setIsEditingAuthor(false)
                          setAuthorInput('')
                          setShowAuthorSuggestions(false)
                          setSelectedAuthorId(article.author?.id || null)
                        }}
                        className="h-8 px-2"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ) : (
                    article.author ? (
                      <button
                        onClick={() => {
                          setIsEditingAuthor(true)
                          setAuthorInput(article.author.name || '')
                          setSelectedAuthorId(article.author.id || null)
                        }}
                        className="flex items-center gap-1 hover:text-foreground transition-colors"
                      >
                        <User className="h-4 w-4" />
                        {article.author.name}
                        <Edit3 className="h-3 w-3 ml-1 opacity-50" />
                      </button>
                    ) : (
                      <button
                        onClick={() => {
                          setIsEditingAuthor(true)
                          setAuthorInput('')
                          setSelectedAuthorId(null)
                        }}
                        className="flex items-center gap-1 hover:text-foreground transition-colors text-muted-foreground"
                      >
                        <User className="h-4 w-4" />
                        <span className="italic">Add author</span>
                        <Plus className="h-3 w-3 ml-1 opacity-50" />
                      </button>
                    )
                  )}

                  {/* Published Date */}
                  {isEditingDate ? (
                    <div className="flex items-center gap-2">
                      <Calendar className="h-4 w-4" />
                      <Input
                        type="date"
                        value={editedDate}
                        onChange={(e) => setEditedDate(e.target.value)}
                        className="h-8 w-40"
                      />
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={saveEditedDate}
                        disabled={savingEdits}
                        className="h-8 px-2"
                      >
                        <Save className="h-3 w-3" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => {
                          setIsEditingDate(false)
                          setEditedDate(article.published_at ? article.published_at.split('T')[0] : '')
                        }}
                        className="h-8 px-2"
                      >
                        <X className="h-3 w-3" />
                      </Button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setIsEditingDate(true)}
                      className="flex items-center gap-1 hover:text-foreground transition-colors"
                    >
                      <Calendar className="h-4 w-4" />
                      {article.published_at ? new Date(article.published_at).toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' }) : 'No date'}
                      <Edit3 className="h-3 w-3 ml-1 opacity-50" />
                    </button>
                  )}

                  {/* Extract Metadata Button - only show if author or date is missing */}
                  {(!article.author || !article.published_at) && (
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleExtractMetadata}
                      disabled={extractingMetadata}
                      className="h-8 gap-1.5"
                    >
                      {extractingMetadata ? (
                        <>
                          <Loader2 className="h-3 w-3 animate-spin" />
                          Extracting...
                        </>
                      ) : (
                        <>
                          <Wand2 className="h-3 w-3" />
                          Extract {!article.author && !article.published_at ? 'Author & Date' : !article.author ? 'Author' : 'Date'}
                        </>
                      )}
                    </Button>
                  )}

                  {/* Read time and word count (non-editable) */}
                  <div className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    {article.reading_time_minutes} min read
                  </div>
                  <div className="flex items-center gap-1">
                    <FileText className="h-4 w-4" />
                    {article.word_count} words
                  </div>
                  {isEditingUrl ? (
                    <div className="flex items-center gap-2 w-full max-w-2xl">
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
                        className="h-8 w-full"
                        autoFocus
                      />
                      <Button
                        size="sm"
                        onClick={saveUrl}
                        className="h-8"
                      >
                        Save
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          setIsEditingUrl(false)
                          setEditedUrl(article.url || '')
                        }}
                        className="h-8"
                      >
                        Cancel
                      </Button>
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

                {/* AI Model Selection for Summarization */}
                {!article.summary && (
                  <div className="mt-4 p-4 border rounded-lg bg-muted/30">
                    <UnifiedModelSelector
                      taskType="article_summarizer"
                      value={summarizerModel || ''}
                      onValueChange={selectSummarizerModel}
                      label="Summarization Model"
                      description="Choose the AI model for generating article summaries"
                      disabled={modelLoading || generatingSummary}
                      compact={false}
                    />
                  </div>
                )}

                {/* Action Buttons */}
                <div className="flex flex-wrap gap-2 mt-4">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowEntityAnnotation(true)}
                    className="bg-gradient-to-r from-purple-500/10 to-purple-600/10 hover:from-purple-500/20 hover:to-purple-600/20"
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    Edit Annotation Review
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
                    disabled={generatingSummary || !summarizerModel}
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

                  {article.summary && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={generateSummary}
                      disabled={generatingSummary || !summarizerModel}
                      title="Regenerate summary with current model"
                    >
                      {generatingSummary ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Regenerating...
                        </>
                      ) : (
                        <>
                          <RefreshCw className="h-4 w-4 mr-2" />
                          Redo Summary
                        </>
                      )}
                    </Button>
                  )}

                  <Button
                    variant="outline"
                    size="sm"
                    onClick={recollectArticle}
                    disabled={recollecting || !article.url}
                    title="Re-fetch article content from URL"
                  >
                    {recollecting ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Recollecting...
                      </>
                    ) : (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Recollect
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
                    onClick={beautifyMarkdown}
                    disabled={beautifyingMarkdown}
                    title="Beautify and format the markdown content"
                  >
                    {beautifyingMarkdown ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Beautifying...
                      </>
                    ) : (
                      <>
                        <Wand2 className="h-4 w-4 mr-2" />
                        Beautify Markdown
                      </>
                    )}
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

              {/* Summary Error Message */}
              {summaryError && (
                <div className="px-6 pb-4">
                  <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                    <svg className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <div className="flex-1">
                      <p className="text-sm text-red-800 font-medium">Summary Generation Failed</p>
                      <p className="text-sm text-red-700 mt-1">{summaryError}</p>
                    </div>
                    <button
                      onClick={() => setSummaryError('')}
                      className="text-red-600 hover:text-red-800"
                      title="Dismiss"
                    >
                      <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}

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
                        <Tags className="h-3 w-3 mr-1" />
                        {tag.tag}
                        <button
                          onClick={() => removeTag(tag.id, tag.tag)}
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
                    <div 
                      className="relative p-4 rounded-lg"
                      style={{
                        background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0f9ff 100%)',
                        border: '1px solid #bfdbfe',
                        boxShadow: 'inset 0 1px 3px rgba(147, 197, 253, 0.2)'
                      }}
                      onMouseUp={() => {
                        const selection = window.getSelection()
                        const text = selection?.toString().trim()
                        if (text && text.length > 2) {
                          setSelectedSummaryText(text)
                        }
                      }}
                    >
                      {selectedSummaryText && (
                        <div className="absolute top-2 right-2 z-10">
                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={async (e) => {
                              e.stopPropagation()
                              if (!selectedSummaryText) return
                              
                              try {
                                const response = await fetch(
                                  `http://localhost:8000/api/articles/${article.id}/concepts?text=${encodeURIComponent(selectedSummaryText)}`,
                                  { method: 'POST' }
                                )
                                const data = await response.json()
                                if (data.success) {
                                  // Refresh the article to show the new concept
                                  const articleResponse = await fetch(`http://localhost:8000/api/articles/${article.id}`)
                                  const articleData = await articleResponse.json()
                                  setArticle(articleData)
                                  setHasChanges(true)  // Mark as changed for list refresh
                                  setSelectedSummaryText('')
                                  window.getSelection()?.removeAllRanges()
                                }
                              } catch (error) {
                                console.error('Error creating concept:', error)
                                alert('Failed to create concept')
                              }
                            }}
                            className="text-xs shadow-md"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            Create Concept
                          </Button>
                        </div>
                      )}
                      <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-h1:text-xl prose-h2:text-lg prose-h3:text-base prose-strong:text-gray-900 prose-ul:list-disc prose-ol:list-decimal prose-li:text-gray-700 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100">
                        <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeRaw]}
                        components={{
                          h1: ({children}) => <h1 className="text-xl font-bold mt-4 mb-3 text-gray-900">{children}</h1>,
                          h2: ({children}) => <h2 className="text-lg font-semibold mt-3 mb-2 text-gray-800">{children}</h2>,
                          h3: ({children}) => <h3 className="text-base font-semibold mt-2 mb-2 text-gray-800">{children}</h3>,
                          p: ({ children, ...props }) => {
                            const hasCodeBlock = React.Children.toArray(children).some(
                              child => React.isValidElement(child) && (
                                child.type === 'pre' || 
                                child.props?.node?.tagName === 'pre'
                              )
                            )
                            
                            if (hasCodeBlock) {
                              return <div className="mb-3" {...props}>{children}</div>
                            }
                            
                            return <p className="mb-3 text-gray-700 leading-relaxed" {...props}>{children}</p>
                          },
                          ul: ({children}) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                          ol: ({children}) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                          li: ({children}) => <li className="text-gray-700">{children}</li>,
                          strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                          em: ({children}) => <em className="italic text-gray-700">{children}</em>,
                          blockquote: ({children}) => (
                            <blockquote className="border-l-4 border-blue-500 pl-3 py-1 my-3 italic bg-blue-50 rounded-r">
                              {children}
                            </blockquote>
                          ),
                          code: ({children, className, ...props}) => {
                            const isInline = !className?.includes('language-')
                            if (isInline) {
                              return <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono text-gray-800">{children}</code>;
                            }
                            return (
                              <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto mb-3">
                                <code className="text-sm font-mono">{children}</code>
                              </pre>
                            );
                          },
                          hr: () => <hr className="my-3 border-gray-300" />,
                          a: ({href, children}) => (
                            <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
                              {children}
                            </a>
                          ),
                          table: ({children}) => (
                            <div className="overflow-x-auto mb-3">
                              <table className="min-w-full border border-gray-300 text-sm">{children}</table>
                            </div>
                          ),
                          th: ({children}) => <th className="border border-gray-300 px-3 py-1.5 bg-gray-100 font-semibold text-left">{children}</th>,
                          td: ({children}) => <td className="border border-gray-300 px-3 py-1.5">{children}</td>,
                        }}
                      >
                        {article.summary
                          ?.replace(/<think>/gi, '')
                          .replace(/<\/think>/gi, '')
                          .replace(/<think[^>]*>/gi, '')
                        }
                      </ReactMarkdown>
                      </div>
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

              {/* Snippets Section */}
              {article.snippets && article.snippets.length > 0 && (
                <Card className="mb-6">
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg flex items-center gap-2">
                        <StickyNote className="h-5 w-5" />
                        Saved Snippets
                        <Badge variant="secondary">{article.snippets.length}</Badge>
                      </CardTitle>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {article.snippets.map((snippet, index) => (
                        <div key={snippet.id || index} className="border rounded-lg p-3 hover:bg-gray-50">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <Badge variant="outline" className="text-xs">
                                  {snippet.category === 'insight' && '💡 Insight'}
                                  {snippet.category === 'question' && '❓ Question'}
                                  {snippet.category === 'critique' && '🤔 Critique'}
                                  {snippet.category === 'todo' && '✅ Todo'}
                                  {snippet.category === 'quote' && '💬 Quote'}
                                  {snippet.category === 'yellow' && '🟡 Highlight'}
                                  {snippet.category === 'green' && '🟢 Highlight'}
                                  {snippet.category === 'blue' && '🔵 Highlight'}
                                  {snippet.category === 'pink' && '🩷 Highlight'}
                                  {!snippet.category && '📝 Note'}
                                </Badge>
                                {snippet.importance && (
                                  <Badge variant="outline" className="text-xs">
                                    Importance: {snippet.importance}/10
                                  </Badge>
                                )}
                              </div>
                              <div className="text-sm font-medium bg-gray-100 p-2 rounded mb-2">
                                "{snippet.text}"
                              </div>
                              {snippet.annotation && (
                                <div className="text-sm text-gray-600 italic">
                                  📝 {snippet.annotation}
                                </div>
                              )}
                            </div>
                            <button
                              onClick={async () => {
                                console.log('Deleting snippet:', snippet.id, 'from article:', article.id)
                                if (window.confirm('Are you sure you want to delete this snippet?')) {
                                  try {
                                    const url = `http://localhost:8000/api/articles/${article.id}/snippets/${snippet.id}`
                                    console.log('DELETE URL:', url)
                                    const response = await fetch(url, { 
                                      method: 'DELETE',
                                      headers: {
                                        'Content-Type': 'application/json'
                                      }
                                    })
                                    console.log('Delete response:', response.status)
                                    if (response.ok) {
                                      console.log('Snippet deleted successfully')
                                      fetchArticle() // Refresh to show updated snippets
                                    } else {
                                      const errorText = await response.text()
                                      console.error('Delete failed:', response.status, errorText)
                                      alert(`Failed to delete snippet: ${errorText}`)
                                    }
                                  } catch (error) {
                                    console.error('Error deleting snippet:', error)
                                    alert('Network error: Could not delete snippet')
                                  }
                                }
                              }}
                              className="p-1 hover:bg-red-100 rounded"
                              title="Delete snippet"
                            >
                              <Trash2 className="h-4 w-4 text-red-600" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
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
                  onMouseDown={(e) => {
                    // Don't clear selection on right-click
                    if (e.button === 2) {
                      e.preventDefault()
                    }
                  }}
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
                        // Check if there are any snippets that might be highlights
                        const hasHighlights = article.snippets && article.snippets.length > 0 && 
                          article.snippets.some(s => 
                            ['yellow', 'green', 'blue', 'pink'].includes(s.category) &&
                            content.toLowerCase().includes(s.text.toLowerCase())
                          )
                        
                        if (hasHighlights) {
                          return (
                            <p 
                              className="mb-4 leading-relaxed"
                              onContextMenu={handleContextMenu}
                              {...props}
                              dangerouslySetInnerHTML={{ 
                                __html: highlightSnippets(content) 
                              }}
                            />
                          )
                        }
                        
                        return (
                          <p 
                            className="mb-4 leading-relaxed" 
                            onContextMenu={handleContextMenu}
                            onMouseUp={() => {
                              // Capture selection on mouseup
                              const selection = window.getSelection()
                              if (selection && selection.toString().trim() !== '') {
                                lastSelectionRef.current = {
                                  text: selection.toString().trim(),
                                  time: Date.now()
                                }
                              }
                            }}
                            {...props}
                          >
                            {children}
                          </p>
                        )
                      },
                      h1: ({node, ...props}) => (
                        <h1 
                          className="text-3xl font-bold mt-8 mb-4" 
                          onContextMenu={handleContextMenu}
                          onMouseUp={() => {
                            const selection = window.getSelection()
                            if (selection && selection.toString().trim() !== '') {
                              lastSelectionRef.current = {
                                text: selection.toString().trim(),
                                time: Date.now()
                              }
                            }
                          }}
                          {...props} 
                        />
                      ),
                      h2: ({node, ...props}) => (
                        <h2 
                          className="text-2xl font-bold mt-6 mb-3" 
                          onContextMenu={handleContextMenu}
                          onMouseUp={() => {
                            const selection = window.getSelection()
                            if (selection && selection.toString().trim() !== '') {
                              lastSelectionRef.current = {
                                text: selection.toString().trim(),
                                time: Date.now()
                              }
                            }
                          }}
                          {...props} 
                        />
                      ),
                      h3: ({node, ...props}) => (
                        <h3 
                          className="text-xl font-semibold mt-5 mb-2" 
                          onContextMenu={handleContextMenu}
                          onMouseUp={() => {
                            const selection = window.getSelection()
                            if (selection && selection.toString().trim() !== '') {
                              lastSelectionRef.current = {
                                text: selection.toString().trim(),
                                time: Date.now()
                              }
                            }
                          }}
                          {...props} 
                        />
                      ),
                      h4: ({node, ...props}) => (
                        <h4 
                          className="text-lg font-semibold mt-4 mb-2" 
                          onContextMenu={handleContextMenu}
                          onMouseUp={() => {
                            const selection = window.getSelection()
                            if (selection && selection.toString().trim() !== '') {
                              lastSelectionRef.current = {
                                text: selection.toString().trim(),
                                time: Date.now()
                              }
                            }
                          }}
                          {...props} 
                        />
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
                        <li className="leading-relaxed" onContextMenu={handleContextMenu} {...props} />
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
                      code: ({node, className, children, ...props}: any) => {
                        const match = /language-(\w+)/.exec(className || '')
                        const isInline = !match && !className?.includes('language-')
                        
                        return isInline ? (
                          <code
                            {...props}
                            className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
                          >
                            {children}
                          </code>
                        ) : (
                          <div className="my-4">
                            <pre className="bg-muted p-4 rounded-lg overflow-auto">
                              <code className={`font-mono text-sm ${className || ''}`} {...props}>
                                {children}
                              </code>
                            </pre>
                          </div>
                        )
                      }
                    }}
                  >
                    {(article.content_markdown || '')
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
      {showContextMenu && selectionCoords && selectionCoords.x !== undefined && selectionCoords.y !== undefined && ReactDOM.createPortal(
        <>
          {console.log('Rendering context menu at:', selectionCoords)}
          {console.log('Selected text:', selectedText)}
          {console.log('Has selected text:', hasSelectedText)}
          {/* Ensure flag is set when menu is rendered */}
          {(() => { isInteractingWithMenu.current = true; return null })()}
          {/* Test visibility div */}
          <div 
            className="context-menu"
            style={{
              position: 'fixed',
              left: `${selectionCoords.x - 100}px`,
              top: `${selectionCoords.y}px`,
              width: '200px',
              backgroundColor: 'white',
              border: '2px solid black',
              borderRadius: '8px',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.3)',
              padding: '8px',
              zIndex: 2147483647,
              pointerEvents: 'auto',
              display: 'block',
              visibility: 'visible',
              opacity: 1
            }}
            onClick={(e) => {
              e.stopPropagation()
              e.preventDefault()
            }}
            onMouseDown={(e) => {
              e.stopPropagation()
              e.preventDefault()
            }}
            onMouseUp={(e) => {
              e.stopPropagation()
              e.preventDefault()
            }}
          >
          <button
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
            }}
            onClick={(e) => {
              try {
                e.preventDefault()
                e.stopPropagation()
                console.log('Highlighting clicked')
                console.log('Using text:', selectedTextRef.current)
                // Keep the flag set while transitioning to the form
                isInteractingWithMenu.current = true
                // Text is already preserved
                setShowContextMenu(false)
                setShowHighlightForm(true)
                // Don't clear the flag here - let the useEffect handle it
              } catch (error) {
                console.error('Error in highlighting button:', error)
              }
            }}
            style={{
              width: '100%',
              padding: '8px 12px',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <Palette className="h-4 w-4" />
            Highlighting
          </button>
          <button
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
            }}
            onClick={(e) => {
              try {
                e.preventDefault()
                e.stopPropagation()
                console.log('Create Snippet clicked')
                console.log('Using text:', selectedTextRef.current)
                // Keep the flag set while transitioning to the form
                isInteractingWithMenu.current = true
                // Text is already preserved
                setShowContextMenu(false)
                setShowAnnotationForm(true)
                // Don't clear the flag here - let the useEffect handle it
              } catch (error) {
                console.error('Error in snippet button:', error)
              }
            }}
            style={{
              width: '100%',
              padding: '8px 12px',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <StickyNote className="h-4 w-4" />
            Create Snippet
          </button>
          <div style={{ height: '1px', backgroundColor: '#e5e7eb', margin: '4px 0' }} />
          <button
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
            }}
            onClick={(e) => {
              try {
                e.preventDefault()
                e.stopPropagation()
                console.log('Concept Creation clicked')
                console.log('Using text:', selectedTextRef.current)
                // Keep the flag set while transitioning to the form
                isInteractingWithMenu.current = true
                // Preserve the selected text and show tag creation form
                setTagEditText(selectedTextRef.current || '')
                setShowContextMenu(false)
                setShowTagCreation(true)
                // Don't clear the flag here - let the useEffect handle it
              } catch (error) {
                console.error('Error in tag creation button:', error)
              }
            }}
            style={{
              width: '100%',
              padding: '8px 12px',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <span>🏷️</span>
            <span>Concept Creation</span>
          </button>
          <div style={{ height: '1px', backgroundColor: '#e5e7eb', margin: '4px 0' }} />
          <button
            onMouseDown={(e) => {
              e.preventDefault()
              e.stopPropagation()
            }}
            onClick={(e) => {
              e.preventDefault()
              e.stopPropagation()
              console.log('Cancel clicked')
              cancelSelection()
            }}
            style={{
              width: '100%',
              padding: '8px 12px',
              textAlign: 'left',
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              fontSize: '14px',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer'
            }}
            onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
            onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
          >
            <X className="h-4 w-4" />
            Cancel
          </button>
        </div>
        </>,
        document.body
      )}

      {/* Highlight Form */}
      {showHighlightForm && selectionCoords && (() => {
        // Create a dedicated container for the portal
        const portalContainer = document.createElement('div')
        portalContainer.style.position = 'fixed'
        portalContainer.style.top = '0'
        portalContainer.style.left = '0'
        portalContainer.style.right = '0'
        portalContainer.style.bottom = '0'
        portalContainer.style.zIndex = '2147483647'
        portalContainer.style.pointerEvents = 'none'
        document.body.appendChild(portalContainer)
        
        // Clean up container when component unmounts
        setTimeout(() => {
          if (document.body.contains(portalContainer) && !showHighlightForm) {
            document.body.removeChild(portalContainer)
          }
        }, 100)
        
        return ReactDOM.createPortal(
          <div className="fixed w-80 highlight-form" style={{
            left: `${selectionCoords?.x || 100}px`,
            top: `${selectionCoords?.y || 100}px`,
            transform: 'translateX(-50%)',
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
            pointerEvents: 'auto'
          }}>
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold">🎨 Highlighting</h3>
              <button
                type="button"
                onMouseUp={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  console.log('Highlight X button MOUSEUP')
                  cancelSelection()
                }}
                className="h-6 w-6 rounded hover:bg-gray-100 flex items-center justify-center"
                style={{ cursor: 'pointer' }}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="p-4 space-y-3">
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
                  <button
                    key={color.value}
                    type="button"
                    onMouseUp={(e) => {
                      e.stopPropagation()
                      e.preventDefault()
                      console.log(`Highlight color ${color.value} selected`)
                      setHighlightColor(color.value)
                    }}
                    className={`flex-1 px-3 py-2 rounded-md border ${
                      highlightColor === color.value 
                        ? 'bg-blue-600 text-white border-blue-600' 
                        : 'bg-white border-gray-300 hover:bg-gray-50'
                    }`}
                    style={{ cursor: 'pointer' }}
                  >
                    {color.emoji}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="flex gap-2">
              <button
                type="button"
                onMouseUp={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  console.log('Highlight Cancel button MOUSEUP')
                  cancelSelection()
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                style={{ cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onMouseUp={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  console.log('Save Highlight button MOUSEUP')
                  saveHighlight()
                }}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                style={{ cursor: 'pointer' }}
              >
                Mark in {highlightColor.charAt(0).toUpperCase() + highlightColor.slice(1)}
              </button>
            </div>
          </div>
        </div>,
        portalContainer
        )
      })()}

      {/* Annotation Form */}
      {showAnnotationForm && selectionCoords && (() => {
        // Create a dedicated container for the portal
        const portalContainer = document.createElement('div')
        portalContainer.style.position = 'fixed'
        portalContainer.style.top = '0'
        portalContainer.style.left = '0'
        portalContainer.style.right = '0'
        portalContainer.style.bottom = '0'
        portalContainer.style.zIndex = '2147483647'
        portalContainer.style.pointerEvents = 'none'
        document.body.appendChild(portalContainer)
        
        // Clean up container when component unmounts
        setTimeout(() => {
          if (document.body.contains(portalContainer) && !showAnnotationForm) {
            document.body.removeChild(portalContainer)
          }
        }, 100)
        
        return ReactDOM.createPortal(
          <div className="fixed w-96 annotation-form" style={{
            left: `${selectionCoords?.x || 100}px`,
            top: `${selectionCoords?.y || 100}px`,
            transform: 'translateX(-50%)',
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
            pointerEvents: 'auto'
          }}>
            <div className="p-4 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-semibold">Create Annotation</h3>
              <button
                type="button"
                onMouseUp={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  console.log('Annotation X button MOUSEUP')
                  cancelSelection()
                }}
                className="h-6 w-6 rounded hover:bg-gray-100 flex items-center justify-center"
                style={{ cursor: 'pointer' }}
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="p-4 space-y-3">
            <div>
              <Label className="text-sm font-medium">Selected Text:</Label>
              <div className="mt-1 p-2 bg-gray-50 rounded border text-sm">
                {selectedText}
              </div>
            </div>
            
            <div>
              <Label className="text-sm font-medium">Category:</Label>
              <select
                value={snippetCategory}
                onChange={(e) => setSnippetCategory(e.target.value)}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                style={{ cursor: 'pointer' }}
              >
                <option value="insight">💡 Insight</option>
                <option value="question">❓ Question</option>
                <option value="critique">🤔 Critique</option>
                <option value="todo">✅ Todo</option>
                <option value="quote">💬 Quote</option>
              </select>
            </div>
            
            <div>
              <Label className="text-sm font-medium">Add Note (optional):</Label>
              <textarea
                placeholder="Add your thoughts or context about this snippet..."
                value={annotation}
                onChange={(e) => setAnnotation(e.target.value)}
                onMouseDown={(e) => e.stopPropagation()}
                onClick={(e) => e.stopPropagation()}
                rows={3}
                className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                style={{ cursor: 'text' }}
              />
            </div>
            
            <div className="flex gap-2">
              <button
                type="button"
                onMouseUp={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  console.log('Annotation Cancel button MOUSEUP')
                  cancelSelection()
                }}
                className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                style={{ cursor: 'pointer' }}
              >
                Cancel
              </button>
              <button
                type="button"
                onMouseUp={(e) => {
                  e.stopPropagation()
                  e.preventDefault()
                  console.log('Save Snippet button MOUSEUP')
                  saveAnnotation()
                }}
                className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                style={{ cursor: 'pointer' }}
              >
                Save Snippet
              </button>
            </div>
          </div>
        </div>,
        portalContainer
        )
      })()}

      {/* Concept Creation Form */}
      {showTagCreation && selectionCoords && (() => {
        // Create a dedicated container for the portal
        const portalContainer = document.createElement('div')
        portalContainer.style.position = 'fixed'
        portalContainer.style.top = '0'
        portalContainer.style.left = '0'
        portalContainer.style.right = '0'
        portalContainer.style.bottom = '0'
        portalContainer.style.zIndex = '2147483647'
        portalContainer.style.pointerEvents = 'none'
        document.body.appendChild(portalContainer)
        
        // Clean up container when component unmounts
        setTimeout(() => {
          if (document.body.contains(portalContainer) && !showTagCreation) {
            document.body.removeChild(portalContainer)
          }
        }, 100)
        
        return ReactDOM.createPortal(
          (() => {
            try {
              console.log('Rendering tag creation form...')
              console.log('selectedText for form:', selectedText)
              console.log('tagEditText for form:', tagEditText)
              console.log('Coordinates for form:', selectionCoords)
              return (
                <div 
                  className="fixed w-96 tag-creation-form" 
                  style={{
                    left: `${selectionCoords?.x || 100}px`,
                    top: `${selectionCoords?.y || 100}px`,
                    transform: 'translateX(-50%)',
                    backgroundColor: 'white',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 10px 40px rgba(0, 0, 0, 0.3)',
                    pointerEvents: 'auto'
                  }}>
                  <div className="p-4 border-b">
                    <div className="flex items-center justify-between">
                      <h3 className="text-base font-semibold">🏷️ Create Concept from Selection</h3>
                <button
                  type="button"
                  onMouseUp={(e) => {
                    e.stopPropagation()
                    e.preventDefault()
                    console.log('X button MOUSEUP')
                    cancelSelection()
                  }}
                  className="h-6 w-6 rounded hover:bg-gray-100 flex items-center justify-center"
                  style={{ cursor: 'pointer' }}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="p-4 space-y-3">
              <div className="text-sm text-muted-foreground">
                Original text: "{selectedText ? selectedText.substring(0, 50) : ''}{selectedText && selectedText.length > 50 ? '...' : ''}"
              </div>
              
              <div>
                <Label htmlFor="tag-edit">Edit tag name:</Label>
                <Input
                  id="tag-edit"
                  value={tagEditText}
                  onChange={(e) => setTagEditText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      e.stopPropagation()
                      saveTagFromSelection()
                    } else if (e.key === 'Escape') {
                      e.preventDefault()
                      e.stopPropagation()
                      cancelSelection()
                    }
                  }}
                  onClick={(e) => {
                    e.stopPropagation()
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
                <button
                  type="button"
                  onMouseUp={(e) => {
                    e.stopPropagation()
                    e.preventDefault()
                    console.log('Cancel button MOUSEUP')
                    cancelSelection()
                  }}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50"
                  style={{ cursor: 'pointer' }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onMouseUp={(e) => {
                    e.stopPropagation()
                    e.preventDefault()
                    console.log('Create Concept button MOUSEUP')
                    console.log('Current tagEditText:', tagEditText)
                    saveTagFromSelection()
                  }}
                  disabled={!tagEditText}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  style={{ cursor: tagEditText ? 'pointer' : 'not-allowed' }}
                >
                  Create Concept
                </button>
              </div>
            </div>
          </div>
              )
            } catch (error) {
              console.error('Error rendering tag creation form:', error)
              console.error('Stack:', (error as Error).stack)
              return null
            }
          })(),
          portalContainer
        )
      })()}

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
                setHasChanges(true)  // Mark as changed for list refresh
              }}
            />
          </DialogContent>
        </Dialog>
      )}
    </>
  )
  } catch (error) {
    console.error('ArticleViewerModern encountered an error:', error)
    console.error('Stack:', (error as Error).stack)
    return (
      <Dialog open={true} onOpenChange={onClose}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Error</DialogTitle>
            <DialogDescription>
              An error occurred while rendering the article viewer. Please try again.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button onClick={onClose}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    )
  }
}

export default ArticleViewerModern