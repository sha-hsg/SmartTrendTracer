/**
 * ArticleAnnotator - Context menu and annotation forms for article text selection.
 *
 * Renders portal-based UI for:
 *   - Context menu (highlight, snippet, concept creation)
 *   - Highlight color picker form
 *   - Annotation/snippet creation form
 *   - Concept/tag creation form
 *
 * All forms are rendered via ReactDOM.createPortal to escape the Dialog's z-index.
 */
import React, { useState, useRef, useCallback, useEffect } from 'react'
import ReactDOM from 'react-dom'
import { Label } from "@/components/ui/label"
import { X, Palette, StickyNote } from 'lucide-react'
import { useTextSelection } from '../ArticleViewer/hooks/useTextSelection'
import { AnnotationForm, TagCreationForm } from './AnnotatorForms'

/**
 * The annotator manages its own visibility state for the context menu and forms.
 * The parent triggers it via `handleContextMenu` (returned from this component's hook).
 */
export function useArticleAnnotator() {
  const [selectedText, setSelectedText] = useState('')
  const [preservedSelection, setPreservedSelection] = useState<{ text: string; rangeData: any } | null>(null)
  const [showContextMenu, setShowContextMenu] = useState(false)
  const [showHighlightForm, setShowHighlightForm] = useState(false)
  const [showAnnotationForm, setShowAnnotationForm] = useState(false)
  const [showTagCreation, setShowTagCreation] = useState(false)
  const [hasSelectedText, setHasSelectedText] = useState(false)
  const [selectionCoords, setSelectionCoords] = useState<{ x: number; y: number }>({ x: 0, y: 0 })
  const [tagEditText, setTagEditText] = useState('')
  const [tagError, setTagError] = useState('')
  const [highlightColor, setHighlightColor] = useState('yellow')
  const [annotation, setAnnotation] = useState('')
  const [snippetCategory, setSnippetCategory] = useState('insight')
  const [selectedSummaryText, setSelectedSummaryText] = useState('')

  const selectedTextRef = useRef<string>('')
  const selectionRangeRef = useRef<Range | null>(null)

  const { isInteractingWithMenu, lastSelectionRef } = useTextSelection({
    showContextMenu,
    setShowContextMenu,
    showHighlightForm,
    showAnnotationForm,
    showTagCreation,
    preservedSelection,
    selectedText,
    setSelectedText,
    selectedTextRef,
  })

  const cancelSelection = useCallback(() => {
    setShowContextMenu(false)
    setShowHighlightForm(false)
    setShowAnnotationForm(false)
    setShowTagCreation(false)
    setSelectedText('')
    setAnnotation('')
    setTagEditText('')
    setTagError('')
    isInteractingWithMenu.current = false
    setHasSelectedText(false)
    setPreservedSelection(null)
    selectedTextRef.current = ''
    selectionRangeRef.current = null
    setTimeout(() => {
      isInteractingWithMenu.current = false
    }, 100)
  }, [isInteractingWithMenu])

  const handleContextMenu = useCallback((e: React.MouseEvent) => {
    try {
      e.preventDefault()
      e.stopPropagation()
      const selection = window.getSelection()
      if (!selection || selection.rangeCount === 0 || selection.isCollapsed) return
      const text = selection.toString().trim()
      if (!text) return

      setSelectedText(text)
      selectedTextRef.current = text
      setPreservedSelection({ text, rangeData: null })
      setTagEditText(text.replace(/\s+/g, '-'))
      setHasSelectedText(true)

      const coords = { x: e.clientX, y: e.clientY }
      if (coords.y + 200 > window.innerHeight) {
        coords.y = e.clientY - 150
      }
      setSelectionCoords(coords)
      isInteractingWithMenu.current = true
      setShowContextMenu(true)
    } catch (error) {
      console.error('Error in handleContextMenu:', error)
      setShowContextMenu(false)
      setSelectedText('')
      selectedTextRef.current = ''
    }
  }, [isInteractingWithMenu])

  return {
    // State needed by parent
    selectedText,
    selectedSummaryText,
    setSelectedSummaryText,
    showContextMenu,
    showHighlightForm,
    showAnnotationForm,
    showTagCreation,
    hasSelectedText,
    selectionCoords,
    tagEditText,
    setTagEditText,
    tagError,
    setTagError,
    highlightColor,
    setHighlightColor,
    annotation,
    setAnnotation,
    snippetCategory,
    setSnippetCategory,
    selectedTextRef,

    // Refs
    isInteractingWithMenu,
    lastSelectionRef,

    // Actions
    cancelSelection,
    handleContextMenu,

    // For transitioning between forms
    setShowContextMenu,
    setShowHighlightForm,
    setShowAnnotationForm,
    setShowTagCreation,
  }
}

// ---------- Portal-based UI Components ----------

