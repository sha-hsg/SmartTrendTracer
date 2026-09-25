import { useState, useEffect, useCallback, useRef } from 'react'
import http from '@/services/http'
import type { AnalysisType, GeneratedAnalysis, BatchProgress } from './constants'
import {
  generateMultipleAnalyses as batchGenerateMultiple,
  generateAllAnalyses as batchGenerateAll,
  exportAllAnalysesAsMarkdown as exportMarkdown,
} from './analysisHelpers'


interface UsePaperAnalysisProps {
  paperId: string | number
  paperTitle?: string
  hasContent?: boolean
  selectedModel: string
  onTagCreate?: (tag: string) => void
  onSnippetCreate?: (text: string) => void
}

export function usePaperAnalysis({
  paperId,
  paperTitle,
  hasContent = true,
  selectedModel,
  onTagCreate,
  onSnippetCreate,
}: UsePaperAnalysisProps) {
  const [availableAnalyses, setAvailableAnalyses] = useState<Record<string, AnalysisType[]>>({})
  const [generatedAnalyses, setGeneratedAnalyses] = useState<Record<string, GeneratedAnalysis>>({})
  const [loadingAnalyses, setLoadingAnalyses] = useState<Set<string>>(new Set())
  const [copiedAnalysis, setCopiedAnalysis] = useState<string | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [expandedAnalyses, setExpandedAnalyses] = useState<Set<string>>(new Set())
  const [editingAnalysis, setEditingAnalysis] = useState<string | null>(null)
  const [editedContent, setEditedContent] = useState<Record<string, string>>({})

  // Free-form analysis state
  const [freeAnalyses, setFreeAnalyses] = useState<any[]>([])
  const [currentPrompt, setCurrentPrompt] = useState<string>('')
  const [loadingFreeAnalysis, setLoadingFreeAnalysis] = useState(false)
  const [expandedFreeAnalyses, setExpandedFreeAnalyses] = useState<Set<string>>(new Set())
  const [editingFreeAnalysis, setEditingFreeAnalysis] = useState<string | null>(null)
  const [editedFreeContent, setEditedFreeContent] = useState<Record<string, string>>({})

  // Batch generation progress tracking
  const [batchProgress, setBatchProgress] = useState<BatchProgress>({
    total: 0,
    completed: 0,
    current: null,
    skipped: 0
  })

  // Context menu state
  const [_selectedText, setSelectedText] = useState('')
  const [showContextMenu, setShowContextMenu] = useState(false)
  const [contextMenuPosition, setContextMenuPosition] = useState({ x: 0, y: 0 })
  const [showTagDialog, setShowTagDialog] = useState(false)
  const [tagText, setTagText] = useState('')
  const [creatingTag, setCreatingTag] = useState(false)
  const selectedTextRef = useRef<string>('')

  useEffect(() => {
    loadAvailableAnalyses()
    loadSavedAnalyses()
    loadFreeAnalyses()
  }, [paperId])

  // Listen for paper analysis updates from FacetedPapersDashboard
  useEffect(() => {
    const handlePaperAnalysisUpdated = (event: CustomEvent) => {
      const { paperId: updatedPaperId, analysisType, content } = event.detail
      if (updatedPaperId?.toString() === paperId?.toString()) {
        setGeneratedAnalyses(prev => ({
          ...prev,
          [analysisType]: {
            ...prev[analysisType],
            content,
            success: true,
            generated_at: new Date().toISOString()
          }
        }))
        setEditedContent(prev => {
          if (prev[analysisType] !== undefined) {
            return { ...prev, [analysisType]: content }
          }
          return prev
        })
      }
    }

    window.addEventListener('paperAnalysisUpdated', handlePaperAnalysisUpdated as EventListener)
    return () => {
      window.removeEventListener('paperAnalysisUpdated', handlePaperAnalysisUpdated as EventListener)
    }
  }, [paperId])

  // Handle context menu
  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()

    const selection = window.getSelection()
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      return
    }

    const text = selection.toString().trim()
    setSelectedText(text)
    selectedTextRef.current = text

    const viewportHeight = window.innerHeight
    const menuHeight = 200

    let menuY = e.clientY
    if (e.clientY + menuHeight > viewportHeight) {
      menuY = e.clientY - menuHeight
    }

    setContextMenuPosition({ x: e.clientX, y: menuY })
    setShowContextMenu(true)
  }, [])

  const handleMenuAction = (action: string) => {
    const text = selectedTextRef.current
    if (!text) return

    switch (action) {
      case 'copy':
        navigator.clipboard.writeText(text)
        break
      case 'snippet':
        if (onSnippetCreate) onSnippetCreate(text)
        break
      case 'highlight':
        console.log('Highlight:', text)
        break
      case 'tag':
        setTagText(text.trim())
        setShowTagDialog(true)
        break
    }

    setShowContextMenu(false)
  }

  const handleCreateTag = async () => {
    if (!tagText.trim()) return
    setCreatingTag(true)
    try {
      if (onTagCreate) {
        await onTagCreate(tagText.trim())
      } else {
        await http.post(`/api/papers/${paperId}/tags`, {
          tag: tagText.trim(),
          tag_type: 'manual'
        })
      }
      setShowTagDialog(false)
      setTagText('')
    } catch (error) {
      console.error('Error creating tag:', error)
    } finally {
      setCreatingTag(false)
    }
  }

  const handleTagDialogClose = () => {
    setShowTagDialog(false)
    setTagText('')
    setCreatingTag(false)
  }

  // Close context menu on click outside
  useEffect(() => {
    const handleClickOutside = (_e: MouseEvent) => {
      if (showContextMenu) setShowContextMenu(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showContextMenu])

  const loadAvailableAnalyses = async () => {
    try {
      const response = await http.get(`/api/papers/${paperId}/analyses/available`)
      setAvailableAnalyses(response.data.by_category || {})
      const categories = Object.keys(response.data.by_category || {})
      if (categories.length > 0) {
        setSelectedCategory(categories[0])
      }
    } catch (err) {
      console.error('Failed to load available analyses:', err)
    }
  }

  const loadSavedAnalyses = async () => {
    try {
      const response = await http.get(`/api/papers/${paperId}/analyses/saved`)
      if (response.data.analyses) {
        setGeneratedAnalyses(response.data.analyses)
        const expandedSet = new Set<string>()
        Object.keys(response.data.analyses).forEach(type => {
          if (response.data.analyses[type].success) {
            expandedSet.add(type)
          }
        })
        setExpandedAnalyses(expandedSet)
      }
    } catch (err) {
      console.error('Failed to load saved analyses:', err)
    }
  }

  const generateAnalysis = async (analysisType: string, regenerate: boolean = false) => {
    if (!hasContent) {
      alert('No extracted content available. Please process the PDF with Marker or MinerU first.')
      return
    }
    setLoadingAnalyses(prev => new Set(prev).add(analysisType))

    try {
      const response = await http.post(
        `/api/papers/${paperId}/analyses/generate`,
        { analysis_type: analysisType, regenerate, model: selectedModel }
      )

      if (response.data.success) {
        setGeneratedAnalyses(prev => ({ ...prev, [analysisType]: response.data }))
        setExpandedAnalyses(prev => new Set(prev).add(analysisType))

        if (regenerate) {
          await loadSavedAnalyses()
          window.dispatchEvent(new CustomEvent('paperAnalysisUpdated', {
            detail: { paperId, analysisType, content: response.data.content }
          }))
        }
      } else {
        console.error('Analysis generation failed:', response.data.error)
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || err.message || 'Unknown error'
      console.error('Analysis generation failed:', errorMessage, err)
      alert(`Failed to generate ${analysisType.replace(/_/g, ' ')}: ${errorMessage}`)
      setGeneratedAnalyses(prev => ({
        ...prev,
        [analysisType]: { success: false, error: 'Failed to generate analysis' }
      }))
    } finally {
      setLoadingAnalyses(prev => {
        const newSet = new Set(prev)
        newSet.delete(analysisType)
        return newSet
      })
    }
  }

  const batchDeps = {
    paperId, hasContent, selectedModel, availableAnalyses,
    setBatchProgress, setLoadingAnalyses, setGeneratedAnalyses, setExpandedAnalyses,
  }

  const generateMultipleAnalyses = (category: string) => batchGenerateMultiple(category, batchDeps)
  const generateAllAnalyses = () => batchGenerateAll(batchDeps)

  // Free-form analysis functions
  const loadFreeAnalyses = async () => {
    try {
      const response = await http.get(`/api/papers/${paperId}/analyses/free`)
      if (response.data.analyses) {
        setFreeAnalyses(response.data.analyses)
        setExpandedFreeAnalyses(new Set())
      }
    } catch (err) {
      console.error('Failed to load free analyses:', err)
    }
  }

  const submitFreeAnalysis = async () => {
    if (!currentPrompt.trim()) {
      alert('Please enter a prompt')
      return
    }
    setLoadingFreeAnalysis(true)
    try {
      const response = await http.post(
        `/api/papers/${paperId}/analyses/free`,
        { prompt: currentPrompt, model: selectedModel }
      )
      if (response.data) {
        setFreeAnalyses(prev => [response.data, ...prev])
        setCurrentPrompt('')
        setExpandedFreeAnalyses(prev => new Set([...prev, response.data.id]))
      }
    } catch (err: any) {
      console.error('Failed to generate free analysis:', err)
      alert(`Failed to generate analysis: ${err.response?.data?.detail || err.message}`)
    } finally {
      setLoadingFreeAnalysis(false)
    }
  }

  const deleteFreeAnalysis = async (analysisId: string) => {
    if (!confirm('Are you sure you want to delete this analysis?')) return
    try {
      await http.delete(`/api/papers/${paperId}/analyses/free/${analysisId}`)
      setFreeAnalyses(prev => prev.filter(a => a.id !== analysisId))
    } catch (err) {
      console.error('Failed to delete analysis:', err)
      alert('Failed to delete analysis')
    }
  }

  const saveFreeAnalysisEdit = async (analysisId: string) => {
    const content = editedFreeContent[analysisId]
    if (!content) return
    try {
      await http.put(
        `/api/papers/${paperId}/analyses/free/${analysisId}`,
        { content }
      )
      setFreeAnalyses(prev => prev.map(a => a.id === analysisId ? { ...a, content } : a))
      setEditingFreeAnalysis(null)
      setEditedFreeContent(prev => {
        const updated = { ...prev }
        delete updated[analysisId]
        return updated
      })
    } catch (err) {
      console.error('Failed to save analysis edit:', err)
      alert('Failed to save changes')
    }
  }

  const copyAnalysis = (analysisType: string, content: string) => {
    navigator.clipboard.writeText(content)
    setCopiedAnalysis(analysisType)
    setTimeout(() => setCopiedAnalysis(null), 2000)
  }

  const downloadAnalysis = (analysisType: string, content: string) => {
    const blob = new Blob([content], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${paperTitle || 'paper'}_${analysisType}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const toggleAnalysisExpansion = (analysisType: string) => {
    setExpandedAnalyses(prev => {
      const newSet = new Set(prev)
      if (newSet.has(analysisType)) newSet.delete(analysisType)
      else newSet.add(analysisType)
      return newSet
    })
  }

  const startEditingAnalysis = (analysisType: string, content: string) => {
    setEditingAnalysis(analysisType)
    setEditedContent(prev => ({ ...prev, [analysisType]: content }))
  }

  const cancelEditingAnalysis = (analysisType: string) => {
    setEditingAnalysis(null)
    setEditedContent(prev => {
      const newContent = { ...prev }
      delete newContent[analysisType]
      return newContent
    })
  }

  const saveEditedAnalysis = async (analysisType: string) => {
    const newContent = editedContent[analysisType]
    if (newContent !== undefined) {
      try {
        await http.put(
          `/api/papers/${paperId}/analyses/generated/${analysisType}`,
          { content: newContent }
        )
        setGeneratedAnalyses(prev => ({
          ...prev,
          [analysisType]: { ...prev[analysisType], content: newContent }
        }))
        loadSavedAnalyses()
        window.dispatchEvent(new CustomEvent('paperAnalysisUpdated', {
          detail: { paperId, analysisType, content: newContent }
        }))
      } catch (err) {
        console.error('Failed to save analysis edit:', err)
        alert('Failed to save changes')
      }
    }
    setEditingAnalysis(null)
  }

  const getAllAnalyses = () => {
    const all: AnalysisType[] = []
    Object.values(availableAnalyses).forEach(analyses => {
      all.push(...analyses)
    })
    return all
  }

  const exportAllAnalysesAsMarkdown = () =>
    exportMarkdown({ paperTitle, generatedAnalyses, freeAnalyses, getAllAnalyses })

  return {
    // State
    availableAnalyses, generatedAnalyses, loadingAnalyses, copiedAnalysis,
    selectedCategory, expandedAnalyses, editingAnalysis, editedContent,
    freeAnalyses, currentPrompt, loadingFreeAnalysis,
    expandedFreeAnalyses, editingFreeAnalysis, editedFreeContent,
    batchProgress, showContextMenu, contextMenuPosition,
    showTagDialog, tagText, creatingTag,

    // Setters
    setSelectedCategory, setExpandedAnalyses, setExpandedFreeAnalyses,
    setGeneratedAnalyses, setEditedContent, setCurrentPrompt,
    setEditingFreeAnalysis, setEditedFreeContent, setTagText,

    // Actions
    handleContextMenu, handleMenuAction, handleCreateTag, handleTagDialogClose,
    generateAnalysis, generateMultipleAnalyses, generateAllAnalyses,
    submitFreeAnalysis, deleteFreeAnalysis, saveFreeAnalysisEdit,
    copyAnalysis, downloadAnalysis, toggleAnalysisExpansion,
    startEditingAnalysis, cancelEditingAnalysis, saveEditedAnalysis,
    getAllAnalyses, exportAllAnalysesAsMarkdown,
  }
}
