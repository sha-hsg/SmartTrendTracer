/**
 * useModelSelector Hook
 *
 * Custom React hook for managing LLM model selection with backend integration.
 *
 * Features:
 * - Fetches default model and user preferences from backend
 * - Manages model selection state
 * - Persists preferences to backend API
 * - Handles loading and error states
 * - Provides methods to reset to default
 *
 * Usage:
 * ```tsx
 * const {
 *   selectedModel,
 *   availableModels,
 *   loading,
 *   error,
 *   selectModel,
 *   resetToDefault
 * } = useModelSelector('tag_suggestion')
 * ```
 */

import { useState, useEffect, useCallback } from 'react'

interface ModelInfo {
  model: string
  provider: string
  temperature?: number
  max_tokens?: number
}

interface TaskInfo {
  task_type: string
  model: string
  provider: string
  temperature?: number
  max_tokens?: number
}

interface UseModelSelectorReturn {
  /** Currently selected model */
  selectedModel: string | null

  /** Available models for this task */
  availableModels: ModelInfo[]

  /** Default model info */
  defaultModel: TaskInfo | null

  /** User's saved preference (null if using default) */
  userPreference: string | null

  /** Loading state */
  loading: boolean

  /** Error message if any */
  error: string | null

  /** Saving state (when persisting preference) */
  saving: boolean

  /** Select a model and persist to backend */
  selectModel: (model: string) => Promise<void>

  /** Reset to default model */
  resetToDefault: () => Promise<void>

  /** Refresh data from backend */
  refresh: () => Promise<void>
}

export function useModelSelector(
  taskType: string,
  userId: string = 'default'
): UseModelSelectorReturn {
  const [selectedModel, setSelectedModel] = useState<string | null>(null)
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([])
  const [defaultModel, setDefaultModel] = useState<TaskInfo | null>(null)
  const [userPreference, setUserPreference] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  // Fetch all data from backend
  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch in parallel for performance
      const [taskRes, modelsRes, prefsRes] = await Promise.all([
        fetch(`http://localhost:8000/api/llm/tasks/${taskType}`),
        fetch('http://localhost:8000/api/llm/models'),
        fetch(`http://localhost:8000/api/llm/preferences?user_id=${userId}`)
      ])

      // Check responses
      if (!taskRes.ok) {
        throw new Error(`Task type '${taskType}' not found`)
      }
      if (!modelsRes.ok) {
        throw new Error('Failed to fetch available models')
      }

      // Parse responses
      const taskData: TaskInfo = await taskRes.json()
      const modelsData = await modelsRes.json()
      const prefsData = prefsRes.ok ? await prefsRes.json() : {}

      // Set state
      setDefaultModel(taskData)
      setAvailableModels(modelsData[taskType] || [])

      const pref = prefsData[taskType]
      setUserPreference(pref || null)

      // Set selected model (preference > default)
      setSelectedModel(pref || taskData.model)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load model data'
      setError(errorMessage)
      console.error('useModelSelector error:', err)
    } finally {
      setLoading(false)
    }
  }, [taskType, userId])

  // Load data on mount and when dependencies change
  useEffect(() => {
    fetchData()
  }, [fetchData])

  // Select a model and save to backend
  const selectModel = useCallback(async (model: string) => {
    setSaving(true)
    setError(null)

    try {
      const response = await fetch(`http://localhost:8000/api/llm/preferences?user_id=${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          task_type: taskType,
          model_name: model
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to save preference')
      }

      // Update local state
      setSelectedModel(model)
      setUserPreference(model)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to save preference'
      setError(errorMessage)
      throw err  // Re-throw so caller can handle
    } finally {
      setSaving(false)
    }
  }, [taskType, userId])

  // Reset to default model
  const resetToDefault = useCallback(async () => {
    if (!defaultModel) {
      setError('No default model available')
      return
    }

    setSaving(true)
    setError(null)

    try {
      const response = await fetch(
        `http://localhost:8000/api/llm/preferences/${taskType}?user_id=${userId}`,
        { method: 'DELETE' }
      )

      if (!response.ok) {
        throw new Error('Failed to reset preference')
      }

      // Update local state
      setSelectedModel(defaultModel.model)
      setUserPreference(null)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to reset preference'
      setError(errorMessage)
      throw err
    } finally {
      setSaving(false)
    }
  }, [taskType, userId, defaultModel])

  return {
    selectedModel,
    availableModels,
    defaultModel,
    userPreference,
    loading,
    error,
    saving,
    selectModel,
    resetToDefault,
    refresh: fetchData
  }
}

/**
 * useMultiModelSelector Hook
 *
 * Manage model selection for multiple tasks simultaneously.
 * Useful for forms that need model selection across different operations.
 *
 * Usage:
 * ```tsx
 * const {
 *   models,
 *   loading,
 *   selectModel,
 *   resetAll
 * } = useMultiModelSelector(['tag_suggestion', 'entity_extraction', 'summarization'])
 * ```
 */
export function useMultiModelSelector(taskTypes: string[], userId: string = 'default') {
  const [models, setModels] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch all preferences
  useEffect(() => {
    const fetchPreferences = async () => {
      setLoading(true)
      setError(null)

      try {
        const response = await fetch(`http://localhost:8000/api/llm/preferences?user_id=${userId}`)
        if (!response.ok) {
          throw new Error('Failed to fetch preferences')
        }

        const prefs = await response.json()

        // For each task type, use preference or fetch default
        const modelPromises = taskTypes.map(async (taskType) => {
          if (prefs[taskType]) {
            return [taskType, prefs[taskType]]
          }

          // Fetch default
          const taskRes = await fetch(`http://localhost:8000/api/llm/tasks/${taskType}`)
          if (taskRes.ok) {
            const taskData = await taskRes.json()
            return [taskType, taskData.model]
          }

          return [taskType, null]
        })

        const results = await Promise.all(modelPromises)
        const modelsMap = Object.fromEntries(results.filter(([_, model]) => model !== null))

        setModels(modelsMap)

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load preferences')
      } finally {
        setLoading(false)
      }
    }

    fetchPreferences()
  }, [taskTypes, userId])

  // Select model for a specific task
  const selectModel = useCallback(async (taskType: string, model: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/llm/preferences?user_id=${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          task_type: taskType,
          model_name: model
        })
      })

      if (!response.ok) {
        throw new Error('Failed to save preference')
      }

      setModels(prev => ({
        ...prev,
        [taskType]: model
      }))

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save preference')
      throw err
    }
  }, [userId])

  // Reset all to defaults
  const resetAll = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/llm/preferences?user_id=${userId}`, {
        method: 'DELETE'
      })

      if (!response.ok) {
        throw new Error('Failed to reset preferences')
      }

      // Reload defaults
      const defaults: Record<string, string> = {}
      for (const taskType of taskTypes) {
        const taskRes = await fetch(`http://localhost:8000/api/llm/tasks/${taskType}`)
        if (taskRes.ok) {
          const taskData = await taskRes.json()
          defaults[taskType] = taskData.model
        }
      }

      setModels(defaults)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset preferences')
      throw err
    }
  }, [taskTypes, userId])

  return {
    models,
    loading,
    error,
    selectModel,
    resetAll
  }
}
