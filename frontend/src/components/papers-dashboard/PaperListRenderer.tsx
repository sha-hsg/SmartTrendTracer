import React from 'react'
import {
  Loader2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Checkbox } from '@/components/ui/checkbox'
import type { Paper, Facets } from './types'
import PaperCard from './PaperCard'

interface PaperListRendererProps {
  papers: Paper[]
  loading: boolean
  error: string | null
  processingMessage: string | null
  processingPapers: Set<number>
  facets: Facets | null

  // Pagination
  currentPage: number
  totalPapers: number
  totalPages: number
  pageSize: number
  setCurrentPage: (page: number | ((prev: number) => number)) => void

  // Selection for batch analysis
  selectedPapersForAnalysis: Set<number>
  togglePaperSelection: (paperId: number) => void
  toggleSelectAllPapers: () => void

  // Tags UI state
  expandedTags: Set<number>
  toggleExpandedTags: (paperId: number) => void

  // Summary state
  expandedSummaries: Set<string>
  editingSummaries: Set<string>
  editedSummaryContent: Record<string, string>
  savingSummaries: Set<string>
  toggleSummary: (paperId: string) => void
  startEditingSummary: (paperId: string, content: string) => void
  cancelEditingSummary: (paperId: string) => void
  saveSummaryEdit: (paperId: string) => void
  setEditedSummaryContent: React.Dispatch<React.SetStateAction<Record<string, string>>>
  setExpandedSummaries: React.Dispatch<React.SetStateAction<Set<string>>>

  // Paper actions
  setSelectedPaperId: (id: number | string | null) => void
  setSelectedPaperForTags: (paper: any) => void
  setShowTagSuggestionModal: (v: boolean) => void
  setSelectedTags: (s: Set<string>) => void
  togglePaperFlag: (paperId: number, e: React.MouseEvent) => void
  handleRatePaper: (paperId: number | string, rating: number, e?: React.MouseEvent) => void
  handleDeletePaper: (paperId: number, e: React.MouseEvent) => void
  handleProcessPaper: (paperId: number, processor: 'marker' | 'mineru', e?: React.MouseEvent) => void
  formatDate: (dateString: string) => string
}

const PaperListRenderer: React.FC<PaperListRendererProps> = ({
  papers,
  loading,
  error,
  processingMessage,
  processingPapers,
  currentPage,
  totalPapers,
  totalPages,
  pageSize,
  setCurrentPage,
  selectedPapersForAnalysis,
  togglePaperSelection,
  toggleSelectAllPapers,
  expandedTags,
  toggleExpandedTags,
  expandedSummaries,
  editingSummaries,
  editedSummaryContent,
  savingSummaries,
  toggleSummary,
  startEditingSummary,
  cancelEditingSummary,
  saveSummaryEdit,
  setEditedSummaryContent,
  setExpandedSummaries,
  setSelectedPaperId,
  setSelectedPaperForTags,
  setShowTagSuggestionModal,
  setSelectedTags,
  togglePaperFlag,
  handleRatePaper,
  handleDeletePaper,
  handleProcessPaper,
  formatDate,
}) => {
  const getTagColor = (_tag: string, _index: number) => {
    return 'border-blue-200 text-blue-800 bg-blue-50 dark:bg-blue-950 hover:bg-blue-100'
  }

  return (
    <>
      {/* Processing Message */}
      {processingMessage && (
        <Alert className={processingMessage.includes('Error') ? "border-red-200 bg-red-50 dark:bg-red-950" : processingMessage.includes('Successfully') ? "border-green-200 bg-green-50" : "border-blue-200 bg-blue-50 dark:bg-blue-950"}>
          <AlertDescription className={processingMessage.includes('Error') ? "text-red-800" : processingMessage.includes('Successfully') ? "text-green-800" : "text-blue-800"}>
            {processingMessage}
          </AlertDescription>
        </Alert>
      )}

      {/* Error */}
      {error && (
        <Alert className="border-red-200 bg-red-50 dark:bg-red-950">
          <AlertDescription className="text-red-800">
            {error}
          </AlertDescription>
        </Alert>
      )}

      {loading ? (
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
              <p className="text-gray-500 dark:text-gray-400">Loading papers...</p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Select All Header */}
          {papers.length > 0 && (
            <div className="flex items-center gap-2 mb-2 px-1">
              <Checkbox
                id="select-all-papers"
                checked={selectedPapersForAnalysis.size === papers.length && papers.length > 0}
                onCheckedChange={toggleSelectAllPapers}
                className="h-4 w-4"
              />
              <label
                htmlFor="select-all-papers"
                className="text-sm text-gray-600 dark:text-gray-400 cursor-pointer select-none"
              >
                Select all ({papers.length}) for batch analysis
              </label>
              {selectedPapersForAnalysis.size > 0 && (
                <Badge variant="secondary" className="ml-2 bg-purple-100 text-purple-700">
                  {selectedPapersForAnalysis.size} selected
                </Badge>
              )}
            </div>
          )}

          <div className="grid gap-3">
            {papers.map((paper) => (
              <PaperCard
                key={paper.id}
                paper={paper}
                processingPapers={processingPapers}
                selectedPapersForAnalysis={selectedPapersForAnalysis}
                togglePaperSelection={togglePaperSelection}
                expandedTags={expandedTags}
                toggleExpandedTags={toggleExpandedTags}
                expandedSummaries={expandedSummaries}
                editingSummaries={editingSummaries}
                editedSummaryContent={editedSummaryContent}
                savingSummaries={savingSummaries}
                toggleSummary={toggleSummary}
                startEditingSummary={startEditingSummary}
                cancelEditingSummary={cancelEditingSummary}
                saveSummaryEdit={saveSummaryEdit}
                setEditedSummaryContent={setEditedSummaryContent}
                setExpandedSummaries={setExpandedSummaries}
                setSelectedPaperId={setSelectedPaperId}
                setSelectedPaperForTags={setSelectedPaperForTags}
                setShowTagSuggestionModal={setShowTagSuggestionModal}
                setSelectedTags={setSelectedTags}
                togglePaperFlag={togglePaperFlag}
                handleRatePaper={handleRatePaper}
                handleDeletePaper={handleDeletePaper}
                handleProcessPaper={handleProcessPaper}
                formatDate={formatDate}
                getTagColor={getTagColor}
              />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between bg-white dark:bg-gray-950 rounded-lg p-4">
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Showing {((currentPage - 1) * pageSize) + 1}-{Math.min(currentPage * pageSize, totalPapers)} of {totalPapers} papers
              </p>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((prev: number) => Math.max(1, prev - 1))}
                  disabled={currentPage === 1}
                >
                  Previous
                </Button>
                <span className="text-sm">
                  Page {currentPage} of {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((prev: number) => Math.min(totalPages, prev + 1))}
                  disabled={currentPage === totalPages}
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </>
  )
}

export default PaperListRenderer
