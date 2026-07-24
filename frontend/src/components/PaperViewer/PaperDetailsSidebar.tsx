import React from "react";
import {
  FileText,
  ChevronRight,
  ChevronLeft,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import PaperMetadataSection from "./PaperMetadataSection";
import PaperConceptsSection from "./PaperConceptsSection";
import type { Paper } from "./types";

interface PaperDetailsSidebarProps {
  paper: Paper;
  paperId: string | number;
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (collapsed: boolean) => void;
  // Processing state
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
  processingStartTime: Date | null;
  setProcessingStartTime: (time: Date | null) => void;
  processingError: string | null;
  setProcessingError: (error: string | null) => void;
  processingWithMarker: boolean;
  processingWithMinerU: boolean;
  processingWithAuto: boolean;
  isAnyProcessing: boolean;
  // Tag state
  newTag: string;
  setNewTag: (tag: string) => void;
  addingTag: boolean;
  // Extraction state
  extractingAuthors: boolean;
  extractingAffiliations: boolean;
  // Import URL editing
  editingImportUrl: boolean;
  setEditingImportUrl: (editing: boolean) => void;
  editedImportUrl: string;
  setEditedImportUrl: (url: string) => void;
  savingImportUrl: boolean;
  // Handlers
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>;
  handleEditMetadata: () => void;
  handleToggleFlag: () => void;
  handleSetRating: (rating: number | null) => void;
  handleExtractAuthors: () => void;
  handleExtractAffiliations: () => void;
  handleAddTag: () => void;
  handleRemoveTag: (tag: string) => void;
  handleSaveImportUrl: () => void;
  setShowTagModal: (show: boolean) => void;
  setShowEntityModal: (show: boolean) => void;
  setShowDBLPModal: (show: boolean) => void;
  setShowMarkerModal: (show: boolean) => void;
  setEditingConceptTag: (tag: string | null) => void;
  setShowConceptEditModal: (show: boolean) => void;
  loadPaperDetails: () => void;
  pollProcessingStatus: () => Promise<ReturnType<typeof setInterval>>;
  pollingIntervalRef: React.MutableRefObject<ReturnType<typeof setInterval> | null>;
}

const PaperDetailsSidebar: React.FC<PaperDetailsSidebarProps> = ({
  paper,
  paperId,
  sidebarCollapsed,
  setSidebarCollapsed,
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
  extractingAuthors,
  extractingAffiliations,
  editingImportUrl,
  setEditingImportUrl,
  editedImportUrl,
  setEditedImportUrl,
  savingImportUrl,
  setPaper,
  handleEditMetadata,
  handleToggleFlag,
  handleSetRating,
  handleExtractAuthors,
  handleExtractAffiliations,
  handleAddTag,
  handleRemoveTag,
  handleSaveImportUrl,
  setShowTagModal,
  setShowEntityModal,
  setShowDBLPModal,
  setShowMarkerModal,
  setEditingConceptTag,
  setShowConceptEditModal,
  loadPaperDetails,
  pollProcessingStatus,
  pollingIntervalRef,
}) => {
  return (
    <div
      className={cn(
        "bg-white border-r border-gray-200 transition-all duration-300 flex flex-col overflow-hidden shadow-sm",
        sidebarCollapsed ? "w-16" : "w-[440px]"
      )}
    >
      {/* Enhanced Sidebar Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between bg-gradient-to-r from-blue-50 to-indigo-50">
        {!sidebarCollapsed ? (
          <div className="flex items-center gap-2">
            <FileText className="h-4 w-4 text-blue-600" />
            <h3 className="font-semibold text-sm text-gray-800">Paper Details</h3>
          </div>
        ) : (
          <FileText className="h-4 w-4 text-blue-600 mx-auto" />
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="hover:bg-white/60 transition-colors"
          title={sidebarCollapsed ? "Expand details" : "Collapse details"}
        >
          {sidebarCollapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </Button>
      </div>

      {/* Scrollable Sidebar Content */}
      {!sidebarCollapsed && (
        <ScrollArea className="flex-1 overflow-x-hidden">
          <div className="p-4 space-y-4 pr-2">
            <PaperMetadataSection
              paper={paper}
              paperId={paperId}
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
              handleSaveImportUrl={handleSaveImportUrl}
              setShowDBLPModal={setShowDBLPModal}
              setShowMarkerModal={setShowMarkerModal}
              loadPaperDetails={loadPaperDetails}
              pollProcessingStatus={pollProcessingStatus}
              pollingIntervalRef={pollingIntervalRef}
            />

            <PaperConceptsSection
              paper={paper}
              newTag={newTag}
              setNewTag={setNewTag}
              addingTag={addingTag}
              handleAddTag={handleAddTag}
              handleRemoveTag={handleRemoveTag}
              setShowTagModal={setShowTagModal}
              setShowEntityModal={setShowEntityModal}
              setEditingConceptTag={setEditingConceptTag}
              setShowConceptEditModal={setShowConceptEditModal}
            />
          </div>
          <div className="pb-6"></div>
        </ScrollArea>
      )}
    </div>
  );
};

export default PaperDetailsSidebar;
