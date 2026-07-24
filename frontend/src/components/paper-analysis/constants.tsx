import React from 'react'
import {
  FileText,
  Microscope,
  ClipboardList,
  Library,
} from 'lucide-react'

export const extractTextContent = (content: unknown): string => {
  if (typeof content === 'string') {
    return content
  }
  if (Array.isArray(content)) {
    return content
      .map(part => {
        if (typeof part === 'string') return part
        if (part && typeof part === 'object' && 'text' in part) return part.text
        return ''
      })
      .join('\n')
  }
  if (content && typeof content === 'object' && 'text' in content) {
    return (content as { text: string }).text
  }
  return String(content || '')
}

export const getRelativeTime = (date: Date): string => {
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  if (days < 7) return `${days}d ago`
  return date.toLocaleDateString()
}

export const categoryIcons: Record<string, React.ReactNode> = {
  summaries: <FileText className="h-4 w-4" />,
  analysis: <Microscope className="h-4 w-4" />,
  review: <ClipboardList className="h-4 w-4" />,
  reference: <Library className="h-4 w-4" />
}

export const analysisTypeColors: Record<string, { bg: string; border: string; header: string }> = {
  sas_summary: {
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
    header: 'bg-indigo-100'
  },
  sas_review: {
    bg: 'bg-blue-50',
    border: 'border-blue-200',
    header: 'bg-blue-100'
  },
  switt: {
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    header: 'bg-violet-100'
  },
  summary: {
    bg: 'bg-sky-50',
    border: 'border-sky-200',
    header: 'bg-sky-100'
  },
  key_findings: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-200',
    header: 'bg-emerald-100'
  },
  methodology: {
    bg: 'bg-rose-50',
    border: 'border-rose-200',
    header: 'bg-rose-100'
  },
  evaluation: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    header: 'bg-red-100'
  },
  limitations: {
    bg: 'bg-pink-50',
    border: 'border-pink-200',
    header: 'bg-pink-100'
  },
  glossary: {
    bg: 'bg-teal-50',
    border: 'border-teal-200',
    header: 'bg-teal-100'
  },
  layman_summary: {
    bg: 'bg-sky-50',
    border: 'border-sky-200',
    header: 'bg-sky-100'
  },
  mollick_summary: {
    bg: 'bg-purple-50',
    border: 'border-purple-200',
    header: 'bg-purple-100'
  },
  pareto_summary: {
    bg: 'bg-lime-50',
    border: 'border-lime-200',
    header: 'bg-lime-100'
  },
  switt_analysis: {
    bg: 'bg-violet-50',
    border: 'border-violet-200',
    header: 'bg-violet-100'
  },
  review: {
    bg: 'bg-orange-50',
    border: 'border-orange-200',
    header: 'bg-orange-100'
  },
  default: {
    bg: 'bg-gray-50',
    border: 'border-gray-200',
    header: 'bg-gray-100'
  }
}

export interface AnalysisType {
  id: string
  name: string
  description: string
  category: string
}

export interface GeneratedAnalysis {
  success: boolean
  content?: string
  error?: string
  analysis_name?: string
  generated_at?: string
  model_used?: string
  was_skipped?: boolean
}

export interface BatchProgress {
  total: number
  completed: number
  current: string | null
  skipped: number
}
