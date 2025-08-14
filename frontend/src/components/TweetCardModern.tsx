import React, { useState, useRef, useEffect } from 'react'
import ReactDOM from 'react-dom'
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import { Separator } from "@/components/ui/separator"
import { 
  Twitter, 
  Heart, 
  MessageCircle, 
  Repeat2, 
  Plus, 
  X, 
  Sparkles,
  Hash,
  Image as ImageIcon,
  Film,
  Calendar,
  User,
  ExternalLink,
  Tag
} from 'lucide-react'
import { cn } from "@/lib/utils"

interface TweetCardProps {
  tweet: {
    id: string
    text: string
    author_username: string
    created_at: string
    metrics: {
      likes: number
      retweets: number
      replies: number
    }
    media: any[]
    tags: { tag: string; type: string }[]
  }
  onTagAdded: (tweetId: string, tag: string) => void
  onTagRemoved: (tweetId: string, tag: string) => void
  onTweetClick?: (tweet: any) => void
  onSuggestTags?: (tweet: any) => void
}

export default function TweetCardModern({ 
  tweet, 
  onTagAdded, 
  onTagRemoved, 
  onTweetClick, 
  onSuggestTags 
}: TweetCardProps) {
  const [isAddingTag, setIsAddingTag] = useState(false)
  const [newTag, setNewTag] = useState('')
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null)
  const [showTagCreationForm, setShowTagCreationForm] = useState(false)
  const [tagCreationText, setTagCreationText] = useState('')
  const [brokenImages, setBrokenImages] = useState<Set<number>>(new Set())
  const selectedTextRef = useRef<string>('')
  const tweetContentRef = useRef<HTMLDivElement>(null)

  const handleAddTag = () => {
    if (newTag.trim()) {
      onTagAdded(tweet.id, newTag.trim())
      setNewTag('')
      setIsAddingTag(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  const openTweetInTwitter = () => {
    window.open(`https://twitter.com/${tweet.author_username}/status/${tweet.id}`, '_blank')
  }

  const handleTextSelection = () => {
    const selection = window.getSelection()
    if (selection && selection.toString().trim()) {
      selectedTextRef.current = selection.toString().trim()
    }
  }

  const handleContextMenu = (e: React.MouseEvent) => {
    const selection = window.getSelection()
    if (selection && selection.toString().trim()) {
      e.preventDefault()
      selectedTextRef.current = selection.toString().trim()
      setContextMenu({ x: e.clientX, y: e.clientY })
    }
  }

  const handleCreateTag = () => {
    setTagCreationText(selectedTextRef.current)
    setShowTagCreationForm(true)
    setContextMenu(null)
  }

  const handleImageError = (index: number) => {
    setBrokenImages(prev => new Set(prev).add(index))
  }

  const getTagVariant = (type: string) => {
    switch(type) {
      case 'llm':
      case 'ai':
        return 'ai'
      case 'similar':
      case 'existing':
        return 'similar'
      case 'entity':
        return 'entity'
      case 'new':
        return 'new'
      case 'manual':
      default:
        return 'default'
    }
  }

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setContextMenu(null)
      setShowTagCreationForm(false)
    }
    if (contextMenu || showTagCreationForm) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [contextMenu, showTagCreationForm])

  const hasVisibleMedia = tweet.media.length > 0 && 
    tweet.media.some((_, index) => !brokenImages.has(index))

  return (
    <>
      <Card className="mb-4 hover:shadow-lg transition-all duration-200 border-gray-200">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-blue-600 flex items-center justify-center">
                <User className="h-5 w-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-gray-900">@{tweet.author_username}</span>
                  <Badge variant="outline" className="text-xs">
                    <Twitter className="h-3 w-3 mr-1" />
                    X
                  </Badge>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-500 mt-0.5">
                  <Calendar className="h-3 w-3" />
                  {formatDate(tweet.created_at)}
                </div>
              </div>
            </div>
            <Button
              onClick={openTweetInTwitter}
              size="sm"
              variant="ghost"
              className="rounded-full hover:bg-blue-50"
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pb-3">
          <div 
            ref={tweetContentRef}
            className="text-gray-800 leading-relaxed whitespace-pre-wrap select-text"
            onMouseUp={handleTextSelection}
            onContextMenu={handleContextMenu}
          >
            {tweet.text}
          </div>

          {hasVisibleMedia && (
            <div className={cn(
              "mt-3 grid gap-2 rounded-lg overflow-hidden",
              tweet.media.length === 1 && "grid-cols-1",
              tweet.media.length === 2 && "grid-cols-2",
              tweet.media.length === 3 && "grid-cols-2",
              tweet.media.length >= 4 && "grid-cols-2"
            )}>
              {tweet.media.map((media, index) => (
                !brokenImages.has(index) && (
                  <div 
                    key={index} 
                    className={cn(
                      "relative bg-gray-100 rounded-lg overflow-hidden",
                      tweet.media.length === 3 && index === 0 && "col-span-2"
                    )}
                  >
                    {media.type === 'photo' ? (
                      <img 
                        src={media.media_url || media.url}
                        alt={`Media ${index + 1}`}
                        className="w-full h-full object-cover"
                        onError={() => handleImageError(index)}
                      />
                    ) : media.type === 'animated_gif' || media.type === 'video' ? (
                      <div className="flex items-center justify-center h-32 bg-gray-200">
                        <Film className="h-8 w-8 text-gray-400" />
                        <span className="ml-2 text-sm text-gray-500">
                          {media.type === 'animated_gif' ? 'GIF' : 'Video'}
                        </span>
                      </div>
                    ) : (
                      <div className="flex items-center justify-center h-32">
                        <ImageIcon className="h-8 w-8 text-gray-400" />
                      </div>
                    )}
                  </div>
                )
              ))}
            </div>
          )}

          <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-100">
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Heart className="h-4 w-4" />
              <span>{tweet.metrics.likes.toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <Repeat2 className="h-4 w-4" />
              <span>{tweet.metrics.retweets.toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <MessageCircle className="h-4 w-4" />
              <span>{tweet.metrics.replies.toLocaleString()}</span>
            </div>
          </div>
        </CardContent>

        <CardFooter className="flex-col items-start gap-3 pt-0">
          <div className="flex flex-wrap gap-2 w-full">
            {tweet.tags.map((tag, index) => (
              <TagBadge
                key={`${tag.tag}-${index}`}
                variant={getTagVariant(tag.type)}
                removable
                onRemove={() => onTagRemoved(tweet.id, tag.tag)}
                icon={tag.type === 'ai' || tag.type === 'llm' ? <Sparkles className="h-3 w-3" /> : <Hash className="h-3 w-3" />}
              >
                {tag.tag}
              </TagBadge>
            ))}
          </div>

          <div className="flex gap-2 w-full">
            {!isAddingTag ? (
              <>
                <Button
                  onClick={() => setIsAddingTag(true)}
                  size="sm"
                  variant="outline"
                  className="gap-1"
                >
                  <Plus className="h-3 w-3" />
                  Add Tag
                </Button>
                {onSuggestTags && (
                  <Button
                    onClick={() => onSuggestTags(tweet)}
                    size="sm"
                    variant="outline"
                    className="gap-1"
                  >
                    <Sparkles className="h-3 w-3" />
                    Suggest Tags
                  </Button>
                )}
              </>
            ) : (
              <div className="flex gap-2 flex-1">
                <Input
                  value={newTag}
                  onChange={(e) => setNewTag(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
                  placeholder="Enter tag name..."
                  className="flex-1 h-8"
                  autoFocus
                />
                <Button onClick={handleAddTag} size="sm" variant="default">
                  <Plus className="h-3 w-3" />
                </Button>
                <Button 
                  onClick={() => {
                    setIsAddingTag(false)
                    setNewTag('')
                  }} 
                  size="sm" 
                  variant="ghost"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            )}
          </div>
        </CardFooter>
      </Card>

      {/* Context Menu */}
      {contextMenu && ReactDOM.createPortal(
        <div
          className="fixed z-50 min-w-[150px] rounded-md border bg-white shadow-md"
          style={{ 
            left: `${contextMenu.x}px`, 
            top: `${contextMenu.y}px`
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="flex items-center gap-2 w-full px-3 py-2 text-sm hover:bg-gray-100"
            onClick={handleCreateTag}
          >
            <Tag className="h-4 w-4" />
            Create Tag
          </button>
        </div>,
        document.body
      )}

      {/* Tag Creation Form */}
      {showTagCreationForm && ReactDOM.createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card 
            className="w-96 max-w-[90vw]"
            onClick={(e) => e.stopPropagation()}
          >
            <CardHeader>
              <h3 className="text-lg font-semibold">Create Tag from Selection</h3>
            </CardHeader>
            <CardContent>
              <Input
                value={tagCreationText}
                onChange={(e) => setTagCreationText(e.target.value)}
                placeholder="Tag name..."
                className="mb-4"
                autoFocus
              />
              <div className="text-sm text-gray-500 mb-4">
                Selected text: "{selectedTextRef.current}"
              </div>
            </CardContent>
            <CardFooter className="gap-2">
              <Button
                onClick={() => {
                  if (tagCreationText.trim()) {
                    onTagAdded(tweet.id, tagCreationText.trim())
                    setShowTagCreationForm(false)
                    setTagCreationText('')
                  }
                }}
                size="sm"
              >
                Create Tag
              </Button>
              <Button
                onClick={() => {
                  setShowTagCreationForm(false)
                  setTagCreationText('')
                }}
                size="sm"
                variant="outline"
              >
                Cancel
              </Button>
            </CardFooter>
          </Card>
        </div>,
        document.body
      )}
    </>
  )
}