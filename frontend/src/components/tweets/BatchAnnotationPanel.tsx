import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import {
  Loader2,
  Sparkles,
  CheckCircle2,
  AlertCircle
} from 'lucide-react'
import UnifiedModelSelector from '../UnifiedModelSelector'
import type { BatchResult, AnnotateAllProgress, AnnotateAllResult } from './useBatchAnnotation'

interface AnnotationFacet {
  status: string
  label: string
  count: number
}

interface BatchAnnotationPanelProps {
  tweetCount: number
  annotationStatusFacets: AnnotationFacet[]
  batchAnnotating: boolean
  batchProgress: number
  batchModel: string
  setBatchModel: (model: string) => void
  batchResult: BatchResult
  annotateAllRunning: boolean
  annotateAllProgress: AnnotateAllProgress
  annotateAllResult: AnnotateAllResult
  onBatchAnnotate: () => void
  onAnnotateAll: () => void
  onCancelAnnotateAll: () => void
}

export default function BatchAnnotationPanel({
  tweetCount,
  annotationStatusFacets,
  batchAnnotating,
  batchProgress,
  batchModel,
  setBatchModel,
  batchResult,
  annotateAllRunning,
  annotateAllProgress,
  annotateAllResult,
  onBatchAnnotate,
  onAnnotateAll,
  onCancelAnnotateAll,
}: BatchAnnotationPanelProps) {
  const notAnnotatedFacet = annotationStatusFacets.find(s => s.status === 'not_annotated')
  const notAnnotatedCount = notAnnotatedFacet?.count || 0

  return (
    <Card className="mb-6">
      <CardContent className="p-4 space-y-3">
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-purple-500" />
            <span className="text-sm font-medium">Batch Annotation / Summary</span>
          </div>

          <div className="flex-1 min-w-[200px] max-w-[300px]">
            <UnifiedModelSelector
              taskType="tag_suggestion"
              value={batchModel}
              onValueChange={setBatchModel}
              compact={true}
              disabled={batchAnnotating || annotateAllRunning}
            />
          </div>

          <Button
            onClick={onBatchAnnotate}
            disabled={batchAnnotating || annotateAllRunning || tweetCount === 0 || !batchModel}
            className="bg-purple-600 hover:bg-purple-700"
          >
            {batchAnnotating ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Annotating... {batchProgress}%
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Batch Annotate ({tweetCount} tweets)
              </>
            )}
          </Button>

          {/* Annotate All Unannotated button */}
          <Button
            onClick={onAnnotateAll}
            disabled={batchAnnotating || annotateAllRunning || notAnnotatedCount === 0 || !batchModel}
            className="bg-orange-600 hover:bg-orange-700"
          >
            {annotateAllRunning ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Annotating All...
              </>
            ) : (
              <>
                <Sparkles className="mr-2 h-4 w-4" />
                Annotate All Unannotated ({notAnnotatedCount})
              </>
            )}
          </Button>

          {/* Progress bar for page batch */}
          {batchAnnotating && (
            <div className="flex-1 min-w-[200px]">
              <Progress value={batchProgress} className="h-2" />
            </div>
          )}

          {/* Result message */}
          {batchResult.status === 'completed' && (
            <div className="flex items-center gap-2 text-sm">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-green-700">
                {batchResult.newTagsCount} new tags added
                {batchResult.skippedCount ? `, ${batchResult.skippedCount} skipped` : ''}
                {batchResult.errorCount ? `, ${batchResult.errorCount} errors` : ''}
              </span>
            </div>
          )}

          {batchResult.status === 'error' && (
            <div className="flex items-center gap-2 text-sm">
              <AlertCircle className="h-4 w-4 text-red-500" />
              <span className="text-red-700">{batchResult.message}</span>
            </div>
          )}
        </div>

        {/* Annotate All progress banner */}
        {annotateAllRunning && (
          <div className="flex items-center gap-4 p-3 bg-orange-50 dark:bg-orange-950 rounded-lg border border-orange-200 dark:border-orange-800">
            <Loader2 className="h-5 w-5 text-orange-600 animate-spin flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm font-medium text-orange-800 dark:text-orange-200">
                  Annotating tweets... {annotateAllProgress.processed}/{annotateAllProgress.total} ({annotateAllProgress.progress}%)
                  {annotateAllProgress.newTagsCount > 0 && ` — ${annotateAllProgress.newTagsCount} new tags`}
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={onCancelAnnotateAll}
                  className="h-7 px-3 text-xs border-orange-300 text-orange-700 hover:bg-orange-100"
                >
                  Cancel
                </Button>
              </div>
              <Progress value={annotateAllProgress.progress} className="h-2" />
            </div>
          </div>
        )}

        {/* Annotate All result message */}
        {annotateAllResult.status === 'completed' && (
          <div className="flex items-center gap-2 text-sm p-2 bg-green-50 dark:bg-green-950 rounded">
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-green-700 dark:text-green-300">
              {annotateAllResult.message || `All done! ${annotateAllResult.newTagsCount} new tags added`}
              {annotateAllResult.skippedCount ? `, ${annotateAllResult.skippedCount} skipped` : ''}
              {annotateAllResult.errorCount ? `, ${annotateAllResult.errorCount} errors` : ''}
            </span>
          </div>
        )}
        {annotateAllResult.status === 'cancelled' && (
          <div className="flex items-center gap-2 text-sm p-2 bg-yellow-50 dark:bg-yellow-950 rounded">
            <AlertCircle className="h-4 w-4 text-yellow-500" />
            <span className="text-yellow-700 dark:text-yellow-300">
              Annotation cancelled. {annotateAllResult.newTagsCount || 0} new tags added before cancellation.
            </span>
          </div>
        )}
        {annotateAllResult.status === 'error' && (
          <div className="flex items-center gap-2 text-sm p-2 bg-red-50 dark:bg-red-950 rounded">
            <AlertCircle className="h-4 w-4 text-red-500" />
            <span className="text-red-700 dark:text-red-300">{annotateAllResult.message}</span>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
