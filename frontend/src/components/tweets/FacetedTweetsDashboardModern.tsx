import { useState, useEffect, useCallback } from 'react'
import http from '@/services/http'
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Search,
  RefreshCw,
} from 'lucide-react'
import TagSuggestionModalModern from '../TagSuggestionModalModern'
import { cn } from "@/lib/utils"
import { Concept } from '@/types/concept'
import TweetFilterPanel from './TweetFilterPanel'
import TweetCard from './TweetCard'
import type { Tweet } from './TweetCard'
import BatchAnnotationPanel from './BatchAnnotationPanel'
import { useBatchAnnotation } from './useBatchAnnotation'

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

  const pageSize = 50
  const totalPages = Math.ceil(totalTweets / pageSize)

  const fetchTweets = useCallback(async () => {
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

      if (selectedAnnotationStatus.length === 1) {
        params.append('annotation_status', selectedAnnotationStatus[0])
      }

      const response = await http.get<FacetedSearchResponse>(
        `/api/tweets/faceted-search?${params.toString()}`
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
  }, [currentPage, searchTerm, excludeRetweets, selectedAuthors, selectedConcepts, selectedYears, selectedAnnotationStatus])

  const batch = useBatchAnnotation(fetchTweets)

  useEffect(() => {
    fetchTweets()
  }, [fetchTweets])

  useEffect(() => {
    if (showHierarchy) {
      fetchHierarchyFacets()
    }
  }, [showHierarchy])

  const fetchHierarchyFacets = async () => {
    try {
      const response = await http.get<any>(
        '/api/tweets/hierarchy-facets'
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
    setTweets(prev => prev.map(tweet =>
      tweet.id === tweetId
        ? { ...tweet, concepts: [...(tweet.concepts || []), concept] }
        : tweet
    ))
  }

  const handleConceptRemoved = async (tweetId: string, conceptId: string) => {
    setTweets(prev => prev.map(tweet =>
      tweet.id === tweetId
        ? { ...tweet, concepts: tweet.concepts?.filter(c => c.concept_id !== conceptId) }
        : tweet
    ))
  }

  const handleSuggestConcepts = (tweet: Tweet) => {
    setSavedScrollPosition(window.scrollY)
    setSelectedTweet(tweet)
    setShowSuggestionModal(true)
  }

  const handleTagsUpdated = async () => {
    if (selectedTweet) {
      try {
        const response = await http.get(`/api/tweets/${selectedTweet.id}`)
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
  }

  const clearFilters = () => {
    setSelectedAuthors([])
    setSelectedConcepts([])
    setSelectedYears([])
    setSearchTerm('')
    setExcludeRetweets(false)
    setCurrentPage(1)
  }

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
      <BatchAnnotationPanel
        tweetCount={tweets.length}
        annotationStatusFacets={facets.annotation_status}
        batchAnnotating={batch.batchAnnotating}
        batchProgress={batch.batchProgress}
        batchModel={batch.batchModel}
        setBatchModel={batch.setBatchModel}
        batchResult={batch.batchResult}
        annotateAllRunning={batch.annotateAllRunning}
        annotateAllProgress={batch.annotateAllProgress}
        annotateAllResult={batch.annotateAllResult}
        onBatchAnnotate={() => batch.handleBatchAnnotate(tweets.map(t => t.id))}
        onAnnotateAll={batch.handleAnnotateAll}
        onCancelAnnotateAll={batch.handleCancelAnnotateAll}
      />

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <TweetFilterPanel
          facets={facets}
          hierarchyFacets={hierarchyFacets}
          selectedAuthors={selectedAuthors}
          selectedConcepts={selectedConcepts}
          selectedYears={selectedYears}
          selectedAnnotationStatus={selectedAnnotationStatus}
          showHierarchy={showHierarchy}
          showAllConcepts={showAllConcepts}
          expandedConcepts={expandedConcepts}
          onToggleAuthor={toggleAuthor}
          onToggleYear={toggleYear}
          onToggleConcept={toggleConcept}
          onToggleConceptExpansion={toggleConceptExpansion}
          onSetSelectedAuthors={setSelectedAuthors}
          onSetSelectedConcepts={setSelectedConcepts}
          onSetSelectedYears={setSelectedYears}
          onSetSelectedAnnotationStatus={setSelectedAnnotationStatus}
          onSetShowHierarchy={setShowHierarchy}
          onSetShowAllConcepts={setShowAllConcepts}
        />

        <TweetCard
          tweets={tweets}
          loading={loading}
          totalTweets={totalTweets}
          currentPage={currentPage}
          totalPages={totalPages}
          selectedAuthors={selectedAuthors}
          selectedConcepts={selectedConcepts}
          selectedYears={selectedYears}
          onPageChange={setCurrentPage}
          onConceptAdded={handleConceptAdded}
          onConceptRemoved={handleConceptRemoved}
          onSuggestConcepts={handleSuggestConcepts}
        />
      </div>

      {/* Tag Suggestion Modal */}
      {showSuggestionModal && selectedTweet && (
        <TagSuggestionModalModern
          contentId={selectedTweet.id}
          contentType="tweet"
          contentPreview={selectedTweet.text}
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
