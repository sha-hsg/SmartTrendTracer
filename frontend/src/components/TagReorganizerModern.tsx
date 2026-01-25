import { useState, useEffect } from 'react'
import axios from 'axios'
import { Button } from './ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Alert, AlertDescription } from './ui/alert'
import { Badge } from './ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs'
import { ScrollArea } from './ui/scroll-area'
import { Progress } from './ui/progress'
import { 
  ChevronRight, 
  ChevronDown, 
  Sparkles, 
  AlertCircle, 
  CheckCircle2,
  XCircle,
  Loader2,
  GitMerge,
  Archive,
  Eye,
  EyeOff,
  RefreshCw,
  Folder,
  FolderOpen,
  Tag,
  Info
} from 'lucide-react'

interface TagNode {
  // New structure fields
  id: string  // Unique ID like "c_0001"
  slug: string  // Normalized name like "large_language_models"
  display_name: string  // Human-readable name
  description: string | null
  status: string  // active, deprecated, etc.
  parents: string[]  // Now plural, supports poly-hierarchy
  children: string[]  // Child concept IDs
  usage_count: number
  icon?: string  // Emoji icon
  color?: string  // Color code for UI
  
  // Legacy fields for backwards compatibility
  name?: string  // Will be set to slug for compatibility
  parent?: string | null  // Single parent for backwards compatibility
  level?: number  // Hierarchy level
  synonyms?: string[]  // Now handled via aliases
}

interface Proposal {
  proposal_id: string
  version: string
  created_at: string
  model_used: string
  total_tags: number
  confidence_score: number
  reasoning: string
  statistics: any
  root_categories: string[]
  hierarchy: { [key: string]: TagNode }
  merge_proposals: any[]
  deprecated_tags: string[]
  new_tags_suggested: any[]
}

