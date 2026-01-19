/**
 * Reusable Model Selector Component
 * Displays AI model selection with icons, badges, and descriptions
 */

import React, { useEffect, useState } from 'react'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Label } from "@/components/ui/label"
import {
  AVAILABLE_MODELS,
  getDefaultModel,
  getModelStorageKey,
  MODEL_PRESETS
} from '@/config/models'

interface ModelSelectorProps {
  /** Current selected model value */
  value: string

  /** Callback when model changes */
  onValueChange: (value: string) => void

  /** Optional task type for filtering and defaults */
  task?: keyof typeof MODEL_PRESETS

  /** Optional label text (defaults to "AI Model") */
  label?: string

  /** Optional description below selector */
  description?: string

  /** Show only models relevant to task */
  filterByTask?: boolean

  /** Enable localStorage persistence */
  persist?: boolean

  /** Custom storage key (overrides task-based key) */
  storageKey?: string

  /** Additional className for container */
  className?: string

  /** Disable the selector */
  disabled?: boolean
}

export default function ModelSelector({
  value,
  onValueChange,
  task,
  label = "AI Model",
  description,
  filterByTask = false,
  persist = true,
  storageKey,
  className = "",
  disabled = false
}: ModelSelectorProps) {
  // Get available models (filtered or all)
  const availableModels = React.useMemo(() => {
    if (filterByTask && task) {
      const preset = MODEL_PRESETS[task]
      const relevantValues = [preset.default, ...preset.alternatives]
      return AVAILABLE_MODELS.filter(m => relevantValues.includes(m.value))
    }
    return AVAILABLE_MODELS
  }, [filterByTask, task])

  // Handle model change with optional persistence
  const handleChange = (newValue: string) => {
    onValueChange(newValue)

    // Persist to localStorage if enabled
    if (persist) {
      const key = storageKey || (task ? getModelStorageKey(task) : 'selectedModel')
      localStorage.setItem(key, newValue)
    }
  }

  // Load from localStorage on mount if persist is enabled
  useEffect(() => {
    if (persist && !value) {
      const key = storageKey || (task ? getModelStorageKey(task) : 'selectedModel')
      const stored = localStorage.getItem(key)
      if (stored) {
        onValueChange(stored)
      } else if (task) {
        // Use default for task
        onValueChange(getDefaultModel(task))
      }
    }
  }, [persist, task, storageKey, value, onValueChange])

  return (
    <div className={`space-y-2 ${className}`}>
      {label && (
        <Label className="text-sm font-medium">{label}</Label>
      )}

      <Select value={value} onValueChange={handleChange} disabled={disabled}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder="Select an AI model..." />
        </SelectTrigger>
        <SelectContent>
          {availableModels.map((model) => {
            const IconComponent = model.icon

            return (
              <SelectItem key={model.value} value={model.value}>
                <div className="flex items-center gap-2 py-1">
                  <IconComponent className={`h-4 w-4 ${model.iconColor}`} />
                  <span className="font-medium">{model.label}</span>
                  {model.badge && (
                    <Badge variant={model.badgeVariant || 'secondary'} className="ml-2 text-xs">
                      {model.badge}
                    </Badge>
                  )}
                </div>
              </SelectItem>
            )
          })}
        </SelectContent>
      </Select>

      {description && (
        <p className="text-xs text-muted-foreground">{description}</p>
      )}
    </div>
  )
}

/**
 * Hook for managing model selection with persistence
 */
export function useModelSelection(task: keyof typeof MODEL_PRESETS) {
  const storageKey = getModelStorageKey(task)
  const defaultModel = getDefaultModel(task)

  const [selectedModel, setSelectedModel] = useState<string>(() => {
    const stored = localStorage.getItem(storageKey)
    return stored || defaultModel
  })

  const handleModelChange = (value: string) => {
    setSelectedModel(value)
    localStorage.setItem(storageKey, value)
  }

  return {
    selectedModel,
    setSelectedModel: handleModelChange
  }
}
