import React, { useState, useEffect } from 'react'
import { Loader2, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ProcessingTimerProps {
  startTime?: Date
  estimatedMinutes?: number
  onCheckStatus?: () => Promise<boolean>
  onCancel?: () => void
  paperId?: number
}

export const ProcessingTimer: React.FC<ProcessingTimerProps> = ({ 
  startTime = new Date(), 
  estimatedMinutes = 10,  // Changed to 10 minutes as Marker can take longer
  onCheckStatus,
  onCancel,
  paperId 
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [isComplete, setIsComplete] = useState(false)
  const [showCancelButton, setShowCancelButton] = useState(false)

  useEffect(() => {
    const interval = setInterval(async () => {
      const now = new Date()
      const elapsed = Math.floor((now.getTime() - startTime.getTime()) / 1000)
      setElapsedSeconds(elapsed)
      
      // Show cancel button after 5 minutes
      if (elapsed >= 300 && !showCancelButton) {
        setShowCancelButton(true)
      }

      // Check status every 30 seconds
      if (elapsed % 30 === 0 && onCheckStatus) {
        const complete = await onCheckStatus()
        if (complete) {
          setIsComplete(true)
          clearInterval(interval)
        }
      }
    }, 1000)

    return () => clearInterval(interval)
  }, [startTime, onCheckStatus])

  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${minutes}:${secs.toString().padStart(2, '0')}`
  }

  const getEstimateMessage = (): string => {
    const estimatedSeconds = estimatedMinutes * 60
    const percentComplete = Math.min(100, Math.floor((elapsedSeconds / estimatedSeconds) * 100))
    
    if (elapsedSeconds < 60) {
      return `Just started... Marker processing with LLM can take up to ${estimatedMinutes} minutes`
    } else if (elapsedSeconds < estimatedSeconds * 0.5) {
      return `Processing PDF with Marker... About ${Math.ceil((estimatedSeconds - elapsedSeconds) / 60)} minutes remaining`
    } else if (elapsedSeconds < estimatedSeconds * 0.8) {
      return `Still processing... Should be done in ${Math.ceil((estimatedSeconds - elapsedSeconds) / 60)} minute${Math.ceil((estimatedSeconds - elapsedSeconds) / 60) === 1 ? '' : 's'}`
    } else if (elapsedSeconds < estimatedSeconds) {
      return 'Almost done... Just a bit longer'
    } else if (elapsedSeconds < estimatedSeconds * 1.5) {
      return 'Taking a bit longer than expected... Complex PDFs may need extra time'
    } else {
      return 'This is taking unusually long. The PDF might be very complex or there might be an issue.'
    }
  }

  if (isComplete) {
    return (
      <div className="flex items-center gap-2 text-green-600">
        <span className="text-sm font-medium">✓ Processing Complete!</span>
        <span className="text-xs text-gray-500">({formatTime(elapsedSeconds)})</span>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-3">
        <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-gray-700">Processing with Marker Service</span>
            <span className="text-sm font-mono text-gray-500">{formatTime(elapsedSeconds)}</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">{getEstimateMessage()}</p>
        </div>
      </div>
      
      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-1.5">
        <div 
          className="bg-blue-500 h-1.5 rounded-full transition-all duration-1000"
          style={{ 
            width: `${Math.min(100, (elapsedSeconds / (estimatedMinutes * 60)) * 100)}%` 
          }}
        />
      </div>

      {elapsedSeconds > 30 && elapsedSeconds % 30 < 2 && (
        <p className="text-xs text-gray-400 animate-pulse">
          Checking status...
        </p>
      )}
      
      {/* Cancel button after 5 minutes */}
      {showCancelButton && onCancel && (
        <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
          <div className="flex items-start gap-2">
            <div className="flex-1">
              <p className="text-xs font-medium text-yellow-800">
                Processing is taking longer than expected
              </p>
              <p className="text-xs text-yellow-700 mt-1">
                {elapsedSeconds >= 1800 
                  ? 'This has been running for over 30 minutes. The Marker service might be stuck.'
                  : 'If the Marker service is not responding, you can cancel and try again later.'}
              </p>
            </div>
            <Button
              size="sm"
              variant="destructive"
              onClick={onCancel}
              className="flex items-center gap-1"
            >
              <XCircle className="h-3 w-3" />
              Cancel
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}