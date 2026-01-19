import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import { 
  Search, 
  Filter, 
  User, 
  Tag,
  Loader2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
  X,
  MessageSquare,
  ArrowUp,
  Clock,
  Link as LinkIcon,
  Star
} from 'lucide-react'
import TagSuggestionModalModern from './TagSuggestionModalModern'
import SemanticConceptSearch from './SemanticConceptSearch'
import { cn } from "@/lib/utils"
import { Concept } from '@/types/concept'

interface RedditPost {
  _id: string
  reddit_id: string
  title: string
  selftext: string
  author: string
  subreddit: string
  subreddit_config: {
    name: string
    display_name: string
    category: string
    description: string
  }
  score: number
  upvote_ratio: number
  num_comments: number
  created_utc: string
  permalink: string
  url: string
  urls: string[]
  is_self: boolean
  is_video: boolean
  over_18: boolean
  spoiler: boolean
  stickied: boolean
  gilded: number
  comments: Array<{
    id: string
    author: string
    body: string
    score: number
  }>
  tags: string[]
  concepts: Concept[]
  processed: boolean
}

interface SubredditFacet {
  name: string
  count: number
}

interface AuthorFacet {
  name: string
  count: number
}

interface TimeFacet {
  '24h': number
  '7d': number
  '30d': number
}

interface ScoreFacet {
  high_score: number
  medium_score: number
  low_score: number
}

interface PostTypeFacet {
  text_posts: number
  link_posts: number
  video_posts: number
}

interface RedditFacets {
  subreddits: SubredditFacet[]
  authors: AuthorFacet[]
  time_ranges: TimeFacet
  score_ranges: ScoreFacet
  post_types: PostTypeFacet
  total_posts: number
}

interface PaginationInfo {
  page: number
  page_size: number
  total_posts: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

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
      const postsResponse = await axios.get('http://localhost:8000/api/reddit/faceted-search', { params })
      setPosts(postsResponse.data.posts)
      setPagination(postsResponse.data.pagination)
      
