import { useCallback, useEffect, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { toast } from 'sonner'
import { Newspaper, Loader2, RefreshCw, TrendingUp, TrendingDown, AlertTriangle, Twitter, FileText } from 'lucide-react'
import http, { apiErrorMessage } from '@/services/http'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface TrendItem { concept: string; count: number; previous: number; velocity_pct: number }

interface Digest {
  id: string
  week_start: string
  week_end: string
  created_at: string
  stats: { tweets: number; articles: number; papers: number; feed_suggestions: number; active_concepts?: number }
  summary?: string
  summary_error?: string | null
  rising?: TrendItem[]
  declining?: TrendItem[]
  anomalies?: { concept: string; z_score: number; current: number; baseline: number }[]
  new_papers?: { id: string; title: string; source?: string }[]
  new_articles?: { id: string; title: string; author?: string; url?: string }[]
  top_tweets?: { id: string; author: string; likes: number; text: string }[]
  feed_suggestions?: { title: string; arxiv_id: string; score: number | null }[]
}

const fmt = (d: string) => new Date(d).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })

function Stat({ label, value }: { label: string; value?: number }) {
  return (
    <div className="rounded-lg border p-3">
      <div className="text-2xl font-semibold">{value ?? '–'}</div>
      <div className="text-sm text-muted-foreground">{label}</div>
    </div>
  )
}

export default function WeeklyDigest() {
  const [list, setList] = useState<Digest[]>([])
  const [digest, setDigest] = useState<Digest | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)

  const open = useCallback(async (id?: string) => {
    try {
      const { data } = await http.get<Digest>(id ? `/api/digest/${id}` : '/api/digest/latest')
      setDigest(data)
    } catch (err: any) {
      if (err?.response?.status !== 404) toast.error(apiErrorMessage(err, 'Could not load the digest'))
      setDigest(null)
    }
  }, [])

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const { data } = await http.get<Digest[]>('/api/digest')
      setList(data)
      if (data.length) await open(data[0].id)
    } catch (err) {
      toast.error(apiErrorMessage(err, 'Could not load digests'))
    } finally {
      setLoading(false)
    }
  }, [open])

  useEffect(() => { load() }, [load])

  const generate = async () => {
    setGenerating(true)
    const run = http.post('/api/digest/generate')
    toast.promise(run, {
      loading: 'Writing this week\'s digest — about 30 seconds…',
      success: (r) => r.data.summary_ok ? 'Digest ready' : 'Digest saved, but the AI summary failed',
      error: (e) => apiErrorMessage(e, 'Digest failed'),
    })
    try { await run; await load() } catch { /* toast shows it */ } finally { setGenerating(false) }
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-6">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold mb-2 flex items-center gap-2">
            <Newspaper className="w-7 h-7" /> Weekly Digest
          </h1>
          <p className="text-gray-600">
            A briefing on the last 7 days — written automatically once a week from your trends, papers and tweets
          </p>
        </div>
        <Button variant="outline" onClick={generate} disabled={generating}>
          {generating ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
          Generate now
        </Button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin" /></div>
      ) : !digest ? (
        <Card><CardContent className="py-10 text-center text-muted-foreground">
          No digest yet. The scheduler writes one every week; "Generate now" creates one immediately.
        </CardContent></Card>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1fr_240px]">
          <div className="space-y-6 min-w-0">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <Stat label="Tweets" value={digest.stats.tweets} />
              <Stat label="Articles" value={digest.stats.articles} />
              <Stat label="Papers" value={digest.stats.papers} />
              <Stat label="Feed suggestions" value={digest.stats.feed_suggestions} />
            </div>

            <Card>
              <CardHeader>
                <CardTitle>{fmt(digest.week_start)} – {fmt(digest.week_end)}</CardTitle>
              </CardHeader>
              <CardContent>
                {digest.summary ? (
                  <div className="prose prose-sm dark:prose-invert max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{digest.summary}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm text-amber-700 flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4" />
                    The AI summary failed ({digest.summary_error || 'unknown error'}); the facts below are complete.
                  </p>
                )}
              </CardContent>
            </Card>

            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="text-base flex items-center gap-2"><TrendingUp className="w-4 h-4" /> Rising</CardTitle></CardHeader>
                <CardContent className="space-y-1 text-sm">
                  {(digest.rising || []).map(t => (
                    <div key={t.concept} className="flex justify-between gap-2">
                      <span className="truncate">{t.concept}</span>
                      <span className="text-muted-foreground shrink-0">{t.previous} → {t.count}</span>
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-base flex items-center gap-2"><TrendingDown className="w-4 h-4" /> Declining &amp; spikes</CardTitle></CardHeader>
                <CardContent className="space-y-1 text-sm">
                  {(digest.declining || []).map(t => (
                    <div key={t.concept} className="flex justify-between gap-2">
                      <span className="truncate">{t.concept}</span>
                      <span className="text-muted-foreground shrink-0">{t.previous} → {t.count}</span>
                    </div>
                  ))}
                  {(digest.anomalies || []).map(a => (
                    <div key={`a-${a.concept}`} className="flex justify-between gap-2">
                      <span className="truncate">{a.concept}</span>
                      <Badge variant="outline" className="shrink-0">spike z={a.z_score}</Badge>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
              <Card>
                <CardHeader><CardTitle className="text-base flex items-center gap-2"><FileText className="w-4 h-4" /> New papers &amp; articles</CardTitle></CardHeader>
                <CardContent className="space-y-1 text-sm">
                  {(digest.new_papers || []).slice(0, 12).map(p => <div key={p.id} className="truncate">{p.title}</div>)}
                  {(digest.new_articles || []).map(a => (
                    <div key={a.id} className="truncate text-muted-foreground">
                      {a.url ? <a href={a.url} target="_blank" rel="noreferrer" className="hover:underline">{a.title}</a> : a.title}
                      {a.author ? ` · ${a.author}` : ''}
                    </div>
                  ))}
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle className="text-base flex items-center gap-2"><Twitter className="w-4 h-4" /> Most-liked tweets</CardTitle></CardHeader>
                <CardContent className="space-y-3 text-sm">
                  {(digest.top_tweets || []).slice(0, 6).map(t => (
                    <div key={t.id}>
                      <div className="font-medium">@{t.author} <span className="text-muted-foreground font-normal">· {t.likes.toLocaleString()} likes</span></div>
                      <div className="text-muted-foreground line-clamp-2">{t.text}</div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            </div>
          </div>

          <Card className="h-fit">
            <CardHeader><CardTitle className="text-base">Earlier digests</CardTitle></CardHeader>
            <CardContent className="space-y-1">
              {list.map(d => (
                <button key={d.id} onClick={() => open(d.id)}
                        className={`w-full text-left text-sm rounded-md px-2 py-1.5 hover:bg-accent ${d.id === digest.id ? 'bg-accent font-medium' : ''}`}>
                  {fmt(d.week_start)} – {fmt(d.week_end)}
                </button>
              ))}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
