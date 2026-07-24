import ReactDOM from 'react-dom'
import {
  Loader2,
  Copy,
  Highlighter,
  MessageSquare,
  Tag as TagIcon,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'


interface AnalysisContextMenuProps {
  showContextMenu: boolean
  contextMenuPosition: { x: number; y: number }
  onMenuAction: (action: string) => void
}

export function AnalysisContextMenu({
  showContextMenu,
  contextMenuPosition,
  onMenuAction,
}: AnalysisContextMenuProps) {
  if (!showContextMenu) return null

  return ReactDOM.createPortal(
    <div
      className="fixed z-[9999] bg-white rounded-lg shadow-2xl border border-gray-200 py-1 min-w-[180px]"
      style={{
        left: `${contextMenuPosition.x}px`,
        top: `${contextMenuPosition.y}px`,
      }}
      onMouseDown={(e) => e.stopPropagation()}
    >
      <button
        className="w-full px-4 py-2 text-left text-sm hover:bg-blue-50 flex items-center gap-2 transition-colors"
        onClick={() => onMenuAction('copy')}
      >
        <Copy className="h-4 w-4 text-blue-600" />
        <span>Copy Text</span>
      </button>

      <div className="border-t border-gray-100 my-1" />

      <button
        className="w-full px-4 py-2 text-left text-sm hover:bg-green-50 flex items-center gap-2 transition-colors"
        onClick={() => onMenuAction('snippet')}
      >
        <MessageSquare className="h-4 w-4 text-green-600" />
        <span>Create Snippet</span>
      </button>

      <button
        className="w-full px-4 py-2 text-left text-sm hover:bg-yellow-50 flex items-center gap-2 transition-colors"
        onClick={() => onMenuAction('highlight')}
      >
        <Highlighter className="h-4 w-4 text-yellow-600" />
        <span>Highlight</span>
      </button>

      <button
        className="w-full px-4 py-2 text-left text-sm hover:bg-purple-50 flex items-center gap-2 transition-colors"
        onClick={() => onMenuAction('tag')}
      >
        <TagIcon className="h-4 w-4 text-purple-600" />
        <span>Create Tag</span>
      </button>
    </div>,
    document.body
  )
}


interface TagCreationDialogProps {
  open: boolean
  tagText: string
  creatingTag: boolean
  onTagTextChange: (text: string) => void
  onCreateTag: () => void
  onClose: () => void
}

export function TagCreationDialog({
  open,
  tagText,
  creatingTag,
  onTagTextChange,
  onCreateTag,
  onClose,
}: TagCreationDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <TagIcon className="h-5 w-5 text-purple-600" />
            Create Tag from Analysis
          </DialogTitle>
          <DialogDescription>
            Edit the selected text and create a tag for this paper.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div>
            <label htmlFor="analysisTagText" className="block text-sm font-medium text-gray-700 mb-2">
              Tag Text
            </label>
            <Input
              id="analysisTagText"
              value={tagText}
              onChange={(e) => onTagTextChange(e.target.value)}
              placeholder="Enter tag text..."
              className="w-full"
              onKeyPress={(e) => {
                if (e.key === 'Enter' && !creatingTag) {
                  onCreateTag()
                }
              }}
              disabled={creatingTag}
            />
          </div>
          <div className="flex justify-end gap-2">
            <Button
              variant="outline"
              onClick={onClose}
              disabled={creatingTag}
            >
              Cancel
            </Button>
            <Button
              onClick={onCreateTag}
              disabled={!tagText.trim() || creatingTag}
              className="bg-purple-600 hover:bg-purple-700"
            >
              {creatingTag ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Tag'
              )}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
