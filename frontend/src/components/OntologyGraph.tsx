import React, { useEffect, useState, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import ELK from 'elkjs/lib/elk.bundled.js';
import axios from 'axios';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Minimize2,
  Expand,
  Download,
  RefreshCw,
  Layers,
  GitBranch,
} from 'lucide-react';

import { GraphNode, GraphLink, GraphData } from './ontology-graph/types';
import { renderNodeCanvas } from './ontology-graph/nodeCanvasRenderer';
import NodeInfoPanel from './ontology-graph/NodeInfoPanel';
import GraphLegend from './ontology-graph/GraphLegend';

const OntologyGraph: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  // Graph controls
  const [showOrphans, setShowOrphans] = useState(true);
  const [showSynonyms, setShowSynonyms] = useState(true);
  const [minUsage, setMinUsage] = useState(0);
  const [highlightNeighbors, _setHighlightNeighbors] = useState(true);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [layoutType, setLayoutType] = useState<'force' | 'elk'>('elk');
  const [collapsedNodes, setCollapsedNodes] = useState<Set<string>>(new Set());
  const [maxDepth, setMaxDepth] = useState(4);
  const [showCrossRefs, setShowCrossRefs] = useState(false);

  const graphRef = useRef<any>();
  const containerRef = useRef<HTMLDivElement>(null);
  const elk = new ELK();

  // Process graph data for ELK layout
  const processGraphForELK = useCallback(async (data: GraphData) => {
    if (!data) return data;

    // Create virtual super-root for forest layout
    const virtualRoot = {
      id: '__root__',
      name: 'Root',
      tag: '__root__',
      level: -1,
      usage: 0,
      size: 0,
      color: 'transparent',
      x: dimensions.width / 2,
      y: 0
    };

    // Find root nodes (nodes without parents)
    const childIds = new Set(data.links
      .filter(l => l.type === 'parent-child')
      .map(l => l.target));

    const rootNodes = data.nodes.filter(n => !childIds.has(n.id));

    // Add virtual root and links to root nodes
    const enhancedNodes = [...data.nodes, virtualRoot];
    const enhancedLinks = [
      ...data.links,
      ...rootNodes.map(root => ({
        source: '__root__',
        target: root.id,
        strength: 1,
        type: 'parent-child' as const
      }))
    ];

    // Filter by depth and collapsed nodes
    const visibleNodes = new Set<string | number>();
    const queue: Array<{id: string | number, depth: number}> = [{id: '__root__', depth: 0}];

    while (queue.length > 0) {
      const {id, depth} = queue.shift()!;

      if (depth > maxDepth) continue;

      visibleNodes.add(id);

      // Don't add children if this node is collapsed (except for the virtual root)
      if (collapsedNodes.has(String(id)) && id !== '__root__') {
        continue;
      }

      // Add children to queue
      enhancedLinks
        .filter(l => l.source === id && l.type === 'parent-child')
        .forEach(l => queue.push({id: l.target, depth: depth + 1}));
    }

    // Filter nodes and links based on visibility
    const filteredNodes = enhancedNodes.filter(n => visibleNodes.has(n.id));
    const filteredLinks = enhancedLinks.filter(l =>
      visibleNodes.has(l.source) &&
      visibleNodes.has(l.target) &&
      (l.type === 'parent-child' || (showCrossRefs && l.type === 'synonym'))
    );

    // Build ELK graph
    const elkGraph = {
      id: 'root',
      layoutOptions: {
        'elk.algorithm': 'layered',
        'elk.direction': 'DOWN',
        'elk.spacing.nodeNode': '50',
        'elk.layered.spacing.nodeNodeBetweenLayers': '100',
        'elk.layered.mergeEdges': 'false',
        'elk.hierarchyHandling': 'INCLUDE_CHILDREN'
      },
      children: filteredNodes.map(node => ({
        id: String(node.id),
        width: Math.max(100, node.name.length * 8),
        height: 40,
        labels: [{text: node.name}]
      })),
      edges: filteredLinks.map((link, idx) => ({
        id: `e${idx}`,
        sources: [String(link.source)],
        targets: [String(link.target)]
      }))
    };

    try {
      // Calculate layout
      const layout = await elk.layout(elkGraph);

      // Apply layout positions to nodes
      const positionedNodes = filteredNodes.map(node => {
        const elkNode = layout.children?.find(n => n.id === String(node.id));
        return {
          ...node,
          x: elkNode?.x || 0,
          y: elkNode?.y || 0,
          fx: elkNode?.x || 0,  // Fixed position for force graph
          fy: elkNode?.y || 0
        };
      });

      return {
        ...data,
        nodes: positionedNodes.filter(n => n.id !== '__root__'),
        links: filteredLinks.filter(l => l.source !== '__root__')
      };
    } catch (error) {
      console.error('ELK layout failed:', error);
      return data;
    }
  }, [dimensions, maxDepth, collapsedNodes, showCrossRefs]);

  // Fetch graph data
  const fetchGraphData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.get(`/api/ontology-graph/data`, {
        params: {
          include_orphans: showOrphans,
          min_usage: minUsage
        }
      });

      // Filter out synonyms if needed
      let data = response.data;
      if (!showSynonyms) {
        data = {
          ...data,
          nodes: data.nodes.filter((n: GraphNode) => !n.is_synonym),
          links: data.links.filter((l: GraphLink) => l.type !== 'synonym')
        };
      }

      // Apply ELK layout if selected
      if (layoutType === 'elk') {
        const processedData = await processGraphForELK(data);
        setGraphData(processedData);
      } else {
        setGraphData(data);
      }
    } catch (err) {
      setError('Failed to load graph data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [showOrphans, showSynonyms, minUsage, layoutType, processGraphForELK, collapsedNodes]);

  // Update dimensions on resize
  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        if (isFullscreen) {
          setDimensions({
            width: window.innerWidth - 40,
            height: window.innerHeight - 100
          });
        } else {
          setDimensions({
            width: containerRef.current.offsetWidth,
            height: window.innerHeight - 250
          });
        }
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, [isFullscreen]);

  // Fetch data on mount and when filters change
  useEffect(() => {
    fetchGraphData();
  }, [fetchGraphData]);

  // Graph interaction handlers
  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);

    if (layoutType === 'elk') {
      const nodeId = String(node.id);
      setCollapsedNodes(prev => {
        const newSet = new Set(prev);
        if (newSet.has(nodeId)) {
          newSet.delete(nodeId);
        } else {
          newSet.add(nodeId);
        }
        return newSet;
      });
    }
  }, [layoutType]);

  const handleNodeHover = useCallback((_node: GraphNode | null) => {
    if (!highlightNeighbors || !graphRef.current) return;
  }, [highlightNeighbors]);

  // Zoom controls
  const handleZoomIn = () => { graphRef.current?.zoom(1.2); };
  const handleZoomOut = () => { graphRef.current?.zoom(0.8); };
  const handleZoomFit = () => { graphRef.current?.zoomToFit(400); };

  // Export graph as image
  const handleExport = () => {
    if (graphRef.current) {
      const canvas = graphRef.current.canvas();
      const url = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      link.download = 'ontology-graph.png';
      link.href = url;
      link.click();
    }
  };

  const toggleFullscreen = () => { setIsFullscreen(!isFullscreen); };

  // Handle ESC key to exit fullscreen
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };

    if (isFullscreen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'auto';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'auto';
    };
  }, [isFullscreen]);

  if (loading) {
    return (
      <Card className="p-6">
        <div className="flex items-center justify-center h-96">
          <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
          <span className="ml-2">Loading graph data...</span>
        </div>
      </Card>
    );
  }

  if (error || !graphData) {
    return (
      <Card className="p-6">
        <div className="text-red-500 text-center">
          {error || 'No data available'}
        </div>
      </Card>
    );
  }

  const containerStyles = isFullscreen ? {
    position: 'fixed' as const,
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    zIndex: 50,
    backgroundColor: 'white',
    padding: '1rem'
  } : {};

  return (
    <div className="space-y-4" style={containerStyles}>
      {/* Controls */}
      <Card className="p-4">
        <div className="flex flex-wrap items-center gap-4">
          {/* Zoom controls */}
          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={handleZoomIn}>
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button size="sm" variant="outline" onClick={handleZoomOut}>
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button size="sm" variant="outline" onClick={handleZoomFit}>
              <Maximize2 className="w-4 h-4" />
            </Button>
            <Button
              size="sm"
              variant={isFullscreen ? "default" : "outline"}
              onClick={toggleFullscreen}
              title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
            >
              {isFullscreen ? (
                <>
                  <Minimize2 className="w-4 h-4 mr-1" />
                  Exit
                </>
              ) : (
                <>
                  <Expand className="w-4 h-4 mr-1" />
                  Fullscreen
                </>
              )}
            </Button>
          </div>

          {/* Layout Toggle */}
          <div className="flex items-center gap-2 border-l pl-4">
            <Button
              size="sm"
              variant={layoutType === 'elk' ? "default" : "outline"}
              onClick={() => setLayoutType('elk')}
              title="Hierarchical layout"
            >
              <Layers className="w-4 h-4 mr-1" />
              Tree
            </Button>
            <Button
              size="sm"
              variant={layoutType === 'force' ? "default" : "outline"}
              onClick={() => setLayoutType('force')}
              title="Force-directed layout"
            >
              <GitBranch className="w-4 h-4 mr-1" />
              Force
            </Button>
          </div>

          {/* Depth Control (for ELK layout) */}
          {layoutType === 'elk' && (
            <div className="flex items-center gap-2">
              <Label htmlFor="max-depth">Depth: {maxDepth}</Label>
              <Slider
                id="max-depth"
                min={1}
                max={6}
                step={1}
                value={[maxDepth]}
                onValueChange={(value) => setMaxDepth(value[0])}
                className="w-24"
              />
            </div>
          )}

          {/* Filters */}
          <div className="flex items-center gap-2">
            <Label htmlFor="show-orphans">Show Orphans</Label>
            <Switch
              id="show-orphans"
              checked={showOrphans}
              onCheckedChange={setShowOrphans}
            />
          </div>

          <div className="flex items-center gap-2">
            <Label htmlFor="show-synonyms">Show Synonyms</Label>
            <Switch
              id="show-synonyms"
              checked={showSynonyms}
              onCheckedChange={setShowSynonyms}
            />
          </div>

          {layoutType === 'elk' && (
            <div className="flex items-center gap-2">
              <Label htmlFor="show-crossrefs">Cross-References</Label>
              <Switch
                id="show-crossrefs"
                checked={showCrossRefs}
                onCheckedChange={setShowCrossRefs}
              />
            </div>
          )}

          <div className="flex items-center gap-2">
            <Label htmlFor="min-usage">Min Usage: {minUsage}</Label>
            <Slider
              id="min-usage"
              min={0}
              max={50}
              step={1}
              value={[minUsage]}
              onValueChange={(value) => setMinUsage(value[0])}
              className="w-32"
            />
          </div>

          {/* Actions */}
          <Button size="sm" variant="outline" onClick={fetchGraphData}>
            <RefreshCw className="w-4 h-4 mr-1" />
            Refresh
          </Button>

          <Button size="sm" variant="outline" onClick={handleExport}>
            <Download className="w-4 h-4 mr-1" />
            Export
          </Button>
        </div>

        {/* Statistics */}
        <div className="flex flex-wrap gap-2 mt-4">
          <Badge variant="outline">
            Nodes: {graphData.stats.total_nodes}
          </Badge>
          <Badge variant="outline">
            Links: {graphData.stats.total_links}
          </Badge>
          <Badge variant="outline">
            Roots: {graphData.stats.root_nodes}
          </Badge>
          <Badge variant="outline">
            Max Depth: {graphData.stats.max_depth}
          </Badge>
          <Badge variant="outline">
            Total Usage: {graphData.stats.total_usage}
          </Badge>
          {layoutType === 'elk' && (
            <Badge variant="secondary" className="ml-auto">
              Click nodes to collapse/expand
            </Badge>
          )}
        </div>
      </Card>

      {/* Graph */}
      <Card className="relative">
        <div ref={containerRef} className="relative">
          <ForceGraph2D
            ref={graphRef}
            graphData={graphData}
            width={dimensions.width}
            height={dimensions.height}
            nodeLabel="name"
            nodeAutoColorBy="level"
            nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
              renderNodeCanvas(node, ctx, globalScale, { layoutType, collapsedNodes });
            }}
            linkDirectionalArrowLength={3}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.25}
            linkWidth={(link: any) => Math.sqrt(link.strength * 10)}
            linkColor={(link: any) => link.type === 'synonym' ? '#b2bec3' : '#dfe6e9'}
            onNodeClick={handleNodeClick}
            onNodeHover={handleNodeHover}
            enableNodeDrag={true}
            enableZoomInteraction={true}
            cooldownTicks={100}
            onEngineStop={() => graphRef.current?.zoomToFit(400)}
          />
        </div>

        {/* Selected node info */}
        {selectedNode && (
          <NodeInfoPanel
            node={selectedNode}
            layoutType={layoutType}
            collapsedNodes={collapsedNodes}
            onClose={() => setSelectedNode(null)}
          />
        )}

        {/* Legend */}
        <GraphLegend />
      </Card>
    </div>
  );
};

export default OntologyGraph;
