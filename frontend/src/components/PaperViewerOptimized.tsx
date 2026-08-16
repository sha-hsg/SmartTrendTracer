import React, { useState, useRef } from "react";

import "katex/dist/katex.min.css";
import "highlight.js/styles/github-dark.css";

import {
  FileText,
  X,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";

// Extracted PaperViewer sub-components and hooks
import PaperDetailsSidebar from "./PaperViewer/PaperDetailsSidebar";
import { PaperDialogs } from "./PaperViewer/PaperDialogs";
import PaperTabsContent from "./PaperViewer/PaperTabsContent";
import { useKeyboardNavigation } from "./PaperViewer/hooks/useKeyboardNavigation";
import { useTableOfContents } from "./PaperViewer/hooks/useTableOfContents";
import { usePaperData } from "./PaperViewer/hooks/usePaperData";

interface PaperViewerOptimizedProps {
  paperId: string | number; // Support both MongoDB ObjectId strings and legacy integer IDs
  onClose?: () => void;
  onMetadataUpdate?: () => void;
}

const PaperViewerOptimized: React.FC<PaperViewerOptimizedProps> = ({
  paperId,
  onClose,
  onMetadataUpdate,
}) => {
  const [activeTab, setActiveTab] = useState("pdf");
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const markdownContainerRef = useRef<HTMLDivElement>(null);

  // Use the extracted custom hook for all paper data and operations
  const paperData = usePaperData(paperId, onMetadataUpdate);

  const {
    paper,
    setPaper,
    loading,
    error,
    pdfAvailable,
    setPdfAvailable,
    isProcessing,
    setIsProcessing,
    processingStartTime,
    setProcessingStartTime,
    processingError,
    setProcessingError,
    processingWithMarker,
    processingWithMinerU,
    processingWithAuto,
    isAnyProcessing,
    newTag,
    setNewTag,
    addingTag,
    handleAddTag,
    handleRemoveTag,
    handleCreateTagFromPDF,
    editingMetadata,
    setEditingMetadata,
    editedMetadata,
    setEditedMetadata,
    handleEditMetadata,
    handleSaveMetadata,
    extractingAuthors,
    handleExtractAuthors,
    extractingAffiliations,
    showAffiliationDialog,
    setShowAffiliationDialog,
    affiliationSuggestions,
    selectedAffiliations,
    handleExtractAffiliations,
    handleApplyAffiliations,
    toggleAffiliationSelection,
    handleToggleFlag,
    handleSetRating,
    editingImportUrl,
    setEditingImportUrl,
    editedImportUrl,
    setEditedImportUrl,
    savingImportUrl,
    handleSaveImportUrl,
    expandedSections,
    editingSectionId,
    editedSectionContent,
    setEditedSectionContent,
    editingSectionTitleId,
    editedSectionTitle,
    setEditedSectionTitle,
    savingSection,
    extractingSections,
    toggleSection,
    handleEditSection,
    handleEditSectionTitle,
    handleSaveSectionTitle,
    handleCancelSectionTitleEdit,
    handleSaveSection,
    handleCancelSectionEdit,
    handleExtractSections,
    isEditingMarkdown,
    setIsEditingMarkdown,
    editedMarkdown,
    setEditedMarkdown,
    savingMarkdown,
    handleSaveMarkdown,
    selectedText,
    setSelectedText,
    snippetAnnotation,
    setSnippetAnnotation,
    snippetCategory,
    setSnippetCategory,
    creatingSnippet,
    handleCreateSnippet,
    copiedText,
    handleCopyText,
    loadPaperDetails,
    pollProcessingStatus,
    pollingIntervalRef,
    showMarkdownContextMenu,
    markdownContextMenuPosition,
    showMarkdownTagDialog,
    markdownTagText,
    setMarkdownTagText,
    creatingMarkdownTag,
    handleMarkdownContextMenu,
    handleMarkdownMenuAction,
    handleCreateMarkdownTag,
    handleMarkdownTagDialogClose,
    editingConceptTag,
    setEditingConceptTag,
    showConceptEditModal,
    setShowConceptEditModal,
    showTagModal,
    setShowTagModal,
    showEntityModal,
    setShowEntityModal,
    showDBLPModal,
    setShowDBLPModal,
    showMarkerModal,
    setShowMarkerModal,
  } = paperData;

  // Content for TOC (needed for keyboard navigation)
  const content = paper?.markdown_content || paper?.content;
  const { navigateToSection } = useTableOfContents(content, markdownContainerRef);

  // Keyboard navigation
  useKeyboardNavigation({
    activeTab,
    isEditingMarkdown,
    onClose,
    hasContent: !!paper?.content,
    setActiveTab,
    setShowTagModal,
    setShowEntityModal,
    navigateToSection,
    markdownContainerRef,
  });

  // Handle snippet action from markdown context menu (needs activeTab setter)
  const handleMarkdownMenuActionWithTab = (action: string) => {
    if (action === "snippet") {
      handleMarkdownMenuAction(action);
      setActiveTab("snippets");
    } else {
      handleMarkdownMenuAction(action);
    }
  };

  // Enhanced loading state with skeleton
  if (loading) {
    return (
      <div className="h-[calc(100vh-4rem)] flex bg-gray-50 dark:bg-gray-900">
        {/* Skeleton Sidebar */}
        <div className="w-[440px] bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-800 p-4 space-y-4 animate-pulse">
          <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-3/4"></div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2"></div>
            <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/3"></div>
            <div className="h-20 bg-gray-200 dark:bg-gray-800 rounded"></div>
          </div>
          <div className="space-y-2">
            <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/2"></div>
            <div className="flex flex-wrap gap-2">
              <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-16"></div>
              <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-20"></div>
              <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-12"></div>
            </div>
          </div>
        </div>

        {/* Skeleton Main Content */}
        <div className="flex-1 flex flex-col">
          <div className="p-4 border-b dark:border-gray-800 bg-white dark:bg-gray-950">
            <div className="h-6 bg-gray-200 dark:bg-gray-800 rounded w-1/4 animate-pulse"></div>
          </div>
          <div className="flex-1 p-4">
            <div className="h-full bg-white dark:bg-gray-950 rounded-lg border dark:border-gray-800 p-6">
              <div className="space-y-4 animate-pulse">
                <div className="h-8 bg-gray-200 dark:bg-gray-800 rounded w-full"></div>
                <div className="space-y-2">
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-full"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-5/6"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-4/5"></div>
                </div>
                <div className="h-48 bg-gray-200 dark:bg-gray-800 rounded"></div>
              </div>
            </div>
          </div>
        </div>

        {/* Close button */}
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-50 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm rounded-full p-2.5 shadow-lg hover:shadow-xl transition-all duration-200 group border border-gray-200 dark:border-gray-700"
            title="Close viewer (Esc)"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
        )}
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="h-[calc(100vh-4rem)] flex items-center justify-center bg-white dark:bg-gray-950 relative">
        <div className="max-w-md w-full px-6">
          <Alert variant="destructive" className="shadow-sm">
            <AlertDescription>
              {error || "Paper not found"}
            </AlertDescription>
          </Alert>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="absolute top-4 right-4 z-50 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm rounded-full p-2.5 shadow-lg hover:shadow-xl transition-all duration-200 group border border-gray-200 dark:border-gray-700"
            title="Close viewer (Esc)"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-300" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="h-[calc(100vh-4rem)] flex bg-gray-50 dark:bg-gray-900 relative">
      {error && (
        <div className="absolute top-4 left-1/2 z-40 w-full max-w-2xl -translate-x-1/2 px-4">
          <Alert variant="destructive" className="shadow-sm">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </div>
      )}

      {/* Paper Details Sidebar */}
      <PaperDetailsSidebar
        paper={paper}
        paperId={paperId}
        sidebarCollapsed={sidebarCollapsed}
        setSidebarCollapsed={setSidebarCollapsed}
        isProcessing={isProcessing}
        setIsProcessing={setIsProcessing}
        processingStartTime={processingStartTime}
        setProcessingStartTime={setProcessingStartTime}
        processingError={processingError}
        setProcessingError={setProcessingError}
        processingWithMarker={processingWithMarker}
        processingWithMinerU={processingWithMinerU}
        processingWithAuto={processingWithAuto}
        isAnyProcessing={isAnyProcessing}
        newTag={newTag}
        setNewTag={setNewTag}
        addingTag={addingTag}
        extractingAuthors={extractingAuthors}
        extractingAffiliations={extractingAffiliations}
        editingImportUrl={editingImportUrl}
        setEditingImportUrl={setEditingImportUrl}
        editedImportUrl={editedImportUrl}
        setEditedImportUrl={setEditedImportUrl}
        savingImportUrl={savingImportUrl}
        setPaper={setPaper}
        handleEditMetadata={handleEditMetadata}
        handleToggleFlag={handleToggleFlag}
        handleSetRating={handleSetRating}
        handleExtractAuthors={handleExtractAuthors}
        handleExtractAffiliations={handleExtractAffiliations}
        handleAddTag={handleAddTag}
        handleRemoveTag={handleRemoveTag}
        handleSaveImportUrl={handleSaveImportUrl}
        setShowTagModal={setShowTagModal}
        setShowEntityModal={setShowEntityModal}
        setShowDBLPModal={setShowDBLPModal}
        setShowMarkerModal={setShowMarkerModal}
        setEditingConceptTag={setEditingConceptTag}
        setShowConceptEditModal={setShowConceptEditModal}
        loadPaperDetails={loadPaperDetails}
        pollProcessingStatus={pollProcessingStatus}
        pollingIntervalRef={pollingIntervalRef}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Enhanced Header Bar with Keyboard Shortcuts */}
        <div className="bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800 px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {sidebarCollapsed && (
              <div className="flex items-center gap-2">
                <FileText className="h-5 w-5 text-blue-600" />
                <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 truncate max-w-md">
                  {paper.title}
                </h2>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div className="text-xs text-gray-500 dark:text-gray-400 hidden sm:flex items-center gap-2">
              <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                Ctrl+T
              </kbd>
              <span>Tags</span>
              <kbd className="px-2 py-1 bg-gray-100 dark:bg-gray-800 rounded text-xs">
                Ctrl+1-5
              </kbd>
              <span>Tabs</span>
            </div>
            {onClose && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onClose}
                title="Close (Esc)"
              >
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Content Tabs - Full Height */}
        <div className="flex-1 flex flex-col">
          <PaperTabsContent
            paper={paper}
            paperId={paperId}
            activeTab={activeTab}
            setActiveTab={setActiveTab}
            pdfAvailable={pdfAvailable}
            setPdfAvailable={setPdfAvailable}
            isEditingMarkdown={isEditingMarkdown}
            setIsEditingMarkdown={setIsEditingMarkdown}
            editedMarkdown={editedMarkdown}
            setEditedMarkdown={setEditedMarkdown}
            savingMarkdown={savingMarkdown}
            handleSaveMarkdown={handleSaveMarkdown}
            isAnyProcessing={isAnyProcessing}
            setIsProcessing={setIsProcessing}
            setProcessingStartTime={setProcessingStartTime}
            copiedText={copiedText}
            handleCopyText={handleCopyText}
            handleMarkdownContextMenu={handleMarkdownContextMenu}
            markdownContainerRef={markdownContainerRef}
            expandedSections={expandedSections}
            editingSectionId={editingSectionId}
            editedSectionContent={editedSectionContent}
            setEditedSectionContent={setEditedSectionContent}
            editingSectionTitleId={editingSectionTitleId}
            editedSectionTitle={editedSectionTitle}
            setEditedSectionTitle={setEditedSectionTitle}
            savingSection={savingSection}
            extractingSections={extractingSections}
            toggleSection={toggleSection}
            handleEditSection={handleEditSection}
            handleEditSectionTitle={handleEditSectionTitle}
            handleSaveSectionTitle={handleSaveSectionTitle}
            handleCancelSectionTitleEdit={handleCancelSectionTitleEdit}
            handleSaveSection={handleSaveSection}
            handleCancelSectionEdit={handleCancelSectionEdit}
            handleExtractSections={handleExtractSections}
            selectedText={selectedText}
            setSelectedText={setSelectedText}
            snippetAnnotation={snippetAnnotation}
            setSnippetAnnotation={setSnippetAnnotation}
            snippetCategory={snippetCategory}
            setSnippetCategory={setSnippetCategory}
            creatingSnippet={creatingSnippet}
            handleCreateSnippet={handleCreateSnippet}
            handleCreateTagFromPDF={handleCreateTagFromPDF}
            loadPaperDetails={loadPaperDetails}
          />
        </div>
      </div>

      {/* All Dialogs and Modals */}
      <PaperDialogs
        paper={paper}
        paperId={typeof paperId === 'string' ? parseInt(paperId) || 0 : paperId}
        setPaper={setPaper}
        loadPaperDetails={loadPaperDetails}
        onMetadataUpdate={onMetadataUpdate}
        showMarkdownContextMenu={showMarkdownContextMenu}
        markdownContextMenuPosition={markdownContextMenuPosition}
        handleMarkdownMenuAction={handleMarkdownMenuActionWithTab}
        showMarkdownTagDialog={showMarkdownTagDialog}
        markdownTagText={markdownTagText}
        setMarkdownTagText={setMarkdownTagText}
        creatingMarkdownTag={creatingMarkdownTag}
        handleMarkdownTagDialogClose={handleMarkdownTagDialogClose}
        handleCreateMarkdownTag={handleCreateMarkdownTag}
        editingMetadata={editingMetadata}
        setEditingMetadata={setEditingMetadata}
        editedMetadata={editedMetadata}
        setEditedMetadata={setEditedMetadata}
        handleSaveMetadata={handleSaveMetadata}
        showTagModal={showTagModal}
        setShowTagModal={setShowTagModal}
        showEntityModal={showEntityModal}
        setShowEntityModal={setShowEntityModal}
        showDBLPModal={showDBLPModal}
        setShowDBLPModal={setShowDBLPModal}
        showAffiliationDialog={showAffiliationDialog}
        setShowAffiliationDialog={setShowAffiliationDialog}
        affiliationSuggestions={affiliationSuggestions}
        selectedAffiliations={selectedAffiliations}
        toggleAffiliationSelection={toggleAffiliationSelection}
        handleApplyAffiliations={handleApplyAffiliations}
        showMarkerModal={showMarkerModal}
        setShowMarkerModal={setShowMarkerModal}
        editingConceptTag={editingConceptTag}
        showConceptEditModal={showConceptEditModal}
        setShowConceptEditModal={setShowConceptEditModal}
        setEditingConceptTag={setEditingConceptTag}
      />
    </div>
  );
};

export default PaperViewerOptimized;
