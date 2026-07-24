import React from "react";
import ReactDOM from "react-dom";
import axios from "axios";
import {
  Tag as TagIcon,
  X,
  Copy,
  Loader2,
  MessageSquare,
  Highlighter,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

import PaperTagSuggestionModal from "../PaperTagSuggestionModal";
import PaperEntityAnnotationReview from "../PaperEntityAnnotationReview";
import { DBLPSearchModal } from "../DBLPSearchModal";
import { MarkerProgressModal } from "../MarkerProgressModal";
import ConceptEditModal from "../ConceptEditModal";

import { MetadataDialog } from "./MetadataDialog";
import { AffiliationDialog } from "./AffiliationDialog";
import type { Paper } from "./types";

interface PaperDialogsProps {
  paper: Paper | null;
  paperId: number;
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>;
  loadPaperDetails: () => void;
  onMetadataUpdate?: () => void;

  // Markdown context menu
  showMarkdownContextMenu: boolean;
  markdownContextMenuPosition: { x: number; y: number };
  handleMarkdownMenuAction: (action: string) => void;

  // Markdown tag dialog
  showMarkdownTagDialog: boolean;
  markdownTagText: string;
  setMarkdownTagText: (text: string) => void;
  creatingMarkdownTag: boolean;
  handleMarkdownTagDialogClose: () => void;
  handleCreateMarkdownTag: () => void;

  // Metadata editing
  editingMetadata: boolean;
  setEditingMetadata: (editing: boolean) => void;
  editedMetadata: any;
  setEditedMetadata: (metadata: any) => void;
  handleSaveMetadata: () => void;

  // Tag modal
  showTagModal: boolean;
  setShowTagModal: (show: boolean) => void;

  // Entity modal
  showEntityModal: boolean;
  setShowEntityModal: (show: boolean) => void;

  // DBLP modal
  showDBLPModal: boolean;
  setShowDBLPModal: (show: boolean) => void;

  // Affiliation dialog
  showAffiliationDialog: boolean;
  setShowAffiliationDialog: (show: boolean) => void;
  affiliationSuggestions: any[];
  selectedAffiliations: Set<number>;
  toggleAffiliationSelection: (idx: number) => void;
  handleApplyAffiliations: () => void;

  // Marker modal
  showMarkerModal: boolean;
  setShowMarkerModal: (show: boolean) => void;

  // Concept edit modal
  editingConceptTag: string | null;
  showConceptEditModal: boolean;
  setShowConceptEditModal: (show: boolean) => void;
  setEditingConceptTag: (tag: string | null) => void;
}

export function PaperDialogs({
  paper,
  paperId,
  setPaper,
  loadPaperDetails,
  onMetadataUpdate,
  showMarkdownContextMenu,
  markdownContextMenuPosition,
  handleMarkdownMenuAction,
  showMarkdownTagDialog,
  markdownTagText,
  setMarkdownTagText,
  creatingMarkdownTag,
  handleMarkdownTagDialogClose,
  handleCreateMarkdownTag,
  editingMetadata,
  setEditingMetadata,
  editedMetadata,
  setEditedMetadata,
  handleSaveMetadata,
  showTagModal,
  setShowTagModal,
  showEntityModal,
  setShowEntityModal,
  showDBLPModal,
  setShowDBLPModal,
  showAffiliationDialog,
  setShowAffiliationDialog,
  affiliationSuggestions,
  selectedAffiliations,
  toggleAffiliationSelection,
  handleApplyAffiliations,
  showMarkerModal,
  setShowMarkerModal,
  editingConceptTag,
  showConceptEditModal,
  setShowConceptEditModal,
  setEditingConceptTag,
}: PaperDialogsProps) {
  return (
    <>
      {/* Markdown Context Menu Portal */}
      {showMarkdownContextMenu &&
        ReactDOM.createPortal(
          <div
            className="fixed z-[9999] bg-white rounded-lg shadow-2xl border border-gray-200 py-1 min-w-[180px]"
            style={{
              left: `${markdownContextMenuPosition.x}px`,
              top: `${markdownContextMenuPosition.y}px`,
            }}
            onMouseDown={(e) => e.stopPropagation()}
          >
            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-blue-50 flex items-center gap-2 transition-colors"
              onClick={() => handleMarkdownMenuAction("copy")}
            >
              <Copy className="h-4 w-4 text-blue-600" />
              <span>Copy Text</span>
            </button>

            <div className="border-t border-gray-100 my-1" />

            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-green-50 flex items-center gap-2 transition-colors"
              onClick={() => handleMarkdownMenuAction("snippet")}
            >
              <MessageSquare className="h-4 w-4 text-green-600" />
              <span>Create Snippet</span>
            </button>

            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-yellow-50 flex items-center gap-2 transition-colors"
              onClick={() => handleMarkdownMenuAction("highlight")}
            >
              <Highlighter className="h-4 w-4 text-yellow-600" />
              <span>Highlight</span>
            </button>

            <button
              className="w-full px-4 py-2 text-left text-sm hover:bg-purple-50 flex items-center gap-2 transition-colors"
              onClick={() => handleMarkdownMenuAction("tag")}
            >
              <TagIcon className="h-4 w-4 text-purple-600" />
              <span>Create Tag</span>
            </button>
          </div>,
          document.body,
        )}

      {/* Markdown Tag Creation Dialog */}
      <Dialog
        open={showMarkdownTagDialog}
        onOpenChange={handleMarkdownTagDialogClose}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <TagIcon className="h-5 w-5 text-purple-600" />
              Create Tag from Markdown
            </DialogTitle>
            <DialogDescription>
              Edit the selected text and create a tag for this paper.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label
                htmlFor="markdownTagText"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Tag Text
              </label>
              <Input
                id="markdownTagText"
                value={markdownTagText}
                onChange={(e) => setMarkdownTagText(e.target.value)}
                placeholder="Enter tag text..."
                className="w-full"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !creatingMarkdownTag) {
                    handleCreateMarkdownTag();
                  }
                }}
                disabled={creatingMarkdownTag}
              />
            </div>
            <div className="flex justify-end gap-2">
              <Button
                variant="outline"
                onClick={handleMarkdownTagDialogClose}
                disabled={creatingMarkdownTag}
              >
                Cancel
              </Button>
              <Button
                onClick={handleCreateMarkdownTag}
                disabled={!markdownTagText.trim() || creatingMarkdownTag}
                className="bg-purple-600 hover:bg-purple-700"
              >
                {creatingMarkdownTag ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Tag"
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Metadata Editing Dialog */}
      <MetadataDialog
        editingMetadata={editingMetadata}
        setEditingMetadata={setEditingMetadata}
        editedMetadata={editedMetadata}
        setEditedMetadata={setEditedMetadata}
        handleSaveMetadata={handleSaveMetadata}
      />

      {/* Tag Management Modal */}
      {paper && (
        <PaperTagSuggestionModal
          paper={paper}
          isOpen={showTagModal}
          onClose={() => setShowTagModal(false)}
          onTagsUpdated={(updatedTags?: string[]) => {
            if (updatedTags) {
              setPaper((prev) =>
                prev ? { ...prev, tags: updatedTags } : null,
              );
            }
            if (onMetadataUpdate) {
              onMetadataUpdate();
            }
          }}
        />
      )}

      {/* Entity Annotation Modal */}
      {showEntityModal && paper && (
        <div className="fixed inset-0 z-50 bg-black/50 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-auto">
            <div className="p-4 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold">
                Entity Annotation Review
              </h2>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowEntityModal(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="p-4">
              <PaperEntityAnnotationReview
                paperId={paper.id}
                onComplete={() => {
                  setShowEntityModal(false);
                  axios
                    .get(`/api/papers/${paper.id}`)
                    .then((response) => {
                      setPaper((prev) =>
                        prev ? { ...prev, tags: response.data.tags } : null,
                      );
                      if (onMetadataUpdate) {
                        onMetadataUpdate();
                      }
                    })
                    .catch((err) =>
                      console.error("Error reloading tags:", err),
                    );
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* DBLP Search Modal */}
      {paper && (
        <DBLPSearchModal
          isOpen={showDBLPModal}
          onClose={() => {
            setShowDBLPModal(false);
            loadPaperDetails();
            if (onMetadataUpdate) {
              onMetadataUpdate();
            }
          }}
          initialTitle={paper.title}
          paperId={paper.id}
          hasExistingMetadata={!!paper.dblp_key}
        />
      )}

      {/* Affiliation Extraction Dialog */}
      <AffiliationDialog
        showAffiliationDialog={showAffiliationDialog}
        setShowAffiliationDialog={setShowAffiliationDialog}
        affiliationSuggestions={affiliationSuggestions}
        selectedAffiliations={selectedAffiliations}
        toggleAffiliationSelection={toggleAffiliationSelection}
        handleApplyAffiliations={handleApplyAffiliations}
      />

      {/* Marker Progress Modal */}
      <MarkerProgressModal
        isOpen={showMarkerModal}
        onClose={() => setShowMarkerModal(false)}
        paperId={paperId}
        paperTitle={paper?.title}
        onSuccess={() => {
          setShowMarkerModal(false);
          loadPaperDetails();
        }}
      />

      {/* Concept Edit Modal */}
      {editingConceptTag && (
        <ConceptEditModal
          tagName={editingConceptTag}
          isOpen={showConceptEditModal}
          onClose={() => {
            setShowConceptEditModal(false);
            setEditingConceptTag(null);
          }}
          onUpdate={() => {
            // Optionally refresh paper details if needed
          }}
        />
      )}
    </>
  );
}
