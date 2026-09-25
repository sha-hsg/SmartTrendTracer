/**
 * ArticleContentRenderer - Renders article markdown content with highlight support.
 *
 * Handles both view mode (ReactMarkdown with snippet highlighting)
 * and edit mode (textarea with save/cancel).
 */
import React, { useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Save, Loader2 } from 'lucide-react'
import type { FullArticle } from './types'

interface ArticleContentRendererProps {
  article: FullArticle
  isEditing: boolean
  editedContent: string
  savingEdits: boolean
  onEditedContentChange: (value: string) => void
  onSave: () => void
  onCancel: () => void
  onContextMenu: (e: React.MouseEvent) => void
  lastSelectionRef: React.MutableRefObject<{ text: string; time: number } | null>
}

/** Apply snippet-highlight markup to paragraph text. */
function highlightSnippets(text: string, snippets: FullArticle['snippets']): string {
  if (!snippets || snippets.length === 0) return text

  let highlightedText = text
  const highlightable = snippets
    .filter(s => s.category && ['yellow', 'green', 'blue', 'pink'].includes(s.category))
    .sort((a, b) => b.text.length - a.text.length)

  highlightable.forEach(snippet => {
    const color = snippet.category === 'yellow' ? '#fff59d' :
                 snippet.category === 'green' ? '#a5d6a7' :
                 snippet.category === 'blue' ? '#90caf9' :
                 snippet.category === 'pink' ? '#f48fb1' : '#ffeb3b'
    const escapedText = snippet.text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`(${escapedText})`, 'gi')
    highlightedText = highlightedText.replace(
      regex,
      `<mark style="background-color: ${color}; padding: 2px 4px; border-radius: 3px; font-weight: 500;">$1</mark>`
    )
  })
  return highlightedText
}

