import React, { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import { decodeHtmlEntities } from '@/utils/htmlDecoder'
import { 
  FileText, 
  Upload, 
  Search, 
  Filter, 
  Calendar,
  Clock, 
  Building2, 
  Tag as TagIcon, 
  Eye,
  Download,
  BookOpen,
  BarChart3,
  Users,
  Hash,
  Trash2,
  FileDown,
  Loader2,
  X,
  RotateCcw,
  PlayCircle,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  FilterX,
  Cpu,
  GraduationCap,
  Flag,
  FileCode,
  Layers,
  Edit2,
  Save,
  X as CancelIcon,
  Star
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Separator } from '@/components/ui/separator'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Checkbox } from '@/components/ui/checkbox'
import { Textarea } from '@/components/ui/textarea'

import PaperUploadModern from './PaperUploadModern'
import PaperViewerOptimized from './PaperViewerOptimized'
import UnifiedImportDialog from './UnifiedImportDialog'
import PaperTagSuggestionModal from './PaperTagSuggestionModal'

interface Paper {
  id: number
  title: string
  abstract?: string
  authors: Array<{ name: string; email?: string; affiliation?: string }> | string
  authors_detailed?: Array<{ name: string; email?: string; affiliation?: string }>
  publication_date?: string
  year?: number
  conference?: string
  journal?: string
  arxiv_id?: string
  doi?: string
  dblp_url?: string
  pdf_path?: string
  page_count: number
  word_count?: number
  tags: string[]
  concepts?: Array<{ concept_id: string; slug: string; display_name: string }>
  created_at: string
  processed: boolean
  processor?: string
  processor_used?: string
  processing_error?: string
  processing_status?: string
  is_flagged?: boolean
  flag_notes?: string
  tei_content?: string  // TEI/XML content
  analyses?: Array<any>  // Available analyses
  ai_summary?: string
  key_findings?: string[]
  readability?: {
    flesch_reading_ease?: number
    flesch_kincaid_grade?: number
    difficulty?: string
    academic_level?: string
  }
  user_rating?: number  // Star rating (1-5 or undefined for unrated)
}

interface PapersStats {
  total_papers: number
  total_authors: number
  total_concept_tags?: number  // New field name
  total_tags?: number  // For backwards compatibility
  total_snippets: number
  recent_papers: Array<{ id: number; title: string; created_at: string }>
  top_tags: Array<{ tag: string; count: number }>
}

interface FacetItem {
  value: string | number
  count: number
  label: string
}

interface Facets {
  authors: FacetItem[]
  conferences: FacetItem[]
  journals: FacetItem[]
  years: FacetItem[]
  tags: FacetItem[]
  concepts: any[] // Raw concepts from API with concept_id, slug, display_name, count
  affiliations: FacetItem[]
  processors: FacetItem[]
  special_filters: FacetItem[]
  missing_data?: {
    no_processor: number
    no_year: number
    no_conference: number
    no_affiliation: number
    no_annotations: number
  }
  paper_status?: {
    flagged: number
    unflagged: number
  }
  rating?: {
    '5_stars': number
    '4_stars': number
    '3_stars': number
    '2_stars': number
    '1_star': number
    'unrated': number
    [key: string]: number  // Allow dynamic key access
  }
}

interface FacetResponse {
  facets: Facets
  total_results: number
  active_filters: {
    search?: string
    author?: string
    tag?: string
    conference?: string
    year?: number
    affiliation?: string
  }
}

