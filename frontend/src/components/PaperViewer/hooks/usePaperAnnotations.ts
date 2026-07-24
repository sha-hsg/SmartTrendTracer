import { useState, useEffect, useRef, useCallback } from "react";
import axios from "axios";
import type { Paper } from "../types";

export interface UsePaperAnnotationsReturn {
  newTag: string;
  setNewTag: React.Dispatch<React.SetStateAction<string>>;
  addingTag: boolean;
  handleAddTag: () => Promise<void>;
  handleRemoveTag: (tag: string) => Promise<void>;
  handleCreateTagFromPDF: (tagText: string) => Promise<void>;

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

  editingConceptTag: string | null;
  setEditingConceptTag: React.Dispatch<React.SetStateAction<string | null>>;
  showConceptEditModal: boolean;
  setShowConceptEditModal: React.Dispatch<React.SetStateAction<boolean>>;

  showTagModal: boolean;
  setShowTagModal: React.Dispatch<React.SetStateAction<boolean>>;
  showEntityModal: boolean;
  setShowEntityModal: React.Dispatch<React.SetStateAction<boolean>>;
  showDBLPModal: boolean;
  setShowDBLPModal: React.Dispatch<React.SetStateAction<boolean>>;
  showMarkerModal: boolean;
  setShowMarkerModal: React.Dispatch<React.SetStateAction<boolean>>;
}

export function usePaperAnnotations(
  paperId: string | number,
  paper: Paper | null,
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>,
  setSelectedText: React.Dispatch<React.SetStateAction<string>>,
): UsePaperAnnotationsReturn {
  const [newTag, setNewTag] = useState("");
  const [addingTag, setAddingTag] = useState(false);

  const [, setSelectedMarkdownText] = useState("");
  const [showMarkdownContextMenu, setShowMarkdownContextMenu] = useState(false);
  const [markdownContextMenuPosition, setMarkdownContextMenuPosition] = useState({ x: 0, y: 0 });
  const [showMarkdownTagDialog, setShowMarkdownTagDialog] = useState(false);
  const [markdownTagText, setMarkdownTagText] = useState("");
  const [creatingMarkdownTag, setCreatingMarkdownTag] = useState(false);
  const selectedMarkdownTextRef = useRef<string>("");

  const [editingConceptTag, setEditingConceptTag] = useState<string | null>(null);
  const [showConceptEditModal, setShowConceptEditModal] = useState(false);

  const [showTagModal, setShowTagModal] = useState(false);
  const [showEntityModal, setShowEntityModal] = useState(false);
  const [showDBLPModal, setShowDBLPModal] = useState(false);
  const [showMarkerModal, setShowMarkerModal] = useState(false);

  useEffect(() => {
    const handleClickOutside = (_e: MouseEvent) => {
      if (showMarkdownContextMenu) {
        setShowMarkdownContextMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [showMarkdownContextMenu]);

  // --- Tag handlers ---
  const handleCreateTagFromPDF = async (tagText: string) => {
    if (!paper) return;

    try {
      await axios.post(`/api/papers/${paper.id}/tags`, {
        tag: tagText,
        tag_type: "manual",
      });

      setPaper((prev) =>
        prev
          ? {
              ...prev,
              tags: [...(prev.tags || []), tagText],
            }
          : null,
      );
    } catch (error) {
      console.error("Error creating tag:", error);
      throw error;
    }
  };

  const handleAddTag = async () => {
    if (!newTag.trim() || !paper) return;

    setAddingTag(true);
    try {
      await axios.post(`/api/papers/${paperId}/tags`, {
        tag: newTag.trim(),
      });

      setPaper({
        ...paper,
        tags: [...(paper.tags || []), newTag.trim()],
      });
      setNewTag("");
    } catch (err) {
      console.error("Failed to add tag:", err);
    } finally {
      setAddingTag(false);
    }
  };

  const handleRemoveTag = async (tag: string) => {
    if (!paper) return;

    try {
      await axios.delete(
        `/api/papers/${paperId}/tags/${encodeURIComponent(tag)}`,
      );

      setPaper({
        ...paper,
        tags: (paper.tags || []).filter((t) => t !== tag),
      });
    } catch (err) {
      console.error("Failed to remove tag:", err);
    }
  };

  // --- Markdown context menu ---
  const handleMarkdownContextMenu = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    const selection = window.getSelection();
    if (!selection || selection.isCollapsed || !selection.toString().trim()) {
      return;
    }

    const text = selection.toString().trim();
    setSelectedMarkdownText(text);
    selectedMarkdownTextRef.current = text;

    const viewportHeight = window.innerHeight;
    const menuHeight = 200;

    let menuY = e.clientY;
    if (e.clientY + menuHeight > viewportHeight) {
      menuY = e.clientY - menuHeight;
    }

    setMarkdownContextMenuPosition({ x: e.clientX, y: menuY });
    setShowMarkdownContextMenu(true);
  }, []);

  const handleMarkdownMenuAction = (action: string) => {
    const text = selectedMarkdownTextRef.current;
    if (!text) return;

    switch (action) {
      case "copy":
        navigator.clipboard.writeText(text);
        break;
      case "snippet":
        setSelectedText(text);
        break;
      case "highlight":
        console.log("Highlight:", text);
        break;
      case "tag":
        setMarkdownTagText(text.trim());
        setShowMarkdownTagDialog(true);
        break;
    }

    setShowMarkdownContextMenu(false);
  };

  const handleCreateMarkdownTag = async () => {
    if (!markdownTagText.trim() || !paper) return;

    setCreatingMarkdownTag(true);
    try {
      await axios.post(`/api/papers/${paper.id}/tags`, {
        tag: markdownTagText.trim(),
        tag_type: "manual",
      });

      setPaper((prev) =>
        prev
          ? {
              ...prev,
              tags: [...(prev.tags || []), markdownTagText.trim()],
            }
          : null,
      );
      setShowMarkdownTagDialog(false);
      setMarkdownTagText("");
    } catch (error) {
      console.error("Error creating markdown tag:", error);
    } finally {
      setCreatingMarkdownTag(false);
    }
  };

  const handleMarkdownTagDialogClose = () => {
    setShowMarkdownTagDialog(false);
    setMarkdownTagText("");
    setCreatingMarkdownTag(false);
  };

  return {
    newTag,
    setNewTag,
    addingTag,
    handleAddTag,
    handleRemoveTag,
    handleCreateTagFromPDF,

    showMarkdownContextMenu,
    markdownContextMenuPosition,
    showMarkdownTagDialog,
    setShowMarkdownTagDialog,
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
  };
}
