import { ChartOptions } from 'chart.js'

export interface TrendData {
  daily: { date: string; count: number }[]
  hourly: { hour: string; count: number }[]
  by_account: { [key: string]: { date: string; count: number }[] }
}

export interface TagTrendData {
  top_tags: { tag: string; count: number }[]
  timeline: { [key: string]: { date: string; count: number }[] }
}

export interface QuickInsight {
  type: 'increase' | 'decrease' | 'stable' | 'peak' | 'low'
  title: string
  value: string
  description: string
  icon: React.ReactNode
}

export const accountColors = [
  'rgb(29, 161, 242)',
  'rgb(126, 34, 206)',
  'rgb(16, 185, 129)',
  'rgb(251, 146, 60)',
  'rgb(244, 63, 94)',
  'rgb(99, 102, 241)',
  'rgb(236, 72, 153)'
]

export const getTimelineLabels = (data: any[], timeRangeNum: number): string[] => {
  if (!data || data.length === 0) return []

  if (timeRangeNum >= 180) {
    return data.map(d => new Date(d.date).toLocaleDateString('en-US', {
      month: 'short',
      year: timeRangeNum >= 365 ? '2-digit' : undefined
    }))
  } else if (timeRangeNum >= 30) {
    return data.map(d => new Date(d.date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    }))
  } else {
    return data.map(d => new Date(d.date).toLocaleDateString('en-US', {
      month: timeRangeNum <= 7 ? undefined : 'short',
      day: 'numeric',
      weekday: timeRangeNum <= 3 ? 'short' : undefined
    }))
  }
}

export const chartOptions: ChartOptions<'line'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'top' as const,
    },
    tooltip: {
      mode: 'index' as const,
      intersect: false,
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      }
    },
    x: {
      grid: {
        display: false
      }
    }
  }
}

export const barChartOptions: ChartOptions<'bar'> = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      grid: {
        color: 'rgba(0, 0, 0, 0.05)'
      }
    },
    x: {
      grid: {
        display: false
      }
    }
  }
}