const FacetedPapersDashboard: React.FC = () => {
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [papers, setPapers] = useState<Paper[]>([])
  const [stats, setStats] = useState<PapersStats | null>(null)
  const [facets, setFacets] = useState<Facets | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingFacets, setLoadingFacets] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedPaperId, setSelectedPaperId] = useState<number | string | null>(null)
  const [searchMode, setSearchMode] = useState<'standard' | 'semantic'>('standard')
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [processingPapers, setProcessingPapers] = useState<Set<number>>(new Set())
  const [processingMessage, setProcessingMessage] = useState<string | null>(null)
  
  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedAuthors, setSelectedAuthors] = useState<Set<string>>(new Set())
  const [selectedTags, setSelectedTags] = useState<Set<string>>(new Set())
  const [conceptSearch, setConceptSearch] = useState('')
  const [showHierarchy, setShowHierarchy] = useState(false)
  const [selectedConferences, setSelectedConferences] = useState<Set<string>>(new Set())
  const [selectedYears, setSelectedYears] = useState<Set<number>>(new Set())
  const [selectedAffiliations, setSelectedAffiliations] = useState<Set<string>>(new Set())
  const [selectedProcessors, setSelectedProcessors] = useState<Set<string>>(new Set())
  const [sortBy, setSortBy] = useState<'created_at' | 'publication_date' | 'title' | 'rating'>('created_at')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  // Special filters
  const [showFlagged, setShowFlagged] = useState<boolean | null>(null) // null = all, true = flagged, false = unflagged
  const [showNoProcessor, setShowNoProcessor] = useState(false)
  const [showNoYear, setShowNoYear] = useState(false)
  const [showNoConference, setShowNoConference] = useState(false)
  const [showNoAffiliation, setShowNoAffiliation] = useState(false)
  const [showNoAnnotations, setShowNoAnnotations] = useState(false)

  // Rating filters
  const [selectedRating, setSelectedRating] = useState<number | null>(null)  // Exact rating filter (1-5)
  const [minRating, setMinRating] = useState<number | null>(null)            // Minimum rating filter
  const [showUnratedOnly, setShowUnratedOnly] = useState(false)              // Show only unrated papers
  
  // Facet UI state
  const [expandedFacets, setExpandedFacets] = useState<Set<string>>(new Set(['authors', 'concepts', 'years', 'special']))
  const [expandedSummaries, setExpandedSummaries] = useState<Set<string>>(new Set())
  const [editingSummaries, setEditingSummaries] = useState<Set<string>>(new Set())
  const [editedSummaryContent, setEditedSummaryContent] = useState<Record<string, string>>({})
  const [savingSummaries, setSavingSummaries] = useState<Set<string>>(new Set())
  const [expandedTags, setExpandedTags] = useState<Set<number>>(new Set())
  const [showTagSuggestionModal, setShowTagSuggestionModal] = useState(false)
  const [selectedPaperForTags, setSelectedPaperForTags] = useState<any | null>(null)
  
  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPapers, setTotalPapers] = useState(0)
  const pageSize = 20

  // Function to assign colors to tags
  const getTagColor = (tag: string, index: number) => {
    return 'border-blue-200 text-blue-800 bg-blue-50 hover:bg-blue-100'
  }

  // Load facets
  const loadFacets = useCallback(async () => {
    setLoadingFacets(true)
    try {
      const params = new URLSearchParams()
      if (searchTerm) params.append('search', searchTerm)
      if (selectedAuthors.size === 1) params.append('author', Array.from(selectedAuthors)[0])
      // Pass all selected concept IDs for dynamic facet filtering
      if (selectedTags.size > 0) {
        Array.from(selectedTags).forEach(conceptId => {
          params.append('concept_ids', conceptId)
        })
      }
      // Always send as plural parameters for consistency
      selectedConferences.forEach(conf => params.append('conferences', conf))
      selectedYears.forEach(year => params.append('years', year.toString()))
      selectedAffiliations.forEach(affil => params.append('affiliations', affil))
      selectedProcessors.forEach(proc => params.append('processors', proc))
      
      // Load facets from MongoDB
      const response = await axios.get(`http://localhost:8000/api/papers/facets?${params}`)
      
      // Transform MongoDB response to expected format
      const facetsData = response.data
      setFacets({
        authors: facetsData.authors?.map((f: any) => ({ value: f.name, count: f.count, label: f.name })) || [],
        conferences: facetsData.conferences?.map((f: any) => ({ value: f.name, count: f.count, label: f.name })) || [],
        journals: facetsData.journals?.map((f: any) => ({ value: f.name, count: f.count, label: f.name })) || [],
        years: facetsData.years?.map((f: any) => ({ value: f.year, count: f.count, label: f.year.toString() })) || [],
        tags: facetsData.concepts?.map((f: any) => ({
          value: f.display_name,
          count: f.count,
          label: f.display_name,
          id: f.concept_id || f.id || f.display_name  // Add unique id for key
        })) || [],
        concepts: facetsData.concepts || [], // Add concepts field with raw data from API
        affiliations: facetsData.institutions?.map((f: any) => ({ value: f.name, count: f.count, label: f.name })) || [],
        processors: facetsData.processors?.map((f: any) => ({ value: f.name, count: f.count, label: f.name })) || [],
        special_filters: facetsData.special_filters?.map((f: any) => ({ value: f.name, count: f.count, label: f.label })) || [],
        missing_data: facetsData.missing_data,  // Add missing_data from backend
        paper_status: facetsData.paper_status,  // Add paper_status from backend
        rating: facetsData.rating  // Add rating facet from backend
      })
    } catch (err: any) {
      console.error('Failed to load facets:', err)
      // Initialize with empty facets on error
      setFacets({
        authors: [],
        conferences: [],
        journals: [],
        years: [],
        tags: [],
        concepts: [], // Add empty concepts array
        affiliations: [],
        processors: [],
        special_filters: [],
        missing_data: undefined,
        paper_status: undefined,
        rating: undefined
      })
    } finally {
      setLoadingFacets(false)
    }
  }, [searchTerm, selectedAuthors, selectedTags, selectedConferences, selectedYears, selectedAffiliations])

  // Load papers
  const loadPapers = useCallback(async () => {
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
        // Use standard filtering with facets
        const params = new URLSearchParams({
          page: currentPage.toString(),
          page_size: pageSize.toString()
        })
        
        if (searchTerm) params.append('search', searchTerm)
        
        // For multi-select facets, we'll need to handle this differently
        // For now, support single selection
        if (selectedAuthors.size === 1) params.append('author', Array.from(selectedAuthors)[0])
        // Use concept_ids parameter for tag filtering (supports multiple)
        if (selectedTags.size > 0) {
          // Send all selected concept IDs for AND filtering
          Array.from(selectedTags).forEach(conceptId => {
            params.append('concept_ids', conceptId)
          })
        }
        // Send all selected values for proper filtering
        selectedConferences.forEach(conf => params.append('conferences', conf))
        selectedYears.forEach(year => params.append('years', year.toString()))
        selectedAffiliations.forEach(affil => params.append('affiliations', affil))
        selectedProcessors.forEach(proc => params.append('processors', proc))
        
        // Special filters
        if (showFlagged !== null) params.append('is_flagged', showFlagged.toString())
        if (showNoProcessor) params.append('no_processor', 'true')
        if (showNoYear) params.append('no_year', 'true')
        if (showNoConference) params.append('no_conference', 'true')
        if (showNoAffiliation) params.append('no_affiliation', 'true')
        if (showNoAnnotations) params.append('no_annotations', 'true')

        // Rating filters
        if (selectedRating !== null) params.append('rating', selectedRating.toString())
        if (minRating !== null) params.append('min_rating', minRating.toString())
        if (showUnratedOnly) params.append('unrated_only', 'true')

        // Sort options - use backend sorting
        params.append('sort_by', sortBy)
        params.append('sort_order', sortOrder)

        const response = await axios.get(`http://localhost:8000/api/papers/?${params}`)

        // Handle both array and object responses
        const papersData = Array.isArray(response.data) ? response.data : (response.data.papers || [])

        setPapers(papersData)
        // Set total from response or count the papers
        setTotalPapers(response.data.total || papersData.length)
      }
    } catch (err: any) {
      setError('Failed to load papers: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }, [searchMode, searchTerm, selectedAuthors, selectedTags, selectedConferences, selectedYears, selectedAffiliations, selectedProcessors, currentPage, sortBy, sortOrder, showFlagged, showNoProcessor, showNoYear, showNoConference, showNoAffiliation, showNoAnnotations, selectedRating, minRating, showUnratedOnly])

  const loadStats = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/papers/stats/overview')
      setStats(response.data)
    } catch (err: any) {
      console.error('Failed to load stats:', err)
    }
  }

  const handleUploadComplete = () => {
    loadStats()
    loadPapers()
    loadFacets()
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  const clearAllFilters = () => {
    setSearchTerm('')
    setSelectedAuthors(new Set())
    setSelectedTags(new Set())
    setSelectedConferences(new Set())
    setSelectedYears(new Set())
    setSelectedAffiliations(new Set())
    setSelectedProcessors(new Set())
    setShowFlagged(null)
    setShowNoProcessor(false)
    setShowNoYear(false)
    setShowNoConference(false)
    setShowNoAffiliation(false)
    setShowNoAnnotations(false)
    setSelectedRating(null)
    setMinRating(null)
    setShowUnratedOnly(false)
    setCurrentPage(1)
  }

  const togglePaperFlag = async (paperId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    
    const paper = papers.find(p => p.id === paperId)
    if (!paper) return
    
    try {
      const response = await axios.post(`http://localhost:8000/api/papers/${paperId}/flag`, {
        is_flagged: !paper.is_flagged
      })
      
      // Update local state
      setPapers(papers.map(p => 
        p.id === paperId 
          ? { ...p, is_flagged: response.data.is_flagged }
          : p
      ))
    } catch (err: any) {
      console.error('Failed to toggle flag:', err)
    }
  }

  // Handle paper rating
  const handleRatePaper = async (paperId: number | string, rating: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()

    try {
      await axios.patch(`http://localhost:8000/api/papers/${paperId}/rating`, null, {
        params: { rating }
      })

      // Update local state
      setPapers(papers.map(p =>
        (p.id === paperId || String(p.id) === String(paperId))
          ? { ...p, user_rating: rating === 0 ? undefined : rating }
          : p
      ))

      // Refresh facets to update rating counts
      loadFacets()
    } catch (err: any) {
      console.error('Failed to set rating:', err)
    }
  }

  // Star Rating Component
  const StarRating = ({
    rating,
    onRate,
    size = 'sm',
    readOnly = false
  }: {
    rating?: number
    onRate?: (rating: number) => void
    size?: 'sm' | 'md'
    readOnly?: boolean
  }) => {
    const [hoverRating, setHoverRating] = useState<number | null>(null)
    const displayRating = hoverRating ?? rating ?? 0
    const starSize = size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'

    return (
      <div className="flex items-center gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <button
            key={star}
            onClick={(e) => {
              if (readOnly || !onRate) return
              e.stopPropagation()
              onRate(star === rating ? 0 : star)  // Click same star to clear
            }}
            onMouseEnter={() => !readOnly && setHoverRating(star)}
            onMouseLeave={() => !readOnly && setHoverRating(null)}
            className={`p-0.5 transition-transform ${!readOnly ? 'hover:scale-110 cursor-pointer' : 'cursor-default'}`}
            disabled={readOnly}
          >
            <Star
              className={`${starSize} ${
                star <= displayRating
                  ? "fill-yellow-400 text-yellow-400"
                  : "text-gray-300"
              }`}
            />
          </button>
        ))}
      </div>
    )
  }

  const toggleFacet = (facetName: string) => {
    const newExpanded = new Set(expandedFacets)
    if (newExpanded.has(facetName)) {
      newExpanded.delete(facetName)
    } else {
      newExpanded.add(facetName)
    }
    setExpandedFacets(newExpanded)
  }

  const toggleSummary = (paperId: string) => {
    const newExpanded = new Set(expandedSummaries)
    if (newExpanded.has(paperId)) {
      newExpanded.delete(paperId)
    } else {
      newExpanded.add(paperId)
    }
    setExpandedSummaries(newExpanded)
  }

  const toggleExpandedTags = (paperId: number) => {
    const newExpanded = new Set(expandedTags)
    if (newExpanded.has(paperId)) {
      newExpanded.delete(paperId)
    } else {
      newExpanded.add(paperId)
    }
    setExpandedTags(newExpanded)
  }

  const startEditingSummary = (paperId: string, content: string) => {
    setEditingSummaries(prev => new Set(prev).add(paperId))
    setEditedSummaryContent(prev => ({ ...prev, [paperId]: content }))
  }

  const cancelEditingSummary = (paperId: string) => {
    setEditingSummaries(prev => {
      const newSet = new Set(prev)
      newSet.delete(paperId)
      return newSet
    })
    setEditedSummaryContent(prev => {
      const newContent = { ...prev }
      delete newContent[paperId]
      return newContent
    })
  }

  const saveSummaryEdit = async (paperId: string) => {
    const content = editedSummaryContent[paperId]
    if (!content) return

    setSavingSummaries(prev => new Set(prev).add(paperId))
    
    try {
      await axios.put(
        `http://localhost:8000/api/papers/${paperId}/analyses/generated/mollick_summary`,
        { content }
      )
      
      // Update the local paper data
      setPapers(prev => prev.map(p => {
        if (p.id === paperId && p.analyses) {
          const updatedAnalyses = p.analyses.map((a: any) => {
            if (a.analysis_type === 'mollick_summary' || 
                a.analysis_name === 'mollick_summary' ||
                a.type === 'mollick_summary') {
              return { ...a, content }
            }
            return a
          })
          return { ...p, analyses: updatedAnalyses }
        }
        return p
      }))
      
      // Emit event for PaperAnalysisPanel to update if open
      window.dispatchEvent(new CustomEvent('paperAnalysisUpdated', {
        detail: {
          paperId,
          analysisType: 'mollick_summary',
          content
        }
      }))
      
      // Clear editing state
      cancelEditingSummary(paperId)
    } catch (err) {
      console.error('Failed to save summary edit:', err)
      alert('Failed to save changes')
    } finally {
      setSavingSummaries(prev => {
        const newSet = new Set(prev)
        newSet.delete(paperId)
        return newSet
      })
    }
  }

  const toggleFacetValue = (facetType: string, value: string | number) => {
    let newSet: Set<any>
    let setter: (s: Set<any>) => void
    
    switch (facetType) {
      case 'author':
        newSet = new Set(selectedAuthors)
        setter = setSelectedAuthors
        break
      case 'tag':
        newSet = new Set(selectedTags)
        setter = setSelectedTags
        break
      case 'conference':
        newSet = new Set(selectedConferences)
        setter = setSelectedConferences
        break
      case 'year':
        newSet = new Set(selectedYears)
        setter = setSelectedYears
        value = Number(value)
        break
      case 'affiliation':
        newSet = new Set(selectedAffiliations)
        setter = setSelectedAffiliations
        break
      case 'processor':
        newSet = new Set(selectedProcessors)
        setter = setSelectedProcessors
        break
      default:
        return
    }
    
    if (newSet.has(value)) {
      newSet.delete(value)
    } else {
      // Allow multiple selection for tags/concepts, single for others
      if (facetType !== 'tag') {
        newSet.clear() // Single selection for non-tag facets
      }
      newSet.add(value)
    }
    setter(newSet)
    setCurrentPage(1)
  }

  const handleDeletePaper = async (paperId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    
    if (!window.confirm('Are you sure you want to delete this paper? This action cannot be undone.')) {
      return
    }
    
    try {
      await axios.delete(`http://localhost:8000/api/papers/${paperId}`)
      loadPapers()
      loadStats()
      loadFacets()
    } catch (error) {
      console.error('Error deleting paper:', error)
      setError('Failed to delete paper')
    }
  }

  const totalPages = Math.ceil(totalPapers / pageSize)
  const activeFilterCount = 
    (searchTerm ? 1 : 0) +
    selectedAuthors.size +
    selectedTags.size +
    selectedConferences.size +
    selectedYears.size +
    selectedAffiliations.size +
    selectedProcessors.size +
    (showFlagged !== null ? 1 : 0) +
    (showNoProcessor ? 1 : 0) +
    (showNoYear ? 1 : 0) +
    (showNoConference ? 1 : 0) +
    (showNoAffiliation ? 1 : 0) +
    (showNoAnnotations ? 1 : 0) +
    (selectedRating !== null ? 1 : 0) +
    (minRating !== null ? 1 : 0) +
    (showUnratedOnly ? 1 : 0)

  // Load data when component mounts or filters change
  useEffect(() => {
    loadStats()
    loadFacets() // Always load facets - will update based on filters
    loadPapers()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTags, selectedAuthors, selectedConferences, selectedYears, selectedAffiliations, selectedProcessors, searchTerm, currentPage, sortBy, sortOrder, showFlagged, showNoProcessor, showNoYear, showNoConference, showNoAffiliation, showNoAnnotations, selectedRating, minRating, showUnratedOnly])

  // Periodically check for processing status updates when papers are being processed
  useEffect(() => {
    if (processingPapers.size > 0) {
      const interval = setInterval(() => {
        loadPapers()
        loadFacets()
      }, 5000) // Check every 5 seconds

      return () => clearInterval(interval)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processingPapers.size])

  // Listen for switch to upload event from import dialog
  useEffect(() => {
    const handleSwitchToUpload = () => {
      // Upload functionality handled by button click
    }
    
    window.addEventListener('switchToUpload', handleSwitchToUpload)
    return () => {
      window.removeEventListener('switchToUpload', handleSwitchToUpload)
    }
  }, [])

  // Listen for paper analysis updates from PaperAnalysisPanel
  useEffect(() => {
    const handlePaperAnalysisUpdated = (event: CustomEvent) => {
      const { paperId, analysisType, content } = event.detail
      
      // Update the papers state to reflect the new analysis content
      setPapers(prevPapers => 
        prevPapers.map(paper => {
          if (paper.id.toString() === paperId.toString()) {
            // Update the analyses array for this paper
            const updatedAnalyses = paper.analyses ? [...paper.analyses] : []
            const analysisIndex = updatedAnalyses.findIndex(a => 
              a.analysis_type === analysisType || 
              a.analysis_name === analysisType ||
              a.type === analysisType
            )
            
            if (analysisIndex >= 0) {
              // Update existing analysis
              updatedAnalyses[analysisIndex] = {
                ...updatedAnalyses[analysisIndex],
                content: content,
                analysis_content: content,
                updated_at: new Date().toISOString()
              }
            } else {
              // Add new analysis if it doesn't exist
              updatedAnalyses.push({
                analysis_type: analysisType,
                type: analysisType,
                content: content,
                analysis_content: content,
                updated_at: new Date().toISOString()
              })
            }
            
            return {
              ...paper,
              analyses: updatedAnalyses
            }
          }
          return paper
        })
      )
    }
    
    window.addEventListener('paperAnalysisUpdated', handlePaperAnalysisUpdated as EventListener)
    return () => {
      window.removeEventListener('paperAnalysisUpdated', handlePaperAnalysisUpdated as EventListener)
    }
  }, [])

  // Listen for paper tags updates from PaperViewerOptimized
  useEffect(() => {
    const handlePaperTagsUpdated = (event: CustomEvent) => {
      const { paperId, concepts } = event.detail

      // Update the papers state to reflect the new concepts
      setPapers(prevPapers =>
        prevPapers.map(paper => {
          if (paper.id.toString() === paperId.toString()) {
            return {
              ...paper,
              concepts: concepts
            }
          }
          return paper
        })
      )
    }

    window.addEventListener('paperTagsUpdated', handlePaperTagsUpdated as EventListener)
    return () => {
      window.removeEventListener('paperTagsUpdated', handlePaperTagsUpdated as EventListener)
    }
  }, [])

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Left Sidebar - Facets */}
      <div className="w-80 bg-white border-r border-gray-200 overflow-y-auto">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Filters</h2>
            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={clearAllFilters}
                className="text-blue-600 hover:text-blue-800"
              >
                <FilterX className="h-4 w-4 mr-1" />
                Clear All ({activeFilterCount})
              </Button>
            )}
          </div>
          
          
          {/* Facets */}
          {loadingFacets ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <div className="space-y-4">
              {/* Authors Facet */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => toggleFacet('authors')}
                    className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
                  >
                    <Users className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Authors</span>
                    {selectedAuthors.size > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {selectedAuthors.size}
                      </Badge>
                    )}
                    {expandedFacets.has('authors') ? (
                      <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400 ml-1" />
                    )}
                  </button>
                  {selectedAuthors.size > 0 && (
                    <button
                      onClick={() => {
                        setSelectedAuthors(new Set())
                        setCurrentPage(1)
                      }}
                      className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                      title="Clear author filters"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
                {expandedFacets.has('authors') && (
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {facets && facets.authors && facets.authors.length > 0 ? (
                      facets.authors.map((author, index) => (
                        <label
                          key={`${author.value}-${index}`}
                          className="flex items-center space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded"
                        >
                          <Checkbox
                            checked={selectedAuthors.has(author.value as string)}
                            onCheckedChange={() => toggleFacetValue('author', author.value)}
                          />
                          <span className="text-sm text-gray-600 flex-1 truncate" title={author.label}>
                            {author.label}
                          </span>
                          <span className="text-xs text-gray-400">({author.count})</span>
                        </label>
                      ))
                    ) : (
                      <div className="text-sm text-gray-400 px-2 py-2">No authors found</div>
                    )}
                  </div>
                )}
              </div>
              
              {/* Years Facet */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => toggleFacet('years')}
                    className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
                  >
                    <Calendar className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Years</span>
                    {selectedYears.size > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {selectedYears.size}
                      </Badge>
                    )}
                    {expandedFacets.has('years') ? (
                      <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400 ml-1" />
                    )}
                  </button>
                  {selectedYears.size > 0 && (
                    <button
                      onClick={() => {
                        setSelectedYears(new Set())
                        setCurrentPage(1)
                      }}
                      className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                      title="Clear year filters"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
                  {expandedFacets.has('years') && (
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {facets && facets.years && facets.years.length > 0 ? (
                        facets.years.map((year, index) => (
                        <label
                          key={`${year.value}-${index}`}
                          className="flex items-center space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded"
                        >
                          <Checkbox
                            checked={selectedYears.has(year.value as number)}
                            onCheckedChange={() => toggleFacetValue('year', year.value)}
                          />
                          <span className="text-sm text-gray-600 flex-1">
                            {year.label}
                          </span>
                          <span className="text-xs text-gray-400">({year.count})</span>
                        </label>
                      ))
                      ) : (
                        <div className="text-sm text-gray-400 px-2 py-2">No years found</div>
                      )}
                    </div>
                  )}
                </div>
              
              {/* Conferences Facet */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => toggleFacet('conferences')}
                    className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
                  >
                    <Building2 className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Conferences</span>
                    {selectedConferences.size > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {selectedConferences.size}
                      </Badge>
                    )}
                    {expandedFacets.has('conferences') ? (
                      <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400 ml-1" />
                    )}
                  </button>
                  {selectedConferences.size > 0 && (
                    <button
                      onClick={() => {
                        setSelectedConferences(new Set())
                        setCurrentPage(1)
                      }}
                      className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                      title="Clear conference filters"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
                  {expandedFacets.has('conferences') && (
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {facets && facets.conferences && facets.conferences.length > 0 ? (
                        facets.conferences.map((conf, index) => (
                        <label
                          key={`${conf.value}-${index}`}
                          className="flex items-center space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded"
                        >
                          <Checkbox
                            checked={selectedConferences.has(conf.value as string)}
                            onCheckedChange={() => toggleFacetValue('conference', conf.value)}
                          />
                          <span className="text-sm text-gray-600 flex-1 truncate" title={conf.label}>
                            {conf.label}
                          </span>
                          <span className="text-xs text-gray-400">({conf.count})</span>
                        </label>
                      ))
                      ) : (
                        <div className="text-sm text-gray-400 px-2 py-2">No conferences found</div>
                      )}
                    </div>
                  )}
                </div>
              
              {/* Affiliations/Institutions Facet */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => toggleFacet('affiliations')}
                    className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
                  >
                    <GraduationCap className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Institutions</span>
                    {selectedAffiliations.size > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {selectedAffiliations.size}
                      </Badge>
                    )}
                    {expandedFacets.has('affiliations') ? (
                      <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400 ml-1" />
                    )}
                  </button>
                  {selectedAffiliations.size > 0 && (
                    <button
                      onClick={() => {
                        setSelectedAffiliations(new Set())
                        setCurrentPage(1)
                      }}
                      className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                      title="Clear institution filters"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
                {expandedFacets.has('affiliations') && (
                  <div className="space-y-1 max-h-48 overflow-y-auto">
                    {facets && facets.affiliations && facets.affiliations.length > 0 ? (
                      facets.affiliations.map((affil, index) => (
                        <label
                          key={`${affil.value}-${index}`}
                          className="flex items-center space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded"
                        >
                          <Checkbox
                            checked={selectedAffiliations.has(affil.value as string)}
                            onCheckedChange={() => toggleFacetValue('affiliation', affil.value)}
                          />
                          <span className="text-sm text-gray-600 flex-1 truncate" title={affil.label}>
                            {affil.label}
                          </span>
                          <span className="text-xs text-gray-400">({affil.count})</span>
                        </label>
                      ))
                    ) : (
                      <div className="text-sm text-gray-400 px-2 py-2">No institutions found</div>
                    )}
                  </div>
                )}
              </div>
              
              {/* Processors Facet */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => toggleFacet('processors')}
                    className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
                  >
                    <Cpu className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Processors</span>
                    {selectedProcessors.size > 0 && (
                      <Badge variant="secondary" className="text-xs">
                        {selectedProcessors.size}
                      </Badge>
                    )}
                    {expandedFacets.has('processors') ? (
                      <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400 ml-1" />
                    )}
                  </button>
                  {selectedProcessors.size > 0 && (
                    <button
                      onClick={() => {
                        setSelectedProcessors(new Set())
                        setCurrentPage(1)
                      }}
                      className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                      title="Clear processor filters"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
                  {expandedFacets.has('processors') && (
                    <div className="space-y-1 max-h-48 overflow-y-auto">
                      {facets && facets.processors && facets.processors.length > 0 ? (
                        facets.processors.map((proc, index) => (
                        <label
                          key={`${proc.value}-${index}`}
                          className="flex items-center space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded"
                        >
                          <Checkbox
                            checked={selectedProcessors.has(proc.value as string)}
                            onCheckedChange={() => toggleFacetValue('processor', proc.value)}
                          />
                          <span className="text-sm text-gray-600 flex-1">
                            {proc.label}
                          </span>
                          <span className="text-xs text-gray-400">({proc.count})</span>
                        </label>
                      ))
                      ) : (
                        <div className="text-sm text-gray-400 px-2 py-2">No processors found</div>
                      )}
                    </div>
                  )}
                </div>
                
              {/* Special Filters Section */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <button
                    onClick={() => toggleFacet('special')}
                    className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
                  >
                    <Filter className="h-4 w-4 text-gray-500" />
                    <span className="text-sm font-medium text-gray-700">Special Filters</span>
                    {(showFlagged !== null || showNoProcessor || showNoYear || showNoConference || showNoAffiliation || showNoAnnotations) && (
                      <Badge variant="secondary" className="text-xs">
                        {(showFlagged !== null ? 1 : 0) + (showNoProcessor ? 1 : 0) + (showNoYear ? 1 : 0) + (showNoConference ? 1 : 0) + (showNoAffiliation ? 1 : 0) + (showNoAnnotations ? 1 : 0)}
                      </Badge>
                    )}
                    {expandedFacets.has('special') ? (
                      <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
                    ) : (
                      <ChevronRight className="h-4 w-4 text-gray-400 ml-1" />
                    )}
                  </button>
                  {(showFlagged !== null || showNoProcessor || showNoYear || showNoConference || showNoAffiliation || showNoAnnotations) && (
                    <button
                      onClick={() => {
                        setShowFlagged(null)
                        setShowNoProcessor(false)
                        setShowNoYear(false)
                        setShowNoConference(false)
                        setShowNoAffiliation(false)
                        setShowNoAnnotations(false)
                        setCurrentPage(1)
                      }}
                      className="p-1 hover:bg-gray-100 rounded text-gray-400 hover:text-gray-600"
                      title="Clear special filters"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  )}
                </div>
                {expandedFacets.has('special') && (
                  <div className="space-y-3 px-2">
                    {/* Flagged Papers Filter */}
                    <div className="space-y-2">
                      <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">Paper Status</span>
                      <div className="space-y-1">
                        <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={showFlagged === true}
                              onCheckedChange={(checked) => {
                                setShowFlagged(checked ? true : null)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-1">
                              <Flag className="h-3 w-3 text-orange-500" />
                              <span className="text-sm text-gray-600">Flagged</span>
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">({facets?.paper_status?.flagged || 0})</span>
                        </label>
                        <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={showFlagged === false}
                              onCheckedChange={(checked) => {
                                setShowFlagged(checked ? false : null)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-1">
                              <Flag className="h-3 w-3 text-gray-300" />
                              <span className="text-sm text-gray-600">Not Flagged</span>
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">({facets?.paper_status?.unflagged || 0})</span>
                        </label>
                      </div>
                    </div>
                    
                    <Separator className="my-2" />
                    
                    {/* Missing Data Filters */}
                    <div className="space-y-2">
                      <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">Missing Data</span>
                      <div className="space-y-1">
                        <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={showNoProcessor}
                              onCheckedChange={(checked) => {
                                setShowNoProcessor(checked as boolean)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-1">
                              <Cpu className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600">Processing</span>
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">({facets?.missing_data?.no_processor || 0})</span>
                        </label>
                        <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={showNoYear}
                              onCheckedChange={(checked) => {
                                setShowNoYear(checked as boolean)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-1">
                              <Calendar className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600">Year</span>
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">({facets?.missing_data?.no_year || 0})</span>
                        </label>
                        <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={showNoConference}
                              onCheckedChange={(checked) => {
                                setShowNoConference(checked as boolean)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-1">
                              <Building2 className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600">Conference</span>
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">({facets?.missing_data?.no_conference || 0})</span>
                        </label>
                        <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={showNoAffiliation}
                              onCheckedChange={(checked) => {
                                setShowNoAffiliation(checked as boolean)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-1">
                              <GraduationCap className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600">Affiliation</span>
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">({facets?.missing_data?.no_affiliation || 0})</span>
                        </label>
                        <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={showNoAnnotations}
                              onCheckedChange={(checked) => {
                                setShowNoAnnotations(checked as boolean)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-1">
                              <BookOpen className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600">Annotations</span>
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">({facets?.missing_data?.no_annotations || 0})</span>
                        </label>
                      </div>
                    </div>

                    <Separator className="my-2" />

                    {/* Rating Filter */}
                    <div className="space-y-2">
                      <span className="text-xs font-medium text-gray-600 uppercase tracking-wide">Rating</span>
                      <div className="space-y-1">
                        {[5, 4, 3, 2, 1].map((stars) => (
                          <label key={stars} className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                            <div className="flex items-center space-x-2">
                              <Checkbox
                                checked={selectedRating === stars}
                                onCheckedChange={(checked) => {
                                  setSelectedRating(checked ? stars : null)
                                  setMinRating(null)
                                  setShowUnratedOnly(false)
                                  setCurrentPage(1)
                                }}
                              />
                              <div className="flex items-center gap-0.5">
                                {Array.from({ length: 5 }).map((_, i) => (
                                  <Star
                                    key={i}
                                    className={`h-3 w-3 ${i < stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300'}`}
                                  />
                                ))}
                              </div>
                            </div>
                            <span className="text-xs text-gray-400">
                              ({facets?.rating?.[`${stars}_star${stars !== 1 ? 's' : ''}`] || 0})
                            </span>
                          </label>
                        ))}
                        <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={showUnratedOnly}
                              onCheckedChange={(checked) => {
                                setShowUnratedOnly(checked as boolean)
                                setSelectedRating(null)
                                setMinRating(null)
                                setCurrentPage(1)
                              }}
                            />
                            <span className="text-sm text-gray-600">Unrated</span>
                          </div>
                          <span className="text-xs text-gray-400">({facets?.rating?.unrated || 0})</span>
                        </label>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      
      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Research Papers</h1>
              <p className="text-gray-600">Upload, analyze, and manage PDF research papers with AI-powered processing</p>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={() => setShowImportDialog(true)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <FileDown className="h-4 w-4" />
                Import Paper
              </Button>
              <Button 
                onClick={() => setShowUploadModal(true)}
                variant="default"
                className="flex items-center gap-2"
              >
                <Upload className="h-4 w-4" />
                Upload PDF
              </Button>
            </div>
          </div>
          
          {/* Statistics Cards */}
          {stats && (
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Total Papers</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_papers}</p>
                    </div>
                    <FileText className="h-8 w-8 text-blue-500 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Authors</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_authors}</p>
                    </div>
                    <Users className="h-8 w-8 text-green-500 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Concepts</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_concept_tags || stats.total_tags || 0}</p>
                    </div>
                    <Hash className="h-8 w-8 text-purple-500 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500">Snippets</p>
                      <p className="text-2xl font-bold text-gray-900">{stats.total_snippets}</p>
                    </div>
                    <BookOpen className="h-8 w-8 text-orange-500 opacity-50" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
          
          {/* Main Content Area */}
          <div className="space-y-4">
            {/* Search Bar and Results Count */}
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Input
                  placeholder={searchMode === 'semantic' ? "Ask a question..." : "Search papers..."}
                  value={searchTerm}
                  onChange={(e) => {
                    setSearchTerm(e.target.value)
                    setCurrentPage(1)
                  }}
                  className="pr-24"
                />
                <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {searchTerm && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSearchTerm('')
                        setCurrentPage(1)
                      }}
                      className="h-7 w-7 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                  <Select value={searchMode} onValueChange={(value: any) => setSearchMode(value)}>
                    <SelectTrigger className="w-24 h-7 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Standard</SelectItem>
                      <SelectItem value="semantic">Semantic</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              
              {/* Results Counter */}
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <FileText className="h-4 w-4" />
                <span>{totalPapers} {totalPapers === 1 ? 'paper' : 'papers'}</span>
                {activeFilterCount > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {activeFilterCount} {activeFilterCount === 1 ? 'filter' : 'filters'} applied
                  </Badge>
                )}
              </div>
            </div>
            
            {/* Active Concept Filters */}
            {selectedTags.size > 0 && (
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <span className="text-sm font-medium text-gray-600">Active concepts:</span>
                {Array.from(selectedTags).map(tagId => {
                  const concept = facets?.concepts?.find(c => (c.concept_id || c.slug) === tagId)
                  return (
                    <Badge
                      key={tagId}
                      variant="default"
                      className="bg-blue-100 text-blue-800 hover:bg-blue-200 cursor-pointer"
                      onClick={() => toggleFacetValue('tag', tagId)}
                    >
                      {concept?.display_name || tagId}
                      <X className="h-3 w-3 ml-1" />
                    </Badge>
                  )
                })}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setSelectedTags(new Set())}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  Clear all
                </Button>
              </div>
            )}
            
            {/* Sorting Controls */}
            <Card className="bg-white">
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-medium text-gray-600">Sort by:</span>
                    <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
                      <SelectTrigger className="w-48">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="created_at">Date Added</SelectItem>
                        <SelectItem value="publication_date">Publication Date</SelectItem>
                        <SelectItem value="title">Title</SelectItem>
                        <SelectItem value="rating">Rating (Highest First)</SelectItem>
                      </SelectContent>
                    </Select>
                    <Select value={sortOrder} onValueChange={(value: any) => setSortOrder(value)}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="desc">Newest First</SelectItem>
                        <SelectItem value="asc">Oldest First</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </CardContent>
            </Card>

                {/* Processing Message */}
                {processingMessage && (
                  <Alert className={processingMessage.includes('Error') ? "border-red-200 bg-red-50" : processingMessage.includes('Successfully') ? "border-green-200 bg-green-50" : "border-blue-200 bg-blue-50"}>
                    <AlertDescription className={processingMessage.includes('Error') ? "text-red-800" : processingMessage.includes('Successfully') ? "text-green-800" : "text-blue-800"}>
                      {processingMessage}
                    </AlertDescription>
                  </Alert>
                )}

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
                        <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
                        <p className="text-gray-500">Loading papers...</p>
                      </div>
                    </CardContent>
                  </Card>
                ) : (
                  <>
                    <div className="grid gap-3">
                      {papers.map((paper) => (
                        <Card key={paper.id} className="hover:shadow-md transition-all duration-200 bg-white border-gray-200">
                          <CardContent className="p-3">
                            <div className="flex justify-between items-start gap-3">
                              <div className="flex-1 min-w-0">
                                {/* Title and Main Actions in same row */}
                                <div className="flex items-start gap-2 mb-2">
                                  <h3 className="text-base font-semibold text-gray-900 line-clamp-2 flex-1">
                                    {decodeHtmlEntities(paper.title)}
                                  </h3>
                                  <div className="flex items-center gap-1 flex-shrink-0">
                                    <Button
                                      size="sm"
                                      variant={paper.is_flagged ? "default" : "outline"}
                                      className={paper.is_flagged 
                                        ? "bg-orange-500 hover:bg-orange-600 text-white h-7 px-2" 
                                        : "h-7 px-2 hover:bg-orange-50 hover:text-orange-600 hover:border-orange-300"}
                                      onClick={(e) => togglePaperFlag(paper.id, e)}
                                      title={paper.is_flagged ? "Remove flag" : "Flag this paper"}
                                    >
                                      <Flag className="h-3 w-3" fill={paper.is_flagged ? "currentColor" : "none"} />
                                    </Button>
                                    <Button 
                                      size="sm" 
                                      className="bg-blue-600 hover:bg-blue-700 text-white h-7 px-3 text-xs"
                                      onClick={() => setSelectedPaperId(paper.id)}
                                    >
                                      <Eye className="h-3 w-3 mr-1" />
                                      View
                                    </Button>
                                    {paper.pdf_path && (
                                      <Button 
                                        size="sm" 
                                        variant="outline"
                                        className="h-7 w-7 p-0"
                                        onClick={(e) => {
                                          e.stopPropagation()
                                          window.open(`http://localhost:8000/papers/${paper.pdf_path.split('/').pop()}`, '_blank')
                                        }}
                                        title="Download PDF"
                                      >
                                        <Download className="h-3 w-3" />
                                      </Button>
                                    )}
                                    <Button 
                                      size="sm" 
                                      variant="outline"
                                      className="h-7 w-7 p-0"
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        setSelectedPaperForTags(paper)
                                        setShowTagSuggestionModal(true)
                                      }}
                                      title="Suggest tags"
                                    >
                                      <TagIcon className="h-3 w-3" />
                                    </Button>
                                    <Button 
                                      size="sm" 
                                      variant="outline"
                                      className="h-7 w-7 p-0 hover:bg-red-50 hover:text-red-600"
                                      onClick={(e) => handleDeletePaper(paper.id, e)}
                                      title="Delete"
                                    >
                                      <Trash2 className="h-3 w-3" />
                                    </Button>
                                  </div>
                                </div>
                                
                                {/* Authors - More compact */}
                                {paper.authors && (
                                  <div className="text-xs text-gray-600 mb-2 flex items-center gap-1">
                                    <Users className="h-3 w-3 text-gray-400 flex-shrink-0" />
                                    <span className="line-clamp-1">
                                        {typeof paper.authors === 'string' 
                                          ? paper.authors
                                          : Array.isArray(paper.authors) 
                                            ? paper.authors.map(a => typeof a === 'string' ? a : a.name).join(', ')
                                            : ''}
                                    </span>
                                    {/* Inline affiliations if available */}
                                    {paper.authors_detailed && paper.authors_detailed.length > 0 && (() => {
                                      const affiliations = paper.authors_detailed
                                        .filter(author => author.affiliation)
                                        .map(author => author.affiliation)
                                        .filter((value, index, self) => self.indexOf(value) === index);
                                      
                                      if (affiliations.length === 0) return null;
                                      
                                      return (
                                        <>
                                          <span className="text-gray-400">•</span>
                                          <Building2 className="h-3 w-3 text-gray-400" />
                                          <span className="line-clamp-1">{affiliations[0]}</span>
                                        </>
                                      );
                                    })()}
                                  </div>
                                )}

                                {/* Star Rating */}
                                <div className="flex items-center gap-2 mb-2">
                                  <StarRating
                                    rating={paper.user_rating}
                                    onRate={(rating) => handleRatePaper(paper.id, rating)}
                                    size="sm"
                                  />
                                  {paper.user_rating && (
                                    <span className="text-xs text-gray-500">
                                      {paper.user_rating}/5
                                    </span>
                                  )}
                                </div>

                                {/* Additional Metadata - Only non-redundant items */}
                                {(paper.tei_content || (paper.analyses && paper.analyses.length > 0)) && (
                                  <div className="flex items-center gap-2 mb-2">
                                    {/* TEI Available Icon */}
                                    {paper.tei_content && (
                                      <div className="flex items-center text-xs text-blue-600" title="TEI/XML available">
                                        <FileCode className="h-3 w-3 mr-1" />
                                        XML
                                      </div>
                                    )}
                                    
                                    {/* Analysis Available Icon */}
                                    {paper.analyses && paper.analyses.length > 0 && (
                                      <div className="flex items-center text-xs text-purple-600" title={`${paper.analyses.length} analysis available`}>
                                        <BarChart3 className="h-3 w-3 mr-1" />
                                        {paper.analyses.length} Analysis
                                      </div>
                                    )}
                                  </div>
                                )}
                                
                                {/* Processing Status Badge */}
                                {paper.processing_error && (
                                  <div className="mb-2 flex items-center gap-2">
                                    <Badge variant="destructive" className="bg-red-100 text-red-800 text-xs">
                                      ⚠️ Processing Error
                                    </Badge>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={async (e) => {
                                        e.stopPropagation()
                                        setProcessingPapers(prev => new Set(prev).add(paper.id))
                                        setProcessingMessage(`Retrying processing for paper ${paper.id}...`)
                                        try {
                                          const response = await axios.post(`http://localhost:8000/api/papers/${paper.id}/process`)
                                          if (response.data.success) {
                                            setProcessingMessage(`Successfully started processing paper ${paper.id}`)
                                            await loadPapers()
                                            await loadFacets()
                                          } else {
                                            setProcessingMessage(response.data.message || 'Failed to retry processing')
                                          }
                                        } catch (error: any) {
                                          const errorMsg = error.response?.data?.detail || error.message || 'Failed to retry processing'
                                          setProcessingMessage(`Error: ${errorMsg}`)
                                          console.error('Failed to retry processing:', error)
                                        } finally {
                                          setProcessingPapers(prev => {
                                            const newSet = new Set(prev)
                                            newSet.delete(paper.id)
                                            return newSet
                                          })
                                          setTimeout(() => setProcessingMessage(null), 3000)
                                        }
                                      }}
                                      disabled={processingPapers.has(paper.id)}
                                      className="h-5 px-2 text-xs"
                                      title={paper.processing_error}
                                    >
                                      {processingPapers.has(paper.id) ? (
                                        <>
                                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                          Retrying...
                                        </>
                                      ) : (
                                        <>
                                          <RotateCcw className="h-3 w-3 mr-1" />
                                          Retry
                                        </>
                                      )}
                                    </Button>
                                  </div>
                                )}
                                {!paper.processed && !paper.processing_error && (
                                  <div className="mb-2 flex items-center gap-2">
                                    <Badge className="bg-yellow-50 text-yellow-700 border-yellow-200 text-xs">
                                      ⏳ Not Processed
                                    </Badge>
                                    <Button
                                      size="sm"
                                      variant="outline"
                                      onClick={async (e) => {
                                        e.stopPropagation()
                                        setProcessingPapers(prev => new Set(prev).add(paper.id))
                                        setProcessingMessage(`Starting processing for paper ${paper.id}...`)
                                        try {
                                          const response = await axios.post(`http://localhost:8000/api/papers/${paper.id}/process`)
                                          if (response.data.success) {
                                            setProcessingMessage(`Successfully started processing paper ${paper.id}`)
                                            // Refresh the papers list to show processing state
                                            await loadPapers()
                                            await loadFacets()
                                          } else {
                                            setProcessingMessage(response.data.message || 'Failed to start processing')
                                          }
                                        } catch (error: any) {
                                          const errorMsg = error.response?.data?.detail || error.message || 'Failed to start processing'
                                          setProcessingMessage(`Error: ${errorMsg}`)
                                          console.error('Failed to start processing:', error)
                                        } finally {
                                          setProcessingPapers(prev => {
                                            const newSet = new Set(prev)
                                            newSet.delete(paper.id)
                                            return newSet
                                          })
                                          setTimeout(() => setProcessingMessage(null), 3000)
                                        }
                                      }}
                                      disabled={processingPapers.has(paper.id)}
                                      className="h-5 px-2 text-xs"
                                    >
                                      {processingPapers.has(paper.id) ? (
                                        <>
                                          <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                          Processing...
                                        </>
                                      ) : (
                                        <>
                                          <PlayCircle className="h-3 w-3 mr-1" />
                                          Process
                                        </>
                                      )}
                                    </Button>
                                  </div>
                                )}
                                {paper.processed && paper.processor_used && (
                                  <div className="mb-2 flex items-center gap-2">
                                    {/* Show current processor badge */}
                                    {paper.processor_used === 'pypdfium2' ? (
                                      <Badge className="bg-gray-100 text-gray-600 border-gray-200 text-xs">
                                        📄 Basic (Backup)
                                      </Badge>
                                    ) : paper.processor_used === 'marker' || paper.processor_used === 'marker_service' ? (
                                      <Badge className="bg-purple-100 text-purple-700 border-purple-200 text-xs">
                                        🎯 Marker
                                      </Badge>
                                    ) : paper.processor_used === 'mineru' || paper.processor_used === 'mineru_service' ? (
                                      <Badge className="bg-blue-100 text-blue-700 border-blue-200 text-xs">
                                        ⛏️ MinerU
                                      </Badge>
                                    ) : paper.processor_used === 'pix2text' ? (
                                      <Badge className="bg-green-100 text-green-700 border-green-200 text-xs">
                                        🖼️ Pix2Text
                                      </Badge>
                                    ) : (
                                      <Badge className="bg-purple-100 text-purple-700 border-purple-200 text-xs">
                                        {paper.processor_used.replace('_', ' ').replace('service', '').trim()}
                                      </Badge>
                                    )}
                                    
                                    {/* Show reprocess buttons for all papers */}
                                    <div className="flex gap-1">
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={async (e) => {
                                              e.stopPropagation()
                                              setProcessingPapers(prev => new Set(prev).add(paper.id))
                                              setProcessingMessage(`Processing paper ${paper.id} with Marker...`)
                                              try {
                                                const response = await axios.post(`http://localhost:8000/api/papers/${paper.id}/process`)
                                                if (response.data.success) {
                                                  setProcessingMessage(`Successfully started processing paper ${paper.id}`)
                                                  // Refresh the papers list to show processing state
                                                  await loadPapers()
                                                  await loadFacets()
                                                } else {
                                                  setProcessingMessage(response.data.message || 'Failed to start processing')
                                                  console.error('Processing failed:', response.data)
                                                }
                                              } catch (error: any) {
                                                const errorMsg = error.response?.data?.detail || error.message || 'Failed to start processing'
                                                setProcessingMessage(`Error: ${errorMsg}`)
                                                console.error('Failed to start processing:', error)
                                              } finally {
                                                setProcessingPapers(prev => {
                                                  const newSet = new Set(prev)
                                                  newSet.delete(paper.id)
                                                  return newSet
                                                })
                                                // Clear message after 3 seconds
                                                setTimeout(() => setProcessingMessage(null), 3000)
                                              }
                                            }}
                                            disabled={processingPapers.has(paper.id)}
                                            className="h-5 px-2 text-xs"
                                            title="Reprocess with Marker service for better quality"
                                          >
                                            {processingPapers.has(paper.id) ? (
                                              <>
                                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                                Processing...
                                              </>
                                            ) : (
                                              <>
                                                <RotateCcw className="h-3 w-3 mr-1" />
                                                Use Marker
                                              </>
                                            )}
                                          </Button>
                                          <Button
                                            size="sm"
                                            variant="outline"
                                            onClick={async (e) => {
                                              e.stopPropagation()
                                              setProcessingPapers(prev => new Set(prev).add(paper.id))
                                              setProcessingMessage(`Processing paper ${paper.id} with MinerU...`)
                                              try {
                                                const response = await axios.post(`http://localhost:8000/api/papers/${paper.id}/process-mineru`)
                                                if (response.data.success) {
                                                  setProcessingMessage(`Successfully started processing paper ${paper.id} with MinerU`)
                                                  // Refresh the papers list to show processing state
                                                  await loadPapers()
                                                  await loadFacets()
                                                } else {
                                                  setProcessingMessage(response.data.message || 'Failed to start MinerU processing')
                                                  console.error('MinerU processing failed:', response.data)
                                                }
                                              } catch (error: any) {
                                                const errorMsg = error.response?.data?.detail || error.message || 'Failed to start MinerU processing'
                                                setProcessingMessage(`Error: ${errorMsg}`)
                                                console.error('Failed to start MinerU processing:', error)
                                              } finally {
                                                setProcessingPapers(prev => {
                                                  const newSet = new Set(prev)
                                                  newSet.delete(paper.id)
                                                  return newSet
                                                })
                                                // Clear message after 3 seconds
                                                setTimeout(() => setProcessingMessage(null), 3000)
                                              }
                                            }}
                                            disabled={processingPapers.has(paper.id)}
                                            className="h-5 px-2 text-xs"
                                            title="Reprocess with MinerU service for math-heavy PDFs"
                                          >
                                            {processingPapers.has(paper.id) ? (
                                              <>
                                                <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                                Processing...
                                              </>
                                            ) : (
                                              <>
                                                <RotateCcw className="h-3 w-3 mr-1" />
                                                Use MinerU
                                              </>
                                            )}
                                          </Button>
                                        </div>
                                  </div>
                                )}
                                
                                {/* Abstract - More compact with 2 lines */}
                                {paper.abstract && (
                                  <p className="text-xs text-gray-600 mb-2 line-clamp-3">
                                    {paper.abstract}
                                  </p>
                                )}
                                
                                {/* Mollick-Style Summary - Foldable with Edit */}
                                {paper.analyses && (() => {
                                  const mollickSummary = paper.analyses.find((a: any) => 
                                    a.analysis_type === 'mollick_summary' || 
                                    a.analysis_name === 'mollick_summary' ||
                                    a.type === 'mollick_summary'
                                  );
                                  if (!mollickSummary) return null;
                                  
                                  const paperId = paper.id.toString();
                                  const isExpanded = expandedSummaries.has(paperId);
                                  const isEditing = editingSummaries.has(paperId);
                                  const isSaving = savingSummaries.has(paperId);
                                  const summaryContent = mollickSummary.content || mollickSummary.analysis_content || '';
                                  
                                  return (
                                    <div className="mb-2 border-l-2 border-purple-200 pl-2">
                                      <div className="flex items-center justify-between">
                                        <button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            setExpandedSummaries(prev => {
                                              const newSet = new Set(prev);
                                              if (isExpanded) {
                                                newSet.delete(paperId);
                                              } else {
                                                newSet.add(paperId);
                                              }
                                              return newSet;
                                            });
                                          }}
                                          className="flex items-center gap-1 text-xs font-medium text-purple-700 hover:text-purple-900 transition-colors"
                                        >
                                          {isExpanded ? (
                                            <ChevronDown className="h-3 w-3" />
                                          ) : (
                                            <ChevronRight className="h-3 w-3" />
                                          )}
                                          <span>Mollick-Style Summary</span>
                                          <Badge variant="outline" className="h-4 px-1 text-[10px] bg-purple-50 border-purple-200">
                                            AI
                                          </Badge>
                                        </button>
                                        
                                        {isExpanded && !isEditing && (
                                          <Button
                                            size="sm"
                                            variant="ghost"
                                            className="h-5 px-1 mr-1"
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              startEditingSummary(paperId, summaryContent);
                                            }}
                                            title="Edit summary"
                                          >
                                            <Edit2 className="h-3 w-3 text-purple-600" />
                                          </Button>
                                        )}
                                      </div>
                                      
                                      {isExpanded && (
                                        <div className="mt-1 text-xs text-gray-700 bg-purple-50 rounded p-2">
                                          {isEditing ? (
                                            <div className="space-y-2">
                                              <Textarea
                                                value={editedSummaryContent[paperId] || ''}
                                                onChange={(e) => {
                                                  setEditedSummaryContent(prev => ({
                                                    ...prev,
                                                    [paperId]: e.target.value
                                                  }));
                                                }}
                                                className="min-h-[200px] text-xs bg-white"
                                                onClick={(e) => e.stopPropagation()}
                                              />
                                              <div className="flex gap-2 justify-end">
                                                <Button
                                                  size="sm"
                                                  variant="outline"
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    cancelEditingSummary(paperId);
                                                  }}
                                                  disabled={isSaving}
                                                  className="h-6 px-2 text-xs"
                                                >
                                                  <CancelIcon className="h-3 w-3 mr-1" />
                                                  Cancel
                                                </Button>
                                                <Button
                                                  size="sm"
                                                  onClick={(e) => {
                                                    e.stopPropagation();
                                                    saveSummaryEdit(paperId);
                                                  }}
                                                  disabled={isSaving}
                                                  className="h-6 px-2 text-xs bg-purple-600 hover:bg-purple-700 text-white"
                                                >
                                                  {isSaving ? (
                                                    <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                                                  ) : (
                                                    <Save className="h-3 w-3 mr-1" />
                                                  )}
                                                  Save
                                                </Button>
                                              </div>
                                            </div>
                                          ) : (
                                            <div className="prose prose-sm max-w-none markdown-content">
                                              <ReactMarkdown
                                                components={{
                                                  h1: ({children}) => <h1 className="text-base font-bold mt-2 mb-1">{children}</h1>,
                                                  h2: ({children}) => <h2 className="text-sm font-bold mt-2 mb-1">{children}</h2>,
                                                  h3: ({children}) => <h3 className="text-xs font-bold mt-1 mb-1">{children}</h3>,
                                                  p: ({children}) => <p className="text-xs mb-1">{children}</p>,
                                                  ul: ({children}) => <ul className="text-xs list-disc ml-4 mb-1">{children}</ul>,
                                                  ol: ({children}) => <ol className="text-xs list-decimal ml-4 mb-1">{children}</ol>,
                                                  li: ({children}) => <li className="mb-0.5">{children}</li>,
                                                  strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                                                  em: ({children}) => <em className="italic">{children}</em>,
                                                }}
                                              >
                                                {summaryContent || 'Loading summary...'}
                                              </ReactMarkdown>
                                            </div>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  );
                                })()}
                                
                                {/* Compact Metrics Row */}
                                <div className="flex flex-wrap items-center gap-1.5 mb-2 text-xs">
                                  {/* Readability - Ultra compact */}
                                  {paper.readability?.difficulty && (
                                    <Badge 
                                      variant="outline"
                                      className="h-5 px-1.5 text-[10px] border-purple-200 bg-purple-50 text-purple-700"
                                      title={`Flesch Reading Ease: ${paper.readability.flesch_reading_ease || 'N/A'}`}
                                    >
                                      {paper.readability.difficulty}
                                    </Badge>
                                  )}
                                  {paper.readability?.academic_level && (
                                    <Badge 
                                      variant="outline"
                                      className="h-5 px-1.5 text-[10px] border-gray-200 bg-gray-50 text-gray-700"
                                    >
                                      <GraduationCap className="h-2.5 w-2.5 inline mr-0.5" />
                                      {paper.readability.academic_level.replace(' Level', '')}
                                    </Badge>
                                  )}
                                  
                                  {/* Document Size - Ultra compact */}
                                  {paper.word_count && paper.word_count > 0 && (
                                    <span className="text-gray-500">
                                      {paper.word_count.toLocaleString()} words
                                    </span>
                                  )}
                                  
                                  {/* Conference and Date inline */}
                                  {paper.conference && (
                                    <Badge variant="outline" className="h-5 px-1.5 text-[10px] border-blue-200 bg-blue-50 text-blue-700">
                                      {paper.conference}
                                    </Badge>
                                  )}
                                  {(paper.publication_date || paper.year) && (
                                    <span className="text-gray-500">
                                      <Calendar className="h-2.5 w-2.5 inline mr-0.5" />
                                      {paper.publication_date ? formatDate(paper.publication_date) : paper.year}
                                    </span>
                                  )}
                                </div>
                                
                                {/* Tags Section - Ultra compact inline */}
                                {(paper.tags?.length > 0 || paper.concepts?.length > 0) && (
                                  <div className="flex flex-wrap items-center gap-1 mb-2">
                                    <TagIcon className="h-3 w-3 text-gray-400" />
                                    <span className="text-[10px] font-medium text-gray-500 mr-1">
                                      {paper.tags?.length || paper.concepts?.length || 0}
                                    </span>
                                      {(paper.tags || paper.concepts || [])
                                        .slice(0, expandedTags.has(paper.id) ? undefined : 6)
                                        .map((item, index) => {
                                        const tagName = typeof item === 'string' ? item : item.display_name
                                        const tagId = typeof item === 'string' ? item : item.concept_id
                                        return (
                                          <Badge 
                                            key={`${paper.id}-tag-${index}`} 
                                            variant="outline" 
                                            className={`h-5 px-1.5 text-[10px] cursor-pointer transition-colors hover:bg-gray-100 ${
                                              getTagColor(tagName, index)
                                            }`}
                                            onClick={() => {
                                              setSelectedTags(new Set([tagId]))
                                              setCurrentPage(1)
                                            }}
                                            title={`Filter by: ${tagName}`}
                                          >
                                            {tagName}
                                          </Badge>
                                        )
                                      })}
                                      {((paper.tags?.length || paper.concepts?.length || 0) > 6) && !expandedTags.has(paper.id) && (
                                        <Badge 
                                          variant="outline" 
                                          className="h-5 px-1.5 text-[10px] text-gray-500 border-dashed hover:bg-gray-50 cursor-pointer"
                                          title={`Click to show ${((paper.tags?.length || paper.concepts?.length || 0) - 6)} more tags`}
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            toggleExpandedTags(paper.id)
                                          }}
                                        >
                                          +{((paper.tags?.length || paper.concepts?.length || 0) - 6)}
                                        </Badge>
                                      )}
                                      {expandedTags.has(paper.id) && ((paper.tags?.length || paper.concepts?.length || 0) > 6) && (
                                        <button
                                          className="text-[10px] text-gray-500 hover:text-gray-700 ml-1"
                                          onClick={(e) => {
                                            e.stopPropagation()
                                            toggleExpandedTags(paper.id)
                                          }}
                                        >
                                          less
                                        </button>
                                      )}
                                  </div>
                                )}
                                
                                {/* Added date at the bottom */}
                                <div className="flex items-center gap-2 text-[10px] text-gray-400">
                                  <Clock className="h-2.5 w-2.5" />
                                  <span>Added: {formatDate(paper.created_at)}</span>
                                </div>
                              </div>
                            </div>
                            
                            {/* Foldable AI Summary Section */}
                            {paper.ai_summary && (
                              <div className="mt-4 pt-4 border-t">
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    toggleSummary(paper.id)
                                  }}
                                  className="flex items-center gap-2 text-sm font-medium text-gray-700 hover:text-blue-600 transition-colors w-full text-left"
                                >
                                  <span className="text-purple-600">🎓</span>
                                  <span>Mollick-Style Summary</span>
                                  {expandedSummaries.has(paper.id) ? (
                                    <ChevronUp className="h-4 w-4 ml-auto" />
                                  ) : (
                                    <ChevronDown className="h-4 w-4 ml-auto" />
                                  )}
                                </button>
                                {expandedSummaries.has(paper.id) && (
                                  <div className="mt-3 p-3 bg-purple-50 rounded-lg">
                                    <div className="prose prose-sm max-w-none">
                                      <p className="text-sm text-gray-700 whitespace-pre-wrap">{paper.ai_summary}</p>
                                    </div>
                                    {paper.key_findings && (
                                      <div className="mt-3 pt-3 border-t border-purple-100">
                                        <h4 className="text-xs font-semibold text-purple-700 mb-2">Key Findings:</h4>
                                        <ul className="list-disc list-inside text-xs text-gray-600 space-y-1">
                                          {paper.key_findings.map((finding: string, idx: number) => (
                                            <li key={idx}>{finding}</li>
                                          ))}
                                        </ul>
                                      </div>
                                    )}
                                  </div>
                                )}
                              </div>
                            )}
                            
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
                      <div className="flex items-center justify-between bg-white rounded-lg p-4">
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
        </div>
      </div>
      
      {/* Right Sidebar - Concepts */}
      <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
        <div className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <TagIcon className="h-5 w-5 text-gray-700" />
              <h2 className="text-lg font-semibold text-gray-900">Concepts</h2>
            </div>
            <div className="flex items-center gap-1">
              {selectedTags.size > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => {
                    setSelectedTags(new Set())
                    setCurrentPage(1)
                  }}
                  className="h-7 px-2 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              )}
              <Button
                size="sm"
                variant={showHierarchy ? "default" : "outline"}
                onClick={() => setShowHierarchy(!showHierarchy)}
                className="h-7 px-2"
                title={showHierarchy ? "Show flat list" : "Show hierarchy"}
              >
                {showHierarchy ? <Layers className="h-3 w-3" /> : <Hash className="h-3 w-3" />}
              </Button>
            </div>
          </div>
          
          {/* Semantic Concept Search */}
          <div className="mb-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="Search concepts semantically..."
                value={conceptSearch}
                onChange={(e) => setConceptSearch(e.target.value)}
                className="pl-9 pr-3 h-9 text-sm"
              />
            </div>
          </div>
          
          <div className="space-y-2">
            {loadingFacets ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : facets && facets.concepts && facets.concepts.length > 0 ? (
              <ScrollArea className="h-[calc(100vh-240px)]">
                <div className="space-y-1 pr-4">
                  {facets.concepts
                    .filter(concept => 
                      !conceptSearch || 
                      concept.display_name.toLowerCase().includes(conceptSearch.toLowerCase())
                    )
                    .map((concept, index) => (
                    <label
                      key={concept.concept_id || concept.id || `${concept.slug}-${index}`}
                      className="flex items-start gap-2 px-3 py-1 hover:bg-blue-50 cursor-pointer rounded-lg transition-colors"
                    >
                      <Checkbox
                        checked={selectedTags.has(concept.concept_id || concept.slug)}
                        onCheckedChange={() => toggleFacetValue('tag', concept.concept_id || concept.slug)}
                        className="mt-0.5"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-sm text-blue-800 bg-blue-50 px-2 py-0.5 rounded break-words" 
                                title={concept.display_name}>
                            {concept.display_name}
                          </span>
                          <Badge 
                            variant="outline" 
                            className="text-xs shrink-0 bg-blue-100 text-blue-700 border-blue-200">
                            {concept.count}
                          </Badge>
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              </ScrollArea>
            ) : (
              <div className="text-sm text-gray-400 text-center py-8">
                No concepts found
              </div>
            )}
          </div>
        </div>
      </div>
      
      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-auto shadow-2xl">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Upload PDF Paper</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setShowUploadModal(false)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <PaperUploadModern onUploadComplete={() => {
                handleUploadComplete()
                setShowUploadModal(false)
              }} />
            </div>
          </div>
        </div>
      )}
      
      {/* Paper Viewer Modal */}
      {selectedPaperId && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-7xl max-h-[90vh] overflow-auto shadow-2xl">
            <PaperViewerOptimized 
              paperId={selectedPaperId} 
              onClose={() => setSelectedPaperId(null)}
              onMetadataUpdate={async () => {
                // Update the specific paper in the list without full reload
                try {
                  const response = await axios.get(`http://localhost:8000/api/papers/${selectedPaperId}`)
                  const updatedPaper = response.data
                  
                  // Update the paper in the papers list
                  setPapers(prevPapers => 
                    prevPapers.map(p => 
                      p.id === selectedPaperId 
                        ? { ...p, tags: updatedPaper.tags, ...updatedPaper }
                        : p
                    )
                  )
                  
                  // Only refresh facets and stats to update counts
                  loadFacets()
                  loadStats()
                } catch (error) {
                  console.error('Error updating paper:', error)
                }
              }}
            />
          </div>
        </div>
      )}
      
      {/* Paper Tag Suggestion Modal */}
      {selectedPaperForTags && (
        <PaperTagSuggestionModal
          paper={selectedPaperForTags}
          isOpen={showTagSuggestionModal}
          onClose={() => {
            setShowTagSuggestionModal(false)
            setSelectedPaperForTags(null)
          }}
          onTagsUpdated={() => {
            loadPapers()
            loadFacets()
          }}
        />
      )}
      
      {/* Unified Import Dialog */}
      <UnifiedImportDialog
        isOpen={showImportDialog}
        onClose={() => setShowImportDialog(false)}
        onImportSuccess={(paperId) => {
          loadPapers()
          loadStats()
          loadFacets()
          setSelectedPaperId(paperId)
        }}
      />
    </div>
  )
}

export default FacetedPapersDashboard