function ArticleContentRenderer({
  article,
  isEditing,
  editedContent,
  savingEdits,
  onEditedContentChange,
  onSave,
  onCancel,
  onContextMenu,
  lastSelectionRef,
}: ArticleContentRendererProps) {

  const captureSelection = useCallback(() => {
    const selection = window.getSelection()
    if (selection && selection.toString().trim() !== '') {
      lastSelectionRef.current = {
        text: selection.toString().trim(),
        time: Date.now()
      }
    }
  }, [lastSelectionRef])

  if (isEditing) {
    return (
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Edit Content</CardTitle>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={onCancel}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={onSave}
                disabled={savingEdits}
              >
                {savingEdits ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Save className="h-4 w-4 mr-2" />
                    Save
                  </>
                )}
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Textarea
            value={editedContent}
            onChange={(e) => onEditedContentChange(e.target.value)}
            className="min-h-[500px] font-mono text-sm"
          />
        </CardContent>
      </Card>
    )
  }

  return (
    <div
      className="prose prose-lg max-w-none"
      onContextMenu={onContextMenu}
      onMouseDown={(e) => {
        if (e.button === 2) {
          e.preventDefault()
        }
      }}
    >
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          p: ({ children, ...props }) => {
            const hasCodeBlock = React.Children.toArray(children).some(
              child => React.isValidElement(child) && (
                child.type === 'pre' ||
                child.props?.node?.tagName === 'pre' ||
                (child.props && child.props.children && React.isValidElement(child.props.children) && child.props.children.type === 'pre')
              )
            )
            if (hasCodeBlock) {
              return <div className="mb-4" {...props}>{children}</div>
            }
            const content = String(children)
            const hasHighlights = article.snippets && article.snippets.length > 0 &&
              article.snippets.some(s =>
                s.category && ['yellow', 'green', 'blue', 'pink'].includes(s.category) &&
                content.toLowerCase().includes(s.text.toLowerCase())
              )
            if (hasHighlights) {
              return (
                <p
                  className="mb-4 leading-relaxed"
                  onContextMenu={onContextMenu}
                  {...props}
                  dangerouslySetInnerHTML={{
                    __html: highlightSnippets(content, article.snippets)
                  }}
                />
              )
            }
            return (
              <p
                className="mb-4 leading-relaxed"
                onContextMenu={onContextMenu}
                onMouseUp={captureSelection}
                {...props}
              >
                {children}
              </p>
            )
          },
          h1: ({node, ...props}) => (
            <h1
              className="text-3xl font-bold mt-8 mb-4"
              onContextMenu={onContextMenu}
              onMouseUp={captureSelection}
              {...props}
            />
          ),
          h2: ({node, ...props}) => (
            <h2
              className="text-2xl font-bold mt-6 mb-3"
              onContextMenu={onContextMenu}
              onMouseUp={captureSelection}
              {...props}
            />
          ),
          h3: ({node, ...props}) => (
            <h3
              className="text-xl font-semibold mt-5 mb-2"
              onContextMenu={onContextMenu}
              onMouseUp={captureSelection}
              {...props}
            />
          ),
          h4: ({node, ...props}) => (
            <h4
              className="text-lg font-semibold mt-4 mb-2"
              onContextMenu={onContextMenu}
              onMouseUp={captureSelection}
              {...props}
            />
          ),
          h5: ({node, ...props}) => (
            <h5 className="text-base font-semibold mt-3 mb-1" {...props} />
          ),
          h6: ({node, ...props}) => (
            <h6 className="text-sm font-semibold mt-3 mb-1" {...props} />
          ),
          ul: ({node, ...props}) => (
            <ul className="list-disc pl-6 mb-4 space-y-1" {...props} />
          ),
          ol: ({node, ...props}) => (
            <ol className="list-decimal pl-6 mb-4 space-y-1" {...props} />
          ),
          li: ({node, ...props}) => (
            <li className="leading-relaxed" onContextMenu={onContextMenu} {...props} />
          ),
          img: ({node, ...props}) => (
            <img
              {...props}
              className="rounded-lg shadow-md my-6 max-w-full h-auto"
              loading="lazy"
            />
          ),
          a: ({node, ...props}) => (
            <a
              {...props}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline font-medium"
            />
          ),
          blockquote: ({node, ...props}) => (
            <blockquote
              {...props}
              className="border-l-4 border-primary/30 pl-4 italic my-6 text-muted-foreground"
            />
          ),
          hr: ({node, ...props}) => (
            <hr className="my-8 border-t border-border" {...props} />
          ),
          table: ({node, ...props}) => (
            <div className="overflow-x-auto my-6">
              <table className="min-w-full divide-y divide-border" {...props} />
            </div>
          ),
          thead: ({node, ...props}) => (
            <thead className="bg-muted/50" {...props} />
          ),
          tbody: ({node, ...props}) => (
            <tbody className="divide-y divide-border" {...props} />
          ),
          tr: ({node, ...props}) => (
            <tr className="hover:bg-muted/30 transition-colors" {...props} />
          ),
          th: ({node, ...props}) => (
            <th className="px-4 py-2 text-left font-semibold" {...props} />
          ),
          td: ({node, ...props}) => (
            <td className="px-4 py-2" {...props} />
          ),
          strong: ({node, ...props}) => (
            <strong className="font-semibold" {...props} />
          ),
          em: ({node, ...props}) => (
            <em className="italic" {...props} />
          ),
          del: ({node, ...props}) => (
            <del className="line-through text-muted-foreground" {...props} />
          ),
          code: ({node, className, children, ...props}: any) => {
            const match = /language-(\w+)/.exec(className || '')
            const isInline = !match && !className?.includes('language-')
            return isInline ? (
              <code
                {...props}
                className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono"
              >
                {children}
              </code>
            ) : (
              <div className="my-4">
                <pre className="bg-muted p-4 rounded-lg overflow-auto">
                  <code className={`font-mono text-sm ${className || ''}`} {...props}>
                    {children}
                  </code>
                </pre>
              </div>
            )
          }
        }}
      >
        {(article.content_markdown || '')
          .replace(/<think>/gi, '')
          .replace(/<\/think>/gi, '')
          .replace(/<think[^>]*>/gi, '')
        }
      </ReactMarkdown>
    </div>
  )
}

export default React.memo(ArticleContentRenderer)
