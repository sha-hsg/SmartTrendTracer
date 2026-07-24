import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { CheckCircle, Download, FileText } from 'lucide-react'

interface ResultDisplayProps {
  result: any
  taskId: string | null
  taskStatus: any
  onApply: () => void
  onReviewLater: () => void
}

export function ResultDisplay({
  result,
  taskId,
  taskStatus,
  onApply,
  onReviewLater
}: ResultDisplayProps) {
  const handleViewDebug = () => {
    const debugData = {
      request: {
        model: result.model_used || 'gemini-2.5-pro',
        concepts_sent: result.stats?.total_tags || result.statistics?.total_tags || 0,
        prompt_size: result.prompt_size || 'N/A',
        timestamp: taskStatus?.created_at
      },
      response: {
        concepts_returned: result.stats?.unique_concepts || result.statistics?.new_concepts || 0,
        aliases_returned: result.aliases?.length || 0,
        duration: taskStatus?.completed_at && taskStatus?.created_at
          ? Math.round((new Date(taskStatus.completed_at).getTime() - new Date(taskStatus.created_at).getTime()) / 1000) + ' seconds'
          : 'N/A',
        fallback_used: result.fallback_used || false,
        error: result.error || null
      },
      raw_result: result
    }
    const blob = new Blob([JSON.stringify(debugData, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    window.open(url, '_blank')
  }

  const handleExport = () => {
    const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `reorganization-${taskId || 'result'}.json`
    a.click()
  }

  return (
    <Card className="border-green-200">
      <CardHeader>
        <CardTitle className="text-green-700 flex items-center justify-between">
          <span>Reorganization Complete!</span>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={handleViewDebug}>
              <FileText className="w-4 h-4 mr-2" />
              View Debug
            </Button>
            <Button size="sm" variant="outline" onClick={handleExport}>
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <Alert className="border-green-200 bg-green-50">
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Results are saved and will persist even if you close the browser or the server restarts.
            </AlertDescription>
          </Alert>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="font-medium">Total Concepts:</span> {result.stats?.total_tags || result.statistics?.total_tags || 0}
            </div>
            <div>
              <span className="font-medium">New Concepts:</span> {result.stats?.unique_concepts || result.statistics?.new_concepts || 0}
            </div>
            <div>
              <span className="font-medium">Merged:</span> {result.stats?.merge_groups || result.statistics?.merged_tags || 0}
            </div>
            <div>
              <span className="font-medium">Categories:</span> {result.stats?.hierarchy_levels || result.statistics?.total_categories || 0}
            </div>
          </div>

          <div className="flex gap-2">
            <Button
              onClick={onApply}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              Apply Reorganization
            </Button>
            <Button onClick={onReviewLater} variant="outline">
              Review Later
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
