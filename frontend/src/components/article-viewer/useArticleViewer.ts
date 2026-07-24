/**
 * Custom hook consolidating ArticleViewerModern's data fetching,
 * article state management, and all API operations.
 *
 * Reduces the original 7 useEffects (3 in component + 4 in useTextSelection)
 * down to 2 in this hook (fetch on id change, sync edited fields).
 * The author-filter effect is computed inline instead of via useEffect.
 *
 * Editing and snippet operations are delegated to sub-hooks:
 *   - useArticleEditing: title, content, URL, date, author editing
 *   - useArticleSnippets: snippet CRUD, highlights, annotations, tags
 */
import { useState, useEffect, useCallback } from 'react'
import { API_BASE_URL } from '@/config/api'
import { useArticleEditing } from './useArticleEditing'
import { useArticleSnippets } from './useArticleSnippets'

export interface FullArticle {
  id: number
  title: string
  subtitle: string | null
  author?: {
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

export interface Author {
  id: number
  name: string
  subdomain?: string
  url?: string
}

export function useArticleViewer(articleId: string | number) {
  // --- Core article state ---
  const [article, setArticle] = useState<FullArticle | null>(null)
  const [loading, setLoading] = useState(true)
  const [hasChanges, setHasChanges] = useState(false)

  // --- Summary state ---
  const [showSummary, setShowSummary] = useState(false)
  const [generatingSummary, setGeneratingSummary] = useState(false)
  const [summaryModel, setSummaryModel] = useState<string>('')
  const [summaryError, setSummaryError] = useState<string>('')
  const [keyPoints, setKeyPoints] = useState<string[]>([])

  // --- Action state ---
  const [exportingPDF, setExportingPDF] = useState(false)
  const [beautifyingMarkdown, setBeautifyingMarkdown] = useState(false)
  const [recollecting, setRecollecting] = useState(false)
  const [extractingMetadata, setExtractingMetadata] = useState(false)
  const [showEntityAnnotation, setShowEntityAnnotation] = useState(false)

  // --- Authors list ---
  const [authors, setAuthors] = useState<Author[]>([])

  // ---------- Helper: Extract key points from summary ----------
  const extractKeyPoints = useCallback((summary: string) => {
    const points = summary
      .split('\n')
      .filter((line: string) => {
        const trimmed = line.trim()
        if (!trimmed.startsWith('\u2022') && !trimmed.startsWith('-')) return false
        if (/^-+$/.test(trimmed)) return false
        const content = trimmed.replace(/^[\u2022\-]\s*/, '').trim()
        return content.length > 0
      })
      .map((line: string) => line.replace(/^[\u2022\-]\s*/, '').trim())
    setKeyPoints(points)

    const modelMatch = summary.match(/\[Model: ([^\]]+)\]/i)
    if (modelMatch) {
      setSummaryModel(modelMatch[1])
    }
  }, [])

  // ---------- Data fetching ----------
  const fetchArticle = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${articleId}`)
      if (!response.ok) {
        console.error('Failed to fetch article:', response.status)
        setArticle(null)
        setLoading(false)
        return
      }
      const data = await response.json()
      setArticle(data)
      if (data.summary) {
        extractKeyPoints(data.summary)
      }
    } catch (error) {
      console.error('Error fetching article:', error)
      setArticle(null)
    } finally {
      setLoading(false)
    }
  }, [articleId, extractKeyPoints])

  const fetchAuthors = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/authors/all`)
      if (response.ok) {
        const data = await response.json()
        setAuthors(data)
      }
    } catch (error) {
      console.error('Error fetching authors:', error)
    }
  }, [])

  // Effect: Fetch article + authors when articleId changes
  useEffect(() => {
    fetchArticle()
    fetchAuthors()
  }, [fetchArticle, fetchAuthors])

  // ---------- Delegate to sub-hooks ----------
  const editing = useArticleEditing({
    article,
    fetchAuthors,
    authors,
  })

  const snippets = useArticleSnippets({
    article,
    setArticle,
    setHasChanges,
    fetchArticle,
  })

  // ---------- Wrap editing saves to update local article state ----------
  const saveTitle = useCallback(async () => {
    const result = await editing.saveTitle()
    if (result !== undefined) {
      setArticle(prev => prev ? { ...prev, title: result } : null)
    }
  }, [editing.saveTitle])

  const saveContent = useCallback(async () => {
    const result = await editing.saveContent()
    if (result !== undefined) {
      setArticle(prev => prev ? { ...prev, content_markdown: result } : null)
    }
  }, [editing.saveContent])

  const saveUrl = useCallback(async () => {
    const result = await editing.saveUrl()
    if (result !== undefined) {
      setArticle(prev => prev ? { ...prev, url: result } : null)
    }
  }, [editing.saveUrl])

  const saveEditedDate = useCallback(async () => {
    const result = await editing.saveEditedDate()
    if (result !== undefined) {
      setArticle(prev => prev ? { ...prev, published_at: result } : null)
    }
  }, [editing.saveEditedDate])

  const saveEditedAuthor = useCallback(async () => {
    const result = await editing.saveEditedAuthor()
    if (result) {
      if (result.author) {
        setArticle(prev => prev ? { ...prev, author: result.author } : null)
      } else {
        setArticle(prev => prev ? { ...prev, author: undefined } : null)
      }
    }
  }, [editing.saveEditedAuthor])

  // ---------- API operations (kept in main hook) ----------

  const generateSummary = useCallback(async (model?: string) => {
    if (!article) return
    setGeneratingSummary(true)
    setSummaryError('')
    try {
      const qs = model ? `?model=${encodeURIComponent(model)}` : ''
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}/summarize${qs}`, {
        method: 'POST'
      })
      if (response.ok) {
        const data = await response.json()
        setArticle(prev => prev ? { ...prev, summary: data.summary } : null)
        extractKeyPoints(data.summary)
        setShowSummary(true)
      } else {
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
      if (error instanceof TypeError && (error as TypeError).message.includes('fetch')) {
        setSummaryError('Cannot connect to server. Please check if the backend is running.')
      } else {
        setSummaryError('An unexpected error occurred. Please try again.')
      }
    } finally {
      setGeneratingSummary(false)
    }
  }, [article, extractKeyPoints])

  const recollectArticle = useCallback(async () => {
    if (!article) return
    setRecollecting(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}/recollect`, {
        method: 'POST'
      })
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
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
  }, [article, fetchArticle])

  const beautifyMarkdown = useCallback(async () => {
    if (!article) return
    setBeautifyingMarkdown(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/article-preview/beautify/${article.id}`, {
        method: 'POST'
      })
      if (response.ok) {
        const data = await response.json()
        if (data.changed) {
          const articleResponse = await fetch(`${API_BASE_URL}/api/articles/${article.id}`)
          if (articleResponse.ok) {
            const updatedArticle = await articleResponse.json()
            setArticle(updatedArticle)
            if (editing.isEditingContent) {
              editing.setEditedContent(updatedArticle.content_markdown)
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
  }, [article, editing.isEditingContent, editing.setEditedContent])

  const exportToMarkdown = useCallback(() => {
    if (!article) return
    const lines: string[] = []
    lines.push(`# ${article.title}`)
    if (article.author?.name) lines.push(`\n**Author:** ${article.author.name}`)
    if (article.published_at) lines.push(`**Published:** ${new Date(article.published_at).toLocaleDateString()}`)
    if (article.url) lines.push(`**Source:** ${article.url}`)
    lines.push('\n---\n')
    lines.push(article.content_markdown || '')

    const blob = new Blob([lines.join('\n')], { type: 'text/markdown;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${article.title.replace(/[^a-z0-9]/gi, '_').slice(0, 60)}.md`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [article])

  const exportToPDF = useCallback(async () => {
    if (!article) return
    setExportingPDF(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/pdf/article/${article.id}`)
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
  }, [article])

  const handleExtractMetadata = useCallback(async (model?: string) => {
    if (!article) return
    setExtractingMetadata(true)
    try {
      const qs = model ? `?model=${encodeURIComponent(model)}` : ''
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}/extract-metadata${qs}`, {
        method: 'POST'
      })
      if (response.ok) {
        const result = await response.json()
        console.log('Extracted metadata:', result)
        await fetchArticle()
        alert(`Successfully extracted:\n${result.updated_fields.includes('author_name') ? '\u2713 Author: ' + result.extracted.author : ''}\n${result.updated_fields.includes('published_at') ? '\u2713 Date: ' + result.extracted.date : ''}`)
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
  }, [article, fetchArticle])

  return {
    // Core state
    article,
    setArticle,
    loading,
    hasChanges,
    setHasChanges,

    // Summary
    showSummary,
    setShowSummary,
    generatingSummary,
    summaryModel,
    summaryError,
    setSummaryError,
    keyPoints,

    // Editing (from sub-hook)
    isEditingTitle: editing.isEditingTitle,
    setIsEditingTitle: editing.setIsEditingTitle,
    editedTitle: editing.editedTitle,
    setEditedTitle: editing.setEditedTitle,
    isEditingContent: editing.isEditingContent,
    setIsEditingContent: editing.setIsEditingContent,
    editedContent: editing.editedContent,
    setEditedContent: editing.setEditedContent,
    isEditingUrl: editing.isEditingUrl,
    setIsEditingUrl: editing.setIsEditingUrl,
    editedUrl: editing.editedUrl,
    setEditedUrl: editing.setEditedUrl,
    isEditingDate: editing.isEditingDate,
    setIsEditingDate: editing.setIsEditingDate,
    editedDate: editing.editedDate,
    setEditedDate: editing.setEditedDate,
    isEditingAuthor: editing.isEditingAuthor,
    setIsEditingAuthor: editing.setIsEditingAuthor,
    selectedAuthorId: editing.selectedAuthorId,
    setSelectedAuthorId: editing.setSelectedAuthorId,
    authorInput: editing.authorInput,
    setAuthorInput: editing.setAuthorInput,
    showAuthorSuggestions: editing.showAuthorSuggestions,
    setShowAuthorSuggestions: editing.setShowAuthorSuggestions,
    savingEdits: editing.savingEdits,

    // Actions
    exportingPDF,
    beautifyingMarkdown,
    recollecting,
    extractingMetadata,
    showEntityAnnotation,
    setShowEntityAnnotation,

    // Authors
    authors,
    filteredAuthors: editing.filteredAuthors,

    // Operations (wrapped saves + sub-hook operations)
    fetchArticle,
    generateSummary,
    recollectArticle,
    beautifyMarkdown,
    saveTitle,
    saveContent,
    saveUrl,
    saveEditedDate,
    saveEditedAuthor,
    exportToPDF,
    exportToMarkdown,
    removeTag: snippets.removeTag,
    handleExtractMetadata,
    deleteSnippet: snippets.deleteSnippet,
    saveHighlight: snippets.saveHighlight,
    saveAnnotation: snippets.saveAnnotation,
    saveTagFromSelection: snippets.saveTagFromSelection,
    addConceptFromSummary: snippets.addConceptFromSummary,
  }
}
