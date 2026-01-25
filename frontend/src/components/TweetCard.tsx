import React, { useState, useRef, useEffect } from 'react'
import ReactDOM from 'react-dom'
import './TweetCard.css'

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
  onTweetClick?: (tweet: any) => void  // Made optional for backward compatibility
  onSuggestTags?: (tweet: any) => void  // New prop name
}

const TweetCard = React.memo(function TweetCard({ tweet, onTagAdded, onTagRemoved, onTweetClick, onSuggestTags }: TweetCardProps) {
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
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString()
  }

  const handleCardDoubleClick = () => {
    // Open tweet in X/Twitter on double-click
    window.open(`https://twitter.com/${tweet.author_username}/status/${tweet.id}`, '_blank')
  }

  const decodeHTMLEntities = (text: string) => {
    const textArea = document.createElement('textarea')
    textArea.innerHTML = text
    return textArea.value
  }

  // Handle text selection
  const handleTextSelection = () => {
    const selection = window.getSelection()
    if (selection && selection.toString().trim()) {
      selectedTextRef.current = selection.toString().trim()
    }
  }

  // Handle context menu with smart positioning
  const handleContextMenu = (e: React.MouseEvent) => {
    const selection = window.getSelection()
    const selectedText = selection ? selection.toString().trim() : ''
    
    // Only show context menu if there's selected text
    if (selectedText) {
      e.preventDefault()
      e.stopPropagation() // Stop event from bubbling up
      
      selectedTextRef.current = selectedText
      console.log('Context menu triggered for text:', selectedText) // Debug log
      
      // Calculate position with boundary detection
      const menuWidth = 150 // Approximate width of context menu
      const menuHeight = 40 // Approximate height of context menu
      const padding = 10 // Padding from edges
      
      let x = e.clientX
      let y = e.clientY
      
      // Check right boundary
      if (x + menuWidth > window.innerWidth - padding) {
        x = window.innerWidth - menuWidth - padding
      }
      
      // Check bottom boundary
      if (y + menuHeight > window.innerHeight - padding) {
        y = e.clientY - menuHeight - 5 // Position above cursor
      }
      
      // Check left boundary
      if (x < padding) {
        x = padding
      }
      
      // Check top boundary
      if (y < padding) {
        y = padding
      }
      
      setContextMenu({ x, y })
    }
  }

  // Close context menu when clicking outside
  useEffect(() => {
    const handleClickOutside = () => {
      setContextMenu(null)
    }
    if (contextMenu) {
      document.addEventListener('click', handleClickOutside)
      return () => document.removeEventListener('click', handleClickOutside)
    }
  }, [contextMenu])

  // Handle tag creation from selected text
  const handleCreateTag = () => {
    setTagCreationText(selectedTextRef.current)
    setShowTagCreationForm(true)
    setContextMenu(null)
  }

  const submitTagCreation = () => {
    if (tagCreationText.trim()) {
      onTagAdded(tweet.id, tagCreationText.trim())
      setTagCreationText('')
      setShowTagCreationForm(false)
    }
  }

  // Handle image load errors
  const handleImageError = (index: number) => {
    setBrokenImages(prev => new Set(prev).add(index))
  }

  return (
    <div className="tweet-card">
      <div className="tweet-header">
        <span className="tweet-author">@{tweet.author_username}</span>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span className="tweet-date">{formatDate(tweet.created_at)}</span>
          <button
            onClick={handleCardDoubleClick}
            className="open-tweet-button"
            style={{
              background: 'linear-gradient(135deg, #1DA1F2 0%, #0A85D9 100%)',
              border: 'none',
              borderRadius: '50%',
              padding: '8px',
              cursor: 'pointer',
              color: 'white',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              transition: 'all 0.2s ease',
              boxShadow: '0 2px 6px rgba(29, 161, 242, 0.2)',
              width: '32px',
              height: '32px'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-2px) scale(1.1)'
              e.currentTarget.style.boxShadow = '0 4px 12px rgba(29, 161, 242, 0.4)'
              e.currentTarget.style.background = 'linear-gradient(135deg, #1DA1F2 0%, #1a91da 100%)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0) scale(1)'
              e.currentTarget.style.boxShadow = '0 2px 6px rgba(29, 161, 242, 0.2)'
              e.currentTarget.style.background = 'linear-gradient(135deg, #1DA1F2 0%, #0A85D9 100%)'
            }}
            title="Open original tweet in X/Twitter"
          >
            <svg 
              width="16" 
              height="16" 
              viewBox="0 0 24 24" 
              fill="currentColor"
            >
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
            </svg>
          </button>
        </div>
      </div>
      
      <div 
        className="tweet-content"
        ref={tweetContentRef}
        onMouseUp={handleTextSelection}
        onContextMenu={handleContextMenu}
      >
        <p>{decodeHTMLEntities(tweet.text)}</p>
        
        {tweet.media && tweet.media.length > 0 && brokenImages.size < tweet.media.length && (
          <div className={`tweet-media media-count-${Math.min(tweet.media.length, 4)}`}>
            {tweet.media.map((media, index) => (
              <div key={index} className="media-item">
                {(media.type === 'photo' || media.type === 'link_card') && (
                  brokenImages.has(index) ? (
                    <div 
                      style={{
                        width: '100%',
                        height: '200px',
                        background: '#f0f0f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#999',
                        fontSize: '14px',
                        borderRadius: '8px'
                      }}
                    >
                      🖼️ Image unavailable
                    </div>
                  ) : (
                    <img 
                      src={media.url || media.media_url} 
                      alt={media.alt_text || 'Tweet media'} 
                      loading="lazy"
                      onError={() => handleImageError(index)}
                      onClick={(e) => {
                        e.stopPropagation()
                        if (!brokenImages.has(index)) {
                          window.open(media.url || media.media_url, '_blank')
                        }
                      }}
                      style={{ cursor: brokenImages.has(index) ? 'default' : 'pointer' }}
                    />
                  )
                )}
                {media.type === 'video' && (
                  <div className="video-container">
                    {media.preview_image_url && !brokenImages.has(index) ? (
                      <img 
                        src={media.preview_image_url} 
                        alt="Video preview" 
                        loading="lazy"
                        onError={() => handleImageError(index)}
                      />
                    ) : (
                      <div style={{
                        width: '100%',
                        height: '200px',
                        background: '#2a2a2a'
                      }}></div>
                    )}
                    <div className="video-overlay">
                      <span className="play-button">▶️</span>
                      <span className="video-label">Video</span>
                    </div>
                  </div>
                )}
                {media.type === 'animated_gif' && (
                  <div className="gif-container">
                    {brokenImages.has(index) ? (
                      <div style={{
                        width: '100%',
                        height: '200px',
                        background: '#f0f0f0',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: '#999'
                      }}>
                        🎬 GIF unavailable
                      </div>
                    ) : (
                      <img 
                        src={media.url || media.media_url} 
                        alt="GIF" 
                        loading="lazy"
                        onError={() => handleImageError(index)}
                      />
                    )}
                    <span className="gif-label">GIF</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
      
      <div className="tweet-metrics">
        <span>❤️ {tweet.metrics.likes}</span>
        <span>🔁 {tweet.metrics.retweets}</span>
        <span>💬 {tweet.metrics.replies}</span>
      </div>
      
      <div className="tweet-tags" onClick={(e) => e.stopPropagation()}>
        <div className="tags-list">
          {tweet.tags.map((tag, index) => (
            <span key={index} className="tag">
              {tag.tag}
              <button 
                onClick={() => onTagRemoved(tweet.id, tag.tag)}
                className="remove-tag"
              >
                ×
              </button>
            </span>
          ))}
        </div>
        
        {isAddingTag ? (
          <div className="add-tag-form">
            <input
              type="text"
              value={newTag}
              onChange={(e) => setNewTag(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleAddTag()}
              placeholder="Enter tag"
              autoFocus
            />
            <button onClick={handleAddTag}>Add</button>
            <button onClick={() => {
              setIsAddingTag(false)
              setNewTag('')
            }}>Cancel</button>
          </div>
        ) : (
          <button 
            onClick={() => setIsAddingTag(true)}
            className="add-tag-button"
          >
            + Add Tag
          </button>
        )}
      </div>
      
      <div className="tweet-actions" onClick={(e) => e.stopPropagation()}>
        <button 
          onClick={() => {
            // Use onSuggestTags if provided, otherwise fall back to onTweetClick
            if (onSuggestTags) {
              onSuggestTags(tweet)
            } else if (onTweetClick) {
              onTweetClick(tweet)
            }
          }}
          className="suggest-tags-button"
        >
          🏷️ Suggest Concept Tags
        </button>
      </div>

      {/* Context Menu - Rendered as Portal */}
      {contextMenu && ReactDOM.createPortal(
        <div 
          className="tweet-context-menu"
          style={{
            position: 'fixed',
            left: contextMenu.x,
            top: contextMenu.y,
            background: 'white',
            border: '1px solid #d1d5db',
            borderRadius: '6px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.15), 0 0 1px rgba(0,0,0,0.1)',
            zIndex: 99999, // Even higher z-index
            padding: '4px 0',
            minWidth: '140px',
            pointerEvents: 'auto' // Ensure it can receive mouse events
          }}
          onClick={(e) => e.stopPropagation()}
          onMouseDown={(e) => e.stopPropagation()}
          onMouseEnter={(e) => e.stopPropagation()}
          onContextMenu={(e) => {
            e.preventDefault()
            e.stopPropagation()
          }}
        >
          <div 
            className="context-menu-item"
            onClick={handleCreateTag}
            style={{
              padding: '10px 16px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              color: '#374151',
              transition: 'background-color 0.15s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f3f4f6'
              e.currentTarget.style.color = '#1f2937'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent'
              e.currentTarget.style.color = '#374151'
            }}
          >
            🏷️ Tag Creation
          </div>
        </div>,
        document.body
      )}

      {/* Tag Creation Form Modal */}
      {showTagCreationForm && (
        <div 
          className="tag-creation-overlay"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1001
          }}
          onClick={() => setShowTagCreationForm(false)}
        >
          <div 
            className="tag-creation-form"
            style={{
              background: 'white',
              padding: '20px',
              borderRadius: '8px',
              width: '400px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.2)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ marginTop: 0 }}>Create Tag from Selection</h3>
            <p style={{ color: '#666', fontSize: '14px' }}>Edit the selected text to create a tag:</p>
            <input
              type="text"
              value={tagCreationText}
              onChange={(e) => setTagCreationText(e.target.value)}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ddd',
                borderRadius: '4px',
                fontSize: '14px',
                marginBottom: '16px'
              }}
              autoFocus
              onKeyPress={(e) => e.key === 'Enter' && submitTagCreation()}
            />
            <div style={{ display: 'flex', gap: '8px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowTagCreationForm(false)}
                style={{
                  padding: '8px 16px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  background: 'white',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={submitTagCreation}
                style={{
                  padding: '8px 16px',
                  border: 'none',
                  borderRadius: '4px',
                  background: '#007bff',
                  color: 'white',
                  cursor: 'pointer'
                }}
              >
                Create Tag
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
})

export default TweetCard