import { useState } from "react";
import http from '@/services/http'
import type { Paper } from "../types";
import { useSectionActions } from "./useSectionActions";
import type { UseSectionActionsReturn } from "./useSectionActions";

export interface UsePaperActionsReturn extends UseSectionActionsReturn {
  editingMetadata: boolean;
  setEditingMetadata: React.Dispatch<React.SetStateAction<boolean>>;
  editedMetadata: any;
  setEditedMetadata: React.Dispatch<React.SetStateAction<any>>;
  handleEditMetadata: () => void;
  handleSaveMetadata: () => Promise<void>;

  extractingAuthors: boolean;
  handleExtractAuthors: () => Promise<void>;

  extractingAffiliations: boolean;
  showAffiliationDialog: boolean;
  setShowAffiliationDialog: React.Dispatch<React.SetStateAction<boolean>>;
  affiliationSuggestions: any[];
  selectedAffiliations: Set<number>;
  handleExtractAffiliations: () => Promise<void>;
  handleApplyAffiliations: () => Promise<void>;
  toggleAffiliationSelection: (index: number) => void;

  handleToggleFlag: () => Promise<void>;
  handleSetRating: (rating: number | null) => Promise<void>;

  editingImportUrl: boolean;
  setEditingImportUrl: React.Dispatch<React.SetStateAction<boolean>>;
  savingImportUrl: boolean;
  handleSaveImportUrl: () => Promise<void>;

  isEditingMarkdown: boolean;
  setIsEditingMarkdown: React.Dispatch<React.SetStateAction<boolean>>;
  editedMarkdown: string;
  setEditedMarkdown: React.Dispatch<React.SetStateAction<string>>;
  savingMarkdown: boolean;
  handleSaveMarkdown: () => Promise<void>;

  selectedText: string;
  setSelectedText: React.Dispatch<React.SetStateAction<string>>;
  snippetAnnotation: string;
  setSnippetAnnotation: React.Dispatch<React.SetStateAction<string>>;
  snippetCategory: string;
  setSnippetCategory: React.Dispatch<React.SetStateAction<string>>;
  creatingSnippet: boolean;
  handleCreateSnippet: () => Promise<void>;

  copiedText: string | null;
  handleCopyText: (text: string) => void;
}

