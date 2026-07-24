import React from "react";
import axios from "axios";
import {
  Loader2,
  PlayCircle,
  RotateCcw,
  Cpu,
  GraduationCap,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { ProcessingTimer } from "../ProcessingTimer";
import { ProcessingStatusIndicator } from "../ProcessingStatusIndicator";
import type { Paper } from "./types";

export interface PaperProcessingSectionProps {
  paper: Paper;
  paperId: string | number;
  isProcessing: boolean;
  setIsProcessing: (processing: boolean) => void;
  processingStartTime: Date | null;
  setProcessingStartTime: (time: Date | null) => void;
  processingError: string | null;
  setProcessingError: (error: string | null) => void;
  processingWithMarker: boolean;
  processingWithMinerU: boolean;
  processingWithAuto: boolean;
  isAnyProcessing: boolean;
  setPaper: React.Dispatch<React.SetStateAction<Paper | null>>;
  setShowMarkerModal: (show: boolean) => void;
  loadPaperDetails: () => void;
  pollProcessingStatus: () => Promise<ReturnType<typeof setInterval>>;
  pollingIntervalRef: React.MutableRefObject<ReturnType<typeof setInterval> | null>;
}

const PaperProcessingSection: React.FC<PaperProcessingSectionProps> = ({
  paper,
  paperId,
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
  setPaper,
  setShowMarkerModal,
  loadPaperDetails,
  pollProcessingStatus,
  pollingIntervalRef,
}) => {
  return (
    <div className="bg-gray-50 rounded-lg p-3 border">
      <div className="flex items-center gap-2 mb-2">
        <Cpu className="h-4 w-4 text-blue-600" />
        <span className="text-sm font-medium text-gray-700">Processing Status</span>
      </div>
      {isProcessing ? (
        <ProcessingTimer
          startTime={processingStartTime || new Date()}
          estimatedMinutes={10}
          paperId={paperId}
          onCheckStatus={async () => {
            try {
              const response = await axios.get(`/api/papers/${paperId}`);
              return response.data.processed || !!response.data.processing_error;
            } catch (error: any) {
              if (error.response?.status === 404) return true;
              return false;
            }
          }}
          onCancel={async () => {
            try {
              const response = await axios.post(
                `/api/papers/${paperId}/cancel-processing`
              );
              if (response.data.success) {
                setIsProcessing(false);
                loadPaperDetails();
              }
            } catch (error) {
              console.error("Failed to cancel processing:", error);
            }
          }}
        />
      ) : (
        <div className="space-y-1">
          {paper.processed ? (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                {paper.processor_used === "marker_service" && (
                  <Badge className="text-xs bg-purple-100 text-purple-800 border-purple-300">Marker</Badge>
                )}
                {paper.processor_used === "mineru_service" && (
                  <Badge className="text-xs bg-blue-100 text-blue-800 border-blue-300">MinerU</Badge>
                )}
                {paper.processor_used === "pypdfium2" && (
                  <Badge className="text-xs bg-gray-100 text-gray-600 border-gray-300">Basic</Badge>
                )}
                {!["marker_service", "mineru_service", "pypdfium2"].includes(paper.processor_used || "") &&
                  paper.processor_used && (
                    <Badge variant="outline" className="text-xs">{paper.processor_used}</Badge>
                  )}
              </div>

              {/* Reprocess Options */}
              {!isProcessing && (
                <div className="pt-2 border-t border-gray-200">
                  <div className="text-xs text-gray-500 mb-2">Reprocess with different method:</div>
                  <div className="flex flex-wrap gap-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => setShowMarkerModal(true)}
                      className="h-6 px-2 text-xs bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-300"
                    >
                      <Cpu className="h-3 w-3 mr-1" />
                      Use Marker
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={async () => {
                        try {
                          const response = await axios.post(
                            `/api/papers/${paperId}/process-with-mineru`
                          );
                          if (response.data.success) {
                            setPaper((prev) =>
                              prev ? { ...prev, processing_status: "processing_with_mineru" } : null
                            );
                          }
                        } catch (error) {
                          console.error("Failed to start MinerU processing:", error);
                        }
                      }}
                      className="h-6 px-2 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-300"
                    >
                      <GraduationCap className="h-3 w-3 mr-1" />
                      Use MinerU
                    </Button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="h-4 w-4 rounded-full bg-amber-100 flex items-center justify-center">
                  <div className="h-2 w-2 rounded-full bg-amber-500" />
                </div>
                <span className="text-sm font-medium text-amber-700">Ready to Process</span>
              </div>
              <p className="text-xs text-gray-600">Choose a processing method to extract text and structure:</p>
              {processingError && (
                <Alert variant="destructive" className="mb-2">
                  <AlertDescription className="text-xs">{processingError}</AlertDescription>
                </Alert>
              )}
              {!isProcessing && (
                <div className="flex flex-wrap gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      setProcessingError(null);
                      try {
                        const response = await axios.post(
                          `/api/papers/${paperId}/process-with-marker`
                        );
                        if (response.data.success) {
                          setPaper((prev) =>
                            prev ? { ...prev, processing_status: "processing_with_marker" } : null
                          );
                        }
                      } catch (error: any) {
                        console.error("Failed to start Marker processing:", error);
                        setProcessingError(
                          error.response?.data?.detail || "Failed to start Marker processing. Please try again."
                        );
                        setTimeout(() => setProcessingError(null), 5000);
                      }
                    }}
                    disabled={processingWithMarker || processingWithMinerU || processingWithAuto}
                    className="h-6 px-2 text-xs bg-purple-50 hover:bg-purple-100 text-purple-700 border-purple-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {processingWithMarker ? (
                      <>
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <Cpu className="h-3 w-3 mr-1" />
                        Use Marker
                      </>
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      setProcessingError(null);
                      try {
                        const response = await axios.post(
                          `/api/papers/${paperId}/process-with-mineru`
                        );
                        if (response.data.success) {
                          setPaper((prev) =>
                            prev ? { ...prev, processing_status: "processing_with_mineru" } : null
                          );
                        }
                      } catch (error: any) {
                        console.error("Failed to start MinerU processing:", error);
                        setProcessingError(
                          error.response?.data?.detail || "Failed to start MinerU processing. Please try again."
                        );
                        setTimeout(() => setProcessingError(null), 5000);
                      }
                    }}
                    disabled={processingWithMarker || processingWithMinerU || processingWithAuto}
                    className="h-6 px-2 text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 border-blue-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {processingWithMinerU ? (
                      <>
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <GraduationCap className="h-3 w-3 mr-1" />
                        Use MinerU
                      </>
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      setProcessingError(null);
                      try {
                        setIsProcessing(true);
                        setProcessingStartTime(new Date());
                        const response = await axios.post(
                          `/api/papers/${paperId}/process`
                        );
                        if (response.data.success) {
                          console.log("Processing started for paper", paperId);
                          const intervalId = await pollProcessingStatus();
                          pollingIntervalRef.current = intervalId;
                        }
                      } catch (error: any) {
                        console.error("Failed to start processing:", error);
                        setIsProcessing(false);
                        setProcessingError(
                          error.response?.data?.detail ||
                            "Failed to start automatic processing. Please try again."
                        );
                        setTimeout(() => setProcessingError(null), 5000);
                      }
                    }}
                    disabled={processingWithMarker || processingWithMinerU || processingWithAuto}
                    className="h-6 px-2 text-xs disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {processingWithAuto ? (
                      <>
                        <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                        Processing...
                      </>
                    ) : (
                      <>
                        <PlayCircle className="h-3 w-3 mr-1" />
                        Auto (Basic)
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          )}

          {/* Show retry button for errors */}
          {paper.processing_error && (
            <div className="mt-2 space-y-1">
              <p className="text-xs text-red-600">{paper.processing_error.slice(0, 100)}...</p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    try {
                      const response = await axios.post(
                        `/api/papers/${paperId}/process-with-marker`
                      );
                      if (response.data.success) {
                        setPaper((prev) =>
                          prev ? { ...prev, processing_status: "processing_with_marker" } : null
                        );
                      }
                    } catch (error) {
                      console.error("Failed to retry with Marker:", error);
                    }
                  }}
                  className="h-6 px-2 text-xs"
                >
                  <RotateCcw className="h-3 w-3 mr-1" />
                  Retry with Marker
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    try {
                      const response = await axios.post(
                        `/api/papers/${paperId}/process-with-mineru`
                      );
                      if (response.data.success) {
                        setPaper((prev) =>
                          prev ? { ...prev, processing_status: "processing_with_mineru" } : null
                        );
                      }
                    } catch (error) {
                      console.error("Failed to retry with MinerU:", error);
                    }
                  }}
                  className="h-6 px-2 text-xs"
                >
                  <RotateCcw className="h-3 w-3 mr-1" />
                  Retry with MinerU
                </Button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Processing Status Indicator */}
      {isAnyProcessing && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <ProcessingStatusIndicator
            paperId={paperId}
            compact={true}
            onComplete={() => loadPaperDetails()}
          />
        </div>
      )}
    </div>
  );
};

export default PaperProcessingSection;
