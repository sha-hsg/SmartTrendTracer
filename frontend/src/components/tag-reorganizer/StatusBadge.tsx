import { Badge } from '@/components/ui/badge'
import {
  CheckCircle,
  XCircle,
  RotateCcw,
  Clock,
  AlertCircle
} from 'lucide-react'

const statusConfig = {
  'completed': { color: 'bg-green-500', icon: CheckCircle },
  'failed': { color: 'bg-red-500', icon: XCircle },
  'processing': { color: 'bg-blue-500', icon: RotateCcw },
  'cancelled': { color: 'bg-gray-500', icon: XCircle },
  'interrupted': { color: 'bg-orange-500', icon: AlertCircle },
  'initializing': { color: 'bg-yellow-500', icon: Clock }
}

export function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status as keyof typeof statusConfig] || statusConfig['initializing']
  const Icon = config.icon

  return (
    <Badge className={`${config.color} text-white`}>
      <Icon className="w-3 h-3 mr-1" />
      {status}
    </Badge>
  )
}
