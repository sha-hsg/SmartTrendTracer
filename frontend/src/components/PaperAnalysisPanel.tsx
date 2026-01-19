import React, { useState, useEffect, useCallback, useRef } from 'react'
import ReactDOM from 'react-dom'
import axios from 'axios'
import {
  FileText,
  Brain,
  Microscope,
  ClipboardList,
  Library,
  Loader2,
  Download,
  Copy,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Minimize2,
  RefreshCw,
  Edit2,
  Save,
  X,
  Highlighter,
  MessageSquare,
  Tag as TagIcon,
  Trash2
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Textarea } from '@/components/ui/textarea'
import { Progress } from '@/components/ui/progress'


import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import ModelSelector from './ModelSelector'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

// Helper function to extract text from LLM response content
// Handles both string format and Gemini's array format [{type: 'text', text: '...'}]
const extractTextContent = (content: unknown): string => {
  if (typeof content === 'string') {
    return content
  }
  if (Array.isArray(content)) {
    return content
      .map(part => {
        if (typeof part === 'string') return part
        if (part && typeof part === 'object' && 'text' in part) return part.text
        return ''
      })
      .join('\n')
  }
  if (content && typeof content === 'object' && 'text' in content) {
    return (content as { text: string }).text
  }
  return String(content || '')
}

// Helper function for relative time display
const getRelativeTime = (date: Date): string => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)
  
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

interface PaperAnalysisPanelProps {
  paperId: number
  paperTitle?: string
  onTagCreate?: (tag: string) => void
  onSnippetCreate?: (text: string) => void
}

interface AnalysisType {
  id: string
  name: string
  description: string
  category: string
}

interface GeneratedAnalysis {
  success: boolean
  content?: string
  error?: string
  analysis_name?: string
  generated_at?: string
  model_used?: string
}

const categoryIcons: Record<string, React.ReactNode> = {
  summaries: <FileText className="h-4 w-4" />,
  analysis: <Microscope className="h-4 w-4" />,
  review: <ClipboardList className="h-4 w-4" />,
  reference: <Library className="h-4 w-4" />
}

const categoryColors: Record<string, string> = {
  summaries: 'bg-blue-50 border-blue-200',
  analysis: 'bg-purple-50 border-purple-200',
  review: 'bg-orange-50 border-orange-200',
  reference: 'bg-green-50 border-green-200'
}

// Specific color schemes for different analysis types - designed for readability and semantic meaning
const analysisTypeColors: Record<string, { bg: string; border: string; header: string }> = {
  // Match the actual API IDs
  // SAS analyses - Blue/Indigo tones
  sas_summary: {
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
    header: 'bg-indigo-100'
  },
  sas_review: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    header: 'bg-blue-100'
  },
  
  // SWITT Analysis - Violet (strategic, analytical)
  switt: {
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    header: 'bg-violet-100'
  },
  
  // Summary - Sky blue (calm, accessible)
  summary: {
    bg: 'bg-sky-50',
    border: 'border-sky-200',
    header: 'bg-sky-100'
  },
  
  // Key Findings - Emerald (discovery, insights)
  key_findings: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    header: 'bg-emerald-100'
  },
  
  // Methodology - Rose (critical analysis)
  methodology: {
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    header: 'bg-rose-100'
  },
  
  // Evaluation - Red tones (critical)
  evaluation: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    header: 'bg-red-100'
  },
  
  // Limitations - Pink (constructive criticism)
  limitations: {
    bg: 'bg-pink-50',
    border: 'border-pink-200',
    header: 'bg-pink-100'
  },
  
  // Glossary - Teal (reference, comprehensive)
  glossary: {
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    header: 'bg-teal-100'
  },
  
  // Additional summaries from prompts_config
  layman_summary: {
    bg: 'bg-sky-50',
    border: 'border-sky-200',
    header: 'bg-sky-100'
  },
  mollick_summary: {
    bg: 'bg-purple-50',    // Purple for Mollick's thoughtful, educator perspective
    border: 'border-purple-200',
    header: 'bg-purple-100'
  },
  pareto_summary: {
    bg: 'bg-lime-50',      // Lime green for efficiency and the 80/20 principle
    border: 'border-lime-200',
    header: 'bg-lime-100'
  },
  
  // Analysis types
  switt_analysis: {
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    header: 'bg-violet-100'
  },
  
  // Review type - Academic Review
  review: {
    bg: 'bg-orange-50',    // Orange for comprehensive academic review
    border: 'border-orange-200',
    header: 'bg-orange-100'
  },
  
  // Default fallback
  default: {
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    header: 'bg-gray-100'
  }
}

