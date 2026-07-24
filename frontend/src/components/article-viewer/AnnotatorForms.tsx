/**
 * AnnotatorForms - Annotation and Tag creation form sub-components
 * for ArticleAnnotator portal UI.
 *
 * Extracted from ArticleAnnotator.tsx to keep file sizes manageable.
 */
import React from 'react'
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { X, AlertCircle } from 'lucide-react'

const stopEvent = (e: React.MouseEvent) => { e.stopPropagation(); e.preventDefault() }

export function AnnotationForm({
  selectedText,
  snippetCategory,
  annotation,
  onCategoryChange,
  onAnnotationChange,
  onSave,
  onCancel,
}: {
  selectedText: string
  snippetCategory: string
  annotation: string
  onCategoryChange: (v: string) => void
  onAnnotationChange: (v: string) => void
  onSave: () => void
  onCancel: () => void
}) {
  return (
    <div className="fixed w-96 annotation-form" style={{
      left: '50%', top: '20%', transform: 'translateX(-50%)',
      backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px',
      boxShadow: '0 10px 40px rgba(0,0,0,0.3)', pointerEvents: 'auto',
    }}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold">Create Annotation</h3>
          <button type="button" onMouseUp={(e) => { stopEvent(e); onCancel() }}
            className="h-6 w-6 rounded hover:bg-gray-100 flex items-center justify-center" style={{ cursor: 'pointer' }}>
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="p-4 space-y-3">
        <div>
          <Label className="text-sm font-medium">Selected Text:</Label>
          <div className="mt-1 p-2 bg-gray-50 rounded border text-sm">{selectedText}</div>
        </div>
        <div>
          <Label className="text-sm font-medium">Category:</Label>
          <select value={snippetCategory} onChange={(e) => onCategoryChange(e.target.value)}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            style={{ cursor: 'pointer' }}>
            <option value="insight">{'\uD83D\uDCA1'} Insight</option>
            <option value="question">{'\u2753'} Question</option>
            <option value="critique">{'\uD83E\uDD14'} Critique</option>
            <option value="todo">{'\u2705'} Todo</option>
            <option value="quote">{'\uD83D\uDCAC'} Quote</option>
          </select>
        </div>
        <div>
          <Label className="text-sm font-medium">Add Note (optional):</Label>
          <textarea placeholder="Add your thoughts or context about this snippet..."
            value={annotation} onChange={(e) => onAnnotationChange(e.target.value)}
            onMouseDown={(e) => e.stopPropagation()} onClick={(e) => e.stopPropagation()}
            rows={3}
            className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            style={{ cursor: 'text' }} />
        </div>
        <div className="flex gap-2">
          <button type="button" onMouseUp={(e) => { stopEvent(e); onCancel() }}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50" style={{ cursor: 'pointer' }}>
            Cancel
          </button>
          <button type="button" onMouseUp={(e) => { stopEvent(e); onSave() }}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700" style={{ cursor: 'pointer' }}>
            Save Snippet
          </button>
        </div>
      </div>
    </div>
  )
}

export function TagCreationForm({
  selectedText,
  tagEditText,
  tagError,
  onTagEditTextChange,
  onSave,
  onCancel,
}: {
  selectedText: string
  tagEditText: string
  tagError: string
  onTagEditTextChange: (v: string) => void
  onSave: () => void
  onCancel: () => void
}) {
  return (
    <div className="fixed w-96 tag-creation-form" style={{
      left: '50%', top: '25%', transform: 'translateX(-50%)',
      backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px',
      boxShadow: '0 10px 40px rgba(0,0,0,0.3)', pointerEvents: 'auto',
    }}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold">{'\uD83C\uDFF7\uFE0F'} Create Concept from Selection</h3>
          <button type="button" onMouseUp={(e) => { stopEvent(e); onCancel() }}
            className="h-6 w-6 rounded hover:bg-gray-100 flex items-center justify-center" style={{ cursor: 'pointer' }}>
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="p-4 space-y-3">
        <div className="text-sm text-muted-foreground">
          Original text: &ldquo;{selectedText ? selectedText.substring(0, 50) : ''}{selectedText && selectedText.length > 50 ? '...' : ''}&rdquo;
        </div>
        <div>
          <Label htmlFor="tag-edit">Edit tag name:</Label>
          <Input id="tag-edit" value={tagEditText}
            onChange={(e) => onTagEditTextChange(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') { e.preventDefault(); e.stopPropagation(); onSave() }
              else if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); onCancel() }
            }}
            onClick={(e) => e.stopPropagation()}
            autoFocus
          />
          <p className="text-xs text-muted-foreground mt-1">
            Spaces will be converted to hyphens. Capital letters are preserved for proper nouns.
          </p>
          {tagError && (
            <Alert variant="destructive" className="mt-2">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{tagError}</AlertDescription>
            </Alert>
          )}
        </div>
        <div className="flex gap-2">
          <button type="button" onMouseUp={(e) => { stopEvent(e); onCancel() }}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50" style={{ cursor: 'pointer' }}>
            Cancel
          </button>
          <button type="button" onMouseUp={(e) => { stopEvent(e); onSave() }}
            disabled={!tagEditText}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            style={{ cursor: tagEditText ? 'pointer' : 'not-allowed' }}>
            Create Concept
          </button>
        </div>
      </div>
    </div>
  )
}
