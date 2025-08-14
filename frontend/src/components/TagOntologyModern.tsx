import React, { useState, useEffect } from 'react'
import axios from 'axios'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
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
  ChevronRight,
  ChevronDown,
  Plus,
  Edit2,
  Trash2,
  Save,
  X,
  Search,
  RefreshCw,
  Download,
  Upload,
  Sparkles,
  Bot,
  FolderTree,
  Tag,
  Hash,
  Info,
  AlertCircle,
  CheckCircle,
  Loader2,
  Link2,
  Twitter,
  FileText
} from 'lucide-react'
import OntologyAISuggestions from './OntologyAISuggestions'
import TagReorganizer from './TagReorganizer'
import { cn } from "@/lib/utils"

interface TagConcept {
  id: number
  tag: string
  display_name: string
  description: string | null
  child_count: number
  descendant_count: number
  synonyms: string[]
  children?: TagConcept[]
}

interface ConceptDetails {
  id: number
  tag: string
  display_name: string
  description: string | null
  parent_id: number | null
  parent?: {
    id: number
    tag: string
    display_name: string
  }
  children?: Array<{
    id: number
    tag: string
    display_name: string
    child_count: number
  }>
  level: number
  child_count: number
  descendant_count: number
  synonyms: string[]
  path: string
  usage_stats?: {
    tweet_count: number
    article_count: number
    total_count: number
  }
}

