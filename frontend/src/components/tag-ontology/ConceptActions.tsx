import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import {
  Plus,
  Loader2,
} from 'lucide-react'
import OntologyGraph from '../OntologyGraph'

interface NewConceptForm {
  tag: string
  display_name: string
  description: string
  parent_id: string
}

interface ConceptActionsProps {
  newConceptForm: NewConceptForm
  actionLoading: boolean
  onSetNewConceptForm: (form: NewConceptForm) => void
  onCreateConcept: () => void
}

export function CreateConceptPanel({
  newConceptForm,
  actionLoading,
  onSetNewConceptForm,
  onCreateConcept,
}: ConceptActionsProps) {
  return (
    <div className="grid gap-4">
      <div>
        <Label>Tag ID</Label>
        <Input
          placeholder="e.g., machine-learning"
          value={newConceptForm.tag}
          onChange={(e) => onSetNewConceptForm({
            ...newConceptForm,
            tag: e.target.value
          })}
        />
      </div>

      <div>
        <Label>Display Name</Label>
        <Input
          placeholder="e.g., Machine Learning"
          value={newConceptForm.display_name}
          onChange={(e) => onSetNewConceptForm({
            ...newConceptForm,
            display_name: e.target.value
          })}
        />
      </div>

      <div>
        <Label>Description</Label>
        <Textarea
          placeholder="Enter concept description..."
          value={newConceptForm.description}
          onChange={(e) => onSetNewConceptForm({
            ...newConceptForm,
            description: e.target.value
          })}
          rows={3}
        />
      </div>

      <div>
        <Label>Parent Concept (Optional)</Label>
        <Input
          type="text"
          placeholder="Parent concept ID (e.g., c_0001)"
          value={newConceptForm.parent_id}
          onChange={(e) => onSetNewConceptForm({
            ...newConceptForm,
            parent_id: e.target.value
          })}
        />
      </div>

      <Button
        onClick={onCreateConcept}
        disabled={!newConceptForm.tag || !newConceptForm.display_name || actionLoading}
        className="w-full"
      >
        {actionLoading ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Creating...
          </>
        ) : (
          <>
            <Plus className="w-4 h-4 mr-2" />
            Create Concept
          </>
        )}
      </Button>
    </div>
  )
}

export function GraphPanel() {
  return (
    <div className="h-[600px]">
      <OntologyGraph />
    </div>
  )
}
