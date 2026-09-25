import React, { useState, useRef, useEffect } from 'react'
import ReactDOM from 'react-dom'
import { Card, CardContent, CardFooter, CardHeader } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { 
  Heart, 
  MessageCircle, 
  Repeat2, 
  Plus, 
  X, 
  Sparkles,
  Image as ImageIcon,
  Film,
  Calendar,
  User,
  ExternalLink,
  Tag,
  Play
} from 'lucide-react'
import { Tweet, Concept } from '@/types/concept'
import conceptService from '@/services/conceptService'
import { decodeHtmlEntities } from '@/utils/htmlDecoder'

interface TweetCardProps {
  tweet: Tweet
  onConceptAdded: (tweetId: string, concept: Concept) => void
  onConceptRemoved: (tweetId: string, conceptId: string) => void
  onTweetClick?: (tweet: Tweet) => void
  onSuggestConcepts?: (tweet: Tweet) => void
}

const TweetCardModern = React.memo(function TweetCardModern({
  tweet,
  onConceptAdded,
  onConceptRemoved,
  onTweetClick,
  onSuggestConcepts
}: TweetCardProps) {
  const [isAddingConcept, setIsAddingConcept] = useState(false)
  const [newConceptText, setNewConceptText] = useState('')
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number } | null>(null)
  const [showConceptCreationForm, setShowConceptCreationForm] = useState(false)
  const [conceptCreationText, setConceptCreationText] = useState('')
  const [brokenImages, setBrokenImages] = useState<Set<number>>(new Set())
  const [isCreatingConcept, setIsCreatingConcept] = useState(false)
  const selectedTextRef = useRef<string>('')
  const tweetContentRef = useRef<HTMLDivElement>(null)
  const [playingVideos, setPlayingVideos] = useState<Set<number>>(new Set())
  const videoRefs = useRef<{ [key: number]: HTMLVideoElement | null }>({})
  const [hoveredVideo, setHoveredVideo] = useState<number | null>(null)
  const [profileImageBroken, setProfileImageBroken] = useState(false)

  const handleAddConcept = async () => {
    if (newConceptText.trim() && !isCreatingConcept) {
      setIsCreatingConcept(true)
      try {
        const concept = await conceptService.addConceptToContent('tweet', tweet.id, newConceptText.trim())
        if (concept) {
          onConceptAdded(tweet.id, concept)
          setNewConceptText('')
          setIsAddingConcept(false)
        }
      } catch (error) {
        console.error('Failed to add concept:', error)
      } finally {
        setIsCreatingConcept(false)
      }
    }
  }

  const handleRemoveConcept = async (conceptId: string) => {
    const success = await conceptService.removeConceptFromContent('tweet', tweet.id, conceptId)
    if (success) {
      onConceptRemoved(tweet.id, conceptId)
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

  const handleCreateConcept = () => {
    setConceptCreationText(selectedTextRef.current)
    setShowConceptCreationForm(true)
    setContextMenu(null)
  }

  const handleSubmitConceptCreation = async () => {
    if (conceptCreationText.trim() && !isCreatingConcept) {
      setIsCreatingConcept(true)
      try {
        const concept = await conceptService.addConceptToContent('tweet', tweet.id, conceptCreationText.trim())
        if (concept) {
          onConceptAdded(tweet.id, concept)
          setConceptCreationText('')
          setShowConceptCreationForm(false)
        }
      } catch (error) {
        console.error('Failed to create concept:', error)
      } finally {
        setIsCreatingConcept(false)
      }
    }
  }

  const handleImageError = (index: number) => {
    setBrokenImages(prev => new Set(prev).add(index))
  }

  const toggleVideoPlay = (index: number) => {
    const video = videoRefs.current[index]
    if (!video) return

    if (playingVideos.has(index)) {
      video.pause()
      setPlayingVideos(prev => {
        const newSet = new Set(prev)
        newSet.delete(index)
        return newSet
      })
    } else {
      video.play()
      setPlayingVideos(prev => new Set(prev).add(index))
    }
  }

  const handleVideoEnded = (index: number) => {
    setPlayingVideos(prev => {
      const newSet = new Set(prev)
      newSet.delete(index)
      return newSet
    })
  }

  const getConceptBadgeStyle = (_concept: Concept) => {
    const isDark = document.documentElement.classList.contains('dark')
    return {
      backgroundColor: isDark ? '#1e3a5f' : '#DBEAFE',
      color: isDark ? '#93c5fd' : '#1E40AF'
    }
  }

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setContextMenu(null)
      setShowConceptCreationForm(false)
    }
    if (contextMenu || showConceptCreationForm) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [contextMenu, showConceptCreationForm])

  const hasVisibleMedia = (tweet.media?.length ?? 0) > 0 &&
    tweet.media?.some((_, index) => !brokenImages.has(index))

  // Get concepts for display
  const concepts = tweet.concepts || []

  return (
    <>
      <Card className="mb-4 hover:shadow-lg transition-all duration-200 border-gray-200 dark:border-gray-700">
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              {tweet.author_profile_image_url && !profileImageBroken ? (
                <img
                  src={tweet.author_profile_image_url}
                  alt={`@${tweet.author_username}`}
                  className="w-10 h-10 rounded-full object-cover"
                  onError={() => setProfileImageBroken(true)}
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
              <div>
                <div className="font-semibold text-gray-900 dark:text-gray-100">@{tweet.author_username}</div>
                <div className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1">
                  <Calendar className="w-3 h-3" />
                  {formatDate(tweet.created_at)}
                </div>
              </div>
            </div>
            <Button
              size="sm"
              variant="ghost"
              onClick={openTweetInTwitter}
              className="rounded-full w-8 h-8 p-0 bg-gradient-to-br from-blue-400 to-blue-600 hover:from-blue-500 hover:to-blue-700 text-white"
              title="Open original tweet in X/Twitter"
            >
              <ExternalLink className="w-4 h-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="pb-3">
          <div 
            ref={tweetContentRef}
            className="text-gray-800 dark:text-gray-100 whitespace-pre-wrap break-words select-text cursor-text"
            onClick={() => onTweetClick?.(tweet)}
            onMouseUp={handleTextSelection}
            onContextMenu={handleContextMenu}
          >
            {decodeHtmlEntities(tweet.text)}
          </div>

          {hasVisibleMedia && tweet.media && (
            <div className="mt-3 grid grid-cols-2 gap-2">
              {tweet.media.map((media, index) => (
                !brokenImages.has(index) && (
                  <div key={`${media.media_key}-${index}`} className="relative rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800">
                    {media.type === 'photo' ? (
                      <img 
                        src={media.url} 
                        alt={media.alt_text || 'Tweet image'}
                        className="w-full h-auto object-cover"
                        onError={() => handleImageError(index)}
                      />
                    ) : media.type === 'video' ? (
                      media.url ? (
                        <div 
                          className="relative group"
                          onMouseEnter={() => setHoveredVideo(index)}
                          onMouseLeave={() => setHoveredVideo(null)}
                        >
                          <video
                            ref={el => videoRefs.current[index] = el}
                            src={media.url}
                            poster={media.preview_image_url}
                            controls
                            className="w-full h-auto max-h-64 object-contain bg-black"
                            onError={() => handleImageError(index)}
                            onEnded={() => handleVideoEnded(index)}
                            onClick={(e) => e.stopPropagation()}
                          >
                            Your browser does not support the video tag.
                          </video>
                          {/* Play button overlay for better UX */}
                          {!playingVideos.has(index) && hoveredVideo === index && (
                            <div 
                              className="absolute inset-0 flex items-center justify-center bg-black/30 cursor-pointer transition-opacity"
                              onClick={(e) => {
                                e.stopPropagation()
                                toggleVideoPlay(index)
                              }}
                            >
                              <div className="bg-white/90 rounded-full p-3 shadow-lg transform hover:scale-110 transition-transform">
                                <Play className="h-8 w-8 text-gray-900 fill-current" />
                              </div>
                            </div>
                          )}
                          {/* Video type indicator */}
                          <div className="absolute top-2 right-2 pointer-events-none">
                            <Badge variant="secondary" className="bg-black/60 text-white text-xs">
                              <Film className="h-3 w-3 mr-1" />
                              Video
                            </Badge>
                          </div>
                        </div>
                      ) : (
                        <div className="relative">
                          {media.preview_image_url ? (
                            <img
                              src={media.preview_image_url}
                              alt="Video preview"
                              className="w-full h-auto max-h-64 object-contain opacity-75 cursor-default"
                              onClick={(e) => e.stopPropagation()}
                            />
                          ) : (
                            <div className="flex items-center justify-center h-32 bg-gray-200 dark:bg-gray-700">
                              <Film className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                            </div>
                          )}
                          <div className="absolute inset-0 flex items-center justify-center bg-black/50 pointer-events-none">
                            <div className="text-white text-center p-3">
                              <Film className="h-8 w-8 mx-auto mb-2" />
                              <span className="text-sm">Video preview only</span>
                            </div>
                          </div>
                          <div className="absolute top-2 right-2">
                            <Badge variant="secondary" className="bg-black/60 text-white text-xs">
                              Video
                            </Badge>
                          </div>
                        </div>
                      )
                    ) : media.type === 'animated_gif' ? (
                      media.url ? (
                        <div className="relative group">
                          <video
                            ref={el => videoRefs.current[index] = el}
                            src={media.url}
                            poster={media.preview_image_url}
                            autoPlay
                            loop
                            muted
                            playsInline
                            className="w-full h-auto max-h-64 object-contain bg-black cursor-pointer"
                            onError={() => handleImageError(index)}
                            onClick={(e) => {
                              e.stopPropagation()
                              const video = e.currentTarget as HTMLVideoElement
                              if (video.paused) {
                                video.play()
                              } else {
                                video.pause()
                              }
                            }}
                          >
                            Your browser does not support the video tag.
                          </video>
                          {/* GIF indicator */}
                          <div className="absolute top-2 right-2 pointer-events-none">
                            <Badge variant="secondary" className="bg-black/60 text-white text-xs">
                              GIF
                            </Badge>
                          </div>
                        </div>
                      ) : (
                        <div className="relative">
                          {media.preview_image_url ? (
                            <img
                              src={media.preview_image_url}
                              alt="GIF preview"
                              className="w-full h-auto max-h-64 object-contain opacity-75 cursor-default"
                              onClick={(e) => e.stopPropagation()}
                            />
                          ) : (
                            <div className="flex items-center justify-center h-32 bg-gray-200 dark:bg-gray-700">
                              <ImageIcon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                            </div>
                          )}
                          <div className="absolute inset-0 flex items-center justify-center bg-black/50 pointer-events-none">
                            <div className="text-white text-center p-3">
                              <span className="text-sm">🎬 GIF preview only</span>
                            </div>
                          </div>
                          <div className="absolute top-2 right-2">
                            <Badge variant="secondary" className="bg-black/60 text-white text-xs">
                              GIF
                            </Badge>
                          </div>
                        </div>
                      )
                    ) : (
                      <div className="flex items-center justify-center h-32 bg-gray-200 dark:bg-gray-700">
                        <ImageIcon className="w-8 h-8 text-gray-400 dark:text-gray-500" />
                        <span className="ml-2 text-sm text-gray-500 dark:text-gray-400">Media</span>
                      </div>
                    )}
                  </div>
                )
              ))}
            </div>
          )}

          <div className="flex items-center gap-4 mt-3 text-sm text-gray-500 dark:text-gray-400">
            <div className="flex items-center gap-1">
              <Heart className="w-4 h-4" />
              <span>{(tweet.metrics?.likes || 0).toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-1">
              <Repeat2 className="w-4 h-4" />
              <span>{(tweet.metrics?.retweets || 0).toLocaleString()}</span>
            </div>
            <div className="flex items-center gap-1">
              <MessageCircle className="w-4 h-4" />
              <span>{(tweet.metrics?.replies || 0).toLocaleString()}</span>
            </div>
          </div>
        </CardContent>

        <Separator className="my-2" />

        <CardFooter className="pt-3 pb-3">
          <div className="w-full">
            <div className="flex items-center gap-2 mb-2">
              <Tag className="w-4 h-4 text-gray-500 dark:text-gray-400" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Concepts</span>
              {onSuggestConcepts && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onSuggestConcepts(tweet)}
                  className="ml-auto"
                >
                  <Sparkles className="w-3 h-3 mr-1" />
                  Suggest
                </Button>
              )}
            </div>
            
            <div className="flex flex-wrap gap-2">
              {concepts.map((concept, index) => (
                <Badge
                  key={`${concept.concept_id}-${index}`}
                  variant="outline"
                  className="group cursor-pointer transition-all hover:shadow-md"
                  style={getConceptBadgeStyle(concept)}
                  title={concept.description || `Concept: ${concept.display_name}`}
                >
                  <span className="mr-1">{conceptService.getConceptIcon(concept)}</span>
                  {concept.display_name}
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRemoveConcept(concept.concept_id)
                    }}
                    className="ml-2 opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <X className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
              
              {isAddingConcept ? (
                <div className="flex items-center gap-1">
                  <Input
                    type="text"
                    value={newConceptText}
                    onChange={(e) => setNewConceptText(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleAddConcept()}
                    placeholder="Type concept..."
                    className="h-7 w-32 text-sm"
                    autoFocus
                    disabled={isCreatingConcept}
                  />
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleAddConcept}
                    disabled={isCreatingConcept}
                    className="h-7 w-7 p-0"
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => {
                      setIsAddingConcept(false)
                      setNewConceptText('')
                    }}
                    className="h-7 w-7 p-0"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              ) : (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setIsAddingConcept(true)}
                  className="h-7"
                >
                  <Plus className="w-3 h-3 mr-1" />
                  Add Concept
                </Button>
              )}
            </div>
          </div>
        </CardFooter>
      </Card>

      {/* Context Menu Portal */}
      {contextMenu && ReactDOM.createPortal(
        <div
          className="fixed bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg py-1 z-50"
          style={{
            left: contextMenu.x,
            top: contextMenu.y,
            maxWidth: '200px'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <button
            className="w-full px-4 py-2 text-left text-sm hover:bg-gray-100 dark:hover:bg-gray-800 flex items-center gap-2"
            onClick={handleCreateConcept}
          >
            <Tag className="w-4 h-4" />
            Create Concept
          </button>
        </div>,
        document.body
      )}

      {/* Concept Creation Form Portal */}
      {showConceptCreationForm && ReactDOM.createPortal(
        <div
          className="fixed bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg shadow-xl p-4 z-50"
          style={{
            left: '50%',
            top: '50%',
            transform: 'translate(-50%, -50%)',
            width: '300px'
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <h3 className="font-semibold mb-2">Create Concept from Selection</h3>
          <Input
            type="text"
            value={conceptCreationText}
            onChange={(e) => setConceptCreationText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSubmitConceptCreation()}
            placeholder="Enter concept text..."
            className="mb-3"
            autoFocus
            disabled={isCreatingConcept}
          />
          <div className="flex justify-end gap-2">
            <Button
              size="sm"
              variant="outline"
              onClick={() => {
                setShowConceptCreationForm(false)
                setConceptCreationText('')
              }}
              disabled={isCreatingConcept}
            >
              Cancel
            </Button>
            <Button
              size="sm"
              onClick={handleSubmitConceptCreation}
              disabled={isCreatingConcept || !conceptCreationText.trim()}
            >
              Create Concept
            </Button>
          </div>
        </div>,
        document.body
      )}
    </>
  )
})

export default TweetCardModern