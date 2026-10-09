/**
 * ConceptAssociations Component (replaces the separate Correlation and
 * Network tabs, which showed the same co-occurrence data twice).
 * Data: /network (app.services.trend_core): concept pairs that meet more
 * often than chance (NPMI), with support from two sources; flags pairs that
 * are new against the previous window. Left: network (node size = items,
 * colour = cluster, edge width = NPMI, dashed = new). Right: pair list.
 */
import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import ForceGraph2D, { ForceGraphMethods, LinkObject, NodeObject } from 'react-force-graph-2d';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Download, Maximize, Network, X } from 'lucide-react';
import { CooccurrencePair, NetworkGraphData } from '../../types/trends';

interface ConceptAssociationsProps {
  data: NetworkGraphData | null;
  loading?: boolean;
  onConceptClick?: (conceptId: string) => void;
}

interface GraphNode extends NodeObject {
  id: string;
  name: string;
  val: number;
  color: string;
}

interface GraphLink extends LinkObject {
  source: string | GraphNode;
  target: string | GraphNode;
  value: number;
  strength: number;
  new?: boolean;
}

const endId = (e: string | GraphNode) => (typeof e === 'object' ? e.id : e);

const ConceptAssociations: React.FC<ConceptAssociationsProps> = ({ data, loading, onConceptClick }) => {
  const fgRef = useRef<ForceGraphMethods>();
  const boxRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 700, height: 460 });
  const [selected, setSelected] = useState<string | null>(null);
  const [hover, setHover] = useState<string | null>(null);
  const [onlyNew, setOnlyNew] = useState(false);
  const [fg, setFg] = useState('#1f2328');

  useEffect(() => {
    const el = boxRef.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => {
      const r = entries[0].contentRect;
      setSize({ width: Math.max(300, r.width), height: 460 });
    });
    ro.observe(el);
    setFg(getComputedStyle(el).color || '#1f2328');   // canvas text follows the theme
    return () => ro.disconnect();
  }, [data]);

  const graph = useMemo(() => {
    if (!data) return { nodes: [] as GraphNode[], links: [] as GraphLink[] };
    const maxVal = Math.max(1, ...data.nodes.map(n => n.val));
    return {
      nodes: data.nodes.map(n => ({ id: n.id, name: n.name, color: n.color, val: 2 + 18 * (n.val / maxVal) })),
      links: data.links.map(l => ({ source: l.source, target: l.target, value: l.value, strength: l.strength, new: l.new })),
    };
  }, [data]);

  const neighbours = useMemo(() => {
    const m = new Map<string, Set<string>>();
    graph.links.forEach(l => {
      const a = endId(l.source), b = endId(l.target);
      if (!m.has(a)) m.set(a, new Set());
      if (!m.has(b)) m.set(b, new Set());
      m.get(a)!.add(b);
      m.get(b)!.add(a);
    });
    return m;
  }, [graph]);

  const focus = selected ?? hover;
  const focusSet = useMemo(() => {
    if (!focus) return null;
    return new Set([focus, ...(neighbours.get(focus) || [])]);
  }, [focus, neighbours]);

  const name = useCallback((id: string) => data?.nodes.find(n => n.id === id)?.name
    ?? data?.pairs?.find(p => p.concept_a_id === id)?.concept_a
    ?? data?.pairs?.find(p => p.concept_b_id === id)?.concept_b ?? id, [data]);

  const pairs: CooccurrencePair[] = useMemo(() => {
    let ps = data?.pairs || [];
    if (onlyNew) ps = ps.filter(p => p.new);
    if (selected) ps = ps.filter(p => p.concept_a_id === selected || p.concept_b_id === selected);
    return ps;
  }, [data, onlyNew, selected]);

  const drawNode = useCallback((node: NodeObject, ctx: CanvasRenderingContext2D, scale: number) => {
    const n = node as GraphNode;
    const r = Math.sqrt(n.val) * 2.2;
    const dim = focusSet && !focusSet.has(n.id);
    ctx.globalAlpha = dim ? 0.15 : 1;
    ctx.beginPath();
    ctx.arc(n.x!, n.y!, r, 0, 2 * Math.PI);
    ctx.fillStyle = n.color;
    ctx.fill();
    if (selected === n.id) {
      ctx.lineWidth = 2;
      ctx.strokeStyle = fg;
      ctx.stroke();
    }
    const fontSize = Math.max(3, 11 / scale);
    ctx.font = `${fontSize}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = fg;
    ctx.fillText(n.name, n.x!, n.y! + r + 1);
    ctx.globalAlpha = 1;
  }, [focusSet, selected, fg]);

  const drawLink = useCallback((link: LinkObject, ctx: CanvasRenderingContext2D) => {
    const l = link as GraphLink;
    const a = l.source as GraphNode, b = l.target as GraphNode;
    if (a.x === undefined || b.x === undefined) return;
    const on = !focusSet || (focusSet.has(a.id) && focusSet.has(b.id) && (a.id === focus || b.id === focus));
    ctx.globalAlpha = on ? 0.8 : 0.08;
    ctx.setLineDash(l.new ? [3, 3] : []);
    ctx.beginPath();
    ctx.moveTo(a.x, a.y!);
    ctx.lineTo(b.x, b.y!);
    ctx.strokeStyle = '#8c959f';
    ctx.lineWidth = 0.5 + 3 * l.strength;
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.globalAlpha = 1;
  }, [focusSet, focus]);

  const exportPng = () => {
    const canvas = boxRef.current?.querySelector('canvas');
    if (!canvas) return;
    const a = document.createElement('a');
    a.download = 'concept-associations.png';
    a.href = canvas.toDataURL('image/png');
    a.click();
  };

  const header = (
    <CardTitle className="flex items-center gap-2">
      <Network className="w-5 h-5" />
      Concept Associations
    </CardTitle>
  );

  if (loading) {
    return <Card className="h-[600px]"><CardHeader>{header}</CardHeader>
      <CardContent className="h-[480px] flex items-center justify-center text-muted-foreground animate-pulse">Loading…</CardContent></Card>;
  }
  if (!data || !graph.nodes.length) {
    return <Card className="h-[600px]"><CardHeader>{header}</CardHeader>
      <CardContent className="h-[480px] flex items-center justify-center text-muted-foreground">No associations in this window</CardContent></Card>;
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <div>
            {header}
            <p className="text-xs text-muted-foreground mt-1">
              Concept pairs that appear together more often than chance would predict (NPMI), in ≥3 items from ≥2 sources.
              Node size = items, colour = cluster, line width = strength, dashed = new against the previous window.
              Click a concept to see its pairs{data.data_through ? ` · data through ${data.data_through}` : ''}.
            </p>
          </div>
          <div className="flex gap-1 shrink-0">
            <Button variant="outline" size="icon" className="h-8 w-8" title="Fit" onClick={() => fgRef.current?.zoomToFit(400, 40)}>
              <Maximize className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" title="Export PNG" onClick={exportPng}>
              <Download className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-1 text-xs">
          <Badge variant="outline">{data.statistics.total_nodes} concepts</Badge>
          <Badge variant="outline">{data.statistics.total_edges} links shown</Badge>
          {data.statistics.significant_pairs !== undefined &&
            <Badge variant="outline">{data.statistics.significant_pairs} significant pairs in total</Badge>}
          {data.clusters.slice(0, 8).map(c => (
            <span key={c.id} className="flex items-center gap-1 text-muted-foreground">
              <span className="inline-block w-2.5 h-2.5 rounded-full" style={{ background: c.color }} />{c.name}
            </span>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col lg:flex-row gap-4">
          <div ref={boxRef} className="flex-1 min-w-0 border rounded-lg text-foreground">
            <ForceGraph2D
              ref={fgRef}
              width={size.width}
              height={size.height}
              graphData={graph}
              nodeCanvasObject={drawNode}
              nodePointerAreaPaint={(node, color, ctx) => {
                const n = node as GraphNode;
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(n.x!, n.y!, Math.sqrt(n.val) * 2.2 + 2, 0, 2 * Math.PI);
                ctx.fill();
              }}
              linkCanvasObject={drawLink}
              cooldownTicks={120}
              onEngineStop={() => fgRef.current?.zoomToFit(400, 40)}
              onNodeHover={n => setHover(n ? (n as GraphNode).id : null)}
              onNodeClick={n => setSelected(prev => (prev === (n as GraphNode).id ? null : (n as GraphNode).id))}
              onBackgroundClick={() => setSelected(null)}
            />
          </div>
          <div className="lg:w-80 shrink-0 text-sm">
            <div className="flex items-center justify-between mb-2">
              {selected ? (
                <div className="flex items-center gap-2 min-w-0">
                  <span className="font-semibold truncate">{name(selected)}</span>
                  <button onClick={() => setSelected(null)} aria-label="Clear selection"><X className="w-4 h-4" /></button>
                </div>
              ) : <span className="font-semibold">Strongest pairs</span>}
              <label className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                <input type="checkbox" checked={onlyNew} onChange={e => setOnlyNew(e.target.checked)} /> only new
              </label>
            </div>
            {selected && (
              <Button size="sm" variant="outline" className="mb-2 w-full" onClick={() => onConceptClick?.(selected)}>
                Open “{name(selected)}” in the Topic Explorer
              </Button>
            )}
            <div className="space-y-1 max-h-[420px] overflow-y-auto pr-1">
              {pairs.map(p => (
                <button key={`${p.concept_a_id}-${p.concept_b_id}`}
                  className="w-full text-left rounded border px-2 py-1 hover:bg-muted"
                  onClick={() => setSelected(selected === p.concept_a_id ? p.concept_b_id : p.concept_a_id)}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="truncate">{p.concept_a} ↔ {p.concept_b}</span>
                    {p.new && <Badge variant="secondary" className="text-[10px] shrink-0">new</Badge>}
                  </div>
                  <div className="text-xs text-muted-foreground">{p.count} items · strength {p.strength.toFixed(2)}</div>
                </button>
              ))}
              {!pairs.length && <p className="text-muted-foreground text-xs">No pairs</p>}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default ConceptAssociations;
