import type { Paper, PaperSection } from "../types";
import { usePaperFetch } from "./usePaperFetch";
import { usePaperActions } from "./usePaperActions";
import { usePaperAnnotations } from "./usePaperAnnotations";

export interface UsePaperDataReturn {
  // Core state
  paper: Paper | null;
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>;
  loading: boolean;
  error: string | null;
  pdfAvailable: boolean;
  setPdfAvailable: React.Dispatch<React.SetStateAction<boolean>>;

  // Processing state
  isProcessing: boolean;
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>;
  processingStartTime: Date | null;
  setProcessingStartTime: React.Dispatch<React.SetStateAction<Date | null>>;
  processingError: string | null;
  setProcessingError: React.Dispatch<React.SetStateAction<string | null>>;
  processingWithMarker: boolean;
  processingWithMinerU: boolean;
  processingWithAuto: boolean;
  isAnyProcessing: boolean;

  // Tag management
  newTag: string;
  setNewTag: React.Dispatch<React.SetStateAction<string>>;
  addingTag: boolean;
  handleAddTag: () => Promise<void>;
  handleRemoveTag: (tag: string) => Promise<void>;
  handleCreateTagFromPDF: (tagText: string) => Promise<void>;

  // Metadata editing
  editingMetadata: boolean;
  setEditingMetadata: React.Dispatch<React.SetStateAction<boolean>>;
  editedMetadata: any;
  setEditedMetadata: React.Dispatch<React.SetStateAction<any>>;
  handleEditMetadata: () => void;
  handleSaveMetadata: () => Promise<void>;

  // Author extraction
  extractingAuthors: boolean;
  handleExtractAuthors: () => Promise<void>;

  // Affiliation extraction
  extractingAffiliations: boolean;
  showAffiliationDialog: boolean;
  setShowAffiliationDialog: React.Dispatch<React.SetStateAction<boolean>>;
  affiliationSuggestions: any[];
  selectedAffiliations: Set<number>;
  handleExtractAffiliations: () => Promise<void>;
  handleApplyAffiliations: () => Promise<void>;
  toggleAffiliationSelection: (index: number) => void;

  // Flag and rating
  handleToggleFlag: () => Promise<void>;
  handleSetRating: (rating: number | null) => Promise<void>;

  // Import URL
  editingImportUrl: boolean;
  setEditingImportUrl: React.Dispatch<React.SetStateAction<boolean>>;
  editedImportUrl: string;
  setEditedImportUrl: React.Dispatch<React.SetStateAction<string>>;
  savingImportUrl: boolean;
  handleSaveImportUrl: () => Promise<void>;

  // Section editing
  expandedSections: Set<number>;
  editingSectionId: number | null;
  editedSectionContent: string;
  setEditedSectionContent: React.Dispatch<React.SetStateAction<string>>;
  editingSectionTitleId: number | null;
  editedSectionTitle: string;
  setEditedSectionTitle: React.Dispatch<React.SetStateAction<string>>;
  savingSection: boolean;
  extractingSections: boolean;
  toggleSection: (sectionId: number) => void;
  handleEditSection: (section: PaperSection) => void;
  handleEditSectionTitle: (section: PaperSection) => void;
  handleSaveSectionTitle: (sectionId: number) => Promise<void>;
  handleCancelSectionTitleEdit: () => void;
  handleSaveSection: (sectionId: number) => Promise<void>;
  handleCancelSectionEdit: () => void;
  handleExtractSections: () => Promise<void>;

  // Markdown editing
  isEditingMarkdown: boolean;
  setIsEditingMarkdown: React.Dispatch<React.SetStateAction<boolean>>;
  editedMarkdown: string;
  setEditedMarkdown: React.Dispatch<React.SetStateAction<string>>;
  savingMarkdown: boolean;
  handleSaveMarkdown: () => Promise<void>;

  // Snippet creation
  selectedText: string;
  setSelectedText: React.Dispatch<React.SetStateAction<string>>;
  snippetAnnotation: string;
  setSnippetAnnotation: React.Dispatch<React.SetStateAction<string>>;
  snippetCategory: string;
  setSnippetCategory: React.Dispatch<React.SetStateAction<string>>;
  creatingSnippet: boolean;
  handleCreateSnippet: () => Promise<void>;

  // Clipboard
  copiedText: string | null;
  handleCopyText: (text: string) => void;

