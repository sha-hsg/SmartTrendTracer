/**
 * Sub-hook: Article field editing state and save operations.
 * Manages title, content, URL, date, and author editing.
 */
import { useState, useEffect, useMemo, useCallback } from 'react'
import { API_BASE_URL } from '@/config/api'
import type { FullArticle, Author } from './types'

export interface UseArticleEditingParams {
  article: FullArticle | null
  fetchAuthors: () => Promise<void>
  authors: Author[]
}

export function useArticleEditing({
  article,
  fetchAuthors,
  authors,
}: UseArticleEditingParams) {
  // --- Editing state ---
  const [isEditingTitle, setIsEditingTitle] = useState(false)
  const [editedTitle, setEditedTitle] = useState('')
  const [isEditingContent, setIsEditingContent] = useState(false)
  const [editedContent, setEditedContent] = useState('')
  const [isEditingUrl, setIsEditingUrl] = useState(false)
  const [editedUrl, setEditedUrl] = useState('')
  const [isEditingDate, setIsEditingDate] = useState(false)
  const [editedDate, setEditedDate] = useState('')
  const [isEditingAuthor, setIsEditingAuthor] = useState(false)
  const [selectedAuthorId, setSelectedAuthorId] = useState<number | null>(null)
  const [authorInput, setAuthorInput] = useState('')
  const [showAuthorSuggestions, setShowAuthorSuggestions] = useState(false)
  const [savingEdits, setSavingEdits] = useState(false)

  // Sync editing fields when article data arrives/changes
  useEffect(() => {
    if (article) {
      setEditedTitle(article.title)
      setEditedContent(article.content_markdown)
      setEditedDate(article.published_at ? article.published_at.split('T')[0] : '')
      setSelectedAuthorId(article.author?.id || null)
    }
  }, [article])

  // Computed: filter authors based on input
  const filteredAuthors = useMemo(() => {
    if (authorInput) {
      return authors.filter(a =>
        a.name.toLowerCase().includes(authorInput.toLowerCase())
      )
    }
    return authors
  }, [authorInput, authors])

  const saveTitle = useCallback(async () => {
    if (!article || editedTitle === article.title) {
      setIsEditingTitle(false)
      return
    }
    setSavingEdits(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: editedTitle })
      })
      if (response.ok) {
        setIsEditingTitle(false)
        return editedTitle
      }
    } catch (error) {
      console.error('Error saving title:', error)
    } finally {
      setSavingEdits(false)
    }
    return undefined
  }, [article, editedTitle])

  const saveContent = useCallback(async () => {
    if (!article || editedContent === article.content_markdown) {
      setIsEditingContent(false)
      return
    }
    setSavingEdits(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content_markdown: editedContent })
      })
      if (response.ok) {
        setIsEditingContent(false)
        return editedContent
      }
    } catch (error) {
      console.error('Error saving content:', error)
    } finally {
      setSavingEdits(false)
    }
    return undefined
  }, [article, editedContent])

  const saveUrl = useCallback(async () => {
    if (!article || editedUrl === article.url) {
      setIsEditingUrl(false)
      return
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: editedUrl || null })
      })
      if (response.ok) {
        setIsEditingUrl(false)
        return editedUrl || null
      }
    } catch (error) {
      console.error('Error saving URL:', error)
    }
    return undefined
  }, [article, editedUrl])

  const saveEditedDate = useCallback(async () => {
    if (!article) return
    setSavingEdits(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          published_at: editedDate ? new Date(editedDate).toISOString() : null
        })
      })
      if (response.ok) {
        setIsEditingDate(false)
        return editedDate ? new Date(editedDate).toISOString() : null
      }
    } catch (error) {
      console.error('Error saving date:', error)
    } finally {
      setSavingEdits(false)
    }
    return undefined
  }, [article, editedDate])

  const saveEditedAuthor = useCallback(async () => {
    if (!article) return
    setSavingEdits(true)
    try {
      const existingAuthor = authors.find(a => a.name.toLowerCase() === authorInput.toLowerCase())
      let requestBody: Record<string, string | null> = {}
      if (existingAuthor) {
        requestBody.author_id = existingAuthor.id.toString()
      } else if (authorInput.trim()) {
        requestBody.author_name = authorInput.trim()
      } else if (selectedAuthorId) {
        requestBody.author_id = selectedAuthorId.toString()
      } else {
        requestBody.author_id = null
      }
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}/author`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody)
      })
      if (response.ok) {
        let newAuthor: FullArticle['author'] | undefined
        if (authorInput.trim() || selectedAuthorId) {
          const authorToUse = existingAuthor || authors.find(a => a.id === selectedAuthorId)
          newAuthor = {
            id: authorToUse?.id || 0,
            name: authorInput.trim() || authorToUse?.name || '',
            subdomain: authorToUse?.subdomain || '',
            url: authorToUse?.url || ''
          }
          if (!existingAuthor && authorInput.trim()) {
            fetchAuthors()
          }
        }
        setIsEditingAuthor(false)
        setShowAuthorSuggestions(false)
        setAuthorInput('')
        return { success: true as const, author: newAuthor }
      }
    } catch (error) {
      console.error('Error saving author:', error)
    } finally {
      setSavingEdits(false)
    }
    return undefined
  }, [article, authorInput, authors, selectedAuthorId, fetchAuthors])

  return {
    // Editing state
    isEditingTitle,
    setIsEditingTitle,
    editedTitle,
    setEditedTitle,
    isEditingContent,
    setIsEditingContent,
    editedContent,
    setEditedContent,
    isEditingUrl,
    setIsEditingUrl,
    editedUrl,
    setEditedUrl,
    isEditingDate,
    setIsEditingDate,
    editedDate,
    setEditedDate,
    isEditingAuthor,
    setIsEditingAuthor,
    selectedAuthorId,
    setSelectedAuthorId,
    authorInput,
    setAuthorInput,
    showAuthorSuggestions,
    setShowAuthorSuggestions,
    savingEdits,
    filteredAuthors,

    // Save operations
    saveTitle,
    saveContent,
    saveUrl,
    saveEditedDate,
    saveEditedAuthor,
  }
}
