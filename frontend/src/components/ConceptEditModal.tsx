import { useState, useEffect } from 'react'
import axios from 'axios'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { 
  Loader2, 
  Save, 
  X,
  Info,
  Hash,
  Type,
  FileText,
  Tag,
  Eye
} from "lucide-react"

interface Concept {
  _id?: string
  id: string
  slug: string
  name: string
  display_name: string
  description: string
  entity_type?: string
  usage_count?: number
  parents?: any[]
  children?: any[]
}

interface ConceptEditModalProps {
  tagName: string
  isOpen: boolean
  onClose: () => void
  onUpdate?: (concept: Concept) => void
}

export default function ConceptEditModal({ 
  tagName, 
  isOpen, 
  onClose,
  onUpdate 
}: ConceptEditModalProps) {
  const [concept, setConcept] = useState<Concept | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editedConcept, setEditedConcept] = useState<Partial<Concept>>({})

  useEffect(() => {
    if (isOpen && tagName) {
      loadConcept()
    }
  }, [isOpen, tagName])

  const loadConcept = async () => {
    setLoading(true)
    setError(null)
    try {
      // First try to find concept by slug/name
      const response = await axios.get(
        `/api/ontology/find-by-name/${encodeURIComponent(tagName)}`
      )
      
      if (response.data) {
        setConcept(response.data)
        setEditedConcept({
          slug: response.data.slug || '',
          name: response.data.name || response.data.display_name || '',
          display_name: response.data.display_name || '',
          description: response.data.description || ''
        })
      } else {
        setError("Concept not found")
      }
    } catch (err: any) {
      console.error("Failed to load concept:", err)
      setError(err.response?.data?.detail || "Failed to load concept")
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!concept) return
    
    setSaving(true)
    setError(null)
    
    try {
      const updateData: any = {
        slug: editedConcept.slug,
        display_name: editedConcept.display_name,
        description: editedConcept.description
      }
      
      // Only include name if it's been edited
      if (editedConcept.name && editedConcept.name !== editedConcept.display_name) {
        updateData.name = editedConcept.name
      }
      
      // Use the concept's ID for updating
      const conceptId = concept.id || concept._id
      await axios.put(
        `/api/ontology/concepts/${conceptId}`,
        updateData
      )
      
      // Update local state
      const updatedConcept = { ...concept, ...updateData }
      setConcept(updatedConcept)
      
      // Notify parent component
      if (onUpdate) {
        onUpdate(updatedConcept)
      }
      
      // Show success and close after a delay
      setTimeout(() => {
        onClose()
      }, 500)
    } catch (err: any) {
      console.error("Failed to update concept:", err)
      setError(err.response?.data?.detail || "Failed to update concept")
    } finally {
      setSaving(false)
    }
  }

  const handleInputChange = (field: keyof Concept, value: string) => {
    setEditedConcept(prev => ({ ...prev, [field]: value }))
  }

  if (!isOpen) return null

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Tag className="h-5 w-5" />
            Edit Concept
          </DialogTitle>
          <DialogDescription>
            Modify the concept properties. Changes will affect how this concept appears throughout the system.
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin" />
            <span className="ml-2">Loading concept...</span>
          </div>
        ) : error ? (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : concept ? (
          <div className="space-y-4">
            {/* Read-only fields */}
            <div className="grid grid-cols-2 gap-4 p-3 bg-gray-50 rounded-lg">
              <div>
                <Label className="text-xs text-gray-500 flex items-center gap-1">
                  <Hash className="h-3 w-3" />
                  Concept ID
                </Label>
                <div className="font-mono text-sm mt-1">{concept.id || 'Not assigned'}</div>
              </div>
              <div>
                <Label className="text-xs text-gray-500 flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  MongoDB ID
                </Label>
                <div className="font-mono text-xs mt-1 truncate" title={concept._id}>
                  {concept._id}
                </div>
              </div>
              {concept.entity_type && (
                <div>
                  <Label className="text-xs text-gray-500">Entity Type</Label>
                  <Badge variant="outline" className="mt-1">
                    {concept.entity_type}
                  </Badge>
                </div>
              )}
              {concept.usage_count !== undefined && (
                <div>
                  <Label className="text-xs text-gray-500">Usage Count</Label>
                  <div className="text-sm mt-1">{concept.usage_count}</div>
                </div>
              )}
            </div>

            {/* Editable fields */}
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="slug" className="flex items-center gap-1">
                    <Type className="h-3 w-3" />
                    Slug
                  </Label>
                  <Input
                    id="slug"
                    value={editedConcept.slug || ''}
                    onChange={(e) => handleInputChange('slug', e.target.value)}
                    placeholder="url-friendly-name"
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    URL-friendly identifier (lowercase, hyphens)
                  </p>
                </div>
                
                <div>
                  <Label htmlFor="name" className="flex items-center gap-1">
                    <Type className="h-3 w-3" />
                    Name
                  </Label>
                  <Input
                    id="name"
                    value={editedConcept.name || ''}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    placeholder="Concept Name"
                    className="mt-1"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Internal name for the concept
                  </p>
                </div>
              </div>

              <div>
                <Label htmlFor="display_name" className="flex items-center gap-1">
                  <Eye className="h-3 w-3" />
                  Display Name
                </Label>
                <Input
                  id="display_name"
                  value={editedConcept.display_name || ''}
                  onChange={(e) => handleInputChange('display_name', e.target.value)}
                  placeholder="Display Name"
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  How this concept appears in the UI
                </p>
              </div>

              <div>
                <Label htmlFor="description" className="flex items-center gap-1">
                  <FileText className="h-3 w-3" />
                  Description
                </Label>
                <Textarea
                  id="description"
                  value={editedConcept.description || ''}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  placeholder="Describe this concept..."
                  rows={3}
                  className="mt-1"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Detailed description of what this concept represents
                </p>
              </div>
            </div>

            {/* Info about relationships */}
            {((concept.parents?.length ?? 0) > 0 || (concept.children?.length ?? 0) > 0) && (
              <div className="p-3 bg-blue-50 rounded-lg">
                <div className="flex items-start gap-2">
                  <Info className="h-4 w-4 text-blue-600 mt-0.5" />
                  <div className="text-sm text-blue-800">
                    <div>
                      This concept has {concept.parents?.length || 0} parent(s) 
                      and {concept.children?.length || 0} children in the hierarchy.
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        ) : null}

        <div className="flex justify-end gap-2 mt-4">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={saving}
          >
            <X className="h-4 w-4 mr-1" />
            Cancel
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving || loading || !!error || !concept}
          >
            {saving ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Saving...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-1" />
                Save Changes
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}