  // Data loading
  loadPaperDetails: (retryCount?: number) => Promise<void>;
  pollProcessingStatus: () => Promise<ReturnType<typeof setInterval>>;
  pollingIntervalRef: React.MutableRefObject<ReturnType<typeof setInterval> | null>;

  // Markdown context menu
  showMarkdownContextMenu: boolean;
  markdownContextMenuPosition: { x: number; y: number };
  showMarkdownTagDialog: boolean;
  setShowMarkdownTagDialog: React.Dispatch<React.SetStateAction<boolean>>;
  markdownTagText: string;
  setMarkdownTagText: React.Dispatch<React.SetStateAction<string>>;
  creatingMarkdownTag: boolean;
  handleMarkdownContextMenu: (e: React.MouseEvent) => void;
  handleMarkdownMenuAction: (action: string) => void;
  handleCreateMarkdownTag: () => Promise<void>;
  handleMarkdownTagDialogClose: () => void;

  // Concept editing
  editingConceptTag: string | null;
  setEditingConceptTag: React.Dispatch<React.SetStateAction<string | null>>;
  showConceptEditModal: boolean;
  setShowConceptEditModal: React.Dispatch<React.SetStateAction<boolean>>;

  // Modals
  showTagModal: boolean;
  setShowTagModal: React.Dispatch<React.SetStateAction<boolean>>;
  showEntityModal: boolean;
  setShowEntityModal: React.Dispatch<React.SetStateAction<boolean>>;
  showDBLPModal: boolean;
  setShowDBLPModal: React.Dispatch<React.SetStateAction<boolean>>;
  showMarkerModal: boolean;
  setShowMarkerModal: React.Dispatch<React.SetStateAction<boolean>>;
}

