import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Progress } from "@/components/ui/progress"
import {
  Search,
  User,
  Tag,
  Calendar,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Twitter,
  RefreshCw,
  GitBranch,
  Layers,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
  Sparkles,
  X,
  CheckCircle2,
  AlertCircle
} from 'lucide-react'
import TweetCardModern from './TweetCardModern'
import TagSuggestionModalModern from './TagSuggestionModalModern'
import SemanticConceptSearch from './SemanticConceptSearch'
import UnifiedModelSelector from './UnifiedModelSelector'
import { cn } from "@/lib/utils"
import { Concept } from '@/types/concept'
import conceptService from '@/services/conceptService'

interface AuthorFacet {
  username: string
  name?: string
  count: number
}

interface YearFacet {
  year: number
  count: number
}

interface AnnotationFacet {
  status: string
  label: string
  count: number
}

interface Tweet {
  id: string
  text: string
  author_id: string
  author_username: string
  author_name?: string
  tags?: any
  concepts?: Concept[]
  created_at: string
  is_retweet?: boolean
  like_count?: number
  retweet_count?: number
  reply_count?: number
  metrics?: {
    // API returns these fields
    like_count?: number
    retweet_count?: number
    reply_count?: number
    quote_count?: number
    // Transformed to these for display
    likes: number
    retweets: number
    replies: number
    quotes?: number
  }
  media?: Array<{
    type: string
    url: string
    thumbnail_url?: string
  }>
}

interface ConceptFacet {
  concept_id: string
  id?: string
  slug: string
  display_name: string
  count: number
  aggregate_count?: number
  entity_type?: string
  children?: ConceptFacet[]
  parents?: string[]
}

interface FacetedSearchResponse {
  tweets: Tweet[]
  facets: {
    authors: AuthorFacet[]
    concepts: ConceptFacet[]
    years?: YearFacet[]
    annotation_status?: AnnotationFacet[]
  }
  total: number
  page: number
  page_size: number
}

