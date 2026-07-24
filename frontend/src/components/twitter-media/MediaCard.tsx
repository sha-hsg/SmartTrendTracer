import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import {
  Image as ImageIcon,
  Film,
  FileVideo,
  Heart,
  Repeat2,
  Download,
  ExternalLink,
  Eye,
  CheckSquare,
  Square,
  ImageOff,
  Play,
} from 'lucide-react'

export interface MediaItem {
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

export interface MediaStats {
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

export interface Author {
  username: string
  name: string
  media_count: number
}

export interface MediaType {
  type: string
  count: number
  icon: string
  label: string
}

export function getMediaIcon(type: string) {
  switch(type) {
    case 'photo': return <ImageIcon className="h-4 w-4" />
    case 'video': return <Film className="h-4 w-4" />
    case 'animated_gif': return <FileVideo className="h-4 w-4" />
    default: return <ImageIcon className="h-4 w-4" />
  }
}

export function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

export function formatDuration(ms: number) {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

interface MediaCardProps {
  item: MediaItem
  index: number
  viewMode: 'grid' | 'list'
  isSelected: boolean
  isBroken: boolean
  onToggleSelection: (id: string) => void
  onOpenLightbox: (item: MediaItem, index: number) => void
  onDownload: (item: MediaItem) => void
  onImageError: (id: string) => void
}

export default function MediaCard({
  item,
  index,
  viewMode,
  isSelected,
  isBroken,
  onToggleSelection,
  onOpenLightbox,
  onDownload,
  onImageError,
}: MediaCardProps) {
  return (
    <Card
      key={item.id}
      className={cn(
        "group relative overflow-hidden cursor-pointer transition-all",
        isSelected && "ring-2 ring-blue-500",
        viewMode === 'grid' ? 'aspect-square' : 'h-32'
      )}
      onClick={() => viewMode === 'grid' && onOpenLightbox(item, index)}
    >
      {/* Selection checkbox */}
      <div className="absolute top-2 left-2 z-10">
        <Button
          size="sm"
          variant={isSelected ? "default" : "secondary"}
          className="h-6 w-6 p-0"
          onClick={(e) => {
            e.stopPropagation()
            onToggleSelection(item.id)
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
                  onError={() => onImageError(item.id)}
                />
              ) : (
                <div className="relative h-full">
                  <img
                    src={item.thumbnail_url || item.url || ''}
                    alt={'Video thumbnail'}
                    className="w-full h-full object-cover"
                    onError={() => onImageError(item.id)}
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
                  onError={() => onImageError(item.id)}
                />
              ) : (
                <div className="relative h-full">
                  <img
                    src={item.thumbnail_url || item.url || ''}
                    alt={'Video thumbnail'}
                    className="w-full h-full object-cover rounded"
                    onError={() => onImageError(item.id)}
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
                    onOpenLightbox(item, index)
                  }}
                >
                  <Eye className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDownload(item)
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
