import React, { useState, useEffect, useMemo } from 'react'
import axios from 'axios'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Textarea } from "@/components/ui/textarea"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
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
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
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
  AlertCircle,
  CheckCircle,
  Hash,
  Twitter,
  FileText,
  BookOpen,
  GitBranch,
  Sparkles,
  Loader2,
  MoreVertical,
  Brain
} from 'lucide-react'
import TagReorganizerAsync from './TagReorganizerAsync'

// Types
interface Concept {
  id: string
  slug: string
  name: string
  display_name: string
  description?: string
  parent_id?: string | null
  parents?: string[]
  children?: string[]
  entity_type?: string
  icon?: string
  color?: string
  created_at?: string
  created_by?: string
  auto_generated?: boolean
  verified?: boolean
  quality_score?: number
}

interface ConceptTreeNode {
  // Base concept properties (not extended to avoid children type conflict)
  id: string
  slug: string
  name: string
  display_name: string
  description?: string
  parent_id?: string | null
  parents?: string[]
  entity_type?: string
  icon?: string
  color?: string
  created_at?: string
  created_by?: string
  auto_generated?: boolean
  verified?: boolean
  quality_score?: number

  // Tree-specific properties
  children?: ConceptTreeNode[]
  children_details?: ConceptTreeNode[]
  expanded?: boolean
  usage_stats?: {
    tweet_count: number
    article_count: number
    paper_count: number
    total_count: number
  }
}

interface UnorganizedConcept {
  _id: string
  display_name: string
  slug: string
  description?: string
  usage_count: number
  created_at: string
}

interface OrganizationSuggestion {
  is_alias: boolean
  parent_concept?: string
  parent_concept_name?: string
  confidence: number
  reasoning: string
}

interface OntologyStats {
  concepts: {
    total: number
    active: number
    root: number
    with_children: number
  }
  aliases: {
    total: number
    unique_concepts: number
  }
  instances: {
    total: number
    tweets: number
    papers: number
    articles: number
    resolved: number
    orphaned: number
  }
}

