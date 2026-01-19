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
  ChevronDown,
  ChevronRight
} from 'lucide-react';

interface GraphNode {
  id: string | number;
  name: string;
  tag: string;
  level: number;
  usage: number;
  size: number;
  color: string;
  description?: string;
  verified?: boolean;
  quality_score?: number;
  child_count?: number;
  descendant_count?: number;
  is_synonym?: boolean;
  x?: number;
  y?: number;
}

interface GraphLink {
  source: string | number;
  target: string | number;
  strength: number;
  type: 'parent-child' | 'synonym';
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
  stats: {
    total_nodes: number;
    total_links: number;
    root_nodes: number;
    max_depth: number;
    total_usage: number;
    orphan_count: number;
  };
}

const OntologyGraph: React.FC = () => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  
  // Graph controls
  const [showOrphans, setShowOrphans] = useState(true);
  const [showSynonyms, setShowSynonyms] = useState(true);
  const [minUsage, setMinUsage] = useState(0);
  const [highlightNeighbors, setHighlightNeighbors] = useState(true);
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
    const nodeMap = new Map(data.nodes.map(n => [n.id, n]));
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
      const response = await axios.get('http://localhost:8000/api/ontology-graph/data', {
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
          // In fullscreen mode, use full viewport
          setDimensions({
            width: window.innerWidth - 40, // Small margin
            height: window.innerHeight - 100 // Account for controls
          });
        } else {
          // Normal mode
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
    
    // Toggle collapse state on double-click
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

  const handleNodeHover = useCallback((node: GraphNode | null) => {
    if (!highlightNeighbors || !graphRef.current) return;
    
    // Highlight logic would go here
    // This would highlight connected nodes
  }, [highlightNeighbors]);

  // Zoom controls
  const handleZoomIn = () => {
    if (graphRef.current) {
      graphRef.current.zoom(1.2);
    }
  };

  const handleZoomOut = () => {
    if (graphRef.current) {
      graphRef.current.zoom(0.8);
    }
  };

  const handleZoomFit = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400);
    }
  };

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

  // Toggle fullscreen mode
  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  // Handle ESC key to exit fullscreen
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isFullscreen) {
        setIsFullscreen(false);
      }
    };

    if (isFullscreen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent scrolling in fullscreen
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

  // Fullscreen container styles
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
              💡 Click nodes to collapse/expand
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
              const label = node.name;
              const fontSize = 12 / globalScale;
              const nodeRadius = node.size || 5;
              ctx.font = `${fontSize}px Sans-Serif`;
              
              // Draw node circle
              ctx.fillStyle = node.color || '#999';
              ctx.beginPath();
              ctx.arc(node.x, node.y, nodeRadius, 0, 2 * Math.PI, false);
              ctx.fill();
              
              // Draw border for nodes with children (in ELK layout)
              if (layoutType === 'elk' && node.child_count && node.child_count > 0) {
                ctx.strokeStyle = collapsedNodes.has(String(node.id)) ? '#ef4444' : '#10b981';
                ctx.lineWidth = 2 / globalScale;
                ctx.beginPath();
                ctx.arc(node.x, node.y, nodeRadius + 2, 0, 2 * Math.PI, false);
                ctx.stroke();
              }
              
              // Draw collapse/expand indicator for nodes with children (in ELK layout)
              if (layoutType === 'elk' && node.child_count && node.child_count > 0) {
                const isCollapsed = collapsedNodes.has(String(node.id));
                const indicatorSize = 8 / globalScale;
                const indicatorX = node.x + nodeRadius + 4;
                const indicatorY = node.y - nodeRadius;
                
                // Draw background circle for indicator
                ctx.fillStyle = '#ffffff';
                ctx.beginPath();
                ctx.arc(indicatorX, indicatorY, indicatorSize, 0, 2 * Math.PI, false);
                ctx.fill();
                
                ctx.strokeStyle = isCollapsed ? '#ef4444' : '#10b981';
                ctx.lineWidth = 1.5 / globalScale;
                ctx.beginPath();
                ctx.arc(indicatorX, indicatorY, indicatorSize, 0, 2 * Math.PI, false);
                ctx.stroke();
                
                // Draw chevron
                ctx.strokeStyle = isCollapsed ? '#ef4444' : '#10b981';
                ctx.lineWidth = 2 / globalScale;
                ctx.beginPath();
                if (isCollapsed) {
                  // Chevron right for collapsed
                  ctx.moveTo(indicatorX - indicatorSize/2, indicatorY - indicatorSize/2);
                  ctx.lineTo(indicatorX + indicatorSize/3, indicatorY);
                  ctx.lineTo(indicatorX - indicatorSize/2, indicatorY + indicatorSize/2);
                } else {
                  // Chevron down for expanded
                  ctx.moveTo(indicatorX - indicatorSize/2, indicatorY - indicatorSize/3);
                  ctx.lineTo(indicatorX, indicatorY + indicatorSize/2);
                  ctx.lineTo(indicatorX + indicatorSize/2, indicatorY - indicatorSize/3);
                }
                ctx.stroke();
              }
              
              // Draw label
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              ctx.fillStyle = '#333';
              ctx.fillText(label, node.x, node.y + nodeRadius + fontSize);
              
              // Draw usage count
              if (node.usage > 0) {
                ctx.font = `${fontSize * 0.8}px Sans-Serif`;
                ctx.fillStyle = '#666';
                ctx.fillText(`(${node.usage})`, node.x, node.y);
              }
              
              // Draw verified badge (only if not already showing collapse indicator)
              if (node.verified && !(layoutType === 'elk' && node.child_count > 0)) {
                ctx.fillStyle = '#10b981';
                ctx.beginPath();
                ctx.arc(node.x + nodeRadius, node.y - nodeRadius, 3, 0, 2 * Math.PI, false);
                ctx.fill();
              }
            }}
            linkDirectionalArrowLength={3}
            linkDirectionalArrowRelPos={1}
            linkCurvature={0.25}
            linkWidth={(link: any) => Math.sqrt(link.strength * 10)}
            linkColor={(link: any) => link.type === 'synonym' ? '#b2bec3' : '#dfe6e9'}
            onNodeClick={handleNodeClick}
            onNodeHover={handleNodeHover}
            enableNodeDrag={true}
            enableZoomPanInteraction={true}
            cooldownTicks={100}
            onEngineStop={() => graphRef.current?.zoomToFit(400)}
          />
        </div>

        {/* Selected node info */}
        {selectedNode && (
          <div className="absolute top-4 right-4 bg-white border rounded-lg shadow-lg p-4 max-w-xs">
            <div className="flex items-start justify-between mb-2">
              <h3 className="font-semibold">{selectedNode.name}</h3>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            
            <div className="space-y-1 text-sm">
              <div>Tag: <code className="bg-gray-100 px-1">{selectedNode.tag}</code></div>
              <div>Level: {selectedNode.level}</div>
              <div>Usage: {selectedNode.usage}</div>
              {selectedNode.child_count !== undefined && (
                <div>Children: {selectedNode.child_count}</div>
              )}
              {selectedNode.descendant_count !== undefined && (
                <div>Descendants: {selectedNode.descendant_count}</div>
              )}
              {layoutType === 'elk' && selectedNode.child_count && selectedNode.child_count > 0 && (
                <div className="flex items-center gap-2">
                  <span>Status:</span>
                  {collapsedNodes.has(String(selectedNode.id)) ? (
                    <Badge variant="destructive" className="text-xs">
                      <ChevronRight className="w-3 h-3 mr-1" />
                      Collapsed
                    </Badge>
                  ) : (
                    <Badge variant="default" className="text-xs">
                      <ChevronDown className="w-3 h-3 mr-1" />
                      Expanded
                    </Badge>
                  )}
                </div>
              )}
              {selectedNode.verified && (
                <Badge className="mt-2" variant="default">Verified</Badge>
              )}
              {selectedNode.is_synonym && (
                <Badge className="mt-2" variant="secondary">Synonym</Badge>
              )}
              {selectedNode.description && (
                <div className="mt-2 text-gray-600">{selectedNode.description}</div>
              )}
            </div>
          </div>
        )}

        {/* Legend */}
        <div className="absolute bottom-4 left-4 bg-white border rounded-lg shadow p-3">
          <div className="text-xs font-semibold mb-2">Legend</div>
          <div className="space-y-1 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-400"></div>
              <span>Root Concepts</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-teal-400"></div>
              <span>Level 1</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-400"></div>
              <span>Level 2</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-400"></div>
              <span>Level 3+</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-gray-400"></div>
              <span>Synonyms</span>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default OntologyGraph;