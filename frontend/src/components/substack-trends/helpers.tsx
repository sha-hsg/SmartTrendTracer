import {
  TrendingUp,
  TrendingDown,
  ArrowRight,
  Flame,
  Zap,
  PenTool,
  Timer,
  Activity,
} from 'lucide-react'

export const getProductivityIcon = (productivity: string) => {
  switch(productivity) {
    case 'very_high': return <Flame className="h-4 w-4 text-red-500" />
    case 'high': return <Zap className="h-4 w-4 text-orange-500" />
    case 'moderate': return <PenTool className="h-4 w-4 text-blue-500" />
    case 'low': return <Timer className="h-4 w-4 text-gray-500" />
    default: return <Activity className="h-4 w-4 text-gray-400" />
  }
}

export const getProductivityColor = (productivity: string) => {
  switch(productivity) {
    case 'very_high': return 'bg-red-50 text-red-700 border-red-200'
    case 'high': return 'bg-orange-50 text-orange-700 border-orange-200'
    case 'moderate': return 'bg-blue-50 text-blue-700 border-blue-200'
    case 'low': return 'bg-gray-50 text-gray-700 border-gray-200'
    default: return 'bg-gray-50 text-gray-500 border-gray-200'
  }
}

export const getTrendIcon = (trend: string) => {
  switch(trend) {
    case 'rising': return <TrendingUp className="h-4 w-4 text-green-500" />
    case 'falling': return <TrendingDown className="h-4 w-4 text-red-500" />
    default: return <ArrowRight className="h-4 w-4 text-gray-500" />
  }
}

export const formatDate = (dateStr: string) => {
  if (!dateStr) return 'N/A'
  try {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    })
  } catch {
    return 'N/A'
  }
}