interface AnnotatorPortalsProps {
  showContextMenu: boolean
  showHighlightForm: boolean
  showAnnotationForm: boolean
  showTagCreation: boolean
  selectionCoords: { x: number; y: number }
  selectedText: string
  selectedTextRef: React.MutableRefObject<string>
  tagEditText: string
  tagError: string
  highlightColor: string
  annotation: string
  snippetCategory: string
  isInteractingWithMenu: React.MutableRefObject<boolean>
  onSetShowContextMenu: (v: boolean) => void
  onSetShowHighlightForm: (v: boolean) => void
  onSetShowAnnotationForm: (v: boolean) => void
  onSetShowTagCreation: (v: boolean) => void
  onSetTagEditText: (v: string) => void
  onSetTagError: (v: string) => void
  onSetHighlightColor: (v: string) => void
  onSetAnnotation: (v: string) => void
  onSetSnippetCategory: (v: string) => void
  onCancelSelection: () => void
  onSaveHighlight: (text: string, color: string) => Promise<boolean | undefined>
  onSaveAnnotation: (text: string, category: string, annotationText: string) => Promise<boolean | undefined>
  onSaveTag: (tagText: string) => Promise<{ success: boolean; error?: string }>
}

export function AnnotatorPortals({
  showContextMenu,
  showHighlightForm,
  showAnnotationForm,
  showTagCreation,
  selectionCoords,
  selectedText,
  selectedTextRef,
  tagEditText,
  tagError,
  highlightColor,
  annotation,
  snippetCategory,
  isInteractingWithMenu,
  onSetShowContextMenu,
  onSetShowHighlightForm,
  onSetShowAnnotationForm,
  onSetShowTagCreation,
  onSetTagEditText,
  onSetTagError,
  onSetHighlightColor,
  onSetAnnotation,
  onSetSnippetCategory,
  onCancelSelection,
  onSaveHighlight,
  onSaveAnnotation,
  onSaveTag,
}: AnnotatorPortalsProps) {
  return (
    <>
      {/* Context Menu */}
      {showContextMenu && selectionCoords && selectionCoords.x !== undefined && selectionCoords.y !== undefined && ReactDOM.createPortal(
        <ContextMenuContent
          coords={selectionCoords}
          isInteractingWithMenu={isInteractingWithMenu}
          onHighlight={() => {
            isInteractingWithMenu.current = true
            onSetShowContextMenu(false)
            onSetShowHighlightForm(true)
          }}
          onSnippet={() => {
            isInteractingWithMenu.current = true
            onSetShowContextMenu(false)
            onSetShowAnnotationForm(true)
          }}
          onConcept={() => {
            isInteractingWithMenu.current = true
            onSetTagEditText(selectedTextRef.current || '')
            onSetShowContextMenu(false)
            onSetShowTagCreation(true)
          }}
          onCancel={onCancelSelection}
        />,
        document.body
      )}

      {/* Highlight Form */}
      {showHighlightForm && selectionCoords && (
        <PortalForm visible={showHighlightForm}>
          <HighlightForm
            selectedText={selectedText}
            highlightColor={highlightColor}
            onColorChange={onSetHighlightColor}
            onSave={async () => {
              const ok = await onSaveHighlight(selectedText, highlightColor)
              if (ok) onCancelSelection()
            }}
            onCancel={onCancelSelection}
          />
        </PortalForm>
      )}

      {/* Annotation Form */}
      {showAnnotationForm && selectionCoords && (
        <PortalForm visible={showAnnotationForm}>
          <AnnotationForm
            selectedText={selectedText}
            snippetCategory={snippetCategory}
            annotation={annotation}
            onCategoryChange={onSetSnippetCategory}
            onAnnotationChange={onSetAnnotation}
            onSave={async () => {
              const ok = await onSaveAnnotation(selectedText, snippetCategory, annotation)
              if (ok) onCancelSelection()
            }}
            onCancel={onCancelSelection}
          />
        </PortalForm>
      )}

      {/* Tag/Concept Creation Form */}
      {showTagCreation && selectionCoords && (
        <PortalForm visible={showTagCreation}>
          <TagCreationForm
            selectedText={selectedText}
            tagEditText={tagEditText}
            tagError={tagError}
            onTagEditTextChange={onSetTagEditText}
            onSave={async () => {
              const result = await onSaveTag(tagEditText)
              if (result.success) {
                onCancelSelection()
              } else if (result.error) {
                onSetTagError(result.error)
                setTimeout(() => onSetTagError(''), 5000)
              }
            }}
            onCancel={onCancelSelection}
          />
        </PortalForm>
      )}
    </>
  )
}

// ---------- Internal sub-components ----------

/** Wrapper that creates a portal container and renders children inside it. */
function PortalForm({ visible, children }: { visible: boolean; children: React.ReactNode }) {
  const containerRef = React.useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const el = document.createElement('div')
    el.style.position = 'fixed'
    el.style.top = '0'
    el.style.left = '0'
    el.style.right = '0'
    el.style.bottom = '0'
    el.style.zIndex = '2147483647'
    el.style.pointerEvents = 'none'
    document.body.appendChild(el)
    containerRef.current = el
    return () => {
      if (document.body.contains(el)) {
        document.body.removeChild(el)
      }
    }
  }, [])

  if (!containerRef.current || !visible) return null
  return ReactDOM.createPortal(children, containerRef.current)
}