export default function FacetedTweetsDashboardModern() {
  const [tweets, setTweets] = useState<Tweet[]>([])
  const [facets, setFacets] = useState<{ authors: AuthorFacet[]; concepts: ConceptFacet[]; years: YearFacet[]; annotation_status: AnnotationFacet[] }>({
    authors: [],
    concepts: [],
    years: [],
    annotation_status: []
  })
  const [hierarchyFacets, setHierarchyFacets] = useState<ConceptFacet[]>([])
  const [selectedAuthors, setSelectedAuthors] = useState<string[]>([])
  const [selectedConcepts, setSelectedConcepts] = useState<string[]>([])
  const [selectedYears, setSelectedYears] = useState<number[]>([])
  const [selectedAnnotationStatus, setSelectedAnnotationStatus] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [excludeRetweets, setExcludeRetweets] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalTweets, setTotalTweets] = useState(0)
  const [loading, setLoading] = useState(false)
  const [showHierarchy, setShowHierarchy] = useState(false)
  const [expandedConcepts, setExpandedConcepts] = useState<Set<string>>(new Set())
  const [selectedTweet, setSelectedTweet] = useState<Tweet | null>(null)
  const [showSuggestionModal, setShowSuggestionModal] = useState(false)
  const [showAllConcepts, setShowAllConcepts] = useState(false)
  const [_savedScrollPosition, setSavedScrollPosition] = useState<number>(0)

  // Batch annotation state
  const [batchAnnotating, setBatchAnnotating] = useState(false)
  const [_batchTaskId, setBatchTaskId] = useState<string | null>(null)
  const [batchProgress, setBatchProgress] = useState(0)
  const [batchModel, setBatchModel] = useState<string>('')
  const [batchResult, setBatchResult] = useState<{
    status: 'idle' | 'running' | 'completed' | 'error'
    newTagsCount?: number
    skippedCount?: number
    errorCount?: number
    message?: string
  }>({ status: 'idle' })
  const batchPollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // "Annotate All Unannotated" state with localStorage persistence
  const [annotateAllRunning, setAnnotateAllRunning] = useState(false)
  const [annotateAllTaskId, setAnnotateAllTaskId] = useState<string | null>(null)
  const [annotateAllProgress, setAnnotateAllProgress] = useState<{
    processed: number
    total: number
    newTagsCount: number
    progress: number
  }>({ processed: 0, total: 0, newTagsCount: 0, progress: 0 })
  const [annotateAllResult, setAnnotateAllResult] = useState<{
    status: 'idle' | 'running' | 'completed' | 'cancelled' | 'error'
    message?: string
    newTagsCount?: number
    skippedCount?: number
    errorCount?: number
  }>({ status: 'idle' })
  const annotateAllPollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const annotateAllActiveRef = useRef(false)

  const pageSize = 50
  const totalPages = Math.ceil(totalTweets / pageSize)

  useEffect(() => {
    fetchTweets()
  }, [selectedAuthors, selectedConcepts, selectedYears, selectedAnnotationStatus, searchTerm, excludeRetweets, currentPage])

  useEffect(() => {
    if (showHierarchy) {
      fetchHierarchyFacets()
    }
  }, [showHierarchy])

  const fetchTweets = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams()
      params.append('page', currentPage.toString())
      params.append('page_size', pageSize.toString())
      
      if (searchTerm) {
        params.append('search', searchTerm)
      }
      
      if (excludeRetweets) {
        params.append('exclude_retweets', 'true')
      }
      
      selectedAuthors.forEach(author => params.append('authors', author))
      selectedConcepts.forEach(conceptId => params.append('concept_ids', conceptId))
      selectedYears.forEach(year => params.append('years', year.toString()))
      
      // Add annotation status filter
      if (selectedAnnotationStatus.length === 1) {
        params.append('annotation_status', selectedAnnotationStatus[0])
      }
      
      const response = await axios.get<FacetedSearchResponse>(
        `http://localhost:8000/api/tweets/faceted-search?${params.toString()}`
      )
      
      const transformedTweets = response.data.tweets.map(tweet => ({
        ...tweet,
        metrics: tweet.metrics ? {
          likes: tweet.metrics.like_count || 0,
          retweets: tweet.metrics.retweet_count || 0,
          replies: tweet.metrics.reply_count || 0,
          quotes: tweet.metrics.quote_count || 0
        } : {
          likes: 0,
          retweets: 0,
          replies: 0,
          quotes: 0
        },
        tags: tweet.tags ? tweet.tags.map((tag: any) => 
          typeof tag === 'string' ? { tag, type: 'manual' } : tag
        ) : []
      }))
      
      setTweets(transformedTweets)
      setFacets({
        authors: response.data.facets.authors,
        concepts: response.data.facets.concepts,
        years: response.data.facets.years || [],
        annotation_status: response.data.facets.annotation_status || []
      })
      setTotalTweets(response.data.total)
    } catch (error) {
      console.error('Error fetching tweets:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchHierarchyFacets = async () => {
    try {
      const response = await axios.get<any>(
        'http://localhost:8000/api/tweets/hierarchy-facets'
      )
      setHierarchyFacets(response.data.hierarchy || [])
    } catch (error) {
      console.error('Error fetching hierarchy facets:', error)
    }
  }

  const toggleAuthor = (username: string) => {
    setSelectedAuthors(prev => {
      if (prev.includes(username)) {
        return prev.filter(u => u !== username)
      }
      return [...prev, username]
    })
    setCurrentPage(1)
  }

  const toggleYear = (year: number) => {
    setSelectedYears(prev => {
      if (prev.includes(year)) {
        return prev.filter(y => y !== year)
      }
      return [...prev, year]
    })
    setCurrentPage(1)
  }

  const toggleConcept = (conceptId: string) => {
    setSelectedConcepts(prev => {
      if (prev.includes(conceptId)) {
        return prev.filter(c => c !== conceptId)
      }
      return [...prev, conceptId]
    })
    setCurrentPage(1)
  }

  const toggleConceptExpansion = (conceptId: string) => {
    setExpandedConcepts(prev => {
      const newSet = new Set(prev)
      if (newSet.has(conceptId)) {
        newSet.delete(conceptId)
      } else {
        newSet.add(conceptId)
      }
      return newSet
    })
  }



  const handleConceptAdded = async (tweetId: string, concept: Concept) => {
    // Local state update - no full refresh needed
    setTweets(prev => prev.map(tweet =>
      tweet.id === tweetId
        ? { ...tweet, concepts: [...(tweet.concepts || []), concept] }
        : tweet
    ))
  }

  const handleConceptRemoved = async (tweetId: string, conceptId: string) => {
    // Local state update - no full refresh needed
    setTweets(prev => prev.map(tweet =>
      tweet.id === tweetId
        ? { ...tweet, concepts: tweet.concepts?.filter(c => c.concept_id !== conceptId) }
        : tweet
    ))
  }

  const handleSuggestConcepts = (tweet: Tweet) => {
    // Save current scroll position before opening modal
    setSavedScrollPosition(window.scrollY)
    setSelectedTweet(tweet)
    setShowSuggestionModal(true)
  }

  const handleTagsUpdated = async () => {
    // Fetch only the updated tweet - no full refresh needed
    if (selectedTweet) {
      try {
        const response = await axios.get(`http://localhost:8000/api/tweets/${selectedTweet.id}`)
        const updatedTweet = response.data
        setTweets(prev => prev.map(tweet =>
          tweet.id === selectedTweet.id
            ? { ...tweet, concepts: updatedTweet.concepts }
            : tweet
        ))
      } catch (error) {
        console.error('Error fetching updated tweet:', error)
      }
    }
    // No need to restore scroll position - we didn't scroll
  }

  // Batch annotation handlers
  const handleBatchAnnotate = async () => {
    if (!batchModel) {
      setBatchResult({
        status: 'error',
        message: 'Please select a model first'
      })
      return
    }

    if (tweets.length === 0) {
      setBatchResult({
        status: 'error',
        message: 'No tweets to annotate'
      })
      return
    }

    setBatchAnnotating(true)
    setBatchProgress(0)
    setBatchResult({ status: 'running' })

    try {
      // Get all tweet IDs from current filtered view
      const tweetIds = tweets.map(t => t.id)

      const response = await axios.post('http://localhost:8000/api/tweets/batch-annotate', {
        tweet_ids: tweetIds,
        model: batchModel
      })

      setBatchTaskId(response.data.task_id)
      // Start polling for progress
      pollBatchStatus(response.data.task_id)
    } catch (error: any) {
      console.error('Error starting batch annotation:', error)
      setBatchAnnotating(false)
      setBatchResult({
        status: 'error',
        message: error.response?.data?.detail || 'Failed to start batch annotation'
      })
    }
  }

  const pollBatchStatus = (taskId: string) => {
    // Clear any existing polling
    if (batchPollingRef.current) {
      clearInterval(batchPollingRef.current)
    }

    batchPollingRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/tweets/batch-annotate/${taskId}/status`)
        const status = response.data

        setBatchProgress(status.progress)

        if (status.status === 'completed') {
          // Stop polling
          if (batchPollingRef.current) {
            clearInterval(batchPollingRef.current)
            batchPollingRef.current = null
          }

          setBatchAnnotating(false)
          setBatchTaskId(null)
          setBatchResult({
            status: 'completed',
            newTagsCount: status.new_tags_count,
            skippedCount: status.skipped_count,
            errorCount: status.error_count
          })

          // Refresh tweets to show new tags
          fetchTweets()

          // Clear result message after 10 seconds
          setTimeout(() => {
            setBatchResult({ status: 'idle' })
          }, 10000)
        }
      } catch (error: any) {
        console.error('Error polling batch status:', error)
        if (error.response?.status === 404) {
          if (batchPollingRef.current) {
            clearInterval(batchPollingRef.current)
            batchPollingRef.current = null
          }
          setBatchAnnotating(false)
          setBatchTaskId(null)
          setBatchResult({
            status: 'completed',
            message: 'Annotation task finished (backend was restarted)',
          })
          fetchTweets()
          setTimeout(() => setBatchResult({ status: 'idle' }), 10000)
        }
      }
    }, 2000) // Poll every 2 seconds
  }

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (batchPollingRef.current) {
        clearInterval(batchPollingRef.current)
      }
      if (annotateAllPollingRef.current) {
        clearInterval(annotateAllPollingRef.current)
      }
    }
  }, [])

  // Resume "Annotate All" from localStorage on mount
  useEffect(() => {
    const saved = localStorage.getItem('annotateAllProgress')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (parsed.taskId && parsed.isRunning) {
          setAnnotateAllTaskId(parsed.taskId)
          setAnnotateAllRunning(true)
          setAnnotateAllProgress({
            processed: parsed.processed || 0,
            total: parsed.total || 0,
            newTagsCount: parsed.newTagsCount || 0,
            progress: parsed.progress || 0,
          })
          setAnnotateAllResult({ status: 'running' })
          pollAnnotateAllStatus(parsed.taskId)
        }
      } catch {
        localStorage.removeItem('annotateAllProgress')
      }
    }
  }, [])

  // "Annotate All Unannotated" handler
  const handleAnnotateAll = async () => {
    if (!batchModel) {
      setAnnotateAllResult({ status: 'error', message: 'Please select a model first' })
      return
    }
    if (annotateAllActiveRef.current) return
    annotateAllActiveRef.current = true

    setAnnotateAllRunning(true)
    setAnnotateAllProgress({ processed: 0, total: 0, newTagsCount: 0, progress: 0 })
    setAnnotateAllResult({ status: 'running' })

    try {
      const response = await axios.post('http://localhost:8000/api/tweets/batch-annotate-all', {
        model: batchModel
      })

      if (!response.data.task_id) {
        // All already annotated
        setAnnotateAllRunning(false)
        annotateAllActiveRef.current = false
        setAnnotateAllResult({ status: 'completed', message: response.data.message, newTagsCount: 0 })
        setTimeout(() => setAnnotateAllResult({ status: 'idle' }), 10000)
        return
      }

      const taskId = response.data.task_id
      setAnnotateAllTaskId(taskId)
      setAnnotateAllProgress(prev => ({ ...prev, total: response.data.total }))

      // Persist to localStorage
      localStorage.setItem('annotateAllProgress', JSON.stringify({
        taskId,
        total: response.data.total,
        isRunning: true,
        processed: 0,
        newTagsCount: 0,
        progress: 0,
      }))

      pollAnnotateAllStatus(taskId)
    } catch (error: any) {
      console.error('Error starting annotate-all:', error)
      setAnnotateAllRunning(false)
      annotateAllActiveRef.current = false
      setAnnotateAllResult({
        status: 'error',
        message: error.response?.data?.detail || 'Failed to start annotation'
      })
    }
  }

  const resetAnnotateAllState = () => {
    if (annotateAllPollingRef.current) {
      clearInterval(annotateAllPollingRef.current)
      annotateAllPollingRef.current = null
    }
    setAnnotateAllRunning(false)
    setAnnotateAllTaskId(null)
    annotateAllActiveRef.current = false
    localStorage.removeItem('annotateAllProgress')
  }

  const pollAnnotateAllStatus = (taskId: string) => {
    if (annotateAllPollingRef.current) {
      clearInterval(annotateAllPollingRef.current)
    }

    annotateAllPollingRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`http://localhost:8000/api/tweets/batch-annotate/${taskId}/status`)
        const status = response.data

        setAnnotateAllProgress({
          processed: status.processed,
          total: status.total,
          newTagsCount: status.new_tags_count,
          progress: status.progress,
        })

        // Update localStorage
        localStorage.setItem('annotateAllProgress', JSON.stringify({
          taskId,
          total: status.total,
          isRunning: status.status === 'running',
          processed: status.processed,
          newTagsCount: status.new_tags_count,
          progress: status.progress,
        }))

        if (status.status === 'completed' || status.status === 'cancelled') {
          resetAnnotateAllState()

          setAnnotateAllResult({
            status: status.status === 'cancelled' ? 'cancelled' : 'completed',
            newTagsCount: status.new_tags_count,
            skippedCount: status.skipped_count,
            errorCount: status.error_count,
            message: status.status === 'cancelled' ? 'Annotation cancelled' : undefined,
          })

          fetchTweets()
          setTimeout(() => setAnnotateAllResult({ status: 'idle' }), 10000)
        }
      } catch (error: any) {
        console.error('Error polling annotate-all status:', error)
        // If task not found (404) — backend was restarted, task is gone
        if (error.response?.status === 404) {
          resetAnnotateAllState()
          setAnnotateAllResult({
            status: 'completed',
            message: 'Annotation task finished (backend was restarted)',
          })
          fetchTweets()
          setTimeout(() => setAnnotateAllResult({ status: 'idle' }), 10000)
        }
      }
    }, 3000) // Poll every 3 seconds
  }

  const handleCancelAnnotateAll = async () => {
    if (!annotateAllTaskId) return
    try {
      await axios.post(`http://localhost:8000/api/tweets/batch-annotate/${annotateAllTaskId}/cancel`)
    } catch (error) {
      console.error('Error cancelling annotation:', error)
    }
  }

  const clearFilters = () => {
    setSelectedAuthors([])
    setSelectedConcepts([])
    setSelectedYears([])
    setSearchTerm('')
    setExcludeRetweets(false)
    setCurrentPage(1)
  }

  const renderHierarchicalConcept = (concept: ConceptFacet, level: number = 0) => {
    const isExpanded = expandedConcepts.has(concept.concept_id)
    const hasChildren = concept.children && concept.children.length > 0
    const isSelected = selectedConcepts.includes(concept.concept_id)

    return (
      <div className="w-full">
        <div 
          className={cn(
            "flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
            isSelected && "bg-blue-50 dark:bg-blue-950",
            level > 0 && "ml-4"
          )}
          onClick={() => toggleConcept(concept.concept_id)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleConceptExpansion(concept.concept_id)
              }}
              className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRightIcon className="h-3 w-3" />
              )}
            </button>
          )}
          {!hasChildren && level > 0 && <div className="w-4" />}
          
          <TagBadge 
            variant={isSelected ? "default" : "system"}
            className="flex-1 justify-between cursor-pointer"
            style={{
              backgroundColor: isSelected ? '#93C5FD' : '#DBEAFE', // lighter blue when selected
              color: '#1E40AF'
            }}
          >
            <span className="flex items-center gap-1">
              <span>{conceptService.getConceptIcon(concept as unknown as Concept)}</span>
              <span>{concept.display_name}</span>
            </span>
            <span className="ml-2 text-xs opacity-70">{concept.aggregate_count ?? concept.count}</span>
          </TagBadge>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {concept.children!.map((child, childIndex) => (
              <React.Fragment key={`${concept.concept_id}-child-${child.concept_id}-${childIndex}`}>
                {renderHierarchicalConcept(child, level + 1)}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>
    )
  }

  // Control how many concepts to show initially
  const INITIAL_CONCEPTS_LIMIT = 50
  const displayedConcepts = showHierarchy 
    ? hierarchyFacets 
    : (showAllConcepts ? facets.concepts : facets.concepts.slice(0, INITIAL_CONCEPTS_LIMIT))

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Twitter/X Feed</h1>
        <p className="text-gray-600 dark:text-gray-400">Browse and analyze collected tweets with advanced filtering</p>
      </div>

      {/* Search Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 dark:text-gray-500 h-4 w-4" />
              <Input
                type="text"
                placeholder="Search tweets..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value)
                  setCurrentPage(1)
                }}
                className="pl-10"
              />
            </div>
            <div className="flex items-center gap-2">
              <Checkbox
                id="exclude-retweets"
                checked={excludeRetweets}
                onCheckedChange={(checked) => {
                  setExcludeRetweets(checked as boolean)
                  setCurrentPage(1)
                }}
              />
              <label htmlFor="exclude-retweets" className="text-sm cursor-pointer">
                Exclude Retweets
              </label>
            </div>
            <Button onClick={fetchTweets} variant="outline" disabled={loading}>
              <RefreshCw className={cn("h-4 w-4 mr-2", loading && "animate-spin")} />
              Refresh
            </Button>
            {(selectedAuthors.length > 0 || selectedConcepts.length > 0 || selectedYears.length > 0 || searchTerm) && (
              <Button onClick={clearFilters} variant="outline">
                Clear Filters
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Batch Annotation Controls */}
      <Card className="mb-6">
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium">Batch Annotation</span>
            </div>

            <div className="flex-1 min-w-[200px] max-w-[300px]">
              <UnifiedModelSelector
                taskType="tag_suggestion"
                value={batchModel}
                onValueChange={setBatchModel}
                compact={true}
                disabled={batchAnnotating || annotateAllRunning}
              />
            </div>

            <Button
              onClick={handleBatchAnnotate}
              disabled={batchAnnotating || annotateAllRunning || tweets.length === 0 || !batchModel}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {batchAnnotating ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Annotating... {batchProgress}%
                </>
              ) : (
                <>
                  <Sparkles className="mr-2 h-4 w-4" />
                  Batch Annotate ({tweets.length} tweets)
                </>
              )}
            </Button>

            {/* Annotate All Unannotated button */}
            {(() => {
              const notAnnotatedFacet = facets.annotation_status.find(s => s.status === 'not_annotated')
              const notAnnotatedCount = notAnnotatedFacet?.count || 0
              return (
                <Button
                  onClick={handleAnnotateAll}
                  disabled={batchAnnotating || annotateAllRunning || notAnnotatedCount === 0 || !batchModel}
                  className="bg-orange-600 hover:bg-orange-700"
                >
                  {annotateAllRunning ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Annotating All...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Annotate All Unannotated ({notAnnotatedCount})
                    </>
                  )}
                </Button>
              )
            })()}

            {/* Progress bar for page batch */}
            {batchAnnotating && (
              <div className="flex-1 min-w-[200px]">
                <Progress value={batchProgress} className="h-2" />
              </div>
            )}

            {/* Result message */}
            {batchResult.status === 'completed' && (
              <div className="flex items-center gap-2 text-sm">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <span className="text-green-700">
                  {batchResult.newTagsCount} new tags added
                  {batchResult.skippedCount ? `, ${batchResult.skippedCount} skipped` : ''}
                  {batchResult.errorCount ? `, ${batchResult.errorCount} errors` : ''}
                </span>
              </div>
            )}

            {batchResult.status === 'error' && (
              <div className="flex items-center gap-2 text-sm">
                <AlertCircle className="h-4 w-4 text-red-500" />
                <span className="text-red-700">{batchResult.message}</span>
              </div>
            )}
          </div>

          {/* Annotate All progress banner */}
          {annotateAllRunning && (
            <div className="flex items-center gap-4 p-3 bg-orange-50 dark:bg-orange-950 rounded-lg border border-orange-200 dark:border-orange-800">
              <Loader2 className="h-5 w-5 text-orange-600 animate-spin flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-medium text-orange-800 dark:text-orange-200">
                    Annotating tweets... {annotateAllProgress.processed}/{annotateAllProgress.total} ({annotateAllProgress.progress}%)
                    {annotateAllProgress.newTagsCount > 0 && ` — ${annotateAllProgress.newTagsCount} new tags`}
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleCancelAnnotateAll}
                    className="h-7 px-3 text-xs border-orange-300 text-orange-700 hover:bg-orange-100"
                  >
                    Cancel
                  </Button>
                </div>
                <Progress value={annotateAllProgress.progress} className="h-2" />
              </div>
            </div>
          )}

          {/* Annotate All result message */}
          {annotateAllResult.status === 'completed' && (
            <div className="flex items-center gap-2 text-sm p-2 bg-green-50 dark:bg-green-950 rounded">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-green-700 dark:text-green-300">
                {annotateAllResult.message || `All done! ${annotateAllResult.newTagsCount} new tags added`}
                {annotateAllResult.skippedCount ? `, ${annotateAllResult.skippedCount} skipped` : ''}
                {annotateAllResult.errorCount ? `, ${annotateAllResult.errorCount} errors` : ''}
              </span>
            </div>
          )}
          {annotateAllResult.status === 'cancelled' && (
            <div className="flex items-center gap-2 text-sm p-2 bg-yellow-50 dark:bg-yellow-950 rounded">
              <AlertCircle className="h-4 w-4 text-yellow-500" />
              <span className="text-yellow-700 dark:text-yellow-300">
                Annotation cancelled. {annotateAllResult.newTagsCount || 0} new tags added before cancellation.
              </span>
            </div>
          )}
          {annotateAllResult.status === 'error' && (
            <div className="flex items-center gap-2 text-sm p-2 bg-red-50 dark:bg-red-950 rounded">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <span className="text-red-700 dark:text-red-300">{annotateAllResult.message}</span>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Sidebar - Authors Filter */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Authors
                </CardTitle>
                {selectedAuthors.length > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedAuthors([])}
                    className="h-7 px-2 text-xs"
                  >
                    <X className="h-3 w-3 mr-1" />
                    Clear
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[553px] px-4 pb-4">
                {facets.authors.map(author => (
                  <div
                    key={author.username}
                    className={cn(
                      "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                      selectedAuthors.includes(author.username) && "bg-blue-50 dark:bg-blue-950"
                    )}
                    onClick={() => toggleAuthor(author.username)}
                  >
                    <div className="flex items-center gap-2">
                      <Checkbox
                        checked={selectedAuthors.includes(author.username)}
                        onCheckedChange={() => toggleAuthor(author.username)}
                      />
                      <span className="text-sm font-medium">@{author.username}</span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {author.count}
                    </Badge>
                  </div>
                ))}
              </ScrollArea>
            </CardContent>
          </Card>
          
          {/* Year Navigation */}
          <Card className="mt-6">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Calendar className="h-4 w-4" />
                  Years
                </CardTitle>
                {selectedYears.length > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedYears([])}
                    className="h-7 px-2 text-xs"
                  >
                    <X className="h-3 w-3 mr-1" />
                    Clear
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[200px] px-4 pb-4">
                {facets.years.map(year => (
                  <div
                    key={year.year}
                    className={cn(
                      "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                      selectedYears.includes(year.year) && "bg-blue-50 dark:bg-blue-950"
                    )}
                    onClick={() => toggleYear(year.year)}
                  >
                    <div className="flex items-center gap-2">
                      <Checkbox
                        checked={selectedYears.includes(year.year)}
                        onCheckedChange={() => toggleYear(year.year)}
                      />
                      <span className="text-sm font-medium">{year.year}</span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {year.count}
                    </Badge>
                  </div>
                ))}
              </ScrollArea>
            </CardContent>
          </Card>
          
          {/* Annotation Status Filter */}
          <Card className="mt-6">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Tag className="h-4 w-4" />
                  Annotation Status
                </CardTitle>
                {selectedAnnotationStatus.length > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => setSelectedAnnotationStatus([])}
                    className="h-7 px-2 text-xs"
                  >
                    <X className="h-3 w-3 mr-1" />
                    Clear
                  </Button>
                )}
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <div className="px-4 pb-4 space-y-2">
                {facets.annotation_status.map(status => (
                  <div
                    key={status.status}
                    className={cn(
                      "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                      selectedAnnotationStatus.includes(status.status) && "bg-blue-50 dark:bg-blue-950"
                    )}
                    onClick={() => {
                      // Toggle annotation status (only allow one at a time)
                      if (selectedAnnotationStatus.includes(status.status)) {
                        setSelectedAnnotationStatus([])
                      } else {
                        setSelectedAnnotationStatus([status.status])
                      }
                    }}
                  >
                    <div className="flex items-center gap-2">
                      <Checkbox
                        checked={selectedAnnotationStatus.includes(status.status)}
                        onCheckedChange={() => {
                          if (selectedAnnotationStatus.includes(status.status)) {
                            setSelectedAnnotationStatus([])
                          } else {
                            setSelectedAnnotationStatus([status.status])
                          }
                        }}
                        onClick={(e) => e.stopPropagation()}
                        className="h-4 w-4"
                      />
                      <span className="text-sm font-medium">
                        {status.label}
                      </span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {status.count}
                    </Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Sidebar - Tags Filter */}
        <div className="lg:col-span-3 order-last lg:order-last">
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Tag className="h-4 w-4" />
                  Concepts
                </CardTitle>
                <div className="flex gap-1">
                  {selectedConcepts.length > 0 && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => setSelectedConcepts([])}
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
                    {showHierarchy ? <GitBranch className="h-3 w-3" /> : <Layers className="h-3 w-3" />}
                  </Button>
                </div>
              </div>
            </CardHeader>
            
            {/* Semantic Concept Search */}
            <div className="px-4 pt-4 pb-2">
              <SemanticConceptSearch
                onConceptSelect={(conceptId, _displayName) => {
                  if (!selectedConcepts.includes(conceptId)) {
                    setSelectedConcepts([...selectedConcepts, conceptId])
                  }
                }}
                selectedConcepts={selectedConcepts}
                contentTypes={['tweet']}
                placeholder="Search concepts semantically..."
                className="w-full"
              />
            </div>
            
            <CardContent className="p-0">
              <ScrollArea className="h-[1200px] px-4 pb-4">
                {showHierarchy ? (
                  <div className="space-y-1">
                    {hierarchyFacets && hierarchyFacets.map((concept, index) => (
                      <React.Fragment key={`hierarchy-root-${concept.concept_id}-${index}`}>
                        {renderHierarchicalConcept(concept)}
                      </React.Fragment>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-1">
                    {displayedConcepts.map((concept, index) => (
                      <div
                        key={`${concept.concept_id}-${index}`}
                        className={cn(
                          "flex items-center justify-between py-1 px-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                          selectedConcepts.includes(concept.concept_id) && "bg-blue-50 dark:bg-blue-950"
                        )}
                        onClick={() => toggleConcept(concept.concept_id)}
                      >
                        <div className="flex items-center gap-2">
                          <Checkbox
                            checked={selectedConcepts.includes(concept.concept_id)}
                            onCheckedChange={() => toggleConcept(concept.concept_id)}
                            onClick={(e) => e.stopPropagation()}
                            className="h-3 w-3"
                          />
                          <div
                            className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-xs font-medium"
                            style={{
                              backgroundColor: selectedConcepts.includes(concept.concept_id) ? '#93C5FD' : '#DBEAFE',
                              color: '#1E40AF'
                            }}
                          >
                            <span className="text-xs">{conceptService.getConceptIcon(concept as unknown as Concept)}</span>
                            <span>{concept.display_name}</span>
                          </div>
                        </div>
                        <Badge variant="secondary" className="text-xs py-0 px-1">
                          {concept.count}
                        </Badge>
                      </div>
                    ))}
                    
                    {/* Show More/Less button */}
                    {!showHierarchy && facets.concepts.length > INITIAL_CONCEPTS_LIMIT && (
                      <div className="mt-3 pt-3 border-t">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setShowAllConcepts(!showAllConcepts)}
                          className="w-full justify-center text-xs"
                        >
                          {showAllConcepts ? (
                            <>
                              <ChevronDown className="h-3 w-3 mr-1 rotate-180" />
                              Show Less
                            </>
                          ) : (
                            <>
                              <ChevronDown className="h-3 w-3 mr-1" />
                              Show {facets.concepts.length - INITIAL_CONCEPTS_LIMIT} More Concepts
                            </>
                          )}
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Main Content - Center */}
        <div className="lg:col-span-7 order-2 lg:order-2">
          {/* Stats Bar */}
          <div className="mb-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Badge variant="outline" className="py-1.5 px-3">
                <Twitter className="h-3 w-3 mr-1" />
                {totalTweets} tweets
              </Badge>
              {selectedAuthors.length > 0 && (
                <Badge variant="secondary" className="py-1.5 px-3">
                  {selectedAuthors.length} author{selectedAuthors.length !== 1 ? 's' : ''} selected
                </Badge>
              )}
              {selectedConcepts.length > 0 && (
                <Badge variant="secondary" className="py-1.5 px-3">
                  {selectedConcepts.length} concept{selectedConcepts.length !== 1 ? 's' : ''} selected
                </Badge>
              )}
              {selectedYears.length > 0 && (
                <Badge variant="secondary" className="py-1.5 px-3">
                  <Calendar className="h-3 w-3 mr-1" />
                  {selectedYears.length > 1 ? `${selectedYears.length} years` : selectedYears[0]} selected
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500 dark:text-gray-400">
                Page {currentPage} of {totalPages}
              </span>
            </div>
          </div>

          {/* Tweets List */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400 dark:text-gray-500" />
            </div>
          ) : tweets.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Twitter className="h-12 w-12 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-gray-500 dark:text-gray-400">No tweets found matching your filters</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {tweets.map(tweet => (
                <TweetCardModern
                  key={tweet.id}
                  tweet={tweet}
                  onConceptAdded={handleConceptAdded}
                  onConceptRemoved={handleConceptRemoved}
                  onSuggestConcepts={handleSuggestConcepts}
                />
              ))}
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <Button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1 || loading}
                variant="outline"
                size="sm"
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
              
              <div className="flex gap-1">
                {[...Array(Math.min(5, totalPages))].map((_, i) => {
                  let pageNum: number
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }
                  
                  return (
                    <Button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      variant={currentPage === pageNum ? "default" : "outline"}
                      size="sm"
                      className="w-10"
                    >
                      {pageNum}
                    </Button>
                  )
                })}
              </div>
              
              <Button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages || loading}
                variant="outline"
                size="sm"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Tag Suggestion Modal */}
      {showSuggestionModal && selectedTweet && (
        <TagSuggestionModalModern
          tweet={selectedTweet}
          isOpen={showSuggestionModal}
          onClose={() => {
            setShowSuggestionModal(false)
            setSelectedTweet(null)
          }}
          onTagsUpdated={handleTagsUpdated}
        />
      )}
    </div>
  )
}