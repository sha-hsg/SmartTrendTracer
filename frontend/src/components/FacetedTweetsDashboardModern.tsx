import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { 
  Search, 
  Filter, 
  User, 
  Hash, 
  Calendar,
  Loader2,
  ChevronLeft,
  ChevronRight,
  Twitter,
  RefreshCw,
  Tag,
  GitBranch,
  Layers,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
  Eye,
  EyeOff,
  Sparkles
} from 'lucide-react'
import TweetCardModern from './TweetCardModern'
import TagSuggestionModalModern from './TagSuggestionModalModern'
import { cn } from "@/lib/utils"

interface AuthorFacet {
  username: string
  name?: string
  count: number
}

interface TagFacet {
  tag: string
  display_name?: string
  count: number
  level?: number
  parent?: string | null
  children?: TagFacet[]
}

interface Tweet {
  id: string
  text: string
  author_username: string
  author_name?: string
  tags: any
  created_at: string
  is_retweet?: boolean
  like_count?: number
  retweet_count?: number
  reply_count?: number
  metrics?: {
    likes: number
    retweets: number
    replies: number
  }
  media?: Array<{
    type: string
    url: string
    thumbnail_url?: string
  }>
}

interface FacetedSearchResponse {
  tweets: Tweet[]
  facets: {
    authors: AuthorFacet[]
    tags: TagFacet[]
  }
  total: number
  page: number
  page_size: number
}

