import { useState } from "react";
import axios from "axios";
import type { Paper, PaperSection } from "../types";

export interface UseSectionActionsReturn {
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
}

export function useSectionActions(
  paperId: string | number,
  paper: Paper | null,
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>,
  loadPaperDetails: (retryCount?: number) => Promise<void>,
): UseSectionActionsReturn {
  const [expandedSections, setExpandedSections] = useState<Set<number>>(new Set());
  const [editingSectionId, setEditingSectionId] = useState<number | null>(null);
  const [editedSectionContent, setEditedSectionContent] = useState<string>("");
  const [editingSectionTitleId, setEditingSectionTitleId] = useState<number | null>(null);
  const [editedSectionTitle, setEditedSectionTitle] = useState<string>("");
  const [savingSection, setSavingSection] = useState<boolean>(false);
  const [extractingSections, setExtractingSections] = useState<boolean>(false);

  const toggleSection = (sectionId: number) => {
    setExpandedSections(prev => {
      const newExpanded = new Set(prev);
      if (newExpanded.has(sectionId)) {
        newExpanded.delete(sectionId);
      } else {
        newExpanded.add(sectionId);
      }
      return newExpanded;
    });
  };

  const handleEditSection = (section: PaperSection) => {
    setEditingSectionId(section.id);
    setEditedSectionContent(section.content);
  };

  const handleEditSectionTitle = (section: PaperSection) => {
    setEditingSectionTitleId(section.id);
    setEditedSectionTitle(section.title);
  };

  const handleSaveSectionTitle = async (sectionId: number) => {
    if (!paper || savingSection || !editedSectionTitle.trim()) return;
    setSavingSection(true);
    try {
      const response = await axios.put(
        `/api/papers/${paperId}/sections/${sectionId}`,
        {
          title: editedSectionTitle.trim(),
        },
      );
      if (response.data.success) {
        const updatedSections = paper.sections?.map(s =>
          s.id === sectionId ? { ...s, title: editedSectionTitle.trim() } : s
        );
        setPaper({ ...paper, sections: updatedSections });
        setEditingSectionTitleId(null);
        setEditedSectionTitle("");
      }
    } catch (err: any) {
      console.error("Failed to save section title:", err);
      alert(
        "Failed to save section title: " +
          (err.response?.data?.detail || err.message)
      );
    } finally {
      setSavingSection(false);
    }
  };

  const handleCancelSectionTitleEdit = () => {
    setEditingSectionTitleId(null);
    setEditedSectionTitle("");
  };

  const handleSaveSection = async (sectionId: number) => {
    if (!paper || savingSection) return;

    setSavingSection(true);
    try {
      const response = await axios.put(
        `/api/papers/${paperId}/sections/${sectionId}`,
        {
          content: editedSectionContent,
        },
      );

      if (response.data.success) {
        if (sectionId === -1) {
          setPaper((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              abstract: editedSectionContent,
              sections: prev.sections?.map((s) =>
                s.id === -1 ? { ...s, content: editedSectionContent } : s,
              ),
            };
          });
        } else {
          setPaper((prev) => {
            if (!prev) return null;
            return {
              ...prev,
              sections: prev.sections?.map((s) =>
                s.id === sectionId
                  ? { ...s, content: editedSectionContent }
                  : s,
              ),
            };
          });
        }

        setEditingSectionId(null);
        setEditedSectionContent("");

        console.log(
          `${response.data.section_type || "Section"} saved successfully`,
        );
      }
    } catch (err: any) {
      console.error("Failed to save section:", err);
      alert(
        "Failed to save section: " +
          (err.response?.data?.detail || err.message),
      );
    } finally {
      setSavingSection(false);
    }
  };

  const handleCancelSectionEdit = () => {
    setEditingSectionId(null);
    setEditedSectionContent("");
  };

  const handleExtractSections = async () => {
    if (!paper || extractingSections) return;

    setExtractingSections(true);
    try {
      const response = await axios.post(
        `/api/papers/${paperId}/extract-sections`
      );

      if (response.data.success) {
        await loadPaperDetails();

        const extractedCount = response.data.sections_extracted;

        let message = `Successfully extracted ${extractedCount} section${extractedCount !== 1 ? 's' : ''}`;
        if (response.data.conclusion_title && response.data.conclusion_title !== 'Conclusion') {
          message += ` (Conclusion found as "${response.data.conclusion_title}")`;
        }

        console.log(message);

        if (paper.sections) {
          paper.sections.forEach(section => {
            setExpandedSections(prev => {
              const newSet = new Set(prev);
              newSet.add(section.id);
              return newSet;
            });
          });
        }
      }
    } catch (err: any) {
      console.error("Failed to extract sections:", err);
      alert(
        "Failed to extract sections: " +
          (err.response?.data?.detail || err.message)
      );
    } finally {
      setExtractingSections(false);
    }
  };

  return {
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
  };
}