      // Load facets if first load
      if (page === 1) {
        const facetsResponse = await axios.get('http://localhost:8000/api/reddit/facets')
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

  const handlePostTypeFilter = (postType: string) => {
    setSelectedPostType(selectedPostType === postType ? '' : postType)
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

  const handleTagUpdate = async (postId: string, newConcepts: Concept[]) => {
    // Update local state
    setPosts(prevPosts => prevPosts.map(post => 
      post._id === postId ? { ...post, concepts: newConcepts } : post
    ))
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
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg flex items-center gap-2">
                  <Filter className="w-5 h-5" />
                  Filters
                </CardTitle>
                {getActiveFiltersCount() > 0 && (
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="text-xs">
                      {getActiveFiltersCount()} active
                    </Badge>
                    <Button
                      onClick={clearAllFilters}
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                )}
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Search */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Search Posts</label>
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
                  <Input
                    placeholder="Search titles and content..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
              </div>

              {/* Concept Search */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Filter by Concept</label>
                {selectedConcept ? (
                  <div className="flex items-center gap-2">
                    <TagBadge size="sm">{selectedConcept.display_name}</TagBadge>
                    <Button
                      onClick={() => setSelectedConcept(null)}
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                ) : (
                  <Button
                    onClick={() => setConceptSearchOpen(true)}
                    variant="outline"
                    size="sm"
                    className="w-full justify-start"
                  >
                    <Search className="w-4 h-4 mr-2" />
                    Search Concepts...
                  </Button>
                )}
              </div>

              {/* Subreddits */}
              {facets?.subreddits && facets.subreddits.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Subreddits</label>
                    <Button
                      onClick={() => toggleSection('subreddits')}
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                    >
                      {collapsedSections['subreddits'] ? 
                        <ChevronRightIcon className="w-3 h-3" /> : 
                        <ChevronDown className="w-3 h-3" />
                      }
                    </Button>
                  </div>
                  {!collapsedSections['subreddits'] && (
                    <div className="space-y-1 max-h-40 overflow-y-auto">
                      {facets.subreddits.map(subreddit => (
                        <div
                          key={subreddit.name}
                          className={cn(
                            "flex items-center justify-between p-2 rounded cursor-pointer text-sm",
                            selectedSubreddit === subreddit.name 
                              ? "bg-primary text-primary-foreground" 
                              : "hover:bg-muted"
                          )}
                          onClick={() => handleSubredditFilter(subreddit.name)}
                        >
                          <span>r/{subreddit.name}</span>
                          <Badge variant="secondary" className="text-xs">
                            {subreddit.count}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Time Ranges */}
              {facets?.time_ranges && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Time Range</label>
                  <div className="space-y-1">
                    {Object.entries(facets.time_ranges).map(([range, count]) => (
                      <div
                        key={range}
                        className={cn(
                          "flex items-center justify-between p-2 rounded cursor-pointer text-sm",
                          selectedTimeRange === range 
                            ? "bg-primary text-primary-foreground" 
                            : "hover:bg-muted"
                        )}
                        onClick={() => handleTimeRangeFilter(range)}
                      >
                        <span className="flex items-center gap-2">
                          <Clock className="w-3 h-3" />
                          {range === '24h' && 'Last 24 hours'}
                          {range === '7d' && 'Last 7 days'}
                          {range === '30d' && 'Last 30 days'}
                        </span>
                        <Badge variant="secondary" className="text-xs">
                          {count}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Score Ranges */}
              {facets?.score_ranges && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Post Score</label>
                  <div className="space-y-1">
                    {Object.entries(facets.score_ranges).map(([scoreType, count]) => (
                      <div
                        key={scoreType}
                        className={cn(
                          "flex items-center justify-between p-2 rounded cursor-pointer text-sm",
                          (scoreType === 'high_score' && minScore === 100) ||
                          (scoreType === 'medium_score' && minScore === 10) ||
                          (scoreType === 'low_score' && minScore === 0)
                            ? "bg-primary text-primary-foreground" 
                            : "hover:bg-muted"
                        )}
                        onClick={() => handleScoreFilter(scoreType)}
                      >
                        <span className="flex items-center gap-2">
                          <ArrowUp className="w-3 h-3" />
                          {scoreType === 'high_score' && '100+ points'}
                          {scoreType === 'medium_score' && '10-99 points'}
                          {scoreType === 'low_score' && '< 10 points'}
                        </span>
                        <Badge variant="secondary" className="text-xs">
                          {count}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Top Authors */}
              {facets?.authors && facets.authors.length > 0 && (
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-sm font-medium">Top Authors</label>
                    <Button
                      onClick={() => toggleSection('authors')}
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                    >
                      {collapsedSections['authors'] ? 
                        <ChevronRightIcon className="w-3 h-3" /> : 
                        <ChevronDown className="w-3 h-3" />
                      }
                    </Button>
                  </div>
                  {!collapsedSections['authors'] && (
                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {facets.authors.slice(0, 10).map(author => (
                        <div
                          key={author.name}
                          className={cn(
                            "flex items-center justify-between p-2 rounded cursor-pointer text-sm",
                            selectedAuthor === author.name 
                              ? "bg-primary text-primary-foreground" 
                              : "hover:bg-muted"
                          )}
                          onClick={() => handleAuthorFilter(author.name)}
                        >
                          <span className="flex items-center gap-2">
                            <User className="w-3 h-3" />
                            {author.name}
                          </span>
                          <Badge variant="secondary" className="text-xs">
                            {author.count}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
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
                <Card key={post._id} className="hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="space-y-4">
                      {/* Post Header */}
                      <div className="flex items-start justify-between">
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Badge variant="outline">r/{post.subreddit}</Badge>
                          <span>•</span>
                          <User className="w-3 h-3" />
                          <span>{post.author}</span>
                          <span>•</span>
                          <Clock className="w-3 h-3" />
                          <span>{formatDate(post.created_utc)}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge variant="secondary" className="text-xs">
                            <ArrowUp className="w-3 h-3 mr-1" />
                            {post.score}
                          </Badge>
                          <Badge variant="secondary" className="text-xs">
                            <MessageSquare className="w-3 h-3 mr-1" />
                            {post.num_comments}
                          </Badge>
                        </div>
                      </div>

                      {/* Post Title */}
                      <div className="space-y-2">
                        <h3 className="text-lg font-semibold leading-tight">
                          <a
                            href={`https://reddit.com${post.permalink}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-primary transition-colors"
                          >
                            {post.title}
                          </a>
                        </h3>

                        {/* Post Content Preview */}
                        {post.selftext && (
                          <p className="text-muted-foreground line-clamp-3">
                            {post.selftext.substring(0, 300)}
                            {post.selftext.length > 300 && '...'}
                          </p>
                        )}

                        {/* External URL */}
                        {!post.is_self && post.url && (
                          <div className="flex items-center gap-2 p-2 bg-muted rounded text-sm">
                            <LinkIcon className="w-3 h-3" />
                            <a
                              href={post.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-primary hover:underline truncate"
                            >
                              {post.url}
                            </a>
                          </div>
                        )}

                        {/* Post Type Indicators */}
                        <div className="flex items-center gap-2">
                          {post.is_self && <Badge variant="outline" className="text-xs">Text Post</Badge>}
                          {post.is_video && <Badge variant="outline" className="text-xs">Video</Badge>}
                          {post.stickied && <Badge variant="outline" className="text-xs">Pinned</Badge>}
                          {post.gilded > 0 && (
                            <Badge variant="outline" className="text-xs">
                              <Star className="w-3 h-3 mr-1" />
                              {post.gilded} Award{post.gilded > 1 ? 's' : ''}
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Tags and Actions */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 flex-wrap">
                          {post.concepts?.map(concept => (
                            <TagBadge key={concept.id} size="sm">{concept.display_name}</TagBadge>
                          ))}
                          <Button
                            onClick={() => openTagModal(post)}
                            variant="ghost"
                            size="sm"
                            className="text-xs"
                          >
                            <Tag className="w-3 h-3 mr-1" />
                            Add Tag
                          </Button>
                        </div>

                        <div className="flex items-center gap-2">
                          <Button variant="ghost" size="sm" asChild>
                            <a
                              href={`https://reddit.com${post.permalink}`}
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              View on Reddit
                            </a>
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
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
          isOpen={tagModalOpen}
          onClose={() => {
            setTagModalOpen(false)
            setSelectedPostForTagging(null)
          }}
          tweet={{
            id: selectedPostForTagging._id,
            text: selectedPostForTagging.title + '\n' + (selectedPostForTagging.selftext || ''),
            tags: selectedPostForTagging.concepts || []
          }}
          onTagsUpdated={() => {
            // Refresh posts to get updated tags
            fetchPosts()
          }}
        />
      )}

      {/* Concept Search Modal */}
      {conceptSearchOpen && (
        <SemanticConceptSearch
          isOpen={conceptSearchOpen}
          onClose={() => setConceptSearchOpen(false)}
          onConceptSelect={handleConceptSelect}
          placeholder="Search concepts to filter posts..."
        />
      )}
    </div>
  )
}

export default FacetedRedditDashboardModern