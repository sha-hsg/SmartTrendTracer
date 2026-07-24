import React from 'react'
import {
  Loader2,
  Download,
  Copy,
  CheckCircle,
  ChevronDown,
  ChevronRight,
  Sparkles,
  RefreshCw,
  Edit2,
  Save,
  X,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Textarea } from '@/components/ui/textarea'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { extractTextContent, analysisTypeColors, categoryIcons } from './constants'
import type { AnalysisType, GeneratedAnalysis } from './constants'

export interface AnalysisCardProps {
  analysis: AnalysisType
  isLoading: boolean
  isGenerated: boolean
  isExpanded: boolean
  result: GeneratedAnalysis | undefined
  hasContent: boolean
  editingAnalysis: string | null
  editedContent: Record<string, string>
  copiedAnalysis: string | null
  onToggleExpansion: (id: string) => void
  onStartEditing: (id: string, content: string) => void
  onSaveEditing: (id: string) => void
  onCancelEditing: (id: string) => void
  onSetEditedContent: (fn: (prev: Record<string, string>) => Record<string, string>) => void
  onCopy: (id: string, content: string) => void
  onDownload: (id: string, content: string) => void
  onGenerate: (id: string, regenerate?: boolean) => void
  onContextMenu: (e: React.MouseEvent) => void
}

const MARKDOWN_STYLES = `
.markdown-content h1 { font-size: 1.875rem; font-weight: 700; margin-top: 1.5rem; margin-bottom: 1rem; color: rgb(15 23 42); border-bottom: 2px solid rgba(0, 0, 0, 0.15); padding-bottom: 0.5rem; }
.markdown-content h2 { font-size: 1.5rem; font-weight: 700; margin-top: 1.25rem; margin-bottom: 0.75rem; color: rgb(15 23 42); }
.markdown-content h3 { font-size: 1.25rem; font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem; color: rgb(30 41 59); }
.markdown-content h4 { font-size: 1.125rem; font-weight: 600; margin-top: 0.75rem; margin-bottom: 0.5rem; color: rgb(30 41 59); }
.markdown-content p { margin-bottom: 1rem; color: rgb(30 41 59); line-height: 1.8; font-size: 1rem; }
.markdown-content ul { list-style-type: disc; margin-bottom: 1rem; padding-left: 1.5rem; }
.markdown-content ol { list-style-type: decimal; margin-bottom: 1rem; padding-left: 1.5rem; }
.markdown-content li { margin-bottom: 0.375rem; color: rgb(30 41 59); line-height: 1.7; }
.markdown-content ul ul, .markdown-content ol ul { margin-top: 0.25rem; margin-bottom: 0.25rem; padding-left: 1.5rem; }
.markdown-content ul ol, .markdown-content ol ol { margin-top: 0.25rem; margin-bottom: 0.25rem; padding-left: 1.5rem; }
.markdown-content strong { font-weight: 700; color: rgb(15 23 42); }
.markdown-content em { font-style: italic; }
.markdown-content code { background-color: rgba(255, 255, 255, 0.8); color: rgb(220 38 38); padding: 0.125rem 0.375rem; border-radius: 0.25rem; font-family: 'Courier New', monospace; font-size: 0.9rem; font-weight: 500; }
.markdown-content pre { background-color: rgba(255, 255, 255, 0.9); padding: 1rem; border-radius: 0.5rem; overflow-x: auto; margin-bottom: 1rem; border: 1px solid rgba(0, 0, 0, 0.1); }
.markdown-content pre code { background-color: transparent; color: rgb(30 41 59); padding: 0; font-size: 0.875rem; }
.markdown-content blockquote { border-left: 4px solid currentColor; opacity: 0.85; padding: 0.75rem 1rem; margin-bottom: 1rem; font-style: italic; color: rgb(51 65 85); background-color: rgba(255, 255, 255, 0.3); border-radius: 0.25rem; }
.markdown-content a { color: rgb(29 78 216); text-decoration: underline; font-weight: 500; }
.markdown-content a:hover { color: rgb(30 58 138); text-decoration-thickness: 2px; }
.markdown-content hr { margin: 1.5rem 0; border-color: rgba(0, 0, 0, 0.1); border-style: solid; }
.markdown-content table { width: 100%; border-collapse: collapse; margin-bottom: 1rem; background-color: rgba(255, 255, 255, 0.7); }
.markdown-content th { border: 1px solid rgba(0, 0, 0, 0.1); padding: 0.75rem; background-color: rgba(255, 255, 255, 0.9); font-weight: 600; text-align: left; color: rgb(15 23 42); }
.markdown-content td { border: 1px solid rgba(0, 0, 0, 0.1); padding: 0.75rem; color: rgb(30 41 59); }
`

