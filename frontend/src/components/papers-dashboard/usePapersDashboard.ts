/**
 * Custom hook for the Papers Dashboard.
 *
 * Manages:
 *   - All filter state (search, authors, tags, conferences, years, etc.)
 *   - Data fetching (papers, facets, stats)
 *   - Pagination and sorting
 *   - Paper actions (flag, rate, delete, process)
 *   - Summary editing state
 */
import { useState, useEffect, useCallback } from 'react'
import http from '@/services/http'
import type { Paper, PapersStats, Facets } from './types'

export function usePapersDashboard(paperType: string = 'research') {
  // ---- Core data ----
  const [papers, setPapers] = useState<Paper[]>([])
  const [stats, setStats] = useState<PapersStats | null>(null)
  const [facets, setFacets] = useState<Facets | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingFacets, setLoadingFacets] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // ---- UI state ----
  const [selectedPaperId, setSelectedPaperId] = useState<number | string | null>(null)
  const [searchMode, setSearchMode] = useState<'standard' | 'content' | 'semantic'>('standard')
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showImportDialog, setShowImportDialog] = useState(false)
  const [processingPapers, setProcessingPapers] = useState<Set<number>>(new Set())
  const [processingMessage, setProcessingMessage] = useState<string | null>(null)
  const [showTagSuggestionModal, setShowTagSuggestionModal] = useState(false)
  const [selectedPaperForTags, setSelectedPaperForTags] = useState<any | null>(null)

  // ---- Filters ----
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

  // ---- Special filters ----
  const [showFlagged, setShowFlagged] = useState<boolean | null>(null)
  const [showNoProcessor, setShowNoProcessor] = useState(false)
  const [showNoYear, setShowNoYear] = useState(false)
  const [showNoConference, setShowNoConference] = useState(false)
  const [showNoAffiliation, setShowNoAffiliation] = useState(false)
  const [showNoAnnotations, setShowNoAnnotations] = useState(false)
  const [showNoMollickSummary, setShowNoMollickSummary] = useState(false)

  // ---- Rating filters ----
  const [selectedRating, setSelectedRating] = useState<number | null>(null)
  const [minRating, setMinRating] = useState<number | null>(null)
  const [showUnratedOnly, setShowUnratedOnly] = useState(false)

  // ---- Facet UI state ----
  const [expandedFacets, setExpandedFacets] = useState<Set<string>>(new Set(['authors', 'concepts', 'years', 'special']))
  const [expandedSummaries, setExpandedSummaries] = useState<Set<string>>(new Set())
  const [editingSummaries, setEditingSummaries] = useState<Set<string>>(new Set())
  const [editedSummaryContent, setEditedSummaryContent] = useState<Record<string, string>>({})
  const [savingSummaries, setSavingSummaries] = useState<Set<string>>(new Set())
  const [expandedTags, setExpandedTags] = useState<Set<number>>(new Set())

  // ---- Pagination ----
  const [currentPage, setCurrentPage] = useState(1)
  const [totalPapers, setTotalPapers] = useState(0)
  const pageSize = 20
  const totalPages = Math.ceil(totalPapers / pageSize)

  // ---- Active filter count ----
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

  // ================= Data Fetching =================

  const loadFacets = useCallback(async () => {
    setLoadingFacets(true)
    try {
      const params = new URLSearchParams()
      if (searchTerm) {
        params.append('search', searchTerm)
        const backendMode = searchMode === 'standard' ? 'title' : searchMode === 'content' ? 'content' : 'all'
        params.append('search_mode', backendMode)
      }
      if (selectedAuthors.size === 1) params.append('author', Array.from(selectedAuthors)[0])
      if (selectedTags.size > 0) {
        Array.from(selectedTags).forEach(conceptId => {
          params.append('concept_ids', conceptId)
        })
      }
      selectedConferences.forEach(conf => params.append('conferences', conf))
      selectedYears.forEach(year => params.append('years', year.toString()))
      selectedAffiliations.forEach(affil => params.append('affiliations', affil))
      selectedProcessors.forEach(proc => params.append('processors', proc))

      params.append('paper_type', paperType)
      const response = await http.get(`/api/papers/facets?${params}`)
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
          id: f.concept_id || f.id || f.display_name
        })) || [],
        concepts: facetsData.concepts || [],
        affiliations: facetsData.institutions?.map((f: any) => ({ value: f.name, count: f.count, label: f.name })) || [],
        processors: facetsData.processors?.map((f: any) => ({ value: f.name, count: f.count, label: f.name })) || [],
        special_filters: facetsData.special_filters?.map((f: any) => ({ value: f.name, count: f.count, label: f.label })) || [],
        missing_data: facetsData.missing_data,
        paper_status: facetsData.paper_status,
        rating: facetsData.rating
      })
    } catch (err: any) {
      console.error('Failed to load facets:', err)
      setFacets({
        authors: [], conferences: [], journals: [], years: [], tags: [],
        concepts: [], affiliations: [], processors: [], special_filters: [],
        missing_data: undefined, paper_status: undefined, rating: undefined
      })
    } finally {
      setLoadingFacets(false)
    }
  }, [searchTerm, searchMode, selectedAuthors, selectedTags, selectedConferences, selectedYears, selectedAffiliations, selectedProcessors, paperType])

  const loadPapers = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const params = new URLSearchParams({
        page: currentPage.toString(),
        page_size: pageSize.toString()
      })
      params.append('paper_type', paperType)
      if (searchTerm) {
        params.append('search', searchTerm)
        const backendMode = searchMode === 'standard' ? 'title' : searchMode === 'content' ? 'content' : 'all'
        params.append('search_mode', backendMode)
      }
      if (selectedAuthors.size === 1) params.append('author', Array.from(selectedAuthors)[0])
      if (selectedTags.size > 0) {
        Array.from(selectedTags).forEach(conceptId => {
          params.append('concept_ids', conceptId)
        })
      }
      selectedConferences.forEach(conf => params.append('conferences', conf))
      selectedYears.forEach(year => params.append('years', year.toString()))
      selectedAffiliations.forEach(affil => params.append('affiliations', affil))
      selectedProcessors.forEach(proc => params.append('processors', proc))
      if (showFlagged !== null) params.append('is_flagged', showFlagged.toString())
      if (showNoProcessor) params.append('no_processor', 'true')
      if (showNoYear) params.append('no_year', 'true')
      if (showNoConference) params.append('no_conference', 'true')
      if (showNoAffiliation) params.append('no_affiliation', 'true')
      if (showNoAnnotations) params.append('no_annotations', 'true')
      if (showNoMollickSummary) params.append('no_mollick_summary', 'true')
      if (selectedRating !== null) params.append('rating', selectedRating.toString())
      if (minRating !== null) params.append('min_rating', minRating.toString())
      if (showUnratedOnly) params.append('unrated_only', 'true')
      params.append('sort_by', sortBy)
      params.append('sort_order', sortOrder)

      const response = await http.get(`/api/papers/?${params}`)
      const papersData = Array.isArray(response.data) ? response.data : (response.data.papers || [])
      setPapers(papersData)
      setTotalPapers(response.data.total || papersData.length)
    } catch (err: any) {
      setError('Failed to load papers: ' + (err.response?.data?.detail || err.message))
    } finally {
      setLoading(false)
    }
  }, [searchTerm, searchMode, selectedAuthors, selectedTags, selectedConferences, selectedYears, selectedAffiliations, selectedProcessors, currentPage, sortBy, sortOrder, showFlagged, showNoProcessor, showNoYear, showNoConference, showNoAffiliation, showNoAnnotations, showNoMollickSummary, selectedRating, minRating, showUnratedOnly, paperType])

  const loadStats = useCallback(async () => {
    try {
      const response = await http.get(`/api/papers/stats/overview?paper_type=${paperType}`)
      setStats(response.data)
    } catch (err: any) {
      console.error('Failed to load stats:', err)
    }
  }, [paperType])

  // ================= Effects =================

  useEffect(() => {
    loadStats()
    loadFacets()
    loadPapers()
  }, [loadStats, loadFacets, loadPapers, selectedTags, selectedAuthors, selectedConferences, selectedYears, selectedAffiliations, selectedProcessors, searchTerm, currentPage, sortBy, sortOrder, showFlagged, showNoProcessor, showNoYear, showNoConference, showNoAffiliation, showNoAnnotations, showNoMollickSummary, selectedRating, minRating, showUnratedOnly])

  useEffect(() => {
    if (processingPapers.size > 0) {
      const interval = setInterval(() => {
        loadPapers()
        loadFacets()
      }, 5000)
      return () => clearInterval(interval)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [processingPapers.size])

  // ================= Actions =================

  const handleUploadComplete = () => {
    loadStats()
    loadPapers()
    loadFacets()
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

  const toggleFacet = (facetName: string) => {
    const newExpanded = new Set(expandedFacets)
    if (newExpanded.has(facetName)) {
      newExpanded.delete(facetName)
    } else {
      newExpanded.add(facetName)
    }
    setExpandedFacets(newExpanded)
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
      if (facetType !== 'tag') {
        newSet.clear()
      }
      newSet.add(value)
    }
    setter(newSet)
    setCurrentPage(1)
  }

  const togglePaperFlag = async (paperId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    const paper = papers.find(p => p.id === paperId)
    if (!paper) return
    try {
      const response = await http.post(`/api/papers/${paperId}/flag`, {
        is_flagged: !paper.is_flagged
      })
      setPapers(papers.map(p =>
        p.id === paperId
          ? { ...p, is_flagged: response.data.is_flagged }
          : p
      ))
    } catch (err: any) {
      console.error('Failed to toggle flag:', err)
    }
  }

  const handleRatePaper = async (paperId: number | string, rating: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    try {
      await http.patch(`/api/papers/${paperId}/rating`, null, {
        params: { rating }
      })
      setPapers(papers.map(p =>
        (p.id === paperId || String(p.id) === String(paperId))
          ? { ...p, user_rating: rating === 0 ? undefined : rating }
          : p
      ))
      loadFacets()
    } catch (err: any) {
      console.error('Failed to set rating:', err)
    }
  }

  const handleDeletePaper = async (paperId: number, e: React.MouseEvent) => {
    e.stopPropagation()
    if (!window.confirm('Are you sure you want to delete this paper? This action cannot be undone.')) {
      return
    }
    try {
      await http.delete(`/api/papers/${paperId}`)
      loadPapers()
      loadStats()
      loadFacets()
    } catch (error) {
      console.error('Error deleting paper:', error)
      setError('Failed to delete paper')
    }
  }

  const handleProcessPaper = async (paperId: number, processor: 'marker' | 'mineru' = 'marker', e?: React.MouseEvent) => {
    if (e) e.stopPropagation()
    setProcessingPapers(prev => new Set(prev).add(paperId))
    const processorLabel = processor === 'mineru' ? 'MinerU' : 'Marker'
    setProcessingMessage(`Processing paper ${paperId} with ${processorLabel}...`)
    try {
      const endpoint = processor === 'mineru'
        ? `/api/papers/${paperId}/process-mineru`
        : `/api/papers/${paperId}/process`
      const response = await http.post(endpoint)
      if (response.data.success) {
        setProcessingMessage(`Successfully started processing paper ${paperId}`)
        await loadPapers()
        await loadFacets()
      } else {
        setProcessingMessage(response.data.message || `Failed to start ${processorLabel} processing`)
        console.error(`${processorLabel} processing failed:`, response.data)
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || error.message || `Failed to start ${processorLabel} processing`
      setProcessingMessage(`Error: ${errorMsg}`)
      console.error(`Failed to start ${processorLabel} processing:`, error)
    } finally {
      setProcessingPapers(prev => {
        const newSet = new Set(prev)
        newSet.delete(paperId)
        return newSet
      })
      setTimeout(() => setProcessingMessage(null), 3000)
    }
  }

  // ================= Summary editing =================

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
      await http.put(
        `/api/papers/${paperId}/analyses/generated/mollick_summary`,
        { content }
      )
      setPapers(prev => prev.map(p => {
        if (String(p.id) === String(paperId) && p.analyses) {
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
      window.dispatchEvent(new CustomEvent('paperAnalysisUpdated', {
        detail: { paperId, analysisType: 'mollick_summary', content }
      }))
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    })
  }

  return {
    // Core data
    papers, setPapers, stats, facets, loading, loadingFacets, error, setError,

    // Data fetching
    loadPapers, loadFacets, loadStats,

    // UI state
    selectedPaperId, setSelectedPaperId,
    searchMode, setSearchMode,
    showUploadModal, setShowUploadModal,
    showImportDialog, setShowImportDialog,
    processingPapers, setProcessingPapers,
    processingMessage, setProcessingMessage,
    showTagSuggestionModal, setShowTagSuggestionModal,
    selectedPaperForTags, setSelectedPaperForTags,

    // Filters
    searchTerm, setSearchTerm,
    selectedAuthors, setSelectedAuthors,
    selectedTags, setSelectedTags,
    conceptSearch, setConceptSearch,
    showHierarchy, setShowHierarchy,
    selectedConferences, setSelectedConferences,
    selectedYears, setSelectedYears,
    selectedAffiliations, setSelectedAffiliations,
    selectedProcessors, setSelectedProcessors,
    sortBy, setSortBy,
    sortOrder, setSortOrder,

    // Special filters
    showFlagged, setShowFlagged,
    showNoProcessor, setShowNoProcessor,
    showNoYear, setShowNoYear,
    showNoConference, setShowNoConference,
    showNoAffiliation, setShowNoAffiliation,
    showNoAnnotations, setShowNoAnnotations,
    showNoMollickSummary, setShowNoMollickSummary,

    // Rating filters
    selectedRating, setSelectedRating,
    minRating, setMinRating,
    showUnratedOnly, setShowUnratedOnly,

    // Facet UI state
    expandedFacets, toggleFacet,
    expandedSummaries, setExpandedSummaries, toggleSummary,
    editingSummaries, editedSummaryContent, setEditedSummaryContent,
    savingSummaries,
    expandedTags, toggleExpandedTags,
    startEditingSummary, cancelEditingSummary, saveSummaryEdit,

    // Pagination
    currentPage, setCurrentPage, totalPapers, pageSize, totalPages,

    // Computed
    activeFilterCount,

    // Actions
    handleUploadComplete,
    clearAllFilters,
    toggleFacetValue,
    togglePaperFlag,
    handleRatePaper,
    handleDeletePaper,
    handleProcessPaper,
    formatDate,
  }
}