export function usePaperData(
  paperId: string | number,
  onMetadataUpdate?: () => void,
): UsePaperDataReturn {
  const fetchData = usePaperFetch(paperId);

  const actions = usePaperActions(
    paperId,
    fetchData.paper,
    fetchData.setPaper,
    fetchData.editedImportUrl,
    fetchData.loadPaperDetails,
    onMetadataUpdate,
  );

  const annotations = usePaperAnnotations(
    paperId,
    fetchData.paper,
    fetchData.setPaper,
    actions.setSelectedText,
  );

  return {
    // Core state (from fetch)
    paper: fetchData.paper,
    setPaper: fetchData.setPaper,
    loading: fetchData.loading,
    error: fetchData.error,
    pdfAvailable: fetchData.pdfAvailable,
    setPdfAvailable: fetchData.setPdfAvailable,

    // Processing state (from fetch)
    isProcessing: fetchData.isProcessing,
    setIsProcessing: fetchData.setIsProcessing,
    processingStartTime: fetchData.processingStartTime,
    setProcessingStartTime: fetchData.setProcessingStartTime,
    processingError: fetchData.processingError,
    setProcessingError: fetchData.setProcessingError,
    processingWithMarker: fetchData.processingWithMarker,
    processingWithMinerU: fetchData.processingWithMinerU,
    processingWithAuto: fetchData.processingWithAuto,
    isAnyProcessing: fetchData.isAnyProcessing,

    // Tag management (from annotations)
    newTag: annotations.newTag,
    setNewTag: annotations.setNewTag,
    addingTag: annotations.addingTag,
    handleAddTag: annotations.handleAddTag,
    handleRemoveTag: annotations.handleRemoveTag,
    handleCreateTagFromPDF: annotations.handleCreateTagFromPDF,

    // Metadata editing (from actions)
    editingMetadata: actions.editingMetadata,
    setEditingMetadata: actions.setEditingMetadata,
    editedMetadata: actions.editedMetadata,
    setEditedMetadata: actions.setEditedMetadata,
    handleEditMetadata: actions.handleEditMetadata,
    handleSaveMetadata: actions.handleSaveMetadata,

    // Author extraction (from actions)
    extractingAuthors: actions.extractingAuthors,
    handleExtractAuthors: actions.handleExtractAuthors,

    // Affiliation extraction (from actions)
    extractingAffiliations: actions.extractingAffiliations,
    showAffiliationDialog: actions.showAffiliationDialog,
    setShowAffiliationDialog: actions.setShowAffiliationDialog,
    affiliationSuggestions: actions.affiliationSuggestions,
    selectedAffiliations: actions.selectedAffiliations,
    handleExtractAffiliations: actions.handleExtractAffiliations,
    handleApplyAffiliations: actions.handleApplyAffiliations,
    toggleAffiliationSelection: actions.toggleAffiliationSelection,

    // Flag and rating (from actions)
    handleToggleFlag: actions.handleToggleFlag,
    handleSetRating: actions.handleSetRating,

    // Import URL (from actions + fetch for editedImportUrl)
    editingImportUrl: actions.editingImportUrl,
    setEditingImportUrl: actions.setEditingImportUrl,
    editedImportUrl: fetchData.editedImportUrl,
    setEditedImportUrl: fetchData.setEditedImportUrl,
    savingImportUrl: actions.savingImportUrl,
    handleSaveImportUrl: actions.handleSaveImportUrl,

    // Section editing (from actions)
    expandedSections: actions.expandedSections,
    editingSectionId: actions.editingSectionId,
    editedSectionContent: actions.editedSectionContent,
    setEditedSectionContent: actions.setEditedSectionContent,
    editingSectionTitleId: actions.editingSectionTitleId,
    editedSectionTitle: actions.editedSectionTitle,
    setEditedSectionTitle: actions.setEditedSectionTitle,
    savingSection: actions.savingSection,
    extractingSections: actions.extractingSections,
    toggleSection: actions.toggleSection,
    handleEditSection: actions.handleEditSection,
    handleEditSectionTitle: actions.handleEditSectionTitle,
    handleSaveSectionTitle: actions.handleSaveSectionTitle,
    handleCancelSectionTitleEdit: actions.handleCancelSectionTitleEdit,
    handleSaveSection: actions.handleSaveSection,
    handleCancelSectionEdit: actions.handleCancelSectionEdit,
    handleExtractSections: actions.handleExtractSections,

    // Markdown editing (from actions)
    isEditingMarkdown: actions.isEditingMarkdown,
    setIsEditingMarkdown: actions.setIsEditingMarkdown,
    editedMarkdown: actions.editedMarkdown,
    setEditedMarkdown: actions.setEditedMarkdown,
    savingMarkdown: actions.savingMarkdown,
    handleSaveMarkdown: actions.handleSaveMarkdown,

    // Snippet creation (from actions)
    selectedText: actions.selectedText,
    setSelectedText: actions.setSelectedText,
    snippetAnnotation: actions.snippetAnnotation,
    setSnippetAnnotation: actions.setSnippetAnnotation,
    snippetCategory: actions.snippetCategory,
    setSnippetCategory: actions.setSnippetCategory,
    creatingSnippet: actions.creatingSnippet,
    handleCreateSnippet: actions.handleCreateSnippet,

    // Clipboard (from actions)
    copiedText: actions.copiedText,
    handleCopyText: actions.handleCopyText,

    // Data loading (from fetch)
    loadPaperDetails: fetchData.loadPaperDetails,
    pollProcessingStatus: fetchData.pollProcessingStatus,
    pollingIntervalRef: fetchData.pollingIntervalRef,

    // Markdown context menu (from annotations)
    showMarkdownContextMenu: annotations.showMarkdownContextMenu,
    markdownContextMenuPosition: annotations.markdownContextMenuPosition,
    showMarkdownTagDialog: annotations.showMarkdownTagDialog,
    setShowMarkdownTagDialog: annotations.setShowMarkdownTagDialog,
    markdownTagText: annotations.markdownTagText,
    setMarkdownTagText: annotations.setMarkdownTagText,
    creatingMarkdownTag: annotations.creatingMarkdownTag,
    handleMarkdownContextMenu: annotations.handleMarkdownContextMenu,
    handleMarkdownMenuAction: annotations.handleMarkdownMenuAction,
    handleCreateMarkdownTag: annotations.handleCreateMarkdownTag,
    handleMarkdownTagDialogClose: annotations.handleMarkdownTagDialogClose,

    // Concept editing (from annotations)
    editingConceptTag: annotations.editingConceptTag,
    setEditingConceptTag: annotations.setEditingConceptTag,
    showConceptEditModal: annotations.showConceptEditModal,
    setShowConceptEditModal: annotations.setShowConceptEditModal,

    // Modals (from annotations)
    showTagModal: annotations.showTagModal,
    setShowTagModal: annotations.setShowTagModal,
    showEntityModal: annotations.showEntityModal,
    setShowEntityModal: annotations.setShowEntityModal,
    showDBLPModal: annotations.showDBLPModal,
    setShowDBLPModal: annotations.setShowDBLPModal,
    showMarkerModal: annotations.showMarkerModal,
    setShowMarkerModal: annotations.setShowMarkerModal,
  };
}
