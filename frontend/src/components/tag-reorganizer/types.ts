export interface Task {
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

export const calculateEstimatedTime = (tagCount: number, mode: 'comprehensive' | 'gpt5'): number => {
  if (mode === 'comprehensive') {
    return 0.5 // 30 seconds
  } else {
    // GPT-5 processing formula: Time (minutes) = (Number_of_Tags / 75) + 2
    return Math.ceil((tagCount / 75) + 2)
  }
}

export const formatTime = (seconds: number): string => {
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

export const formatMinutes = (minutes: number): string => {
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
