/**
 * BatchProcessingPanel - Progress banners for batch Marker processing
 * and batch analysis generation.
 */
import React from 'react'
import {
  Cpu,
  BarChart3,
  Loader2,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Progress } from '@/components/ui/progress'
import type { BatchProgress } from '../PapersDashboard/hooks/useBatchProcessing'
import type { AnalysisBatchProgress } from '../PapersDashboard/hooks/useAnalysisBatchProcessing'

interface BatchProcessingPanelProps {
  batchProgress: BatchProgress | null
  setBatchProgress: (progress: BatchProgress | null) => void
  analysisBatchProgress: AnalysisBatchProgress | null
}

const BatchProcessingPanel: React.FC<BatchProcessingPanelProps> = ({
  batchProgress,
  setBatchProgress,
  analysisBatchProgress,
}) => {
  return (
    <>
      {/* Batch Marker Processing Progress Banner */}
      {batchProgress && (
        <Alert className="mb-4 relative">
          <Cpu className="h-4 w-4" />
          <AlertTitle>
            {batchProgress.isProcessing ? 'Processing Papers with Marker...' : 'Batch Processing Complete'}
          </AlertTitle>
          <AlertDescription>
            <div className="flex items-center gap-4 mt-2">
              <Progress
                value={batchProgress.total > 0 ? ((batchProgress.completed + batchProgress.failed + batchProgress.skipped) / batchProgress.total) * 100 : 0}
                className="flex-1"
              />
              <span className="text-sm whitespace-nowrap">
                {batchProgress.completed}/{batchProgress.total} completed
                {batchProgress.failed > 0 && <span className="text-red-600 ml-1">({batchProgress.failed} failed)</span>}
                {batchProgress.skipped > 0 && <span className="text-yellow-600 ml-1">({batchProgress.skipped} skipped)</span>}
              </span>
            </div>
            {batchProgress.current && (
              <p className="text-sm mt-2 text-muted-foreground">
                <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
                Currently processing: {batchProgress.current.length > 50 ? batchProgress.current.substring(0, 50) + '...' : batchProgress.current}
              </p>
            )}
          </AlertDescription>
          {!batchProgress.isProcessing && (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setBatchProgress(null)
                localStorage.removeItem('batchProcessingProgress')
              }}
              className="absolute top-2 right-2"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </Alert>
      )}

      {/* Analysis Batch Processing Progress Banner */}
      {analysisBatchProgress && (
        <Alert className="mb-4 relative border-purple-200 bg-purple-50 dark:bg-purple-950">
          <BarChart3 className="h-4 w-4 text-purple-600" />
          <AlertTitle className="text-purple-800">
            {analysisBatchProgress.isProcessing ? 'Generating Analyses for Selected Papers...' : 'Batch Analysis Complete'}
          </AlertTitle>
          <AlertDescription>
            <div className="flex items-center gap-4 mt-2">
              <Progress
                value={analysisBatchProgress.totalAnalyses > 0
                  ? (analysisBatchProgress.completedAnalyses / analysisBatchProgress.totalAnalyses) * 100
                  : 0}
                className="flex-1"
              />
              <span className="text-sm whitespace-nowrap text-purple-700">
                Paper {analysisBatchProgress.completedPapers}/{analysisBatchProgress.totalPapers} &#8226;
                Analysis {analysisBatchProgress.completedAnalyses}/{analysisBatchProgress.totalAnalyses}
                {analysisBatchProgress.failed > 0 && <span className="text-red-600 ml-1">({analysisBatchProgress.failed} failed)</span>}
                {analysisBatchProgress.skipped > 0 && <span className="text-yellow-600 ml-1">({analysisBatchProgress.skipped} skipped)</span>}
              </span>
            </div>
            {analysisBatchProgress.currentPaper && (
              <p className="text-sm mt-2 text-purple-600">
                <Loader2 className="h-3 w-3 inline mr-1 animate-spin" />
                {analysisBatchProgress.currentPaper.length > 40
                  ? analysisBatchProgress.currentPaper.substring(0, 40) + '...'
                  : analysisBatchProgress.currentPaper}
                {analysisBatchProgress.currentAnalysis && (
                  <span className="ml-2 text-purple-500">&rarr; {analysisBatchProgress.currentAnalysis}</span>
                )}
              </p>
            )}
          </AlertDescription>
        </Alert>
      )}
    </>
  )
}

export default BatchProcessingPanel
