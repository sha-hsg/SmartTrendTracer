import { useState, useEffect } from 'react'
import axios from 'axios'
import './PDFExportModal.css'

interface PDFExportModalProps {
  isOpen: boolean
  onClose: () => void
  selectedArticles?: number[]
  authorId?: number
  tag?: string
}

interface Author {
  id: number
  name: string
  subdomain: string
}

function PDFExportModal({ isOpen, onClose, selectedArticles = [], authorId, tag }: PDFExportModalProps) {
  const [exportType, setExportType] = useState<'selected' | 'author' | 'recent' | 'tag'>('selected')
  const [authors, setAuthors] = useState<Author[]>([])
  const [selectedAuthor, setSelectedAuthor] = useState<number | null>(authorId || null)
  const [selectedTag, setSelectedTag] = useState<string>(tag || '')
  const [recentDays, setRecentDays] = useState(7)
  const [recentLimit, setRecentLimit] = useState(10)
  const [customTitle, setCustomTitle] = useState('Article Collection')
  const [includeTOC, setIncludeTOC] = useState(true)
  const [exporting, setExporting] = useState(false)
  const [availableTags, setAvailableTags] = useState<string[]>([])

  useEffect(() => {
    if (isOpen) {
      fetchAuthors()
      fetchTags()
      
      // Set default export type based on props
      if (selectedArticles.length > 0) {
        setExportType('selected')
      } else if (authorId) {
        setExportType('author')
      } else if (tag) {
        setExportType('tag')
      }
    }
  }, [isOpen, selectedArticles, authorId, tag])

  const fetchAuthors = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/substack/authors')
      setAuthors(response.data)
    } catch (error) {
      console.error('Error fetching authors:', error)
    }
  }

  const fetchTags = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tags')
      const uniqueTags = [...new Set(response.data.map((t: any) => t.tag))] as string[]
      setAvailableTags(uniqueTags.sort())
    } catch (error) {
      console.error('Error fetching tags:', error)
    }
  }

  const handleExport = async () => {
    setExporting(true)
    
    try {
      let response: any
      
      switch (exportType) {
        case 'selected':
          if (selectedArticles.length === 0) {
            alert('Please select articles to export')
            setExporting(false)
            return
          }
          
          response = await axios.post('http://localhost:8000/api/pdf/articles/bulk', {
            article_ids: selectedArticles,
            title: customTitle,
            include_toc: includeTOC
          }, { responseType: 'blob' })
          break
          
        case 'author':
          if (!selectedAuthor) {
            alert('Please select an author')
            setExporting(false)
            return
          }
          
          response = await axios.get(
            `http://localhost:8000/api/pdf/author/${selectedAuthor}`,
            { responseType: 'blob' }
          )
          break
          
        case 'recent':
          response = await axios.get(
            `http://localhost:8000/api/pdf/recent?days=${recentDays}&limit=${recentLimit}`,
            { responseType: 'blob' }
          )
          break
          
        case 'tag':
          if (!selectedTag) {
            alert('Please select a tag')
            setExporting(false)
            return
          }
          
          response = await axios.get(
            `http://localhost:8000/api/pdf/tagged/${encodeURIComponent(selectedTag)}`,
            { responseType: 'blob' }
          )
          break
      }
      
      // Create download link
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      
      // Generate filename based on export type
      let filename = 'articles.pdf'
      switch (exportType) {
        case 'selected':
          filename = `${customTitle.replace(/[^a-z0-9\s-_]/gi, '')}.pdf`
          break
        case 'author':
          const author = authors.find(a => a.id === selectedAuthor)
          filename = `${author?.name.replace(/[^a-z0-9\s-_]/gi, '') || 'author'}_articles.pdf`
          break
        case 'recent':
          filename = `recent_articles_${recentDays}days.pdf`
          break
        case 'tag':
          filename = `articles_${selectedTag.replace(/[^a-z0-9-_]/gi, '')}.pdf`
          break
      }
      
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
      
      // Close modal after successful export
      onClose()
      
    } catch (error) {
      console.error('Error exporting PDF:', error)
      alert('Failed to export PDF. Please try again.')
    } finally {
      setExporting(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="pdf-export-modal-overlay" onClick={onClose}>
      <div className="pdf-export-modal" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>📥 Export Articles to PDF</h2>
          <button className="close-button" onClick={onClose}>✕</button>
        </div>
        
        <div className="modal-body">
          <div className="export-type-selector">
            <label>Export Type:</label>
            <div className="radio-group">
              <label>
                <input
                  type="radio"
                  value="selected"
                  checked={exportType === 'selected'}
                  onChange={(e) => setExportType(e.target.value as any)}
                  disabled={selectedArticles.length === 0}
                />
                Selected Articles ({selectedArticles.length})
              </label>
              
              <label>
                <input
                  type="radio"
                  value="author"
                  checked={exportType === 'author'}
                  onChange={(e) => setExportType(e.target.value as any)}
                />
                By Author
              </label>
              
              <label>
                <input
                  type="radio"
                  value="recent"
                  checked={exportType === 'recent'}
                  onChange={(e) => setExportType(e.target.value as any)}
                />
                Recent Articles
              </label>
              
              <label>
                <input
                  type="radio"
                  value="tag"
                  checked={exportType === 'tag'}
                  onChange={(e) => setExportType(e.target.value as any)}
                />
                By Tag
              </label>
            </div>
          </div>
          
          {exportType === 'selected' && (
            <div className="export-options">
              <div className="form-group">
                <label>Collection Title:</label>
                <input
                  type="text"
                  value={customTitle}
                  onChange={(e) => setCustomTitle(e.target.value)}
                  placeholder="Enter collection title"
                />
              </div>
              
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={includeTOC}
                    onChange={(e) => setIncludeTOC(e.target.checked)}
                  />
                  Include Table of Contents
                </label>
              </div>
            </div>
          )}
          
          {exportType === 'author' && (
            <div className="export-options">
              <div className="form-group">
                <label>Select Author:</label>
                <select
                  value={selectedAuthor || ''}
                  onChange={(e) => setSelectedAuthor(Number(e.target.value))}
                >
                  <option value="">-- Select Author --</option>
                  {authors.map(author => (
                    <option key={author.id} value={author.id}>
                      {author.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
          
          {exportType === 'recent' && (
            <div className="export-options">
              <div className="form-group">
                <label>Days to look back:</label>
                <input
                  type="number"
                  value={recentDays}
                  onChange={(e) => setRecentDays(Number(e.target.value))}
                  min="1"
                  max="365"
                />
              </div>
              
              <div className="form-group">
                <label>Maximum articles:</label>
                <input
                  type="number"
                  value={recentLimit}
                  onChange={(e) => setRecentLimit(Number(e.target.value))}
                  min="1"
                  max="100"
                />
              </div>
            </div>
          )}
          
          {exportType === 'tag' && (
            <div className="export-options">
              <div className="form-group">
                <label>Select Tag:</label>
                <select
                  value={selectedTag}
                  onChange={(e) => setSelectedTag(e.target.value)}
                >
                  <option value="">-- Select Tag --</option>
                  {availableTags.map(tag => (
                    <option key={tag} value={tag}>
                      {tag}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          <button className="cancel-button" onClick={onClose}>
            Cancel
          </button>
          <button 
            className="export-button"
            onClick={handleExport}
            disabled={exporting}
          >
            {exporting ? '⏳ Exporting...' : '📥 Export PDF'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default PDFExportModal