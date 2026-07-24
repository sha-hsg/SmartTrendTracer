import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Textarea } from "@/components/ui/textarea"
import {
  ChevronRight,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  Tag,
  Hash,
  Info,
  AlertCircle,
  Loader2,
  Link2,
  Twitter,
  FileText,
  FolderTree,
} from 'lucide-react'
import type { ConceptDetails as ConceptDetailsType } from './types'

interface ConceptDetailsProps {
  selectedConcept: ConceptDetailsType | null
  editMode: boolean
  actionLoading: boolean
  onSetEditMode: (mode: boolean) => void
  onUpdateConcept: () => void
  onDeleteConcept: (conceptId: string) => void
  onSetSelectedConcept: (concept: ConceptDetailsType) => void
  onFetchConceptDetails: (conceptId: string) => void
}

export default function ConceptDetails({
  selectedConcept,
  editMode,
  actionLoading,
  onSetEditMode,
  onUpdateConcept,
  onDeleteConcept,
  onSetSelectedConcept,
  onFetchConceptDetails,
}: ConceptDetailsProps) {
  return (
    <>
      {/* Details Tab Content */}
      {selectedConcept ? (
        <>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold flex items-center gap-2">
                <Tag className="w-5 h-5" />
                {selectedConcept.display_name}
              </h3>
              <div className="flex gap-2">
                {editMode ? (
                  <>
                    <Button
                      size="sm"
                      onClick={onUpdateConcept}
                      disabled={actionLoading}
                    >
                      {actionLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Save className="w-4 h-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        onSetEditMode(false)
                        onFetchConceptDetails(selectedConcept.id)
                      }}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => onSetEditMode(true)}
                    >
                      <Edit2 className="w-4 h-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="destructive"
                      onClick={() => onDeleteConcept(selectedConcept.id)}
                      disabled={actionLoading}
                    >
                      {actionLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Trash2 className="w-4 h-4" />
                      )}
                    </Button>
                  </>
                )}
              </div>
            </div>

            <Separator />

            <div className="grid gap-4">
              {/* Basic Information */}
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs text-muted-foreground">MongoDB _id</Label>
                    <Input value={selectedConcept._id || selectedConcept.id || ''} disabled className="font-mono text-xs" />
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Concept ID</Label>
                    <Input value={selectedConcept.id || ''} disabled className="font-mono text-xs" />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs text-muted-foreground">Slug</Label>
                    <Input value={selectedConcept.slug || selectedConcept.tag || ''} disabled className="font-mono text-xs" />
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Entity Type</Label>
                    <Input value={selectedConcept.entity_type || 'topic'} disabled className="text-xs" />
                  </div>
                </div>

                <div>
                  <Label>Display Name</Label>
                  <Input
                    value={selectedConcept.display_name || ''}
                    onChange={(e) => onSetSelectedConcept({
                      ...selectedConcept,
                      display_name: e.target.value
                    })}
                    disabled={!editMode}
                  />
                </div>

                <div>
                  <Label>Description</Label>
                  <Textarea
                    value={selectedConcept.description || ''}
                    onChange={(e) => onSetSelectedConcept({
                      ...selectedConcept,
                      description: e.target.value
                    })}
                    disabled={!editMode}
                    rows={3}
                  />
                </div>

                {/* Metadata */}
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <Label className="text-xs text-muted-foreground">Created At</Label>
                    <Input
                      value={selectedConcept.created_at ? new Date(selectedConcept.created_at).toLocaleString() : 'Unknown'}
                      disabled
                      className="text-xs"
                    />
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Created By</Label>
                    <Input value={selectedConcept.created_by || 'system'} disabled className="text-xs" />
                  </div>
                </div>

                {/* Auto-generated and original tag */}
                {selectedConcept.auto_generated && (
                  <div className="p-2 rounded-md bg-muted">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="secondary" className="text-xs">Auto-generated</Badge>
                      {selectedConcept.original_tag_text && (
                        <span className="text-xs text-muted-foreground">
                          from: "{selectedConcept.original_tag_text}"
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>

              <Separator />

              {/* Hierarchy Information */}
              <div className="space-y-4">
                <h4 className="font-semibold text-sm">Hierarchy</h4>

                {/* Parent Concepts (can be multiple) */}
                {selectedConcept.parent_details && selectedConcept.parent_details.length > 0 && (
                  <div>
                    <Label className="text-xs text-muted-foreground">
                      Parent Concept{selectedConcept.parent_details.length > 1 ? 's' : ''}
                      {selectedConcept.parent_details.length > 1 && (
                        <span className="ml-1 text-primary">(poly-hierarchy)</span>
                      )}
                    </Label>
                    <div className="mt-1 space-y-1">
                      {selectedConcept.parent_details.map((parent: any) => (
                        <div
                          key={parent.id}
                          className="p-2 rounded-md bg-muted hover:bg-accent cursor-pointer transition-colors flex items-center gap-2"
                          onClick={() => onFetchConceptDetails(parent.id)}
                        >
                          <ChevronRight className="w-4 h-4" />
                          {parent.icon ? (
                            <span className="text-base">{parent.icon}</span>
                          ) : (
                            <Tag className="w-4 h-4 text-muted-foreground" />
                          )}
                          <span className="font-medium">{parent.display_name}</span>
                          <span className="text-xs text-muted-foreground">({parent.tag})</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Child Concepts */}
                {selectedConcept.children && selectedConcept.children.length > 0 && (
                  <div>
                    <Label className="text-xs text-muted-foreground">Child Concepts ({selectedConcept.children.length})</Label>
                    <ScrollArea className="h-32 mt-1 rounded-md border">
                      <div className="p-2 space-y-1">
                        {selectedConcept.children.map(child => (
                          <div
                            key={child.id}
                            className="p-2 rounded-md hover:bg-accent cursor-pointer transition-colors flex items-center gap-2"
                            onClick={() => onFetchConceptDetails(child.id)}
                          >
                            <Tag className="w-4 h-4 text-muted-foreground" />
                            <span className="font-medium">{child.display_name}</span>
                            <span className="text-xs text-muted-foreground">({child.tag})</span>
                            {child.child_count > 0 && (
                              <Badge variant="outline" className="text-xs ml-auto">
                                {child.child_count} children
                              </Badge>
                            )}
                          </div>
                        ))}
                      </div>
                    </ScrollArea>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs text-muted-foreground">Level</Label>
                    <Input value={selectedConcept.level || ''} disabled className="mt-1" />
                  </div>
                  <div>
                    <Label className="text-xs text-muted-foreground">Path</Label>
                    <Input value={selectedConcept.path || ''} disabled className="mt-1" />
                  </div>
                </div>
              </div>

              <Separator />

              {/* Usage Statistics */}
              <div className="space-y-4">
                <h4 className="font-semibold text-sm">Usage Statistics</h4>

                {selectedConcept.usage_stats ? (
                  <div className="grid grid-cols-2 gap-4">
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <Twitter className="w-4 h-4 text-blue-500" />
                          <div className="text-2xl font-bold">{selectedConcept.usage_stats.tweet_count}</div>
                        </div>
                        <p className="text-xs text-muted-foreground">Tweets</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <FileText className="w-4 h-4 text-green-500" />
                          <div className="text-2xl font-bold">{selectedConcept.usage_stats.article_count}</div>
                        </div>
                        <p className="text-xs text-muted-foreground">Articles</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <FileText className="w-4 h-4 text-orange-500" />
                          <div className="text-2xl font-bold">{selectedConcept.usage_stats.paper_count || 0}</div>
                        </div>
                        <p className="text-xs text-muted-foreground">Papers</p>
                      </CardContent>
                    </Card>
                    <Card>
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between mb-2">
                          <Hash className="w-4 h-4 text-purple-500" />
                          <div className="text-2xl font-bold">{selectedConcept.usage_stats.total_count}</div>
                        </div>
                        <p className="text-xs text-muted-foreground">Total</p>
                      </CardContent>
                    </Card>
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Usage statistics not available</p>
                  </div>
                )}

                <div className="flex gap-4">
                  <Badge variant="secondary" className="gap-1">
                    <Hash className="w-3 h-3" />
                    {selectedConcept.child_count} direct children
                  </Badge>
                  <Badge variant="secondary" className="gap-1">
                    <FolderTree className="w-3 h-3" />
                    {selectedConcept.descendant_count} descendants
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : (
        <div className="text-center py-12 text-muted-foreground">
          <Info className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>Select a concept from the tree to view details</p>
        </div>
      )}
    </>
  )
}

interface SynonymsPanelProps {
  selectedConcept: ConceptDetailsType | null
  actionLoading: boolean
  onAddSynonym: (synonym: string) => void
}

export function SynonymsPanel({
  selectedConcept,
  actionLoading,
  onAddSynonym,
}: SynonymsPanelProps) {
  const [newSynonym, setNewSynonym] = useState('')

  const handleAddSynonym = () => {
    if (!newSynonym) return
    onAddSynonym(newSynonym)
    setNewSynonym('')
  }

  if (!selectedConcept) {
    return (
      <div className="text-center py-12 text-muted-foreground">
        <Link2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>Select a concept to manage synonyms</p>
      </div>
    )
  }

  return (
    <>
      <div className="flex gap-2">
        <Input
          placeholder="Enter synonym tag..."
          value={newSynonym}
          onChange={(e) => setNewSynonym(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') handleAddSynonym()
          }}
        />
        <Button
          onClick={handleAddSynonym}
          disabled={!newSynonym || actionLoading}
        >
          {actionLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <Plus className="w-4 h-4 mr-2" />
              Add
            </>
          )}
        </Button>
      </div>

      <div className="space-y-2">
        <Label>Current Synonyms</Label>
        {selectedConcept.synonyms.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {selectedConcept.synonyms.map(synonym => (
              <Badge
                key={synonym}
                variant="secondary"
                className="gap-1"
              >
                <Link2 className="w-3 h-3" />
                {synonym}
              </Badge>
            ))}
          </div>
        ) : (
          <p className="text-sm text-muted-foreground">
            No synonyms defined
          </p>
        )}
      </div>
    </>
  )
}
