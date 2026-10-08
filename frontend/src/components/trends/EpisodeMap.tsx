/**
 * Episode map: when topics in the bubble flare up and fade, and which
 * episode continues which (lineage). Data: /api/analytics/trends/episodes
 * (computed weekly by the topic_map scheduler job).
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader2, RefreshCw, X } from 'lucide-react';
import http, { apiErrorMessage } from '@/services/http';

interface Episode {
  id: number;
  name: string;
  tags: string;
  topic: string;
  family: number;
  start: string;
  end: string;
  peak: string;
  wi: [number, number];
  weeks: number;
  docs: number;
  intensity: number;
  channels: Record<string, number>;
  events: string[];
  parents: number[];
  children: number[];
  movers?: [string, number][];
  examples?: string[];
}

interface EpisodeLink { source: number; target: number; sim: number; share: number }

interface TopicMap {
  created_at: string;
  weeks: string[];
  families: { id: number; name: string; size: number }[];
  episodes: Episode[];
  episode_links: EpisodeLink[];
  stats: { documents: number; episodes: number; links: number; events: Record<string, number> };
}

interface RebuildStatus { running: boolean; error: string | null }

const PALETTE = ['#4e79a7', '#f28e2b', '#e15759', '#76b7b2', '#59a14f', '#edc948', '#b07aa1', '#ff9da7',
  '#9c755f', '#8f8f8f', '#1f77b4', '#d62728', '#2ca02c', '#9467bd', '#8c564b', '#e377c2', '#17becf',
  '#bcbd22', '#6b6ecf', '#e7969c'];
const LABEL_W = 210;
const LANE_H = 17;
const ROW_GAP = 8;
const CHAR_W = 5.6;

const familyName = (name: string) => name.split(' · ').slice(0, 2).join(' · ').slice(0, 34);
const label = (e: Episode) =>
  (e.events.includes('merge') ? '⑃ ' : '') + e.name +
  (e.events.includes('split') ? ' ⑂' : '') + (e.events.includes('end') ? ' †' : '');

const EpisodeMap: React.FC = () => {
  const [map, setMap] = useState<TopicMap | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rebuilding, setRebuilding] = useState(false);
  const [query, setQuery] = useState('');
  const [hover, setHover] = useState<number | null>(null);
  const [selected, setSelected] = useState<Episode | null>(null);
  const [width, setWidth] = useState(1100);
  const boxRef = useRef<HTMLDivElement>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await http.get('/api/analytics/trends/episodes');
      setMap(data.available ? data.map : null);
      setRebuilding(Boolean(data.rebuild?.running));
      setError(null);
    } catch (e) {
      setError(apiErrorMessage(e, 'Could not load the topic map'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => setWidth(Math.max(700, entries[0].contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, [map]);

  // poll while a rebuild runs, then reload the map
  useEffect(() => {
    if (!rebuilding) return;
    const t = setInterval(async () => {
      try {
        const { data } = await http.get<RebuildStatus>('/api/analytics/trends/episodes/rebuild/status');
        if (!data.running) {
          setRebuilding(false);
          if (data.error) setError(data.error);
          load();
        }
      } catch { /* keep polling */ }
    }, 3000);
    return () => clearInterval(t);
  }, [rebuilding, load]);

  const rebuild = async () => {
    try {
      await http.post('/api/analytics/trends/episodes/rebuild');
      setRebuilding(true);
    } catch (e) {
      setError(apiErrorMessage(e, 'Rebuild failed to start'));
    }
  };

  const openEpisode = async (id: number) => {
    try {
      const { data } = await http.get<Episode>(`/api/analytics/trends/episodes/${id}`);
      setSelected(data);
    } catch (e) {
      setError(apiErrorMessage(e, 'Could not load the episode'));
    }
  };

  const layout = useMemo(() => {
    if (!map) return null;
    const nWeeks = map.weeks.length;
    const plotW = width - LABEL_W - 130;
    const xw = (i: number) => LABEL_W + (i / nWeeks) * plotW;
    const famIndex = new Map(map.families.map((f, i) => [f.id, i]));
    const pos: Record<number, { x0: number; x1: number; y: number; inside: boolean; text: string }> = {};
    const rows: { name: string; y: number; h: number; color: string }[] = [];
    let y = 4;
    map.families.forEach((f, fi) => {
      const eps = map.episodes.filter(e => e.family === f.id).sort((a, b) => a.wi[0] - b.wi[0]);
      if (!eps.length) return;
      const lanes: number[] = [];
      eps.forEach(e => {
        const x0 = xw(e.wi[0]);
        const x1 = Math.max(x0 + 4, xw(e.wi[1] + 1));
        const text = label(e);
        const tw = text.length * CHAR_W + 6;
        const inside = x1 - x0 >= tw;
        const reach = inside ? x1 : x1 + tw;
        let lane = lanes.findIndex(end => end + 4 <= x0);
        if (lane < 0) { lane = lanes.length; lanes.push(reach); } else lanes[lane] = reach;
        pos[e.id] = { x0, x1, y: y + lane * LANE_H, inside, text };
      });
      const h = Math.max(1, lanes.length) * LANE_H;
      rows.push({ name: familyName(f.name), y, h, color: PALETTE[fi % PALETTE.length] });
      y += h + ROW_GAP;
    });
    const color = (e: Episode) => PALETTE[(famIndex.get(e.family) ?? 0) % PALETTE.length];
    const maxI = Math.max(...map.episodes.map(e => Math.log(e.intensity)), 1);
    // month ticks
    const ticks = map.weeks.map((w, i) => ({ w, i })).filter(({ w }, k, arr) =>
      k === 0 || w.slice(0, 7) !== arr[k - 1].w.slice(0, 7)).filter((_, k) => k % 2 === 0);
    return { pos, rows, height: y + 24, xw, color, maxI, ticks };
  }, [map, width]);

  const chain = useCallback((id: number) => {
    const seen = new Set([id]);
    if (!map) return seen;
    for (const dir of ['parents', 'children'] as const) {
      const stack = [id];
      while (stack.length) {
        for (const n of map.episodes[stack.pop()!][dir]) if (!seen.has(n)) { seen.add(n); stack.push(n); }
      }
    }
    return seen;
  }, [map]);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q || !map) return null;
    return map.episodes.filter(e => `${e.name} ${e.tags} ${e.topic}`.toLowerCase().includes(q)).length;
  }, [query, map]);

  const focus = useMemo(() => {
    if (hover !== null) return chain(hover);
    const q = query.trim().toLowerCase();
    if (!q || !map) return null;
    const set = new Set<number>();
    map.episodes.filter(e => `${e.name} ${e.tags} ${e.topic}`.toLowerCase().includes(q))
      .forEach(e => chain(e.id).forEach(i => set.add(i)));
    return set;
  }, [hover, query, map, chain]);

  if (loading && !map) {
    return <Card><CardContent className="py-12 flex justify-center"><Loader2 className="w-6 h-6 animate-spin" /></CardContent></Card>;
  }

  if (!map || !layout) {
    return (
      <Card>
        <CardContent className="py-10 text-center space-y-3">
          <p className="text-muted-foreground">{error || 'No topic map computed yet.'}</p>
          <Button onClick={rebuild} disabled={rebuilding}>
            {rebuilding ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <RefreshCw className="w-4 h-4 mr-2" />}
            Compute topic map
          </Button>
        </CardContent>
      </Card>
    );
  }

  const ev = map.stats.events || {};
  const byId = (i: number) => map.episodes[i];

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <CardTitle className="text-lg">Episodes — when topics in your bubble flare up and fade</CardTitle>
            <p className="text-sm text-muted-foreground mt-1">
              Bar = weeks clearly above the topic's own baseline (darker = stronger). Rows = topic families.
              Curves = lineage: the later episode continues the earlier one. ⑂ split · ⑃ merge · † ended without successor.
              Hover to follow a line, click for details.
            </p>
          </div>
          <div className="flex items-center gap-2">
            {matches !== null && <span className="text-xs text-muted-foreground">{matches} match{matches === 1 ? '' : 'es'}</span>}
            <Input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search: agent, memory, GPT"
              className="w-56 h-8" />
            <Button size="sm" variant="outline" onClick={rebuild} disabled={rebuilding} title="Recompute the topic map">
              {rebuilding ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
            </Button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground mt-2">
          <Badge variant="secondary">{map.stats.episodes} episodes</Badge>
          <Badge variant="secondary">{map.stats.links} lineage links</Badge>
          <Badge variant="secondary">{ev.split || 0} splits · {ev.merge || 0} merges · {ev.end || 0} ended</Badge>
          <span className="self-center">
            {map.stats.documents.toLocaleString()} documents · computed {new Date(map.created_at).toLocaleDateString()}
            {rebuilding && ' · recomputing…'}
          </span>
          {error && <span className="self-center text-red-600">{error}</span>}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-4">
          <div ref={boxRef} className="flex-1 min-w-0 overflow-x-auto">
            <svg width={width} height={layout.height} className="text-foreground">
              {layout.rows.map(r => (
                <g key={r.name + r.y}>
                  <rect x={0} y={r.y - 2} width={width} height={r.h + 4} className="fill-muted" opacity={0.5} />
                  <rect x={0} y={r.y - 2} width={3} height={r.h + 4} fill={r.color} />
                  <text x={8} y={r.y + 12} fontSize={11} fill="currentColor">{r.name}</text>
                </g>
              ))}
              <g fill="none">
                {map.episode_links.map(l => {
                  const a = layout.pos[l.source], b = layout.pos[l.target];
                  if (!a || !b) return null;
                  const x0 = Math.min(a.x1, b.x0), y0 = a.y + (LANE_H - 3) / 2;
                  const x1 = b.x0, y1 = b.y + (LANE_H - 3) / 2, dx = Math.max(20, (x1 - x0) / 2);
                  const same = byId(l.source).family === byId(l.target).family;
                  const on = focus ? focus.has(l.source) && focus.has(l.target) : true;
                  return (
                    <path key={`${l.source}-${l.target}`} d={`M${x0},${y0} C${x0 + dx},${y0} ${x1 - dx},${y1} ${x1},${y1}`}
                      stroke={layout.color(byId(l.source))} strokeWidth={1 + 3 * Math.max(0, l.sim - 0.25)}
                      strokeDasharray={same ? undefined : '3 3'}
                      strokeOpacity={focus ? (on ? 0.95 : 0.05) : same ? 0.6 : 0.2} />
                  );
                })}
              </g>
              {map.episodes.map(e => {
                const p = layout.pos[e.id];
                if (!p) return null;
                const dim = focus && !focus.has(e.id);
                return (
                  <g key={e.id} opacity={dim ? 0.15 : 1} className="cursor-pointer"
                    onMouseEnter={() => setHover(e.id)} onMouseLeave={() => setHover(null)}
                    onClick={() => openEpisode(e.id)}>
                    <title>{`${e.name}\n${e.start} → ${e.end} (${e.weeks} weeks) · ×${e.intensity} · ${e.docs} docs`}</title>
                    <rect x={p.x0} y={p.y} width={p.x1 - p.x0} height={LANE_H - 3} rx={3} fill={layout.color(e)}
                      opacity={0.35 + 0.65 * Math.log(e.intensity) / layout.maxI}
                      stroke={selected?.id === e.id ? 'currentColor' : undefined} />
                    <text x={p.inside ? p.x0 + 3 : p.x1 + 3} y={p.y + 10.5} fontSize={10} fill="currentColor"
                      pointerEvents="none">{p.text}</text>
                  </g>
                );
              })}
              <g>
                {layout.ticks.map(t => (
                  <text key={t.w} x={layout.xw(t.i)} y={layout.height - 6} fontSize={10} className="fill-muted-foreground">
                    {t.w.slice(0, 7)}
                  </text>
                ))}
              </g>
            </svg>
          </div>
          {selected && (
            <div className="w-80 shrink-0 border rounded-lg p-3 text-sm space-y-2 self-start sticky top-4">
              <div className="flex items-start justify-between gap-2">
                <p className="font-semibold">{selected.name}</p>
                <button onClick={() => setSelected(null)} aria-label="Close"><X className="w-4 h-4" /></button>
              </div>
              <p className="text-muted-foreground">
                {selected.start} → {selected.end} · {selected.weeks} weeks · peak {selected.peak}<br />
                ×{selected.intensity} the topic's usual level · {selected.docs} docs
                (tweets {selected.channels.tweet || 0}, articles {selected.channels.article || 0}, papers {selected.channels.paper || 0})
              </p>
              <p><span className="text-muted-foreground">From: </span>
                {selected.parents.length ? selected.parents.map(byId).map(e => e.name).join(', ') : '★ new — no predecessor'}</p>
              {selected.children.length > 0 && (
                <p><span className="text-muted-foreground">Continues as: </span>
                  {selected.children.map(byId).map(e => e.name).join(', ')}</p>
              )}
              {selected.movers && selected.movers.length > 0 && (
                <p><span className="text-muted-foreground">First movers: </span>
                  {selected.movers.map(([a, n]) => `${a} (${n})`).join(', ')}</p>
              )}
              <p className="text-muted-foreground text-xs">Topic: {selected.topic}</p>
              {selected.examples && (
                <ul className="space-y-1 text-xs border-t pt-2">
                  {selected.examples.map((x, i) => <li key={i}>• {x}</li>)}
                </ul>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default EpisodeMap;
