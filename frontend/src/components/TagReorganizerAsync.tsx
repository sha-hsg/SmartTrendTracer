import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  Play,
  StopCircle,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  Brain,
  Loader2,
  MessageSquare,
  TrendingUp,
  GitMerge,
  Layers,
  Hash,
  Activity,
  ChevronDown,
  ChevronRight,
  XCircle,
  Download,
  Eye
} from 'lucide-react'
import { cn } from "@/lib/utils"

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface ReorganizationStatus {
  task_id: string
  mode: string
  status: 'initializing' | 'starting' | 'collecting' | 'analyzing' | 'generating' | 'completed' | 'error' | 'cancelled' | 'cancelling'
  progress: number
  current_step: string
  messages: Array<{
    time: string
    text: string
  }>
  start_time: string
  end_time?: string
  elapsed_seconds: number
  cancelled: boolean
  error?: string
  total_steps: number
  completed_steps: number
}

interface ReorganizationResult {
  merge_groups: Array<{
    tags: string[]
    suggested: string
  }>
  hierarchy: Record<string, string[]>
  entity_types: Record<string, string>
  stats: {
    total_tags: number
    unique_concepts: number
    merge_groups: number
    hierarchy_levels: number
  }
  concepts?: Array<{ slug: string; display_name: string }>
  aliases?: Array<{ alias: string; concept_slug: string }>
  merge_proposals?: Array<{ tags: string[]; suggested: string }>
}

