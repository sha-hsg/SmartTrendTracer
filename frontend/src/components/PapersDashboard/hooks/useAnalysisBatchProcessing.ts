/**
 * Hook for batch analysis generation across selected papers.
 *
 * Consolidates:
 *   - Analysis batch state (analysisBatchProgress, selectedPapersForAnalysis)
 *   - AbortController for cancellation
 *   - Concurrent task runner (runWithConcurrency)
 *   - batchGenerateAnalyses handler
 *   - togglePaperSelection / toggleSelectAllPapers helpers
 */
import { useState, useRef } from "react";
import axios from "axios";

interface Paper {
  id: number;
  title: string;
  analyses?: any[];
  [key: string]: any;
}

export interface AnalysisBatchProgress {
  isProcessing: boolean;
  totalPapers: number;
  completedPapers: number;
  currentPaper: string | null;
  currentPaperId: number | null;
  totalAnalyses: number;
  completedAnalyses: number;
  currentAnalysis: string | null;
  failed: number;
  skipped: number;
}

const ANALYSIS_TYPES = [
  { id: "layman_summary", name: "Layman Summary" },
  { id: "mollick_summary", name: "Mollick-Style Summary" },
  { id: "summary", name: "Concise Summary" },
  { id: "pareto_summary", name: "Pareto Summary (80/20)" },
  { id: "sas_summary", name: "SAS Summary" },
  { id: "switt_analysis", name: "SWITT Analysis" },
  { id: "evaluation", name: "Critical Evaluation" },
  { id: "key_findings", name: "Key Findings" },
  { id: "methodology", name: "Methodology Analysis" },
  { id: "limitations", name: "Limitations & Future Work" },
  { id: "glossary", name: "Technical Glossary" },
  { id: "review", name: "Academic Review" },
];

const ANALYSIS_CONCURRENCY = 4;

interface UseAnalysisBatchOptions {
  papers: Paper[];
  loadPapers: () => void;
}

async function runWithConcurrency<T>(
  tasks: (() => Promise<T>)[],
  concurrency: number,
  onTaskComplete?: (result: T, index: number) => void,
  signal?: AbortSignal
): Promise<T[]> {
  const results: T[] = [];
  let currentIndex = 0;
  let aborted = false;

  const runNext = async (): Promise<void> => {
    if (aborted || signal?.aborted) {
      aborted = true;
      return;
    }

    const index = currentIndex++;
    if (index >= tasks.length) return;

    const result = await tasks[index]();
    results[index] = result;
    onTaskComplete?.(result, index);

    if (!signal?.aborted) {
      await runNext();
    }
  };

  await Promise.all(
    Array(Math.min(concurrency, tasks.length))
      .fill(null)
      .map(() => runNext())
  );

  return results;
}

