/**
 * Hook for batch Marker processing of unprocessed papers.
 *
 * Consolidates 3 useEffect hooks:
 *   - Cleanup on unmount (L252)
 *   - Persist to localStorage (L924)
 *   - Resume batch processing (L933)
 *
 * Plus handlers: handleBatchProcess, waitForProcessingComplete
 */
import { useState, useEffect, useRef } from "react";
import axios from "axios";
import { toast } from "sonner";
export interface BatchProgress {
  isProcessing: boolean;
  total: number;
  completed: number;
  current: string | null;
  failed: number;
  skipped: number;
  papers?: any[];
  currentIndex?: number;
}

interface UseBatchProcessingOptions {
  loadPapers: () => void;
  loadFacets: () => void;
  setError: (error: string | null) => void;
}

export function useBatchProcessing({
  loadPapers,
  loadFacets,
  setError,
}: UseBatchProcessingOptions) {
  const [batchProgress, setBatchProgress] = useState<BatchProgress | null>(
    () => {
      try {
        const saved = localStorage.getItem("batchProcessingProgress");
        if (saved) {
          const parsed = JSON.parse(saved);
          if (parsed.isProcessing) {
            return parsed;
          }
        }
      } catch (e) {
        console.error("Failed to load batch progress from localStorage:", e);
      }
      return null;
    }
  );

  const batchProcessingActiveRef = useRef(false);
  const batchAbortControllerRef = useRef<AbortController | null>(null);

  // Cleanup batch processing on unmount (RES-009)
  useEffect(() => {
    return () => {
      if (batchAbortControllerRef.current) {
        batchAbortControllerRef.current.abort();
        batchAbortControllerRef.current = null;
      }
    };
  }, []);

  // Persist batch progress to localStorage when it changes
  useEffect(() => {
    if (batchProgress) {
      localStorage.setItem(
        "batchProcessingProgress",
        JSON.stringify(batchProgress)
      );
    } else {
      localStorage.removeItem("batchProcessingProgress");
    }
  }, [batchProgress]);

  // Resume batch processing if we loaded an active batch from localStorage
  useEffect(() => {
    const resumeBatchProcessing = async () => {
      if (
        !batchProgress?.isProcessing ||
        !batchProgress?.papers ||
        batchProgress.currentIndex === undefined
      ) {
        return;
      }

      if (batchProcessingActiveRef.current) {
        console.log("Batch processing already active, skipping resume");
        return;
      }
      batchProcessingActiveRef.current = true;

      batchAbortControllerRef.current = new AbortController();
      const signal = batchAbortControllerRef.current.signal;

      const papers = batchProgress.papers;
      const startIndex = batchProgress.currentIndex;

      for (let i = startIndex; i < papers.length; i++) {
        if (signal.aborted) {
          console.log("Resumed batch processing aborted");
          break;
        }

        const paper = papers[i];
        const paperId = paper._id || paper.id;
        const paperTitle = paper.title || "Untitled";

        try {
          setBatchProgress((prev) => ({
            ...prev!,
            current: paperTitle,
            currentIndex: i,
          }));

          if (!paper.pdf_path) {
            setBatchProgress((prev) => ({
              ...prev!,
              skipped: prev!.skipped + 1,
              current: null,
            }));
            continue;
          }

          try {
            const statusResponse = await axios.get(
              `/api/papers/${paperId}/processing-status`
            );
            const currentStatus = statusResponse.data?.status;

            if (currentStatus === "failed") {
              setBatchProgress((prev) => ({
                ...prev!,
                failed: prev!.failed + 1,
                current: null,
              }));
              continue;
            }

            if (currentStatus === "completed") {
              setBatchProgress((prev) => ({
                ...prev!,
                completed: prev!.completed + 1,
                current: null,
              }));
              continue;
            }

            if (
              currentStatus === "processing_with_marker" ||
              currentStatus === "processing_with_mineru"
            ) {
              await waitForProcessingComplete(paperId);
              setBatchProgress((prev) => ({
                ...prev!,
                completed: prev!.completed + 1,
                current: null,
              }));
              continue;
            }
          } catch (statusErr: any) {
            if (statusErr.response?.status !== 404) {
              throw statusErr;
            }
          }

          await axios.post(
            `/api/papers/${paperId}/process-with-marker`
          );
          await waitForProcessingComplete(paperId);

          setBatchProgress((prev) => ({
            ...prev!,
            completed: prev!.completed + 1,
            current: null,
          }));
        } catch (error: any) {
          console.error(
            `Failed to process paper ${paperId} (resume):`,
            error
          );
          setBatchProgress((prev) => ({
            ...prev!,
            failed: prev!.failed + 1,
            current: null,
          }));
        }
      }

      setBatchProgress((prev) => ({
        ...prev!,
        isProcessing: false,
        current: null,
        papers: undefined,
        currentIndex: undefined,
      }));
      localStorage.removeItem("batchProcessingProgress");
      batchProcessingActiveRef.current = false;
      batchAbortControllerRef.current = null;
      loadPapers();
      loadFacets();
    };

    resumeBatchProcessing();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const waitForProcessingComplete = async (
    paperId: string
  ): Promise<void> => {
    const maxAttempts = 360; // 60 minutes max (10s intervals)
    for (let i = 0; i < maxAttempts; i++) {
      try {
        const status = await axios.get(
          `/api/papers/${paperId}/processing-status`
        );

        if (status.data.status === "completed") return;
        if (status.data.status === "failed")
          throw new Error("Processing failed");
        if (status.data.status === "cancelled")
          throw new Error("Processing cancelled");

        await new Promise((resolve) => setTimeout(resolve, 10000));
      } catch (err: any) {
        if (err.response?.status === 404) {
          await new Promise((resolve) => setTimeout(resolve, 10000));
          continue;
        }
        throw err;
      }
    }
    throw new Error("Processing timeout");
  };

  const handleBatchProcess = async () => {
    if (batchProcessingActiveRef.current) {
      console.log("Batch processing already active, skipping duplicate call");
      return;
    }
    batchProcessingActiveRef.current = true;

    batchAbortControllerRef.current = new AbortController();
    const signal = batchAbortControllerRef.current.signal;

    try {
      let allUnprocessedPapers: any[] = [];
      let page = 1;
      const fetchPageSize = 100;

      while (true) {
        const response = await axios.get("/api/papers/", {
          params: {
            no_processor: true,
            page: page,
            page_size: fetchPageSize,
          },
        });

        const papers = response.data.papers || response.data || [];
        allUnprocessedPapers = [...allUnprocessedPapers, ...papers];

        if (papers.length < fetchPageSize) break;
        page++;
      }

      if (allUnprocessedPapers.length === 0) {
        alert("No unprocessed papers found");
        batchProcessingActiveRef.current = false;
        batchAbortControllerRef.current = null;
        return;
      }

      setBatchProgress({
        isProcessing: true,
        total: allUnprocessedPapers.length,
        completed: 0,
        current: null,
        failed: 0,
        skipped: 0,
        papers: allUnprocessedPapers,
        currentIndex: 0,
      });

      for (let i = 0; i < allUnprocessedPapers.length; i++) {
        if (signal.aborted) {
          console.log("Batch processing aborted");
          break;
        }

        const paper = allUnprocessedPapers[i];
        const paperId = paper._id || paper.id;
        const paperTitle = paper.title || "Untitled";

        try {
          setBatchProgress((prev) => ({
            ...prev!,
            current: paperTitle,
            currentIndex: i,
          }));

          if (!paper.pdf_path) {
            setBatchProgress((prev) => ({
              ...prev!,
              skipped: prev!.skipped + 1,
              current: null,
            }));
            continue;
          }

          try {
            const statusResponse = await axios.get(
              `/api/papers/${paperId}/processing-status`
            );
            const currentStatus = statusResponse.data?.status;

            if (currentStatus === "failed") {
              setBatchProgress((prev) => ({
                ...prev!,
                failed: prev!.failed + 1,
                current: null,
              }));
              continue;
            }

            if (currentStatus === "completed") {
              setBatchProgress((prev) => ({
                ...prev!,
                completed: prev!.completed + 1,
                current: null,
              }));
              continue;
            }
          } catch (statusErr: any) {
            if (statusErr.response?.status !== 404) {
              throw statusErr;
            }
          }

          await axios.post(
            `/api/papers/${paperId}/process-with-marker`
          );
          await waitForProcessingComplete(paperId);

          setBatchProgress((prev) => ({
            ...prev!,
            completed: prev!.completed + 1,
            current: null,
          }));
        } catch (error: any) {
          console.error(`Failed to process paper ${paperId}:`, error);
          setBatchProgress((prev) => ({
            ...prev!,
            failed: prev!.failed + 1,
            current: null,
          }));
        }
      }

      setBatchProgress((prev) => {
        const completed = prev?.completed ?? 0;
        const failed = prev?.failed ?? 0;
        if (failed > 0) {
          toast.warning(`Batch complete: ${completed} processed, ${failed} failed`);
        } else {
          toast.success(`Batch complete: ${completed} papers processed`);
        }
        return {
          ...prev!,
          isProcessing: false,
          current: null,
          papers: undefined,
          currentIndex: undefined,
        };
      });
      localStorage.removeItem("batchProcessingProgress");
      batchProcessingActiveRef.current = false;
      batchAbortControllerRef.current = null;
      loadPapers();
      loadFacets();
    } catch (error: any) {
      console.error("Batch processing error:", error);
      toast.error("Batch processing failed: " + (error.message || "Unknown error"));
      setBatchProgress((prev) =>
        prev
          ? {
              ...prev,
              isProcessing: false,
              papers: undefined,
              currentIndex: undefined,
            }
          : null
      );
      localStorage.removeItem("batchProcessingProgress");
      batchProcessingActiveRef.current = false;
      batchAbortControllerRef.current = null;
      setError(
        "Failed to start batch processing: " +
          (error.message || "Unknown error")
      );
    }
  };

  return {
    batchProgress,
    setBatchProgress,
    handleBatchProcess,
    batchAbortControllerRef,
  };
}
