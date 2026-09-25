import { useState, useEffect } from 'react'
import http from '@/services/http'
import type { ConceptTreeNode } from './ConceptTreePanel'
import type { Concept, UnorganizedConcept, OrganizationSuggestion, OntologyStats } from './types'

export default function useConceptManagement() {
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
  const [_importDialogOpen, setImportDialogOpen] = useState(false)
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
      const response = await http.get('/api/ontology/tree')
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
      const response = await http.get('/api/ontology/stats')
      setStats(response.data)
    } catch (err) {
      console.error('Failed to load stats:', err)
    }
  }

  const fetchUnorganizedConcepts = async () => {
    setLoading(true)
    try {
      const response = await http.get('/api/concepts/organization/unorganized?limit=50')
      setUnorganizedConcepts(response.data.concepts || [])
    } catch (err) {
      console.error('Failed to load unorganized concepts:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchOrganizationStats = async () => {
    try {
      const response = await http.get('/api/concepts/organization/stats')
      setOrganizationStats(response.data.stats)
    } catch (err) {
      console.error('Failed to load organization stats:', err)
    }
  }

  const fetchConceptDetails = async (conceptId: string) => {
    try {
      const response = await http.get(`/api/ontology/concept/${conceptId}`)
      setSelectedConcept(response.data)
    } catch (err) {
      console.error('Failed to load concept details:', err)
    }
  }

  const fetchOrganizationSuggestion = async (conceptId: string) => {
    setLoading(true)
    try {
      const response = await http.post('/api/concepts/organization/organize', {
        concept_id: conceptId,
        auto_apply: false
      })
      if (response.data.success) {
        setOrganizationSuggestion({
          is_alias: response.data.is_alias,
          alias_of: response.data.alias_of,
          parent_concepts: response.data.parent_concepts,
          entity_type: response.data.entity_type,
          description: response.data.description,
          reasoning: response.data.reasoning
        })
      } else {
        setError(response.data.error || 'Failed to get organization suggestion')
      }
    } catch (err: any) {
      console.error('Failed to get organization suggestion:', err)
      setError(err.response?.data?.detail || 'Failed to get organization suggestion')
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
      await http.post('/api/ontology/concepts', formData)
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
      await http.put(`/api/ontology/concepts/${selectedConcept.id}`, formData)
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
      await http.delete(`/api/ontology/concepts/${selectedConcept.id}`)
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
      await http.post(
        `/api/concepts/organization/apply-organization/${selectedUnorganized._id}`,
        organizationSuggestion
      )
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
      const response = await http.get('/api/ontology/export', {
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

  const handleBatchReorganize = async (limit: number, autoApply: boolean) => {
    setLoading(true)
    try {
      const response = await http.post('/api/concepts/organization/organize-batch', {
        limit,
        auto_apply: autoApply
      })
      setSuccess(
        response.data.message ||
        `Successfully ${autoApply ? 'organized' : 'processed'} ${response.data.processed ?? 0} concepts`
      )
      fetchUnorganizedConcepts()
      fetchOrganizationStats()
      if (autoApply) fetchTreeData()
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to batch reorganize')
    } finally {
      setLoading(false)
    }
  }

  const openEditDialog = () => {
    if (!selectedConcept) return
    const { children: _children, ...conceptData } = selectedConcept
    setFormData(conceptData)
    setEditDialogOpen(true)
  }

  const openCreateChildDialog = () => {
    if (!selectedConcept) return
    setFormData({ parent_id: selectedConcept.id })
    setCreateDialogOpen(true)
  }

  return {
    // Browse & Edit state
    treeData,
    selectedConcept,
    searchQuery,
    setSearchQuery,
    expandedNodes,
    toggleNode,
    handleConceptSelect,

    // Organize state
    unorganizedConcepts,
    selectedUnorganized,
    setSelectedUnorganized,
    organizationSuggestion,
    setOrganizationSuggestion,
    organizationStats,

    // General state
    loading,
    error,
    setError,
    success,
    setSuccess,
    stats,
    activeTab,
    setActiveTab,

    // Dialog state
    editDialogOpen,
    setEditDialogOpen,
    createDialogOpen,
    setCreateDialogOpen,
    deleteDialogOpen,
    setDeleteDialogOpen,
    setImportDialogOpen,
    reorganizerDialogOpen,
    setReorganizerDialogOpen,

    // Form state
    formData,
    setFormData,

    // Actions
    fetchTreeData,
    fetchOrganizationSuggestion,
    handleCreateConcept,
    handleUpdateConcept,
    handleDeleteConcept,
    handleApplyOrganization,
    handleExportOntology,
    handleBatchReorganize,
    openEditDialog,
    openCreateChildDialog,
  }
}
