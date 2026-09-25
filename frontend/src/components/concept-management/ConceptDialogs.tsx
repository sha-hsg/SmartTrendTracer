import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Plus,
  Trash2,
  Save,
} from 'lucide-react'
import TagReorganizerPersistent from '../tag-reorganizer/TagReorganizerPersistent'
import type { Concept } from './types'
import type { ConceptTreeNode } from './ConceptTreePanel'

interface ConceptDialogsProps {
  // Edit dialog
  editDialogOpen: boolean
  setEditDialogOpen: (open: boolean) => void
  handleUpdateConcept: () => void

  // Create dialog
  createDialogOpen: boolean
  setCreateDialogOpen: (open: boolean) => void
  handleCreateConcept: () => void

  // Delete dialog
  deleteDialogOpen: boolean
  setDeleteDialogOpen: (open: boolean) => void
  handleDeleteConcept: () => void
  selectedConcept: ConceptTreeNode | null

  // Reorganizer dialog
  reorganizerDialogOpen: boolean
  setReorganizerDialogOpen: (open: boolean) => void

  // Form state
  formData: Partial<Concept>
  setFormData: (data: Partial<Concept>) => void
}

function EntityTypeSelect({
  value,
  onValueChange,
}: {
  value: string
  onValueChange: (value: string) => void
}) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="concept">Concept</SelectItem>
        <SelectItem value="person">Person</SelectItem>
        <SelectItem value="organisation">Organisation</SelectItem>
        <SelectItem value="location">Location</SelectItem>
        <SelectItem value="event">Event</SelectItem>
        <SelectItem value="topic">Topic</SelectItem>
      </SelectContent>
    </Select>
  )
}

export default function ConceptDialogs({
  editDialogOpen,
  setEditDialogOpen,
  handleUpdateConcept,
  createDialogOpen,
  setCreateDialogOpen,
  handleCreateConcept,
  deleteDialogOpen,
  setDeleteDialogOpen,
  handleDeleteConcept,
  selectedConcept,
  reorganizerDialogOpen,
  setReorganizerDialogOpen,
  formData,
  setFormData,
}: ConceptDialogsProps) {
  return (
    <>
      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Concept</DialogTitle>
            <DialogDescription>
              Update the concept details
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Display Name</Label>
              <Input
                value={formData.display_name || ''}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
            </div>
            <div>
              <Label>Entity Type</Label>
              <EntityTypeSelect
                value={formData.entity_type || 'concept'}
                onValueChange={(value) => setFormData({ ...formData, entity_type: value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateConcept}>
              <Save className="h-4 w-4 mr-2" />
              Save Changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Dialog */}
      <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Concept</DialogTitle>
            <DialogDescription>
              Add a new concept to the hierarchy
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Display Name *</Label>
              <Input
                value={formData.display_name || ''}
                onChange={(e) => setFormData({ ...formData, display_name: e.target.value })}
                placeholder="e.g., Machine Learning"
              />
            </div>
            <div>
              <Label>Slug *</Label>
              <Input
                value={formData.slug || ''}
                onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                placeholder="e.g., machine-learning"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                value={formData.description || ''}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional description..."
              />
            </div>
            <div>
              <Label>Entity Type</Label>
              <EntityTypeSelect
                value={formData.entity_type || 'concept'}
                onValueChange={(value) => setFormData({ ...formData, entity_type: value })}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCreateDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateConcept}>
              <Plus className="h-4 w-4 mr-2" />
              Create Concept
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Concept</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{selectedConcept?.display_name}"?
              This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDeleteConcept}>
              <Trash2 className="h-4 w-4 mr-2" />
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Advanced AI Reorganization Dialog */}
      <Dialog open={reorganizerDialogOpen} onOpenChange={setReorganizerDialogOpen}>
        <DialogContent className="max-w-7xl h-[85vh] p-0">
          <div className="h-full overflow-hidden">
            <TagReorganizerPersistent />
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}
