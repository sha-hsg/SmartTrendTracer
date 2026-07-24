/**
 * TrendNetworkGraph Component
 * Force-directed graph showing concept relationships
 * Node size = activity level, Edge thickness = co-occurrence strength
 */

import React, { useRef, useCallback, useEffect, useState } from 'react';
import ForceGraph2D, { ForceGraphMethods, NodeObject, LinkObject } from 'react-force-graph-2d';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import {
  Network,
  ZoomIn,
  ZoomOut,
  Maximize,
  Download,
  Settings2,
  Eye,
  EyeOff,
} from 'lucide-react';
import { NetworkGraphData, NetworkNode, NetworkLink } from '../../types/trends';

interface TrendNetworkGraphProps {
  data: NetworkGraphData | null;
  loading?: boolean;
  onNodeClick?: (nodeId: string) => void;
}

interface GraphNode extends NodeObject {
  id: string;
  name: string;
  val: number;
  color: string;
  entity_type?: string;
  activity: number;
}

interface GraphLink extends LinkObject {
  source: string | GraphNode;
  target: string | GraphNode;
  value: number;
  strength: number;
}

const TrendNetworkGraph: React.FC<TrendNetworkGraphProps> = ({ data, loading, onNodeClick }) => {
  const fgRef = useRef<ForceGraphMethods>();
  const containerRef = useRef<HTMLDivElement>(null);

  const [showLabels, setShowLabels] = useState(true);
  const [showControls, setShowControls] = useState(false);
  const [nodeSize, setNodeSize] = useState(1);
  const [linkDistance, setLinkDistance] = useState(100);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [highlightNodes, setHighlightNodes] = useState<Set<string>>(new Set());
  const [highlightLinks, setHighlightLinks] = useState<Set<string>>(new Set());
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  // Update dimensions on container resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect();
        setDimensions({ width: width - 20, height: Math.max(400, height - 20) });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  // Build graph data
  const graphData = React.useMemo(() => {
    if (!data) return { nodes: [], links: [] };

    const nodes: GraphNode[] = data.nodes.map(n => ({
      id: n.id,
      name: n.name,
      val: Math.max(n.val || 1, 5) * nodeSize,
      color: n.color,
      entity_type: n.entity_type,
      activity: n.activity,
    }));

    const links: GraphLink[] = data.links.map(l => ({
      source: l.source,
      target: l.target,
      value: l.value,
      strength: l.strength,
    }));

    return { nodes, links };
  }, [data, nodeSize]);

  const handleNodeClick = useCallback((node: NodeObject) => {
    const graphNode = node as GraphNode;
    setSelectedNode(graphNode);

    // Highlight connected nodes and links
    const connectedNodes = new Set<string>();
    const connectedLinks = new Set<string>();

    connectedNodes.add(graphNode.id);

    graphData.links.forEach(link => {
      const sourceId = typeof link.source === 'object' ? (link.source as GraphNode).id : link.source;
      const targetId = typeof link.target === 'object' ? (link.target as GraphNode).id : link.target;

      if (sourceId === graphNode.id) {
        connectedNodes.add(targetId);
        connectedLinks.add(`${sourceId}-${targetId}`);
      } else if (targetId === graphNode.id) {
        connectedNodes.add(sourceId);
        connectedLinks.add(`${sourceId}-${targetId}`);
      }
    });

    setHighlightNodes(connectedNodes);
    setHighlightLinks(connectedLinks);

    if (onNodeClick) {
      onNodeClick(graphNode.id);
    }
  }, [graphData.links, onNodeClick]);

  const handleNodeHover = useCallback((node: NodeObject | null) => {
    if (!node) {
      setHighlightNodes(new Set());
      setHighlightLinks(new Set());
      return;
    }

    const graphNode = node as GraphNode;
    const connectedNodes = new Set<string>();
    const connectedLinks = new Set<string>();

    connectedNodes.add(graphNode.id);

    graphData.links.forEach(link => {
      const sourceId = typeof link.source === 'object' ? (link.source as GraphNode).id : link.source;
      const targetId = typeof link.target === 'object' ? (link.target as GraphNode).id : link.target;

      if (sourceId === graphNode.id) {
        connectedNodes.add(targetId);
        connectedLinks.add(`${sourceId}-${targetId}`);
      } else if (targetId === graphNode.id) {
        connectedNodes.add(sourceId);
        connectedLinks.add(`${sourceId}-${targetId}`);
      }
    });

    setHighlightNodes(connectedNodes);
    setHighlightLinks(connectedLinks);
  }, [graphData.links]);

  const handleZoomIn = () => fgRef.current?.zoom(2, 300);
  const handleZoomOut = () => fgRef.current?.zoom(0.5, 300);
  const handleZoomFit = () => fgRef.current?.zoomToFit(400, 50);

  const handleExport = () => {
    const canvas = containerRef.current?.querySelector('canvas');
    if (canvas) {
      const url = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = 'trend-network.png';
      link.href = url;
      link.click();
    }
  };

  // Custom node rendering
  const nodeCanvasObject = useCallback((node: NodeObject, ctx: CanvasRenderingContext2D, globalScale: number) => {
    const graphNode = node as GraphNode;
    const label = graphNode.name;
    const fontSize = Math.max(8, 12 / globalScale);
    const nodeRadius = Math.sqrt(graphNode.val || 10) * 2;

    const isHighlighted = highlightNodes.has(graphNode.id);
    const isSelected = selectedNode?.id === graphNode.id;

    // Draw node circle
    ctx.beginPath();
    ctx.arc(node.x!, node.y!, nodeRadius, 0, 2 * Math.PI);
    ctx.fillStyle = isHighlighted || isSelected
      ? graphNode.color
      : highlightNodes.size > 0
        ? `${graphNode.color}40`
        : graphNode.color;
    ctx.fill();

    // Draw border for selected/highlighted
    if (isSelected || isHighlighted) {
      ctx.strokeStyle = isSelected ? '#000' : graphNode.color;
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.stroke();
    }

    // Draw label
    if (showLabels && globalScale > 0.4) {
      ctx.font = `${fontSize}px Sans-Serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = isHighlighted || highlightNodes.size === 0 ? '#333' : '#99999966';
      ctx.fillText(label, node.x!, node.y! + nodeRadius + fontSize);
    }
  }, [showLabels, highlightNodes, selectedNode]);

  // Custom link rendering
  const linkCanvasObject = useCallback((link: LinkObject, ctx: CanvasRenderingContext2D) => {
    const graphLink = link as GraphLink;
    const sourceNode = graphLink.source as GraphNode;
    const targetNode = graphLink.target as GraphNode;

    if (!sourceNode.x || !targetNode.x) return;

    const linkId = `${sourceNode.id}-${targetNode.id}`;
    const isHighlighted = highlightLinks.has(linkId);

    ctx.beginPath();
    ctx.moveTo(sourceNode.x, sourceNode.y!);
    ctx.lineTo(targetNode.x, targetNode.y!);
    ctx.strokeStyle = isHighlighted
      ? '#3B82F6'
      : highlightLinks.size > 0
        ? '#e5e7eb'
        : '#d1d5db';
    ctx.lineWidth = isHighlighted
      ? Math.max(graphLink.strength * 5, 2)
      : Math.max(graphLink.strength * 3, 0.5);
    ctx.stroke();
  }, [highlightLinks]);

  if (loading) {
    return (
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5" />
            Concept Network
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[500px] flex items-center justify-center">
          <div className="animate-pulse text-muted-foreground">Loading network graph...</div>
        </CardContent>
      </Card>
    );
  }

  if (!data || graphData.nodes.length === 0) {
    return (
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5" />
            Concept Network
          </CardTitle>
        </CardHeader>
        <CardContent className="h-[500px] flex items-center justify-center">
          <p className="text-muted-foreground">No network data available</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="h-[600px]">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Network className="w-5 h-5" />
            Concept Network
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleZoomFit}>
              <Maximize className="h-4 w-4" />
            </Button>
            <Button variant="outline" size="icon" className="h-8 w-8" onClick={handleExport}>
              <Download className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="icon"
              className="h-8 w-8"
              onClick={() => setShowControls(!showControls)}
            >
              <Settings2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Controls panel */}
        {showControls && (
          <div className="mt-2 p-3 border rounded-lg bg-muted/50 space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Show Labels</Label>
              <Switch checked={showLabels} onCheckedChange={setShowLabels} />
            </div>
            <div className="space-y-1">
              <Label className="text-sm">Node Size: {nodeSize.toFixed(1)}</Label>
              <Slider
                value={[nodeSize]}
                min={0.5}
                max={2}
                step={0.1}
                onValueChange={([v]) => setNodeSize(v)}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-sm">Link Distance: {linkDistance}</Label>
              <Slider
                value={[linkDistance]}
                min={50}
                max={200}
                step={10}
                onValueChange={([v]) => setLinkDistance(v)}
              />
            </div>
          </div>
        )}

        {/* Statistics */}
        <div className="flex items-center gap-2 mt-2">
          <Badge variant="outline" className="text-xs">
            {data.statistics.total_nodes} nodes
          </Badge>
          <Badge variant="outline" className="text-xs">
            {data.statistics.total_edges} edges
          </Badge>
          <Badge variant="outline" className="text-xs">
            Avg: {data.statistics.avg_connections} connections
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="h-[420px] relative" ref={containerRef}>
        <ForceGraph2D
          ref={fgRef}
          width={dimensions.width}
          height={dimensions.height}
          graphData={graphData}
          nodeCanvasObject={nodeCanvasObject}
          linkCanvasObject={linkCanvasObject}
          nodeRelSize={6}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          d3AlphaDecay={0.02}
          d3VelocityDecay={0.3}
          cooldownTime={3000}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
        />

        {/* Selected node info */}
        {selectedNode && (
          <div className="absolute bottom-4 left-4 p-3 bg-white border rounded-lg shadow-lg max-w-xs">
            <div className="flex items-center justify-between">
              <h4 className="font-semibold text-sm">{selectedNode.name}</h4>
              <Badge variant="outline" className="text-[10px]">{selectedNode.entity_type}</Badge>
            </div>
            <div className="mt-2 text-xs text-muted-foreground space-y-1">
              <p>Activity: {selectedNode.activity} connections</p>
              <p>Click to filter content with this concept</p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default TrendNetworkGraph;
