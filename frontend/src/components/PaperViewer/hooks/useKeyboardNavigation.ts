/**
 * Hook for keyboard navigation in the paper viewer.
 *
 * Consolidates 2 useEffect hooks:
 *   - Section navigation (j/k, Alt+Arrow) (L692)
 *   - Global shortcuts (Escape, Ctrl+1-5, Ctrl+T/E) (L999)
 */
import { useEffect } from "react";

interface KeyboardNavOptions {
  activeTab: string;
  isEditingMarkdown: boolean;
  onClose?: () => void;
  hasContent: boolean;
  setActiveTab: (tab: string) => void;
  setShowTagModal: (show: boolean) => void;
  setShowEntityModal: (show: boolean) => void;
  navigateToSection: (direction: "next" | "previous") => void;
  markdownContainerRef: React.RefObject<HTMLDivElement | null>;
}

export function useKeyboardNavigation({
  activeTab,
  isEditingMarkdown,
  onClose,
  hasContent,
  setActiveTab,
  setShowTagModal,
  setShowEntityModal,
  navigateToSection,
  markdownContainerRef,
}: KeyboardNavOptions) {
  // Section navigation for markdown tab
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (activeTab !== "markdown" || isEditingMarkdown) return;

      if (e.key === "j" || (e.key === "ArrowDown" && e.altKey)) {
        e.preventDefault();
        navigateToSection("next");
      } else if (e.key === "k" || (e.key === "ArrowUp" && e.altKey)) {
        e.preventDefault();
        navigateToSection("previous");
      } else if (e.key === "g" && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        markdownContainerRef.current?.scrollTo({ top: 0, behavior: "smooth" });
      } else if (e.key === "G" && !e.ctrlKey && !e.metaKey) {
        e.preventDefault();
        const container = markdownContainerRef.current;
        if (container) {
          container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [activeTab, isEditingMarkdown, navigateToSection, markdownContainerRef]);

  // Global shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && onClose) {
        onClose();
        return;
      }

      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case "1":
            e.preventDefault();
            setActiveTab("pdf");
            break;
          case "2":
            e.preventDefault();
            setActiveTab("markdown");
            break;
          case "3":
            e.preventDefault();
            setActiveTab("sections");
            break;
          case "4":
            e.preventDefault();
            setActiveTab("snippets");
            break;
          case "5":
            e.preventDefault();
            setActiveTab("analyses");
            break;
          case "t":
            e.preventDefault();
            if (hasContent) {
              setShowTagModal(true);
            }
            break;
          case "e":
            e.preventDefault();
            if (hasContent) {
              setShowEntityModal(true);
            }
            break;
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, hasContent, setActiveTab, setShowTagModal, setShowEntityModal]);
}