export function useAnalysisBatchProcessing({
  papers,
  loadPapers,
}: UseAnalysisBatchOptions) {
  const [selectedPapersForAnalysis, setSelectedPapersForAnalysis] = useState<
    Set<number>
  >(new Set());
  const [analysisBatchProgress, setAnalysisBatchProgress] =
    useState<AnalysisBatchProgress | null>(null);
  // Model picker selection (saved as preference for 'paper_analysis' task).
  // When set, passed explicitly to the API so the batch run uses it for every paper.
  const [analysisModel, setAnalysisModel] = useState<string>("");
  const analysisAbortControllerRef = useRef<AbortController | null>(null);

  const togglePaperSelection = (paperId: number) => {
    setSelectedPapersForAnalysis((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(paperId)) {
        newSet.delete(paperId);
      } else {
        newSet.add(paperId);
      }
      return newSet;
    });
  };

  const toggleSelectAllPapers = () => {
    if (selectedPapersForAnalysis.size === papers.length) {
      setSelectedPapersForAnalysis(new Set());
    } else {
      setSelectedPapersForAnalysis(new Set(papers.map((p) => p.id)));
    }
  };

  const batchGenerateAnalyses = async () => {
    if (selectedPapersForAnalysis.size === 0) {
      alert("Please select at least one paper");
      return;
    }

    analysisAbortControllerRef.current = new AbortController();
    const signal = analysisAbortControllerRef.current.signal;

    const selectedPapersList = papers.filter((p) =>
      selectedPapersForAnalysis.has(p.id)
    );
    const totalAnalyses = selectedPapersList.length * ANALYSIS_TYPES.length;

    setAnalysisBatchProgress({
      isProcessing: true,
      totalPapers: selectedPapersList.length,
      completedPapers: 0,
      currentPaper: null,
      currentPaperId: null,
      totalAnalyses,
      completedAnalyses: 0,
      currentAnalysis: `Running ${ANALYSIS_CONCURRENCY} in parallel`,
      failed: 0,
      skipped: 0,
    });

    let completedAnalyses = 0;
    let failedCount = 0;
    let skippedCount = 0;
    let completedPapers = 0;

    try {
      for (const paper of selectedPapersList) {
        if (signal.aborted) {
          console.log("Analysis batch processing aborted");
          break;
        }

        setAnalysisBatchProgress((prev) => ({
          ...prev!,
          currentPaper: paper.title,
          currentPaperId: paper.id,
          currentAnalysis: `Running ${ANALYSIS_CONCURRENCY} in parallel`,
        }));

        const analysisTasks = ANALYSIS_TYPES.map(
          (analysisType) => async () => {
            if (signal.aborted) {
              return {
                success: false,
                skipped: true,
                name: analysisType.name,
                aborted: true,
              };
            }
            try {
              const response = await axios.post(
                `/api/papers/${paper.id}/analyses/generate`,
                {
                  analysis_type: analysisType.id,
                  regenerate: false,
                  ...(analysisModel ? { model: analysisModel } : {}),
                }
              );
              return {
                success: true,
                skipped: response.data.was_skipped,
                name: analysisType.name,
              };
            } catch (error) {
              console.error(
                `Failed to generate ${analysisType.name} for paper ${paper.id}:`,
                error
              );
              return {
                success: false,
                skipped: false,
                name: analysisType.name,
              };
            }
          }
        );

        await runWithConcurrency(
          analysisTasks,
          ANALYSIS_CONCURRENCY,
          (result: any) => {
            if (result.aborted) return;
            completedAnalyses++;
            if (!result.success) {
              failedCount++;
            } else if (result.skipped) {
              skippedCount++;
            }
            setAnalysisBatchProgress((prev) => ({
              ...prev!,
              completedAnalyses,
              skipped: skippedCount,
              failed: failedCount,
            }));
          },
          signal
        );

        completedPapers++;
        setAnalysisBatchProgress((prev) => ({
          ...prev!,
          completedPapers,
        }));
      }

      if (!signal.aborted) {
        const generated = totalAnalyses - skippedCount - failedCount;
        alert(
          `Batch analysis complete!\n\n` +
            `Papers processed: ${completedPapers}/${selectedPapersList.length}\n` +
            `Analyses generated: ${generated}\n` +
            `Already existed (skipped): ${skippedCount}\n` +
            `Failed: ${failedCount}`
        );
      }
    } catch (error) {
      if (!signal.aborted) {
        console.error("Batch analysis error:", error);
        alert(
          "Batch analysis encountered an error. Check console for details."
        );
      }
    } finally {
      analysisAbortControllerRef.current = null;
      setAnalysisBatchProgress(null);
      setSelectedPapersForAnalysis(new Set());
      loadPapers();
    }
  };

  return {
    selectedPapersForAnalysis,
    setSelectedPapersForAnalysis,
    analysisBatchProgress,
    setAnalysisBatchProgress,
    analysisAbortControllerRef,
    togglePaperSelection,
    toggleSelectAllPapers,
    batchGenerateAnalyses,
    ANALYSIS_TYPES,
    analysisModel,
    setAnalysisModel,
  };
}
