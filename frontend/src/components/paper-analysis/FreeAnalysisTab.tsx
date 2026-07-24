import {
  Loader2,
  Copy,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Edit2,
  MessageSquare,
  Trash2,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { extractTextContent, getRelativeTime } from './constants'


interface FreeAnalysisTabProps {
  freeAnalyses: any[]
  currentPrompt: string
  loadingFreeAnalysis: boolean
  expandedFreeAnalyses: Set<string>
  editingFreeAnalysis: string | null
  editedFreeContent: Record<string, string>
  onSetCurrentPrompt: (prompt: string) => void
  onSetExpandedFreeAnalyses: React.Dispatch<React.SetStateAction<Set<string>>>
  onSetEditingFreeAnalysis: (id: string | null) => void
  onSetEditedFreeContent: React.Dispatch<React.SetStateAction<Record<string, string>>>
  onSubmitFreeAnalysis: () => void
  onDeleteFreeAnalysis: (id: string) => void
  onSaveFreeAnalysisEdit: (id: string) => void
}

export function FreeAnalysisTab({
  freeAnalyses,
  currentPrompt,
  loadingFreeAnalysis,
  expandedFreeAnalyses,
  editingFreeAnalysis,
  editedFreeContent,
  onSetCurrentPrompt,
  onSetExpandedFreeAnalyses,
  onSetEditingFreeAnalysis,
  onSetEditedFreeContent,
  onSubmitFreeAnalysis,
  onDeleteFreeAnalysis,
  onSaveFreeAnalysisEdit,
}: FreeAnalysisTabProps) {
  return (
    <div className="flex flex-col h-full">
      {/* Compact Input Section */}
      <div className="flex gap-3 mb-3">
        <textarea
          value={currentPrompt}
          onChange={(e) => onSetCurrentPrompt(e.target.value)}
          placeholder="Ask a question about this paper..."
          className="flex-1 h-20 p-3 border border-purple-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 bg-purple-50"
          disabled={loadingFreeAnalysis}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && e.metaKey && !loadingFreeAnalysis && currentPrompt.trim()) {
              onSubmitFreeAnalysis()
            }
          }}
        />
        <Button
          onClick={onSubmitFreeAnalysis}
          disabled={loadingFreeAnalysis || !currentPrompt.trim()}
          className="px-6 bg-purple-600 hover:bg-purple-700 text-white self-end"
          title="Generate Analysis (Cmd+Enter)"
        >
          {loadingFreeAnalysis ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <Sparkles className="h-5 w-5" />
          )}
        </Button>
      </div>

      {/* Q&A List - adjusted height calculation */}
      <div className="flex-1 overflow-auto" style={{maxHeight: 'calc(70vh - 250px)'}}>
        <div className="space-y-3">
          {freeAnalyses.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <MessageSquare className="h-12 w-12 mx-auto mb-3 text-gray-300" />
              <p>No analyses yet.</p>
              <p className="text-sm mt-1">Ask a question above to get started!</p>
            </div>
          ) : (
            // Sort analyses to show newest first (by created_at)
            [...freeAnalyses]
              .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
              .map((analysis, _index) => {
                const isExpanded = expandedFreeAnalyses.has(analysis.id)
                const isEditing = editingFreeAnalysis === analysis.id
                const analysisDate = new Date(analysis.created_at)
                const timeAgo = getRelativeTime(analysisDate)

                return (
                  <Card key={analysis.id} className="border-l-4 border-l-purple-500">
                    <CardHeader className="py-3 cursor-pointer" onClick={() => {
                      onSetExpandedFreeAnalyses(prev => {
                        const next = new Set(prev)
                        if (next.has(analysis.id)) {
                          next.delete(analysis.id)
                        } else {
                          next.add(analysis.id)
                        }
                        return next
                      })
                    }}>
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            {isExpanded ? (
                              <ChevronDown className="h-4 w-4 text-purple-600" />
                            ) : (
                              <ChevronRight className="h-4 w-4 text-purple-600" />
                            )}
                            <span className="text-xs font-medium text-purple-600 uppercase">Question</span>
                            <span className="text-xs text-gray-500">{timeAgo}</span>
                          </div>
                          <p className="text-sm font-medium text-gray-900 mt-1 ml-6">
                            {analysis.prompt}
                          </p>
                        </div>
                        <div className="flex items-center space-x-1 ml-4" onClick={(e) => e.stopPropagation()}>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => navigator.clipboard.writeText(`Q: ${analysis.prompt}\n\nA: ${analysis.content}`)}
                            title="Copy Q&A"
                            className="p-1"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                          {!isEditing && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                onSetEditingFreeAnalysis(analysis.id)
                                onSetEditedFreeContent(prev => ({
                                  ...prev,
                                  [analysis.id]: analysis.content
                                }))
                              }}
                              title="Edit answer"
                              className="p-1"
                            >
                              <Edit2 className="h-3 w-3" />
                            </Button>
                          )}
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => onDeleteFreeAnalysis(analysis.id)}
                            title="Delete"
                            className="p-1 text-red-600 hover:text-red-700"
                          >
                            <Trash2 className="h-3 w-3" />
                          </Button>
                        </div>
                      </div>
                    </CardHeader>

                    {/* Answer - Only show when expanded */}
                    {isExpanded && (
                      <CardContent className="pt-0 pb-4">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-xs font-medium text-green-600 uppercase">Answer</span>
                          <span className="text-xs text-gray-500">{analysis.model || 'Gemini 2.5 Pro'}</span>
                        </div>
                        {isEditing ? (
                          <div className="space-y-2">
                            <textarea
                              value={editedFreeContent[analysis.id] || ''}
                              onChange={(e) => onSetEditedFreeContent(prev => ({
                                ...prev,
                                [analysis.id]: e.target.value
                              }))}
                              className="w-full h-40 p-3 text-sm border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500"
                            />
                            <div className="flex justify-end space-x-2">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  onSetEditingFreeAnalysis(null)
                                  onSetEditedFreeContent(prev => {
                                    const updated = { ...prev }
                                    delete updated[analysis.id]
                                    return updated
                                  })
                                }}
                              >
                                Cancel
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => onSaveFreeAnalysisEdit(analysis.id)}
                                className="bg-purple-600 hover:bg-purple-700 text-white"
                              >
                                Save
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="prose prose-sm max-w-none text-gray-700">
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>
                              {extractTextContent(analysis.content)}
                            </ReactMarkdown>
                          </div>
                        )}
                      </CardContent>
                    )}
                  </Card>
                )
              })
          )}
        </div>
      </div>
    </div>
  )
}
