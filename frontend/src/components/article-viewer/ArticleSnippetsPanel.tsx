/**
 * ArticleSnippetsPanel - Displays and manages saved snippets for an article.
 *
 * Shows categorized snippets (insights, questions, highlights, etc.)
 * with delete capability.
 */
import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { StickyNote, Trash2 } from 'lucide-react'
import type { FullArticle } from './useArticleViewer'

interface ArticleSnippetsPanelProps {
  snippets: FullArticle['snippets']
  onDeleteSnippet: (snippetId: number) => void
}

const CATEGORY_LABELS: Record<string, string> = {
  insight: '\uD83D\uDCA1 Insight',
  question: '\u2753 Question',
  critique: '\uD83E\uDD14 Critique',
  todo: '\u2705 Todo',
  quote: '\uD83D\uDCAC Quote',
  yellow: '\uD83D\uDFE1 Highlight',
  green: '\uD83D\uDFE2 Highlight',
  blue: '\uD83D\uDD35 Highlight',
  pink: '\uD83E\uDE77 Highlight',
}

function ArticleSnippetsPanel({ snippets, onDeleteSnippet }: ArticleSnippetsPanelProps) {
  if (!snippets || snippets.length === 0) return null

  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <StickyNote className="h-5 w-5" />
            Saved Snippets
            <Badge variant="secondary">{snippets.length}</Badge>
          </CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {snippets.map((snippet, index) => (
            <div key={snippet.id || index} className="border rounded-lg p-3 hover:bg-gray-50">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <Badge variant="outline" className="text-xs">
                      {CATEGORY_LABELS[snippet.category || ''] || '\uD83D\uDCDD Note'}
                    </Badge>
                    {snippet.importance && (
                      <Badge variant="outline" className="text-xs">
                        Importance: {snippet.importance}/10
                      </Badge>
                    )}
                  </div>
                  <div className="text-sm font-medium bg-gray-100 p-2 rounded mb-2">
                    &ldquo;{snippet.text}&rdquo;
                  </div>
                  {snippet.annotation && (
                    <div className="text-sm text-gray-600 italic">
                      {'\uD83D\uDCDD'} {snippet.annotation}
                    </div>
                  )}
                </div>
                <button
                  onClick={() => onDeleteSnippet(snippet.id)}
                  className="p-1 hover:bg-red-100 rounded"
                  title="Delete snippet"
                >
                  <Trash2 className="h-4 w-4 text-red-600" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default React.memo(ArticleSnippetsPanel)
