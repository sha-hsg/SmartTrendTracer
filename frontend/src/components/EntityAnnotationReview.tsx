import React, { useState, useEffect } from 'react'
import ModelBadge from './ModelBadge'
import './EntityAnnotationReview.css'

interface EntitySuggestion {
  id: string
  text: string
  type: string
  confidence: number
  context: string
  normalized: string
  metadata: Record<string, any>
}

interface EntityAnnotationReviewProps {
  articleId?: number
  tweetId?: string
  onComplete?: () => void
}

interface UndoAction {
  type: 'accept' | 'reject' | 'bulk'
  entities: EntitySuggestion[]
  timestamp: number
}

function EntityAnnotationReview({ articleId, tweetId, onComplete }: EntityAnnotationReviewProps) {
  const [entities, setEntities] = useState<EntitySuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [selectedEntities, setSelectedEntities] = useState<Set<string>>(new Set())
  const [filterType, setFilterType] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'confidence' | 'type' | 'text'>('confidence')
  const [showOnlyUnreviewed, setShowOnlyUnreviewed] = useState(true)
  const [stats, setStats] = useState<any>({})
  const [undoStack, setUndoStack] = useState<UndoAction[]>([])
  const [schema, setSchema] = useState<any>(null)
  const [editingEntity, setEditingEntity] = useState<string | null>(null)
  const [editedValues, setEditedValues] = useState<Record<string, any>>({})
  const [extractionModel, setExtractionModel] = useState<string>('')

  // Load schema on mount
  useEffect(() => {
    loadSchema()
  }, [])

  const loadSchema = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/entities/schema')
      const data = await response.json()
      setSchema(data)
    } catch (error) {
      console.error('Error loading schema:', error)
    }
  }

  const runExtraction = async () => {
    setExtracting(true)
    setLoading(true)
    
    try {
      const payload: any = {}
      if (articleId) payload.article_id = articleId
      if (tweetId) payload.tweet_id = tweetId
      payload.use_fast_model = false

      const response = await fetch('http://localhost:8000/api/entities/extract', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        const data = await response.json()
        setEntities(data.entities)
        setStats(data.stats)
        setExtractionModel(data.model || 'claude-sonnet-4-20250514')
      }
    } catch (error) {
      console.error('Error extracting entities:', error)
    } finally {
      setExtracting(false)
      setLoading(false)
    }
  }

  const acceptEntity = async (entity: EntitySuggestion) => {
    try {
      const response = await fetch('http://localhost:8000/api/entities/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_id: entity.id,
          action: 'accept',
          new_type: editedValues[entity.id]?.type || entity.type,
          new_text: editedValues[entity.id]?.text || entity.text
        })
      })

      if (response.ok) {
        // Remove from list
        setEntities(entities.filter(e => e.id !== entity.id))
        
        // Add to undo stack
        setUndoStack([...undoStack, {
          type: 'accept',
          entities: [entity],
          timestamp: Date.now()
        }])
        
        // Clear selection
        selectedEntities.delete(entity.id)
        setSelectedEntities(new Set(selectedEntities))
      }
    } catch (error) {
      console.error('Error accepting entity:', error)
    }
  }

  const rejectEntity = async (entity: EntitySuggestion) => {
    try {
      const response = await fetch('http://localhost:8000/api/entities/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_id: entity.id,
          action: 'reject'
        })
      })

      if (response.ok) {
        // Remove from list
        setEntities(entities.filter(e => e.id !== entity.id))
        
        // Add to undo stack
        setUndoStack([...undoStack, {
          type: 'reject',
          entities: [entity],
          timestamp: Date.now()
        }])
        
        // Clear selection
        selectedEntities.delete(entity.id)
        setSelectedEntities(new Set(selectedEntities))
      }
    } catch (error) {
      console.error('Error rejecting entity:', error)
    }
  }

  const bulkAccept = async () => {
    const entitiesToAccept = entities.filter(e => selectedEntities.has(e.id))
    if (entitiesToAccept.length === 0) return

    try {
      const response = await fetch('http://localhost:8000/api/entities/bulk-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_ids: Array.from(selectedEntities),
          action: 'accept_all',
          article_id: articleId,  // Pass the article ID
          entities: entitiesToAccept  // Pass full entity data
        })
      })

      if (response.ok) {
        // Remove accepted entities
        setEntities(entities.filter(e => !selectedEntities.has(e.id)))
        
        // Add to undo stack
        setUndoStack([...undoStack, {
          type: 'bulk',
          entities: entitiesToAccept,
          timestamp: Date.now()
        }])
        
        // Clear selection
        setSelectedEntities(new Set())
      }
    } catch (error) {
      console.error('Error bulk accepting:', error)
    }
  }

  const bulkReject = async () => {
    const entitiesToReject = entities.filter(e => selectedEntities.has(e.id))
    if (entitiesToReject.length === 0) return

    try {
      const response = await fetch('http://localhost:8000/api/entities/bulk-action', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_ids: Array.from(selectedEntities),
          action: 'reject_all'
        })
      })

      if (response.ok) {
        // Remove rejected entities
        setEntities(entities.filter(e => !selectedEntities.has(e.id)))
        
        // Add to undo stack
        setUndoStack([...undoStack, {
          type: 'bulk',
          entities: entitiesToReject,
          timestamp: Date.now()
        }])
        
        // Clear selection
        setSelectedEntities(new Set())
      }
    } catch (error) {
      console.error('Error bulk rejecting:', error)
    }
  }

  const undoLastAction = () => {
    if (undoStack.length === 0) return

    const lastAction = undoStack[undoStack.length - 1]
    
    // Restore entities to list
    setEntities([...entities, ...lastAction.entities])
    
    // Remove from undo stack
    setUndoStack(undoStack.slice(0, -1))
  }

  const toggleEntitySelection = (entityId: string) => {
    const newSelection = new Set(selectedEntities)
    if (newSelection.has(entityId)) {
      newSelection.delete(entityId)
    } else {
      newSelection.add(entityId)
    }
    setSelectedEntities(newSelection)
  }

  const selectAll = () => {
    const filteredEntities = getFilteredEntities()
    setSelectedEntities(new Set(filteredEntities.map(e => e.id)))
  }

  const deselectAll = () => {
    setSelectedEntities(new Set())
  }

  const startEditingEntity = (entityId: string, entity: EntitySuggestion) => {
    setEditingEntity(entityId)
    setEditedValues({
      ...editedValues,
      [entityId]: {
        text: entity.text,
        type: entity.type
      }
    })
  }

  const saveEntityEdit = (entityId: string) => {
    setEditingEntity(null)
    // The edited values will be used when accepting the entity
  }

  const cancelEntityEdit = (entityId: string) => {
    setEditingEntity(null)
    const newEditedValues = { ...editedValues }
    delete newEditedValues[entityId]
    setEditedValues(newEditedValues)
  }

  const getFilteredEntities = () => {
    let filtered = [...entities]
    
    // Filter by type
    if (filterType !== 'all') {
      filtered = filtered.filter(e => e.type === filterType)
    }
    
    // Sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'confidence':
          return b.confidence - a.confidence
        case 'type':
          return a.type.localeCompare(b.type)
        case 'text':
          return a.text.localeCompare(b.text)
        default:
          return 0
      }
    })
    
    return filtered
  }

  const getEntityTypeInfo = (type: string) => {
    if (!schema) return { color: '#6B7280', icon: '📌' }
    
    for (const category of Object.values(schema.entity_types || {})) {
      const cat = category as any
      if (cat.tag === type) return { color: cat.color, icon: cat.icon }
      
      for (const child of Object.values(cat.children || {})) {
        const ch = child as any
        if (ch.tag === type) return { color: ch.color, icon: ch.icon }
      }
    }
    
    return { color: '#6B7280', icon: '📌' }
  }

  const filteredEntities = getFilteredEntities()
  const uniqueTypes = Array.from(new Set(entities.map(e => e.type)))

  return (
    <div className="entity-annotation-review">
      {/* Loading overlay while extracting */}
      {extracting && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(255, 255, 255, 0.95)',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          borderRadius: '12px'
        }}>
          <div style={{
            width: '60px',
            height: '60px',
            border: '4px solid #e0e0e0',
            borderTop: '4px solid #8B5CF6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            marginBottom: '20px'
          }}></div>
          <h3 style={{ color: '#6B40A6', marginBottom: '8px' }}>Processing with AI...</h3>
          <p style={{ color: '#6B7280', fontSize: '14px' }}>Extracting entities from {articleId ? 'article' : 'tweet'}</p>
        </div>
      )}
      
      <div className="review-header">
        <h2>🤖 Entity Annotation Review</h2>
        {articleId && <span className="source-badge">Article #{articleId}</span>}
        {tweetId && <span className="source-badge">Tweet</span>}
        {extractionModel && (
          <div style={{ marginLeft: 'auto' }}>
            <ModelBadge model={extractionModel} size="medium" />
          </div>
        )}
      </div>

      {/* Extraction Button */}
      {entities.length === 0 && !loading && (
        <div className="extraction-prompt">
          <p>No entities extracted yet. Run automatic annotation to detect entities.</p>
          <button 
            className="run-extraction-button"
            onClick={runExtraction}
            disabled={extracting}
          >
            {extracting ? (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div className="spinner-small" style={{
                  width: '16px',
                  height: '16px',
                  border: '2px solid rgba(255, 255, 255, 0.3)',
                  borderTop: '2px solid white',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }}></div>
                <span>Extracting entities...</span>
              </div>
            ) : (
              <>🚀 Run Automatic Annotation</>
            )}
          </button>
        </div>
      )}

      {/* Stats Bar */}
      {entities.length > 0 && (
        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-label">Total:</span>
            <span className="stat-value">{entities.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Selected:</span>
            <span className="stat-value">{selectedEntities.size}</span>
          </div>
          {Object.entries(stats.by_type || {}).map(([type, count]) => (
            <div key={type} className="stat-item">
              <span className="stat-label">{type}:</span>
              <span className="stat-value">{count as number}</span>
            </div>
          ))}
          {stats.avg_confidence && (
            <div className="stat-item">
              <span className="stat-label">Avg Confidence:</span>
              <span className="stat-value">{(stats.avg_confidence * 100).toFixed(1)}%</span>
            </div>
          )}
        </div>
      )}

      {/* Controls */}
      {entities.length > 0 && (
        <div className="review-controls">
          <div className="filter-controls">
            <select 
              value={filterType} 
              onChange={(e) => setFilterType(e.target.value)}
              className="filter-select"
            >
              <option value="all">All Types</option>
              {uniqueTypes.map(type => {
                const info = getEntityTypeInfo(type)
                return (
                  <option key={type} value={type}>
                    {info.icon} {type}
                  </option>
                )
              })}
            </select>
            
            <select 
              value={sortBy} 
              onChange={(e) => setSortBy(e.target.value as any)}
              className="sort-select"
            >
              <option value="confidence">Sort by Confidence</option>
              <option value="type">Sort by Type</option>
              <option value="text">Sort by Text</option>
            </select>
          </div>

          <div className="bulk-controls">
            <button onClick={selectAll} className="select-all-button">
              Select All
            </button>
            <button onClick={deselectAll} className="deselect-all-button">
              Deselect All
            </button>
            <button 
              onClick={bulkAccept} 
              className="bulk-accept-button"
              disabled={selectedEntities.size === 0}
            >
              ✅ Accept Selected ({selectedEntities.size})
            </button>
            <button 
              onClick={bulkReject} 
              className="bulk-reject-button"
              disabled={selectedEntities.size === 0}
            >
              ❌ Reject Selected ({selectedEntities.size})
            </button>
            {undoStack.length > 0 && (
              <button onClick={undoLastAction} className="undo-button">
                ↩️ Undo Last Action
              </button>
            )}
          </div>
        </div>
      )}

      {/* Entity List */}
      <div className="entity-list">
        {filteredEntities.map(entity => {
          const typeInfo = getEntityTypeInfo(entity.type)
          const isEditing = editingEntity === entity.id
          const editValues = editedValues[entity.id] || {}
          
          return (
            <div 
              key={entity.id} 
              className={`entity-card ${selectedEntities.has(entity.id) ? 'selected' : ''}`}
            >
              <div className="entity-checkbox">
                <input
                  type="checkbox"
                  checked={selectedEntities.has(entity.id)}
                  onChange={() => toggleEntitySelection(entity.id)}
                />
              </div>
              
              <div className="entity-content">
                <div className="entity-header">
                  {isEditing ? (
                    <input
                      type="text"
                      value={editValues.text || entity.text}
                      onChange={(e) => setEditedValues({
                        ...editedValues,
                        [entity.id]: { ...editValues, text: e.target.value }
                      })}
                      className="entity-text-edit"
                    />
                  ) : (
                    <span className="entity-text">{entity.text}</span>
                  )}
                  
                  <div className="entity-meta">
                    {isEditing ? (
                      <select
                        value={editValues.type || entity.type}
                        onChange={(e) => setEditedValues({
                          ...editedValues,
                          [entity.id]: { ...editValues, type: e.target.value }
                        })}
                        className="entity-type-edit"
                      >
                        {uniqueTypes.map(type => (
                          <option key={type} value={type}>{type}</option>
                        ))}
                      </select>
                    ) : (
                      <span 
                        className="entity-type"
                        style={{ backgroundColor: typeInfo.color }}
                      >
                        {typeInfo.icon} {entity.type}
                      </span>
                    )}
                    
                    <span className="entity-confidence">
                      {(entity.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
                
                {entity.context && (
                  <div className="entity-context">{entity.context}</div>
                )}
                
                <div className="entity-normalized">
                  → {entity.normalized}
                </div>
              </div>
              
              <div className="entity-actions">
                {isEditing ? (
                  <>
                    <button 
                      onClick={() => saveEntityEdit(entity.id)}
                      className="save-edit-button"
                      title="Save changes"
                    >
                      💾
                    </button>
                    <button 
                      onClick={() => cancelEntityEdit(entity.id)}
                      className="cancel-edit-button"
                      title="Cancel"
                    >
                      ❌
                    </button>
                  </>
                ) : (
                  <>
                    <button 
                      onClick={() => startEditingEntity(entity.id, entity)}
                      className="edit-button"
                      title="Edit entity"
                    >
                      ✏️
                    </button>
                    <button 
                      onClick={() => acceptEntity(entity)}
                      className="accept-button"
                      title="Accept and add to ontology"
                    >
                      ✅
                    </button>
                    <button 
                      onClick={() => rejectEntity(entity)}
                      className="reject-button"
                      title="Reject suggestion"
                    >
                      ❌
                    </button>
                  </>
                )}
              </div>
            </div>
          )
        })}
      </div>

      {/* Complete Button */}
      {entities.length === 0 && undoStack.length > 0 && (
        <div className="review-footer">
          <button onClick={onComplete} className="complete-button">
            ✨ Complete Review
          </button>
        </div>
      )}
    </div>
  )
}

export default EntityAnnotationReview