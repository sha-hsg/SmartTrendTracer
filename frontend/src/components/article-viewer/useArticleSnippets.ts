/**
 * Sub-hook: Snippet CRUD, highlight, annotation, and tag operations.
 */
import { useCallback } from 'react'
import { API_BASE_URL } from '@/config/api'
import type { FullArticle } from './types'

export interface UseArticleSnippetsParams {
  article: FullArticle | null
  setArticle: React.Dispatch<React.SetStateAction<FullArticle | null>>
  setHasChanges: React.Dispatch<React.SetStateAction<boolean>>
  fetchArticle: () => Promise<void>
}

export function useArticleSnippets({
  article,
  setArticle,
  setHasChanges,
  fetchArticle,
}: UseArticleSnippetsParams) {
  const removeTag = useCallback(async (tagId: number, tagName: string) => {
    if (!article) return
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}/tags/${encodeURIComponent(tagName)}`, {
        method: 'DELETE'
      })
      if (response.ok) {
        setArticle(prev => prev ? {
          ...prev,
          tags: prev.tags.filter(t => t.id !== tagId)
        } : null)
        setHasChanges(true)
      }
    } catch (error) {
      console.error('Error removing tag:', error)
    }
  }, [article, setArticle, setHasChanges])

  const deleteSnippet = useCallback(async (snippetId: number) => {
    if (!article) return
    if (!window.confirm('Are you sure you want to delete this snippet?')) return
    try {
      const url = `/api/articles/${article.id}/snippets/${snippetId}`
      const response = await fetch(url, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' }
      })
      if (response.ok) {
        fetchArticle()
      } else {
        const errorText = await response.text()
        console.error('Delete failed:', response.status, errorText)
        alert(`Failed to delete snippet: ${errorText}`)
      }
    } catch (error) {
      console.error('Error deleting snippet:', error)
      alert('Network error: Could not delete snippet')
    }
  }, [article, fetchArticle])

  const saveHighlight = useCallback(async (text: string, color: string) => {
    if (!text || !article) return false
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}/snippets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          category: color,
          annotation: `Highlighted in ${color}`
        })
      })
      if (response.ok) {
        fetchArticle()
        window.dispatchEvent(new CustomEvent('articleSnippetsUpdated', {
          detail: { articleId: article.id }
        }))
        return true
      }
    } catch (error) {
      console.error('Error saving highlight:', error)
    }
    return false
  }, [article, fetchArticle])

  const saveAnnotation = useCallback(async (text: string, category: string, annotationText: string) => {
    if (!text || !article) return false
    try {
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}/snippets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text,
          category,
          annotation: annotationText || null
        })
      })
      if (response.ok) {
        fetchArticle()
        window.dispatchEvent(new CustomEvent('articleSnippetsUpdated', {
          detail: { articleId: article.id }
        }))
        return true
      }
    } catch (error) {
      console.error('Error saving snippet:', error)
    }
    return false
  }, [article, fetchArticle])

  const saveTagFromSelection = useCallback(async (tagText: string): Promise<{ success: boolean; error?: string }> => {
    if (!tagText || !article) {
      return { success: false, error: 'Missing required data' }
    }
    if (article.tags?.some(tag => tag.tag.toLowerCase() === tagText.toLowerCase())) {
      return { success: false, error: `Concept "${tagText}" already exists on this article` }
    }
    try {
      const params = new URLSearchParams({ text: tagText })
      const response = await fetch(`${API_BASE_URL}/api/articles/${article.id}/concepts?${params}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      })
      const responseText = await response.text()
      if (response.ok) {
        fetchArticle()
        setHasChanges(true)
        return { success: true }
      } else if (response.status === 400) {
        let error
        try { error = JSON.parse(responseText) } catch { error = { detail: responseText } }
        if (error.detail?.includes('already exists')) {
          return { success: false, error: `Concept "${tagText}" already exists` }
        }
        return { success: false, error: error.detail || 'Error adding concept' }
      } else {
        return { success: false, error: `Server error: ${response.status}` }
      }
    } catch (error) {
      console.error('Network error creating concept:', error)
      return { success: false, error: 'Network error: Could not add concept' }
    }
  }, [article, fetchArticle, setHasChanges])

  const addConceptFromSummary = useCallback(async (text: string) => {
    if (!article || !text) return false
    try {
      const response = await fetch(
        `/api/articles/${article.id}/concepts?text=${encodeURIComponent(text)}`,
        { method: 'POST' }
      )
      const data = await response.json()
      if (data.success) {
        const articleResponse = await fetch(`${API_BASE_URL}/api/articles/${article.id}`)
        const articleData = await articleResponse.json()
        setArticle(articleData)
        setHasChanges(true)
        return true
      }
    } catch (error) {
      console.error('Error creating concept:', error)
      alert('Failed to create concept')
    }
    return false
  }, [article, setArticle, setHasChanges])

  return {
    removeTag,
    deleteSnippet,
    saveHighlight,
    saveAnnotation,
    saveTagFromSelection,
    addConceptFromSummary,
  }
}
