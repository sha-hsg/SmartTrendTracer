/**
 * Hook for book content pagination with smart overlap.
 *
 * Consolidates:
 *   - Page state (markdownPages, currentPage, isChangingPage)
 *   - createPages with smart overlap for context continuity
 *   - goToNextPage / goToPreviousPage / goToPage navigation
 *   - useEffect: Initialize pages when bookContent changes (L382)
 *   - useEffect: Keyboard navigation ArrowLeft/Right, PageUp/Down (L435)
 */
import { useState, useCallback, useRef, useEffect } from "react";

interface UseBookPaginationOptions {
  bookContent: string | null;
}

export function useBookPagination({ bookContent }: UseBookPaginationOptions) {
  const [markdownPages, setMarkdownPages] = useState<string[]>([]);
  const [currentPage, setCurrentPage] = useState(0);
  const [isChangingPage, setIsChangingPage] = useState(false);
  const markdownContainerRef = useRef<HTMLDivElement>(null);

  // Create pages with smart overlap for better context
  const createPages = useCallback((content: string) => {
    if (!content || content.length < 15000) {
      setMarkdownPages([content]);
      setCurrentPage(0);
      return;
    }

    const pages: string[] = [];
    const lines = content.split("\n");
    let currentPageContent = "";
    let currentPageSize = 0;
    const targetPageSize = 15000; // ~15KB per page for books
    const overlapSize = 3000; // ~3KB overlap between pages for context

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const lineSize = line.length + 1; // +1 for newline

      if (
        currentPageSize + lineSize > targetPageSize &&
        currentPageContent.trim()
      ) {
        if (
          line.startsWith("#") ||
          line.trim() === "" ||
          line.startsWith("---")
        ) {
          pages.push(currentPageContent);

          const pageLines = currentPageContent.split("\n");
          let overlapContent = "";
          let overlapBytes = 0;

          for (
            let j = pageLines.length - 1;
            j >= 0 && overlapBytes < overlapSize;
            j--
          ) {
            const overlapLine = pageLines[j] + "\n";
            if (overlapBytes + overlapLine.length <= overlapSize) {
              overlapContent = overlapLine + overlapContent;
              overlapBytes += overlapLine.length;
            } else {
              break;
            }
          }

          currentPageContent = overlapContent + line + "\n";
          currentPageSize = overlapContent.length + lineSize;
        } else {
          currentPageContent += line + "\n";
          currentPageSize += lineSize;
        }
      } else {
        currentPageContent += line + "\n";
        currentPageSize += lineSize;
      }
    }

    if (currentPageContent.trim()) {
      pages.push(currentPageContent);
    }

    setMarkdownPages(pages);
    setCurrentPage(0);
  }, []);

  // Initialize pages when book content changes
  useEffect(() => {
    if (bookContent) {
      createPages(bookContent);
    }
  }, [bookContent, createPages]);

  const scrollToTop = useCallback(() => {
    setTimeout(() => {
      if (markdownContainerRef.current) {
        markdownContainerRef.current.scrollTop = 0;
      }
      setIsChangingPage(false);
    }, 100);
  }, []);

  const goToNextPage = useCallback(() => {
    if (currentPage < markdownPages.length - 1) {
      setIsChangingPage(true);
      setCurrentPage((prev) => prev + 1);
      scrollToTop();
    }
  }, [currentPage, markdownPages.length, scrollToTop]);

  const goToPreviousPage = useCallback(() => {
    if (currentPage > 0) {
      setIsChangingPage(true);
      setCurrentPage((prev) => prev - 1);
      scrollToTop();
    }
  }, [currentPage, scrollToTop]);

  const goToPage = useCallback(
    (pageNumber: number) => {
      if (
        pageNumber >= 0 &&
        pageNumber < markdownPages.length &&
        pageNumber !== currentPage
      ) {
        setIsChangingPage(true);
        setCurrentPage(pageNumber);
        scrollToTop();
      }
    },
    [currentPage, markdownPages.length, scrollToTop]
  );

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (markdownPages.length <= 1) return;

      if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        goToPreviousPage();
      } else if (e.key === "ArrowRight" || e.key === "PageDown") {
        e.preventDefault();
        goToNextPage();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [goToNextPage, goToPreviousPage, markdownPages.length]);

  return {
    markdownPages,
    currentPage,
    isChangingPage,
    markdownContainerRef,
    goToNextPage,
    goToPreviousPage,
    goToPage,
  };
}
