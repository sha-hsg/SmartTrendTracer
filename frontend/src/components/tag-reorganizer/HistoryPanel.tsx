import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ScrollArea } from '@/components/ui/scroll-area'
import { StatusBadge } from './StatusBadge'
import { Task } from './types'

interface HistoryPanelProps {
  taskHistory: Task[]
  showHistory: boolean
  selectedHistoryTask: Task | null
  onSelectTask: (task: Task) => void
  onApplyHistoryTask: (taskId: string) => void
}

export function HistoryPanel({
  taskHistory,
  showHistory,
  selectedHistoryTask,
  onSelectTask,
  onApplyHistoryTask
}: HistoryPanelProps) {
  return (
    <>
      {/* History Panel */}
      {showHistory && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <CardTitle className="text-sm">Recent Reorganization Tasks</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-48">
              <div className="space-y-2">
                {taskHistory.map((task) => (
                  <div
                    key={task.task_id}
                    className="flex items-center justify-between p-2 bg-white rounded cursor-pointer hover:bg-gray-50"
                    onClick={() => onSelectTask(task)}
                  >
                    <div className="flex items-center gap-2">
                      <StatusBadge status={task.status} />
                      <span className="text-sm text-gray-600">
                        {new Date(task.created_at).toLocaleString()}
                      </span>
                    </div>
                    {task.status === 'completed' && task.result && (
                      <Button size="sm" variant="outline">
                        View Result
                      </Button>
                    )}
                  </div>
                ))}
                {taskHistory.length === 0 && (
                  <div className="text-center text-gray-500 py-4">
                    No previous reorganization tasks
                  </div>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      )}

      {/* Selected History Task */}
      {selectedHistoryTask && (
        <Alert className="border-blue-200 bg-blue-50">
          <AlertDescription>
            <div className="flex items-center justify-between">
              <span>
                Viewing task from {new Date(selectedHistoryTask.created_at).toLocaleString()}
              </span>
              {selectedHistoryTask.status === 'completed' && selectedHistoryTask.result && (
                <Button
                  size="sm"
                  onClick={() => onApplyHistoryTask(selectedHistoryTask.task_id)}
                >
                  Apply These Results
                </Button>
              )}
            </div>
          </AlertDescription>
        </Alert>
      )}
    </>
  )
}
