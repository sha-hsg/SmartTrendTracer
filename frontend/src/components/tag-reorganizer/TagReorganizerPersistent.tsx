import { useState, useEffect, useRef } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import http from '@/services/http'
import { API_BASE_URL } from '@/config/api'
import {
  Play,
  RotateCcw,
  Pause,
  History,
  AlertCircle,
  Info
} from 'lucide-react'
import {
  HistoryPanel,
  ProgressDisplay,
  ResultDisplay,
  calculateEstimatedTime,
  formatMinutes
} from '.'
import type { Task } from '.'

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

  // Load task history on mount and get total tag count
  useEffect(() => {
    loadTaskHistory()
    fetchTagCount()

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
      const response = await http.get(`/api/tags/reorganize/debug/current-concepts`)
      const total = response.data.total_concepts || 0
      setTotalTags(total)
      setEstimatedMinutes(calculateEstimatedTime(total, mode))
    } catch (err) {
      console.error('Failed to fetch tag count:', err)
    }
  }

  const loadTaskHistory = async () => {
    try {
      const response = await http.get(`/api/tags/reorganize/history`)
      setTaskHistory(response.data.tasks)
    } catch (err) {
      console.error('Failed to load task history:', err)
    }
  }

  const recoverTask = async (recoveryTaskId: string) => {
    try {
      const response = await http.get(`/api/tags/reorganize/recover/${recoveryTaskId}`)

      if (response.data.status === 'active') {
        const task = response.data.task
        setTaskId(recoveryTaskId)
        setIsRunning(true)
        setTaskStatus(task)

        if (task.created_at || task.start_time) {
          const taskStartTime = new Date(task.created_at || task.start_time)
          setStartTime(taskStartTime)

          const now = new Date()
          const elapsed = Math.floor((now.getTime() - taskStartTime.getTime()) / 1000)
          setElapsedSeconds(elapsed)

          if (task.metadata?.concepts_count) {
            setTotalTags(task.metadata.concepts_count)
            const taskMode = task.mode || 'gpt5'
            setMode(taskMode as 'comprehensive' | 'gpt5')
            setEstimatedMinutes(calculateEstimatedTime(task.metadata.concepts_count, taskMode))
          } else {
            fetchTagCount()
          }
        }

        startListening(recoveryTaskId)
      } else if (response.data.status === 'recovered') {
        const task = response.data.task
        setSelectedHistoryTask(task)

        if (task.status === 'processing' || task.status === 'completed') {
          if (task.created_at && task.completed_at) {
            const start = new Date(task.created_at)
            const end = new Date(task.completed_at)
            const elapsed = Math.floor((end.getTime() - start.getTime()) / 1000)
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
    setEstimatedMinutes(calculateEstimatedTime(totalTags, mode))

    try {
      const response = await http.post(`/api/tags/reorganize/start`, null, {
        params: {
          mode,
          model: mode === 'gpt5' ? selectedModel : undefined
        }
      })

      const { task_id } = response.data
      setTaskId(task_id)
      localStorage.setItem('lastReorganizationTaskId', task_id)
      startListening(task_id)
      loadTaskHistory()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message)
      setIsRunning(false)
      setStartTime(null)
    }
  }

  const startListening = (listenTaskId: string) => {
    const eventSource = new EventSource(`${API_BASE_URL}/api/tags/reorganize/stream/${listenTaskId}`)
    eventSourceRef.current = eventSource

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data)
      setTaskStatus(data)

      if (data.status === 'completed') {
        setIsRunning(false)
        setStartTime(null)
        fetchResult(listenTaskId)
        eventSource.close()
        loadTaskHistory()
        localStorage.removeItem('lastReorganizationTaskId')
      } else if (data.status === 'failed') {
        setIsRunning(false)
        setStartTime(null)
        setError(data.error || 'Task failed')
        eventSource.close()
        loadTaskHistory()
        localStorage.removeItem('lastReorganizationTaskId')
      }
    }

    eventSource.onerror = () => {
      eventSource.close()
      setIsRunning(false)
      setError('Connection to server lost. Task may still be running.')
      loadTaskHistory()
    }
  }

  const cancelReorganization = async () => {
    if (!taskId) return

    try {
      await http.post(`/api/tags/reorganize/cancel/${taskId}`)

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
      const response = await http.get(`/api/tags/reorganize/result/${id}`)
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

      const payload = applyTaskId ? {} : (result || selectedHistoryTask?.result)
      const response = await http.post(`${endpoint}`, payload)

      if (response.data.success) {
        const stats = response.data.stats || {}
        const message = `Reorganization applied successfully!\n\n` +
          `${stats.concepts_updated || 0} concepts updated\n` +
          `${stats.hierarchy_links || 0} hierarchy links established\n` +
          `${stats.concepts_created || 0} new concepts created\n\n` +
          `Please refresh the Tag Ontology view to see the organized hierarchy.`

        alert(message)
        setShowResult(false)
        setResult(null)
        setSelectedHistoryTask(null)
        localStorage.removeItem('lastReorganizationTaskId')
        loadTaskHistory()

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
            <HistoryPanel
              taskHistory={taskHistory}
              showHistory={showHistory}
              selectedHistoryTask={selectedHistoryTask}
              onSelectTask={selectHistoryTask}
              onApplyHistoryTask={(id) => applyReorganization(id)}
            />

            {/* Mode Selection and Time Estimate */}
            <div className="space-y-3">
              <div className="flex items-center gap-4">
                <label className="text-sm font-medium">Mode:</label>
                <select
                  value={mode}
                  onChange={(e) => {
                    const newMode = e.target.value as 'comprehensive' | 'gpt5'
                    setMode(newMode)
                    setEstimatedMinutes(calculateEstimatedTime(totalTags, newMode))
                  }}
                  disabled={isRunning}
                  className="px-3 py-1 border rounded-md"
                >
                  <option value="comprehensive">Comprehensive (Fast)</option>
                  <option value="gpt5">AI-Powered (LLM)</option>
                </select>

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
                        Formula: Time = (Tags / 75) + 2 minutes
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
            <ProgressDisplay
              taskStatus={taskStatus}
              isRunning={isRunning}
              elapsedSeconds={elapsedSeconds}
              estimatedMinutes={estimatedMinutes}
            />

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
              <ResultDisplay
                result={result}
                taskId={taskId}
                taskStatus={taskStatus}
                onApply={() => applyReorganization()}
                onReviewLater={() => setShowResult(false)}
              />
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
