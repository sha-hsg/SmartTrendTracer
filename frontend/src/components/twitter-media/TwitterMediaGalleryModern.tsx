import { useState, useEffect } from 'react'
import axios from 'axios'
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { cn } from "@/lib/utils"
import {
  Film,
  Download,
  ExternalLink,
  X,
  ChevronLeft,
  ChevronRight,
  Loader2,
  BarChart3,
  ImageOff,
  Maximize2
} from 'lucide-react'
import MediaCard, { MediaItem, MediaStats, Author, MediaType, getMediaIcon } from './MediaCard'
import MediaFilterBar from './MediaFilterBar'

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
  const [tag, _setTag] = useState<string>('')
  const [search, setSearch] = useState<string>('')
  const [days, setDays] = useState(7)
  const [sortBy, setSortBy] = useState<string>('date_desc')
  const [_total, setTotal] = useState(0)
  const [totalPages, setTotalPages] = useState(0)

  // View mode
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
  const [gridColumns, _setGridColumns] = useState(4)
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
        `/api/media-gallery/gallery?${params}`
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
        `/api/media-gallery/stats?days=${days}`
      )
      setStats(response.data)
    } catch (error) {
      console.error('Error loading stats:', error)
    }
  }

  const loadAuthors = async () => {
    try {
      const response = await axios.get(
        `/api/media-gallery/authors?days=${days}`
      )
      setAuthors(response.data)
    } catch (error) {
      console.error('Error loading authors:', error)
    }
  }

  const loadMediaTypes = async () => {
    try {
      const response = await axios.get(
        `/api/media-gallery/types`
      )
      setMediaTypes(response.data)
    } catch (error) {
      console.error('Error loading media types:', error)
    }
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
      <MediaFilterBar
        search={search}
        onSearchChange={setSearch}
        days={days}
        onDaysChange={setDays}
        mediaType={mediaType}
        onMediaTypeChange={setMediaType}
        mediaTypes={mediaTypes}
        author={author}
        onAuthorChange={setAuthor}
        authors={authors}
        sortBy={sortBy}
        onSortByChange={setSortBy}
        viewMode={viewMode}
        onViewModeChange={setViewMode}
        selectedCount={selectedMedia.size}
        onClearSelection={() => setSelectedMedia(new Set())}
        onResetPage={() => setPage(1)}
      />

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
            {media.map((item, index) => (
              <MediaCard
                key={item.id}
                item={item}
                index={index}
                viewMode={viewMode}
                isSelected={selectedMedia.has(item.id)}
                isBroken={brokenImages.has(item.id)}
                onToggleSelection={toggleMediaSelection}
                onOpenLightbox={openLightbox}
                onDownload={downloadMedia}
                onImageError={handleImageError}
              />
            ))}
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