export default function FacetedTweetsDashboardModern() {
  const [tweets, setTweets] = useState<Tweet[]>([])
  const [facets, setFacets] = useState<{ authors: AuthorFacet[]; tags: TagFacet[] }>({
    authors: [],
    tags: []
  })
  const [hierarchyFacets, setHierarchyFacets] = useState<TagFacet[]>([])
  const [selectedAuthors, setSelectedAuthors] = useState<string[]>([])
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [searchTerm, setSearchTerm] = useState('')
  const [excludeRetweets, setExcludeRetweets] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [totalTweets, setTotalTweets] = useState(0)
  const [loading, setLoading] = useState(false)
  const [showAllTags, setShowAllTags] = useState(false)
  const [showHierarchy, setShowHierarchy] = useState(false)
  const [expandedTags, setExpandedTags] = useState<Set<string>>(new Set())
  const [selectedTweet, setSelectedTweet] = useState<Tweet | null>(null)
  const [showSuggestionModal, setShowSuggestionModal] = useState(false)

  const pageSize = 50
  const totalPages = Math.ceil(totalTweets / pageSize)

  useEffect(() => {
    fetchTweets()
  }, [selectedAuthors, selectedTags, searchTerm, excludeRetweets, currentPage])

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
      selectedTags.forEach(tag => params.append('tags', tag))
      
      const response = await axios.get<FacetedSearchResponse>(
        `http://localhost:8000/api/v2/tweets/tweets/faceted-search?${params.toString()}`
      )
      
      const transformedTweets = response.data.tweets.map(tweet => ({
        ...tweet,
        metrics: tweet.metrics || {
          likes: tweet.like_count || 0,
          retweets: tweet.retweet_count || 0,
          replies: tweet.reply_count || 0
        },
        tags: tweet.tags ? tweet.tags.map((tag: any) => 
          typeof tag === 'string' ? { tag, type: 'manual' } : tag
        ) : []
      }))
      
      setTweets(transformedTweets)
      setFacets(response.data.facets)
      setTotalTweets(response.data.total)
    } catch (error) {
      console.error('Error fetching tweets:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchHierarchyFacets = async () => {
    try {
      const response = await axios.get<TagFacet[]>(
        'http://localhost:8000/api/v2/tweets/tweets/hierarchy-facets'
      )
      setHierarchyFacets(response.data)
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

  const toggleTag = (tag: string) => {
    setSelectedTags(prev => {
      if (prev.includes(tag)) {
        return prev.filter(t => t !== tag)
      }
      return [...prev, tag]
    })
    setCurrentPage(1)
  }

  const toggleTagExpansion = (tag: string) => {
    setExpandedTags(prev => {
      const newSet = new Set(prev)
      if (newSet.has(tag)) {
        newSet.delete(tag)
      } else {
        newSet.add(tag)
      }
      return newSet
    })
  }

  const handleTagAdded = async (tweetId: string, tag: string) => {
    try {
      await axios.post(`http://localhost:8000/api/tags`, {
        tweet_id: tweetId,
        tag: tag
      })
      fetchTweets()
    } catch (error) {
      console.error('Error adding tag:', error)
    }
  }

  const handleTagRemoved = async (tweetId: string, tag: string) => {
    try {
      await axios.delete(`http://localhost:8000/api/tags`, {
        data: { tweet_id: tweetId, tag: tag }
      })
      fetchTweets()
    } catch (error) {
      console.error('Error removing tag:', error)
    }
  }

  const handleSuggestTags = (tweet: Tweet) => {
    setSelectedTweet(tweet)
    setShowSuggestionModal(true)
  }

  const clearFilters = () => {
    setSelectedAuthors([])
    setSelectedTags([])
    setSearchTerm('')
    setExcludeRetweets(false)
    setCurrentPage(1)
  }

  const renderHierarchicalTag = (tag: TagFacet, level: number = 0) => {
    const isExpanded = expandedTags.has(tag.tag)
    const hasChildren = tag.children && tag.children.length > 0
    const isSelected = selectedTags.includes(tag.tag)

    return (
      <div key={tag.tag} className="w-full">
        <div 
          className={cn(
            "flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-gray-50 cursor-pointer transition-colors",
            isSelected && "bg-blue-50",
            level > 0 && "ml-4"
          )}
          onClick={() => toggleTag(tag.tag)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleTagExpansion(tag.tag)
              }}
              className="p-0.5 hover:bg-gray-200 rounded"
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
          >
            <span>{tag.display_name || tag.tag}</span>
            <span className="ml-2 text-xs opacity-70">{tag.count}</span>
          </TagBadge>
        </div>
        
        {hasChildren && isExpanded && (
          <div className="mt-1">
            {tag.children!.map(child => renderHierarchicalTag(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  const displayedTags = showHierarchy ? hierarchyFacets : (showAllTags ? facets.tags : facets.tags.slice(0, 20))

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Twitter/X Feed</h1>
        <p className="text-gray-600">Browse and analyze collected tweets with advanced filtering</p>
      </div>

      {/* Search Bar */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
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
            {(selectedAuthors.length > 0 || selectedTags.length > 0 || searchTerm) && (
              <Button onClick={clearFilters} variant="outline">
                Clear Filters
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Filters */}
        <div className="lg:col-span-1 space-y-4">
          {/* Authors Filter */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="h-4 w-4" />
                Authors
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[300px] px-4 pb-4">
                {facets.authors.map(author => (
                  <div
                    key={author.username}
                    className={cn(
                      "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 cursor-pointer transition-colors",
                      selectedAuthors.includes(author.username) && "bg-blue-50"
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

          {/* Tags Filter */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Hash className="h-4 w-4" />
                  Tags
                </CardTitle>
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant={showHierarchy ? "default" : "outline"}
                    onClick={() => setShowHierarchy(!showHierarchy)}
                    className="h-7 px-2"
                  >
                    {showHierarchy ? <GitBranch className="h-3 w-3" /> : <Layers className="h-3 w-3" />}
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ScrollArea className="h-[400px] px-4 pb-4">
                {showHierarchy ? (
                  <div className="space-y-1">
                    {hierarchyFacets.map(tag => renderHierarchicalTag(tag))}
                  </div>
                ) : (
                  <div className="space-y-2">
                    {displayedTags.map(tag => (
                      <div
                        key={tag.tag}
                        className={cn(
                          "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 cursor-pointer transition-colors",
                          selectedTags.includes(tag.tag) && "bg-blue-50"
                        )}
                        onClick={() => toggleTag(tag.tag)}
                      >
                        <div className="flex items-center gap-2">
                          <Checkbox
                            checked={selectedTags.includes(tag.tag)}
                            onCheckedChange={() => toggleTag(tag.tag)}
                          />
                          <TagBadge variant="default" size="sm">
                            {tag.display_name || tag.tag}
                          </TagBadge>
                        </div>
                        <Badge variant="secondary" className="text-xs">
                          {tag.count}
                        </Badge>
                      </div>
                    ))}
                  </div>
                )}
                {!showHierarchy && facets.tags.length > 20 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full mt-2"
                    onClick={() => setShowAllTags(!showAllTags)}
                  >
                    {showAllTags ? (
                      <>
                        <EyeOff className="h-3 w-3 mr-2" />
                        Show Less
                      </>
                    ) : (
                      <>
                        <Eye className="h-3 w-3 mr-2" />
                        Show All ({facets.tags.length})
                      </>
                    )}
                  </Button>
                )}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
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
              {selectedTags.length > 0 && (
                <Badge variant="secondary" className="py-1.5 px-3">
                  {selectedTags.length} tag{selectedTags.length !== 1 ? 's' : ''} selected
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">
                Page {currentPage} of {totalPages}
              </span>
            </div>
          </div>

          {/* Tweets List */}
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : tweets.length === 0 ? (
            <Card>
              <CardContent className="py-12 text-center">
                <Twitter className="h-12 w-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No tweets found matching your filters</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {tweets.map(tweet => (
                <TweetCardModern
                  key={tweet.id}
                  tweet={tweet}
                  onTagAdded={handleTagAdded}
                  onTagRemoved={handleTagRemoved}
                  onSuggestTags={handleSuggestTags}
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
          onTagsUpdated={fetchTweets}
        />
      )}
    </div>
  )
}