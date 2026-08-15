import React, { Suspense } from 'react'
import axios from 'axios'
import {
  FileText,
  Upload,
  BookOpen,
  Users,
  Hash,
  FileDown,
  Loader2,
  X,
  Cpu,
  BarChart3,
  RefreshCw,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { cn } from '@/lib/utils'

import PaperUploadModern from './PaperUploadModern'
import UnifiedImportDialog from './UnifiedImportDialog'
import UnifiedModelSelector from './UnifiedModelSelector'

// Lazy-loaded components for code-splitting
const PaperViewerOptimized = React.lazy(() => import('./PaperViewerOptimized'))
import PaperTagSuggestionModal from './PaperTagSuggestionModal'

// Extracted hooks for batch processing and event handling
import { useBatchProcessing } from './PapersDashboard/hooks/useBatchProcessing'
import { useAnalysisBatchProcessing } from './PapersDashboard/hooks/useAnalysisBatchProcessing'
import { usePaperEventListeners } from './PapersDashboard/hooks/usePaperEventListeners'

// Extracted sub-components
import { PaperFacetsPanel, PaperListRenderer, BatchProcessingPanel, ConceptsSidebar } from './papers-dashboard'
import { usePapersDashboard } from './papers-dashboard'

interface FacetedPapersDashboardProps {
  paperType?: 'research' | 'review'
}

const FacetedPapersDashboard: React.FC<FacetedPapersDashboardProps> = ({ paperType = 'research' }) => {
  const dashboard = usePapersDashboard(paperType)

  // Batch Marker processing hook
  const {
    batchProgress,
    setBatchProgress,
    handleBatchProcess,
  } = useBatchProcessing({
    loadPapers: dashboard.loadPapers,
    loadFacets: dashboard.loadFacets,
    setError: dashboard.setError,
  })

  // Batch analysis generation hook
  const {
    selectedPapersForAnalysis,
    analysisBatchProgress,
    togglePaperSelection,
    toggleSelectAllPapers,
    batchGenerateAnalyses,
    analysisModel,
    setAnalysisModel,
  } = useAnalysisBatchProcessing({
    papers: dashboard.papers,
    loadPapers: dashboard.loadPapers,
  })

  // Custom event listeners for paper updates
  usePaperEventListeners({ setPapers: dashboard.setPapers })

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      {/* Left Sidebar - Facets */}
      <PaperFacetsPanel
        facets={dashboard.facets}
        loadingFacets={dashboard.loadingFacets}
        activeFilterCount={dashboard.activeFilterCount}
        selectedAuthors={dashboard.selectedAuthors}
        selectedYears={dashboard.selectedYears}
        selectedConferences={dashboard.selectedConferences}
        selectedAffiliations={dashboard.selectedAffiliations}
        selectedProcessors={dashboard.selectedProcessors}
        showFlagged={dashboard.showFlagged}
        showNoProcessor={dashboard.showNoProcessor}
        showNoYear={dashboard.showNoYear}
        showNoConference={dashboard.showNoConference}
        showNoAffiliation={dashboard.showNoAffiliation}
        showNoAnnotations={dashboard.showNoAnnotations}
        showNoMollickSummary={dashboard.showNoMollickSummary}
        selectedRating={dashboard.selectedRating}
        minRating={dashboard.minRating}
        showUnratedOnly={dashboard.showUnratedOnly}
        expandedFacets={dashboard.expandedFacets}
        clearAllFilters={dashboard.clearAllFilters}
        toggleFacet={dashboard.toggleFacet}
        toggleFacetValue={dashboard.toggleFacetValue}
        setSelectedAuthors={dashboard.setSelectedAuthors}
        setSelectedYears={dashboard.setSelectedYears}
        setSelectedConferences={dashboard.setSelectedConferences}
        setSelectedAffiliations={dashboard.setSelectedAffiliations}
        setSelectedProcessors={dashboard.setSelectedProcessors}
        setShowFlagged={dashboard.setShowFlagged}
        setShowNoProcessor={dashboard.setShowNoProcessor}
        setShowNoYear={dashboard.setShowNoYear}
        setShowNoConference={dashboard.setShowNoConference}
        setShowNoAffiliation={dashboard.setShowNoAffiliation}
        setShowNoAnnotations={dashboard.setShowNoAnnotations}
        setShowNoMollickSummary={dashboard.setShowNoMollickSummary}
        setSelectedRating={dashboard.setSelectedRating}
        setMinRating={dashboard.setMinRating}
        setShowUnratedOnly={dashboard.setShowUnratedOnly}
        setCurrentPage={dashboard.setCurrentPage}
      />

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                {paperType === 'review' ? 'Paper Reviews' : 'Research Papers'}
              </h1>
              <p className="text-gray-600 dark:text-gray-400">
                {paperType === 'review'
                  ? 'Manage papers under review before publication'
                  : 'Upload, analyze, and manage PDF research papers with AI-powered processing'}
              </p>
            </div>
            <div className="flex gap-2">
              <Button
                onClick={() => dashboard.setShowImportDialog(true)}
                variant="outline"
                className="flex items-center gap-2"
              >
                <FileDown className="h-4 w-4" />
                Import Paper
              </Button>
              <Button
                onClick={() => dashboard.setShowUploadModal(true)}
                variant="default"
                className="flex items-center gap-2"
              >
                <Upload className="h-4 w-4" />
                Upload PDF
              </Button>
              <Button
                onClick={() => dashboard.loadPapers()}
                variant="outline"
                disabled={dashboard.loading}
                className="flex items-center gap-2"
              >
                <RefreshCw className={cn("h-4 w-4", dashboard.loading && "animate-spin")} />
                Refresh
              </Button>
              <Button
                onClick={handleBatchProcess}
                variant="outline"
                disabled={batchProgress?.isProcessing || (dashboard.facets?.missing_data?.no_processor || 0) === 0}
                className="flex items-center gap-2"
              >
                <Cpu className={cn("h-4 w-4", batchProgress?.isProcessing && "animate-pulse")} />
                Process All ({dashboard.facets?.missing_data?.no_processor || 0})
              </Button>
              {selectedPapersForAnalysis.size > 0 && (
                <>
                  <div className="min-w-[200px]">
                    <UnifiedModelSelector
                      taskType="paper_analysis"
                      value={analysisModel}
                      onValueChange={setAnalysisModel}
                      compact={true}
                      disabled={analysisBatchProgress?.isProcessing}
                    />
                  </div>
                  <Button
                    onClick={batchGenerateAnalyses}
                    variant="default"
                    disabled={analysisBatchProgress?.isProcessing}
                    className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700"
                  >
                    <BarChart3 className={cn("h-4 w-4", analysisBatchProgress?.isProcessing && "animate-pulse")} />
                    Generate Analyses ({selectedPapersForAnalysis.size})
                  </Button>
                </>
              )}
            </div>
          </div>

          {/* Batch Processing Progress Banners */}
          <BatchProcessingPanel
            batchProgress={batchProgress}
            setBatchProgress={setBatchProgress}
            analysisBatchProgress={analysisBatchProgress}
          />

          {/* Statistics Cards */}
          {dashboard.stats && (
            <div className="grid grid-cols-4 gap-4 mb-6">
              <Card className="bg-white dark:bg-gray-950">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Total Papers</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{dashboard.stats.total_papers}</p>
                    </div>
                    <FileText className="h-8 w-8 text-blue-500 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white dark:bg-gray-950">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Authors</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{dashboard.stats.total_authors}</p>
                    </div>
                    <Users className="h-8 w-8 text-green-500 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white dark:bg-gray-950">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Concepts</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{dashboard.stats.total_concept_tags || dashboard.stats.total_tags || 0}</p>
                    </div>
                    <Hash className="h-8 w-8 text-purple-500 opacity-50" />
                  </div>
                </CardContent>
              </Card>
              <Card className="bg-white dark:bg-gray-950">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Snippets</p>
                      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{dashboard.stats.total_snippets}</p>
                    </div>
                    <BookOpen className="h-8 w-8 text-orange-500 opacity-50" />
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Main Content Area */}
          <div className="space-y-4">
            {/* Search Bar and Results Count */}
            <div className="flex items-center gap-4">
              <div className="flex-1 relative">
                <Input
                  placeholder={dashboard.searchMode === 'content' ? "Search in paper content..." : dashboard.searchMode === 'semantic' ? "Search title & content..." : "Search paper titles..."}
                  value={dashboard.searchTerm}
                  onChange={(e) => {
                    dashboard.setSearchTerm(e.target.value)
                    dashboard.setCurrentPage(1)
                  }}
                  className="pr-24"
                />
                <div className="absolute right-1 top-1/2 -translate-y-1/2 flex items-center gap-1">
                  {dashboard.searchTerm && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        dashboard.setSearchTerm('')
                        dashboard.setCurrentPage(1)
                      }}
                      className="h-7 w-7 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  )}
                  <Select value={dashboard.searchMode} onValueChange={(value: any) => dashboard.setSearchMode(value)}>
                    <SelectTrigger className="w-24 h-7 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="standard">Title</SelectItem>
                      <SelectItem value="content">Content</SelectItem>
                      <SelectItem value="semantic">All</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              {/* Sorting Controls */}
              <Select value={dashboard.sortBy} onValueChange={(value: any) => dashboard.setSortBy(value)}>
                <SelectTrigger className="w-44">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="created_at">Date Added</SelectItem>
                  <SelectItem value="publication_date">Publication Date</SelectItem>
                  <SelectItem value="title">Title</SelectItem>
                  <SelectItem value="rating">Rating (Highest First)</SelectItem>
                </SelectContent>
              </Select>
              <Select value={dashboard.sortOrder} onValueChange={(value: any) => dashboard.setSortOrder(value)}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="desc">Newest First</SelectItem>
                  <SelectItem value="asc">Oldest First</SelectItem>
                </SelectContent>
              </Select>

              {/* Results Counter */}
              <div className="flex items-center gap-2 text-sm font-medium text-gray-700 dark:text-gray-300 whitespace-nowrap">
                <FileText className="h-4 w-4" />
                <span>{dashboard.totalPapers} {dashboard.totalPapers === 1 ? 'paper' : 'papers'}</span>
                {dashboard.activeFilterCount > 0 && (
                  <Badge variant="secondary" className="ml-1">
                    {dashboard.activeFilterCount} {dashboard.activeFilterCount === 1 ? 'filter' : 'filters'} applied
                  </Badge>
                )}
              </div>
            </div>

            {/* Active Concept Filters */}
            {dashboard.selectedTags.size > 0 && (
              <div className="flex flex-wrap items-center gap-2 mb-4">
                <span className="text-sm font-medium text-gray-600 dark:text-gray-400">Active concepts:</span>
                {Array.from(dashboard.selectedTags).map(tagId => {
                  const concept = dashboard.facets?.concepts?.find((c: any) => (c.concept_id || c.slug) === tagId)
                  return (
                    <Badge
                      key={tagId}
                      variant="default"
                      className="bg-blue-100 dark:bg-blue-950 text-blue-800 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-900 cursor-pointer"
                      onClick={() => dashboard.toggleFacetValue('tag', tagId)}
                    >
                      {concept?.display_name || tagId}
                      <X className="h-3 w-3 ml-1" />
                    </Badge>
                  )
                })}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => dashboard.setSelectedTags(new Set())}
                  className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
                >
                  Clear all
                </Button>
              </div>
            )}

            {/* Papers List */}
            <PaperListRenderer
              papers={dashboard.papers}
              loading={dashboard.loading}
              error={dashboard.error}
              processingMessage={dashboard.processingMessage}
              processingPapers={dashboard.processingPapers}
              facets={dashboard.facets}
              currentPage={dashboard.currentPage}
              totalPapers={dashboard.totalPapers}
              totalPages={dashboard.totalPages}
              pageSize={dashboard.pageSize}
              setCurrentPage={dashboard.setCurrentPage}
              selectedPapersForAnalysis={selectedPapersForAnalysis}
              togglePaperSelection={togglePaperSelection}
              toggleSelectAllPapers={toggleSelectAllPapers}
              expandedTags={dashboard.expandedTags}
              toggleExpandedTags={dashboard.toggleExpandedTags}
              expandedSummaries={dashboard.expandedSummaries}
              editingSummaries={dashboard.editingSummaries}
              editedSummaryContent={dashboard.editedSummaryContent}
              savingSummaries={dashboard.savingSummaries}
              toggleSummary={dashboard.toggleSummary}
              startEditingSummary={dashboard.startEditingSummary}
              cancelEditingSummary={dashboard.cancelEditingSummary}
              saveSummaryEdit={dashboard.saveSummaryEdit}
              setEditedSummaryContent={dashboard.setEditedSummaryContent}
              setExpandedSummaries={dashboard.setExpandedSummaries}
              setSelectedPaperId={dashboard.setSelectedPaperId}
              setSelectedPaperForTags={dashboard.setSelectedPaperForTags}
              setShowTagSuggestionModal={dashboard.setShowTagSuggestionModal}
              setSelectedTags={dashboard.setSelectedTags}
              togglePaperFlag={dashboard.togglePaperFlag}
              handleRatePaper={dashboard.handleRatePaper}
              handleDeletePaper={dashboard.handleDeletePaper}
              handleProcessPaper={dashboard.handleProcessPaper}
              formatDate={dashboard.formatDate}
            />
          </div>
        </div>
      </div>

      {/* Right Sidebar - Concepts */}
      <ConceptsSidebar
        facets={dashboard.facets}
        loadingFacets={dashboard.loadingFacets}
        selectedTags={dashboard.selectedTags}
        conceptSearch={dashboard.conceptSearch}
        showHierarchy={dashboard.showHierarchy}
        setConceptSearch={dashboard.setConceptSearch}
        setShowHierarchy={dashboard.setShowHierarchy}
        setSelectedTags={dashboard.setSelectedTags}
        setCurrentPage={dashboard.setCurrentPage}
        toggleFacetValue={dashboard.toggleFacetValue}
      />

      {/* Upload Modal */}
      {dashboard.showUploadModal && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-950 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-auto shadow-2xl">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Upload PDF Paper</h2>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => dashboard.setShowUploadModal(false)}
                  className="h-8 w-8 p-0"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <PaperUploadModern paperType={paperType} onUploadComplete={() => {
                dashboard.handleUploadComplete()
                dashboard.setShowUploadModal(false)
              }} />
            </div>
          </div>
        </div>
      )}

      {/* Paper Viewer Modal - Lazy loaded */}
      {dashboard.selectedPaperId && (
        <div className="fixed inset-0 z-50 bg-black bg-opacity-50 flex items-center justify-center p-4">
          <div className="bg-white dark:bg-gray-950 rounded-lg w-full max-w-7xl max-h-[90vh] overflow-auto shadow-2xl">
            <Suspense fallback={
              <div className="flex items-center justify-center h-96">
                <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                <span className="ml-2 text-gray-600 dark:text-gray-400">Loading Paper Viewer...</span>
              </div>
            }>
              <PaperViewerOptimized
                paperId={dashboard.selectedPaperId}
                onClose={() => dashboard.setSelectedPaperId(null)}
                onMetadataUpdate={async () => {
                  try {
                    const response = await axios.get(`/api/papers/${dashboard.selectedPaperId}`)
                    const updatedPaper = response.data
                    dashboard.setPapers((prevPapers: any[]) =>
                      prevPapers.map(p =>
                        p.id === dashboard.selectedPaperId
                          ? { ...p, tags: updatedPaper.tags, ...updatedPaper }
                          : p
                      )
                    )
                    dashboard.loadFacets()
                    dashboard.loadStats()
                  } catch (error) {
                    console.error('Error updating paper:', error)
                  }
                }}
              />
            </Suspense>
          </div>
        </div>
      )}

      {/* Paper Tag Suggestion Modal */}
      {dashboard.selectedPaperForTags && (
        <PaperTagSuggestionModal
          paper={dashboard.selectedPaperForTags}
          isOpen={dashboard.showTagSuggestionModal}
          onClose={() => {
            dashboard.setShowTagSuggestionModal(false)
            dashboard.setSelectedPaperForTags(null)
          }}
          onTagsUpdated={() => {
            dashboard.loadPapers()
            dashboard.loadFacets()
          }}
        />
      )}

      {/* Unified Import Dialog */}
      <UnifiedImportDialog
        isOpen={dashboard.showImportDialog}
        onClose={() => dashboard.setShowImportDialog(false)}
        onImportSuccess={(paperId) => {
          dashboard.loadPapers()
          dashboard.loadStats()
          dashboard.loadFacets()
          dashboard.setSelectedPaperId(paperId)
        }}
      />
    </div>
  )
}

export default FacetedPapersDashboard
