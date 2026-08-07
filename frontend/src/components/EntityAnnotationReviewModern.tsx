import { useState, useEffect } from 'react'
import { API_BASE_URL } from '@/config/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Sparkles, AlertCircle, Undo2, CheckSquare, XSquare } from 'lucide-react'
import ModelBadge from './ModelBadge'
import UnifiedModelSelector from './UnifiedModelSelector'
import EntityCardReview from './EntityCardReview'
import type { EntitySuggestion } from './EntityCardReview'
import { getDefaultModel } from '@/config/models'

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

function EntityAnnotationReviewModern({ articleId, tweetId, onComplete }: EntityAnnotationReviewProps) {
  const [entities, setEntities] = useState<EntitySuggestion[]>([])
  const [loading, setLoading] = useState(false)
  const [extracting, setExtracting] = useState(false)
  const [selectedEntities, setSelectedEntities] = useState<Set<string>>(new Set())
  const [filterType, setFilterType] = useState<string>('all')
  const [sortBy, setSortBy] = useState<'confidence' | 'type' | 'text'>('confidence')
  const [stats, setStats] = useState<any>({})
  const [undoStack, setUndoStack] = useState<UndoAction[]>([])
  const [schema, setSchema] = useState<any>(null)
  const [editingEntity, setEditingEntity] = useState<string | null>(null)
  const [editedValues, setEditedValues] = useState<Record<string, any>>({})
  const [extractionModel, setExtractionModel] = useState<string>('')

  // Model selection with localStorage persistence - uses centralized config default
  const [selectedModel, setSelectedModel] = useState<string>(() => {
    return localStorage.getItem('preferredEntityExtractionModel') || getDefaultModel('entityExtraction')
  })

  // Save model preference to localStorage whenever it changes
  useEffect(() => {
    localStorage.setItem('preferredEntityExtractionModel', selectedModel)
  }, [selectedModel])

  // Load schema on mount
  useEffect(() => {
    loadSchema()
  }, [])

  const loadSchema = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/entities/schema`)
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

      // Add model selection
      if (selectedModel) payload.model = selectedModel

      const response = await fetch(`${API_BASE_URL}/api/entities/extract`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (response.ok) {
        const data = await response.json()
        setEntities(data.entities)
        setStats(data.stats)
        setExtractionModel(data.model || selectedModel || 'claude-sonnet-5')
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
      const response = await fetch(`${API_BASE_URL}/api/entities/review`, {
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
      const response = await fetch(`${API_BASE_URL}/api/entities/review`, {
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
      const response = await fetch(`${API_BASE_URL}/api/entities/bulk-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_ids: Array.from(selectedEntities),
          action: 'accept_all',
          article_id: articleId,
          entities: entitiesToAccept
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
      const response = await fetch(`${API_BASE_URL}/api/entities/bulk-action`, {
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

  const saveEntityEdit = (_entityId: string) => {
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
    if (!schema) return { color: 'bg-gray-100 text-gray-700', icon: '📌' }
    
    const typeColorMap: Record<string, string> = {
      'person': 'bg-blue-100 text-blue-700',
      'organization': 'bg-purple-100 text-purple-700',
      'technology': 'bg-green-100 text-green-700',
      'product': 'bg-orange-100 text-orange-700',
      'concept': 'bg-yellow-100 text-yellow-700',
      'location': 'bg-red-100 text-red-700',
      'event': 'bg-pink-100 text-pink-700',
      'default': 'bg-gray-100 text-gray-700'
    }
    
    for (const category of Object.values(schema.entity_types || {})) {
      const cat = category as any
      if (cat.tag === type) return { 
        color: typeColorMap[type.toLowerCase()] || typeColorMap.default, 
        icon: cat.icon 
      }
      
      for (const child of Object.values(cat.children || {})) {
        const ch = child as any
        if (ch.tag === type) return { 
          color: typeColorMap[type.toLowerCase()] || typeColorMap.default, 
          icon: ch.icon 
        }
      }
    }
    
    return { color: 'bg-gray-100 text-gray-700', icon: '📌' }
  }

  const filteredEntities = getFilteredEntities()
  const uniqueTypes = Array.from(new Set(entities.map(e => e.type)))

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Entity Annotation Review
            </CardTitle>
            <CardDescription>
              {articleId && <span>Article #{articleId}</span>}
              {tweetId && <span>Tweet</span>}
            </CardDescription>
          </div>
          {extractionModel && (
            <ModelBadge model={extractionModel} size="medium" />
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Extraction Configuration */}
        {entities.length === 0 && !loading && (
          <div className="space-y-4">
            <Alert>
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                No entities extracted yet. Configure your model and run automatic annotation to detect entities.
              </AlertDescription>
            </Alert>

            {/* Model Selection - Uses UnifiedModelSelector with centralized model config */}
            <div className="flex items-end gap-4">
              <div className="flex-1">
                <UnifiedModelSelector
                  taskType="entity_extraction"
                  value={selectedModel}
                  onValueChange={setSelectedModel}
                  label="AI Model for Extraction"
                  description="Select the model to use for entity extraction"
                />
              </div>

              <Button
                onClick={runExtraction}
                disabled={extracting}
                size="lg"
              >
                {extracting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Extracting...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Run Automatic Annotation
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* Loading overlay while extracting */}
        {extracting && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 animate-spin text-purple-600 mb-4" />
            <h3 className="text-lg font-semibold text-purple-700 mb-2">Processing with AI...</h3>
            <p className="text-sm text-gray-600">
              Extracting entities from {articleId ? 'article' : 'tweet'}
            </p>
          </div>
        )}

        {/* Stats Bar */}
        {entities.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">
              Total: {entities.length}
            </Badge>
            <Badge variant="secondary">
              Selected: {selectedEntities.size}
            </Badge>
            {Object.entries(stats.by_type || {}).map(([type, count]) => (
              <Badge key={type} variant="outline">
                {type}: {count as number}
              </Badge>
            ))}
            {stats.avg_confidence && (
              <Badge variant="outline">
                Avg Confidence: {(stats.avg_confidence * 100).toFixed(1)}%
              </Badge>
            )}
          </div>
        )}

        {/* Controls */}
        {entities.length > 0 && (
          <div className="space-y-4">
            <div className="flex flex-wrap gap-2">
              <Select value={filterType} onValueChange={setFilterType}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {uniqueTypes.map(type => {
                    const info = getEntityTypeInfo(type)
                    return (
                      <SelectItem key={type} value={type}>
                        <span className="flex items-center gap-2">
                          <span>{info.icon}</span>
                          <span>{type}</span>
                        </span>
                      </SelectItem>
                    )
                  })}
                </SelectContent>
              </Select>

              <Select value={sortBy} onValueChange={(value: any) => setSortBy(value)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="confidence">Sort by Confidence</SelectItem>
                  <SelectItem value="type">Sort by Type</SelectItem>
                  <SelectItem value="text">Sort by Text</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="flex flex-wrap gap-2">
              <Button variant="outline" size="sm" onClick={selectAll}>
                Select All
              </Button>
              <Button variant="outline" size="sm" onClick={deselectAll}>
                Deselect All
              </Button>
              <Button
                variant="default"
                size="sm"
                onClick={bulkAccept}
                disabled={selectedEntities.size === 0}
              >
                <CheckSquare className="mr-2 h-4 w-4" />
                Accept Selected ({selectedEntities.size})
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={bulkReject}
                disabled={selectedEntities.size === 0}
              >
                <XSquare className="mr-2 h-4 w-4" />
                Reject Selected ({selectedEntities.size})
              </Button>
              {undoStack.length > 0 && (
                <Button variant="outline" size="sm" onClick={undoLastAction}>
                  <Undo2 className="mr-2 h-4 w-4" />
                  Undo Last Action
                </Button>
              )}
            </div>
          </div>
        )}

        {/* Entity List */}
        {filteredEntities.length > 0 && (
          <ScrollArea className="h-[500px] w-full rounded-md border p-4">
            <div className="space-y-3">
              {filteredEntities.map(entity => (
                <EntityCardReview
                  key={entity.id}
                  entity={entity}
                  isSelected={selectedEntities.has(entity.id)}
                  isEditing={editingEntity === entity.id}
                  editValues={editedValues[entity.id] || {}}
                  typeInfo={getEntityTypeInfo(entity.type)}
                  uniqueTypes={uniqueTypes}
                  onToggleSelection={toggleEntitySelection}
                  onStartEditing={startEditingEntity}
                  onSaveEdit={saveEntityEdit}
                  onCancelEdit={cancelEntityEdit}
                  onEditValueChange={(entityId, values) => setEditedValues({
                    ...editedValues,
                    [entityId]: values
                  })}
                  onAccept={acceptEntity}
                  onReject={rejectEntity}
                />
              ))}
            </div>
          </ScrollArea>
        )}

        {/* Complete Button */}
        {entities.length === 0 && undoStack.length > 0 && (
          <div className="flex justify-center pt-4">
            <Button onClick={onComplete} size="lg">
              <Sparkles className="mr-2 h-4 w-4" />
              Complete Review
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default EntityAnnotationReviewModern