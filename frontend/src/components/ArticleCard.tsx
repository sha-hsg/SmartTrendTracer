import React, { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import './ArticleCard.css'

interface ArticleCardProps {
  article: {
    id: number
    title: string
    subtitle: string | null
    author: {
      name: string
      subdomain: string
    }
    preview: string
    word_count: number
    reading_time_minutes: number
    published_at: string | null
    tags: { tag: string; type: string }[]
    snippet_count: number
    has_summary: boolean
    url?: string | null
  }
  onClick: () => void
  onTagAdded: (articleId: number, tag: string) => void
  onTagRemoved: (articleId: number, tag: string) => void
  onDelete?: (articleId: number) => void
}

function ArticleCard({ article, onClick, onTagAdded, onTagRemoved, onDelete }: ArticleCardProps) {
  const [isAddingTag, setIsAddingTag] = useState(false)
  const [newTag, setNewTag] = useState('')
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isEditingDate, setIsEditingDate] = useState(false)
  const [editedDate, setEditedDate] = useState('')
  const [isEditingUrl, setIsEditingUrl] = useState(false)
  const [editedUrl, setEditedUrl] = useState('')

  const handleAddTag = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (newTag.trim()) {
      onTagAdded(article.id, newTag.trim())
      setNewTag('')
      setIsAddingTag(false)
    }
  }

  const handleRemoveTag = (e: React.MouseEvent, tag: string) => {
    e.stopPropagation()
    onTagRemoved(article.id, tag)
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Unknown date'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    })
  }

  const renderPreview = (text: string) => {
    // Limit markdown content length for preview
    const truncated = text.length > 300 ? text.substring(0, 300) + '...' : text
    return (
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          img: () => null, // Don't show images in preview
          h1: ({ children }) => <span className="preview-heading">{children}</span>,
          h2: ({ children }) => <span className="preview-heading">{children}</span>,
          h3: ({ children }) => <span className="preview-heading">{children}</span>,
          p: ({ children }) => <span className="preview-paragraph">{children} </span>,
          strong: ({ children }) => <strong>{children}</strong>,
          em: ({ children }) => <em>{children}</em>,
          code: ({ children }) => <code>{children}</code>,
          a: ({ href, children }) => <span className="preview-link">{children}</span>
        }}
      >
        {truncated}
      </ReactMarkdown>
    )
  }

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (onDelete) {
      onDelete(article.id)
      setShowDeleteConfirm(false)
    }
  }

  const handleSaveDate = async () => {
    if (!editedDate) {
      setIsEditingDate(false)
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/api/substack/articles/${article.id}/date`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ published_at: new Date(editedDate).toISOString() })
      })

      if (response.ok) {
        // Update the article's published_at locally
        article.published_at = new Date(editedDate).toISOString()
        setIsEditingDate(false)
      } else {
        console.error('Failed to update date')
        setIsEditingDate(false)
      }
    } catch (error) {
      console.error('Error updating date:', error)
      setIsEditingDate(false)
    }
  }

  const handleSaveUrl = async () => {
    if (!editedUrl.trim()) {
      // If URL is empty, clear it
      try {
        const response = await fetch(`http://localhost:8000/api/substack/articles/${article.id}/url`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ url: '' })
        })

        if (response.ok) {
          article.url = null
          setIsEditingUrl(false)
        }
      } catch (error) {
        console.error('Error clearing URL:', error)
      }
      return
    }

    // Validate URL format
    if (!editedUrl.startsWith('http://') && !editedUrl.startsWith('https://')) {
      alert('URL must start with http:// or https://')
      return
    }

    try {
      const response = await fetch(`http://localhost:8000/api/substack/articles/${article.id}/url`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ url: editedUrl })
      })

      if (response.ok) {
        article.url = editedUrl
        setIsEditingUrl(false)
      } else {
        console.error('Failed to update URL')
        setIsEditingUrl(false)
      }
    } catch (error) {
      console.error('Error updating URL:', error)
      setIsEditingUrl(false)
    }
  }

  return (
    <div className="article-card" onClick={onClick}>
      <div className="article-header">
        <div className="article-header-content">
          <h3 className="article-title">{article.title}</h3>
          {article.subtitle && (
            <p className="article-subtitle">{article.subtitle}</p>
          )}
        </div>
        <div className="article-header-actions">
          {(article.url || isEditingUrl) && (
            <div className="url-edit-container">
              {isEditingUrl ? (
                <input
                  type="url"
                  value={editedUrl}
                  onChange={(e) => setEditedUrl(e.target.value)}
                  onBlur={handleSaveUrl}
                  onKeyPress={(e) => {
                    e.stopPropagation()
                    if (e.key === 'Enter') {
                      handleSaveUrl()
                    }
                    if (e.key === 'Escape') {
                      setIsEditingUrl(false)
                      setEditedUrl(article.url || '')
                    }
                  }}
                  onClick={(e) => e.stopPropagation()}
                  className="url-input"
                  placeholder="Enter article URL"
                  autoFocus
                />
              ) : (
                <>
                  <button
                    className="open-article-button"
                    onClick={(e) => {
                      e.stopPropagation()
                      if (article.url) {
                        window.open(article.url, '_blank', 'noopener,noreferrer')
                      }
                    }}
                    title="Open original article on Substack"
                  >
                    <svg 
                      width="20" 
                      height="20" 
                      viewBox="0 0 20 20" 
                      fill="currentColor"
                      style={{ display: 'block' }}
                    >
                      <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z"/>
                      <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z"/>
                    </svg>
                  </button>
                  <button
                    className="edit-url-button"
                    onClick={(e) => {
                      e.stopPropagation()
                      setEditedUrl(article.url || '')
                      setIsEditingUrl(true)
                    }}
                    title="Edit article URL"
                  >
                    ✏️
                  </button>
                </>
              )}
            </div>
          )}
          {!article.url && !isEditingUrl && (
            <button
              className="add-url-button"
              onClick={(e) => {
                e.stopPropagation()
                setEditedUrl('')
                setIsEditingUrl(true)
              }}
              title="Add article URL"
            >
              🔗+
            </button>
          )}
          {onDelete && (
            <div className="article-actions" onClick={(e) => e.stopPropagation()}>
              {showDeleteConfirm ? (
                <div className="delete-confirm">
                  <span>Delete?</span>
                  <button onClick={handleDelete} className="confirm-delete">Yes</button>
                  <button onClick={(e) => {
                    e.stopPropagation()
                    setShowDeleteConfirm(false)
                  }} className="cancel-delete">No</button>
                </div>
              ) : (
                <button 
                  onClick={(e) => {
                    e.stopPropagation()
                    setShowDeleteConfirm(true)
                  }} 
                  className="delete-button"
                  title="Delete article"
                >
                  ×
                </button>
              )}
            </div>
          )}
        </div>
      </div>

      <div className="article-meta">
        <span className="article-author">✍️ {article.author.name}</span>
        {isEditingDate ? (
          <span className="article-date-edit" onClick={(e) => e.stopPropagation()}>
            <input
              type="datetime-local"
              value={editedDate}
              onChange={(e) => setEditedDate(e.target.value)}
              onBlur={handleSaveDate}
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSaveDate()
                }
                if (e.key === 'Escape') {
                  setIsEditingDate(false)
                }
              }}
              className="date-input"
              autoFocus
            />
          </span>
        ) : (
          <span 
            className="article-date editable-date" 
            onClick={(e) => {
              e.stopPropagation()
              const currentDate = article.published_at 
                ? new Date(article.published_at).toISOString().slice(0, 16)
                : new Date().toISOString().slice(0, 16)
              setEditedDate(currentDate)
              setIsEditingDate(true)
            }}
            title="Click to edit date"
          >
            📅 {formatDate(article.published_at)} ✏️
          </span>
        )}
        <span className="article-reading-time">⏱️ {article.reading_time_minutes} min</span>
      </div>

      <div className="article-preview">
        {renderPreview(article.preview)}
      </div>

      <div className="article-stats">
        <span className="stat">📝 {article.word_count} words</span>
        {article.snippet_count > 0 && (
          <span className="stat">✂️ {article.snippet_count} highlights</span>
        )}
        {article.has_summary && (
          <span className="stat">📄 Summary available</span>
        )}
      </div>

      <div className="article-tags" onClick={(e) => e.stopPropagation()}>
        <div className="tags-list">
          {article.tags.filter(tag => tag.tag && tag.tag.trim() !== '').map((tag, index) => (
            <span key={index} className={`tag tag-${tag.type}`}>
              {tag.tag}
              <button
                onClick={(e) => handleRemoveTag(e, tag.tag)}
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
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleAddTag(e as any)
                }
              }}
              placeholder="Enter tag"
              autoFocus
              onClick={(e) => e.stopPropagation()}
            />
            <button onClick={handleAddTag}>Add</button>
            <button onClick={(e) => {
              e.stopPropagation()
              setIsAddingTag(false)
              setNewTag('')
            }}>Cancel</button>
          </div>
        ) : (
          <button
            onClick={(e) => {
              e.stopPropagation()
              setIsAddingTag(true)
            }}
            className="add-tag-button"
          >
            + Add Tag
          </button>
        )}
      </div>
    </div>
  )
}

export default ArticleCard