export default function PaperAnalysisPanel({ paperId, paperTitle, onTagCreate, onSnippetCreate }: PaperAnalysisPanelProps) {
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

  // Model selection - managed by ModelSelector component with localStorage persistence
  const [selectedModel, setSelectedModel] = useState<string>('')

  // Batch generation progress tracking
  const [batchProgress, setBatchProgress] = useState<{
    total: number
    completed: number
    current: string | null
    skipped: number
  }>({
    total: 0,
    completed: 0,
    current: null,
    skipped: 0
  })

  // Context menu state
  const [selectedText, setSelectedText] = useState('')
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
      
      // Only update if it's for the same paper
      if (updatedPaperId?.toString() === paperId?.toString()) {
        // Update the generated analyses state
        setGeneratedAnalyses(prev => ({
          ...prev,
          [analysisType]: {
            ...prev[analysisType],
            content,
            success: true,
            generated_at: new Date().toISOString()
          }
        }))
        
        // If user is currently editing this analysis, update the edited content too
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
    
    // Get current selection
    const selection = window.getSelection()
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      return
    }
    
    const text = selection.toString().trim()
    setSelectedText(text)
    selectedTextRef.current = text
    
    // Set context menu position
    const viewportHeight = window.innerHeight
    const menuHeight = 200 // Approximate menu height
    
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
        if (onSnippetCreate) {
          onSnippetCreate(text)
        }
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
        // Fallback to direct API call if no callback provided
        await axios.post(`http://localhost:8000/api/papers/${paperId}/tags`, {
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
    const handleClickOutside = (e: MouseEvent) => {
      if (showContextMenu) {
        setShowContextMenu(false)
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showContextMenu])

  const loadAvailableAnalyses = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/papers/${paperId}/analyses/available`)
      setAvailableAnalyses(response.data.by_category || {})
      
      // Set default category to the first one with analyses
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
      const response = await axios.get(`http://localhost:8000/api/papers/${paperId}/analyses/saved`)
      if (response.data.analyses) {
        setGeneratedAnalyses(response.data.analyses)
        // Expand analyses that have been generated
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
    setLoadingAnalyses(prev => new Set(prev).add(analysisType))

    try {
      const response = await axios.post(
        `http://localhost:8000/api/papers/${paperId}/analyses/generate`,
        {
          analysis_type: analysisType,
          regenerate: regenerate,  // Pass regenerate flag to backend
          model: selectedModel  // Pass selected model to backend
        }
      )
      
      if (response.data.success) {
        setGeneratedAnalyses(prev => ({
          ...prev,
          [analysisType]: response.data
        }))
        setExpandedAnalyses(prev => new Set(prev).add(analysisType))
        
        // If regenerating, also reload saved analyses to get the updated content
        if (regenerate) {
          await loadSavedAnalyses()
          
          // Emit event for paper tile update
          window.dispatchEvent(new CustomEvent('paperAnalysisUpdated', {
            detail: {
              paperId,
              analysisType,
              content: response.data.content
            }
          }))
        }
      } else {
        console.error('Analysis generation failed:', response.data.error)
      }
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || err.response?.data?.error || err.message || 'Unknown error'
      console.error('Analysis generation failed:', errorMessage, err)
      
      // Show user-friendly error message
      alert(`Failed to generate ${analysisType.replace(/_/g, ' ')}: ${errorMessage}`)
      
      setGeneratedAnalyses(prev => ({
        ...prev,
        [analysisType]: {
          success: false,
          error: 'Failed to generate analysis'
        }
      }))
    } finally {
      setLoadingAnalyses(prev => {
        const newSet = new Set(prev)
        newSet.delete(analysisType)
        return newSet
      })
    }
  }

  const generateMultipleAnalyses = async (category: string) => {
    const analyses = availableAnalyses[category] || []
    const analysisTypes = analyses.map(a => a.id)

    if (analysisTypes.length === 0) {
      console.warn('No analyses in category to generate')
      return
    }

    // Initialize progress tracking
    setBatchProgress({
      total: analysisTypes.length,
      completed: 0,
      current: null,
      skipped: 0
    })

    // Set all as loading
    setLoadingAnalyses(new Set(analysisTypes))

    try {
      const newAnalyses: Record<string, GeneratedAnalysis> = {}
      const toExpand = new Set<string>()
      let skippedCount = 0

      // Process each analysis sequentially
      for (let i = 0; i < analysisTypes.length; i++) {
        const analysisType = analysisTypes[i]
        const analysisName = analyses[i].name

        // Update progress - show current analysis
        setBatchProgress(prev => ({
          ...prev,
          current: analysisName,
          completed: i
        }))

        try {
          // Generate single analysis
          const response = await axios.post(
            `http://localhost:8000/api/papers/${paperId}/analyses/generate`,
            {
              analysis_type: analysisType,
              regenerate: false,  // Don't regenerate if exists
              model: selectedModel
            }
          )

          if (response.data.success) {
            newAnalyses[analysisType] = response.data as GeneratedAnalysis
            toExpand.add(analysisType)

            // Check if this was skipped (already existed)
            if (response.data.was_skipped) {
              skippedCount++
            }

            // Update state immediately after each completion
            setGeneratedAnalyses(prev => ({ ...prev, [analysisType]: response.data as GeneratedAnalysis }))
          }
        } catch (err) {
          console.error(`Failed to generate ${analysisType}:`, err)
          newAnalyses[analysisType] = {
            success: false,
            error: `Failed to generate: ${err}`
          }
        }

        // Update progress after completion
        setBatchProgress(prev => ({
          ...prev,
          completed: i + 1,
          skipped: skippedCount
        }))
      }

      // Expand all successfully generated analyses
      setExpandedAnalyses(prev => new Set([...prev, ...toExpand]))

      // Show completion message
      const generatedCount = analysisTypes.length - skippedCount
      console.log(`Batch generation complete: ${generatedCount} generated, ${skippedCount} already existed`)

      // Show alert with completion summary
      const completionMsg = generatedCount > 0
        ? `✓ Generated ${generatedCount} ${generatedCount === 1 ? 'analysis' : 'analyses'}` +
          (skippedCount > 0 ? `, ${skippedCount} already existed` : '')
        : `All ${skippedCount} analyses already existed - no generation needed`

      alert(completionMsg)

    } catch (err) {
      console.error('Failed to generate multiple analyses:', err)
      alert('Failed to generate analyses. Check console for details.')
    } finally {
      setLoadingAnalyses(new Set())
      // Reset progress after a brief delay to show completion
      setTimeout(() => {
        setBatchProgress({
          total: 0,
          completed: 0,
          current: null,
          skipped: 0
        })
      }, 2000)
    }
  }

  const generateAllAnalyses = async () => {
    // Collect ALL analysis types from all categories with their names
    const allAnalyses: { id: string; name: string }[] = []

    for (const category in availableAnalyses) {
      const analyses = availableAnalyses[category] || []
      allAnalyses.push(...analyses.map(a => ({ id: a.id, name: a.name })))
    }

    if (allAnalyses.length === 0) {
      console.warn('No analyses available to generate')
      return
    }

    // Initialize progress tracking (like generateMultipleAnalyses)
    setBatchProgress({
      total: allAnalyses.length,
      completed: 0,
      current: null,
      skipped: 0
    })

    setLoadingAnalyses(new Set(allAnalyses.map(a => a.id)))

    try {
      const toExpand = new Set<string>()
      let skippedCount = 0

      // Sequential processing with progress updates
      for (let i = 0; i < allAnalyses.length; i++) {
        const { id: analysisType, name: analysisName } = allAnalyses[i]

        setBatchProgress(prev => ({
          ...prev,
          current: analysisName,
          completed: i
        }))

        try {
          const response = await axios.post(
            `http://localhost:8000/api/papers/${paperId}/analyses/generate`,
            { analysis_type: analysisType, regenerate: false, model: selectedModel }
          )

          if (response.data.success) {
            setGeneratedAnalyses(prev => ({ ...prev, [analysisType]: response.data }))
            toExpand.add(analysisType)
            if (response.data.was_skipped) skippedCount++
          }
        } catch (err) {
          console.error(`Failed to generate ${analysisType}:`, err)
        }

        setBatchProgress(prev => ({
          ...prev,
          completed: i + 1,
          skipped: skippedCount
        }))
      }

      setExpandedAnalyses(prev => new Set([...prev, ...toExpand]))

      const generatedCount = allAnalyses.length - skippedCount
      alert(generatedCount > 0
        ? `Generated ${generatedCount} analyses` + (skippedCount > 0 ? `, ${skippedCount} already existed` : '')
        : `All ${skippedCount} analyses already existed`)

    } catch (err) {
      console.error('Failed to generate all analyses:', err)
      alert('Failed to generate analyses.')
    } finally {
      setLoadingAnalyses(new Set())
      setTimeout(() => setBatchProgress({ total: 0, completed: 0, current: null, skipped: 0 }), 2000)
    }
  }

  // Free-form analysis functions
  const loadFreeAnalyses = async () => {
    try {
      const response = await axios.get(`http://localhost:8000/api/papers/${paperId}/analyses/free`)
      if (response.data.analyses) {
        setFreeAnalyses(response.data.analyses)
        // Start with all free analyses collapsed by default
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
      const response = await axios.post(
        `http://localhost:8000/api/papers/${paperId}/analyses/free`,
        {
          prompt: currentPrompt,
          model: selectedModel  // Pass selected model to backend
        }
      )
      
      if (response.data) {
        // Add the new analysis to the list
        setFreeAnalyses(prev => [response.data, ...prev])
        setCurrentPrompt('')
        // Expand only the new analysis
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
    if (!confirm('Are you sure you want to delete this analysis?')) {
      return
    }

    try {
      await axios.delete(`http://localhost:8000/api/papers/${paperId}/analyses/free/${analysisId}`)
      // Remove from local state
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
      await axios.put(
        `http://localhost:8000/api/papers/${paperId}/analyses/free/${analysisId}`,
        { content }
      )
      
      // Update local state
      setFreeAnalyses(prev => prev.map(a => 
        a.id === analysisId ? { ...a, content } : a
      ))
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
      if (newSet.has(analysisType)) {
        newSet.delete(analysisType)
      } else {
        newSet.add(analysisType)
      }
      return newSet
    })
  }

  const startEditingAnalysis = (analysisType: string, content: string) => {
    setEditingAnalysis(analysisType)
    setEditedContent(prev => ({
      ...prev,
      [analysisType]: content
    }))
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
        // Save to backend
        await axios.put(
          `http://localhost:8000/api/papers/${paperId}/analyses/generated/${analysisType}`,
          { content: newContent }
        )
        
        // Update local state
        setGeneratedAnalyses(prev => ({
          ...prev,
          [analysisType]: {
            ...prev[analysisType],
            content: newContent
          }
        }))
        
        // Reload saved analyses to get the updated timestamp
        loadSavedAnalyses()
        
        // Emit event for paper tile update
        window.dispatchEvent(new CustomEvent('paperAnalysisUpdated', {
          detail: {
            paperId,
            analysisType,
            content: newContent
          }
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

  const getAnalysesToDisplay = () => {
    if (selectedCategory === 'all') {
      return getAllAnalyses()
    }
    if (selectedCategory === 'free') {
      return [] // Free analyses are handled in their own tab content
    }
    return availableAnalyses[selectedCategory] || []
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between mb-4">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              Paper Analyses
            </CardTitle>
            <CardDescription className="mt-1">
              Generate various types of summaries and analyses
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            {/* Collapse All Button */}
            {(expandedAnalyses.size > 0 || expandedFreeAnalyses.size > 0) && (
              <Button
                size="sm"
                variant="outline"
                onClick={() => {
                  setExpandedAnalyses(new Set())
                  setExpandedFreeAnalyses(new Set())
                }}
                title="Collapse all analyses"
              >
                <Minimize2 className="h-4 w-4 mr-1" />
                Collapse All
              </Button>
            )}
            {selectedCategory === 'all' ? (
            <div className="flex flex-col gap-2">
              <Button
                size="sm"
                onClick={() => generateAllAnalyses()}
                disabled={loadingAnalyses.size > 0}
                variant="default"
              >
                {loadingAnalyses.size > 0 ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Generating All...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-1" />
                    Generate All Analyses
                  </>
                )}
              </Button>

              {/* Progress indicator for "All" batch generation */}
              {batchProgress.total > 0 && (
                <div className="min-w-[250px] space-y-1">
                  <div className="flex items-center justify-between text-xs text-gray-600">
                    <span>
                      {batchProgress.completed} of {batchProgress.total} completed
                      {batchProgress.skipped > 0 && ` (${batchProgress.skipped} skipped)`}
                    </span>
                    <span>{Math.round((batchProgress.completed / batchProgress.total) * 100)}%</span>
                  </div>
                  <Progress value={(batchProgress.completed / batchProgress.total) * 100} className="h-2" />
                  {batchProgress.current && (
                    <p className="text-xs text-blue-600 font-medium">
                      Generating: {batchProgress.current}
                    </p>
                  )}
                </div>
              )}
            </div>
          ) : (
            availableAnalyses[selectedCategory] && (
              <div className="flex flex-col gap-2">
                <Button
                  size="sm"
                  onClick={() => generateMultipleAnalyses(selectedCategory)}
                  disabled={loadingAnalyses.size > 0}
                >
                  {loadingAnalyses.size > 0 ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-1" />
                      Generate All in Category
                    </>
                  )}
                </Button>

                {/* Progress indicator for batch generation */}
                {batchProgress.total > 0 && (
                  <div className="min-w-[250px] space-y-1">
                    <div className="flex items-center justify-between text-xs text-gray-600">
                      <span>
                        {batchProgress.completed} of {batchProgress.total} completed
                        {batchProgress.skipped > 0 && ` (${batchProgress.skipped} skipped)`}
                      </span>
                      <span>{Math.round((batchProgress.completed / batchProgress.total) * 100)}%</span>
                    </div>
                    <Progress value={(batchProgress.completed / batchProgress.total) * 100} className="h-2" />
                    {batchProgress.current && (
                      <p className="text-xs text-blue-600 font-medium">
                        Generating: {batchProgress.current}
                      </p>
                    )}
                  </div>
                )}
              </div>
            )
          )}
          </div>
        </div>

        {/* Model Selection */}
        <ModelSelector
          value={selectedModel}
          onValueChange={setSelectedModel}
          task="paperAnalysis"
          label="AI Model for Analysis"
          persist={true}
        />
      </CardHeader>
      
      <CardContent>
        {/* Category Tabs */}
        <Tabs value={selectedCategory} onValueChange={setSelectedCategory} className="w-full">
          <TabsList className="grid w-full" style={{ gridTemplateColumns: `repeat(${Object.keys(availableAnalyses).length + 2}, 1fr)` }}>
            <TabsTrigger value="all">All</TabsTrigger>
            {Object.keys(availableAnalyses).map(category => (
              <TabsTrigger key={category} value={category} className="capitalize">
                {category}
              </TabsTrigger>
            ))}
            <TabsTrigger value="free" className="font-semibold text-purple-600">
              Free 🚀
            </TabsTrigger>
          </TabsList>

          {/* All Tab */}
          <TabsContent value="all" className="mt-4">
            <ScrollArea className="h-[600px] pr-4">
              <div className="space-y-3">
                {getAllAnalyses().map(analysis => {
                  const isLoading = loadingAnalyses.has(analysis.id)
                  const isGenerated = !!generatedAnalyses[analysis.id]
                  const isExpanded = expandedAnalyses.has(analysis.id)
                  const result = generatedAnalyses[analysis.id]
                  
                  // Get specific colors for this analysis type, or fall back to category colors
                  const typeColors = analysisTypeColors[analysis.id] || analysisTypeColors.default
                  const shouldUseColors = isGenerated && result?.success
                  
                  return (
                    <Card 
                      key={analysis.id} 
                      className={`transition-all duration-200 ${
                        shouldUseColors ? `${typeColors.bg} ${typeColors.border}` : ''
                      } ${!isExpanded && isGenerated ? 'hover:shadow-md' : ''}`}
                    >
                      <CardHeader className={`pb-3 ${shouldUseColors ? typeColors.header : ''}`}>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              {categoryIcons[analysis.category]}
                              <h3 className="font-semibold">{analysis.name}</h3>
                              <Badge variant="outline" className="text-xs">
                                {analysis.category}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                              {analysis.description}
                            </p>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            {isGenerated && result?.success && (
                              <>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => toggleAnalysisExpansion(analysis.id)}
                                >
                                  {isExpanded ? (
                                    <ChevronDown className="h-4 w-4" />
                                  ) : (
                                    <ChevronRight className="h-4 w-4" />
                                  )}
                                </Button>
                                {editingAnalysis === analysis.id ? (
                                  <>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => saveEditedAnalysis(analysis.id)}
                                      title="Save"
                                    >
                                      <Save className="h-4 w-4 text-green-600" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => cancelEditingAnalysis(analysis.id)}
                                      title="Cancel"
                                    >
                                      <X className="h-4 w-4 text-red-600" />
                                    </Button>
                                  </>
                                ) : (
                                  <>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => startEditingAnalysis(analysis.id, result.content || '')}
                                      title="Edit"
                                    >
                                      <Edit2 className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => copyAnalysis(analysis.id, result.content || '')}
                                    >
                                      {copiedAnalysis === analysis.id ? (
                                        <CheckCircle className="h-4 w-4 text-green-600" />
                                      ) : (
                                        <Copy className="h-4 w-4" />
                                      )}
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => downloadAnalysis(analysis.id, result.content || '')}
                                    >
                                      <Download className="h-4 w-4" />
                                    </Button>
                                  </>
                                )}
                              </>
                            )}
                            
                            {!isGenerated && (
                              <Button
                                size="sm"
                                onClick={() => generateAnalysis(analysis.id)}
                                disabled={isLoading}
                              >
                                {isLoading ? (
                                  <>
                                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                                    Generating...
                                  </>
                                ) : (
                                  <>
                                    <Sparkles className="h-4 w-4 mr-1" />
                                    Generate
                                  </>
                                )}
                              </Button>
                            )}
                            
                            {isGenerated && result?.success && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => generateAnalysis(analysis.id, true)}
                                disabled={isLoading}
                                title="Regenerate"
                              >
                                <RefreshCw className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </div>
                        
                        {isGenerated && result?.generated_at && (
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span>Generated: {new Date(result.generated_at).toLocaleString()}</span>
                            {result.model_used && (
                              <span>Model: {result.model_used}</span>
                            )}
                          </div>
                        )}
                      </CardHeader>
                      
                      {isGenerated && result && isExpanded && (
                        <CardContent>
                          <Separator className="mb-4" />
                          {result.success ? (
                            editingAnalysis === analysis.id ? (
                              <div className="space-y-4">
                                <Textarea
                                  value={editedContent[analysis.id] || result.content || ''}
                                  onChange={(e) => setEditedContent(prev => ({
                                    ...prev,
                                    [analysis.id]: e.target.value
                                  }))}
                                  className="min-h-[400px] font-mono text-sm"
                                  placeholder="Enter markdown content..."
                                />
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                  <span>💡 Tip: You can use Markdown formatting</span>
                                </div>
                              </div>
                            ) : (
                              <div 
                                className={`markdown-content rounded-lg p-6 ${
                                  typeColors.bg.replace('50', '50/30')
                                } border ${typeColors.border}`}
                                onContextMenu={handleContextMenu}
                                style={{
                                  backgroundColor: `rgba(${
                                    typeColors.bg.includes('violet') ? '245, 243, 255' :
                                    typeColors.bg.includes('purple') ? '250, 245, 255' :
                                    typeColors.bg.includes('fuchsia') ? '253, 244, 255' :
                                    typeColors.bg.includes('pink') ? '253, 242, 248' :
                                    typeColors.bg.includes('sky') ? '240, 249, 255' :
                                    typeColors.bg.includes('blue') ? '239, 246, 255' :
                                    typeColors.bg.includes('indigo') ? '238, 242, 255' :
                                    typeColors.bg.includes('cyan') ? '236, 254, 255' :
                                    typeColors.bg.includes('orange') ? '255, 247, 237' :
                                    typeColors.bg.includes('amber') ? '254, 251, 235' :
                                    typeColors.bg.includes('yellow') ? '254, 252, 232' :
                                    typeColors.bg.includes('emerald') ? '236, 253, 245' :
                                    typeColors.bg.includes('green') ? '240, 253, 244' :
                                    typeColors.bg.includes('teal') ? '240, 253, 250' :
                                    '249, 250, 251'
                                  }, 0.3)`
                                }}
                              >
                                <style>{`
                                  .markdown-content h1 { 
                                    font-size: 1.875rem; 
                                    font-weight: 700; 
                                    margin-top: 1.5rem; 
                                    margin-bottom: 1rem; 
                                    color: rgb(15 23 42);
                                    border-bottom: 2px solid rgba(0, 0, 0, 0.15);
                                    padding-bottom: 0.5rem;
                                  }
                                  .markdown-content h2 { 
                                    font-size: 1.5rem; 
                                    font-weight: 700; 
                                    margin-top: 1.25rem; 
                                    margin-bottom: 0.75rem; 
                                    color: rgb(15 23 42);
                                  }
                                  .markdown-content h3 { 
                                    font-size: 1.25rem; 
                                    font-weight: 600; 
                                    margin-top: 1rem; 
                                    margin-bottom: 0.5rem; 
                                    color: rgb(30 41 59);
                                  }
                                  .markdown-content h4 { 
                                    font-size: 1.125rem; 
                                    font-weight: 600; 
                                    margin-top: 0.75rem; 
                                    margin-bottom: 0.5rem; 
                                    color: rgb(30 41 59);
                                  }
                                  .markdown-content p { 
                                    margin-bottom: 1rem; 
                                    color: rgb(30 41 59); 
                                    line-height: 1.8;
                                    font-size: 1rem;
                                  }
                                  .markdown-content ul { 
                                    list-style-type: disc; 
                                    margin-bottom: 1rem; 
                                    padding-left: 1.5rem;
                                  }
                                  .markdown-content ol { 
                                    list-style-type: decimal; 
                                    margin-bottom: 1rem; 
                                    padding-left: 1.5rem;
                                  }
                                  .markdown-content li { 
                                    margin-bottom: 0.375rem; 
                                    color: rgb(30 41 59);
                                    line-height: 1.7;
                                  }
                                  .markdown-content ul ul, .markdown-content ol ul { 
                                    margin-top: 0.25rem;
                                    margin-bottom: 0.25rem;
                                    padding-left: 1.5rem;
                                  }
                                  .markdown-content ul ol, .markdown-content ol ol { 
                                    margin-top: 0.25rem;
                                    margin-bottom: 0.25rem;
                                    padding-left: 1.5rem;
                                  }
                                  .markdown-content strong { 
                                    font-weight: 700; 
                                    color: rgb(15 23 42);
                                  }
                                  .markdown-content em { 
                                    font-style: italic;
                                  }
                                  .markdown-content code { 
                                    background-color: rgba(255, 255, 255, 0.8); 
                                    color: rgb(220 38 38); 
                                    padding: 0.125rem 0.375rem; 
                                    border-radius: 0.25rem; 
                                    font-family: 'Courier New', monospace;
                                    font-size: 0.9rem;
                                    font-weight: 500;
                                  }
                                  .markdown-content pre { 
                                    background-color: rgba(255, 255, 255, 0.9); 
                                    padding: 1rem; 
                                    border-radius: 0.5rem; 
                                    overflow-x: auto; 
                                    margin-bottom: 1rem;
                                    border: 1px solid rgba(0, 0, 0, 0.1);
                                  }
                                  .markdown-content pre code { 
                                    background-color: transparent; 
                                    color: rgb(30 41 59); 
                                    padding: 0;
                                    font-size: 0.875rem;
                                  }
                                  .markdown-content blockquote { 
                                    border-left: 4px solid currentColor;
                                    opacity: 0.85;
                                    padding: 0.75rem 1rem; 
                                    margin-bottom: 1rem; 
                                    font-style: italic; 
                                    color: rgb(51 65 85);
                                    background-color: rgba(255, 255, 255, 0.3);
                                    border-radius: 0.25rem;
                                  }
                                  .markdown-content a { 
                                    color: rgb(29 78 216); 
                                    text-decoration: underline;
                                    font-weight: 500;
                                  }
                                  .markdown-content a:hover { 
                                    color: rgb(30 58 138);
                                    text-decoration-thickness: 2px;
                                  }
                                  .markdown-content hr { 
                                    margin: 1.5rem 0; 
                                    border-color: rgba(0, 0, 0, 0.1);
                                    border-style: solid;
                                  }
                                  .markdown-content table { 
                                    width: 100%; 
                                    border-collapse: collapse; 
                                    margin-bottom: 1rem;
                                    background-color: rgba(255, 255, 255, 0.7);
                                  }
                                  .markdown-content th { 
                                    border: 1px solid rgba(0, 0, 0, 0.1); 
                                    padding: 0.75rem; 
                                    background-color: rgba(255, 255, 255, 0.9); 
                                    font-weight: 600;
                                    text-align: left;
                                    color: rgb(15 23 42);
                                  }
                                  .markdown-content td { 
                                    border: 1px solid rgba(0, 0, 0, 0.1); 
                                    padding: 0.75rem;
                                    color: rgb(30 41 59);
                                  }
                                `}</style>
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {extractTextContent(result.content)}
                                </ReactMarkdown>
                              </div>
                            )
                          ) : (
                            <Alert>
                              <AlertDescription>
                                {result.error || 'Failed to generate analysis'}
                              </AlertDescription>
                            </Alert>
                          )}
                        </CardContent>
                      )}
                    </Card>
                  )
                })}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Category-specific Tabs */}
          {Object.keys(availableAnalyses).map(category => (
            <TabsContent key={category} value={category} className="mt-4">
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-3">
                  {(availableAnalyses[category] || []).map(analysis => {
                  const isLoading = loadingAnalyses.has(analysis.id)
                  const isGenerated = !!generatedAnalyses[analysis.id]
                  const isExpanded = expandedAnalyses.has(analysis.id)
                  const result = generatedAnalyses[analysis.id]

                  // Get specific colors for this analysis type, or fall back to category colors
                  const typeColors = analysisTypeColors[analysis.id] || analysisTypeColors.default
                  const shouldUseColors = isGenerated && result?.success

                  return (
                    <Card
                      key={analysis.id}
                      className={`transition-all duration-200 ${
                        shouldUseColors ? `${typeColors.bg} ${typeColors.border}` : ''
                      } ${!isExpanded && isGenerated ? 'hover:shadow-md' : ''}`}
                    >
                      <CardHeader className={`pb-3 ${shouldUseColors ? typeColors.header : ''}`}>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              {categoryIcons[analysis.category]}
                              <h3 className="font-semibold">{analysis.name}</h3>
                              <Badge variant="outline" className="text-xs">
                                {analysis.category}
                              </Badge>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                              {analysis.description}
                            </p>
                          </div>

                          <div className="flex items-center gap-2">
                            {isGenerated && result?.success && (
                              <>
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  onClick={() => toggleAnalysisExpansion(analysis.id)}
                                >
                                  {isExpanded ? (
                                    <ChevronDown className="h-4 w-4" />
                                  ) : (
                                    <ChevronRight className="h-4 w-4" />
                                  )}
                                </Button>
                                {editingAnalysis === analysis.id ? (
                                  <>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => saveEditedAnalysis(analysis.id)}
                                      title="Save"
                                    >
                                      <Save className="h-4 w-4 text-green-600" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => cancelEditingAnalysis(analysis.id)}
                                      title="Cancel"
                                    >
                                      <X className="h-4 w-4 text-red-600" />
                                    </Button>
                                  </>
                                ) : (
                                  <>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => startEditingAnalysis(analysis.id, result.content || '')}
                                      title="Edit"
                                    >
                                      <Edit2 className="h-4 w-4" />
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => copyAnalysis(analysis.id, result.content || '')}
                                    >
                                      {copiedAnalysis === analysis.id ? (
                                        <CheckCircle className="h-4 w-4 text-green-600" />
                                      ) : (
                                        <Copy className="h-4 w-4" />
                                      )}
                                    </Button>
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => downloadAnalysis(analysis.id, result.content || '')}
                                    >
                                      <Download className="h-4 w-4" />
                                    </Button>
                                  </>
                                )}
                              </>
                            )}

                            {!isGenerated && (
                              <Button
                                size="sm"
                                onClick={() => generateAnalysis(analysis.id)}
                                disabled={isLoading}
                              >
                                {isLoading ? (
                                  <>
                                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                                    Generating...
                                  </>
                                ) : (
                                  <>
                                    <Sparkles className="h-4 w-4 mr-1" />
                                    Generate
                                  </>
                                )}
                              </Button>
                            )}

                            {isGenerated && result?.success && (
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => generateAnalysis(analysis.id, true)}
                                disabled={isLoading}
                                title="Regenerate"
                              >
                                <RefreshCw className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </div>

                        {isGenerated && result?.generated_at && (
                          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                            <span>Generated: {new Date(result.generated_at).toLocaleString()}</span>
                            {result.model_used && (
                              <span>Model: {result.model_used}</span>
                            )}
                          </div>
                        )}
                      </CardHeader>

                      {isGenerated && result && isExpanded && (
                        <CardContent>
                          <Separator className="mb-4" />
                          {result.success ? (
                            editingAnalysis === analysis.id ? (
                              <div className="space-y-4">
                                <Textarea
                                  value={editedContent[analysis.id] || result.content || ''}
                                  onChange={(e) => setEditedContent(prev => ({
                                    ...prev,
                                    [analysis.id]: e.target.value
                                  }))}
                                  className="min-h-[400px] font-mono text-sm"
                                  placeholder="Enter markdown content..."
                                />
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                  <span>💡 Tip: You can use Markdown formatting</span>
                                </div>
                              </div>
                            ) : (
                              <div
                                className={`markdown-content rounded-lg p-6 ${
                                  typeColors.bg.replace('50', '50/30')
                                } border ${typeColors.border}`}
                                onContextMenu={handleContextMenu}
                                style={{
                                  backgroundColor: `rgba(${
                                    typeColors.bg.includes('violet') ? '245, 243, 255' :
                                    typeColors.bg.includes('purple') ? '250, 245, 255' :
                                    typeColors.bg.includes('fuchsia') ? '253, 244, 255' :
                                    typeColors.bg.includes('pink') ? '253, 242, 248' :
                                    typeColors.bg.includes('sky') ? '240, 249, 255' :
                                    typeColors.bg.includes('blue') ? '239, 246, 255' :
                                    typeColors.bg.includes('indigo') ? '238, 242, 255' :
                                    typeColors.bg.includes('cyan') ? '236, 254, 255' :
                                    typeColors.bg.includes('orange') ? '255, 247, 237' :
                                    typeColors.bg.includes('amber') ? '254, 251, 235' :
                                    typeColors.bg.includes('yellow') ? '254, 252, 232' :
                                    typeColors.bg.includes('emerald') ? '236, 253, 245' :
                                    typeColors.bg.includes('green') ? '240, 253, 244' :
                                    typeColors.bg.includes('teal') ? '240, 253, 250' :
                                    '249, 250, 251'
                                  }, 0.3)`
                                }}
                              >
                                <style>{`
                                  .markdown-content h1 {
                                    font-size: 1.875rem;
                                    font-weight: 700;
                                    margin-top: 1.5rem;
                                    margin-bottom: 1rem;
                                    color: rgb(15 23 42);
                                    border-bottom: 2px solid rgba(0, 0, 0, 0.15);
                                    padding-bottom: 0.5rem;
                                  }
                                  .markdown-content h2 {
                                    font-size: 1.5rem;
                                    font-weight: 700;
                                    margin-top: 1.25rem;
                                    margin-bottom: 0.75rem;
                                    color: rgb(15 23 42);
                                  }
                                  .markdown-content h3 {
                                    font-size: 1.25rem;
                                    font-weight: 600;
                                    margin-top: 1rem;
                                    margin-bottom: 0.5rem;
                                    color: rgb(30 41 59);
                                  }
                                  .markdown-content h4 {
                                    font-size: 1.125rem;
                                    font-weight: 600;
                                    margin-top: 0.75rem;
                                    margin-bottom: 0.5rem;
                                    color: rgb(30 41 59);
                                  }
                                  .markdown-content p {
                                    margin-bottom: 1rem;
                                    color: rgb(30 41 59);
                                    line-height: 1.8;
                                    font-size: 1rem;
                                  }
                                  .markdown-content ul {
                                    list-style-type: disc;
                                    margin-bottom: 1rem;
                                    padding-left: 1.5rem;
                                  }
                                  .markdown-content ol {
                                    list-style-type: decimal;
                                    margin-bottom: 1rem;
                                    padding-left: 1.5rem;
                                  }
                                  .markdown-content li {
                                    margin-bottom: 0.375rem;
                                    color: rgb(30 41 59);
                                    line-height: 1.7;
                                  }
                                  .markdown-content ul ul, .markdown-content ol ul {
                                    margin-top: 0.25rem;
                                    margin-bottom: 0.25rem;
                                    padding-left: 1.5rem;
                                  }
                                  .markdown-content ul ol, .markdown-content ol ol {
                                    margin-top: 0.25rem;
                                    margin-bottom: 0.25rem;
                                    padding-left: 1.5rem;
                                  }
                                  .markdown-content strong {
                                    font-weight: 700;
                                    color: rgb(15 23 42);
                                  }
                                  .markdown-content em {
                                    font-style: italic;
                                  }
                                  .markdown-content code {
                                    background-color: rgba(255, 255, 255, 0.8);
                                    color: rgb(220 38 38);
                                    padding: 0.125rem 0.375rem;
                                    border-radius: 0.25rem;
                                    font-family: 'Courier New', monospace;
                                    font-size: 0.9rem;
                                    font-weight: 500;
                                  }
                                  .markdown-content pre {
                                    background-color: rgba(255, 255, 255, 0.9);
                                    padding: 1rem;
                                    border-radius: 0.5rem;
                                    overflow-x: auto;
                                    margin-bottom: 1rem;
                                    border: 1px solid rgba(0, 0, 0, 0.1);
                                  }
                                  .markdown-content pre code {
                                    background-color: transparent;
                                    color: rgb(30 41 59);
                                    padding: 0;
                                    font-size: 0.875rem;
                                  }
                                  .markdown-content blockquote {
                                    border-left: 4px solid currentColor;
                                    opacity: 0.85;
                                    padding: 0.75rem 1rem;
                                    margin-bottom: 1rem;
                                    font-style: italic;
                                    color: rgb(51 65 85);
                                    background-color: rgba(255, 255, 255, 0.3);
                                    border-radius: 0.25rem;
                                  }
                                  .markdown-content a {
                                    color: rgb(29 78 216);
                                    text-decoration: underline;
                                    font-weight: 500;
                                  }
                                  .markdown-content a:hover {
                                    color: rgb(30 58 138);
                                    text-decoration-thickness: 2px;
                                  }
                                  .markdown-content hr {
                                    margin: 1.5rem 0;
                                    border-color: rgba(0, 0, 0, 0.1);
                                    border-style: solid;
                                  }
                                  .markdown-content table {
                                    width: 100%;
                                    border-collapse: collapse;
                                    margin-bottom: 1rem;
                                    background-color: rgba(255, 255, 255, 0.7);
                                  }
                                  .markdown-content th {
                                    border: 1px solid rgba(0, 0, 0, 0.1);
                                    padding: 0.75rem;
                                    background-color: rgba(255, 255, 255, 0.9);
                                    font-weight: 600;
                                    text-align: left;
                                    color: rgb(15 23 42);
                                  }
                                  .markdown-content td {
                                    border: 1px solid rgba(0, 0, 0, 0.1);
                                    padding: 0.75rem;
                                    color: rgb(30 41 59);
                                  }
                                `}</style>
                                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                  {extractTextContent(result.content)}
                                </ReactMarkdown>
                              </div>
                            )
                          ) : (
                            <Alert>
                              <AlertDescription>
                                {result.error || 'Failed to generate analysis'}
                              </AlertDescription>
                            </Alert>
                          )}
                        </CardContent>
                      )}
                    </Card>
                  )
                })}
              </div>
            </ScrollArea>
          </TabsContent>
          ))}

          {/* Free Tab Content */}
          <TabsContent value="free" className="mt-2">
            <div className="flex flex-col h-full">
              {/* Compact Input Section */}
              <div className="flex gap-3 mb-3">
                <textarea
                  value={currentPrompt}
                  onChange={(e) => setCurrentPrompt(e.target.value)}
                  placeholder="Ask a question about this paper..."
                  className="flex-1 h-20 p-3 border border-purple-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 bg-purple-50"
                  disabled={loadingFreeAnalysis}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && e.metaKey && !loadingFreeAnalysis && currentPrompt.trim()) {
                      submitFreeAnalysis()
                    }
                  }}
                />
                <Button
                  onClick={submitFreeAnalysis}
                  disabled={loadingFreeAnalysis || !currentPrompt.trim()}
                  className="px-6 bg-purple-600 hover:bg-purple-700 text-white self-end"
                  title="Generate Analysis (⌘+Enter)"
                >
                  {loadingFreeAnalysis ? (
                    <Loader2 className="h-5 w-5 animate-spin" />
                  ) : (
                    <Sparkles className="h-5 w-5" />
                  )}
                </Button>
              </div>

              {/* Q&A List - adjusted height calculation */}
              <div className="flex-1 overflow-auto" style={{maxHeight: 'calc(70vh - 250px)'}}>
                <div className="space-y-3">
                  {freeAnalyses.length === 0 ? (
                    <div className="text-center py-12 text-gray-500">
                      <MessageSquare className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                      <p>No analyses yet.</p>
                      <p className="text-sm mt-1">Ask a question above to get started!</p>
                    </div>
                  ) : (
                    // Sort analyses to show newest first (by created_at)
                    [...freeAnalyses]
                      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
                      .map((analysis, index) => {
                        const isExpanded = expandedFreeAnalyses.has(analysis.id)
                        const isEditing = editingFreeAnalysis === analysis.id
                        const analysisDate = new Date(analysis.created_at)
                        const timeAgo = getRelativeTime(analysisDate)
                        
                        return (
                          <Card key={analysis.id} className="border-l-4 border-l-purple-500">
                            <CardHeader className="py-3 cursor-pointer" onClick={() => {
                              setExpandedFreeAnalyses(prev => {
                                const next = new Set(prev)
                                if (next.has(analysis.id)) {
                                  next.delete(analysis.id)
                                } else {
                                  next.add(analysis.id)
                                }
                                return next
                              })
                            }}>
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    {isExpanded ? (
                                      <ChevronDown className="h-4 w-4 text-purple-600" />
                                    ) : (
                                      <ChevronRight className="h-4 w-4 text-purple-600" />
                                    )}
                                    <span className="text-xs font-medium text-purple-600 uppercase">Question</span>
                                    <span className="text-xs text-gray-500">{timeAgo}</span>
                                  </div>
                                  <p className="text-sm font-medium text-gray-900 mt-1 ml-6">
                                    {analysis.prompt}
                                  </p>
                                </div>
                                <div className="flex items-center space-x-1 ml-4" onClick={(e) => e.stopPropagation()}>
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => navigator.clipboard.writeText(`Q: ${analysis.prompt}\n\nA: ${analysis.content}`)}
                                    title="Copy Q&A"
                                    className="p-1"
                                  >
                                    <Copy className="h-3 w-3" />
                                  </Button>
                                  {!isEditing && (
                                    <Button
                                      size="sm"
                                      variant="ghost"
                                      onClick={() => {
                                        setEditingFreeAnalysis(analysis.id)
                                        setEditedFreeContent(prev => ({
                                          ...prev,
                                          [analysis.id]: analysis.content
                                        }))
                                      }}
                                      title="Edit answer"
                                      className="p-1"
                                    >
                                      <Edit2 className="h-3 w-3" />
                                    </Button>
                                  )}
                                  <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => deleteFreeAnalysis(analysis.id)}
                                    title="Delete"
                                    className="p-1 text-red-600 hover:text-red-700"
                                  >
                                    <Trash2 className="h-3 w-3" />
                                  </Button>
                                </div>
                              </div>
                            </CardHeader>
                            
                            {/* Answer - Only show when expanded */}
                            {isExpanded && (
                              <CardContent className="pt-0 pb-4">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-xs font-medium text-green-600 uppercase">Answer</span>
                                  <span className="text-xs text-gray-500">{analysis.model || 'Gemini 2.5 Pro'}</span>
                                </div>
                                {isEditing ? (
                                  <div className="space-y-2">
                                    <textarea
                                      value={editedFreeContent[analysis.id] || ''}
                                      onChange={(e) => setEditedFreeContent(prev => ({
                                        ...prev,
                                        [analysis.id]: e.target.value
                                      }))}
                                      className="w-full h-40 p-3 text-sm border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                                    />
                                    <div className="flex justify-end space-x-2">
                                      <Button
                                        size="sm"
                                        variant="outline"
                                        onClick={() => {
                                          setEditingFreeAnalysis(null)
                                          setEditedFreeContent(prev => {
                                            const updated = { ...prev }
                                            delete updated[analysis.id]
                                            return updated
                                          })
                                        }}
                                      >
                                        Cancel
                                      </Button>
                                      <Button
                                        size="sm"
                                        onClick={() => saveFreeAnalysisEdit(analysis.id)}
                                        className="bg-purple-600 hover:bg-purple-700 text-white"
                                      >
                                        Save
                                      </Button>
                                    </div>
                                  </div>
                                ) : (
                                  <div className="prose prose-sm max-w-none text-gray-700">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                      {extractTextContent(analysis.content)}
                                    </ReactMarkdown>
                                  </div>
                                )}
                              </CardContent>
                            )}
                          </Card>
                      )
                    })
                  )}
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
        
        {/* Instructions */}
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="text-sm font-semibold mb-2">How to use:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>• Click "Generate" on any analysis to create it</li>
            <li>• Use "Generate All in Category" to batch generate analyses</li>
            <li>• Click the arrow to expand/collapse generated content</li>
            <li>• Copy or download analyses for external use</li>
            <li>• Regenerate any analysis with the refresh button</li>
            <li>• <strong>Right-click on analysis text</strong> to create tags or snippets</li>
          </ul>
        </div>
      </CardContent>

      {/* Context Menu Portal */}
      {showContextMenu && ReactDOM.createPortal(
        <div
          className="fixed z-[9999] bg-white rounded-lg shadow-2xl border border-gray-200 py-1 min-w-[180px]"
          style={{
            left: `${contextMenuPosition.x}px`,
            top: `${contextMenuPosition.y}px`,
          }}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-blue-50 flex items-center gap-2 transition-colors"
            onClick={() => handleMenuAction('copy')}
          >
            <Copy className="h-4 w-4 text-blue-600" />
            <span>Copy Text</span>
          </button>
          
          <div className="border-t border-gray-100 my-1" />
          
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-green-50 flex items-center gap-2 transition-colors"
            onClick={() => handleMenuAction('snippet')}
          >
            <MessageSquare className="h-4 w-4 text-green-600" />
            <span>Create Snippet</span>
          </button>
          
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-yellow-50 flex items-center gap-2 transition-colors"
            onClick={() => handleMenuAction('highlight')}
          >
            <Highlighter className="h-4 w-4 text-yellow-600" />
            <span>Highlight</span>
          </button>
          
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-purple-50 flex items-center gap-2 transition-colors"
            onClick={() => handleMenuAction('tag')}
          >
            <TagIcon className="h-4 w-4 text-purple-600" />
            <span>Create Tag</span>
          </button>
        </div>,
        document.body
      )}

      {/* Tag Creation Dialog */}
      <Dialog open={showTagDialog} onOpenChange={handleTagDialogClose}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TagIcon className="h-5 w-5 text-purple-600" />
              Create Tag from Analysis
            </DialogTitle>
            <DialogDescription>
              Edit the selected text and create a tag for this paper.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label htmlFor="analysisTagText" className="block text-sm font-medium text-gray-700 mb-2">
                Tag Text
              </label>
              <Input
                id="analysisTagText"
                value={tagText}
                onChange={(e) => setTagText(e.target.value)}
                placeholder="Enter tag text..."
                className="w-full"
                onKeyPress={(e) => {
                  if (e.key === 'Enter' && !creatingTag) {
                    handleCreateTag()
                  }
                }}
                disabled={creatingTag}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={handleTagDialogClose}
                disabled={creatingTag}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateTag}
                disabled={!tagText.trim() || creatingTag}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {creatingTag ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  'Create Tag'
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </Card>
  )
}