export default function TagReorganizerModern() {
  const [currentStructure, setCurrentStructure] = useState<any>(null)
  const [proposal, setProposal] = useState<Proposal | null>(null)
  const [loading, setLoading] = useState(false)
  const [selectedNode, setSelectedNode] = useState<string | null>(null)
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())
  const [approvedChanges, setApprovedChanges] = useState<{ [key: string]: boolean }>({})
  const [viewMode, setViewMode] = useState<'current' | 'proposed'>('current')
  const [error, setError] = useState<string | null>(null)
  const [applyingChanges, setApplyingChanges] = useState(false)
  const [debugMode, setDebugMode] = useState(false)
  const [debugInfo, setDebugInfo] = useState<any>({})
  const [conceptStats, setConceptStats] = useState<any>(null)
  const [configTest, setConfigTest] = useState<any>(null)

  useEffect(() => {
    loadCurrentStructure()
    if (debugMode) {
      loadDebugInfo()
    }
  }, [debugMode])

  const loadCurrentStructure = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tags/reorganize/current-structure')
      setCurrentStructure(response.data)
    } catch (error) {
      console.error('Failed to load current structure:', error)
      setError('Failed to load current tag structure')
    }
  }

  const loadDebugInfo = async () => {
    try {
      // Load concept statistics
      const statsResponse = await axios.get('http://localhost:8000/api/tags/reorganize/debug/current-concepts')
      setConceptStats(statsResponse.data)
      console.log('[DEBUG] Concept stats:', statsResponse.data)

      // Test GPT-5 configuration
      const configResponse = await axios.get('http://localhost:8000/api/tags/reorganize/debug/test-gpt5-config')
      setConfigTest(configResponse.data)
      console.log('[DEBUG] GPT-5 config:', configResponse.data)
    } catch (error) {
      console.error('[DEBUG] Failed to load debug info:', error)
      setDebugInfo({ error: 'Failed to load debug information' })
    }
  }

  const generateProposal = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.post('http://localhost:8000/api/tags/reorganize/generate-proposal', {
        include_context: true,
        max_samples_per_tag: 3,
        confidence_threshold: 0.7
      })
      
      setProposal(response.data)
      setViewMode('proposed')
      
      // Initialize all changes as approved by default
      const initialApproval: { [key: string]: boolean } = {}
      Object.keys(response.data.hierarchy).forEach(tag => {
        initialApproval[tag] = true
      })
      setApprovedChanges(initialApproval)
      
    } catch (error: any) {
      console.error('Failed to generate proposal:', error)
      setError(error.response?.data?.detail || 'Failed to generate reorganization proposal')
    } finally {
      setLoading(false)
    }
  }

  const toggleNode = (nodeName: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(nodeName)) {
      newExpanded.delete(nodeName)
    } else {
      newExpanded.add(nodeName)
    }
    setExpandedNodes(newExpanded)
  }

  const toggleApproval = (tagName: string) => {
    setApprovedChanges(prev => ({
      ...prev,
      [tagName]: !prev[tagName]
    }))
  }

  const applyApprovedChanges = async () => {
    if (!proposal) return
    
    setApplyingChanges(true)
    setError(null)
    
    try {
      const approvedHierarchy: { [key: string]: TagNode } = {}
      Object.entries(proposal.hierarchy).forEach(([key, node]) => {
        if (approvedChanges[key]) {
          approvedHierarchy[key] = node
        }
      })
      
      await axios.post(`http://localhost:8000/api/tags/reorganize/proposal/${proposal.proposal_id}/apply`, {
        proposal_id: proposal.proposal_id,
        approved_changes: approvedChanges
      })
      
      // Reload current structure
      await loadCurrentStructure()
      setProposal(null)
      setViewMode('current')
      setError(null)
    } catch (error: any) {
      console.error('Failed to apply changes:', error)
      setError(error.response?.data?.detail || 'Failed to apply reorganization')
    } finally {
      setApplyingChanges(false)
    }
  }

  const renderTagNode = (node: TagNode, hierarchy: { [key: string]: TagNode }) => {
    const nodeId = node.id || node.name || node.slug
    const isExpanded = expandedNodes.has(nodeId)
    const hasChildren = node.children && node.children.length > 0
    const isSelected = selectedNode === nodeId
    const isApproved = approvedChanges[nodeId] !== false
    
    return (
      <div key={nodeId} className="select-none">
        <div
          className={`
            flex items-center gap-2 px-3 py-2 rounded-lg cursor-pointer
            transition-all duration-200
            ${isSelected ? 'bg-blue-100 dark:bg-blue-900/30' : 'hover:bg-gray-100 dark:hover:bg-gray-800'}
            ${!isApproved ? 'opacity-50 line-through' : ''}
          `}
          style={{ paddingLeft: `${(node.level || 0) * 20 + 12}px` }}
          onClick={() => setSelectedNode(nodeId)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleNode(nodeId)
              }}
              className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            >
              {isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
          )}
          
          {!hasChildren && <div className="w-5" />}
          
          {node.icon ? (
            <span className="text-lg">{node.icon}</span>
          ) : node.level === 0 ? (
            isExpanded ? <FolderOpen className="h-4 w-4 text-blue-500" /> : <Folder className="h-4 w-4 text-blue-500" />
          ) : (
            <Tag className="h-4 w-4 text-gray-500" />
          )}
          
          <span className="font-medium text-sm">{node.display_name || node.name || node.slug}</span>
          
          <Badge variant="secondary" className="ml-auto">
            {node.usage_count || 0}
          </Badge>
          
          {node.synonyms && node.synonyms.length > 0 && (
            <Badge variant="outline" className="ml-1">
              {node.synonyms.length} syn
            </Badge>
          )}
          
          {viewMode === 'proposed' && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                toggleApproval(node.name || node.slug)
              }}
              className="ml-2 p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            >
              {isApproved ? (
                <CheckCircle2 className="h-4 w-4 text-green-500" />
              ) : (
                <XCircle className="h-4 w-4 text-red-500" />
              )}
            </button>
          )}
        </div>
        
        {isExpanded && hasChildren && (
          <div className="ml-2">
            {node.children.map(childName => {
              const childNode = hierarchy[childName]
              if (childNode) {
                return renderTagNode(childNode, hierarchy)
              }
              return null
            })}
          </div>
        )}
      </div>
    )
  }

  const getSelectedNodeDetails = () => {
    if (!selectedNode) return null
    
    const hierarchy = viewMode === 'current' 
      ? currentStructure?.hierarchy 
      : proposal?.hierarchy
      
    return hierarchy?.[selectedNode] || null
  }

  const selectedNodeDetails = getSelectedNodeDetails()

  return (
    <div className="space-y-6">
      {/* Debug Toggle */}
      <div className="flex justify-end">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setDebugMode(!debugMode)}
          className="gap-2"
        >
          {debugMode ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          {debugMode ? 'Hide Debug' : 'Show Debug'}
        </Button>
      </div>

      {/* Debug Panel */}
      {debugMode && (
        <Card className="border-orange-200 bg-orange-50">
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Info className="h-5 w-5 text-orange-600" />
              Debug Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="stats">
              <TabsList>
                <TabsTrigger value="stats">Concept Stats</TabsTrigger>
                <TabsTrigger value="config">GPT-5 Config</TabsTrigger>
                <TabsTrigger value="logs">Process Logs</TabsTrigger>
              </TabsList>
              
              <TabsContent value="stats" className="space-y-4">
                {conceptStats && (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-white p-3 rounded-lg">
                      <p className="text-sm text-gray-600">Total Concepts</p>
                      <p className="text-2xl font-bold">{conceptStats.total_concepts}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <p className="text-sm text-gray-600">Unorganized</p>
                      <p className="text-2xl font-bold text-orange-600">{conceptStats.unorganized}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <p className="text-sm text-gray-600">Auto-generated</p>
                      <p className="text-2xl font-bold">{conceptStats.auto_generated}</p>
                    </div>
                    <div className="bg-white p-3 rounded-lg">
                      <p className="text-sm text-gray-600">Manual</p>
                      <p className="text-2xl font-bold">{conceptStats.manual}</p>
                    </div>
                  </div>
                )}
                
                {conceptStats?.unorganized_samples && conceptStats.unorganized_samples.length > 0 && (
                  <div className="bg-white p-4 rounded-lg">
                    <h4 className="font-medium mb-2">Sample Unorganized Concepts:</h4>
                    <div className="space-y-1">
                      {conceptStats.unorganized_samples.slice(0, 5).map((concept: any) => (
                        <div key={concept.id} className="flex items-center justify-between text-sm">
                          <span>{concept.display_name}</span>
                          <div className="flex items-center gap-2">
                            <Badge variant="outline">{concept.slug}</Badge>
                            <Badge>{concept.count} uses</Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </TabsContent>
              
              <TabsContent value="config" className="space-y-4">
                {configTest && (
                  <div className="space-y-3">
                    <div className="bg-white p-4 rounded-lg">
                      <h4 className="font-medium mb-2">LLM Configuration:</h4>
                      {configTest.llm_config?.found ? (
                        <div className="space-y-1 text-sm">
                          <p>✅ Model: {configTest.llm_config.model}</p>
                          <p>✅ Max Tokens: {configTest.llm_config.max_tokens?.toLocaleString()}</p>
                          <p>✅ Temperature: {configTest.llm_config.temperature}</p>
                        </div>
                      ) : (
                        <p className="text-red-600">❌ GPT-5 configuration not found</p>
                      )}
                    </div>
                    
                    <div className="bg-white p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Environment:</h4>
                      <div className="space-y-1 text-sm">
                        <p>{configTest.environment?.OPENAI_API_KEY ? '✅' : '❌'} OpenAI API Key</p>
                        <p>{configTest.environment?.top_level_json ? '✅' : '❌'} Entity Schema (top_level.json)</p>
                      </div>
                    </div>
                    
                    <div className="bg-white p-4 rounded-lg">
                      <h4 className="font-medium mb-2">Service Test:</h4>
                      {configTest.test_init?.success ? (
                        <p className="text-green-600">✅ GPT-5 Reorganizer initialized successfully</p>
                      ) : (
                        <p className="text-red-600">❌ {configTest.test_init?.error || 'Service initialization failed'}</p>
                      )}
                    </div>
                  </div>
                )}
              </TabsContent>
              
              <TabsContent value="logs" className="space-y-4">
                <div className="bg-white p-4 rounded-lg">
                  <h4 className="font-medium mb-2">Process Logs:</h4>
                  {debugInfo.messages && debugInfo.messages.length > 0 ? (
                    <div className="space-y-1 font-mono text-xs">
                      {debugInfo.messages.map((msg: any, idx: number) => (
                        <div key={idx} className="flex gap-2">
                          <span className="text-gray-500">{new Date(msg.time).toLocaleTimeString()}</span>
                          <span>{msg.text}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-gray-500">No process logs yet. Start a reorganization to see logs.</p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
            
            <div className="mt-4 flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={loadDebugInfo}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Refresh Debug Info
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5" />
            GPT-5 Enhanced Concept Reorganizer
          </CardTitle>
          <CardDescription>
            Use GPT-5 to comprehensively reorganize your concepts with full backwards compatibility
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">
                Total Tags: <span className="font-semibold">{currentStructure?.statistics?.total_tags || 0}</span>
              </p>
              <p className="text-sm text-muted-foreground">
                Current Categories: <span className="font-semibold">{currentStructure?.statistics?.root_categories || 0}</span>
              </p>
            </div>
            
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={loadCurrentStructure}
                disabled={loading}
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              
              <Button
                onClick={generateProposal}
                disabled={loading || applyingChanges}
                className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Analyzing with GPT-5...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-2" />
                    Generate Reorganization Proposal
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Main Content */}
      {(currentStructure || proposal) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Tree View */}
          <Card className="lg:col-span-2">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Tag Hierarchy</CardTitle>
                <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'current' | 'proposed')}>
                  <TabsList>
                    <TabsTrigger value="current">
                      <Eye className="h-4 w-4 mr-2" />
                      Current
                    </TabsTrigger>
                    {proposal && (
                      <TabsTrigger value="proposed">
                        <Sparkles className="h-4 w-4 mr-2" />
                        Proposed
                      </TabsTrigger>
                    )}
                  </TabsList>
                </Tabs>
              </div>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] pr-4">
                {viewMode === 'current' && currentStructure?.hierarchy && (
                  <div className="space-y-1">
                    {currentStructure.root_categories?.map((catName: string) => {
                      const node = currentStructure.hierarchy[catName]
                      if (node) {
                        return renderTagNode(node, currentStructure.hierarchy)
                      }
                      return null
                    })}
                  </div>
                )}
                
                {viewMode === 'proposed' && proposal?.hierarchy && (
                  <div className="space-y-1">
                    {proposal.root_categories?.map((catName: string) => {
                      const node = proposal.hierarchy[catName]
                      if (node) {
                        return renderTagNode(node, proposal.hierarchy)
                      }
                      return null
                    })}
                  </div>
                )}
              </ScrollArea>
              
              {viewMode === 'proposed' && proposal && (
                <div className="mt-4 pt-4 border-t">
                  <div className="flex items-center justify-between">
                    <div className="text-sm text-muted-foreground">
                      {Object.values(approvedChanges).filter(v => v).length} of {Object.keys(approvedChanges).length} changes approved
                    </div>
                    <Button
                      onClick={applyApprovedChanges}
                      disabled={applyingChanges || Object.values(approvedChanges).filter(v => v).length === 0}
                    >
                      {applyingChanges ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Applying Changes...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-4 w-4 mr-2" />
                          Apply Approved Changes
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Details Panel */}
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent>
              {selectedNodeDetails ? (
                <div className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-sm mb-1">Display Name</h4>
                    <p className="text-sm text-muted-foreground">{selectedNodeDetails.display_name}</p>
                  </div>
                  
                  {selectedNodeDetails.description && (
                    <div>
                      <h4 className="font-semibold text-sm mb-1">Description</h4>
                      <p className="text-sm text-muted-foreground">{selectedNodeDetails.description}</p>
                    </div>
                  )}
                  
                  <div>
                    <h4 className="font-semibold text-sm mb-1">Usage Count</h4>
                    <Badge variant="secondary">{selectedNodeDetails.usage_count || 0}</Badge>
                  </div>
                  
                  {selectedNodeDetails.parent && (
                    <div>
                      <h4 className="font-semibold text-sm mb-1">Parent</h4>
                      <Badge variant="outline">{selectedNodeDetails.parent}</Badge>
                    </div>
                  )}
                  
                  {selectedNodeDetails.synonyms && selectedNodeDetails.synonyms.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-sm mb-1">Synonyms</h4>
                      <div className="flex flex-wrap gap-1">
                        {selectedNodeDetails.synonyms.map((syn: string) => (
                          <Badge key={syn} variant="outline" className="text-xs">
                            {syn}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {selectedNodeDetails.children && selectedNodeDetails.children.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-sm mb-1">Children ({selectedNodeDetails.children.length})</h4>
                      <ScrollArea className="h-32">
                        <div className="space-y-1">
                          {selectedNodeDetails.children.map((child: string) => (
                            <div key={child} className="text-sm text-muted-foreground">
                              • {child}
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-muted-foreground">Select a tag to view details</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Proposal Statistics */}
      {proposal && (
        <Card>
          <CardHeader>
            <CardTitle>Reorganization Proposal Statistics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Model Used</p>
                <p className="font-semibold">{proposal.model_used}</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Confidence Score</p>
                <Progress value={proposal.confidence_score * 100} className="h-2" />
                <p className="text-xs text-muted-foreground">{(proposal.confidence_score * 100).toFixed(1)}%</p>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Merge Proposals</p>
                <Badge variant="secondary">
                  <GitMerge className="h-3 w-3 mr-1" />
                  {proposal.merge_proposals?.length || 0}
                </Badge>
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">Deprecated Tags</p>
                <Badge variant="secondary">
                  <Archive className="h-3 w-3 mr-1" />
                  {proposal.deprecated_tags?.length || 0}
                </Badge>
              </div>
            </div>
            
            {proposal.reasoning && (
              <div className="mt-4 pt-4 border-t">
                <h4 className="font-semibold text-sm mb-2">AI Reasoning</h4>
                <p className="text-sm text-muted-foreground">{proposal.reasoning}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}