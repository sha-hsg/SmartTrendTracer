/**
 * Hook for table of contents extraction, scroll tracking, section navigation,
 * and reading progress.
 *
 * Consolidates 5 useEffect hooks from the original PaperViewerOptimized:
 *   - TOC extraction (L487)
 *   - IntersectionObserver for active section (L536)
 *   - URL hash scroll (L666)
 *   - Scroll listener for reading progress (L674)
 *   - Scroll timeout cleanup (L736)
 */
import { useState, useCallback, useEffect, useRef } from "react";
import type { TOCItem } from "../types";

export function useTableOfContents(
  content: string | undefined,
  markdownContainerRef: React.RefObject<HTMLDivElement | null>
) {
  const [tableOfContents, setTableOfContents] = useState<TOCItem[]>([]);
  const [activeSection, setActiveSection] = useState<string>("");
  const [showTOC, setShowTOC] = useState(true);
  const [readingProgress, setReadingProgress] = useState(0);
  const observerRef = useRef<IntersectionObserver | null>(null);

  // Extract table of contents from markdown
  const extractTableOfContents = useCallback((text: string) => {
    const headingRegex = /^(#{1,3})\s+(.+)$/gm;
    const toc: TOCItem[] = [];
    let match;
    let index = 0;

    while ((match = headingRegex.exec(text)) !== null) {
      toc.push({
        id: `heading-${index}`,
        text: match[2].trim(),
        level: match[1].length,
        position: match.index,
      });
      index++;
    }

    setTableOfContents(toc);
  }, []);

  // Initialize TOC when content changes + handle initial scroll from URL hash
  useEffect(() => {
    if (content) {
      extractTableOfContents(content);
    }
    // After TOC is extracted, check URL hash for initial scroll
    const hash = window.location.hash.slice(1);
    if (hash) {
      // Defer scroll to after DOM update
      setTimeout(() => {
        if (!markdownContainerRef.current) return;
        const container = markdownContainerRef.current;
        const heading = container.querySelector(`[data-heading-id="${hash}"]`);
        if (heading) {
          const containerRect = container.getBoundingClientRect();
          const headingRect = heading.getBoundingClientRect();
          const scrollTop = container.scrollTop + headingRect.top - containerRect.top - 20;
          container.scrollTo({ top: scrollTop, behavior: "smooth" });
          setActiveSection(hash);
        }
      }, 100);
    }
  }, [content, extractTableOfContents, markdownContainerRef]);

  // Handle scroll to track reading progress
  const handleMarkdownScroll = useCallback(() => {
    if (!markdownContainerRef.current) return;
    const container = markdownContainerRef.current;
    const scrollTop = container.scrollTop;
    const scrollHeight = container.scrollHeight - container.clientHeight;
    const progress = scrollHeight > 0 ? (scrollTop / scrollHeight) * 100 : 0;
    setReadingProgress(Math.min(100, Math.round(progress)));
  }, [markdownContainerRef]);

  // IntersectionObserver for efficient section tracking
  useEffect(() => {
    if (!markdownContainerRef.current || tableOfContents.length === 0) return;

    if (observerRef.current) {
      observerRef.current.disconnect();
    }

    const options = {
      root: markdownContainerRef.current,
      rootMargin: "-20% 0px -70% 0px",
      threshold: [0, 0.1, 0.5, 0.9, 1],
    };

    observerRef.current = new IntersectionObserver((entries) => {
      const visibleSections = entries
        .filter((entry) => entry.isIntersecting)
        .map((entry) => ({
          id: entry.target.getAttribute("data-heading-id") || "",
          ratio: entry.intersectionRatio,
          top: entry.boundingClientRect.top,
        }))
        .filter((section) => section.id);

      if (visibleSections.length > 0) {
        const closestSection = visibleSections.reduce((prev, curr) =>
          Math.abs(curr.top) < Math.abs(prev.top) ? curr : prev
        );

        if (closestSection.id && closestSection.id !== activeSection) {
          setActiveSection(closestSection.id);
          window.history.replaceState(null, "", `#${closestSection.id}`);
        }
      }
    }, options);

    const headings = markdownContainerRef.current.querySelectorAll("[data-heading-id]");
    headings.forEach((heading) => observerRef.current?.observe(heading));

    return () => {
      observerRef.current?.disconnect();
    };
  }, [tableOfContents, activeSection, markdownContainerRef]);

  // Scroll to section
  const scrollToSection = useCallback(
    (sectionId: string) => {
      if (!markdownContainerRef.current) return;

      const container = markdownContainerRef.current;
      const heading = container.querySelector(`[data-heading-id="${sectionId}"]`);

      if (heading) {
        const containerRect = container.getBoundingClientRect();
        const headingRect = heading.getBoundingClientRect();
        const scrollTop = container.scrollTop + headingRect.top - containerRect.top - 20;

        container.scrollTo({ top: scrollTop, behavior: "smooth" });
        setActiveSection(sectionId);
        window.location.hash = sectionId;
      }
    },
    [markdownContainerRef]
  );

  // Navigate to next/previous section
  const navigateToSection = useCallback(
    (direction: "next" | "previous") => {
      const currentIndex = tableOfContents.findIndex((item) => item.id === activeSection);

      if (direction === "next" && currentIndex < tableOfContents.length - 1) {
        scrollToSection(tableOfContents[currentIndex + 1].id);
      } else if (direction === "previous" && currentIndex > 0) {
        scrollToSection(tableOfContents[currentIndex - 1].id);
      }
    },
    [activeSection, tableOfContents, scrollToSection]
  );

  // Setup scroll listener
  useEffect(() => {
    const container = markdownContainerRef.current;
    if (!container) return;

    let scrollTimeout: ReturnType<typeof setTimeout>;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(handleMarkdownScroll, 50);
    };

    container.addEventListener("scroll", handleScroll);
    return () => {
      container.removeEventListener("scroll", handleScroll);
      clearTimeout(scrollTimeout);
    };
  }, [handleMarkdownScroll, markdownContainerRef]);

  // Calculate reading time
  const calculateReadingTime = useCallback((text: string) => {
    const wordsPerMinute = 200;
    const words = text.trim().split(/\s+/).length;
    return Math.ceil(words / wordsPerMinute);
  }, []);

  return {
    tableOfContents,
    activeSection,
    showTOC,
    setShowTOC,
    readingProgress,
    scrollToSection,
    navigateToSection,
    calculateReadingTime,
  };
}
