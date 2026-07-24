import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Check, X, Edit2, Save } from 'lucide-react'

export interface EntitySuggestion {
  id: string
  text: string
  type: string
  confidence: number
  context: string
  normalized: string
  metadata: Record<string, any>
}

export interface EntityTypeInfo {
  color: string
  icon: string
}

interface EntityReviewCardProps {
  entity: EntitySuggestion
  typeInfo: EntityTypeInfo
  isSelected: boolean
  isEditing: boolean
  editValues: Record<string, any>
  uniqueTypes: string[]
  onToggleSelection: (entityId: string) => void
  onStartEditing: (entityId: string, entity: EntitySuggestion) => void
  onSaveEdit: (entityId: string) => void
  onCancelEdit: (entityId: string) => void
  onEditValueChange: (entityId: string, values: Record<string, any>) => void
  onAccept: (entity: EntitySuggestion) => void
  onReject: (entity: EntitySuggestion) => void
}

export default function EntityReviewCard({
  entity,
  typeInfo,
  isSelected,
  isEditing,
  editValues,
  uniqueTypes,
  onToggleSelection,
  onStartEditing,
  onSaveEdit,
  onCancelEdit,
  onEditValueChange,
  onAccept,
  onReject,
}: EntityReviewCardProps) {
  return (
    <Card
      className={`p-4 ${isSelected ? 'ring-2 ring-blue-500' : ''}`}
    >
      <div className="flex items-start gap-3">
        <Checkbox
          checked={isSelected}
          onCheckedChange={() => onToggleSelection(entity.id)}
          className="mt-1"
        />

        <div className="flex-1 space-y-2">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              {isEditing ? (
                <Input
                  value={editValues.text || entity.text}
                  onChange={(e) => onEditValueChange(entity.id, { ...editValues, text: e.target.value })}
                  className="mb-2"
                />
              ) : (
                <span className="font-medium text-lg">{entity.text}</span>
              )}

              <div className="flex items-center gap-2 mt-2">
                {isEditing ? (
                  <Select
                    value={editValues.type || entity.type}
                    onValueChange={(value) => onEditValueChange(entity.id, { ...editValues, type: value })}
                  >
                    <SelectTrigger className="w-[180px]">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {uniqueTypes.map(type => (
                        <SelectItem key={type} value={type}>{type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Badge className={typeInfo.color}>
                    {typeInfo.icon} {entity.type}
                  </Badge>
                )}

                <Badge variant="outline">
                  {(entity.confidence * 100).toFixed(1)}%
                </Badge>
              </div>
            </div>

            <div className="flex gap-1">
              {isEditing ? (
                <>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onSaveEdit(entity.id)}
                    title="Save changes"
                  >
                    <Save className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onCancelEdit(entity.id)}
                    title="Cancel"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </>
              ) : (
                <>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onStartEditing(entity.id, entity)}
                    title="Edit entity"
                  >
                    <Edit2 className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onAccept(entity)}
                    title="Accept and add to ontology"
                    className="text-green-600 hover:text-green-700"
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => onReject(entity)}
                    title="Reject suggestion"
                    className="text-red-600 hover:text-red-700"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </>
              )}
            </div>
          </div>

          {entity.context && (
            <p className="text-sm text-gray-600 italic">"{entity.context}"</p>
          )}

          <p className="text-sm text-gray-500">
            &rarr; {entity.normalized}
          </p>
        </div>
      </div>
    </Card>
  )
}