export default function TagOntologyModern() {
  const [tree, setTree] = useState<TagConcept[]>([])
  const [selectedConcept, setSelectedConcept] = useState<ConceptDetails | null>(null)
  const [loading, setLoading] = useState(true)
  const [editMode, setEditMode] = useState(false)
  const [expandedNodes, setExpandedNodes] = useState<Set<number>>(new Set())
  const [showAI, setShowAI] = useState(false)
  const [showReorganizer, setShowReorganizer] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  
  // Form states
  const [newConceptForm, setNewConceptForm] = useState({
    tag: '',
    display_name: '',
    description: '',
    parent_id: null as number | null
  })
  
  const [newSynonym, setNewSynonym] = useState('')
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
      const response = await axios.get('http://localhost:8000/api/ontology/tree')
      setTree(response.data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching ontology tree:', error)
      setErrorMessage('Failed to load tag ontology')
      setLoading(false)
    }
  }

  const fetchConceptDetails = async (conceptId: number) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/ontology/concept/${conceptId}`)
      setSelectedConcept(response.data)
    } catch (error) {
      console.error('Error fetching concept details:', error)
      setErrorMessage('Failed to load concept details')
    }
  }

  const createConcept = async () => {
    setActionLoading(true)
    try {
      await axios.post('http://localhost:8000/api/ontology/concept', newConceptForm)
      fetchOntologyTree()
      setNewConceptForm({
        tag: '',
        display_name: '',
        description: '',
        parent_id: null
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
      await axios.put(`http://localhost:8000/api/ontology/concept/${selectedConcept.id}`, {
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

  const deleteConcept = async (conceptId: number) => {
    if (!confirm('Are you sure you want to delete this concept?')) return
    
    setActionLoading(true)
    try {
      await axios.delete(`http://localhost:8000/api/ontology/concept/${conceptId}`)
      fetchOntologyTree()
      setSelectedConcept(null)
      setSuccessMessage('Concept deleted successfully!')
    } catch (error: any) {
      setErrorMessage(`Error deleting concept: ${error.response?.data?.detail || error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const addSynonym = async () => {
    if (!selectedConcept || !newSynonym) return
    
    setActionLoading(true)
    try {
      await axios.post(`http://localhost:8000/api/ontology/concept/${selectedConcept.id}/synonym`, {
        synonym_tag: newSynonym
      })
      fetchConceptDetails(selectedConcept.id)
      setNewSynonym('')
      setSuccessMessage('Synonym added successfully!')
    } catch (error: any) {
      setErrorMessage(`Error adding synonym: ${error.response?.data?.detail || error.message}`)
    } finally {
      setActionLoading(false)
    }
  }

  const toggleNode = (nodeId: number) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId)
    } else {
      newExpanded.add(nodeId)
    }
    setExpandedNodes(newExpanded)
  }

  const renderTreeNode = (node: TagConcept, level: number = 0) => {
    const isExpanded = expandedNodes.has(node.id)
    const hasChildren = node.children && node.children.length > 0
    const matchesSearch = !searchTerm || 
      node.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.synonyms.some(s => s.toLowerCase().includes(searchTerm.toLowerCase()))

    if (!matchesSearch && !hasChildren) return null

    return (
      <div key={node.id} className="py-1">
        <div
          className={cn(
            "flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent cursor-pointer transition-colors",
            selectedConcept?.id === node.id && "bg-accent"
          )}
          style={{ paddingLeft: `${level * 24 + 8}px` }}
          onClick={() => fetchConceptDetails(node.id)}
        >
          {hasChildren && (
            <button 
              className="p-0.5 hover:bg-background rounded"
              onClick={(e) => {
                e.stopPropagation()
                toggleNode(node.id)
              }}
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-5" />}
          
          <Tag className="w-4 h-4 text-muted-foreground" />
          
          <div className="flex-1 flex items-center gap-2">
            <span className="font-medium">{node.display_name}</span>
            <span className="text-xs text-muted-foreground">({node.tag})</span>
            {node.descendant_count > 0 && (
              <Badge variant="secondary" className="text-xs">
                {node.descendant_count} descendants
              </Badge>
            )}
            {node.synonyms.length > 0 && (
              <div className="flex gap-1">
                {node.synonyms.slice(0, 3).map(s => (
                  <Badge key={s} variant="outline" className="text-xs">
                    {s}
                  </Badge>
                ))}
                {node.synonyms.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{node.synonyms.length - 3}
                  </Badge>
                )}
              </div>
            )}
          </div>
        </div>
        
        {isExpanded && hasChildren && (
          <div>
            {node.children!.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  const rebuildMappings = async () => {
    setActionLoading(true)
    try {
      await axios.post('http://localhost:8000/api/ontology/rebuild-mappings')
      setSuccessMessage('Tag mappings rebuilt successfully!')
    } catch (error) {
      console.error('Error rebuilding mappings:', error)
      setErrorMessage('Failed to rebuild mappings')
    } finally {
      setActionLoading(false)
    }
  }

  const importExistingTags = async () => {
    setActionLoading(true)
    try {
      const response = await axios.post('http://localhost:8000/api/ontology/import-existing-tags')
      setSuccessMessage(`Imported ${response.data.imported} tags, skipped ${response.data.skipped}`)
      fetchOntologyTree()
    } catch (error) {
      console.error('Error importing tags:', error)
      setErrorMessage('Failed to import existing tags')
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
    <div className="max-w-full mx-auto p-6 space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-2xl flex items-center gap-2">
                <FolderTree className="w-6 h-6" />
                Tag Ontology Manager
              </CardTitle>
              <CardDescription>
                Organize and manage your tag hierarchy with AI assistance
              </CardDescription>
            </div>
            <div className="flex gap-2">
              <Dialog open={showReorganizer} onOpenChange={setShowReorganizer}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4" />
                    Gemini Reorganizer
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
                  <DialogHeader>
                    <DialogTitle>Tag Reorganizer - Gemini 2.5 Pro</DialogTitle>
                    <DialogDescription>
                      Use AI to reorganize and optimize your tag hierarchy
                    </DialogDescription>
                  </DialogHeader>
                  <TagReorganizer />
                </DialogContent>
              </Dialog>

              <Dialog open={showAI} onOpenChange={setShowAI}>
                <DialogTrigger asChild>
                  <Button variant="outline" className="flex items-center gap-2">
                    <Bot className="w-4 h-4" />
                    AI Assistant
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-4xl max-h-[80vh] overflow-auto">
                  <DialogHeader>
                    <DialogTitle>AI Ontology Suggestions</DialogTitle>
                    <DialogDescription>
                      Get AI-powered suggestions for improving your tag hierarchy
                    </DialogDescription>
                  </DialogHeader>
                  <OntologyAISuggestions 
                    currentTree={tree}
                    onApplySuggestion={fetchOntologyTree}
                  />
                </DialogContent>
              </Dialog>

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

              <Button 
                variant="outline" 
                onClick={importExistingTags}
                disabled={actionLoading}
              >
                {actionLoading ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Upload className="w-4 h-4 mr-2" />
                )}
                Import Tags
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
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-lg">Tag Hierarchy</CardTitle>
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tags..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-8"
              />
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[600px] px-4 pb-4">
              {tree.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Tag className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p>No tags in ontology</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="mt-2"
                    onClick={importExistingTags}
                  >
                    Import Existing Tags
                  </Button>
                </div>
              ) : (
                tree.map(node => renderTreeNode(node))
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Details and Actions */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-lg">
              {selectedConcept ? 'Concept Details' : 'Create New Concept'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="details" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="details">Details</TabsTrigger>
                <TabsTrigger value="synonyms">Synonyms</TabsTrigger>
                <TabsTrigger value="create">Create New</TabsTrigger>
              </TabsList>

              <TabsContent value="details" className="space-y-4">
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
                                onClick={updateConcept}
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
                                  setEditMode(false)
                                  fetchConceptDetails(selectedConcept.id)
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
                                onClick={() => setEditMode(true)}
                              >
                                <Edit2 className="w-4 h-4" />
                              </Button>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                onClick={() => deleteConcept(selectedConcept.id)}
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
                          <div>
                            <Label>Tag ID</Label>
                            <Input value={selectedConcept.tag} disabled />
                          </div>

                          <div>
                            <Label>Display Name</Label>
                            <Input 
                              value={selectedConcept.display_name}
                              onChange={(e) => setSelectedConcept({
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
                              onChange={(e) => setSelectedConcept({
                                ...selectedConcept,
                                description: e.target.value
                              })}
                              disabled={!editMode}
                              rows={3}
                            />
                          </div>
                        </div>

                        <Separator />

                        {/* Hierarchy Information */}
                        <div className="space-y-4">
                          <h4 className="font-semibold text-sm">Hierarchy</h4>
                          
                          {/* Parent Concept */}
                          {selectedConcept.parent && (
                            <div>
                              <Label className="text-xs text-muted-foreground">Parent Concept</Label>
                              <div 
                                className="mt-1 p-2 rounded-md bg-muted hover:bg-accent cursor-pointer transition-colors flex items-center gap-2"
                                onClick={() => fetchConceptDetails(selectedConcept.parent!.id)}
                              >
                                <ChevronRight className="w-4 h-4" />
                                <Tag className="w-4 h-4 text-muted-foreground" />
                                <span className="font-medium">{selectedConcept.parent.display_name}</span>
                                <span className="text-xs text-muted-foreground">({selectedConcept.parent.tag})</span>
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
                                      onClick={() => fetchConceptDetails(child.id)}
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
                              <Input value={selectedConcept.level} disabled className="mt-1" />
                            </div>
                            <div>
                              <Label className="text-xs text-muted-foreground">Path</Label>
                              <Input value={selectedConcept.path} disabled className="mt-1" />
                            </div>
                          </div>
                        </div>

                        <Separator />

                        {/* Usage Statistics */}
                        <div className="space-y-4">
                          <h4 className="font-semibold text-sm">Usage Statistics</h4>
                          
                          {selectedConcept.usage_stats ? (
                            <div className="grid grid-cols-3 gap-4">
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
              </TabsContent>

              <TabsContent value="synonyms" className="space-y-4">
                {selectedConcept ? (
                  <>
                    <div className="flex gap-2">
                      <Input 
                        placeholder="Enter synonym tag..."
                        value={newSynonym}
                        onChange={(e) => setNewSynonym(e.target.value)}
                        onKeyPress={(e) => {
                          if (e.key === 'Enter') addSynonym()
                        }}
                      />
                      <Button 
                        onClick={addSynonym}
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
                ) : (
                  <div className="text-center py-12 text-muted-foreground">
                    <Link2 className="w-12 h-12 mx-auto mb-2 opacity-50" />
                    <p>Select a concept to manage synonyms</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="create" className="space-y-4">
                <div className="grid gap-4">
                  <div>
                    <Label>Tag ID</Label>
                    <Input 
                      placeholder="e.g., machine-learning"
                      value={newConceptForm.tag}
                      onChange={(e) => setNewConceptForm({
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
                      onChange={(e) => setNewConceptForm({
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
                      onChange={(e) => setNewConceptForm({
                        ...newConceptForm,
                        description: e.target.value
                      })}
                      rows={3}
                    />
                  </div>

                  <div>
                    <Label>Parent Concept (Optional)</Label>
                    <Input 
                      type="number"
                      placeholder="Parent concept ID"
                      value={newConceptForm.parent_id || ''}
                      onChange={(e) => setNewConceptForm({
                        ...newConceptForm,
                        parent_id: e.target.value ? parseInt(e.target.value) : null
                      })}
                    />
                  </div>

                  <Button 
                    onClick={createConcept}
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
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}