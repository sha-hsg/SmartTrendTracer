import { useState, useEffect } from 'react'
import axios from 'axios'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import {
  TooltipProvider,
} from "@/components/ui/tooltip"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  RefreshCw,
  Sparkles,
  FolderTree,
  AlertCircle,
  CheckCircle,
  Loader2,
  GitBranch,
  FileDown,
} from 'lucide-react'
import TagReorganizerPersistent from '../TagReorganizerPersistent'
import ConceptTree from './ConceptTree'
import ConceptDetails, { SynonymsPanel } from './ConceptDetails'
import { CreateConceptPanel, GraphPanel } from './ConceptActions'
import type { TagConcept, ConceptDetails as ConceptDetailsType } from './types'

export default function TagOntologyModern() {
  const [tree, setTree] = useState<TagConcept[]>([])
  const [selectedConcept, setSelectedConcept] = useState<ConceptDetailsType | null>(null)
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [showReorganizer, setShowReorganizer] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)

  const [newConceptForm, setNewConceptForm] = useState({
    tag: '',
    display_name: '',
    description: '',
    parent_id: '' as string
  })

  const [searchTerm, setSearchTerm] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    fetchOntologyTree()
  }, [])

  useEffect(() => {
    if (successMessage) {
      const timer = setTimeout(() => setSuccessMessage(''), 3000)
      return () => clearTimeout(timer)
    }
  }, [successMessage])

  useEffect(() => {
    if (errorMessage) {
      const timer = setTimeout(() => setErrorMessage(''), 5000)
      return () => clearTimeout(timer)
    }
  }, [errorMessage])

  const fetchOntologyTree = async () => {
    try {
      const response = await axios.get(`/api/ontology/tree`)
      setTree(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching ontology tree:', error)
      setErrorMessage('Failed to load tag ontology')
      setLoading(false)
    }
  }

  const fetchConceptDetails = async (conceptId: string) => {
    try {
      const response = await axios.get(`/api/ontology/concept/${conceptId}`)
      setSelectedConcept({
        ...response.data,
        tag: response.data.tag || '',
        display_name: response.data.display_name || '',
        description: response.data.description || '',
        level: response.data.level || 0,
        path: response.data.path || ''
      })
    } catch (error) {
      console.error('Error fetching concept details:', error)
      setErrorMessage('Failed to load concept details')
    }
  }

  const createConcept = async () => {
    setActionLoading(true)
    try {
      const conceptData = {
        ...newConceptForm,
        parent_id: newConceptForm.parent_id || null
      }
      await axios.post(`/api/ontology/concept`, conceptData)
      fetchOntologyTree()
      setNewConceptForm({
        tag: '',
        display_name: '',
        description: '',
        parent_id: ''
      })
      setSuccessMessage('Concept created successfully!')
    } catch (error: any) {
      setErrorMessage(`Error creating concept: ${error.response?.data?.detail || error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const updateConcept = async () => {
    if (!selectedConcept) return

    setActionLoading(true)
    try {
      await axios.put(`/api/ontology/concept/${selectedConcept.id}`, {
        display_name: selectedConcept.display_name,
        description: selectedConcept.description
      })
      fetchOntologyTree()
      setEditMode(false)
      setSuccessMessage('Concept updated successfully!')
    } catch (error: any) {
      setErrorMessage(`Error updating concept: ${error.response?.data?.detail || error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const deleteConcept = async (conceptId: string) => {
    if (!confirm('Are you sure you want to delete this concept?')) return

    setActionLoading(true)
    try {
      await axios.delete(`/api/ontology/concept/${conceptId}`)
      fetchOntologyTree()
      setSelectedConcept(null)
      setSuccessMessage('Concept deleted successfully!')
    } catch (error: any) {
      setErrorMessage(`Error deleting concept: ${error.response?.data?.detail || error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const addSynonym = async (synonym: string) => {
    if (!selectedConcept || !synonym) return

    setActionLoading(true)
    try {
      await axios.post(`/api/ontology/concept/${selectedConcept.id}/alias`, {
        alias_text: synonym,
        alias_type: 'synonym'
      })
      fetchConceptDetails(selectedConcept.id)
      setSuccessMessage('Synonym added successfully!')
    } catch (error: any) {
      setErrorMessage(`Error adding synonym: ${error.response?.data?.detail || error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId)
    } else {
      newExpanded.add(nodeId)
    }
    setExpandedNodes(newExpanded)
  }

  const exportOntology = async () => {
    try {
      const response = await axios.get(`/api/ontology/export`)

      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5)
      a.href = url
      a.download = `tag_ontology_export_${timestamp}.json`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)

      setSuccessMessage(`Exported ${response.data.stats?.total_concepts ?? response.data.concepts?.length ?? 0} concepts successfully!`)
    } catch (error: any) {
      setErrorMessage(`Export failed: ${error.response?.data?.detail || error.message}`)
    }
  }

  const rebuildMappings = async () => {
    setActionLoading(true)
    try {
      await axios.post(`/api/ontology/rebuild-mappings`)
      setSuccessMessage('Tag mappings rebuilt successfully!')
    } catch (error) {
      console.error('Error rebuilding mappings:', error)
      setErrorMessage('Failed to rebuild mappings')
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin" />
        <span className="ml-2">Loading tag ontology...</span>
      </div>
    )
  }

  return (
    <TooltipProvider>
    <div className="max-w-full mx-auto p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl flex items-center gap-2">
                <FolderTree className="w-6 h-6" />
                Concept Hierarchy Manager
              </CardTitle>
              <CardDescription>
                Organize and manage your concept hierarchy with AI assistance
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Dialog open={showReorganizer} onOpenChange={setShowReorganizer}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    Concept Reorganizer
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
                  <DialogHeader>
                    <DialogTitle>Concept Reorganizer - Persistent & Recoverable</DialogTitle>
                    <DialogDescription>
                      AI-powered concept reorganization with automatic save and recovery. Results persist across browser sessions and server restarts.
                    </DialogDescription>
                  </DialogHeader>
                  <TagReorganizerPersistent />
                </DialogContent>
              </Dialog>

              <Button
                variant="outline"
                onClick={exportOntology}
                title="Export ontology as JSON"
              >
                <FileDown className="w-4 h-4 mr-2" />
                Export
              </Button>

              <Button
                variant="outline"
                onClick={rebuildMappings}
                disabled={actionLoading}
              >
                {actionLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 mr-2" />
                )}
                Rebuild Mappings
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Alerts */}
      {successMessage && (
        <Alert className="border-green-500">
          <CheckCircle className="w-4 h-4 text-green-500" />
          <AlertDescription>{successMessage}</AlertDescription>
        </Alert>
      )}

      {errorMessage && (
        <Alert variant="destructive">
          <AlertCircle className="w-4 h-4" />
          <AlertDescription>{errorMessage}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tree View */}
        <ConceptTree
          tree={tree}
          selectedConceptId={selectedConcept?.id ?? null}
          expandedNodes={expandedNodes}
          searchTerm={searchTerm}
          onSearchChange={setSearchTerm}
          onSelectConcept={fetchConceptDetails}
          onToggleNode={toggleNode}
        />

        {/* Details and Actions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">
              {selectedConcept ? 'Concept Details' : 'Create New Concept'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="details" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="details">Details</TabsTrigger>
                <TabsTrigger value="synonyms">Synonyms</TabsTrigger>
                <TabsTrigger value="graph">
                  <GitBranch className="w-4 h-4 mr-1" />
                  Graph
                </TabsTrigger>
                <TabsTrigger value="create">Create New</TabsTrigger>
              </TabsList>

              <TabsContent value="details" className="space-y-4">
                <ConceptDetails
                  selectedConcept={selectedConcept}
                  editMode={editMode}
                  actionLoading={actionLoading}
                  onSetEditMode={setEditMode}
                  onUpdateConcept={updateConcept}
                  onDeleteConcept={deleteConcept}
                  onSetSelectedConcept={setSelectedConcept}
                  onFetchConceptDetails={fetchConceptDetails}
                />
              </TabsContent>

              <TabsContent value="synonyms" className="space-y-4">
                <SynonymsPanel
                  selectedConcept={selectedConcept}
                  actionLoading={actionLoading}
                  onAddSynonym={addSynonym}
                />
              </TabsContent>

              <TabsContent value="graph" className="space-y-4">
                <GraphPanel />
              </TabsContent>

              <TabsContent value="create" className="space-y-4">
                <CreateConceptPanel
                  newConceptForm={newConceptForm}
                  actionLoading={actionLoading}
                  onSetNewConceptForm={setNewConceptForm}
                  onCreateConcept={createConcept}
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
    </TooltipProvider>
  )
}
