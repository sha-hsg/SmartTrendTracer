import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeRaw from 'rehype-raw'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Separator } from "@/components/ui/separator"
import ModelBadge from '../llm/ModelBadge'
import { useArticleViewer } from './useArticleViewer'
import {
  X,
  Save,
  User,
  Plus,
} from 'lucide-react'

export function AuthorEditor({ viewer, article }: { viewer: ReturnType<typeof useArticleViewer>; article: NonNullable<ReturnType<typeof useArticleViewer>['article']> }) {
  return (
    <div className="flex items-center gap-2">
      <User className="h-4 w-4" />
      <div className="relative">
        <Input
          value={viewer.authorInput}
          onChange={(e) => { viewer.setAuthorInput(e.target.value); viewer.setShowAuthorSuggestions(true) }}
          onFocus={() => viewer.setShowAuthorSuggestions(true)}
          onKeyPress={(e) => { if (e.key === 'Enter') viewer.saveEditedAuthor() }}
          placeholder="Type author name or select..."
          className="h-8 w-48"
        />
        {viewer.showAuthorSuggestions && viewer.filteredAuthors.length > 0 && viewer.authorInput && (
          <div className="absolute top-full mt-1 w-full bg-background border rounded-md shadow-md z-50 max-h-48 overflow-y-auto">
            {viewer.filteredAuthors.map(author => (
              <button key={author.id}
                className="w-full px-3 py-2 text-left hover:bg-muted transition-colors text-sm"
                onClick={() => {
                  viewer.setAuthorInput(author.name)
                  viewer.setSelectedAuthorId(author.id)
                  viewer.setShowAuthorSuggestions(false)
                }}>
                {author.name}
              </button>
            ))}
            {!viewer.filteredAuthors.find(a => a.name.toLowerCase() === viewer.authorInput.toLowerCase()) && viewer.authorInput.trim() && (
              <div className="px-3 py-2 text-sm text-muted-foreground border-t">
                <span className="text-xs">Press Enter to create:</span>
                <div className="font-medium">{viewer.authorInput}</div>
              </div>
            )}
          </div>
        )}
      </div>
      <Button size="sm" variant="ghost" onClick={viewer.saveEditedAuthor}
        disabled={viewer.savingEdits} className="h-8 px-2"
        title={viewer.filteredAuthors.find(a => a.name.toLowerCase() === viewer.authorInput.toLowerCase()) ? "Use existing author" : "Create new author"}>
        <Save className="h-3 w-3" />
      </Button>
      <Button size="sm" variant="ghost"
        onClick={() => {
          viewer.setIsEditingAuthor(false)
          viewer.setAuthorInput('')
          viewer.setShowAuthorSuggestions(false)
          viewer.setSelectedAuthorId(article.author?.id || null)
        }} className="h-8 px-2">
        <X className="h-3 w-3" />
      </Button>
    </div>
  )
}

