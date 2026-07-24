import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  Plus,
  Edit2,
  Trash2,
  Twitter,
  FileText,
  BookOpen,
  MoreVertical,
} from 'lucide-react'
import type { ConceptTreeNode } from './ConceptTreePanel'

interface ConceptDetailPanelProps {
  selectedConcept: ConceptTreeNode | null
  onEdit: () => void
  onAddChild: () => void
  onDelete: () => void
}

export default function ConceptDetailPanel({
  selectedConcept,
  onEdit,
  onAddChild,
  onDelete,
}: ConceptDetailPanelProps) {
  return (
    <Card className="lg:col-span-2">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">
            {selectedConcept ? selectedConcept.display_name : 'Select a concept'}
          </CardTitle>
          {selectedConcept && (
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={onEdit}
              >
                <Edit2 className="h-4 w-4 mr-1" />
                Edit
              </Button>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button size="sm" variant="outline">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={onAddChild}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Child
                  </DropdownMenuItem>
                  <DropdownMenuItem
                    className="text-destructive"
                    onClick={onDelete}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        {selectedConcept ? (
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-muted-foreground">Slug</Label>
                <p className="font-mono text-sm">{selectedConcept.slug}</p>
              </div>
              <div>
                <Label className="text-muted-foreground">Entity Type</Label>
                <p>{selectedConcept.entity_type || 'concept'}</p>
              </div>
            </div>

            {selectedConcept.description && (
              <div>
                <Label className="text-muted-foreground">Description</Label>
                <p className="text-sm">{selectedConcept.description}</p>
              </div>
            )}

            <Separator />

            {/* Usage Statistics */}
            {selectedConcept.usage_stats && (
              <div>
                <Label className="text-muted-foreground">Usage Statistics</Label>
                <div className="grid grid-cols-4 gap-2 mt-2">
                  <Badge variant="outline" className="justify-center">
                    <Twitter className="h-3 w-3 mr-1" />
                    {selectedConcept.usage_stats.tweet_count}
                  </Badge>
                  <Badge variant="outline" className="justify-center">
                    <FileText className="h-3 w-3 mr-1" />
                    {selectedConcept.usage_stats.article_count}
                  </Badge>
                  <Badge variant="outline" className="justify-center">
                    <BookOpen className="h-3 w-3 mr-1" />
                    {selectedConcept.usage_stats.paper_count}
                  </Badge>
                  <Badge variant="outline" className="justify-center">
                    Total: {selectedConcept.usage_stats.total_count}
                  </Badge>
                </div>
              </div>
            )}

            {/* Metadata */}
            <div className="text-sm text-muted-foreground">
              {selectedConcept.created_at && (
                <p>Created: {new Date(selectedConcept.created_at).toLocaleDateString()}</p>
              )}
              {selectedConcept.created_by && (
                <p>Created by: {selectedConcept.created_by}</p>
              )}
              {selectedConcept.auto_generated && (
                <Badge variant="secondary">Auto-generated</Badge>
              )}
              {selectedConcept.verified && (
                <Badge className="bg-green-500">Verified</Badge>
              )}
            </div>
          </div>
        ) : (
          <div className="text-center text-muted-foreground py-8">
            Select a concept from the hierarchy to view details
          </div>
        )}
      </CardContent>
    </Card>
  )
}
