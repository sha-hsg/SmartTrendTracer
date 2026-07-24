import { Card, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Progress } from '@/components/ui/progress'
import { Timer, Clock, AlertCircle } from 'lucide-react'
import { StatusBadge } from './StatusBadge'
import { formatTime } from './types'

interface ProgressDisplayProps {
  taskStatus: any
  isRunning: boolean
  elapsedSeconds: number
  estimatedMinutes: number
}

export function ProgressDisplay({
  taskStatus,
  isRunning,
  elapsedSeconds,
  estimatedMinutes
}: ProgressDisplayProps) {
  if (!taskStatus) return null

  return (
    <Card className="bg-gray-50 border-blue-200">
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Timer Section */}
          {isRunning && (
            <div className="bg-white rounded-lg p-4 border border-blue-100">
              <div className="grid grid-cols-3 gap-4 text-center">
                <div>
                  <div className="text-xs text-gray-500 mb-1">Elapsed Time</div>
                  <div className="text-lg font-mono font-semibold text-blue-600">
                    <Timer className="w-4 h-4 inline mr-1" />
                    {formatTime(elapsedSeconds)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Estimated Total</div>
                  <div className="text-lg font-mono font-semibold text-gray-600">
                    <Clock className="w-4 h-4 inline mr-1" />
                    {formatTime(estimatedMinutes * 60)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-500 mb-1">Time Remaining</div>
                  <div className="text-lg font-mono font-semibold text-green-600">
                    {formatTime(Math.max(0, (estimatedMinutes * 60) - elapsedSeconds))}
                  </div>
                </div>
              </div>

              {/* Visual Progress Bar with Time */}
              <div className="mt-4">
                <div className="flex justify-between text-xs text-gray-500 mb-1">
                  <span>0:00</span>
                  <span className="font-medium">
                    {Math.round((elapsedSeconds / (estimatedMinutes * 60)) * 100)}% Complete
                  </span>
                  <span>{formatTime(estimatedMinutes * 60)}</span>
                </div>
                <Progress
                  value={Math.min(100, (elapsedSeconds / (estimatedMinutes * 60)) * 100)}
                  className="h-3"
                />
              </div>

              {/* Warning if taking longer than expected */}
              {elapsedSeconds > (estimatedMinutes * 60) && (
                <Alert className="mt-3 border-orange-200 bg-orange-50">
                  <AlertCircle className="h-3 w-3" />
                  <AlertDescription className="text-xs">
                    Taking longer than expected. Complex reorganizations may need extra time.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          )}

          {/* Status Section */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Status:</span>
              <StatusBadge status={taskStatus.status} />
            </div>

            {taskStatus.progress && (
              <>
                <div className="flex justify-between text-sm">
                  <span>Progress:</span>
                  <span>{taskStatus.progress.current} / {taskStatus.progress.total || 100}</span>
                </div>

                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{
                      width: `${(taskStatus.progress.current / Math.max(taskStatus.progress.total || 100, 1)) * 100}%`
                    }}
                  />
                </div>

                {taskStatus.progress.current_step && (
                  <div className="text-sm text-gray-600 mt-2">
                    Current: {taskStatus.progress.current_step}
                  </div>
                )}
              </>
            )}

            {/* Messages */}
            {taskStatus.progress?.messages && taskStatus.progress.messages.length > 0 && (
              <div className="mt-4">
                <div className="text-sm font-medium mb-2">Recent Activity:</div>
                <ScrollArea className="h-32 bg-white rounded p-2">
                  <div className="space-y-1">
                    {taskStatus.progress.messages.map((msg: any, idx: number) => (
                      <div key={idx} className="text-xs text-gray-600">
                        <span className="text-gray-400">
                          {new Date(msg.time).toLocaleTimeString()}:
                        </span> {msg.text}
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}

            {/* Timing Information */}
            {taskStatus.created_at && (
              <div className="mt-2 text-sm text-gray-600">
                <div>Started: {new Date(taskStatus.created_at).toLocaleTimeString()}</div>
                {taskStatus.completed_at && (
                  <>
                    <div>Completed: {new Date(taskStatus.completed_at).toLocaleTimeString()}</div>
                    <div className="font-medium">
                      Duration: {Math.round((new Date(taskStatus.completed_at).getTime() - new Date(taskStatus.created_at).getTime()) / 1000)} seconds
                    </div>
                  </>
                )}
                {!taskStatus.completed_at && taskStatus.status === 'analyzing' && (
                  <div className="text-orange-600">
                    Running for: {Math.round((Date.now() - new Date(taskStatus.created_at).getTime()) / 1000)} seconds
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