export default function ConceptManagementCenter() {
  // State for Browse & Edit tab
  const [treeData, setTreeData] = useState<ConceptTreeNode[]>([])
  const [selectedConcept, setSelectedConcept] = useState<ConceptTreeNode | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  
  // State for Organize New tab
  const [unorganizedConcepts, setUnorganizedConcepts] = useState<UnorganizedConcept[]>([])
  const [selectedUnorganized, setSelectedUnorganized] = useState<UnorganizedConcept | null>(null)
  const [organizationSuggestion, setOrganizationSuggestion] = useState<OrganizationSuggestion | null>(null)
  const [organizationStats, setOrganizationStats] = useState<any>(null)
  
  // General state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [stats, setStats] = useState<OntologyStats | null>(null)
  const [activeTab, setActiveTab] = useState('browse')
  
  // Dialogs
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [importDialogOpen, setImportDialogOpen] = useState(false)
  const [reorganizerDialogOpen, setReorganizerDialogOpen] = useState(false)
  
  // Form state
  const [formData, setFormData] = useState<Partial<Concept>>({})

  // Load initial data
  useEffect(() => {
    fetchTreeData()
    fetchStats()
    if (activeTab === 'organize') {
      fetchUnorganizedConcepts()
      fetchOrganizationStats()
    }
  }, [activeTab])

  // Fetch functions
  const fetchTreeData = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/ontology/tree')
      setTreeData(response.data)
    } catch (err: any) {
      setError('Failed to load concept hierarchy')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await axios.get('/api/ontology/stats')
      setStats(response.data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const fetchUnorganizedConcepts = async () => {
    setLoading(true)
    try {
      const response = await axios.get('/api/concepts/unorganized')
      setUnorganizedConcepts(response.data)
    } catch (err) {
      console.error('Failed to load unorganized concepts:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchOrganizationStats = async () => {
    try {
      const response = await axios.get('/api/concepts/organization-stats')
      setOrganizationStats(response.data)
    } catch (err) {
      console.error('Failed to load organization stats:', err)
    }
  }

  const fetchConceptDetails = async (conceptId: string) => {
    try {
      const response = await axios.get(`/api/ontology/concept/${conceptId}`)
      setSelectedConcept(response.data)
    } catch (err) {
      console.error('Failed to load concept details:', err)
    }
  }

  const fetchOrganizationSuggestion = async (conceptId: string) => {
    setLoading(true)
    try {
      const response = await axios.post(`/api/concepts/suggest-organization/${conceptId}`)
      setOrganizationSuggestion(response.data)
    } catch (err) {
      console.error('Failed to get organization suggestion:', err)
    } finally {
      setLoading(false)
    }
  }

  // Tree navigation
  const toggleNode = (nodeId: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId)
    } else {
      newExpanded.add(nodeId)
    }
    setExpandedNodes(newExpanded)
  }

  const handleConceptSelect = (concept: ConceptTreeNode) => {
    setSelectedConcept(concept)
    fetchConceptDetails(concept.id)
  }

  // CRUD operations
  const handleCreateConcept = async () => {
    try {
      await axios.post('/api/ontology/concepts', formData)
      setSuccess('Concept created successfully')
      setCreateDialogOpen(false)
      fetchTreeData()
      fetchStats()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create concept')
    }
  }

  const handleUpdateConcept = async () => {
    if (!selectedConcept) return
    try {
      await axios.put(`/api/ontology/concepts/${selectedConcept.id}`, formData)
      setSuccess('Concept updated successfully')
      setEditDialogOpen(false)
      fetchTreeData()
      fetchConceptDetails(selectedConcept.id)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to update concept')
    }
  }

  const handleDeleteConcept = async () => {
    if (!selectedConcept) return
    try {
      await axios.delete(`/api/ontology/concepts/${selectedConcept.id}`)
      setSuccess('Concept deleted successfully')
      setDeleteDialogOpen(false)
      setSelectedConcept(null)
      fetchTreeData()
      fetchStats()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to delete concept')
    }
  }

  const handleApplyOrganization = async () => {
    if (!selectedUnorganized || !organizationSuggestion) return
    
    try {
      await axios.post(`/api/concepts/apply-organization/${selectedUnorganized._id}`, {
        suggestion: organizationSuggestion
      })
      setSuccess('Concept organized successfully')
      setSelectedUnorganized(null)
      setOrganizationSuggestion(null)
      fetchUnorganizedConcepts()
      fetchOrganizationStats()
      fetchTreeData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to organize concept')
    }
  }

  const handleExportOntology = async () => {
    try {
      const response = await axios.get('/api/ontology/export', {
        responseType: 'blob'
      })
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `ontology-${new Date().toISOString().split('T')[0]}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
      setSuccess('Ontology exported successfully')
    } catch (err) {
      setError('Failed to export ontology')
    }
  }

  // Tree rendering
  const renderTreeNode = (node: ConceptTreeNode, level: number = 0) => {
    const isExpanded = expandedNodes.has(node.id)
    const children = node.children || node.children_details || []  // Support both field names
    const hasChildren = children.length > 0
    const isSelected = selectedConcept?.id === node.id

    return (
      <div key={node.id}>
        <div
          className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer hover:bg-accent ${
            isSelected ? 'bg-accent' : ''
          }`}
          style={{ paddingLeft: `${level * 20 + 8}px` }}
          onClick={() => handleConceptSelect(node)}
        >
          {hasChildren && (
            <button
              className="p-0.5"
              onClick={(e) => {
                e.stopPropagation()
                toggleNode(node.id)
              }}
            >
              {isExpanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-4" />}
          
          {node.entity_type === 'person' && <span>👤</span>}
          {node.entity_type === 'organisation' && <span>🏢</span>}
          {node.entity_type === 'location' && <span>📍</span>}
          
          <span className="text-sm font-medium">{node.display_name}</span>
          
          {node.usage_stats && node.usage_stats.total_count > 0 && (
            <Badge variant="outline" className="ml-auto text-xs">
              {node.usage_stats.total_count}
            </Badge>
          )}
        </div>
        
        {isExpanded && hasChildren && (
          <div>
            {children.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  // Filter tree based on search
  const filteredTree = useMemo(() => {
    if (!searchQuery) return treeData
    
    const filterNodes = (nodes: ConceptTreeNode[]): ConceptTreeNode[] => {
      return nodes.reduce((acc: ConceptTreeNode[], node) => {
        const matchesSearch = node.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                             node.slug.toLowerCase().includes(searchQuery.toLowerCase())
        
        const children = node.children || node.children_details || []
        const filteredChildren = children.length > 0 ? filterNodes(children) : []
        
        if (matchesSearch || filteredChildren.length > 0) {
          acc.push({
            ...node,
            children: filteredChildren,  // Use children field
            children_details: filteredChildren,  // Keep both for compatibility
            expanded: true
          })
        }
        
        return acc
      }, [])
    }
    
    return filterNodes(treeData)
  }, [treeData, searchQuery])

  return (
    <div className="space-y-4">
      {/* Header with stats */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <GitBranch className="h-5 w-5" />
                Concept Management Center
              </CardTitle>
              <CardDescription>
                Manage concept hierarchy and organize new concepts
              </CardDescription>
            </div>
            {stats && (
              <div className="flex gap-4 text-sm">
                <div>
                  <span className="font-medium">{stats.concepts.total}</span>
                  <span className="text-muted-foreground"> concepts</span>
                </div>
                <div>
                  <span className="font-medium">{stats.aliases.total}</span>
                  <span className="text-muted-foreground"> aliases</span>
                </div>
                <div>
                  <span className="font-medium">{stats.instances.total}</span>
                  <span className="text-muted-foreground"> instances</span>
                </div>
              </div>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Main content tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="browse">Browse & Edit</TabsTrigger>
          <TabsTrigger value="organize">Organize New</TabsTrigger>
          <TabsTrigger value="import-export">Import/Export</TabsTrigger>
        </TabsList>

        {/* Browse & Edit Tab */}
        <TabsContent value="browse" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Tree view */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Hierarchy</CardTitle>
                  <Button size="sm" variant="ghost" onClick={fetchTreeData}>
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
                <div className="relative">
                  <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search concepts..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-8"
                  />
                </div>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[500px]">
                  {loading ? (
                    <div className="flex items-center justify-center h-full">
                      <Loader2 className="h-6 w-6 animate-spin" />
                    </div>
                  ) : (
                    <div className="space-y-1">
                      {filteredTree.map(node => renderTreeNode(node))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Details and actions */}
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
                        onClick={() => {
                          setFormData(selectedConcept)
                          setEditDialogOpen(true)
                        }}
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
                          <DropdownMenuItem
                            onClick={() => {
                              setFormData({ parent_id: selectedConcept.id })
                              setCreateDialogOpen(true)
                            }}
                          >
                            <Plus className="h-4 w-4 mr-2" />
                            Add Child
                          </DropdownMenuItem>
                          <DropdownMenuItem
                            className="text-destructive"
                            onClick={() => setDeleteDialogOpen(true)}
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
          </div>
        </TabsContent>

        {/* Organize New Tab */}
        <TabsContent value="organize" className="space-y-4">
          {organizationStats && (
            <div className="grid grid-cols-4 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Unorganized</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{organizationStats.unorganized_count}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Organized Today</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{organizationStats.organized_today}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">This Week</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{organizationStats.organized_this_week}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium">Total Organized</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{organizationStats.total_organized}</div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Batch Organization Actions */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg">Batch Organization</CardTitle>
                  <CardDescription>
                    Use AI to automatically organize multiple concepts at once
                  </CardDescription>
                </div>
                <Button
                  variant="default"
                  size="sm"
                  onClick={() => setReorganizerDialogOpen(true)}
                  className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
                >
                  <Brain className="h-4 w-4 mr-2" />
                  Advanced AI Reorganization
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Button
                  onClick={async () => {
                    setLoading(true)
                    try {
                      const response = await axios.post('/api/concepts/batch-reorganize', {
                        limit: 10,
                        auto_apply: false
                      })
                      setSuccess(`Successfully processed ${response.data.success_count} concepts`)
                      fetchUnorganizedConcepts()
                      fetchOrganizationStats()
                    } catch (err: any) {
                      setError(err.response?.data?.detail || 'Failed to batch reorganize')
                    } finally {
                      setLoading(false)
                    }
                  }}
                  disabled={loading}
                >
                  {loading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : (
                    <>
                      <Sparkles className="h-4 w-4 mr-2" />
                      Organize 10 Concepts
                    </>
                  )}
                </Button>
                
                <Button
                  variant="outline"
                  onClick={async () => {
                    if (!confirm('This will automatically apply AI suggestions to 10 concepts. Continue?')) return
                    setLoading(true)
                    try {
                      const response = await axios.post('/api/concepts/batch-reorganize', {
                        limit: 10,
                        auto_apply: true
                      })
                      setSuccess(`Successfully organized ${response.data.success_count} concepts`)
                      fetchUnorganizedConcepts()
                      fetchOrganizationStats()
                      fetchTreeData()
                    } catch (err: any) {
                      setError(err.response?.data?.detail || 'Failed to batch reorganize')
                    } finally {
                      setLoading(false)
                    }
                  }}
                  disabled={loading}
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Organize & Apply (10)
                </Button>

                <Button
                  variant="destructive"
                  onClick={async () => {
                    if (!confirm('This will process ALL unorganized concepts. This may take a while. Continue?')) return
                    setLoading(true)
                    try {
                      const response = await axios.post('/api/concepts/batch-reorganize', {
                        limit: 50,
                        auto_apply: true
                      })
                      setSuccess(`Successfully organized ${response.data.success_count} concepts`)
                      fetchUnorganizedConcepts()
                      fetchOrganizationStats()
                      fetchTreeData()
                    } catch (err: any) {
                      setError(err.response?.data?.detail || 'Failed to batch reorganize')
                    } finally {
                      setLoading(false)
                    }
                  }}
                  disabled={loading}
                >
                  <AlertCircle className="h-4 w-4 mr-2" />
                  Organize All (Max 50)
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Unorganized concepts list */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-lg">Unorganized Concepts</CardTitle>
                <CardDescription>
                  Concepts that need to be organized into the hierarchy
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  {unorganizedConcepts.length === 0 ? (
                    <div className="text-center text-muted-foreground py-8">
                      <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                      <p>All concepts are organized!</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {unorganizedConcepts.map(concept => (
                        <div
                          key={concept._id}
                          className={`p-3 rounded-lg border cursor-pointer hover:bg-accent ${
                            selectedUnorganized?._id === concept._id ? 'bg-accent' : ''
                          }`}
                          onClick={() => {
                            setSelectedUnorganized(concept)
                            setOrganizationSuggestion(null)
                          }}
                        >
                          <div className="font-medium">{concept.display_name}</div>
                          <div className="text-sm text-muted-foreground">
                            Usage: {concept.usage_count}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>

            {/* Organization suggestion */}
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle className="text-lg">
                  {selectedUnorganized ? 'Organization Suggestion' : 'Select a concept'}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedUnorganized ? (
                  <div className="space-y-4">
                    <div>
                      <Label>Selected Concept</Label>
                      <p className="text-lg font-medium">{selectedUnorganized.display_name}</p>
                      {selectedUnorganized.description && (
                        <p className="text-sm text-muted-foreground mt-1">
                          {selectedUnorganized.description}
                        </p>
                      )}
                    </div>

                    {!organizationSuggestion && (
                      <Button
                        onClick={() => fetchOrganizationSuggestion(selectedUnorganized._id)}
                        disabled={loading}
                      >
                        {loading ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Getting AI Suggestion...
                          </>
                        ) : (
                          <>
                            <Sparkles className="h-4 w-4 mr-2" />
                            Get AI Suggestion
                          </>
                        )}
                      </Button>
                    )}

                    {organizationSuggestion && (
                      <div className="space-y-4">
                        <Alert>
                          <AlertCircle className="h-4 w-4" />
                          <AlertTitle>AI Suggestion</AlertTitle>
                          <AlertDescription className="mt-2">
                            {organizationSuggestion.is_alias ? (
                              <div>
                                <p>This appears to be an alias of:</p>
                                <p className="font-medium mt-1">
                                  {organizationSuggestion.parent_concept_name}
                                </p>
                              </div>
                            ) : (
                              <div>
                                <p>Suggested parent concept:</p>
                                <p className="font-medium mt-1">
                                  {organizationSuggestion.parent_concept_name || 'Root level'}
                                </p>
                              </div>
                            )}
                            <p className="mt-2 text-sm">{organizationSuggestion.reasoning}</p>
                            <div className="mt-2">
                              <Badge variant="outline">
                                Confidence: {(organizationSuggestion.confidence * 100).toFixed(0)}%
                              </Badge>
                            </div>
                          </AlertDescription>
                        </Alert>

                        <div className="flex gap-2">
                          <Button onClick={handleApplyOrganization} disabled={loading}>
                            <CheckCircle className="h-4 w-4 mr-2" />
                            Apply Suggestion
                          </Button>
                          <Button
                            variant="outline"
                            onClick={() => setOrganizationSuggestion(null)}
                          >
                            <X className="h-4 w-4 mr-2" />
                            Reject
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center text-muted-foreground py-8">
                    Select an unorganized concept to get AI suggestions
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Import/Export Tab */}
        <TabsContent value="import-export" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader>
                <CardTitle>Export Ontology</CardTitle>
                <CardDescription>
                  Download the complete concept hierarchy and metadata
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Export Options</Label>
                  <div className="space-y-2">
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" defaultChecked />
                      <span className="text-sm">Include concept hierarchy</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" defaultChecked />
                      <span className="text-sm">Include aliases</span>
                    </label>
                    <label className="flex items-center space-x-2">
                      <input type="checkbox" />
                      <span className="text-sm">Include usage statistics</span>
                    </label>
                  </div>
                </div>
                <Button onClick={handleExportOntology} className="w-full">
                  <Download className="h-4 w-4 mr-2" />
                  Export to JSON
                </Button>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Import Ontology</CardTitle>
                <CardDescription>
                  Upload a JSON file to import concepts and hierarchy
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Alert>
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Warning</AlertTitle>
                  <AlertDescription>
                    Importing will merge with existing concepts. Duplicates will be skipped.
                  </AlertDescription>
                </Alert>
                <Button
                  variant="outline"
                  className="w-full"
                  onClick={() => setImportDialogOpen(true)}
                >
                  <Upload className="h-4 w-4 mr-2" />
                  Select File to Import
                </Button>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Maintenance Tools</CardTitle>
              <CardDescription>
                Administrative tools for managing the concept system
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Button variant="outline">
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Rebuild Index
                </Button>
                <Button variant="outline">
                  <Hash className="h-4 w-4 mr-2" />
                  Recalculate Stats
                </Button>
                <Button variant="outline">
                  <AlertCircle className="h-4 w-4 mr-2" />
                  Find Orphans
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Alerts */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      {success && (
        <Alert className="bg-green-50 border-green-200">
          <CheckCircle className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800">{success}</AlertDescription>
        </Alert>
      )}

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
              <Select
                value={formData.entity_type || 'concept'}
                onValueChange={(value) => setFormData({ ...formData, entity_type: value })}
              >
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
              <Select
                value={formData.entity_type || 'concept'}
                onValueChange={(value) => setFormData({ ...formData, entity_type: value })}
              >
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
            <TagReorganizerAsync />
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}