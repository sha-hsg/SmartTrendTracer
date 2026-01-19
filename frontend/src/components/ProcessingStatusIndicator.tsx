import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle, Clock, AlertCircle, XCircle } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface ProcessingStatusIndicatorProps {
  paperId: string | number;
  onComplete?: () => void;
  onStatusChange?: (status: string) => void;
  compact?: boolean;
  showControls?: boolean;
}

export const ProcessingStatusIndicator: React.FC<ProcessingStatusIndicatorProps> = ({
  paperId,
  onComplete,
  onStatusChange,
  compact = false,
  showControls = true
}) => {
  const [status, setStatus] = useState<string>('checking');
  const [elapsedMinutes, setElapsedMinutes] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [progressData, setProgressData] = useState<any>(null);
  const [progressMessage, setProgressMessage] = useState<string>('');
  const [progressPercentage, setProgressPercentage] = useState<number>(0);
  const [completedNotified, setCompletedNotified] = useState<boolean>(false);
  const [processHealth, setProcessHealth] = useState<any>(null);

  useEffect(() => {
    // Start polling if processing
    if (status === 'processing_with_marker' || status === 'processing_with_mineru' || status === 'processing_pdf' || status === 'processing_analyses') {
      setIsPolling(true);
      setCompletedNotified(false); // Reset completion notification when processing starts
    } else {
      setIsPolling(false);
    }
  }, [status]);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const response = await fetch(`/api/papers/${paperId}/processing-status`);
        if (response.ok) {
          const data = await response.json();
          setStatus(data.status);
          setElapsedMinutes(data.elapsed_minutes || null);
          setError(data.error || null);
          
          // Reset completion flag if status changed away from completed
          if (data.status !== 'completed' && completedNotified) {
            setCompletedNotified(false);
          }
          
          // Update progress data
          if (data.progress) {
            setProgressData(data.progress);
            setProgressMessage(data.progress_message || 'Processing...');
            setProgressPercentage(data.progress_percentage || 0);
          } else {
            // Clear progress data when not processing
            setProgressData(null);
            setProgressMessage('');
            setProgressPercentage(0);
          }
          
          if (onStatusChange && data.status !== status) {
            onStatusChange(data.status);
          }
          
          if (data.status === 'completed' && onComplete && !completedNotified) {
            setCompletedNotified(true);
            onComplete();
          }

          // Stop polling if completed or failed
          if (data.status === 'completed' || data.status === 'failed' || data.status === 'cancelled') {
            setIsPolling(false);
          }
        }
      } catch (error) {
        console.error('Failed to check processing status:', error);
        setStatus('error');
      }
    };

    // Initial check
    checkStatus();

    if (!isPolling) return;

    // Poll every 10 seconds for near real-time updates
    const interval = setInterval(checkStatus, 10000);

    return () => clearInterval(interval);
  }, [paperId, status, onComplete, onStatusChange, isPolling]);

  // Separate polling for process health (every 30 seconds)
  useEffect(() => {
    if (!isPolling) {
      setProcessHealth(null); // Clear health data when not processing
      return;
    }

    const checkHealth = async () => {
      try {
        const response = await fetch(`/api/papers/${paperId}/process-health`);
        if (response.ok) {
          const data = await response.json();
          if (data.is_processing && data.health) {
            setProcessHealth(data.health);
          } else {
            setProcessHealth(null);
          }
        }
      } catch (error) {
        console.error('Failed to check process health:', error);
        // Don't show error to user, health is optional
      }
    };

    // Initial check
    checkHealth();

    // Poll every 10 seconds for health metrics (CPU, RAM)
    const healthInterval = setInterval(checkHealth, 10000);

    return () => clearInterval(healthInterval);
  }, [paperId, isPolling]);

  const handleCancel = async () => {
    try {
      const response = await fetch(`/api/papers/${paperId}/cancel-processing`, {
        method: 'POST'
      });
      if (response.ok) {
        setStatus('cancelled');
        setIsPolling(false);
        if (onStatusChange) {
          onStatusChange('cancelled');
        }
      }
    } catch (err) {
      console.error('Failed to cancel processing:', err);
    }
  };

  const handleStartProcessing = async () => {
    try {
      const response = await fetch(`/api/papers/${paperId}/process-with-marker`, {
        method: 'POST'
      });
      if (response.ok) {
        const data = await response.json();
        setStatus('processing_with_marker');
        setIsPolling(true);
        if (onStatusChange) {
          onStatusChange('processing_with_marker');
        }
      }
    } catch (err) {
      console.error('Failed to start processing:', err);
    }
  };

  // Compact view for paper tiles
  if (compact) {
    if (status === 'processing_with_marker' || status === 'processing_with_mineru' || status === 'processing_pdf') {
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                <div className="flex flex-col">
                  <span className="text-sm text-muted-foreground">
                    {status === 'processing_with_marker' ? 'Marker' : 
                     status === 'processing_with_mineru' ? 'MinerU' : 
                     'Processing'}: {elapsedMinutes ? `${elapsedMinutes}m` : 'Starting...'}
                  </span>
                  {progressMessage && (
                    <span className="text-xs text-blue-600">
                      {progressMessage} {progressPercentage > 0 && `(${Math.round(progressPercentage)}%)`}
                    </span>
                  )}
                </div>
                {showControls && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={handleCancel}
                    className="h-6 px-2 text-red-600"
                  >
                    Cancel
                  </Button>
                )}
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>Processing with {status === 'processing_with_marker' ? 'Marker' : 
                               status === 'processing_with_mineru' ? 'MinerU' : 
                               'PDF processor'} service</p>
              {elapsedMinutes && <p>Elapsed: {elapsedMinutes} minutes</p>}
              {progressMessage && progressPercentage > 0 && (
                <p className="text-xs font-semibold">Progress: {Math.round(progressPercentage)}%</p>
              )}
              <p className="text-xs text-muted-foreground">
                Expected: {status === 'processing_with_mineru' ? '15-20 minutes' : '10-15 minutes'}
              </p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    if (status === 'completed') {
      return (
        <Badge variant="default" className="bg-green-500">
          <CheckCircle className="h-3 w-3 mr-1" />
          Processing Complete
        </Badge>
      );
    }

    if (status === 'failed' || status === 'error') {
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div>
                <Badge variant="destructive">
                  <XCircle className="h-3 w-3 mr-1" />
                  Failed
                </Badge>
              </div>
            </TooltipTrigger>
            <TooltipContent>
              <p>{error || 'Processing failed'}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      );
    }

    if (status === 'cancelled') {
      return (
        <Badge variant="outline" className="text-orange-600">
          <XCircle className="h-3 w-3 mr-1" />
          Cancelled
        </Badge>
      );
    }

    return null;
  }

  // Full view for paper details
  if (status === 'completed') {
    return (
      <div className="flex items-center gap-2 text-green-600">
        <CheckCircle className="w-4 h-4" />
        <span className="text-sm">Processing complete</span>
      </div>
    );
  }

  if (status === 'processing_with_marker' || status === 'processing_with_mineru' || status === 'processing_pdf') {
    return (
      <div className="flex items-center gap-3 p-3 border rounded-lg bg-blue-50">
        <Loader2 className="w-5 h-5 animate-spin text-blue-600" />
        <div className="flex-1">
          <p className="font-medium text-blue-900">
            Processing with {status === 'processing_with_marker' ? 'Marker' : 
                           status === 'processing_with_mineru' ? 'MinerU' : 
                           'PDF processor'}...
          </p>
          <p className="text-sm text-blue-700">
            {elapsedMinutes ? `${elapsedMinutes} minutes elapsed` : 'Starting...'}
          </p>
          {progressMessage && (
            <p className="text-sm text-blue-800 mt-1">
              {progressMessage}
            </p>
          )}
          {progressPercentage > 0 && (
            <div className="w-full bg-blue-200 rounded-full h-2 mt-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{width: `${Math.min(progressPercentage, 100)}%`}}
              />
            </div>
          )}
          {processHealth && (
            <div className="mt-3 pt-3 border-t border-blue-200">
              <p className="text-xs font-semibold text-blue-900 mb-1">📊 Process Health:</p>
              <div className="grid grid-cols-2 gap-2 text-xs text-blue-700">
                {processHealth.pid && (
                  <div>
                    <span className="font-medium">PID:</span> {processHealth.pid}
                  </div>
                )}
                <div>
                  <span className="font-medium">CPU:</span> {processHealth.cpu_percent?.toFixed(1) || 0}%
                  {processHealth.cpu_time && ` (${processHealth.cpu_time.toFixed(1)}s total)`}
                </div>
                <div>
                  <span className="font-medium">RAM:</span> {processHealth.memory_mb ? `${(processHealth.memory_mb / 1024).toFixed(1)} GB` : '0 MB'}
                </div>
                <div>
                  <span className="font-medium">Output:</span>{' '}
                  {processHealth.output_files?.markdown_exists ? (
                    <span className="text-green-600 font-semibold">✓ MD generated</span>
                  ) : (
                    <span>Processing...</span>
                  )}
                </div>
                {processHealth.output_files?.image_count > 0 && (
                  <div className="col-span-2">
                    <span className="font-medium">Images:</span> {processHealth.output_files.image_count} extracted
                  </div>
                )}
              </div>
            </div>
          )}
          <p className="text-xs text-blue-600 mt-2">
            Expected time: {status === 'processing_with_mineru' ? '15-20 minutes' : '10-15 minutes'} for complex papers
          </p>
        </div>
        {showControls && (
          <Button
            variant="outline"
            size="sm"
            onClick={handleCancel}
            className="text-red-600 hover:text-red-700"
          >
            Cancel
          </Button>
        )}
      </div>
    );
  }

  if (status === 'failed' || status === 'error') {
    return (
      <div className="flex items-center gap-2 text-red-600">
        <AlertCircle className="w-4 h-4" />
        <span className="text-sm">{error || 'Processing error'}</span>
        {showControls && (
          <Button
            size="sm"
            variant="outline"
            onClick={handleStartProcessing}
            className="ml-2"
          >
            Retry
          </Button>
        )}
      </div>
    );
  }

  if (status === 'cancelled') {
    return (
      <div className="flex items-center gap-2 text-orange-600">
        <XCircle className="w-4 h-4" />
        <span className="text-sm">Processing cancelled</span>
        {showControls && (
          <Button
            size="sm"
            variant="outline"
            onClick={handleStartProcessing}
            className="ml-2"
          >
            Restart
          </Button>
        )}
      </div>
    );
  }

  if (status === 'not_started' && showControls) {
    return (
      <div className="flex items-center gap-2">
        <Button
          size="sm"
          onClick={handleStartProcessing}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Clock className="w-4 h-4 mr-2" />
          Use Marker Service
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-gray-500">
      <Clock className="w-4 h-4" />
      <span className="text-sm">Checking status...</span>
    </div>
  );
};