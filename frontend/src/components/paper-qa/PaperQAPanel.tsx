import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Loader2, MessageSquareText, Send } from 'lucide-react'
import http, { apiErrorMessage } from '@/services/http'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Badge } from '@/components/ui/badge'

interface QASource {
  n: number
  paper_id: string
  title: string
  section: string
  excerpt: string
  score: number
}

interface QAResponse {
  question: string
  answer: string
  papers: { id: string; title: string }[]
  sources: QASource[]
}

interface PaperQAPanelProps {
  /** Papers to ask; combined with `concept` when both are given */
  paperIds?: string[]
  concept?: string
  /** Hide the paper title in source cards (single-paper mode) */
  singlePaper?: boolean
  disabledReason?: string
}

/** Turn "[2]" / "[1][3]" / "[6, 7]" into links to the source cards below. */
function linkCitations(answer: string) {
  return answer.replace(/\[(\d+(?:\s*,\s*\d+)*)\]/g, (_, nums: string) =>
    nums.split(',').map(n => `[${n.trim()}](#qa-source-${n.trim()})`).join(''))
}

export default function PaperQAPanel({ paperIds, concept, singlePaper, disabledReason }: PaperQAPanelProps) {
  const [question, setQuestion] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<QAResponse | null>(null)

  const ask = async () => {
    if (!question.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const { data } = await http.post<QAResponse>('/api/papers/qa', {
        question: question.trim(),
        paper_ids: paperIds,
        concept: concept || undefined,
      })
      setResult(data)
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not answer the question'))
    } finally {
      setLoading(false)
    }
  }

  const scrollToSource = (n: string) => {
    document.getElementById(`qa-source-${n}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Textarea
          value={question}
          onChange={e => setQuestion(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask() } }}
          placeholder={singlePaper ? 'Ask a question about this paper…' : 'Ask a question across the selected papers…'}
          className="min-h-[72px]"
          disabled={!!disabledReason}
          aria-label="Question"
        />
        <Button onClick={ask} disabled={loading || !question.trim() || !!disabledReason} className="self-end">
          {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Send className="w-4 h-4 mr-2" />}
          Ask
        </Button>
      </div>
      {disabledReason && <p className="text-sm text-muted-foreground">{disabledReason}</p>}
      {loading && !result && (
        <p className="text-sm text-muted-foreground">
          The first question on a paper reads its full text once; this can take up to a minute.
        </p>
      )}
      {error && <p className="text-sm text-red-600">{error}</p>}

      {result && (
        <div className="space-y-4">
          <div className="rounded-lg border p-4">
            <div className="flex items-center gap-2 mb-2 text-sm text-muted-foreground">
              <MessageSquareText className="w-4 h-4" /> {result.question}
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => href?.startsWith('#qa-source-') ? (
                    <button
                      type="button"
                      onClick={() => scrollToSource(href.replace('#qa-source-', ''))}
                      className="no-underline align-super text-xs font-medium text-primary hover:underline px-0.5"
                    >
                      [{children}]
                    </button>
                  ) : <a href={href} target="_blank" rel="noreferrer">{children}</a>,
                }}
              >
                {linkCitations(result.answer)}
              </ReactMarkdown>
            </div>
            {!singlePaper && (
              <p className="mt-3 text-xs text-muted-foreground">Searched {result.papers.length} paper(s)</p>
            )}
          </div>

          <div className="space-y-2">
            <h4 className="text-sm font-medium">Sources</h4>
            {result.sources.map(s => (
              <div key={s.n} id={`qa-source-${s.n}`} className="rounded-md border p-3 text-sm scroll-mt-24">
                <div className="flex items-start gap-2 mb-1">
                  <Badge variant="secondary" className="shrink-0">{s.n}</Badge>
                  <div className="min-w-0">
                    {!singlePaper && <div className="font-medium truncate">{s.title}</div>}
                    <div className="text-muted-foreground">{s.section}</div>
                  </div>
                </div>
                <p className="text-muted-foreground line-clamp-4 whitespace-pre-line">{s.excerpt}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
