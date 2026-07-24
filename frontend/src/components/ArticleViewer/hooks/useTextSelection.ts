/**
 * Hook for text selection and context menu behavior in article viewer.
 *
 * Consolidates 4 useEffect hooks:
 *   - Context menu flag tracking (L150)
 *   - Selection change capture (L170)
 *   - Click outside to close context menu (L216)
 *   - Restore selection when forms shown (L241)
 */
import { useEffect, useRef } from "react";

interface UseTextSelectionOptions {
  showContextMenu: boolean;
  setShowContextMenu: (show: boolean) => void;
  showHighlightForm: boolean;
  showAnnotationForm: boolean;
  showTagCreation: boolean;
  preservedSelection: { text: string; rangeData: any } | null;
  selectedText: string;
  setSelectedText: (text: string) => void;
  selectedTextRef: React.MutableRefObject<string>;
}

export function useTextSelection({
  showContextMenu,
  setShowContextMenu,
  showHighlightForm,
  showAnnotationForm,
  showTagCreation,
  preservedSelection,
  selectedText,
  setSelectedText,
  selectedTextRef,
}: UseTextSelectionOptions) {
  const isInteractingWithMenu = useRef(false);
  const lastSelectionRef = useRef<{ text: string; time: number } | null>(null);

  // Handle context menu interaction flag + close on click outside
  useEffect(() => {
    if (
      showContextMenu ||
      showHighlightForm ||
      showAnnotationForm ||
      showTagCreation
    ) {
      isInteractingWithMenu.current = true;
    } else {
      const timer = setTimeout(() => {
        isInteractingWithMenu.current = false;
      }, 500);

      return () => clearTimeout(timer);
    }

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Element;

      if (
        target.closest(".context-menu") ||
        target.closest(".highlight-form") ||
        target.closest(".annotation-form") ||
        target.closest(".tag-creation-form")
      ) {
        return;
      }

      if (showContextMenu) {
        setShowContextMenu(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showContextMenu, showHighlightForm, showAnnotationForm, showTagCreation, setShowContextMenu]);

  // Capture selection on mouseup/selectionchange
  useEffect(() => {
    const handleSelectionChange = () => {
      const selection = window.getSelection();
      if (selection && selection.toString().trim() !== "") {
        const text = selection.toString().trim();
        lastSelectionRef.current = {
          text: text,
          time: Date.now(),
        };
      }
    };

    document.addEventListener("selectionchange", handleSelectionChange);
    document.addEventListener("mouseup", handleSelectionChange);

    return () => {
      document.removeEventListener("selectionchange", handleSelectionChange);
      document.removeEventListener("mouseup", handleSelectionChange);
    };
  }, []);

  // Restore selection when forms are shown
  useEffect(() => {
    if (
      (showHighlightForm || showAnnotationForm || showTagCreation) &&
      preservedSelection
    ) {
      if (!selectedText && preservedSelection.text) {
        setSelectedText(preservedSelection.text);
        selectedTextRef.current = preservedSelection.text;
      }
    }
  }, [
    showHighlightForm,
    showAnnotationForm,
    showTagCreation,
    preservedSelection,
    selectedText,
    setSelectedText,
    selectedTextRef,
  ]);

  return {
    isInteractingWithMenu,
    lastSelectionRef,
  };
}
