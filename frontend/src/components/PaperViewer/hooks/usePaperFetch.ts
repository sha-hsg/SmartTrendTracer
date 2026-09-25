import { useState, useEffect, useRef } from "react";
import http from '@/services/http'
import type { Paper } from "../types";

export interface UsePaperFetchReturn {
  paper: Paper | null;
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>;
  loading: boolean;
  error: string | null;
  pdfAvailable: boolean;
  setPdfAvailable: React.Dispatch<React.SetStateAction<boolean>>;

  isProcessing: boolean;
  setIsProcessing: React.Dispatch<React.SetStateAction<boolean>>;
  processingStartTime: Date | null;
  setProcessingStartTime: React.Dispatch<React.SetStateAction<Date | null>>;
  processingError: string | null;
  setProcessingError: React.Dispatch<React.SetStateAction<string | null>>;
  processingWithMarker: boolean;
  processingWithMinerU: boolean;
  processingWithAuto: boolean;
  isAnyProcessing: boolean;

  editedImportUrl: string;
  setEditedImportUrl: React.Dispatch<React.SetStateAction<string>>;

  loadPaperDetails: (retryCount?: number, silent?: boolean) => Promise<void>;
  pollProcessingStatus: () => Promise<ReturnType<typeof setInterval>>;
  pollingIntervalRef: React.MutableRefObject<ReturnType<typeof setInterval> | null>;
}

export function usePaperFetch(
  paperId: string | number,
): UsePaperFetchReturn {
  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfAvailable, setPdfAvailable] = useState(false);

  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStartTime, setProcessingStartTime] = useState<Date | null>(null);
  const [processingError, setProcessingError] = useState<string | null>(null);
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const [editedImportUrl, setEditedImportUrl] = useState("");

  const processingWithMarker = paper?.processing_status === "processing_with_marker";
  const processingWithMinerU = paper?.processing_status === "processing_with_mineru";
  const processingWithAuto = paper?.processing_status === "processing" || paper?.processing_status === "processing_pdf";
  const isAnyProcessing = processingWithMarker || processingWithMinerU || processingWithAuto;

  const loadPaperDetails = async (retryCount = 0, silent = false) => {
    // Only show loading skeleton on the very first load (no paper data yet).
    // Subsequent refreshes (onComplete, polling, etc.) update data in-place
    // without unmounting the component tree — this prevents the flicker loop.
    const isInitialLoad = retryCount === 0 && !silent && !paper;
    if (isInitialLoad) {
      setLoading(true);
    }
    setError(null);

    try {
      const paperResponse = await http.get(
        `/api/papers/${paperId}`,
      );

      const combinedData: Partial<Paper> & { id?: string | number } = {
        ...paperResponse.data,
      };

      let pdfPath = paperResponse.data?.pdf_path;

      try {
        const contentResponse = await http.get(
          `/api/papers/${paperId}/content`,
        );
        Object.assign(combinedData, contentResponse.data);
        pdfPath = contentResponse.data?.pdf_path ?? pdfPath;
      } catch (contentErr: any) {
        if (contentErr.response?.status === 404) {
          console.info("Paper content not available yet");
        } else {
          throw contentErr;
        }
      }

      try {
        const snippetsResponse = await http.get(
          `/api/papers/${paperId}/snippets`,
        );
        combinedData.snippets = snippetsResponse.data;
      } catch (snippetsErr: any) {
        if (snippetsErr.response?.status === 404) {
          combinedData.snippets = [];
        } else {
          throw snippetsErr;
        }
      }

      try {
        const sectionsResponse = await http.get(
          `/api/papers/${paperId}/sections`,
        );
        combinedData.sections = sectionsResponse.data || [];
      } catch (sectionsErr: any) {
        if (sectionsErr.response?.status === 404) {
          combinedData.sections = [];
        } else {
          console.warn("Paper sections unavailable:", sectionsErr);
        }
      }

      setPaper((prev) => ({ ...(prev || {}), ...combinedData } as Paper));
      setEditedImportUrl(combinedData.import_url || "");
      setPdfAvailable(Boolean(pdfPath));
    } catch (err: any) {
      const status = err.response?.status;
      const errorMsg =
        err.response?.data?.detail || err.message || "Failed to load paper details";
      console.error("Paper loading error:", errorMsg);

      if (retryCount < 2 && (status === 500 || status === 503)) {
        const delay = Math.min(1000 * Math.pow(2, retryCount), 10000);
        console.log(`Retrying paper load in ${delay}ms...`);
        setTimeout(() => loadPaperDetails(retryCount + 1), delay);
        return;
      }

      if (status === 404) {
        setPaper(null);
        setPdfAvailable(false);
      }

      setError(errorMsg);
    } finally {
      if (isInitialLoad) {
        setLoading(false);
      }
    }
  };

  const pollProcessingStatus = async () => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await http.get(
          `/api/papers/${paperId}`,
        );
        if (response.data.processed || response.data.processing_error) {
          setIsProcessing(false);
          setPaper(response.data);
          clearInterval(pollInterval);

          const contentResponse = await http.get(
            `/api/papers/${paperId}/content`,
          );
          setPaper((prev) =>
            prev ? { ...prev, ...contentResponse.data } : null,
          );

          if (response.data.processed) {
            setPdfAvailable(true);
          }
        }
      } catch (err: any) {
        console.error("Error polling processing status:", err);
        if (err.response?.status === 404) {
          clearInterval(pollInterval);
          setIsProcessing(false);
          console.error(`Paper ${paperId} not found. Stopping polling.`);
        }
      }
    }, 3000);

    return pollInterval;
  };

  useEffect(() => {
    loadPaperDetails();

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    };
  }, [paperId]);

  useEffect(() => {
    if (isAnyProcessing) {
      const intervalId = setInterval(() => {
        loadPaperDetails(0, true);
      }, 10000);

      return () => {
        clearInterval(intervalId);
        console.log('Cleared paper polling interval');
      };
    }
  }, [isAnyProcessing, paperId]);

  return {
    paper,
    setPaper,
    loading,
    error,
    pdfAvailable,
    setPdfAvailable,

    isProcessing,
    setIsProcessing,
    processingStartTime,
    setProcessingStartTime,
    processingError,
    setProcessingError,
    processingWithMarker,
    processingWithMinerU,
    processingWithAuto,
    isAnyProcessing,

    editedImportUrl,
    setEditedImportUrl,

    loadPaperDetails,
    pollProcessingStatus,
    pollingIntervalRef,
  };
}