export default function TagReorganizerAsync() {
  const [isRunning, setIsRunning] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [status, setStatus] = useState<ReorganizationStatus | null>(null)
  const [result, setResult] = useState<ReorganizationResult | null>(null)
  const [mode, setMode] = useState<'gpt5' | 'comprehensive'>('gpt5')
  const [expandedGroups, setExpandedGroups] = useState<Set<number>>(new Set())
  const [showResult, setShowResult] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const [elapsedTime, setElapsedTime] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const messagesEndRef = useRef<HTMLDivElement | null>(null)
  const scrollAreaRef = useRef<HTMLDivElement | null>(null)
  const [autoScroll, setAutoScroll] = useState(true)
  const [applyingRecommendations, setApplyingRecommendations] = useState(false)

  // Update elapsed time every second
  useEffect(() => {
    if (isRunning && status) {
      timerRef.current = setInterval(() => {
        setElapsedTime(Math.floor(status.elapsed_seconds))
      }, 1000)
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [isRunning, status])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [status?.messages, autoScroll])

  const startReorganization = async () => {
    try {
      setIsRunning(true)
      setResult(null)
      setShowResult(false)
      
      const response = await axios.post(`${API_BASE_URL}/api/tags/reorganize/start`, null, {
        params: { mode }
      })
      
      const { task_id } = response.data
      setTaskId(task_id)
      
      // Start listening to SSE stream
      const eventSource = new EventSource(`${API_BASE_URL}/api/tags/reorganize/stream/${task_id}`)
      eventSourceRef.current = eventSource
      
      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data)
        setStatus(data)
        setElapsedTime(Math.floor(data.elapsed_seconds))
        
        if (data.status === 'completed') {
          fetchResult(task_id)
        }
      }
      
      eventSource.addEventListener('done', () => {
        eventSource.close()
        setIsRunning(false)
      })
      
      eventSource.onerror = (error) => {
        console.error('SSE error:', error)
        eventSource.close()
        setIsRunning(false)
      }
      
    } catch (error) {
      console.error('Failed to start reorganization:', error)
      setIsRunning(false)
    }
  }

  const cancelReorganization = async () => {
    if (!taskId) return
    
    try {
      await axios.post(`${API_BASE_URL}/api/tags/reorganize/cancel/${taskId}`)
      
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
      }
      
      setIsRunning(false)
    } catch (error) {
      console.error('Failed to cancel reorganization:', error)
    }
  }

  const fetchResult = async (id: string) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/tags/reorganize/result/${id}`)
      setResult(response.data.result)
      setShowResult(true)
    } catch (error) {
      console.error('Failed to fetch result:', error)
    }
  }

  const formatElapsedTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  const getStatusIcon = () => {
    if (!status) return null
    
    switch (status.status) {
      case 'initializing':
      case 'starting':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
      case 'collecting':
        return <Activity className="h-5 w-5 animate-pulse text-purple-500" />
      case 'analyzing':
        return <Brain className="h-5 w-5 animate-pulse text-indigo-500" />
      case 'generating':
        return <TrendingUp className="h-5 w-5 animate-pulse text-green-500" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'cancelled':
      case 'cancelling':
        return <StopCircle className="h-5 w-5 text-orange-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = () => {
    if (!status) return 'bg-gray-100'
    
    switch (status.status) {
      case 'collecting': return 'bg-purple-50'
      case 'analyzing': return 'bg-indigo-50'
      case 'generating': return 'bg-blue-50'
      case 'completed': return 'bg-green-50'
      case 'error': return 'bg-red-50'
      case 'cancelled': return 'bg-orange-50'
      default: return 'bg-gray-50'
    }
  }

  const toggleGroup = (index: number) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev)
      if (newSet.has(index)) {
        newSet.delete(index)
      } else {
        newSet.add(index)
      }
      return newSet
    })
  }

  const applyRecommendations = async (comprehensive: boolean = false) => {
    if (!result) {
      alert('No recommendations to apply')
      return
    }

    const endpoint = comprehensive ? 'apply-comprehensive' : 'apply'
    const confirmMsg = comprehensive 
      ? `⚠️ COMPREHENSIVE REORGANIZATION ⚠️\n\n` +
        `This will COMPLETELY reorganize your tag system:\n` +
        `- Create ${result.concepts?.length || 0} new concepts\n` +
        `- Create ${result.aliases?.length || 0} aliases\n` +
        `- Process ${result.merge_proposals?.length || 0} merge proposals\n` +
        `- Remap ALL existing tags to new concepts\n` +
        `\nThis is a major operation. Proceed?`
      : `This will create:\n` +
        `- ${result.concepts?.length || 0} concepts\n` +
        `- ${result.aliases?.length || 0} aliases\n` +
        `\nProceed with applying these recommendations?`
    
    if (!confirm(confirmMsg)) {
      return
    }

    setApplyingRecommendations(true)
    
    try {
      const response = await axios.post(`${API_BASE_URL}/api/tags/reorganize/${endpoint}`, result)
      
      if (response.data.success) {
        const stats = response.data.stats
        const summary = response.data.summary
        
        const message = comprehensive
          ? `✅ COMPREHENSIVE REORGANIZATION COMPLETE!\n\n` +
            `Changes Made:\n` +
            `- ${stats.concepts_created} concepts created\n` +
            `- ${stats.aliases_created} aliases created\n` +
            `- ${stats.hierarchy_links} hierarchy links\n` +
            `- ${stats.tags_remapped} tags remapped\n` +
            `- ${stats.merges_processed} merges processed\n` +
            `\nFinal State:\n` +
            `- Total concepts: ${summary?.total_concepts || 0}\n` +
            `- Total aliases: ${summary?.total_aliases || 0}\n` +
            `- Mapped tags: ${summary?.mapped_tags || 0}\n` +
            `- Unmapped tags: ${summary?.unmapped_tags || 0}\n` +
            (stats.errors?.length ? `\n⚠️ ${stats.errors.length} errors occurred` : '')
          : `Successfully applied recommendations!\n\n` +
            `Created:\n` +
            `- ${stats.concepts_created} concepts\n` +
            `- ${stats.aliases_created} aliases\n` +
            `- ${stats.hierarchy_links} hierarchy links\n` +
            `- ${stats.tags_mapped} tags mapped\n` +
            (stats.errors?.length ? `\n⚠️ ${stats.errors.length} errors occurred` : '')
        
        alert(message)
        
        // Reload the page to show new concepts
        window.location.reload()
      } else {
        alert('Failed to apply recommendations: ' + (response.data.message || 'Unknown error'))
      }
    } catch (error: any) {
      console.error('Error applying recommendations:', error)
      alert('Error applying recommendations: ' + (error.response?.data?.detail || error.message))
    } finally {
      setApplyingRecommendations(false)
    }
  }

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Tag Reorganizer - AI Enhanced</h1>
        <p className="text-gray-600">
          Analyze and reorganize your tag system using advanced AI models for better organization
        </p>
      </div>

      {/* Control Panel */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            Reorganization Control
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Mode Selection */}
            <div className="flex gap-4">
              <Button
                variant={mode === 'gpt5' ? 'default' : 'outline'}
                onClick={() => setMode('gpt5')}
                disabled={isRunning}
                className="flex items-center gap-2"
              >
                <Zap className="h-4 w-4" />
                GPT-5 Enhanced
              </Button>
              <Button
                variant={mode === 'comprehensive' ? 'default' : 'outline'}
                onClick={() => setMode('comprehensive')}
                disabled={isRunning}
                className="flex items-center gap-2"
              >
                <Layers className="h-4 w-4" />
                Comprehensive
              </Button>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3">
              {!isRunning ? (
                <Button
                  onClick={startReorganization}
                  className="flex items-center gap-2"
                  variant="default"
                >
                  <Play className="h-4 w-4" />
                  Start Reorganization
                </Button>
              ) : (
                <Button
                  onClick={cancelReorganization}
                  variant="destructive"
                  className="flex items-center gap-2"
                >
                  <StopCircle className="h-4 w-4" />
                  Cancel Process
                </Button>
              )}
              
              {result && (
                <Button
                  variant="outline"
                  onClick={() => setShowResult(!showResult)}
                  className="flex items-center gap-2"
                >
                  <Eye className="h-4 w-4" />
                  {showResult ? 'Hide' : 'Show'} Results
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Status Panel */}
      {status && (
        <Card className={cn("mb-6 transition-all", getStatusColor())}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                {getStatusIcon()}
                <span>Status: {status.status.charAt(0).toUpperCase() + status.status.slice(1)}</span>
              </CardTitle>
              <div className="flex items-center gap-4">
                <Badge variant="outline" className="font-mono">
                  <Clock className="h-3 w-3 mr-1" />
                  {formatElapsedTime(elapsedTime)}
                </Badge>
                <Badge variant="outline">
                  {status.progress}%
                </Badge>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Progress Bar */}
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-600">
                <span>{status.current_step}</span>
                <span>{status.progress}%</span>
              </div>
              <Progress value={status.progress} className="h-3" />
            </div>

            {/* Live Messages */}
            <div className="bg-white rounded-lg p-4 border">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <MessageSquare className="h-4 w-4 text-gray-500" />
                  <span className="text-sm font-medium">Live Updates</span>
                  <Badge variant="secondary" className="text-xs">
                    {status.messages.length} messages
                  </Badge>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setAutoScroll(!autoScroll)}
                  className="text-xs"
                >
                  {autoScroll ? 'Auto-scroll: ON' : 'Auto-scroll: OFF'}
                </Button>
              </div>
              <ScrollArea 
                className="h-64 border rounded-md bg-gray-50 p-2"
                ref={scrollAreaRef}
              >
                <div className="space-y-1">
                  {status.messages.map((msg, idx) => (
                    <div 
                      key={`${msg.time}-${idx}`} 
                      className="flex gap-2 text-sm py-1 px-2 hover:bg-white rounded transition-colors"
                    >
                      <span className="text-gray-400 font-mono text-xs flex-shrink-0">
                        {new Date(msg.time).toLocaleTimeString()}
                      </span>
                      <span className="text-gray-700 break-words">{msg.text}</span>
                    </div>
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              </ScrollArea>
              {status.messages.length > 10 && (
                <div className="mt-2 text-xs text-gray-500 text-center">
                  Scroll up to see earlier messages
                </div>
              )}
            </div>

            {/* Error Display */}
            {status.error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{status.error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      )}

      {/* Results Panel */}
      {showResult && result && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Reorganization Results
            </CardTitle>
            <CardDescription>
              Review the AI-generated recommendations for your tag system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="stats" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="stats">Statistics</TabsTrigger>
                <TabsTrigger value="merges">Merge Groups</TabsTrigger>
                <TabsTrigger value="hierarchy">Hierarchy</TabsTrigger>
                <TabsTrigger value="entities">Entity Types</TabsTrigger>
              </TabsList>

              <TabsContent value="stats" className="space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">{result?.stats?.total_tags || 0}</div>
                      <p className="text-xs text-gray-500">Total Tags</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">{result?.stats?.unique_concepts || 0}</div>
                      <p className="text-xs text-gray-500">Unique Concepts</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">{result?.stats?.merge_groups || 0}</div>
                      <p className="text-xs text-gray-500">Merge Groups</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">{result?.stats?.hierarchy_levels || 0}</div>
                      <p className="text-xs text-gray-500">Hierarchy Levels</p>
                    </CardContent>
                  </Card>
                </div>
              </TabsContent>

              <TabsContent value="merges" className="space-y-2">
                <ScrollArea className="h-96">
                  {result?.merge_groups?.map((group, idx) => (
                    <Card key={idx} className="mb-2">
                      <CardContent className="p-4">
                        <div 
                          className="flex items-center gap-2 cursor-pointer"
                          onClick={() => toggleGroup(idx)}
                        >
                          {expandedGroups.has(idx) ? 
                            <ChevronDown className="h-4 w-4" /> : 
                            <ChevronRight className="h-4 w-4" />
                          }
                          <GitMerge className="h-4 w-4 text-blue-500" />
                          <span className="font-medium">{group.suggested}</span>
                          <Badge variant="secondary" className="ml-auto">
                            {group.tags.length} tags
                          </Badge>
                        </div>
                        {expandedGroups.has(idx) && (
                          <div className="mt-3 pl-6 space-y-1">
                            {group.tags.map((tag, tagIdx) => (
                              <div key={tagIdx} className="flex items-center gap-2">
                                <Hash className="h-3 w-3 text-gray-400" />
                                <span className="text-sm text-gray-600">{tag}</span>
                              </div>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </ScrollArea>
              </TabsContent>

              <TabsContent value="hierarchy" className="space-y-2">
                <ScrollArea className="h-96">
                  {Object.entries(result?.hierarchy || {}).map(([parent, children]) => (
                    <Card key={parent} className="mb-2">
                      <CardContent className="p-4">
                        <div className="flex items-center gap-2 mb-2">
                          <Layers className="h-4 w-4 text-indigo-500" />
                          <span className="font-medium">{parent}</span>
                        </div>
                        <div className="pl-6 space-y-1">
                          {children.map((child, idx) => (
                            <div key={idx} className="flex items-center gap-2">
                              <ChevronRight className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600">{child}</span>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </ScrollArea>
              </TabsContent>

              <TabsContent value="entities" className="space-y-2">
                <ScrollArea className="h-96">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                    {Object.entries(result?.entity_types || {}).map(([entity, type]) => (
                      <div key={entity} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span className="font-medium">{entity}</span>
                        <Badge variant={
                          type === 'person' ? 'default' :
                          type === 'organisation' ? 'secondary' :
                          type === 'product' ? 'outline' : 'default'
                        }>
                          {type}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </TabsContent>
            </Tabs>
          </CardContent>
          <CardFooter>
            <div className="flex gap-3">
              <Button 
                variant="default" 
                className="flex items-center gap-2"
                onClick={() => applyRecommendations(false)}
                disabled={applyingRecommendations || !result}
              >
                {applyingRecommendations ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Applying...
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-4 w-4" />
                    Apply Basic
                  </>
                )}
              </Button>
              <Button 
                variant="destructive" 
                className="flex items-center gap-2"
                onClick={() => applyRecommendations(true)}
                disabled={applyingRecommendations || !result}
              >
                {applyingRecommendations ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Reorganizing...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4" />
                    Apply COMPREHENSIVE
                  </>
                )}
              </Button>
              <Button 
                variant="outline" 
                className="flex items-center gap-2"
                onClick={() => {
                  const dataStr = JSON.stringify(result, null, 2)
                  const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr)
                  const exportFileDefaultName = `tag-reorganization-${new Date().toISOString().split('T')[0]}.json`
                  const linkElement = document.createElement('a')
                  linkElement.setAttribute('href', dataUri)
                  linkElement.setAttribute('download', exportFileDefaultName)
                  linkElement.click()
                }}
                disabled={!result}
              >
                <Download className="h-4 w-4" />
                Export Report
              </Button>
            </div>
          </CardFooter>
        </Card>
      )}
    </div>
  )
}