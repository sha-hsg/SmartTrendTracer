import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Progress } from '@/components/ui/progress'
import axios from 'axios'
import { 
  Play, 
  Pause, 
  RotateCcw, 
  CheckCircle, 
  XCircle, 
  Clock,
  History,
  Download,
  AlertCircle,
  Timer,
  Info,
  FileText
} from 'lucide-react'

interface Task {
  task_id: string
  status: string
  mode: string
  created_at: string
  updated_at: string
  completed_at?: string
  progress: {
    current: number
    total: number
    current_step: string
    messages: Array<{time: string, text: string}>
  }
  result?: any
  error?: string
  metadata?: any
}

export default function TagReorganizerPersistent() {
  const [isRunning, setIsRunning] = useState(false)
  const [taskId, setTaskId] = useState<string | null>(null)
  const [taskStatus, setTaskStatus] = useState<any>(null)
  const [result, setResult] = useState<any>(null)
  const [error, setError] = useState<string | null>(null)
  const [showResult, setShowResult] = useState(false)
  const [mode, setMode] = useState<'comprehensive' | 'gpt5'>('gpt5')
  const [selectedModel, setSelectedModel] = useState<'gemini' | 'gpt5'>('gemini')
  
  // Task history
  const [taskHistory, setTaskHistory] = useState<Task[]>([])
  const [showHistory, setShowHistory] = useState(false)
  const [selectedHistoryTask, setSelectedHistoryTask] = useState<Task | null>(null)
  
  // Time estimation
  const [estimatedMinutes, setEstimatedMinutes] = useState<number>(0)
  const [startTime, setStartTime] = useState<Date | null>(null)
  const [elapsedSeconds, setElapsedSeconds] = useState<number>(0)
  const [totalTags, setTotalTags] = useState<number>(0)
  
  const eventSourceRef = useRef<EventSource | null>(null)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  
  // Time estimation formula
  const calculateEstimatedTime = (tagCount: number, mode: 'comprehensive' | 'gpt5'): number => {
    if (mode === 'comprehensive') {
      // Rule-based processing is very fast
      return 0.5 // 30 seconds
    } else {
      // GPT-5 processing formula: Time (minutes) ≈ (Number_of_Tags / 75) + 2
      return Math.ceil((tagCount / 75) + 2)
    }
  }
  
  // Format time display
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }
  
  const formatMinutes = (minutes: number): string => {
    if (minutes < 1) return 'less than a minute'
    if (minutes === 1) return '1 minute'
    if (minutes < 60) return `${minutes} minutes`
    const hours = Math.floor(minutes / 60)
    const mins = minutes % 60
    if (hours === 1 && mins === 0) return '1 hour'
    if (hours === 1) return `1 hour ${mins} minutes`
    if (mins === 0) return `${hours} hours`
    return `${hours} hours ${mins} minutes`
  }

  // Load task history on mount and get total tag count
  useEffect(() => {
    loadTaskHistory()
    fetchTagCount()
    
    // Check localStorage for last task ID
    const lastTaskId = localStorage.getItem('lastReorganizationTaskId')
    if (lastTaskId) {
      recoverTask(lastTaskId)
    }
  }, [])
  
  // Update estimation when mode or tag count changes
  useEffect(() => {
    if (totalTags > 0 && !isRunning) {
      setEstimatedMinutes(calculateEstimatedTime(totalTags, mode))
    }
  }, [mode, totalTags, isRunning])
  
  // Timer effect
  useEffect(() => {
    if (isRunning && startTime) {
      timerRef.current = setInterval(() => {
        const now = new Date()
        const elapsed = Math.floor((now.getTime() - startTime.getTime()) / 1000)
        setElapsedSeconds(elapsed)
      }, 1000)
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current)
        timerRef.current = null
      }
    }
    
    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
    }
  }, [isRunning, startTime])
  
  const fetchTagCount = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tags/reorganize/debug/current-concepts')
      const total = response.data.total_concepts || 0
      setTotalTags(total)
      // Pre-calculate estimation based on current mode
      setEstimatedMinutes(calculateEstimatedTime(total, mode))
    } catch (err) {
      console.error('Failed to fetch tag count:', err)
    }
  }

  const loadTaskHistory = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/tags/reorganize/history')
      setTaskHistory(response.data.tasks)
    } catch (err) {
      console.error('Failed to load task history:', err)
    }
  }

  const recoverTask = async (recoveryTaskId: string) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/tags/reorganize/recover/${recoveryTaskId}`)
      
      if (response.data.status === 'active') {
        // Task is still running - recover timer state
        const task = response.data.task
        setTaskId(recoveryTaskId)
        setIsRunning(true)
        setTaskStatus(task)
        
        // Recover timer state from task creation time
        if (task.created_at || task.start_time) {
          const taskStartTime = new Date(task.created_at || task.start_time)
          setStartTime(taskStartTime)
          
          // Calculate elapsed time since task started
          const now = new Date()
          const elapsed = Math.floor((now.getTime() - taskStartTime.getTime()) / 1000)
          setElapsedSeconds(elapsed)
          
          // Estimate total time based on mode and tag count
          // First try to get from task metadata, otherwise fetch
          if (task.metadata?.concepts_count) {
            setTotalTags(task.metadata.concepts_count)
            const taskMode = task.mode || 'gpt5'
            setMode(taskMode as 'comprehensive' | 'gpt5')
            setEstimatedMinutes(calculateEstimatedTime(task.metadata.concepts_count, taskMode))
          } else {
            // Fetch current tag count if not in task metadata
            fetchTagCount()
          }
        }
        
        startListening(recoveryTaskId)
      } else if (response.data.status === 'recovered') {
        // Task was completed or interrupted
        const task = response.data.task
        setSelectedHistoryTask(task)
        
        // If task was processing, restore timer state for display
        if (task.status === 'processing' || task.status === 'completed') {
          if (task.created_at && task.completed_at) {
            const startTime = new Date(task.created_at)
            const endTime = new Date(task.completed_at)
            const elapsed = Math.floor((endTime.getTime() - startTime.getTime()) / 1000)
            setElapsedSeconds(elapsed)
          } else if (task.metadata?.processing_time_seconds) {
            setElapsedSeconds(Math.floor(task.metadata.processing_time_seconds))
          }
        }
        
        if (task.status === 'completed' && task.result) {
          setResult(task.result)
          setShowResult(true)
          
          if (response.data.can_apply) {
            setError(null)
            // Show message that results can be applied
            alert('Previous reorganization results recovered! You can now review and apply them.')
          }
        } else if (task.status === 'interrupted') {
          setError('This task was interrupted by a server restart. Please start a new reorganization.')
        }
      }
    } catch (err) {
      console.error('Failed to recover task:', err)
      localStorage.removeItem('lastReorganizationTaskId')
    }
  }

  const startReorganization = async () => {
    setError(null)
    setIsRunning(true)
    setResult(null)
    setShowResult(false)
    setStartTime(new Date())
    setElapsedSeconds(0)
    
    // Calculate and set estimated time
    const estimation = calculateEstimatedTime(totalTags, mode)
    setEstimatedMinutes(estimation)
    
    try {
      const response = await axios.post(`http://localhost:8000/api/tags/reorganize/start`, null, {
        params: { 
          mode,
          model: mode === 'gpt5' ? selectedModel : undefined
        }
      })
      
      const { task_id } = response.data
      setTaskId(task_id)
      
      // Store task ID in localStorage
      localStorage.setItem('lastReorganizationTaskId', task_id)
      
      // Start listening to SSE stream
      startListening(task_id)
      
      // Reload history
      loadTaskHistory()
      
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      setIsRunning(false)
      setStartTime(null)
    }
  }

  const startListening = (listenTaskId: string) => {
    const eventSource = new EventSource(`http://localhost:8000/api/tags/reorganize/stream/${listenTaskId}`)
    eventSourceRef.current = eventSource
    
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setTaskStatus(data)
      
      if (data.status === 'completed') {
        setIsRunning(false)
        setStartTime(null)  // Stop the timer
        fetchResult(listenTaskId)
        eventSource.close()
        loadTaskHistory()
        localStorage.removeItem('lastReorganizationTaskId')
      } else if (data.status === 'failed') {
        setIsRunning(false)
        setStartTime(null)  // Stop the timer
        setError(data.error || 'Task failed')
        eventSource.close()
        loadTaskHistory()
        localStorage.removeItem('lastReorganizationTaskId')
      }
    }
    
    eventSource.onerror = (err) => {
      console.error('SSE error:', err)
      eventSource.close()
      setIsRunning(false)
      setError('Connection to server lost. Task may still be running.')
      loadTaskHistory()
    }
  }

  const cancelReorganization = async () => {
    if (!taskId) return
    
    try {
      await axios.post(`http://localhost:8000/api/tags/reorganize/cancel/${taskId}`)
      
      if (eventSourceRef.current) {
        eventSourceRef.current.close()
        eventSourceRef.current = null
      }
      
      setIsRunning(false)
      setTaskId(null)
      setStartTime(null)
      setElapsedSeconds(0)
      localStorage.removeItem('lastReorganizationTaskId')
      loadTaskHistory()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  const fetchResult = async (id: string) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/tags/reorganize/result/${id}`)
      setResult(response.data.result)
      setShowResult(true)
    } catch (err) {
      console.error('Failed to fetch result:', err)
    }
  }

  const applyReorganization = async (applyTaskId?: string) => {
    const targetTaskId = applyTaskId || taskId
    if (!targetTaskId) return
    
    try {
      const endpoint = applyTaskId 
        ? `/api/tags/reorganize/apply-recovered/${applyTaskId}`
        : `/api/tags/reorganize/apply/${targetTaskId}`
        
      // For apply-recovered, don't send the result data since it's already in MongoDB
      const payload = applyTaskId ? {} : (result || selectedHistoryTask?.result)
      const response = await axios.post(`http://localhost:8000${endpoint}`, payload)
      
      if (response.data.success) {
        const stats = response.data.stats || {}
        const message = `Reorganization applied successfully!\n\n` +
          `✅ ${stats.concepts_updated || 0} concepts updated\n` +
          `✅ ${stats.hierarchy_links || 0} hierarchy links established\n` +
          `✅ ${stats.concepts_created || 0} new concepts created\n\n` +
          `Please refresh the Tag Ontology view to see the organized hierarchy.`
        
        alert(message)
        setShowResult(false)
        setResult(null)
        setSelectedHistoryTask(null)
        localStorage.removeItem('lastReorganizationTaskId')
        loadTaskHistory()
        
        // Trigger a refresh of the parent component if possible
        if (window.location.pathname.includes('ontology')) {
          window.location.reload()
        }
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
    }
  }

  const selectHistoryTask = (task: Task) => {
    setSelectedHistoryTask(task)
    if (task.result) {
      setResult(task.result)
      setShowResult(true)
    }
    setShowHistory(false)
  }

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      'completed': { color: 'bg-green-500', icon: CheckCircle },
      'failed': { color: 'bg-red-500', icon: XCircle },
      'processing': { color: 'bg-blue-500', icon: RotateCcw },
      'cancelled': { color: 'bg-gray-500', icon: XCircle },
      'interrupted': { color: 'bg-orange-500', icon: AlertCircle },
      'initializing': { color: 'bg-yellow-500', icon: Clock }
    }
    
    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig['initializing']
    const Icon = config.icon
    
    return (
      <Badge className={`${config.color} text-white`}>
        <Icon className="w-3 h-3 mr-1" />
        {status}
      </Badge>
    )
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Tag Reorganizer - Persistent</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowHistory(!showHistory)}
            >
              <History className="w-4 h-4 mr-2" />
              History ({taskHistory.length})
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* History Panel */}
            {showHistory && (
              <Card className="border-blue-200 bg-blue-50/50">
                <CardHeader>
                  <CardTitle className="text-sm">Recent Reorganization Tasks</CardTitle>
                </CardHeader>
                <CardContent>
                  <ScrollArea className="h-48">
                    <div className="space-y-2">
                      {taskHistory.map((task) => (
                        <div
                          key={task.task_id}
                          className="flex items-center justify-between p-2 bg-white rounded cursor-pointer hover:bg-gray-50"
                          onClick={() => selectHistoryTask(task)}
                        >
                          <div className="flex items-center gap-2">
                            {getStatusBadge(task.status)}
                            <span className="text-sm text-gray-600">
                              {new Date(task.created_at).toLocaleString()}
                            </span>
                          </div>
                          {task.status === 'completed' && task.result && (
                            <Button size="sm" variant="outline">
                              View Result
                            </Button>
                          )}
                        </div>
                      ))}
                      {taskHistory.length === 0 && (
                        <div className="text-center text-gray-500 py-4">
                          No previous reorganization tasks
                        </div>
                      )}
                    </div>
                  </ScrollArea>
                </CardContent>
              </Card>
            )}

            {/* Selected History Task */}
            {selectedHistoryTask && (
              <Alert className="border-blue-200 bg-blue-50">
                <AlertDescription>
                  <div className="flex items-center justify-between">
                    <span>
                      Viewing task from {new Date(selectedHistoryTask.created_at).toLocaleString()}
                    </span>
                    {selectedHistoryTask.status === 'completed' && selectedHistoryTask.result && (
                      <Button
                        size="sm"
                        onClick={() => applyReorganization(selectedHistoryTask.task_id)}
                      >
                        Apply These Results
                      </Button>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Mode Selection and Time Estimate */}
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium">Mode:</label>
                <select
                  value={mode}
                  onChange={(e) => {
                    const newMode = e.target.value as 'comprehensive' | 'gpt5'
                    setMode(newMode)
                    // Recalculate estimation when mode changes
                    setEstimatedMinutes(calculateEstimatedTime(totalTags, newMode))
                  }}
                  disabled={isRunning}
                  className="px-3 py-1 border rounded-md"
                >
                  <option value="comprehensive">Comprehensive (Fast)</option>
                  <option value="gpt5">AI-Powered (LLM)</option>
                </select>
                
                {/* Model Selection - only show when AI mode is selected */}
                {mode === 'gpt5' && (
                  <select
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value as 'gemini' | 'gpt5')}
                    disabled={isRunning}
                    className="ml-2 px-3 py-1 border rounded-md bg-blue-50"
                  >
                    <option value="gemini">Gemini 2.5 Pro</option>
                    <option value="gpt5">GPT-5 (2025-08-07)</option>
                  </select>
                )}
              </div>
              
              {/* Time Estimation Display */}
              {!isRunning && totalTags > 0 && (
                <Alert className="border-blue-200 bg-blue-50">
                  <Info className="h-4 w-4" />
                  <AlertDescription>
                    <div className="flex items-center justify-between">
                      <span className="text-sm">
                        <strong>{totalTags.toLocaleString()} tags</strong> will take approximately{' '}
                        <strong>{formatMinutes(estimatedMinutes)}</strong> to process
                      </span>
                      <span className="text-xs text-gray-500">
                        Formula: Time ≈ (Tags ÷ 75) + 2 minutes
                      </span>
                    </div>
                  </AlertDescription>
                </Alert>
              )}
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
              <Button
                onClick={startReorganization}
                disabled={isRunning}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {isRunning ? (
                  <>
                    <RotateCcw className="w-4 h-4 mr-2 animate-spin" />
                    Running...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    Start Reorganization
                  </>
                )}
              </Button>
              
              {isRunning && (
                <Button
                  onClick={cancelReorganization}
                  variant="outline"
                  className="border-red-500 text-red-500 hover:bg-red-50"
                >
                  <Pause className="w-4 h-4 mr-2" />
                  Cancel
                </Button>
              )}
            </div>

            {/* Progress Display with Timer */}
            {taskStatus && (
              <Card className="bg-gray-50 border-blue-200">
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {/* Timer Section */}
                    {isRunning && (
                      <div className="bg-white rounded-lg p-4 border border-blue-100">
                        <div className="grid grid-cols-3 gap-4 text-center">
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Elapsed Time</div>
                            <div className="text-lg font-mono font-semibold text-blue-600">
                              <Timer className="w-4 h-4 inline mr-1" />
                              {formatTime(elapsedSeconds)}
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Estimated Total</div>
                            <div className="text-lg font-mono font-semibold text-gray-600">
                              <Clock className="w-4 h-4 inline mr-1" />
                              {formatTime(estimatedMinutes * 60)}
                            </div>
                          </div>
                          <div>
                            <div className="text-xs text-gray-500 mb-1">Time Remaining</div>
                            <div className="text-lg font-mono font-semibold text-green-600">
                              {formatTime(Math.max(0, (estimatedMinutes * 60) - elapsedSeconds))}
                            </div>
                          </div>
                        </div>
                        
                        {/* Visual Progress Bar with Time */}
                        <div className="mt-4">
                          <div className="flex justify-between text-xs text-gray-500 mb-1">
                            <span>0:00</span>
                            <span className="font-medium">
                              {Math.round((elapsedSeconds / (estimatedMinutes * 60)) * 100)}% Complete
                            </span>
                            <span>{formatTime(estimatedMinutes * 60)}</span>
                          </div>
                          <Progress 
                            value={Math.min(100, (elapsedSeconds / (estimatedMinutes * 60)) * 100)} 
                            className="h-3"
                          />
                        </div>
                        
                        {/* Warning if taking longer than expected */}
                        {elapsedSeconds > (estimatedMinutes * 60) && (
                          <Alert className="mt-3 border-orange-200 bg-orange-50">
                            <AlertCircle className="h-3 w-3" />
                            <AlertDescription className="text-xs">
                              Taking longer than expected. Complex reorganizations may need extra time.
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    )}
                    
                    {/* Status Section */}
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium">Status:</span>
                        {getStatusBadge(taskStatus.status)}
                      </div>
                      
                      {taskStatus.progress && (
                        <>
                          <div className="flex justify-between text-sm">
                            <span>Progress:</span>
                            <span>{taskStatus.progress.current} / {taskStatus.progress.total || 100}</span>
                          </div>
                          
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-blue-600 h-2 rounded-full transition-all"
                              style={{ 
                                width: `${(taskStatus.progress.current / Math.max(taskStatus.progress.total || 100, 1)) * 100}%` 
                              }}
                            />
                          </div>
                          
                          {taskStatus.progress.current_step && (
                            <div className="text-sm text-gray-600 mt-2">
                              Current: {taskStatus.progress.current_step}
                            </div>
                          )}
                        </>
                      )}
                    
                      {/* Messages */}
                      {taskStatus.progress?.messages && taskStatus.progress.messages.length > 0 && (
                        <div className="mt-4">
                          <div className="text-sm font-medium mb-2">Recent Activity:</div>
                          <ScrollArea className="h-32 bg-white rounded p-2">
                            <div className="space-y-1">
                              {taskStatus.progress.messages.map((msg: any, idx: number) => (
                                <div key={idx} className="text-xs text-gray-600">
                                  <span className="text-gray-400">
                                    {new Date(msg.time).toLocaleTimeString()}:
                                  </span> {msg.text}
                                </div>
                              ))}
                            </div>
                          </ScrollArea>
                        </div>
                      )}
                      
                      {/* Timing Information */}
                      {taskStatus.created_at && (
                        <div className="mt-2 text-sm text-gray-600">
                          <div>Started: {new Date(taskStatus.created_at).toLocaleTimeString()}</div>
                          {taskStatus.completed_at && (
                            <>
                              <div>Completed: {new Date(taskStatus.completed_at).toLocaleTimeString()}</div>
                              <div className="font-medium">
                                Duration: {Math.round((new Date(taskStatus.completed_at).getTime() - new Date(taskStatus.created_at).getTime()) / 1000)} seconds
                              </div>
                            </>
                          )}
                          {!taskStatus.completed_at && taskStatus.status === 'analyzing' && (
                            <div className="text-orange-600">
                              Running for: {Math.round((Date.now() - new Date(taskStatus.created_at).getTime()) / 1000)} seconds
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Error Display */}
            {error && (
              <Alert className="border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>
                  <div className="space-y-2">
                    <div className="font-medium">{error}</div>
                    {taskStatus?.error_details && (
                      <div className="text-sm text-red-600">
                        Details: {taskStatus.error_details}
                      </div>
                    )}
                    {taskStatus?.fallback_used && (
                      <div className="text-sm text-orange-600">
                        Note: System fell back to rule-based reorganization due to AI processing error.
                      </div>
                    )}
                  </div>
                </AlertDescription>
              </Alert>
            )}

            {/* Result Display */}
            {showResult && result && (
              <Card className="border-green-200">
                <CardHeader>
                  <CardTitle className="text-green-700 flex items-center justify-between">
                    <span>Reorganization Complete!</span>
                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          // View raw LLM request/response data
                          const debugData = {
                            request: {
                              model: result.model_used || 'gemini-2.5-pro',
                              concepts_sent: result.stats?.total_tags || result.statistics?.total_tags || 0,
                              prompt_size: result.prompt_size || 'N/A',
                              timestamp: taskStatus?.created_at
                            },
                            response: {
                              concepts_returned: result.stats?.unique_concepts || result.statistics?.new_concepts || 0,
                              aliases_returned: result.aliases?.length || 0,
                              duration: taskStatus?.completed_at && taskStatus?.created_at ? 
                                Math.round((new Date(taskStatus.completed_at).getTime() - new Date(taskStatus.created_at).getTime()) / 1000) + ' seconds' : 'N/A',
                              fallback_used: result.fallback_used || false,
                              error: result.error || null
                            },
                            raw_result: result
                          }
                          const blob = new Blob([JSON.stringify(debugData, null, 2)], { type: 'application/json' })
                          const url = URL.createObjectURL(blob)
                          window.open(url, '_blank')
                        }}
                      >
                        <FileText className="w-4 h-4 mr-2" />
                        View Debug
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `reorganization-${taskId || 'result'}.json`
                          a.click()
                        }}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        Export
                      </Button>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <Alert className="border-green-200 bg-green-50">
                      <CheckCircle className="h-4 w-4" />
                      <AlertDescription>
                        Results are saved and will persist even if you close the browser or the server restarts.
                      </AlertDescription>
                    </Alert>
                    
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Total Concepts:</span> {result.stats?.total_tags || result.statistics?.total_tags || 0}
                      </div>
                      <div>
                        <span className="font-medium">New Concepts:</span> {result.stats?.unique_concepts || result.statistics?.new_concepts || 0}
                      </div>
                      <div>
                        <span className="font-medium">Merged:</span> {result.stats?.merge_groups || result.statistics?.merged_tags || 0}
                      </div>
                      <div>
                        <span className="font-medium">Categories:</span> {result.stats?.hierarchy_levels || result.statistics?.total_categories || 0}
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button
                        onClick={() => applyReorganization()}
                        className="bg-green-600 hover:bg-green-700 text-white"
                      >
                        Apply Reorganization
                      </Button>
                      <Button
                        onClick={() => setShowResult(false)}
                        variant="outline"
                      >
                        Review Later
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}