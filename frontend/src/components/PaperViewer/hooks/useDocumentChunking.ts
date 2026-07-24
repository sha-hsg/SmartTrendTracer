/**
 * Hook for large document chunking with lazy loading via IntersectionObserver.
 */
import { useState, useCallback, useEffect, useRef } from "react";
import type { DocumentChunk } from "../types";

const CHUNK_SIZE = 50000; // 50KB chunks
const LARGE_DOC_THRESHOLD = 200000; // 200KB = ~80 pages

export function useDocumentChunking(
  content: string | undefined,
  markdownContainerRef: React.RefObject<HTMLDivElement | null>
) {
  const [isLargeDocument, setIsLargeDocument] = useState(false);
  const [documentChunks, setDocumentChunks] = useState<DocumentChunk[]>([]);
  const [loadedChunks, setLoadedChunks] = useState<Set<string>>(new Set());
  const chunkObserverRef = useRef<IntersectionObserver | null>(null);

  // Create chunks for large documents
  const createDocumentChunks = useCallback((text: string): DocumentChunk[] => {
    const chunks: DocumentChunk[] = [];
    let currentIndex = 0;
    let chunkId = 0;

    while (currentIndex < text.length) {
      const endIndex = Math.min(currentIndex + CHUNK_SIZE, text.length);

      // Try to find a good break point (paragraph or heading)
      let breakPoint = endIndex;
      if (endIndex < text.length) {
        const searchStart = Math.max(endIndex - 2000, currentIndex);
        const nextParagraph = text.indexOf("\n\n", searchStart);
        if (nextParagraph > 0 && nextParagraph < endIndex + 2000 && nextParagraph > currentIndex) {
          breakPoint = nextParagraph;
        }
      }

      const chunkContent = text.substring(currentIndex, breakPoint);

      // Extract headings for this chunk
      const headingRegex = /^(#{1,3})\s+(.+)$/gm;
      const chunkHeadings: DocumentChunk["headings"] = [];
      let match;
      while ((match = headingRegex.exec(chunkContent)) !== null) {
        chunkHeadings.push({
          id: `chunk-${chunkId}-heading-${chunkHeadings.length}`,
          text: match[2].trim(),
          level: match[1].length,
        });
      }

      chunks.push({
        id: `chunk-${chunkId}`,
        content: chunkContent,
        startIndex: currentIndex,
        endIndex: breakPoint,
        headings: chunkHeadings,
      });

      currentIndex = breakPoint;
      chunkId++;
    }

    return chunks;
  }, []);

  // Detect large documents and create chunks
  useEffect(() => {
    if (!content) return;

    const contentSize = new Blob([content]).size;

    if (contentSize > LARGE_DOC_THRESHOLD) {
      setIsLargeDocument(true);
      const chunks = createDocumentChunks(content);
      setDocumentChunks(chunks);

      // Initially load first 3 chunks
      const initialChunks = new Set<string>();
      chunks.slice(0, 3).forEach((chunk) => initialChunks.add(chunk.id));
      setLoadedChunks(initialChunks);

      console.log(
        `Large document detected: ${(contentSize / 1024).toFixed(1)}KB, created ${chunks.length} chunks`
      );
    } else {
      setIsLargeDocument(false);
      setDocumentChunks([]);
      setLoadedChunks(new Set());
    }
  }, [content, createDocumentChunks]);

  // Lazy loading observer for document chunks
  useEffect(() => {
    if (!isLargeDocument || !markdownContainerRef.current) return;

    if (chunkObserverRef.current) {
      chunkObserverRef.current.disconnect();
    }

    const options = {
      root: markdownContainerRef.current,
      rootMargin: "500px",
      threshold: 0,
    };

    chunkObserverRef.current = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const chunkId = entry.target.getAttribute("data-chunk-id");
          if (chunkId && !loadedChunks.has(chunkId)) {
            setLoadedChunks((prev) => new Set([...prev, chunkId]));
          }
        }
      });
    }, options);

    const chunkPlaceholders = markdownContainerRef.current.querySelectorAll("[data-chunk-id]");
    chunkPlaceholders.forEach((placeholder) => {
      chunkObserverRef.current?.observe(placeholder);
    });

    return () => {
      chunkObserverRef.current?.disconnect();
    };
  }, [isLargeDocument, documentChunks, loadedChunks, markdownContainerRef]);

  return {
    isLargeDocument,
    documentChunks,
    loadedChunks,
  };
}
