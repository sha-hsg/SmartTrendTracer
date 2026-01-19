import React, { useState, useRef } from 'react'
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
  Play,
  StopCircle,
  Code,
  TreePine,
  Eye,
  EyeOff,
  Copy,
  Download,
  Bug
} from 'lucide-react'

interface TaskUpdate {
  task_id: string
  mode: string
  status: string
  progress: number
  current_step: string
  messages: { time: string; text: string }[]
  elapsed_seconds: number
  debug_prompt?: string
  debug_prompt_full_size?: number
}

interface ReorganizationResult {
  concepts: any[]
  aliases: any[]
  relations?: any[]
  root_categories: string[]
  merge_proposals?: any[]
  validation?: any
  confidence_score?: number
  reasoning?: string
}

export default function TagReorganizerDebug() {
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskUpdate | null>(null)
  const [result, setResult] = useState<ReorganizationResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<'gpt5' | 'comprehensive'>('gpt5')
  const eventSourceRef = useRef<EventSource | null>(null)
  
  // Debug states
  const [showDebug, setShowDebug] = useState(false)
  const [fullPrompt, setFullPrompt] = useState<string>('')
  const [systemPrompt, setSystemPrompt] = useState<string>('')
  const [showPrompt, setShowPrompt] = useState(false)
  const [showPreview, setShowPreview] = useState(false)
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set())

  const startReorganization = async () => {
    try {
      setError(null)
      setResult(null)
      setFullPrompt('')
      setSystemPrompt('')
      
      const response = await axios.post(
        `http://localhost:8000/api/tags/reorganize/start?mode=${mode}`
      )
      
      const { task_id, stream_url } = response.data
      setTaskId(task_id)
      
      // Start listening to SSE stream
      const eventSource = new EventSource(`http://localhost:8000${stream_url}`)
      eventSourceRef.current = eventSource
      
      eventSource.onmessage = (event) => {
        const update = JSON.parse(event.data)
        setTaskStatus(update)
        
        // Check if task is complete
        if (update.status === 'completed') {
          fetchResult(task_id)
          fetchDebugInfo(task_id)
        }
      }
      
      eventSource.addEventListener('done', () => {
        eventSource.close()
        eventSourceRef.current = null
      })
      
      eventSource.onerror = (err) => {
        console.error('SSE error:', err)
        setError('Connection to server lost')
        eventSource.close()
        eventSourceRef.current = null
      }
      
    } catch (err: any) {
      setError(err.message || 'Failed to start reorganization')
    }
  }
  
  const fetchResult = async (taskId: string) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/tags/reorganize/result/${taskId}`
      )
      setResult(response.data.result)
      setShowPreview(true)
    } catch (err: any) {
      if (err.response?.status === 404) {
        // Task was lost due to server restart
        setError('Task results were lost due to server restart. The reorganization completed but results are unavailable. Please run the reorganization again.')
        setTaskStatus(prev => ({
          ...prev,
          status: 'lost',
          messages: [...(prev?.messages || []), {
            time: new Date().toISOString(),
            text: 'Task data lost due to server restart'
          }]
        }))
      } else {
        console.error('Failed to fetch result:', err)
      }
    }
  }
  
  const fetchDebugInfo = async (taskId: string) => {
    try {
      const response = await axios.get(
        `http://localhost:8000/api/tags/reorganize/debug/${taskId}`
      )
      setFullPrompt(response.data.debug_prompt || '')
      setSystemPrompt(response.data.debug_system_prompt || '')
    } catch (err: any) {
      if (err.response?.status === 404) {
        // Silently ignore - debug info was lost with the task
        console.log('Debug info unavailable - task data was lost')
      } else {
        console.error('Failed to fetch debug info:', err)
      }
    }
  }
  
  const cancelReorganization = async () => {
    if (!taskId) return
    
    try {
      await axios.post(
        `http://localhost:8000/api/tags/reorganize/cancel/${taskId}`
      )
      
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      
      setTaskStatus(null)
      setTaskId(null)
    } catch (err: any) {
      setError(err.message || 'Failed to cancel')
    }
  }
  
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }
  
  const downloadPrompt = () => {
    const blob = new Blob([
      `=== SYSTEM PROMPT ===\n\n${systemPrompt}\n\n=== USER PROMPT ===\n\n${fullPrompt}`
    ], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `gpt5_prompt_${taskId}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }
  
  const toggleCategory = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories)
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId)
    } else {
      newExpanded.add(categoryId)
    }
    setExpandedCategories(newExpanded)
  }
  
  const renderConceptTree = (concepts: any[], parentId: string | null = null, level: number = 0) => {
    const children = concepts.filter(c => {
      const parents = c.parents || []
      if (parentId === null) {
        return parents.length === 0 || (parents.length === 1 && parents[0] === '')
      }
      return parents.includes(parentId)
    })
    
    if (children.length === 0) return null
    
    return (
      <div className={`${level > 0 ? 'ml-4' : ''}`}>
        {children.map(concept => {
          const hasChildren = concepts.some(c => c.parents?.includes(concept.id))
          const isExpanded = expandedCategories.has(concept.id)
          
          return (
            <div key={concept.id} className="my-1">
              <div 
                className="flex items-center gap-2 p-2 hover:bg-gray-100 dark:hover:bg-gray-800 rounded cursor-pointer"
                onClick={() => hasChildren && toggleCategory(concept.id)}
              >
                {hasChildren && (
                  isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />
                )}
                {!hasChildren && <div className="w-4" />}
                
                {concept.icon && <span>{concept.icon}</span>}
                <span className="font-medium">{concept.display_name}</span>
                <Badge variant="outline" className="ml-2">
                  {concept.entity_type || 'concept'}
                </Badge>
                {concept.usage_count > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {concept.usage_count}
                  </Badge>
                )}
              </div>
              
              {hasChildren && isExpanded && renderConceptTree(concepts, concept.id, level + 1)}
            </div>
          )
        })}
      </div>
    )
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-5 w-5" />
                Tag Reorganizer with Debug
              </CardTitle>
              <CardDescription>
                Reorganize tags using GPT-5 with full visibility into the process
              </CardDescription>
            </div>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDebug(!showDebug)}
            >
              <Bug className="h-4 w-4 mr-2" />
              {showDebug ? 'Hide' : 'Show'} Debug
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Warning about server restarts */}
            <Alert className="border-yellow-200 bg-yellow-50">
              <AlertDescription className="text-sm">
                <strong>Note:</strong> Reorganization results are stored in memory and will be lost if the server restarts. 
                GPT-5 responses are saved to <code>data/gpt5_responses/</code> for backup.
              </AlertDescription>
            </Alert>
            
            {/* Mode Selection */}
            <div className="flex items-center gap-4">
              <label className="text-sm font-medium">Mode:</label>
              <div className="flex gap-2">
                <Button
                  variant={mode === 'gpt5' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMode('gpt5')}
                  disabled={taskStatus !== null}
                >
                  GPT-5 Enhanced
                </Button>
                <Button
                  variant={mode === 'comprehensive' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMode('comprehensive')}
                  disabled={taskStatus !== null}
                >
                  Rule-Based
                </Button>
              </div>
            </div>
            
            {/* Action Buttons */}
            <div className="flex gap-2">
              {!taskStatus ? (
                <Button 
                  onClick={startReorganization}
                  className="bg-gradient-to-r from-blue-500 to-purple-500 hover:from-blue-600 hover:to-purple-600"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Start Reorganization
                </Button>
              ) : taskStatus.status !== 'completed' ? (
                <Button 
                  onClick={cancelReorganization}
                  variant="destructive"
                >
                  <StopCircle className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
              ) : (
                <Button 
                  onClick={() => {
                    setTaskStatus(null)
                    setTaskId(null)
                    setResult(null)
                  }}
                  variant="outline"
                >
                  Reset
                </Button>
              )}
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
      
      {/* Progress Card */}
      {taskStatus && (
        <Card>
          <CardHeader>
            <CardTitle>Progress</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span>{taskStatus.current_step}</span>
                <span>{taskStatus.progress}%</span>
              </div>
              <Progress value={taskStatus.progress} />
            </div>
            
            <div className="text-sm text-muted-foreground">
              Status: <Badge variant={
                taskStatus.status === 'completed' ? 'default' : 
                taskStatus.status === 'error' ? 'destructive' : 
                'secondary'
              }>
                {taskStatus.status}
              </Badge>
            </div>
            
            <div className="text-sm text-muted-foreground">
              Elapsed: {Math.round(taskStatus.elapsed_seconds)}s
            </div>
            
            {/* Messages Log */}
            <div>
              <h4 className="font-medium text-sm mb-2">Activity Log</h4>
              <ScrollArea className="h-32 border rounded p-2">
                {taskStatus.messages.map((msg, idx) => (
                  <div key={idx} className="text-xs mb-1">
                    <span className="text-muted-foreground">
                      {new Date(msg.time).toLocaleTimeString()}:
                    </span>{' '}
                    {msg.text}
                  </div>
                ))}
              </ScrollArea>
            </div>
          </CardContent>
        </Card>
      )}
      
      {/* Debug Section */}
      {showDebug && taskStatus && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Code className="h-4 w-4" />
              Debug Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Prompt Preview */}
            {taskStatus.debug_prompt && (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-medium text-sm">
                    GPT-5 Prompt ({taskStatus.debug_prompt_full_size?.toLocaleString()} characters)
                  </h4>
                  <div className="flex gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowPrompt(!showPrompt)}
                    >
                      {showPrompt ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => fetchDebugInfo(taskId!)}
                    >
                      Load Full
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={downloadPrompt}
                      disabled={!fullPrompt}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
                
                {showPrompt && (
                  <div className="space-y-2">
                    <div className="border rounded p-2">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-medium text-muted-foreground">System Prompt</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyToClipboard(systemPrompt)}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                      <ScrollArea className="h-32">
                        <pre className="text-xs whitespace-pre-wrap">
                          {systemPrompt || taskStatus.debug_prompt.substring(0, 500) + '...'}
                        </pre>
                      </ScrollArea>
                    </div>
                    
                    <div className="border rounded p-2">
                      <div className="flex justify-between items-center mb-1">
                        <span className="text-xs font-medium text-muted-foreground">User Prompt</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => copyToClipboard(fullPrompt)}
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                      </div>
                      <ScrollArea className="h-64">
                        <pre className="text-xs whitespace-pre-wrap">
                          {fullPrompt || 'Click "Load Full" to see complete prompt'}
                        </pre>
                      </ScrollArea>
                    </div>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
      
      {/* Result Preview */}
      {result && showPreview && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <TreePine className="h-4 w-4" />
                Reorganization Preview
              </CardTitle>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setShowPreview(!showPreview)}
              >
                {showPreview ? 'Hide' : 'Show'} Preview
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="tree">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="tree">Hierarchy</TabsTrigger>
                <TabsTrigger value="aliases">Aliases</TabsTrigger>
                <TabsTrigger value="merges">Merges</TabsTrigger>
                <TabsTrigger value="validation">Validation</TabsTrigger>
              </TabsList>
              
              <TabsContent value="tree" className="mt-4">
                <ScrollArea className="h-96 border rounded p-4">
                  {renderConceptTree(result.concepts)}
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="aliases" className="mt-4">
                <ScrollArea className="h-96 border rounded p-4">
                  <div className="space-y-2">
                    {result.aliases?.slice(0, 50).map((alias: any, idx: number) => (
                      <div key={idx} className="flex items-center gap-2 text-sm">
                        <Badge variant="outline">{alias.alias_text}</Badge>
                        <span className="text-muted-foreground">→</span>
                        <Badge variant="secondary">{alias.alias_of || alias.canonical_slug}</Badge>
                        <Badge variant="outline" className="ml-auto">
                          {alias.kind || alias.alias_type}
                        </Badge>
                      </div>
                    ))}
                    {result.aliases?.length > 50 && (
                      <p className="text-sm text-muted-foreground">
                        ... and {result.aliases.length - 50} more aliases
                      </p>
                    )}
                  </div>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="merges" className="mt-4">
                <ScrollArea className="h-96 border rounded p-4">
                  <div className="space-y-2">
                    {result.merge_proposals?.map((merge: any, idx: number) => (
                      <div key={idx} className="border rounded p-2">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge>{merge.primary}</Badge>
                          <span className="text-muted-foreground">←</span>
                          {merge.merge_into?.map((tag: string) => (
                            <Badge key={tag} variant="outline">{tag}</Badge>
                          ))}
                        </div>
                        <p className="text-xs text-muted-foreground">{merge.reason}</p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>
              
              <TabsContent value="validation" className="mt-4">
                <div className="space-y-4">
                  {result.validation && (
                    <>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium">Coverage</p>
                          <p className="text-2xl font-bold">
                            {result.validation.coverage_mapped_percent?.toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium">Total Tags</p>
                          <p className="text-2xl font-bold">
                            {result.validation.coverage_total_legacy_tags}
                          </p>
                        </div>
                      </div>
                      
                      {result.validation.warnings?.length > 0 && (
                        <Alert>
                          <AlertCircle className="h-4 w-4" />
                          <AlertDescription>
                            {result.validation.warnings.length} warnings found
                          </AlertDescription>
                        </Alert>
                      )}
                      
                      <div className="text-sm">
                        <p className="font-medium mb-2">Statistics:</p>
                        <ul className="space-y-1 text-muted-foreground">
                          <li>• Concepts created: {result.concepts?.length || 0}</li>
                          <li>• Aliases created: {result.aliases?.length || 0}</li>
                          <li>• Root categories: {result.root_categories?.length || 0}</li>
                          <li>• Confidence score: {(result.confidence_score || 0) * 100}%</li>
                        </ul>
                      </div>
                    </>
                  )}
                </div>
              </TabsContent>
            </Tabs>
            
            {result.reasoning && (
              <div className="mt-4 pt-4 border-t">
                <h4 className="font-medium text-sm mb-2">AI Reasoning</h4>
                <p className="text-sm text-muted-foreground">{result.reasoning}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}