export function SummaryCard({
  article,
  summaryModel,
  keyPoints,
  selectedSummaryText,
  setSelectedSummaryText,
  onAddConcept,
}: {
  article: NonNullable<ReturnType<typeof useArticleViewer>['article']>
  summaryModel: string
  keyPoints: string[]
  selectedSummaryText: string
  setSelectedSummaryText: (v: string) => void
  onAddConcept: (text: string) => void
}) {
  return (
    <Card className="mb-6">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">AI Summary</CardTitle>
          {summaryModel && <ModelBadge model={summaryModel} size="medium" />}
        </div>
      </CardHeader>
      <CardContent>
        <div
          className="relative p-4 rounded-lg"
          style={{
            background: 'linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #f0f9ff 100%)',
            border: '1px solid #bfdbfe',
            boxShadow: 'inset 0 1px 3px rgba(147, 197, 253, 0.2)'
          }}
          onMouseUp={() => {
            const selection = window.getSelection()
            const text = selection?.toString().trim()
            if (text && text.length > 2) setSelectedSummaryText(text)
          }}
        >
          {selectedSummaryText && (
            <div className="absolute top-2 right-2 z-10">
              <Button size="sm" variant="secondary"
                onClick={async (e) => {
                  e.stopPropagation()
                  if (!selectedSummaryText) return
                  onAddConcept(selectedSummaryText)
                }}
                className="text-xs shadow-md">
                <Plus className="h-3 w-3 mr-1" />Create Concept
              </Button>
            </div>
          )}
          <div className="prose prose-sm max-w-none prose-headings:text-gray-900 prose-h1:text-xl prose-h2:text-lg prose-h3:text-base prose-strong:text-gray-900 prose-ul:list-disc prose-ol:list-decimal prose-li:text-gray-700 prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic prose-code:bg-gray-100 prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-pre:bg-gray-900 prose-pre:text-gray-100">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeRaw]}
              components={{
                h1: ({children}) => <h1 className="text-xl font-bold mt-4 mb-3 text-gray-900">{children}</h1>,
                h2: ({children}) => <h2 className="text-lg font-semibold mt-3 mb-2 text-gray-800">{children}</h2>,
                h3: ({children}) => <h3 className="text-base font-semibold mt-2 mb-2 text-gray-800">{children}</h3>,
                p: ({ children, ...props }) => {
                  const hasCodeBlock = React.Children.toArray(children).some(
                    child => React.isValidElement(child) && (
                      child.type === 'pre' || child.props?.node?.tagName === 'pre'
                    )
                  )
                  if (hasCodeBlock) return <div className="mb-3" {...props}>{children}</div>
                  return <p className="mb-3 text-gray-700 leading-relaxed" {...props}>{children}</p>
                },
                ul: ({children}) => <ul className="list-disc pl-5 mb-3 space-y-1">{children}</ul>,
                ol: ({children}) => <ol className="list-decimal pl-5 mb-3 space-y-1">{children}</ol>,
                li: ({children}) => <li className="text-gray-700">{children}</li>,
                strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
                em: ({children}) => <em className="italic text-gray-700">{children}</em>,
                blockquote: ({children}) => (
                  <blockquote className="border-l-4 border-blue-500 pl-3 py-1 my-3 italic bg-blue-50 rounded-r">{children}</blockquote>
                ),
                code: ({children, className}) => {
                  const isInline = !className?.includes('language-')
                  if (isInline) return <code className="bg-gray-100 px-1 py-0.5 rounded text-sm font-mono text-gray-800">{children}</code>
                  return (
                    <pre className="bg-gray-900 text-gray-100 p-3 rounded-lg overflow-x-auto mb-3">
                      <code className="text-sm font-mono">{children}</code>
                    </pre>
                  )
                },
                hr: () => <hr className="my-3 border-gray-300" />,
                a: ({href, children}) => (
                  <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">{children}</a>
                ),
                table: ({children}) => (
                  <div className="overflow-x-auto mb-3"><table className="min-w-full border border-gray-300 text-sm">{children}</table></div>
                ),
                th: ({children}) => <th className="border border-gray-300 px-3 py-1.5 bg-gray-100 font-semibold text-left">{children}</th>,
                td: ({children}) => <td className="border border-gray-300 px-3 py-1.5">{children}</td>,
              }}
            >
              {article.summary?.replace(/<think>/gi, '').replace(/<\/think>/gi, '').replace(/<think[^>]*>/gi, '')}
            </ReactMarkdown>
          </div>
        </div>
        {keyPoints.length > 0 && (
          <>
            <Separator className="my-4" />
            <div>
              <h4 className="font-semibold mb-2">{'\uD83D\uDCCC'} Key Points:</h4>
              <ul className="space-y-2">
                {keyPoints.map((point, index) => (
                  <li key={index} className="text-sm flex items-start">
                    <span className="mr-2 mt-1">{'\u2022'}</span>
                    <div className="prose prose-sm max-w-none flex-1">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}
                        components={{
                          p: ({ children }) => <span>{children}</span>,
                          strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                          em: ({ children }) => <em className="italic">{children}</em>,
                          code: ({ children }) => <code className="bg-muted px-1 py-0.5 rounded text-xs">{children}</code>,
                          a: ({ href, children }) => (
                            <a href={href} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">{children}</a>
                          )
                        }}>
                        {point}
                      </ReactMarkdown>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
