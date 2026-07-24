import { useState, useRef, useEffect, useCallback } from 'react'
import axios from 'axios'

export interface BatchResult {
  status: 'idle' | 'running' | 'completed' | 'error'
  newTagsCount?: number
  skippedCount?: number
  errorCount?: number
  message?: string
}

export interface AnnotateAllProgress {
  processed: number
  total: number
  newTagsCount: number
  progress: number
}

export interface AnnotateAllResult {
  status: 'idle' | 'running' | 'completed' | 'cancelled' | 'error'
  message?: string
  newTagsCount?: number
  skippedCount?: number
  errorCount?: number
}

export interface UseBatchAnnotationReturn {
  batchAnnotating: boolean
  batchProgress: number
  batchModel: string
  setBatchModel: (model: string) => void
  batchResult: BatchResult
  annotateAllRunning: boolean
  annotateAllProgress: AnnotateAllProgress
  annotateAllResult: AnnotateAllResult
  handleBatchAnnotate: (tweetIds: string[]) => Promise<void>
  handleAnnotateAll: () => Promise<void>
  handleCancelAnnotateAll: () => Promise<void>
}

export function useBatchAnnotation(onRefresh: () => void): UseBatchAnnotationReturn {
  const [batchAnnotating, setBatchAnnotating] = useState(false)
  const [_batchTaskId, setBatchTaskId] = useState<string | null>(null)
  const [batchProgress, setBatchProgress] = useState(0)
  const [batchModel, setBatchModel] = useState<string>('')
  const [batchResult, setBatchResult] = useState<BatchResult>({ status: 'idle' })
  const batchPollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const [annotateAllRunning, setAnnotateAllRunning] = useState(false)
  const [annotateAllTaskId, setAnnotateAllTaskId] = useState<string | null>(null)
  const [annotateAllProgress, setAnnotateAllProgress] = useState<AnnotateAllProgress>(
    { processed: 0, total: 0, newTagsCount: 0, progress: 0 }
  )
  const [annotateAllResult, setAnnotateAllResult] = useState<AnnotateAllResult>({ status: 'idle' })
  const annotateAllPollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const annotateAllActiveRef = useRef(false)

  const resetAnnotateAllState = useCallback(() => {
    if (annotateAllPollingRef.current) {
      clearInterval(annotateAllPollingRef.current)
      annotateAllPollingRef.current = null
    }
    setAnnotateAllRunning(false)
    setAnnotateAllTaskId(null)
    annotateAllActiveRef.current = false
    localStorage.removeItem('annotateAllProgress')
  }, [])

  const pollAnnotateAllStatus = useCallback((taskId: string) => {
    if (annotateAllPollingRef.current) {
      clearInterval(annotateAllPollingRef.current)
    }

    annotateAllPollingRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`/api/tweets/batch-annotate/${taskId}/status`)
        const status = response.data

        setAnnotateAllProgress({
          processed: status.processed,
          total: status.total,
          newTagsCount: status.new_tags_count,
          progress: status.progress,
        })

        localStorage.setItem('annotateAllProgress', JSON.stringify({
          taskId,
          total: status.total,
          isRunning: status.status === 'running',
          processed: status.processed,
          newTagsCount: status.new_tags_count,
          progress: status.progress,
        }))

        if (status.status === 'completed' || status.status === 'cancelled') {
          resetAnnotateAllState()

          setAnnotateAllResult({
            status: status.status === 'cancelled' ? 'cancelled' : 'completed',
            newTagsCount: status.new_tags_count,
            skippedCount: status.skipped_count,
            errorCount: status.error_count,
            message: status.status === 'cancelled' ? 'Annotation cancelled' : undefined,
          })

          onRefresh()
          setTimeout(() => setAnnotateAllResult({ status: 'idle' }), 10000)
        }
      } catch (error: any) {
        console.error('Error polling annotate-all status:', error)
        if (error.response?.status === 404) {
          resetAnnotateAllState()
          setAnnotateAllResult({
            status: 'completed',
            message: 'Annotation task finished (backend was restarted)',
          })
          onRefresh()
          setTimeout(() => setAnnotateAllResult({ status: 'idle' }), 10000)
        }
      }
    }, 3000)
  }, [onRefresh, resetAnnotateAllState])

  const pollBatchStatus = useCallback((taskId: string) => {
    if (batchPollingRef.current) {
      clearInterval(batchPollingRef.current)
    }

    batchPollingRef.current = setInterval(async () => {
      try {
        const response = await axios.get(`/api/tweets/batch-annotate/${taskId}/status`)
        const status = response.data

        setBatchProgress(status.progress)

        if (status.status === 'completed') {
          if (batchPollingRef.current) {
            clearInterval(batchPollingRef.current)
            batchPollingRef.current = null
          }

          setBatchAnnotating(false)
          setBatchTaskId(null)
          setBatchResult({
            status: 'completed',
            newTagsCount: status.new_tags_count,
            skippedCount: status.skipped_count,
            errorCount: status.error_count
          })

          onRefresh()

          setTimeout(() => {
            setBatchResult({ status: 'idle' })
          }, 10000)
        }
      } catch (error: any) {
        console.error('Error polling batch status:', error)
        if (error.response?.status === 404) {
          if (batchPollingRef.current) {
            clearInterval(batchPollingRef.current)
            batchPollingRef.current = null
          }
          setBatchAnnotating(false)
          setBatchTaskId(null)
          setBatchResult({
            status: 'completed',
            message: 'Annotation task finished (backend was restarted)',
          })
          onRefresh()
          setTimeout(() => setBatchResult({ status: 'idle' }), 10000)
        }
      }
    }, 2000)
  }, [onRefresh])

  // Resume "Annotate All" from localStorage on mount + cleanup polling on unmount
  useEffect(() => {
    const saved = localStorage.getItem('annotateAllProgress')
    if (saved) {
      try {
        const parsed = JSON.parse(saved)
        if (parsed.taskId && parsed.isRunning) {
          setAnnotateAllTaskId(parsed.taskId)
          setAnnotateAllRunning(true)
          setAnnotateAllProgress({
            processed: parsed.processed || 0,
            total: parsed.total || 0,
            newTagsCount: parsed.newTagsCount || 0,
            progress: parsed.progress || 0,
          })
          setAnnotateAllResult({ status: 'running' })
          pollAnnotateAllStatus(parsed.taskId)
        }
      } catch {
        localStorage.removeItem('annotateAllProgress')
      }
    }

    return () => {
      if (batchPollingRef.current) {
        clearInterval(batchPollingRef.current)
      }
      if (annotateAllPollingRef.current) {
        clearInterval(annotateAllPollingRef.current)
      }
    }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const handleBatchAnnotate = useCallback(async (tweetIds: string[]) => {
    if (!batchModel) {
      setBatchResult({
        status: 'error',
        message: 'Please select a model first'
      })
      return
    }

    if (tweetIds.length === 0) {
      setBatchResult({
        status: 'error',
        message: 'No tweets to annotate'
      })
      return
    }

    setBatchAnnotating(true)
    setBatchProgress(0)
    setBatchResult({ status: 'running' })

    try {
      const response = await axios.post(`/api/tweets/batch-annotate`, {
        tweet_ids: tweetIds,
        model: batchModel
      })

      setBatchTaskId(response.data.task_id)
      pollBatchStatus(response.data.task_id)
    } catch (error: any) {
      console.error('Error starting batch annotation:', error)
      setBatchAnnotating(false)
      setBatchResult({
        status: 'error',
        message: error.response?.data?.detail || 'Failed to start batch annotation'
      })
    }
  }, [batchModel, pollBatchStatus])

  const handleAnnotateAll = useCallback(async () => {
    if (!batchModel) {
      setAnnotateAllResult({ status: 'error', message: 'Please select a model first' })
      return
    }
    if (annotateAllActiveRef.current) return
    annotateAllActiveRef.current = true

    setAnnotateAllRunning(true)
    setAnnotateAllProgress({ processed: 0, total: 0, newTagsCount: 0, progress: 0 })
    setAnnotateAllResult({ status: 'running' })

    try {
      const response = await axios.post(`/api/tweets/batch-annotate-all`, {
        model: batchModel
      })

      if (!response.data.task_id) {
        setAnnotateAllRunning(false)
        annotateAllActiveRef.current = false
        setAnnotateAllResult({ status: 'completed', message: response.data.message, newTagsCount: 0 })
        setTimeout(() => setAnnotateAllResult({ status: 'idle' }), 10000)
        return
      }

      const taskId = response.data.task_id
      setAnnotateAllTaskId(taskId)
      setAnnotateAllProgress(prev => ({ ...prev, total: response.data.total }))

      localStorage.setItem('annotateAllProgress', JSON.stringify({
        taskId,
        total: response.data.total,
        isRunning: true,
        processed: 0,
        newTagsCount: 0,
        progress: 0,
      }))

      pollAnnotateAllStatus(taskId)
    } catch (error: any) {
      console.error('Error starting annotate-all:', error)
      setAnnotateAllRunning(false)
      annotateAllActiveRef.current = false
      setAnnotateAllResult({
        status: 'error',
        message: error.response?.data?.detail || 'Failed to start annotation'
      })
    }
  }, [batchModel, pollAnnotateAllStatus])

  const handleCancelAnnotateAll = useCallback(async () => {
    if (!annotateAllTaskId) return
    try {
      await axios.post(`/api/tweets/batch-annotate/${annotateAllTaskId}/cancel`)
    } catch (error) {
      console.error('Error cancelling annotation:', error)
    }
  }, [annotateAllTaskId])

  return {
    batchAnnotating,
    batchProgress,
    batchModel,
    setBatchModel,
    batchResult,
    annotateAllRunning,
    annotateAllProgress,
    annotateAllResult,
    handleBatchAnnotate,
    handleAnnotateAll,
    handleCancelAnnotateAll,
  }
}
