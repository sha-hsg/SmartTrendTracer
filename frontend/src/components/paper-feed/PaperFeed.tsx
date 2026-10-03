import { useCallback, useEffect, useState } from 'react'
import { toast } from 'sonner'
import {
  Rss, RefreshCw, Loader2, Download, X, ExternalLink, Plus, Trash2, Pause, Play, CheckCircle
} from 'lucide-react'
import http, { apiErrorMessage } from '@/services/http'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface Subscription {
  id: string
  name: string
  query: string
  concept: string | null
  max_results: number
  active: boolean
  last_run?: string
  last_found?: number
}

interface Candidate {
  id: string
  subscription_name: string
  concept: string | null
  arxiv_id: string
  title: string
  authors: string[]
  abstract: string
  published?: string
  url?: string
  score: number | null
  status: 'new' | 'imported' | 'dismissed'
  paper_id?: string
}

function formatDate(value?: string) {
  return value ? new Date(value).toLocaleDateString() : ''
}

function CandidateCard({ c, busy, onImport, onDismiss }: {
  c: Candidate
  busy: boolean
  onImport?: () => void
  onDismiss?: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  return (
    <Card>
      <CardContent className="p-4 space-y-2">
        <div className="flex items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 className="font-medium leading-snug">{c.title}</h3>
            <p className="text-sm text-muted-foreground truncate">
              {c.authors.slice(0, 4).join(', ')}{c.authors.length > 4 ? ' et al.' : ''}
              {c.published ? ` · ${formatDate(c.published)}` : ''} · arXiv {c.arxiv_id}
            </p>
          </div>
          <div className="flex shrink-0 gap-2">
            {onImport && (
              <Button size="sm" onClick={onImport} disabled={busy}>
                {busy ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                Import
              </Button>
            )}
            {onDismiss && (
              <Button size="sm" variant="outline" onClick={onDismiss} disabled={busy} aria-label="Dismiss">
                <X className="w-4 h-4" />
              </Button>
            )}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{c.subscription_name}</Badge>
          {c.score !== null && (
            <Badge variant="outline" title={`Similarity to your papers tagged "${c.concept}"`}>
              Relevance {Math.round(c.score * 100)}%
            </Badge>
          )}
          {c.url && (
            <a href={c.url} target="_blank" rel="noreferrer"
               className="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1">
              arXiv <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
        <p className={`text-sm text-muted-foreground ${expanded ? '' : 'line-clamp-3'}`}>{c.abstract}</p>
        {c.abstract.length > 300 && (
          <button className="text-sm text-primary hover:underline" onClick={() => setExpanded(!expanded)}>
            {expanded ? 'Show less' : 'Show more'}
          </button>
        )}
      </CardContent>
    </Card>
  )
}

export default function PaperFeed() {
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([])
  const [candidates, setCandidates] = useState<Candidate[]>([])
  const [imported, setImported] = useState<Candidate[]>([])
  const [loading, setLoading] = useState(true)
  const [running, setRunning] = useState(false)
  const [busyId, setBusyId] = useState<string | null>(null)
  const [form, setForm] = useState({ name: '', query: '', concept: '' })

  const load = useCallback(async () => {
    try {
      const [subs, open, done] = await Promise.all([
        http.get<Subscription[]>('/api/paper-feed/subscriptions'),
        http.get<Candidate[]>('/api/paper-feed/candidates', { params: { status: 'new' } }),
        http.get<Candidate[]>('/api/paper-feed/candidates', { params: { status: 'imported' } }),
      ])
      setSubscriptions(subs.data)
      setCandidates(open.data)
      setImported(done.data)
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not load the paper feed'))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const runNow = async () => {
    setRunning(true)
    try {
      const { data } = await http.post('/api/paper-feed/run')
      toast.success(data.new ? `${data.new} new paper(s) found` : 'No new papers')
      await load()
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Feed check failed'))
    } finally {
      setRunning(false)
    }
  }

  const importCandidate = async (c: Candidate) => {
    setBusyId(c.id)
    try {
      await http.post(`/api/paper-feed/candidates/${c.id}/import`)
      toast.success(`Imported: ${c.title}`)
      setCandidates(prev => prev.filter(x => x.id !== c.id))
      setImported(prev => [{ ...c, status: 'imported' }, ...prev])
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Import failed'))
    } finally {
      setBusyId(null)
    }
  }

  const dismissCandidate = async (c: Candidate) => {
    setBusyId(c.id)
    try {
      await http.post(`/api/paper-feed/candidates/${c.id}/dismiss`)
      setCandidates(prev => prev.filter(x => x.id !== c.id))
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not dismiss'))
    } finally {
      setBusyId(null)
    }
  }

  const addSubscription = async () => {
    if (!form.name.trim() || !form.query.trim()) return
    try {
      await http.post('/api/paper-feed/subscriptions', {
        name: form.name, query: form.query, concept: form.concept || null
      })
      setForm({ name: '', query: '', concept: '' })
      toast.success('Subscription added — use "Check now" to fetch papers')
      await load()
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not add subscription'))
    }
  }

  const toggleSubscription = async (s: Subscription) => {
    try {
      await http.patch(`/api/paper-feed/subscriptions/${s.id}`, { active: !s.active })
      await load()
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not update subscription'))
    }
  }

  const deleteSubscription = async (s: Subscription) => {
    try {
      await http.delete(`/api/paper-feed/subscriptions/${s.id}`)
      toast.success(`Removed "${s.name}" and its open suggestions`)
      await load()
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not delete subscription'))
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <Rss className="w-7 h-7" /> Paper Feed
          </h1>
          <p className="text-gray-600">
            New arXiv papers for your saved searches — checked daily, ranked by similarity to papers you already have
          </p>
        </div>
        <Button variant="outline" onClick={runNow} disabled={running || subscriptions.length === 0}>
          {running ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
          Check now
        </Button>
      </div>

      <Tabs defaultValue="new">
        <TabsList>
          <TabsTrigger value="new">Suggestions ({candidates.length})</TabsTrigger>
          <TabsTrigger value="imported">Imported ({imported.length})</TabsTrigger>
          <TabsTrigger value="subscriptions">Subscriptions ({subscriptions.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="new" className="space-y-3 mt-4">
          {loading ? (
            <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin" /></div>
          ) : candidates.length === 0 ? (
            <Card>
              <CardContent className="py-10 text-center text-muted-foreground">
                {subscriptions.length === 0
                  ? 'No subscriptions yet. Add one in the "Subscriptions" tab.'
                  : 'No open suggestions. New papers appear here after the daily check or "Check now".'}
              </CardContent>
            </Card>
          ) : candidates.map(c => (
            <CandidateCard key={c.id} c={c} busy={busyId === c.id}
                           onImport={() => importCandidate(c)} onDismiss={() => dismissCandidate(c)} />
          ))}
        </TabsContent>

        <TabsContent value="imported" className="space-y-3 mt-4">
          {imported.length === 0 ? (
            <Card><CardContent className="py-10 text-center text-muted-foreground">Nothing imported from the feed yet.</CardContent></Card>
          ) : imported.map(c => (
            <div key={c.id} className="relative">
              <CandidateCard c={c} busy={false} />
              <CheckCircle className="absolute top-4 right-4 w-5 h-5 text-green-600" aria-label="Imported" />
            </div>
          ))}
        </TabsContent>

        <TabsContent value="subscriptions" className="space-y-4 mt-4">
          <Card>
            <CardHeader>
              <CardTitle>Add subscription</CardTitle>
              <CardDescription>
                arXiv query syntax: <code>abs:"agent memory" OR ti:"LLM wiki"</code>. A concept ranks suggestions and is
                tagged on import.
              </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-[1fr_2fr_1fr_auto]">
              <Input placeholder="Name, e.g. Agent Memory" value={form.name}
                     onChange={e => setForm({ ...form, name: e.target.value })} aria-label="Name" />
              <Input placeholder='abs:"agent memory"' value={form.query}
                     onChange={e => setForm({ ...form, query: e.target.value })} aria-label="arXiv query" />
              <Input placeholder="Concept (optional)" value={form.concept}
                     onChange={e => setForm({ ...form, concept: e.target.value })} aria-label="Concept" />
              <Button onClick={addSubscription} disabled={!form.name.trim() || !form.query.trim()}>
                <Plus className="w-4 h-4 mr-2" /> Add
              </Button>
            </CardContent>
          </Card>

          {subscriptions.map(s => (
            <Card key={s.id} className={s.active ? '' : 'opacity-60'}>
              <CardContent className="p-4 flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <div className="font-medium flex items-center gap-2">
                    {s.name}
                    {s.concept && <Badge variant="secondary">{s.concept}</Badge>}
                    {!s.active && <Badge variant="outline">paused</Badge>}
                  </div>
                  <code className="text-sm text-muted-foreground break-all">{s.query}</code>
                  <p className="text-xs text-muted-foreground mt-1">
                    {s.last_run ? `Last check ${formatDate(s.last_run)}: ${s.last_found ?? 0} new` : 'Not checked yet'}
                  </p>
                </div>
                <div className="flex shrink-0 gap-2">
                  <Button size="sm" variant="outline" onClick={() => toggleSubscription(s)}
                          aria-label={s.active ? 'Pause' : 'Resume'}>
                    {s.active ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                  </Button>
                  <Button size="sm" variant="outline" onClick={() => deleteSubscription(s)} aria-label="Delete">
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>
      </Tabs>
    </div>
  )
}
