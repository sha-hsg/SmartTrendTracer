import { useState } from 'react'
import { BookOpenCheck, Loader2, Search } from 'lucide-react'
import http, { apiErrorMessage } from '@/services/http'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Checkbox } from '@/components/ui/checkbox'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import PaperQAPanel from './PaperQAPanel'

interface ScopePaper { id: string; title: string; has_text: boolean }

export default function PaperQA() {
  const [concept, setConcept] = useState('')
  const [papers, setPapers] = useState<ScopePaper[] | null>(null)
  const [selected, setSelected] = useState<Set<string>>(new Set())
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const loadScope = async () => {
    if (!concept.trim()) return
    setLoading(true)
    setError(null)
    try {
      const { data } = await http.post<{ papers: ScopePaper[] }>('/api/papers/qa/scope', { concept: concept.trim() })
      setPapers(data.papers)
      setSelected(new Set(data.papers.filter(p => p.has_text).map(p => p.id)))
    } catch (err) {
      setError(apiErrorMessage(err, 'Could not load papers'))
    } finally {
      setLoading(false)
    }
  }

  const toggle = (id: string) => {
    const next = new Set(selected)
    if (next.has(id)) { next.delete(id) } else { next.add(id) }
    setSelected(next)
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
          <BookOpenCheck className="w-7 h-7" /> Paper Q&amp;A
        </h1>
        <p className="text-gray-600">
          Ask questions across a set of papers — answers cite the exact sections they come from.
          For a single paper, use the "Ask" tab in the paper viewer.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[340px_1fr]">
        <Card className="h-fit">
          <CardHeader>
            <CardTitle className="text-base">Papers</CardTitle>
            <CardDescription>All papers tagged with a concept, e.g. "Hybrid AI Course"</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex gap-2">
              <Input value={concept} onChange={e => setConcept(e.target.value)}
                     onKeyDown={e => { if (e.key === 'Enter') loadScope() }}
                     placeholder="Concept" aria-label="Concept" />
              <Button variant="outline" onClick={loadScope} disabled={loading || !concept.trim()} aria-label="Load papers">
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              </Button>
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            {papers && papers.length === 0 && (
              <p className="text-sm text-muted-foreground">No papers are tagged with this concept.</p>
            )}
            {papers && papers.length > 0 && (
              <div className="space-y-2 max-h-[60vh] overflow-y-auto">
                {papers.map(p => (
                  <label key={p.id} className={`flex items-start gap-2 text-sm ${p.has_text ? '' : 'opacity-50'}`}>
                    <Checkbox checked={selected.has(p.id)} disabled={!p.has_text}
                              onCheckedChange={() => toggle(p.id)} className="mt-0.5" />
                    <span>{p.title}{!p.has_text && ' (no full text yet)'}</span>
                  </label>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <PaperQAPanel
              paperIds={[...selected]}
              disabledReason={selected.size === 0 ? 'Choose papers on the left first.' : undefined}
            />
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