function getBackgroundColor(bg: string): string {
  if (bg.includes('violet')) return '245, 243, 255'
  if (bg.includes('purple')) return '250, 245, 255'
  if (bg.includes('fuchsia')) return '253, 244, 255'
  if (bg.includes('pink')) return '253, 242, 248'
  if (bg.includes('sky')) return '240, 249, 255'
  if (bg.includes('blue')) return '239, 246, 255'
  if (bg.includes('indigo')) return '238, 242, 255'
  if (bg.includes('cyan')) return '236, 254, 255'
  if (bg.includes('orange')) return '255, 247, 237'
  if (bg.includes('amber')) return '254, 251, 235'
  if (bg.includes('yellow')) return '254, 252, 232'
  if (bg.includes('emerald')) return '236, 253, 245'
  if (bg.includes('green')) return '240, 253, 244'
  if (bg.includes('teal')) return '240, 253, 250'
  return '249, 250, 251'
}

export const AnalysisCard: React.FC<AnalysisCardProps> = ({
  analysis,
  isLoading,
  isGenerated,
  isExpanded,
  result,
  hasContent,
  editingAnalysis,
  editedContent,
  copiedAnalysis,
  onToggleExpansion,
  onStartEditing,
  onSaveEditing,
  onCancelEditing,
  onSetEditedContent,
  onCopy,
  onDownload,
  onGenerate,
  onContextMenu,
}) => {
  const typeColors = analysisTypeColors[analysis.id] || analysisTypeColors.default
  const shouldUseColors = isGenerated && result?.success

  return (
    <Card
      className={`transition-all duration-200 ${
        shouldUseColors ? `${typeColors.bg} ${typeColors.border}` : ''
      } ${!isExpanded && isGenerated ? 'hover:shadow-md' : ''}`}
    >
      <CardHeader className={`pb-3 ${shouldUseColors ? typeColors.header : ''}`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              {categoryIcons[analysis.category]}
              <h3 className="font-semibold">{analysis.name}</h3>
              <Badge variant="outline" className="text-xs">
                {analysis.category}
              </Badge>
            </div>
            <p className="text-sm text-gray-600 mt-1">
              {analysis.description}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {isGenerated && result?.success && (
              <>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onToggleExpansion(analysis.id)}
                >
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </Button>
                {editingAnalysis === analysis.id ? (
                  <>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onSaveEditing(analysis.id)}
                      title="Save"
                    >
                      <Save className="h-4 w-4 text-green-600" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onCancelEditing(analysis.id)}
                      title="Cancel"
                    >
                      <X className="h-4 w-4 text-red-600" />
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onStartEditing(analysis.id, result.content || '')}
                      title="Edit"
                    >
                      <Edit2 className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onCopy(analysis.id, result.content || '')}
                    >
                      {copiedAnalysis === analysis.id ? (
                        <CheckCircle className="h-4 w-4 text-green-600" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => onDownload(analysis.id, result.content || '')}
                    >
                      <Download className="h-4 w-4" />
                    </Button>
                  </>
                )}
              </>
            )}

            {!isGenerated && (
              <Button
                size="sm"
                onClick={() => onGenerate(analysis.id)}
                disabled={isLoading || !hasContent}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Sparkles className="h-4 w-4 mr-1" />
                    Generate
                  </>
                )}
              </Button>
            )}

            {isGenerated && result?.success && (
              <Button
                size="sm"
                variant="ghost"
                onClick={() => onGenerate(analysis.id, true)}
                disabled={isLoading}
                title="Regenerate"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {isGenerated && result?.generated_at && (
          <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
            <span>Generated: {new Date(result.generated_at).toLocaleString()}</span>
            {result.model_used && (
              <span>Model: {result.model_used}</span>
            )}
          </div>
        )}
      </CardHeader>

      {isGenerated && result && isExpanded && (
        <CardContent>
          <Separator className="mb-4" />
          {result.success ? (
            editingAnalysis === analysis.id ? (
              <div className="space-y-4">
                <Textarea
                  value={editedContent[analysis.id] || result.content || ''}
                  onChange={(e) => onSetEditedContent(prev => ({
                    ...prev,
                    [analysis.id]: e.target.value
                  }))}
                  className="min-h-[400px] font-mono text-sm"
                  placeholder="Enter markdown content..."
                />
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <span>Tip: You can use Markdown formatting</span>
                </div>
              </div>
            ) : (
              <div
                className={`markdown-content rounded-lg p-6 ${
                  typeColors.bg.replace('50', '50/30')
                } border ${typeColors.border}`}
                onContextMenu={onContextMenu}
                style={{
                  backgroundColor: `rgba(${getBackgroundColor(typeColors.bg)}, 0.3)`
                }}
              >
                <style>{MARKDOWN_STYLES}</style>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {extractTextContent(result.content)}
                </ReactMarkdown>
              </div>
            )
          ) : (
            <Alert>
              <AlertDescription>
                {result.error || 'Failed to generate analysis'}
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      )}
    </Card>
  )
}