function ContextMenuContent({
  coords,
  isInteractingWithMenu,
  onHighlight,
  onSnippet,
  onConcept,
  onCancel,
}: {
  coords: { x: number; y: number }
  isInteractingWithMenu: React.MutableRefObject<boolean>
  onHighlight: () => void
  onSnippet: () => void
  onConcept: () => void
  onCancel: () => void
}) {
  // Ensure flag is set
  isInteractingWithMenu.current = true

  const stopEvent = (e: React.MouseEvent) => { e.stopPropagation(); e.preventDefault() }
  const btnStyle: React.CSSProperties = {
    width: '100%', padding: '8px 12px', textAlign: 'left',
    display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px',
    border: 'none', background: 'transparent', cursor: 'pointer',
  }

  return (
    <div
      className="context-menu"
      style={{
        position: 'fixed', left: `${coords.x - 100}px`, top: `${coords.y}px`,
        width: '200px', backgroundColor: 'white', border: '2px solid black',
        borderRadius: '8px', boxShadow: '0 4px 6px rgba(0,0,0,0.3)', padding: '8px',
        zIndex: 2147483647, pointerEvents: 'auto', display: 'block',
        visibility: 'visible', opacity: 1,
      }}
      onClick={stopEvent}
      onMouseDown={stopEvent}
      onMouseUp={stopEvent}
    >
      <button
        onMouseDown={stopEvent}
        onClick={(e) => { stopEvent(e); onHighlight() }}
        style={btnStyle}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        <Palette className="h-4 w-4" /> Highlighting
      </button>
      <button
        onMouseDown={stopEvent}
        onClick={(e) => { stopEvent(e); onSnippet() }}
        style={btnStyle}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        <StickyNote className="h-4 w-4" /> Create Snippet
      </button>
      <div style={{ height: '1px', backgroundColor: '#e5e7eb', margin: '4px 0' }} />
      <button
        onMouseDown={stopEvent}
        onClick={(e) => { stopEvent(e); onConcept() }}
        style={btnStyle}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        <span>{'\uD83C\uDFF7\uFE0F'}</span><span>Concept Creation</span>
      </button>
      <div style={{ height: '1px', backgroundColor: '#e5e7eb', margin: '4px 0' }} />
      <button
        onMouseDown={stopEvent}
        onClick={(e) => { stopEvent(e); onCancel() }}
        style={btnStyle}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#f3f4f6'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        <X className="h-4 w-4" /> Cancel
      </button>
    </div>
  )
}

function HighlightForm({
  selectedText,
  highlightColor,
  onColorChange,
  onSave,
  onCancel,
}: {
  selectedText: string
  highlightColor: string
  onColorChange: (c: string) => void
  onSave: () => void
  onCancel: () => void
}) {
  const stopEvent = (e: React.MouseEvent) => { e.stopPropagation(); e.preventDefault() }
  const colors = [
    { value: 'yellow', emoji: '\uD83D\uDFE1' },
    { value: 'green', emoji: '\uD83D\uDFE2' },
    { value: 'blue', emoji: '\uD83D\uDD35' },
    { value: 'pink', emoji: '\uD83E\uDE77' },
  ]

  return (
    <div className="fixed w-80 highlight-form" style={{
      left: '50%', top: '30%', transform: 'translateX(-50%)',
      backgroundColor: 'white', border: '1px solid #e5e7eb', borderRadius: '8px',
      boxShadow: '0 10px 40px rgba(0,0,0,0.3)', pointerEvents: 'auto',
    }}>
      <div className="p-4 border-b">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold">{'\uD83C\uDFA8'} Highlighting</h3>
          <button type="button" onMouseUp={(e) => { stopEvent(e); onCancel() }}
            className="h-6 w-6 rounded hover:bg-gray-100 flex items-center justify-center" style={{ cursor: 'pointer' }}>
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
      <div className="p-4 space-y-3">
        <div className="text-sm text-muted-foreground">
          &ldquo;{selectedText.substring(0, 100)}{selectedText.length > 100 ? '...' : ''}&rdquo;
        </div>
        <div>
          <Label className="text-sm">Choose highlight color:</Label>
          <div className="flex gap-2 mt-2">
            {colors.map(color => (
              <button key={color.value} type="button"
                onMouseUp={(e) => { stopEvent(e); onColorChange(color.value) }}
                className={`flex-1 px-3 py-2 rounded-md border ${
                  highlightColor === color.value
                    ? 'bg-blue-600 text-white border-blue-600'
                    : 'bg-white border-gray-300 hover:bg-gray-50'
                }`} style={{ cursor: 'pointer' }}>
                {color.emoji}
              </button>
            ))}
          </div>
        </div>
        <div className="flex gap-2">
          <button type="button" onMouseUp={(e) => { stopEvent(e); onCancel() }}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50" style={{ cursor: 'pointer' }}>
            Cancel
          </button>
          <button type="button" onMouseUp={(e) => { stopEvent(e); onSave() }}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700" style={{ cursor: 'pointer' }}>
            Mark in {highlightColor.charAt(0).toUpperCase() + highlightColor.slice(1)}
          </button>
        </div>
      </div>
    </div>
  )
}

export default AnnotatorPortals
