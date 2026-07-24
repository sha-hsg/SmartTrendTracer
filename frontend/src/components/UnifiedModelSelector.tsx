/**
 * Unified Model Selector Component
 *
 * A reusable component for selecting LLM models for specific tasks.
 * Integrates with the backend LiteLLM Manager API for real-time model selection.
 *
 * Features:
 * - Fetches available models from backend
 * - Shows current default model with provider badge
 * - Allows user to override default with preference
 * - Persists selection to backend
 * - Shows loading and error states
 * - Compact inline design for use in modals/forms
 */

import { useEffect, useState } from 'react'
import { API_BASE_URL } from '@/config/api'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, CheckCircle2, AlertCircle } from 'lucide-react'

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

interface UnifiedModelSelectorProps {
  /** Task type (e.g., "tag_suggestion", "entity_extraction") */
  taskType: string

  /** Current selected model (controlled component) */
  value?: string

  /** Callback when model changes */
  onValueChange?: (model: string) => void

  /** Optional label text */
  label?: string

  /** Optional description */
  description?: string

  /** User ID for preferences (default: "default") */
  userId?: string

  /** Disable the selector */
  disabled?: boolean

  /** Additional className */
  className?: string

  /** Show compact version (minimal) */
  compact?: boolean
}

export default function UnifiedModelSelector({
  taskType,
  value,
  onValueChange,
  label,
  description: _description,
  userId = 'default',
  disabled = false,
  className = '',
  compact = false
}: UnifiedModelSelectorProps) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [taskInfo, setTaskInfo] = useState<TaskInfo | null>(null)
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([])
  const [userPreference, setUserPreference] = useState<string | null>(null)
  const [selectedModel, setSelectedModel] = useState<string>('')

  // Fetch task info and available models
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      setError(null)

      try {
        // Fetch task info (default model)
        const taskRes = await fetch(`${API_BASE_URL}/api/llm/tasks/${taskType}`)
        if (!taskRes.ok) {
          throw new Error(`Task type '${taskType}' not found`)
        }
        const taskData: TaskInfo = await taskRes.json()
        setTaskInfo(taskData)

        // Fetch ALL available models from all tasks
        const modelsRes = await fetch(`${API_BASE_URL}/api/llm/models`)
        if (!modelsRes.ok) {
          throw new Error('Failed to fetch available models')
        }
        const modelsData = await modelsRes.json()

        // Extract ALL unique models from all task types
        const modelMap = new Map<string, ModelInfo>()
        Object.values(modelsData).forEach((models: any) => {
          if (Array.isArray(models)) {
            models.forEach((m: ModelInfo) => {
              if (!modelMap.has(m.model)) {
                modelMap.set(m.model, m)
              }
            })
          }
        })

        // Sort alphabetically by model name
        const allModels = Array.from(modelMap.values()).sort((a, b) =>
          a.model.localeCompare(b.model)
        )

        setAvailableModels(allModels)

        // Fetch user preference
        const prefsRes = await fetch(`${API_BASE_URL}/api/llm/preferences?user_id=${userId}`)
        if (prefsRes.ok) {
          const prefsData = await prefsRes.json()
          const pref = prefsData[taskType]
          setUserPreference(pref || null)

          // Set initial selection (preference > external value > default)
          const initial = pref || value || taskData.model
          setSelectedModel(initial)

          // Notify parent if controlled
          if (onValueChange && initial !== value) {
            onValueChange(initial)
          }
        }

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load model options')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [taskType, userId])

  // Update when external value changes
  useEffect(() => {
    if (value && value !== selectedModel) {
      setSelectedModel(value)
    }
  }, [value])

  // Handle model selection
  const handleModelChange = async (newModel: string) => {
    setSelectedModel(newModel)

    // Notify parent immediately
    if (onValueChange) {
      onValueChange(newModel)
    }

    // Save to backend
    setSaving(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/llm/preferences?user_id=${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          task_type: taskType,
          model_name: newModel
        })
      })

      if (!response.ok) {
        throw new Error('Failed to save preference')
      }

      setUserPreference(newModel)

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save preference')
    } finally {
      setSaving(false)
    }
  }

  // Get provider badge color
  const getProviderColor = (provider: string): string => {
    switch (provider.toLowerCase()) {
      case 'anthropic': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'openai': return 'bg-green-100 text-green-800 border-green-200'
      case 'google':
      case 'gemini': return 'bg-blue-100 text-blue-800 border-blue-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  // Loading state
  if (loading) {
    return (
      <div className={`space-y-2 ${className}`}>
        {label && !compact && <Label className="text-sm font-medium">{label}</Label>}
        <div className="flex items-center gap-2 p-2 border rounded-md bg-muted">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm text-muted-foreground">Loading models...</span>
        </div>
      </div>
    )
  }

  // Error state
  if (error && !taskInfo) {
    return (
      <div className={`space-y-2 ${className}`}>
        {label && !compact && <Label className="text-sm font-medium">{label}</Label>}
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {label && !compact && (
        <Label className="text-sm font-medium">{label}</Label>
      )}

      <div className="space-y-2">
        <Select
          value={selectedModel}
          onValueChange={handleModelChange}
          disabled={disabled || saving}
        >
          <SelectTrigger className="w-full">
            <SelectValue>
              <div className="flex items-center gap-2">
                {saving && <Loader2 className="h-3 w-3 animate-spin" />}
                {!saving && userPreference && <CheckCircle2 className="h-3 w-3 text-green-600" />}
                <span className="font-mono text-sm truncate">{selectedModel}</span>
              </div>
            </SelectValue>
          </SelectTrigger>
          <SelectContent className="max-h-[400px]">
            {availableModels.length > 0 ? (
              availableModels.map((model, idx) => {
                const isSaved = userPreference === model.model

                return (
                  <SelectItem key={idx} value={model.model}>
                    <div className="flex items-center gap-2 py-1">
                      <Badge
                        variant="outline"
                        className={`text-xs ${getProviderColor(model.provider)}`}
                      >
                        {model.provider}
                      </Badge>
                      <span className="font-mono text-xs">{model.model}</span>
                      {isSaved && (
                        <Badge variant="default" className="text-xs bg-green-600">
                          saved
                        </Badge>
                      )}
                    </div>
                  </SelectItem>
                )
              })
            ) : (
              <SelectItem value={selectedModel} disabled>
                <span className="text-sm text-muted-foreground">No models available</span>
              </SelectItem>
            )}
          </SelectContent>
        </Select>

        {!compact && (
          <div className="text-xs text-muted-foreground">
            {userPreference ? (
              <span className="flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3 text-green-600" />
                Your selection will be remembered for this task
              </span>
            ) : (
              <span>Select a model - your choice will be saved for next time</span>
            )}
          </div>
        )}

        {error && (
          <Alert variant="destructive" className="py-2">
            <AlertCircle className="h-3 w-3" />
            <AlertDescription className="text-xs">{error}</AlertDescription>
          </Alert>
        )}
      </div>
    </div>
  )
}
