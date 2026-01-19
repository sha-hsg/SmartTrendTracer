import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import { 
  Image as ImageIcon, 
  Film, 
  FileVideo, 
  Grid3x3, 
  List, 
  Search,
  Download,
  ExternalLink,
  Heart,
  Repeat2,
  X,
  ChevronLeft,
  ChevronRight,
  Loader2,
  BarChart3,
  Eye,
  CheckSquare,
  Square,
  ImageOff,
  Play,
  Maximize2
} from 'lucide-react'

interface MediaItem {
  id: string
  tweet_id: string
  type: string
  url: string
  thumbnail_url: string
  preview_image_url?: string
  alt_text?: string
  media_key?: string
  width?: number | null
  height?: number | null
  duration_ms?: number | null
  author_username: string
  author_id: string
  tweet_text: string
  created_at: string
  metrics: {
    likes?: number
    retweets?: number
    replies?: number
    retweet_count?: number
    like_count?: number
    reply_count?: number
    quote_count?: number
  }
}

interface MediaStats {
  period_days: number
  tweets_with_media: number
  total_tweets: number
  media_percentage: number
  media_types: Record<string, number>
  top_authors: Array<{
    username: string
    tweet_count: number
    media_count: number
  }>
}

interface Author {
  username: string
  name: string
  media_count: number
}

interface MediaType {
  type: string
  count: number
  icon: string
  label: string
}

