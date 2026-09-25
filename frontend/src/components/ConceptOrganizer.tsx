import { useState, useEffect } from 'react'
import http from '@/services/http'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"




import {
  AlertCircle,
  CheckCircle,
  Loader2,
  Info,
  GitBranch,
  Tag,
  Users,
  FileText,
  RefreshCw,
  Sparkles
} from 'lucide-react'

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
  alias_of?: string
  parent_concepts?: string[]
  entity_type?: string
  description?: string
  reasoning?: string
}

interface ConceptDetails {
  _id: string
  display_name: string
}

export default function ConceptOrganizer() {
  const [unorganizedConcepts, setUnorganizedConcepts] = useState<UnorganizedConcept[]>([])
  const [selectedConcept, setSelectedConcept] = useState<UnorganizedConcept | null>(null)
  const [suggestion, setSuggestion] = useState<OrganizationSuggestion | null>(null)
  const [loading, setLoading] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [stats, setStats] = useState<any>(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [_showDetails, setShowDetails] = useState(false)
  const [allConcepts, setAllConcepts] = useState<ConceptDetails[]>([])

  useEffect(() => {
    loadUnorganizedConcepts()
    loadStats()
    loadAllConcepts()
  }, [])
  
  // Clear selection when no unorganized concepts
  useEffect(() => {
    if (unorganizedConcepts.length === 0) {
      setSelectedConcept(null)
      setSuggestion(null)
    }
  }, [unorganizedConcepts])

  const loadUnorganizedConcepts = async () => {
    try {
      setLoading(true)
      const response = await http.get(`/api/concepts/organization/unorganized?limit=50`)
      setUnorganizedConcepts(response.data.concepts || [])
    } catch (err) {
      console.error('Error loading unorganized concepts:', err)
      setError('Failed to load unorganized concepts')
    } finally {
      setLoading(false)
    }
  }

  const loadStats = async () => {
    try {
      const response = await http.get(`/api/concepts/organization/stats`)
      setStats(response.data.stats)
    } catch (err) {
      console.error('Error loading stats:', err)
    }
  }

  const loadAllConcepts = async () => {
    try {
      const response = await http.get(`/api/ontology/concepts`)
      setAllConcepts(response.data.concepts || [])
    } catch (err) {
      console.error('Error loading concepts:', err)
    }
  }

  const analyzeConcept = async (concept: UnorganizedConcept) => {
    // Validate concept before proceeding
    if (!concept || !concept._id) {
      setError('Invalid concept selected')
      return
    }
    
    try {
      setProcessing(true)
      setError('')
      setSuccess('')
      setSuggestion(null)
      setSelectedConcept(concept)
      
      console.log('Analyzing concept:', concept._id, concept.display_name)
      
      // Double-check the concept ID is valid
      if (!concept._id || concept._id === 'undefined') {
        throw new Error('Invalid concept ID')
      }
      
      const response = await http.post(`/api/concepts/organization/organize`, {
        concept_id: concept._id,
        auto_apply: false
      })
      
      if (response.data.success) {
        setSuggestion({
          is_alias: response.data.is_alias,
          alias_of: response.data.alias_of,
          parent_concepts: response.data.parent_concepts,
          entity_type: response.data.entity_type,
          description: response.data.description,
          reasoning: response.data.reasoning
        })
        setShowDetails(true)
      } else {
        setError(response.data.error || 'Failed to analyze concept')
      }
    } catch (err: any) {
      console.error('Error analyzing concept:', err)
      setError(err.response?.data?.detail || 'Failed to analyze concept')
    } finally {
      setProcessing(false)
    }
  }

  const applySuggestion = async () => {
    if (!selectedConcept || !suggestion) {
      setError('No concept or suggestion to apply')
      return
    }
    
    try {
      setProcessing(true)
      setError('')
      
      const response = await http.post(`/api/concepts/organization/apply-organization/${selectedConcept._id}`, suggestion)
      
      if (response.data.success) {
        setSuccess(`Successfully organized "${selectedConcept.display_name}"`)
        setShowDetails(false)
        setSuggestion(null)
        setSelectedConcept(null)
        
        // Reload lists
        await loadUnorganizedConcepts()
        await loadStats()
      }
    } catch (err: any) {
      console.error('Error applying suggestion:', err)
      setError(err.response?.data?.detail || 'Failed to apply organization')
    } finally {
      setProcessing(false)
    }
  }

  const organizeBatch = async () => {
    // Check if there are any concepts to organize
    if (unorganizedConcepts.length === 0) {
      setError('No concepts to organize')
      return
    }
    
    try {
      setProcessing(true)
      setError('')
      
      const response = await http.post(`/api/concepts/organization/organize-batch`, {
        limit: 5,
        auto_apply: false
      })
      
      if (response.data.success) {
        setSuccess(`Processing ${response.data.processed || 5} concepts...`)
        
        // Reload after a delay
        setTimeout(() => {
          loadUnorganizedConcepts()
          loadStats()
        }, 3000)
      }
    } catch (err: any) {
      console.error('Error organizing batch:', err)
      setError(err.response?.data?.detail || 'Failed to organize batch')
    } finally {
      setProcessing(false)
    }
  }

  const getEntityTypeIcon = (type?: string) => {
    switch (type) {
      case 'person': return <Users className="h-4 w-4" />
      case 'organisation': return <Users className="h-4 w-4" />
      case 'technology': return <Tag className="h-4 w-4" />
      default: return <FileText className="h-4 w-4" />
    }
  }

  const getConceptName = (conceptId: string) => {
    const concept = allConcepts.find(c => c._id === conceptId)
    return concept?.display_name || conceptId
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Stats Card */}
      <Card className="lg:col-span-3">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-5 w-5" />
            Concept Organization Center
          </CardTitle>
          <CardDescription>
            Organize new concepts into the hierarchy or identify them as aliases
          </CardDescription>
        </CardHeader>
        <CardContent>
          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold">{stats.total_concepts}</div>
                <div className="text-sm text-muted-foreground">Total Concepts</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{stats.organized_concepts}</div>
                <div className="text-sm text-muted-foreground">Organized</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{stats.unorganized_concepts}</div>
                <div className="text-sm text-muted-foreground">Need Review</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{stats.aliases}</div>
                <div className="text-sm text-muted-foreground">Aliases</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {stats.organization_percentage?.toFixed(1)}%
                </div>
                <div className="text-sm text-muted-foreground">Organized</div>
              </div>
            </div>
          )}
          
          <div className="mt-4 flex gap-2">
            <Button 
              onClick={() => {
                loadUnorganizedConcepts()
                loadStats()
                loadAllConcepts()
                setSelectedConcept(null)
                setSuggestion(null)
                setError('')
                setSuccess('')
              }} 
              variant="outline"
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button 
              onClick={organizeBatch}
              disabled={processing || unorganizedConcepts.length === 0}
            >
              <Sparkles className="h-4 w-4 mr-2" />
              Auto-Organize 5 Concepts
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Unorganized Concepts List */}
      <Card className="lg:col-span-1">
        <CardHeader>
          <CardTitle>Unorganized Concepts</CardTitle>
          <CardDescription>
            {unorganizedConcepts.length} concepts need organization
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[500px]">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="h-6 w-6 animate-spin" />
              </div>
            ) : unorganizedConcepts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-600" />
                All concepts are organized!
              </div>
            ) : (
              <div className="space-y-2">
                {unorganizedConcepts.map((concept) => (
                  <div
                    key={concept._id}
                    className={`p-3 border rounded-lg cursor-pointer hover:bg-accent transition-colors ${
                      selectedConcept?._id === concept._id ? 'bg-accent border-primary' : ''
                    }`}
                    onClick={() => {
                      if (concept && concept._id) {
                        analyzeConcept(concept)
                      } else {
                        console.error('Invalid concept:', concept)
                        setError('Cannot analyze invalid concept')
                      }
                    }}
                  >
                    <div className="font-medium">{concept.display_name}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="secondary" className="text-xs">
                        Used {concept.usage_count} times
                      </Badge>
                      {concept.description && (
                        <Info className="h-3 w-3 text-muted-foreground" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Organization Suggestion */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Organization Analysis</CardTitle>
          <CardDescription>
            AI-powered suggestions for concept organization
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {success && (
            <Alert className="mb-4">
              <CheckCircle className="h-4 w-4" />
              <AlertTitle>Success</AlertTitle>
              <AlertDescription>
                {success}
                {unorganizedConcepts.length === 0 && (
                  <div className="mt-2 text-sm">
                    🎉 All concepts are now organized! Great work!
                  </div>
                )}
              </AlertDescription>
            </Alert>
          )}

          {processing ? (
            <div className="flex flex-col items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin mb-4" />
              <p className="text-muted-foreground">Analyzing concept...</p>
            </div>
          ) : suggestion && selectedConcept && selectedConcept._id ? (
            <div className="space-y-4">
              <div>
                <Label>Analyzing</Label>
                <div className="text-lg font-semibold">{selectedConcept?.display_name || 'Unknown Concept'}</div>
              </div>

              <Separator />

              {suggestion.is_alias ? (
                <Alert>
                  <Info className="h-4 w-4" />
                  <AlertTitle>This is an Alias</AlertTitle>
                  <AlertDescription>
                    This concept appears to be an alias of: 
                    <span className="font-semibold ml-1">
                      {getConceptName(suggestion.alias_of || '')}
                    </span>
                  </AlertDescription>
                </Alert>
              ) : (
                <div className="space-y-4">
                  <div>
                    <Label>Suggested Parent Concepts</Label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {suggestion.parent_concepts?.map((parentId) => (
                        <Badge key={parentId} variant="secondary">
                          {getConceptName(parentId)}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div>
                    <Label>Entity Type</Label>
                    <div className="flex items-center gap-2 mt-2">
                      {getEntityTypeIcon(suggestion.entity_type)}
                      <Badge>{suggestion.entity_type || 'other'}</Badge>
                    </div>
                  </div>

                  {suggestion.description && (
                    <div>
                      <Label>Suggested Description</Label>
                      <Textarea
                        value={suggestion.description}
                        readOnly
                        className="mt-2"
                        rows={3}
                      />
                    </div>
                  )}
                </div>
              )}

              {suggestion.reasoning && (
                <div>
                  <Label>AI Reasoning</Label>
                  <div className="mt-2 p-3 bg-muted rounded-lg text-sm">
                    {suggestion.reasoning}
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button 
                  onClick={applySuggestion}
                  disabled={processing || !suggestion || !selectedConcept}
                >
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Apply Organization
                </Button>
                <Button 
                  variant="outline"
                  onClick={() => {
                    setSuggestion(null)
                    setSelectedConcept(null)
                  }}
                >
                  Skip
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <GitBranch className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>Select an unorganized concept to analyze</p>
              <p className="text-sm mt-2">
                The AI will determine if it's an alias or suggest where to place it in the hierarchy
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}