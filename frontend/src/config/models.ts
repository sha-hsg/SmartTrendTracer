/**
 * Centralized LLM Model Configuration
 * Define all available models once for reuse across components
 * Updated: December 24, 2025 - TESTED and WORKING model IDs
 */

import { LucideIcon, Sparkles, Brain, Zap, Target, Layers, Crown, Bolt, MessageCircle } from 'lucide-react'

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
    value: 'openai/gpt-5.2',
    label: 'GPT-5.2',
    description: 'Latest flagship for knowledge work',
    icon: Crown,
    iconColor: 'text-purple-600',
    badge: 'Latest',
    badgeVariant: 'secondary'
  },
  {
    value: 'openai/gpt-5.1',
    label: 'GPT-5.1',
    description: 'Powerful reasoning and analysis',
    icon: Brain,
    iconColor: 'text-purple-700',
    badge: 'Pro',
    badgeVariant: 'secondary'
  },
  {
    value: 'openai/gpt-5-nano',
    label: 'GPT-5 Nano',
    description: 'Fast and cost-effective',
    icon: Zap,
    iconColor: 'text-purple-500',
    badge: 'Fast',
    badgeVariant: 'secondary'
  },

  // ========== Claude Models (TESTED) ==========
  {
    value: 'claude-opus-4-5-20251101',
    label: 'Claude Opus 4.5',
    description: 'Most powerful - hybrid reasoning & creativity',
    icon: Crown,
    iconColor: 'text-orange-800',
    badge: 'Latest',
    badgeVariant: 'secondary'
  },
  {
    value: 'claude-opus-4-1-20250805',
    label: 'Claude Opus 4.1',
    description: 'Flagship - best coding, agents & research',
    icon: Crown,
    iconColor: 'text-orange-700',
    badge: 'Flagship',
    badgeVariant: 'secondary'
  },
  {
    value: 'claude-opus-4-20250514',
    label: 'Claude Opus 4',
    description: 'Powerful analysis and reasoning',
    icon: Layers,
    iconColor: 'text-orange-600',
    badge: 'Powerful',
    badgeVariant: 'secondary'
  },
  {
    value: 'claude-sonnet-4-20250514',
    label: 'Claude Sonnet 4',
    description: 'Balanced intelligence, speed & cost',
    icon: Target,
    iconColor: 'text-orange-500',
    badge: 'Recommended',
    badgeVariant: 'secondary'
  },
  {
    value: 'claude-3-haiku-20240307',
    label: 'Claude Haiku 3',
    description: 'Fastest and most cost-effective',
    icon: Zap,
    iconColor: 'text-orange-400',
    badge: 'Fast',
    badgeVariant: 'secondary'
  },

  // ========== Gemini 3.x Models (TESTED - NEWEST) ==========
  {
    value: 'gemini/gemini-3.1-pro-preview',
    label: 'Gemini 3.1 Pro Preview',
    description: 'Latest flagship with superior reasoning',
    icon: Crown,
    iconColor: 'text-blue-700',
    badge: 'Latest',
    badgeVariant: 'secondary'
  },
  {
    value: 'gemini/gemini-3.5-flash',
    label: 'Gemini 3.5 Flash',
    description: 'Ultra-fast with latest capabilities',
    icon: Zap,
    iconColor: 'text-blue-600',
    badge: 'Fastest',
    badgeVariant: 'secondary'
  },
  {
    value: 'gemini/gemini-3.1-flash-lite',
    label: 'Gemini 3.1 Flash Lite',
    description: 'Lightweight and cost-efficient',
    icon: Bolt,
    iconColor: 'text-blue-500',
    badge: 'Lite',
    badgeVariant: 'outline'
  },

  // ========== Gemini 2.5 Models (TESTED) ==========
  {
    value: 'gemini/gemini-2.5-pro',
    label: 'Gemini 2.5 Pro',
    description: '2M context, comprehensive analysis',
    icon: Sparkles,
    iconColor: 'text-blue-500',
    badge: 'Large Context',
    badgeVariant: 'secondary'
  },
  {
    value: 'gemini/gemini-2.5-flash',
    label: 'Gemini 2.5 Flash',
    description: 'Fast and reliable',
    icon: Bolt,
    iconColor: 'text-blue-400',
    badge: 'Fast',
    badgeVariant: 'outline'
  },

  // ========== Grok 4.1 Models (TESTED) ==========
  {
    value: 'xai/grok-4-1-fast-reasoning',
    label: 'Grok 4.1 Fast Reasoning',
    description: 'Fast with chain-of-thought reasoning',
    icon: Brain,
    iconColor: 'text-gray-700',
    badge: 'Reasoning',
    badgeVariant: 'secondary'
  },
  {
    value: 'xai/grok-4-1-fast-non-reasoning',
    label: 'Grok 4.1 Fast',
    description: 'Fastest Grok model',
    icon: Zap,
    iconColor: 'text-gray-600',
    badge: 'Fastest',
    badgeVariant: 'secondary'
  },
  {
    value: 'xai/grok-4-1-fast',
    label: 'Grok 4.1',
    description: 'Balanced speed and capability',
    icon: MessageCircle,
    iconColor: 'text-gray-700',
    badge: 'Balanced',
    badgeVariant: 'secondary'
  },

  // ========== Legacy Models (still available) ==========
  {
    value: 'claude-3-opus-20240229',
    label: 'Claude 3 Opus',
    description: 'Legacy - powerful analysis',
    icon: Layers,
    iconColor: 'text-orange-400',
    badge: 'Legacy',
    badgeVariant: 'outline'
  }
]

/**
 * Model presets for different tasks - Updated Dec 2025
 */
export const MODEL_PRESETS = {
  // Tag suggestion for papers - prioritize comprehensive analysis
  paperTagSuggestion: {
    default: 'claude-sonnet-4-20250514',
    alternatives: ['gemini/gemini-2.5-pro', 'openai/gpt-5.2', 'claude-opus-4-1-20250805']
  },

  // Paper analysis - need deep understanding
  paperAnalysis: {
    default: 'gemini/gemini-2.5-pro',
    alternatives: ['claude-opus-4-1-20250805', 'openai/gpt-5.1', 'claude-sonnet-4-20250514']
  },

  // Entity extraction - need accuracy
  entityExtraction: {
    default: 'claude-opus-4-1-20250805',
    alternatives: ['openai/gpt-5.1', 'gemini/gemini-2.5-pro', 'claude-sonnet-4-20250514']
  },

  // Article summarization - need speed and quality
  articleSummarization: {
    default: 'claude-sonnet-4-20250514',
    alternatives: ['gemini/gemini-2.5-flash', 'claude-3-haiku-20240307', 'openai/gpt-5.2']
  },

  // Tweet annotation - need speed
  tweetAnnotation: {
    default: 'claude-3-haiku-20240307',
    alternatives: ['gemini/gemini-2.5-flash', 'openai/gpt-5-nano']
  },

  // Free-form paper analysis
  freeAnalysis: {
    default: 'gemini/gemini-2.5-flash',
    alternatives: ['claude-sonnet-4-20250514', 'openai/gpt-5.2', 'gemini/gemini-2.5-pro']
  },

  // RAG search answers
  ragAnswer: {
    default: 'gemini/gemini-2.5-pro',
    alternatives: ['claude-opus-4-1-20250805', 'openai/gpt-5.1']
  },

  // Trend analysis
  trendAnalysis: {
    default: 'claude-opus-4-1-20250805',
    alternatives: ['openai/gpt-5.2', 'gemini/gemini-2.5-pro']
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
