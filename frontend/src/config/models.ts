/**
 * Centralized LLM Model Configuration
 * Define all available models once for reuse across components
 * Updated: December 24, 2025 - TESTED and WORKING model IDs
 */

import { LucideIcon, Brain, Zap, Target, Crown, Bolt, MessageCircle } from 'lucide-react'

export interface ModelOption {
  value: string
  label: string
  description: string
  icon: LucideIcon
  iconColor: string
  badge?: string
  badgeVariant?: 'default' | 'secondary' | 'destructive' | 'outline'
}

/**
 * All available LLM models - TESTED and WORKING
 * Synced with backend's litellm_config.yaml
 */
export const AVAILABLE_MODELS: ModelOption[] = [
  // ========== OpenAI GPT-5 Models (TESTED) ==========
  {
    value: 'openai/gpt-6-astra',
    label: 'GPT-6 Astra',
    description: 'Latest flagship for knowledge work',
    icon: Crown,
    iconColor: 'text-purple-600',
    badge: 'Latest',
    badgeVariant: 'secondary'
  },
  {
    value: 'openai/gpt-6-sol',
    label: 'GPT-6 Sol',
    description: 'Powerful reasoning and analysis',
    icon: Brain,
    iconColor: 'text-purple-700',
    badge: 'Pro',
    badgeVariant: 'secondary'
  },
  {
    value: 'openai/gpt-6-luna',
    label: 'GPT-6 Luna',
    description: 'Fast and cost-effective',
    icon: Zap,
    iconColor: 'text-purple-500',
    badge: 'Fast',
    badgeVariant: 'secondary'
  },

  // ========== Claude Models (current lineup, Sep 2026) ==========
  {
    value: 'claude-opus-5-5',
    label: 'Claude Opus 5.5',
    description: 'Flagship - deep reasoning, agents & long-horizon work',
    icon: Crown,
    iconColor: 'text-orange-700',
    badge: 'Flagship',
    badgeVariant: 'secondary'
  },
  {
    value: 'claude-sonnet-5',
    label: 'Claude Sonnet 5',
    description: 'Balanced intelligence, speed & cost',
    icon: Target,
    iconColor: 'text-orange-500',
    badge: 'Recommended',
    badgeVariant: 'secondary'
  },
  {
    value: 'claude-haiku-4-5',
    label: 'Claude Haiku 4.5',
    description: 'Fastest and most cost-effective',
    icon: Zap,
    iconColor: 'text-orange-400',
    badge: 'Fast',
    badgeVariant: 'secondary'
  },

  // ========== Gemini Models (current lineup, Sep 2026) ==========
  {
    value: 'gemini/gemini-3.1-pro-preview',
    label: 'Gemini 3.1 Pro Preview',
    description: 'Flagship with superior reasoning, 1M context',
    icon: Crown,
    iconColor: 'text-blue-700',
    badge: 'Flagship',
    badgeVariant: 'secondary'
  },
  {
    value: 'gemini/gemini-3.8-flash',
    label: 'Gemini 3.8 Flash',
    description: 'Ultra-fast with latest capabilities',
    icon: Zap,
    iconColor: 'text-blue-600',
    badge: 'Fastest',
    badgeVariant: 'secondary'
  },
  {
    value: 'gemini/gemini-3.5-flash-lite',
    label: 'Gemini 3.5 Flash Lite',
    description: 'Lightweight and cost-efficient',
    icon: Bolt,
    iconColor: 'text-blue-500',
    badge: 'Lite',
    badgeVariant: 'outline'
  },

  // ========== Grok Models (current lineup, Sep 2026) ==========
  {
    value: 'xai/grok-4.7',
    label: 'Grok 4.7',
    description: 'Balanced speed and capability',
    icon: MessageCircle,
    iconColor: 'text-gray-700',
    badge: 'Balanced',
    badgeVariant: 'secondary'
  },
  {
    value: 'xai/grok-4.20-0309-reasoning',
    label: 'Grok 4.20 Reasoning',
    description: 'Fast with chain-of-thought reasoning',
    icon: Brain,
    iconColor: 'text-gray-700',
    badge: 'Reasoning',
    badgeVariant: 'secondary'
  },
  {
    value: 'xai/grok-4.20-0309-non-reasoning',
    label: 'Grok 4.20 Fast',
    description: 'Fastest Grok model',
    icon: Zap,
    iconColor: 'text-gray-600',
    badge: 'Fastest',
    badgeVariant: 'secondary'
  },

]

/**
 * Model presets for different tasks - Updated Dec 2025
 */
export const MODEL_PRESETS = {
  // Tag suggestion for papers - prioritize comprehensive analysis
  paperTagSuggestion: {
    default: 'claude-sonnet-5',
    alternatives: ['gemini/gemini-3.1-pro-preview', 'openai/gpt-6-astra', 'claude-opus-5-5']
  },

  // Paper analysis - need deep understanding
  paperAnalysis: {
    default: 'gemini/gemini-3.1-pro-preview',
    alternatives: ['claude-opus-5-5', 'openai/gpt-6-sol', 'claude-sonnet-5']
  },

  // Entity extraction - need accuracy
  entityExtraction: {
    default: 'claude-opus-5-5',
    alternatives: ['openai/gpt-6-sol', 'gemini/gemini-3.1-pro-preview', 'claude-sonnet-5']
  },

  // Article summarization - need speed and quality
  articleSummarization: {
    default: 'claude-sonnet-5',
    alternatives: ['gemini/gemini-3.8-flash', 'claude-haiku-4-5', 'openai/gpt-6-astra']
  },

  // Tweet annotation - need speed
  tweetAnnotation: {
    default: 'claude-haiku-4-5',
    alternatives: ['gemini/gemini-3.8-flash', 'openai/gpt-6-luna']
  },

  // Free-form paper analysis
  freeAnalysis: {
    default: 'gemini/gemini-3.8-flash',
    alternatives: ['claude-sonnet-5', 'openai/gpt-6-astra', 'gemini/gemini-3.1-pro-preview']
  },

  // RAG search answers
  ragAnswer: {
    default: 'gemini/gemini-3.1-pro-preview',
    alternatives: ['claude-opus-5-5', 'openai/gpt-6-sol']
  },

  // Trend analysis
  trendAnalysis: {
    default: 'claude-opus-5-5',
    alternatives: ['openai/gpt-6-astra', 'gemini/gemini-3.1-pro-preview']
  }
} as const

/**
 * Get model by value
 */
export function getModelByValue(value: string): ModelOption | undefined {
  return AVAILABLE_MODELS.find(m => m.value === value)
}

/**
 * Get models filtered by task preset
 */
export function getModelsForTask(task: keyof typeof MODEL_PRESETS): ModelOption[] {
  const preset = MODEL_PRESETS[task]
  const relevantValues: string[] = [preset.default, ...preset.alternatives]
  return AVAILABLE_MODELS.filter(m => relevantValues.includes(m.value))
}

/**
 * Get default model for a task
 */
export function getDefaultModel(task: keyof typeof MODEL_PRESETS): string {
  return MODEL_PRESETS[task].default
}

/**
 * Get localStorage key for model preference
 */
export function getModelStorageKey(task: string): string {
  return `preferred${task.charAt(0).toUpperCase() + task.slice(1)}Model`
}
