import { useState, useEffect } from 'react'
import { API_BASE_URL } from '@/config/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Sparkles, AlertCircle, Undo2, CheckSquare, XSquare, FileText } from 'lucide-react'
import ModelBadge from './ModelBadge'
import UnifiedModelSelector from './UnifiedModelSelector'
import { useModelSelector } from '@/hooks/useModelSelector'
import EntityReviewCard from './EntityReviewCard'
import type { EntitySuggestion, EntityTypeInfo } from './EntityReviewCard'

interface PaperEntityAnnotationReviewProps {
  paperId: number
  onComplete?: () => void
}

interface UndoAction {
  type: 'accept' | 'reject' | 'bulk'
  entities: EntitySuggestion[]
  timestamp: number
}

function PaperEntityAnnotationReview({ paperId, onComplete }: PaperEntityAnnotationReviewProps) {
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
  const [paperTitle, setPaperTitle] = useState<string>('')

  // Use unified model selector hook for entity extraction
  const {
    selectedModel,
    loading: modelLoading,
    selectModel
  } = useModelSelector('entity_extraction')

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
      // Create abort controller for timeout and cancellation
      const controller = new AbortController()
      // Increase timeout to 5 minutes for GPT-5 and Gemini processing
      const timeoutId = setTimeout(() => {
        controller.abort()
        console.warn('Entity extraction timed out after 5 minutes')
      }, 300000) // 5 minute timeout

      console.log(`Starting entity extraction with model: ${selectedModel}`)

      const response = await fetch(`${API_BASE_URL}/api/papers/${paperId}/entities/extract?model_choice=${selectedModel}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ use_fast_model: false }),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (response.ok) {
        const data = await response.json()
        console.log(`Extraction complete. Found ${data.entities?.length || 0} entities using model: ${data.model}`)
        setEntities(data.entities || [])
        setStats(data.stats)
        setExtractionModel(data.model || 'unknown')
        setPaperTitle(data.paper_title || `Paper ${paperId}`)

        // Show message if it's a placeholder implementation
        if (data.message) {
          console.info('Entity Extraction:', data.message)
        }

        // Alert if no entities were found
        if (!data.entities || data.entities.length === 0) {
          console.warn('No entities were extracted. This might indicate an issue with the extraction process.')
        }
      } else {
        const errorText = await response.text()
        console.error('Error response from server:', errorText)
        alert(`Entity extraction failed: ${errorText}`)
      }
    } catch (error: any) {
      console.error('Error extracting entities:', error)
      if (error.name === 'AbortError') {
        console.error('Entity extraction was cancelled or timed out after 5 minutes')
        alert('Entity extraction timed out. The paper might be too long or the model might be slow. Try using a faster model.')
      } else {
        alert(`Entity extraction error: ${error.message}`)
      }
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
        setEntities(entities.filter(e => e.id !== entity.id))
        setUndoStack([...undoStack, { type: 'accept', entities: [entity], timestamp: Date.now() }])
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
        body: JSON.stringify({ entity_id: entity.id, action: 'reject' })
      })

      if (response.ok) {
        setEntities(entities.filter(e => e.id !== entity.id))
        setUndoStack([...undoStack, { type: 'reject', entities: [entity], timestamp: Date.now() }])
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
      const response = await fetch(`${API_BASE_URL}/api/papers/${paperId}/entities/bulk-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_ids: Array.from(selectedEntities),
          action: 'accept_all',
          entities: entitiesToAccept
        })
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Bulk accept result:', result)
        setEntities(entities.filter(e => !selectedEntities.has(e.id)))
        setUndoStack([...undoStack, { type: 'bulk', entities: entitiesToAccept, timestamp: Date.now() }])
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
      const response = await fetch(`${API_BASE_URL}/api/papers/${paperId}/entities/bulk-action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          entity_ids: Array.from(selectedEntities),
          action: 'reject_all'
        })
      })

      if (response.ok) {
        setEntities(entities.filter(e => !selectedEntities.has(e.id)))
        setUndoStack([...undoStack, { type: 'bulk', entities: entitiesToReject, timestamp: Date.now() }])
        setSelectedEntities(new Set())
      }
    } catch (error) {
      console.error('Error bulk rejecting:', error)
    }
  }

  const undoLastAction = () => {
    if (undoStack.length === 0) return
    const lastAction = undoStack[undoStack.length - 1]
    setEntities([...entities, ...lastAction.entities])
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
      [entityId]: { text: entity.text, type: entity.type }
    })
  }

  const saveEntityEdit = (_entityId: string) => {
    setEditingEntity(null)
  }

  const cancelEntityEdit = (entityId: string) => {
    setEditingEntity(null)
    const newEditedValues = { ...editedValues }
    delete newEditedValues[entityId]
    setEditedValues(newEditedValues)
  }

  const handleEditValueChange = (entityId: string, values: Record<string, any>) => {
    setEditedValues({ ...editedValues, [entityId]: values })
  }

  const getFilteredEntities = () => {
    let filtered = [...entities]
    if (filterType !== 'all') {
      filtered = filtered.filter(e => e.type === filterType)
    }
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'confidence': return b.confidence - a.confidence
        case 'type': return a.type.localeCompare(b.type)
        case 'text': return a.text.localeCompare(b.text)
        default: return 0
      }
    })
    return filtered
  }

  const getEntityTypeInfo = (type: string): EntityTypeInfo => {
    if (!schema) return { color: 'bg-gray-100 text-gray-700', icon: '📌' }

    const typeColorMap: Record<string, string> = {
      'person': 'bg-blue-100 text-blue-700',
      'organisation': 'bg-purple-100 text-purple-700',
      'organization': 'bg-purple-100 text-purple-700',
      'model': 'bg-pink-100 text-pink-700',
      'method': 'bg-orange-100 text-orange-700',
      'dataset': 'bg-green-100 text-green-700',
      'benchmark': 'bg-yellow-100 text-yellow-700',
      'metric': 'bg-purple-100 text-purple-700',
      'research-topic': 'bg-cyan-100 text-cyan-700',
      'location': 'bg-red-100 text-red-700',
      'event': 'bg-pink-100 text-pink-700',
      'tool': 'bg-green-100 text-green-700',
      'concept': 'bg-purple-100 text-purple-700',
      'paper': 'bg-blue-100 text-blue-700',
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

    return { color: typeColorMap[type.toLowerCase()] || typeColorMap.default, icon: '📌' }
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
              Paper Entity Annotation Review
            </CardTitle>
            <CardDescription className="flex items-center gap-2">
              <FileText className="h-4 w-4" />
              {paperTitle || `Paper #${paperId}`}
            </CardDescription>
          </div>
          {extractionModel && (
            <ModelBadge model={extractionModel} size="medium" />
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Extraction Button */}
        {entities.length === 0 && !loading && (
          <Alert>
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-4">
                <span>No entities extracted yet. Run automatic annotation to detect entities in this paper.</span>
                <UnifiedModelSelector
                  taskType="entity_extraction"
                  value={selectedModel || ''}
                  onValueChange={selectModel}
                  label="Entity Extraction Model"
                  description="Select the AI model for extracting entities from this paper"
                  disabled={modelLoading || extracting}
                  compact={false}
                />
                <Button
                  onClick={runExtraction}
                  disabled={extracting || !selectedModel}
                  className="w-full"
                >
                  {extracting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Extracting entities...
                    </>
                  ) : (
                    <>
                      <Sparkles className="mr-2 h-4 w-4" />
                      Run Automatic Annotation
                    </>
                  )}
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        )}

        {/* Loading overlay while extracting */}
        {extracting && (
          <div className="flex flex-col items-center justify-center py-12">
            <Loader2 className="h-12 w-12 animate-spin text-purple-600 mb-4" />
            <h3 className="text-lg font-semibold text-purple-700 mb-2">Processing with AI...</h3>
            <p className="text-sm text-gray-600">
              Extracting entities from full paper content...
            </p>
          </div>
        )}

        {/* Stats Bar */}
        {entities.length > 0 && (
          <div className="flex flex-wrap gap-2">
            <Badge variant="secondary">Total: {entities.length}</Badge>
            <Badge variant="secondary">Selected: {selectedEntities.size}</Badge>
            {Object.entries(stats.by_type || {}).map(([type, count]) => (
              <Badge key={type} variant="outline">{type}: {count as number}</Badge>
            ))}
            {stats.avg_confidence && (
              <Badge variant="outline">Avg Confidence: {(stats.avg_confidence * 100).toFixed(1)}%</Badge>
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
              <Button variant="outline" size="sm" onClick={selectAll}>Select All</Button>
              <Button variant="outline" size="sm" onClick={deselectAll}>Deselect All</Button>
              <Button variant="default" size="sm" onClick={bulkAccept} disabled={selectedEntities.size === 0}>
                <CheckSquare className="mr-2 h-4 w-4" />
                Accept Selected ({selectedEntities.size})
              </Button>
              <Button variant="destructive" size="sm" onClick={bulkReject} disabled={selectedEntities.size === 0}>
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

            {/* Re-extract with different model */}
            <div className="space-y-3">
              <UnifiedModelSelector
                taskType="entity_extraction"
                value={selectedModel || ''}
                onValueChange={selectModel}
                label="Re-extract with Different Model"
                description="Choose a different AI model to re-extract entities"
                disabled={modelLoading || extracting}
                compact={false}
              />
              <Button
                onClick={runExtraction}
                disabled={extracting || !selectedModel}
                className="w-full"
              >
                {extracting ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Re-extracting entities...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-4 w-4" />
                    Re-extract Entities
                  </>
                )}
              </Button>
            </div>
          </div>
        )}

        {/* Entity List */}
        {filteredEntities.length > 0 && (
          <ScrollArea className="h-[500px] w-full rounded-md border p-4">
            <div className="space-y-3">
              {filteredEntities.map(entity => (
                <EntityReviewCard
                  key={entity.id}
                  entity={entity}
                  typeInfo={getEntityTypeInfo(entity.type)}
                  isSelected={selectedEntities.has(entity.id)}
                  isEditing={editingEntity === entity.id}
                  editValues={editedValues[entity.id] || {}}
                  uniqueTypes={uniqueTypes}
                  onToggleSelection={toggleEntitySelection}
                  onStartEditing={startEditingEntity}
                  onSaveEdit={saveEntityEdit}
                  onCancelEdit={cancelEntityEdit}
                  onEditValueChange={handleEditValueChange}
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

export default PaperEntityAnnotationReview