export default function TwitterMediaGalleryModern() {
  const [media, setMedia] = useState<MediaItem[]>([])
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState<MediaStats | null>(null)
  const [authors, setAuthors] = useState<Author[]>([])
  const [mediaTypes, setMediaTypes] = useState<MediaType[]>([])
  const [selectedMedia, setSelectedMedia] = useState<Set<string>>(new Set())
  const [lightboxMedia, setLightboxMedia] = useState<MediaItem | null>(null)
  const [lightboxIndex, setLightboxIndex] = useState<number>(-1)
  
  // Filters
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [mediaType, setMediaType] = useState<string>('all')
  const [author, setAuthor] = useState<string>('all')
  const [tag, setTag] = useState<string>('')
  const [search, setSearch] = useState<string>('')
  const [days, setDays] = useState(7)
  const [sortBy, setSortBy] = useState<string>('date_desc')
  const [total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)
  
  // View mode
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [gridColumns, setGridColumns] = useState(4)
  const [brokenImages, setBrokenImages] = useState<Set<string>>(new Set())

  useEffect(() => {
    loadMedia()
    loadStats()
    loadAuthors()
    loadMediaTypes()
  }, [page, mediaType, author, tag, search, days, sortBy])

  const loadMedia = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
        days: days.toString(),
        sort_by: sortBy
      })
      
      if (mediaType && mediaType !== 'all') params.append('media_type', mediaType)
      if (author && author !== 'all') params.append('author', author)
      if (tag) params.append('tag', tag)
      if (search) params.append('search', search)

      const response = await axios.get(
        `http://localhost:8000/api/media-gallery/gallery?${params}`
      )

      setMedia(response.data.media || [])
      setTotal(response.data.total || 0)
      setTotalPages(response.data.total_pages || 1)
    } catch (error) {
      console.error('Error loading media:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/media-gallery/stats?days=${days}`
      )
      setStats(response.data)
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const loadAuthors = async () => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/media-gallery/authors?days=${days}`
      )
      setAuthors(response.data)
    } catch (error) {
      console.error('Error loading authors:', error)
    }
  }

  const loadMediaTypes = async () => {
    try {
      const response = await axios.get(
        'http://localhost:8000/api/media-gallery/types'
      )
      setMediaTypes(response.data)
    } catch (error) {
      console.error('Error loading media types:', error)
    }
  }

  const getMediaIcon = (type: string) => {
    switch(type) {
      case 'photo': return <ImageIcon className="h-4 w-4" />
      case 'video': return <Film className="h-4 w-4" />
      case 'animated_gif': return <FileVideo className="h-4 w-4" />
      default: return <ImageIcon className="h-4 w-4" />
    }
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  }

  const formatDuration = (ms: number) => {
    const seconds = Math.floor(ms / 1000)
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  const toggleMediaSelection = (id: string) => {
    setSelectedMedia(prev => {
      const newSet = new Set(prev)
      if (newSet.has(id)) {
        newSet.delete(id)
      } else {
        newSet.add(id)
      }
      return newSet
    })
  }

  const openLightbox = (item: MediaItem, index: number) => {
    setLightboxMedia(item)
    setLightboxIndex(index)
  }

  const navigateLightbox = (direction: 'prev' | 'next') => {
    if (!media.length) return
    
    let newIndex = lightboxIndex
    if (direction === 'prev') {
      newIndex = lightboxIndex > 0 ? lightboxIndex - 1 : media.length - 1
    } else {
      newIndex = lightboxIndex < media.length - 1 ? lightboxIndex + 1 : 0
    }
    
    setLightboxMedia(media[newIndex])
    setLightboxIndex(newIndex)
  }

  const handleImageError = (id: string) => {
    setBrokenImages(prev => new Set(prev).add(id))
  }

  const downloadMedia = async (item: MediaItem) => {
    if (!item.url) return
    
    try {
      const response = await fetch(item.url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `media_${item.id}.${item.type === 'photo' ? 'jpg' : 'mp4'}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)
    } catch (error) {
      console.error('Download failed:', error)
    }
  }

  const renderMediaCard = (item: MediaItem, index: number) => {
    const isBroken = brokenImages.has(item.id)
    const isSelected = selectedMedia.has(item.id)
    
    return (
      <Card 
        key={item.id}
        className={cn(
          "group relative overflow-hidden cursor-pointer transition-all",
          isSelected && "ring-2 ring-blue-500",
          viewMode === 'grid' ? 'aspect-square' : 'h-32'
        )}
        onClick={() => viewMode === 'grid' && openLightbox(item, index)}
      >
        {/* Selection checkbox */}
        <div className="absolute top-2 left-2 z-10">
          <Button
            size="sm"
            variant={isSelected ? "default" : "secondary"}
            className="h-6 w-6 p-0"
            onClick={(e) => {
              e.stopPropagation()
              toggleMediaSelection(item.id)
            }}
          >
            {isSelected ? <CheckSquare className="h-3 w-3" /> : <Square className="h-3 w-3" />}
          </Button>
        </div>

        {/* Media type badge */}
        <div className="absolute top-2 right-2 z-10">
          <Badge variant="secondary" className="bg-black/50 text-white">
            {getMediaIcon(item.type)}
          </Badge>
        </div>

        {/* Media content */}
        {viewMode === 'grid' ? (
          <div className="relative h-full">
            {!isBroken ? (
              <>
                {item.type === 'photo' ? (
                  <img
                    src={item.url || item.thumbnail_url || ''}
                    alt={'Media'}
                    className="w-full h-full object-cover"
                    onError={() => handleImageError(item.id)}
                  />
                ) : (
                  <div className="relative h-full">
                    <img
                      src={item.thumbnail_url || item.url || ''}
                      alt={'Video thumbnail'}
                      className="w-full h-full object-cover"
                      onError={() => handleImageError(item.id)}
                    />
                    <div className="absolute inset-0 flex items-center justify-center">
                      <div className="bg-black/50 rounded-full p-3">
                        <Play className="h-8 w-8 text-white" />
                      </div>
                    </div>
                    {item.duration_ms && (
                      <Badge className="absolute bottom-2 right-2 bg-black/70 text-white">
                        {formatDuration(item.duration_ms)}
                      </Badge>
                    )}
                  </div>
                )}
              </>
            ) : (
              <div className="h-full flex items-center justify-center bg-gray-100">
                <div className="text-center">
                  <ImageOff className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-xs text-gray-500">Media unavailable</p>
                </div>
              </div>
            )}

            {/* Hover overlay */}
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity p-3 flex flex-col justify-between">
              <div className="text-white text-xs">
                <p className="font-semibold mb-1">@{item.author_username}</p>
                <p className="line-clamp-2">{item.tweet_text}</p>
              </div>
              <div className="flex items-center justify-between text-white text-xs">
                <div className="flex gap-3">
                  <span className="flex items-center gap-1">
                    <Heart className="h-3 w-3" />
                    {item.metrics.like_count || item.metrics.likes || 0}
                  </span>
                  <span className="flex items-center gap-1">
                    <Repeat2 className="h-3 w-3" />
                    {item.metrics.retweet_count || item.metrics.retweets || 0}
                  </span>
                </div>
                <span>{formatDate(item.created_at)}</span>
              </div>
            </div>
          </div>
        ) : (
          // List view
          <div className="flex gap-4 p-4">
            <div className="w-32 h-24 shrink-0">
              {!isBroken ? (
                item.type === 'photo' ? (
                  <img
                    src={item.url || item.thumbnail_url || ''}
                    alt={'Media'}
                    className="w-full h-full object-cover rounded"
                    onError={() => handleImageError(item.id)}
                  />
                ) : (
                  <div className="relative h-full">
                    <img
                      src={item.thumbnail_url || item.url || ''}
                      alt={'Video thumbnail'}
                      className="w-full h-full object-cover rounded"
                      onError={() => handleImageError(item.id)}
                    />
                    <Play className="absolute inset-0 m-auto h-6 w-6 text-white" />
                  </div>
                )
              ) : (
                <div className="w-full h-full bg-gray-100 rounded flex items-center justify-center">
                  <ImageOff className="h-6 w-6 text-gray-400" />
                </div>
              )}
            </div>
            
            <div className="flex-1 min-w-0">
              <div className="flex items-start justify-between mb-1">
                <div>
                  <p className="font-semibold text-sm">@{item.author_username}</p>
                  <p className="text-xs text-gray-500">{formatDate(item.created_at)}</p>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation()
                      openLightbox(item, index)
                    }}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation()
                      downloadMedia(item)
                    }}
                  >
                    <Download className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation()
                      window.open(`https://twitter.com/${item.author_username}/status/${item.tweet_id}`, '_blank')
                    }}
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <p className="text-sm text-gray-700 line-clamp-2 mb-2">{item.tweet_text}</p>
              <div className="flex items-center gap-4 text-xs text-gray-500">
                <span className="flex items-center gap-1">
                  <Heart className="h-3 w-3" />
                  {item.metrics.like_count || item.metrics.likes || 0}
                </span>
                <span className="flex items-center gap-1">
                  <Repeat2 className="h-3 w-3" />
                  {item.metrics.retweet_count || item.metrics.retweets || 0}
                </span>
                {/* Tags removed - not in API response */
                false && (
                  <div className="flex gap-1">
                    {[].slice(0, 3).map(t => (
                      <Badge key={t} variant="secondary" className="text-xs">
                        {t}
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </Card>
    )
  }

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Media Gallery</h1>
        <p className="text-gray-600">Browse and analyze media from collected tweets</p>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Media Tweets</p>
                  <p className="text-2xl font-bold">{stats.tweets_with_media}</p>
                </div>
                <BarChart3 className="h-8 w-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          
          {stats?.media_types && Object.entries(stats.media_types).map(([type, count]) => (
            <Card key={type}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500 capitalize">{type}s</p>
                    <p className="text-2xl font-bold">{count}</p>
                  </div>
                  {getMediaIcon(type)}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Filters and Controls */}
      <Card className="mb-6">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  type="text"
                  placeholder="Search media..."
                  value={search}
                  onChange={(e) => {
                    setSearch(e.target.value)
                    setPage(1)
                  }}
                  className="pl-10"
                />
              </div>
            </div>

            {/* Time range */}
            <Select value={days.toString()} onValueChange={(v) => setDays(parseInt(v))}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">Last 24h</SelectItem>
                <SelectItem value="7">Last 7 days</SelectItem>
                <SelectItem value="30">Last 30 days</SelectItem>
                <SelectItem value="90">Last 90 days</SelectItem>
              </SelectContent>
            </Select>

            {/* Media type filter */}
            <Select value={mediaType} onValueChange={setMediaType}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All media types" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All types</SelectItem>
                {mediaTypes.map(type => (
                  <SelectItem key={type.type} value={type.type}>
                    {type.label} ({type.count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Author filter */}
            <Select value={author} onValueChange={setAuthor}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="All authors" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All authors</SelectItem>
                {authors.map(a => (
                  <SelectItem key={a.username} value={a.username}>
                    @{a.username} ({a.media_count})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Sort */}
            <Select value={sortBy} onValueChange={setSortBy}>
              <SelectTrigger className="w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="date_desc">Newest first</SelectItem>
                <SelectItem value="date_asc">Oldest first</SelectItem>
                <SelectItem value="likes_desc">Most liked</SelectItem>
                <SelectItem value="retweets_desc">Most retweeted</SelectItem>
              </SelectContent>
            </Select>

            {/* View mode toggle */}
            <div className="flex gap-1">
              <Button
                size="sm"
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                onClick={() => setViewMode('grid')}
              >
                <Grid3x3 className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant={viewMode === 'list' ? 'default' : 'outline'}
                onClick={() => setViewMode('list')}
              >
                <List className="h-4 w-4" />
              </Button>
            </div>
          </div>

          {/* Selected items actions */}
          {selectedMedia.size > 0 && (
            <div className="mt-4 flex items-center justify-between">
              <Badge variant="secondary">
                {selectedMedia.size} item{selectedMedia.size !== 1 ? 's' : ''} selected
              </Badge>
              <div className="flex gap-2">
                <Button size="sm" variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Download Selected
                </Button>
                <Button 
                  size="sm" 
                  variant="ghost"
                  onClick={() => setSelectedMedia(new Set())}
                >
                  Clear Selection
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Media Grid/List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : media.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <ImageOff className="h-12 w-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500">No media found matching your filters</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <div className={cn(
            viewMode === 'grid' 
              ? `grid grid-cols-2 md:grid-cols-3 lg:grid-cols-${gridColumns} gap-4`
              : 'space-y-4'
          )}>
            {media.map((item, index) => renderMediaCard(item, index))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="mt-6 flex items-center justify-center gap-2">
              <Button
                onClick={() => setPage(prev => Math.max(1, prev - 1))}
                disabled={page === 1}
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
                  } else if (page <= 3) {
                    pageNum = i + 1
                  } else if (page >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = page - 2 + i
                  }
                  
                  return (
                    <Button
                      key={pageNum}
                      onClick={() => setPage(pageNum)}
                      variant={page === pageNum ? "default" : "outline"}
                      size="sm"
                      className="w-10"
                    >
                      {pageNum}
                    </Button>
                  )
                })}
              </div>
              
              <Button
                onClick={() => setPage(prev => Math.min(totalPages, prev + 1))}
                disabled={page === totalPages}
                variant="outline"
                size="sm"
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          )}
        </>
      )}

      {/* Lightbox Modal */}
      <Dialog open={!!lightboxMedia} onOpenChange={() => setLightboxMedia(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] p-0 overflow-hidden">
          {/* Hidden but required for accessibility */}
          <DialogTitle className="sr-only">
            Media Preview - {lightboxMedia?.type === 'photo' ? 'Image' : lightboxMedia?.type || 'Media'}
          </DialogTitle>
          <DialogDescription className="sr-only">
            Viewing media from @{lightboxMedia?.author_username}. Use arrow keys to navigate between media items.
          </DialogDescription>
          {lightboxMedia && (
            <div className="relative">
              {/* Navigation buttons */}
              <Button
                size="sm"
                variant="ghost"
                className="absolute left-2 top-1/2 -translate-y-1/2 z-10 bg-black/50 text-white hover:bg-black/70"
                onClick={() => navigateLightbox('prev')}
              >
                <ChevronLeft className="h-6 w-6" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                className="absolute right-2 top-1/2 -translate-y-1/2 z-10 bg-black/50 text-white hover:bg-black/70"
                onClick={() => navigateLightbox('next')}
              >
                <ChevronRight className="h-6 w-6" />
              </Button>

              {/* Close button */}
              <Button
                size="sm"
                variant="ghost"
                className="absolute right-2 top-2 z-10 bg-black/50 text-white hover:bg-black/70"
                onClick={() => setLightboxMedia(null)}
              >
                <X className="h-4 w-4" />
              </Button>

              {/* Media display */}
              {lightboxMedia.type === 'photo' ? (
                <img
                  src={lightboxMedia.url || lightboxMedia.preview_image_url || ''}
                  alt={lightboxMedia.alt_text || 'Media'}
                  className="w-full h-auto max-h-[80vh] object-contain"
                />
              ) : (
                <div className="relative">
                  {lightboxMedia.url ? (
                    <>
                      <video
                        src={lightboxMedia.url}
                        poster={lightboxMedia.preview_image_url || ''}
                        controls
                        autoPlay
                        className="w-full h-auto max-h-[80vh] object-contain"
                        onClick={(e) => e.stopPropagation()}
                      />
                      {/* Fullscreen button */}
                      <Button
                        size="sm"
                        variant="secondary"
                        className="absolute top-2 right-2 bg-black/50 hover:bg-black/70 text-white"
                        onClick={(e) => {
                          e.stopPropagation()
                          const video = e.currentTarget.parentElement?.querySelector('video')
                          if (video && video.requestFullscreen) {
                            video.requestFullscreen()
                          }
                        }}
                      >
                        <Maximize2 className="h-4 w-4" />
                      </Button>
                    </>
                  ) : (
                    <div className="relative">
                      {lightboxMedia.preview_image_url ? (
                        <img
                          src={lightboxMedia.preview_image_url}
                          alt="Video preview"
                          className="w-full h-auto max-h-[80vh] object-contain"
                        />
                      ) : (
                        <div className="flex items-center justify-center h-96 bg-gray-900">
                          <Film className="h-16 w-16 text-gray-600" />
                        </div>
                      )}
                      <div className="absolute inset-0 flex items-center justify-center bg-black/60">
                        <div className="text-white text-center p-6 bg-black/80 rounded-lg">
                          <Film className="h-12 w-12 mx-auto mb-3" />
                          <p className="text-lg font-medium mb-2">Video Unavailable</p>
                          <p className="text-sm opacity-75">The video URL has expired. Only preview image is available.</p>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Media info */}
              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-4 text-white">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">@{lightboxMedia.author_username}</p>
                    <p className="text-sm opacity-90">{lightboxMedia.tweet_text}</p>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-white hover:bg-white/20"
                      onClick={() => downloadMedia(lightboxMedia)}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-white hover:bg-white/20"
                      onClick={() => window.open(`https://twitter.com/${lightboxMedia.author_username}/status/${lightboxMedia.tweet_id}`, '_blank')}
                    >
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}