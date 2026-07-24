import React from 'react'
import {
  Loader2,
  Download,
  Sparkles,
  Minimize2,
  Trash2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import ModelSelector from '../ModelSelector'
import type { AnalysisType, GeneratedAnalysis, BatchProgress } from './constants'

interface AnalysisGenerationControlsProps {
  paperId: string | number
  hasContent: boolean
  selectedCategory: string
  availableAnalyses: Record<string, AnalysisType[]>
  generatedAnalyses: Record<string, GeneratedAnalysis>
  loadingAnalyses: Set<string>
  expandedAnalyses: Set<string>
  expandedFreeAnalyses: Set<string>
  batchProgress: BatchProgress
  selectedModel: string
  onSetSelectedModel: (model: string) => void
  onSetExpandedAnalyses: (set: Set<string>) => void
  onSetExpandedFreeAnalyses: (set: Set<string>) => void
  onSetGeneratedAnalyses: (analyses: Record<string, GeneratedAnalysis>) => void
  onGenerateAllAnalyses: () => void
  onGenerateMultipleAnalyses: (category: string) => void
  onExportAllAnalysesAsMarkdown: () => void
}

export const AnalysisGenerationControls: React.FC<AnalysisGenerationControlsProps> = ({
  paperId,
  hasContent,
  selectedCategory,
  availableAnalyses,
  generatedAnalyses,
  loadingAnalyses,
  expandedAnalyses,
  expandedFreeAnalyses,
  batchProgress,
  selectedModel,
  onSetSelectedModel,
  onSetExpandedAnalyses,
  onSetExpandedFreeAnalyses,
  onSetGeneratedAnalyses,
  onGenerateAllAnalyses,
  onGenerateMultipleAnalyses,
  onExportAllAnalysesAsMarkdown,
}) => {
  return (
    <>
      <div className="flex items-center gap-2">
        {(expandedAnalyses.size > 0 || expandedFreeAnalyses.size > 0) && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => {
              onSetExpandedAnalyses(new Set())
              onSetExpandedFreeAnalyses(new Set())
            }}
            title="Collapse all analyses"
          >
            <Minimize2 className="h-4 w-4 mr-1" />
            Collapse All
          </Button>
        )}
        {Object.keys(generatedAnalyses).length > 0 && (
          <Button
            size="sm"
            variant="outline"
            onClick={onExportAllAnalysesAsMarkdown}
            title="Export all analyses as Markdown file"
          >
            <Download className="h-4 w-4 mr-1" />
            Export MD
          </Button>
        )}
        {Object.keys(generatedAnalyses).length > 0 && (
          <Button
            size="sm"
            variant="outline"
            className="text-red-600 hover:text-red-700 hover:bg-red-50"
            disabled={loadingAnalyses.size > 0}
            onClick={async () => {
              if (!confirm(`Delete all ${Object.keys(generatedAnalyses).length} analyses? This cannot be undone.`)) return
              try {
                const axios = (await import('axios')).default
                await axios.delete(`/api/papers/${paperId}/analyses`)
                onSetGeneratedAnalyses({})
                onSetExpandedAnalyses(new Set())
              } catch (err) {
                console.error('Failed to clear analyses:', err)
                alert('Failed to clear analyses')
              }
            }}
          >
            <Trash2 className="h-4 w-4 mr-1" />
            Clear All
          </Button>
        )}
        {selectedCategory === 'all' ? (
        <div className="flex flex-col gap-2">
          <Button
            size="sm"
            onClick={() => onGenerateAllAnalyses()}
            disabled={loadingAnalyses.size > 0 || !hasContent}
            variant="default"
          >
            {loadingAnalyses.size > 0 ? (
              <>
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                Generating All...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4 mr-1" />
                Generate All Analyses
              </>
            )}
          </Button>

          {batchProgress.total > 0 && (
            <div className="min-w-[250px] space-y-1">
              <div className="flex items-center justify-between text-xs text-gray-600">
                <span>
                  {batchProgress.completed} of {batchProgress.total} completed
                  {batchProgress.skipped > 0 && ` (${batchProgress.skipped} skipped)`}
                </span>
                <span>{Math.round((batchProgress.completed / batchProgress.total) * 100)}%</span>
              </div>
              <Progress value={(batchProgress.completed / batchProgress.total) * 100} className="h-2" />
              {batchProgress.current && (
                <p className="text-xs text-blue-600 font-medium">
                  Generating: {batchProgress.current}
                </p>
              )}
            </div>
          )}
        </div>
      ) : (
        availableAnalyses[selectedCategory] && (
          <div className="flex flex-col gap-2">
            <Button
              size="sm"
              onClick={() => onGenerateMultipleAnalyses(selectedCategory)}
              disabled={loadingAnalyses.size > 0 || !hasContent}
            >
              {loadingAnalyses.size > 0 ? (
                <>
                  <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-1" />
                  Generate All in Category
                </>
              )}
            </Button>

            {batchProgress.total > 0 && (
              <div className="min-w-[250px] space-y-1">
                <div className="flex items-center justify-between text-xs text-gray-600">
                  <span>
                    {batchProgress.completed} of {batchProgress.total} completed
                    {batchProgress.skipped > 0 && ` (${batchProgress.skipped} skipped)`}
                  </span>
                  <span>{Math.round((batchProgress.completed / batchProgress.total) * 100)}%</span>
                </div>
                <Progress value={(batchProgress.completed / batchProgress.total) * 100} className="h-2" />
                {batchProgress.current && (
                  <p className="text-xs text-blue-600 font-medium">
                    Generating: {batchProgress.current}
                  </p>
                )}
              </div>
            )}
          </div>
        )
      )}
      </div>

      <ModelSelector
        value={selectedModel}
        onValueChange={onSetSelectedModel}
        task="paperAnalysis"
        label="AI Model for Analysis"
        persist={true}
      />
    </>
  )
}
