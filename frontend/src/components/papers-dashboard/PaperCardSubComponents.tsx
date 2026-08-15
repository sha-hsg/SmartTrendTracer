import React, { useState } from 'react'
import {
  Loader2,
  RotateCcw,
  PlayCircle,
  Star,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import type { Paper } from './types'

export const StarRating: React.FC<{
  rating?: number
  onRate?: (rating: number) => void
  size?: 'sm' | 'md'
  readOnly?: boolean
}> = ({ rating, onRate, size = 'sm', readOnly = false }) => {
  const [hoverRating, setHoverRating] = useState<number | null>(null)
  const displayRating = hoverRating ?? rating ?? 0
  const starSize = size === 'sm' ? 'h-4 w-4' : 'h-5 w-5'

  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={(e) => {
            if (readOnly || !onRate) return
            e.stopPropagation()
            onRate(star === rating ? 0 : star)
          }}
          onMouseEnter={() => !readOnly && setHoverRating(star)}
          onMouseLeave={() => !readOnly && setHoverRating(null)}
          className={`p-0.5 transition-transform ${!readOnly ? 'hover:scale-110 cursor-pointer' : 'cursor-default'}`}
          disabled={readOnly}
        >
          <Star
            className={`${starSize} ${
              star <= displayRating
                ? "fill-yellow-400 text-yellow-400"
                : "text-gray-300 dark:text-gray-600"
            }`}
          />
        </button>
      ))}
    </div>
  )
}

export const ProcessingStatus: React.FC<{
  paper: Paper
  processingPapers: Set<number>
  handleProcessPaper: (paperId: number, processor: 'marker' | 'mineru', e?: React.MouseEvent) => void
}> = ({ paper, processingPapers, handleProcessPaper }) => {
  if (paper.processing_error) {
    return (
      <div className="mb-2">
        <div className="flex items-center gap-2 mb-1">
          <Badge variant="destructive" className="bg-red-100 dark:bg-red-950 text-red-800 dark:text-red-300 text-xs">
            Processing Error
          </Badge>
          <Button
            size="sm"
            variant="outline"
            onClick={(e) => handleProcessPaper(paper.id, 'marker', e)}
            disabled={processingPapers.has(paper.id)}
            className="h-5 px-2 text-xs"
          >
            {processingPapers.has(paper.id)
              ? <><Loader2 className="h-3 w-3 mr-1 animate-spin" />Retrying...</>
              : <><RotateCcw className="h-3 w-3 mr-1" />Retry</>
            }
          </Button>
        </div>
        <p className="text-xs text-red-600 dark:text-red-400 pl-1">{paper.processing_error}</p>
      </div>
    )
  }

  if (!paper.processed && !paper.processing_error) {
    return (
      <div className="mb-2 flex items-center gap-2">
        <Badge className="bg-yellow-50 dark:bg-yellow-950 text-yellow-700 dark:text-yellow-300 border-yellow-200 dark:border-yellow-900 text-xs">
          Not Processed
        </Badge>
        <Button
          size="sm"
          variant="outline"
          onClick={(e) => handleProcessPaper(paper.id, 'marker', e)}
          disabled={processingPapers.has(paper.id)}
          className="h-5 px-2 text-xs"
        >
          {processingPapers.has(paper.id)
            ? <><Loader2 className="h-3 w-3 mr-1 animate-spin" />Processing...</>
            : <><PlayCircle className="h-3 w-3 mr-1" />Process</>
          }
        </Button>
      </div>
    )
  }

  if (paper.processed && paper.processor_used) {
    const processorBadge = (() => {
      if (paper.processor_used === 'pypdfium2') {
        return <Badge className="bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 border-gray-200 dark:border-gray-700 text-xs">Basic (Backup)</Badge>
      }
      if (paper.processor_used === 'marker' || paper.processor_used === 'marker_service') {
        return <Badge className="bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-900 text-xs">Marker</Badge>
      }
      if (paper.processor_used === 'mineru' || paper.processor_used === 'mineru_service') {
        return <Badge className="bg-blue-100 dark:bg-blue-950 text-blue-700 dark:text-blue-300 border-blue-200 dark:border-blue-900 text-xs">MinerU</Badge>
      }
      if (paper.processor_used === 'pix2text') {
        return <Badge className="bg-green-100 dark:bg-green-950 text-green-700 dark:text-green-300 border-green-200 dark:border-green-900 text-xs">Pix2Text</Badge>
      }
      return <Badge className="bg-purple-100 dark:bg-purple-950 text-purple-700 dark:text-purple-300 border-purple-200 dark:border-purple-900 text-xs">{paper.processor_used.replace('_', ' ').replace('service', '').trim()}</Badge>
    })()

    return (
      <div className="mb-2 flex items-center gap-2">
        {processorBadge}
        <div className="flex gap-1">
          <Button
            size="sm" variant="outline"
            onClick={(e) => handleProcessPaper(paper.id, 'marker', e)}
            disabled={processingPapers.has(paper.id)}
            className="h-5 px-2 text-xs"
            title="Reprocess with Marker service for better quality"
          >
            {processingPapers.has(paper.id)
              ? <><Loader2 className="h-3 w-3 mr-1 animate-spin" />Processing...</>
              : <><RotateCcw className="h-3 w-3 mr-1" />Use Marker</>
            }
          </Button>
          <Button
            size="sm" variant="outline"
            onClick={(e) => handleProcessPaper(paper.id, 'mineru', e)}
            disabled={processingPapers.has(paper.id)}
            className="h-5 px-2 text-xs"
            title="Reprocess with MinerU service for math-heavy PDFs"
          >
            {processingPapers.has(paper.id)
              ? <><Loader2 className="h-3 w-3 mr-1 animate-spin" />Processing...</>
              : <><RotateCcw className="h-3 w-3 mr-1" />Use MinerU</>
            }
          </Button>
        </div>
      </div>
    )
  }

  return null
}
