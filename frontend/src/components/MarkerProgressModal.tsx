import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Loader2,
  CheckCircle,
  XCircle,
  AlertCircle,
  FileText,
  Cpu,
  Clock,
  RotateCcw,
} from 'lucide-react';
import http from '@/services/http'

interface MarkerProgressModalProps {
  isOpen: boolean;
  onClose: () => void;
  paperId: string | number;
  paperTitle?: string;
  onSuccess?: () => void;
}

interface ProgressUpdate {
  stage: string;
  message: string;
  progress: number;
  error?: string;
  timestamp?: string;
}

export const MarkerProgressModal: React.FC<MarkerProgressModalProps> = ({
  isOpen,
  onClose,
  paperId,
  paperTitle,
  onSuccess,
}) => {
  const [status, setStatus] = useState<'idle' | 'processing' | 'success' | 'error'>('idle');
  const [progress, setProgress] = useState(0);
  const [currentStage, setCurrentStage] = useState('Initializing...');
  const [logs, setLogs] = useState<ProgressUpdate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [pollingInterval, setPollingInterval] = useState<ReturnType<typeof setInterval> | null>(null);

  // Update elapsed time
  useEffect(() => {
    if (status === 'processing' && startTime) {
      const timer = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime.getTime()) / 1000));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [status, startTime]);

  // Poll for status updates
  useEffect(() => {
    if (status === 'processing' && paperId) {
      const interval = setInterval(async () => {
        try {
          const response = await http.get(
            `/api/papers/${paperId}`
          );
          
          const paper = response.data;
          
          // Check processing status
          if (paper.processing_status === 'completed_with_marker') {
            setStatus('success');
            setProgress(100);
            setCurrentStage('Processing completed successfully!');
            addLog({
              stage: 'completed',
              message: 'Marker processing finished successfully',
              progress: 100,
            });
            if (onSuccess) {
              onSuccess();
            }
            if (pollingInterval) {
              clearInterval(pollingInterval);
            }
          } else if (paper.processing_status === 'failed') {
            setStatus('error');
            setError(paper.processing_error || 'Processing failed');
            setCurrentStage('Processing failed');
            addLog({
              stage: 'failed',
              message: paper.processing_error || 'Unknown error occurred',
              progress: progress,
              error: paper.processing_error,
            });
            if (pollingInterval) {
              clearInterval(pollingInterval);
            }
          }
        } catch (err) {
          console.error('Error polling status:', err);
        }
      }, 2000); // Poll every 2 seconds
      
      setPollingInterval(interval);
      
      return () => {
        if (interval) {
          clearInterval(interval);
        }
      };
    }
  }, [status, paperId, onSuccess, progress]);

  const addLog = (update: ProgressUpdate) => {
    setLogs((prev) => [...prev, { ...update, timestamp: new Date().toISOString() }]);
  };

  const startProcessing = async () => {
    setStatus('processing');
    setProgress(0);
    setError(null);
    setLogs([]);
    setStartTime(new Date());
    setCurrentStage('Starting Marker processing...');
    
    addLog({
      stage: 'initializing',
      message: 'Initiating Marker PDF processing service',
      progress: 0,
    });

    try {
      // Start the Marker processing
      const response = await http.post(
        `/api/papers/${paperId}/process-with-marker`
      );

      if (response.data.success) {
        setProgress(10);
        setCurrentStage('Connecting to Marker service...');
        addLog({
          stage: 'connecting',
          message: 'Successfully connected to Marker service',
          progress: 10,
        });

        // Simulate progress updates (in real implementation, these would come from server)
        setTimeout(() => {
          setProgress(30);
          setCurrentStage('Loading PDF document...');
          addLog({
            stage: 'loading',
            message: 'PDF document loaded into memory',
            progress: 30,
          });
        }, 1000);

        setTimeout(() => {
          setProgress(50);
          setCurrentStage('Extracting text and structure...');
          addLog({
            stage: 'extracting',
            message: 'Analyzing document structure and extracting content',
            progress: 50,
          });
        }, 3000);

        setTimeout(() => {
          setProgress(70);
          setCurrentStage('Processing images and tables...');
          addLog({
            stage: 'processing_media',
            message: 'Extracting images and table data',
            progress: 70,
          });
        }, 5000);

        setTimeout(() => {
          setProgress(90);
          setCurrentStage('Generating markdown output...');
          addLog({
            stage: 'generating',
            message: 'Converting to markdown format',
            progress: 90,
          });
        }, 7000);

      } else {
        throw new Error(response.data.message || 'Failed to start processing');
      }
    } catch (err: any) {
      setStatus('error');
      setError(err.response?.data?.detail || err.message || 'Failed to start Marker processing');
      setCurrentStage('Error occurred');
      addLog({
        stage: 'error',
        message: err.response?.data?.detail || err.message,
        progress: progress,
        error: err.message,
      });
    }
  };

  const handleRetry = () => {
    setStatus('idle');
    setProgress(0);
    setError(null);
    setLogs([]);
    setElapsedTime(0);
    startProcessing();
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />;
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <Cpu className="h-5 w-5 text-gray-500" />;
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Cpu className="h-5 w-5" />
            Marker PDF Processing
          </DialogTitle>
          <DialogDescription>
            {paperTitle ? (
              <div className="flex items-center gap-2 mt-1">
                <FileText className="h-4 w-4" />
                <span className="font-medium">{paperTitle}</span>
              </div>
            ) : (
              'Processing PDF document with Marker service'
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Status Display */}
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2">
              {getStatusIcon()}
              <span className="font-medium">{currentStage}</span>
            </div>
            {status === 'processing' && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Clock className="h-4 w-4" />
                <span>{formatTime(elapsedTime)}</span>
              </div>
            )}
          </div>

          {/* Progress Bar */}
          {(status === 'processing' || status === 'success') && (
            <div className="space-y-2">
              <div className="flex justify-between text-sm text-gray-600">
                <span>Progress</span>
                <span>{progress}%</span>
              </div>
              <Progress value={progress} className="h-2" />
            </div>
          )}

          {/* Error Display */}
          {error && (
            <Alert className="bg-red-50 border-red-200">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800">
                {error}
              </AlertDescription>
            </Alert>
          )}

          {/* Processing Logs */}
          {logs.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-gray-700">Processing Log</h4>
              <ScrollArea className="h-48 w-full rounded-md border p-3">
                <div className="space-y-2">
                  {logs.map((log, index) => (
                    <div
                      key={index}
                      className={`text-xs ${
                        log.error ? 'text-red-600' : 'text-gray-600'
                      }`}
                    >
                      <span className="font-mono text-gray-400">
                        [{new Date(log.timestamp || '').toLocaleTimeString()}]
                      </span>{' '}
                      <span className={log.stage === 'completed' ? 'text-green-600' : ''}>
                        {log.message}
                      </span>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end gap-2">
            {status === 'idle' && (
              <>
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button onClick={startProcessing}>
                  <Cpu className="h-4 w-4 mr-2" />
                  Start Processing
                </Button>
              </>
            )}
            {status === 'processing' && (
              <Button variant="outline" disabled>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </Button>
            )}
            {status === 'success' && (
              <Button onClick={onClose}>
                <CheckCircle className="h-4 w-4 mr-2" />
                Done
              </Button>
            )}
            {status === 'error' && (
              <>
                <Button variant="outline" onClick={onClose}>
                  Close
                </Button>
                <Button onClick={handleRetry}>
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Retry
                </Button>
              </>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
};