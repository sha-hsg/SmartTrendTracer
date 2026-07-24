import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  Loader2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  MessageSquare
} from 'lucide-react'
import TagSuggestionModalModern from '../TagSuggestionModalModern'
import SemanticConceptSearch from '../SemanticConceptSearch'
import { cn } from "@/lib/utils"
import { Concept } from '@/types/concept'
import RedditPostCard from './RedditPostCard'
import RedditFilterPanel from './RedditFilterPanel'
import { RedditPost, RedditFacets, PaginationInfo } from './types'

const FacetedRedditDashboardModern: React.FC = () => {
  // State management
  const [posts, setPosts] = useState<RedditPost[]>([])
  const [facets, setFacets] = useState<RedditFacets | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [pagination, setPagination] = useState<PaginationInfo>({
    page: 1,
    page_size: 20,
    total_posts: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false
  })

  // Filter state
  const [selectedSubreddit, setSelectedSubreddit] = useState<string>('')
  const [selectedAuthor, setSelectedAuthor] = useState<string>('')
  const [selectedTimeRange, setSelectedTimeRange] = useState<string>('')
  const [minScore, setMinScore] = useState<number | null>(null)
  const [selectedPostType, setSelectedPostType] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedConcept, setSelectedConcept] = useState<Concept | null>(null)

  // UI state
  const [collapsedSections, setCollapsedSections] = useState<{[key: string]: boolean}>({})
  const [tagModalOpen, setTagModalOpen] = useState(false)
  const [selectedPostForTagging, setSelectedPostForTagging] = useState<RedditPost | null>(null)
  const [conceptSearchOpen, setConceptSearchOpen] = useState(false)

  // Load posts and facets
  const loadData = async (page: number = 1) => {
    setLoading(true)
    setError(null)

    try {
      // Build query parameters
      const params: any = {
        page,
        page_size: pagination.page_size
      }

      if (selectedSubreddit) params.subreddit = selectedSubreddit
      if (selectedAuthor) params.author = selectedAuthor
      if (selectedTimeRange) params.time_range = selectedTimeRange
      if (minScore !== null) params.min_score = minScore
      if (searchQuery) params.text_search = searchQuery
      if (selectedConcept) params.concept_id = selectedConcept.id

      // Get posts with faceted search
      const postsResponse = await axios.get('/api/reddit/faceted-search', { params })
      setPosts(postsResponse.data.posts)
      setPagination(postsResponse.data.pagination)

      // Load facets if first load
      if (page === 1) {
        const facetsResponse = await axios.get('/api/reddit/facets')
        setFacets(facetsResponse.data)
      }

    } catch (err) {
      console.error('Error loading Reddit data:', err)
      setError('Failed to load Reddit posts')
    } finally {
      setLoading(false)
    }
  }

  // Initial load
  useEffect(() => {
    loadData()
  }, [])

  // Reload when filters change
  useEffect(() => {
    loadData(1)
  }, [selectedSubreddit, selectedAuthor, selectedTimeRange, minScore, selectedPostType, searchQuery, selectedConcept])

  // Filter handlers
  const handleSubredditFilter = (subreddit: string) => {
    setSelectedSubreddit(selectedSubreddit === subreddit ? '' : subreddit)
  }

  const handleAuthorFilter = (author: string) => {
    setSelectedAuthor(selectedAuthor === author ? '' : author)
  }

  const handleTimeRangeFilter = (range: string) => {
    setSelectedTimeRange(selectedTimeRange === range ? '' : range)
  }

  const handleScoreFilter = (scoreType: string) => {
    const scoreMap: {[key: string]: number} = {
      'high_score': 100,
      'medium_score': 10,
      'low_score': 0
    }
    const newScore = scoreMap[scoreType]
    setMinScore(minScore === newScore ? null : newScore)
  }

  const handleConceptSelect = (conceptId: string, displayName: string) => {
    setSelectedConcept({ id: conceptId, concept_id: conceptId, display_name: displayName, slug: displayName.toLowerCase().replace(/\s+/g, '_') } as Concept)
    setConceptSearchOpen(false)
  }

  const clearAllFilters = () => {
    setSelectedSubreddit('')
    setSelectedAuthor('')
    setSelectedTimeRange('')
    setMinScore(null)
    setSelectedPostType('')
    setSearchQuery('')
    setSelectedConcept(null)
  }

  // Tagging handlers
  const openTagModal = (post: RedditPost) => {
    setSelectedPostForTagging(post)
    setTagModalOpen(true)
  }

  // Utility functions
  const toggleSection = (section: string) => {
    setCollapsedSections(prev => ({ ...prev, [section]: !prev[section] }))
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const getActiveFiltersCount = () => {
    let count = 0
    if (selectedSubreddit) count++
    if (selectedAuthor) count++
    if (selectedTimeRange) count++
    if (minScore !== null) count++
    if (selectedPostType) count++
    if (searchQuery) count++
    if (selectedConcept) count++
    return count
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <Card className="w-96">
          <CardContent className="flex items-center justify-center p-6">
            <div className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={() => loadData()} variant="outline">
                <RefreshCw className="w-4 h-4 mr-2" />
                Try Again
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Reddit Posts</h1>
          <p className="text-muted-foreground">
            AI/ML discussions from {facets?.subreddits?.length || 8} subreddits
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary">
            {facets?.total_posts || 0} total posts
          </Badge>
          <Button onClick={() => loadData(pagination.page)} variant="outline" size="sm">
            <RefreshCw className={cn("w-4 h-4 mr-2", loading && "animate-spin")} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <RedditFilterPanel
            facets={facets}
            searchQuery={searchQuery}
            setSearchQuery={setSearchQuery}
            selectedConcept={selectedConcept}
            setSelectedConcept={setSelectedConcept}
            setConceptSearchOpen={setConceptSearchOpen}
            selectedSubreddit={selectedSubreddit}
            handleSubredditFilter={handleSubredditFilter}
            selectedTimeRange={selectedTimeRange}
            handleTimeRangeFilter={handleTimeRangeFilter}
            minScore={minScore}
            handleScoreFilter={handleScoreFilter}
            selectedAuthor={selectedAuthor}
            handleAuthorFilter={handleAuthorFilter}
            collapsedSections={collapsedSections}
            toggleSection={toggleSection}
            activeFiltersCount={getActiveFiltersCount()}
            clearAllFilters={clearAllFilters}
          />
        </div>

        {/* Posts Content */}
        <div className="lg:col-span-3 space-y-4">
          {/* Posts List */}
          <div className="space-y-4">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                <span>Loading Reddit posts...</span>
              </div>
            ) : posts.length === 0 ? (
              <Card>
                <CardContent className="flex items-center justify-center py-12">
                  <div className="text-center">
                    <MessageSquare className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">No posts found</h3>
                    <p className="text-muted-foreground">
                      Try adjusting your filters or search terms
                    </p>
                  </div>
                </CardContent>
              </Card>
            ) : (
              posts.map(post => (
                <RedditPostCard
                  key={post._id}
                  post={post}
                  onOpenTagModal={openTagModal}
                  formatDate={formatDate}
                />
              ))
            )}
          </div>

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                Page {pagination.page} of {pagination.total_pages} ({pagination.total_posts} total posts)
              </div>
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => loadData(pagination.page - 1)}
                  disabled={!pagination.has_prev || loading}
                  variant="outline"
                  size="sm"
                >
                  <ChevronLeft className="w-4 h-4" />
                  Previous
                </Button>
                <Button
                  onClick={() => loadData(pagination.page + 1)}
                  disabled={!pagination.has_next || loading}
                  variant="outline"
                  size="sm"
                >
                  Next
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tag Modal */}
      {selectedPostForTagging && (
        <TagSuggestionModalModern
          contentId={selectedPostForTagging._id}
          contentType="reddit"
          contentPreview={selectedPostForTagging.title + '\n' + (selectedPostForTagging.selftext || '')}
          isOpen={tagModalOpen}
          onClose={() => {
            setTagModalOpen(false)
            setSelectedPostForTagging(null)
          }}
          onTagsUpdated={() => {
            // Refresh posts to get updated tags
            loadData()
          }}
        />
      )}

      {/* Concept Search */}
      {conceptSearchOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white dark:bg-gray-950 rounded-lg p-4 max-w-md w-full mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold">Search Concepts</h3>
              <Button variant="ghost" size="sm" onClick={() => setConceptSearchOpen(false)}>x</Button>
            </div>
            <SemanticConceptSearch
              onConceptSelect={(conceptId, displayName) => {
                handleConceptSelect(conceptId, displayName)
                setConceptSearchOpen(false)
              }}
              placeholder="Search concepts to filter posts..."
            />
          </div>
        </div>
      )}
    </div>
  )
}

export default FacetedRedditDashboardModern
