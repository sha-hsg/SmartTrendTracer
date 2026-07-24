/**
 * Hook for custom event listeners in the papers dashboard.
 *
 * Consolidates 3 useEffect hooks:
 *   - switchToUpload event (L1246)
 *   - paperAnalysisUpdated event (L1258)
 *   - paperTagsUpdated event (L1310)
 */
import { useEffect } from "react";

interface UsePaperEventListenersOptions {
  setPapers: React.Dispatch<React.SetStateAction<any[]>>;
}

export function usePaperEventListeners({
  setPapers,
}: UsePaperEventListenersOptions) {
  // Listen for switch to upload event from import dialog
  useEffect(() => {
    const handleSwitchToUpload = () => {
      // Upload functionality handled by button click
    };

    window.addEventListener("switchToUpload", handleSwitchToUpload);
    return () => {
      window.removeEventListener("switchToUpload", handleSwitchToUpload);
    };
  }, []);

  // Listen for paper analysis updates from PaperAnalysisPanel
  useEffect(() => {
    const handlePaperAnalysisUpdated = (event: CustomEvent) => {
      const { paperId, analysisType, content } = event.detail;

      setPapers((prevPapers) =>
        prevPapers.map((paper) => {
          if (paper.id.toString() === paperId.toString()) {
            const updatedAnalyses = paper.analyses
              ? [...paper.analyses]
              : [];
            const analysisIndex = updatedAnalyses.findIndex(
              (a) =>
                a.analysis_type === analysisType ||
                a.analysis_name === analysisType ||
                a.type === analysisType
            );

            if (analysisIndex >= 0) {
              updatedAnalyses[analysisIndex] = {
                ...updatedAnalyses[analysisIndex],
                content: content,
                analysis_content: content,
                updated_at: new Date().toISOString(),
              };
            } else {
              updatedAnalyses.push({
                analysis_type: analysisType,
                type: analysisType,
                content: content,
                analysis_content: content,
                updated_at: new Date().toISOString(),
              });
            }

            return {
              ...paper,
              analyses: updatedAnalyses,
            };
          }
          return paper;
        })
      );
    };

    window.addEventListener(
      "paperAnalysisUpdated",
      handlePaperAnalysisUpdated as EventListener
    );
    return () => {
      window.removeEventListener(
        "paperAnalysisUpdated",
        handlePaperAnalysisUpdated as EventListener
      );
    };
  }, [setPapers]);

  // Listen for paper tags updates from PaperViewerOptimized
  useEffect(() => {
    const handlePaperTagsUpdated = (event: CustomEvent) => {
      const { paperId, concepts } = event.detail;

      setPapers((prevPapers) =>
        prevPapers.map((paper) => {
          if (paper.id.toString() === paperId.toString()) {
            return {
              ...paper,
              concepts: concepts,
            };
          }
          return paper;
        })
      );
    };

    window.addEventListener(
      "paperTagsUpdated",
      handlePaperTagsUpdated as EventListener
    );
    return () => {
      window.removeEventListener(
        "paperTagsUpdated",
        handlePaperTagsUpdated as EventListener
      );
    };
  }, [setPapers]);
}