export function usePaperActions(
  paperId: string | number,
  paper: Paper | null,
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>,
  editedImportUrl: string,
  loadPaperDetails: (retryCount?: number) => Promise<void>,
  onMetadataUpdate?: () => void,
): UsePaperActionsReturn {
  const [editingMetadata, setEditingMetadata] = useState(false);
  const [editedMetadata, setEditedMetadata] = useState<any>(null);

  const [extractingAuthors, setExtractingAuthors] = useState(false);

  const [showAffiliationDialog, setShowAffiliationDialog] = useState(false);
  const [extractingAffiliations, setExtractingAffiliations] = useState(false);
  const [affiliationSuggestions, setAffiliationSuggestions] = useState<any[]>([]);
  const [selectedAffiliations, setSelectedAffiliations] = useState<Set<number>>(new Set());

  const [editingImportUrl, setEditingImportUrl] = useState(false);
  const [savingImportUrl, setSavingImportUrl] = useState(false);

  const sectionActions = useSectionActions(paperId, paper, setPaper, loadPaperDetails);

  const [isEditingMarkdown, setIsEditingMarkdown] = useState(false);
  const [editedMarkdown, setEditedMarkdown] = useState("");
  const [savingMarkdown, setSavingMarkdown] = useState(false);

  const [selectedText, setSelectedText] = useState("");
  const [snippetAnnotation, setSnippetAnnotation] = useState("");
  const [snippetCategory, setSnippetCategory] = useState("");
  const [creatingSnippet, setCreatingSnippet] = useState(false);

  const [copiedText, setCopiedText] = useState<string | null>(null);

  // --- Clipboard ---
  const handleCopyText = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(text);
    setTimeout(() => setCopiedText(null), 2000);
  };

  // --- Snippet ---
  const handleCreateSnippet = async () => {
    if (!selectedText.trim()) return;

    setCreatingSnippet(true);
    try {
      const response = await http.post(
        `/api/papers/${paperId}/snippets`,
        {
          content: selectedText,
          annotation: snippetAnnotation,
          category: snippetCategory,
          page_number: null,
        },
      );

      if (paper) {
        setPaper({
          ...paper,
          snippets: [...(paper.snippets || []), response.data],
        });
      }

      setSelectedText("");
      setSnippetAnnotation("");
      setSnippetCategory("");
    } catch (err) {
      console.error("Failed to create snippet:", err);
    } finally {
      setCreatingSnippet(false);
    }
  };

  // --- Markdown editing ---
  const handleSaveMarkdown = async () => {
    setSavingMarkdown(true);
    try {
      await http.put(`/api/papers/${paperId}/content`, {
        content: editedMarkdown,
      });
      setPaper((prev) =>
        prev
          ? {
              ...prev,
              markdown_content: editedMarkdown,
              content: editedMarkdown,
            }
          : null,
      );
      setIsEditingMarkdown(false);
      setEditedMarkdown("");
    } catch (err) {
      console.error("Failed to save markdown:", err);
    } finally {
      setSavingMarkdown(false);
    }
  };

  // --- Author extraction ---
  const handleExtractAuthors = async () => {
    if (!paper) return;

    setExtractingAuthors(true);
    try {
      const response = await http.post(
        `/api/papers/${paperId}/extract-authors`,
        {
          use_full_content: false,
        },
      );

      if (response.data.success && response.data.authors) {
        setPaper({
          ...paper,
          authors: response.data.authors,
        });
        console.log(`Extracted ${response.data.authors.length} authors`);
      } else {
        console.error("Author extraction failed:", response.data.error);
        alert(
          `Failed to extract authors: ${response.data.error || "Unknown error"}`,
        );
      }
    } catch (err: any) {
      console.error("Failed to extract authors:", err);
      const errorMsg =
        err.response?.data?.detail ||
        err.message ||
        "Failed to extract authors";
      alert(errorMsg);
    } finally {
      setExtractingAuthors(false);
    }
  };

  // --- Affiliation extraction ---
  const handleExtractAffiliations = async () => {
    if (!paper) return;

    setExtractingAffiliations(true);
    setAffiliationSuggestions([]);
    setSelectedAffiliations(new Set());

    try {
      const response = await http.post(
        `/api/papers/${paperId}/extract-affiliations`
      );

      if (response.data.suggestions && response.data.suggestions.length > 0) {
        setAffiliationSuggestions(response.data.suggestions);
        const indices = new Set<number>(response.data.suggestions.map((_: any, idx: number) => idx));
        setSelectedAffiliations(indices);
        setShowAffiliationDialog(true);
      } else {
        alert("No affiliations could be extracted from the paper header.");
      }
    } catch (err: any) {
      console.error("Failed to extract affiliations:", err);
      const errorMsg =
        err.response?.data?.detail ||
        err.message ||
        "Failed to extract affiliations";
      alert(errorMsg);
    } finally {
      setExtractingAffiliations(false);
    }
  };

  const handleApplyAffiliations = async () => {
    if (!paper || selectedAffiliations.size === 0) return;

    const affiliationsToApply = affiliationSuggestions
      .filter((_, idx) => selectedAffiliations.has(idx))
      .map((suggestion) => ({
        author_index: suggestion.author_index,
        affiliation: suggestion.suggested_affiliation,
      }));

    try {
      const response = await http.put(
        `/api/papers/${paperId}/apply-affiliations`,
        {
          affiliations: affiliationsToApply,
        }
      );

      if (response.data.updated_count > 0) {
        setPaper({
          ...paper,
          authors: response.data.authors,
        });
        alert(`Successfully updated ${response.data.updated_count} affiliations!`);
        setShowAffiliationDialog(false);
      } else {
        alert("No affiliations were updated.");
      }
    } catch (err: any) {
      console.error("Failed to apply affiliations:", err);
      alert("Failed to apply affiliations. Please try again.");
    }
  };

  const toggleAffiliationSelection = (index: number) => {
    const newSelection = new Set(selectedAffiliations);
    if (newSelection.has(index)) {
      newSelection.delete(index);
    } else {
      newSelection.add(index);
    }
    setSelectedAffiliations(newSelection);
  };

  // --- Flag and rating ---
  const handleToggleFlag = async () => {
    if (!paper) return;

    const newFlagged = !paper.flagged;
    try {
      await http.put(`/api/papers/${paperId}/metadata`, {
        flagged: newFlagged
      });
      setPaper({ ...paper, flagged: newFlagged });
    } catch (err) {
      console.error("Failed to update flag:", err);
    }
  };

  const handleSetRating = async (rating: number | null) => {
    if (!paper) return;

    const newRating = paper.rating === rating ? null : rating;
    try {
      await http.put(`/api/papers/${paperId}/metadata`, {
        rating: newRating
      });
      setPaper({ ...paper, rating: newRating });
    } catch (err) {
      console.error("Failed to update rating:", err);
    }
  };

  // --- Metadata editing ---
  const handleEditMetadata = () => {
    if (!paper) return;

    let formattedDate = "";
    if (paper.publication_date) {
      const date = new Date(paper.publication_date);
      if (!isNaN(date.getTime())) {
        formattedDate = date.toISOString().split('T')[0];
      }
    }

    let authorsList: Array<{ name: string; affiliation: string; email: string }> = [];
    if (Array.isArray(paper.authors_detailed) && paper.authors_detailed.length > 0) {
      authorsList = paper.authors_detailed.map((a) => ({
        name: typeof a === 'string' ? a : (a.name || ''),
        affiliation: typeof a === 'object' ? (a.affiliation || "") : "",
        email: typeof a === 'object' ? (a.email || "") : "",
      }));
    } else if (Array.isArray(paper.authors_list) && paper.authors_list.length > 0) {
      authorsList = paper.authors_list.map((a) => ({
        name: a.name || '',
        affiliation: a.affiliation || "",
        email: a.email || "",
      }));
    } else if (typeof paper.authors === "string" && paper.authors) {
      authorsList = paper.authors.split(",").map((name) => ({
        name: name.trim(),
        affiliation: "",
        email: "",
      }));
    }

    setEditedMetadata({
      title: paper.title,
      abstract: paper.abstract || "",
      publication_date: formattedDate,
      conference: paper.conference || "",
      journal: paper.journal || "",
      arxiv_id: paper.arxiv_id || "",
      doi: paper.doi || "",
      authors: authorsList,
    });
    setEditingMetadata(true);
  };

  const handleSaveMetadata = async () => {
    if (!paper || !editedMetadata) return;

    try {
      const response = await http.put(
        `/api/papers/${paperId}/metadata`,
        editedMetadata,
      );

      setPaper({
        ...paper,
        ...response.data,
      });

      setEditingMetadata(false);
      setEditedMetadata(null);
      console.log("Metadata updated successfully");

      if (onMetadataUpdate) {
        onMetadataUpdate();
      }
    } catch (err) {
      console.error("Failed to save metadata:", err);
    }
  };

  // --- Import URL ---
  const handleSaveImportUrl = async () => {
    setSavingImportUrl(true);
    try {
      await http.patch(`/api/papers/${paperId}`, {
        import_url: editedImportUrl,
      });
      setPaper((prev) =>
        prev
          ? {
              ...prev,
              import_url: editedImportUrl,
            }
          : null,
      );
      setEditingImportUrl(false);
    } catch (err) {
      console.error("Failed to save import URL:", err);
      alert("Failed to save import URL");
    } finally {
      setSavingImportUrl(false);
    }
  };

  return {
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
    savingImportUrl,
    handleSaveImportUrl,

    ...sectionActions,

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
  };
}
