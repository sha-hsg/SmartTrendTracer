import { useEffect, useState, useRef, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize2,
  Download,
  RefreshCw,
  Info,
  Layers,
  Loader2
} from 'lucide-react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

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
}

export default function ConceptGraph() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showLabels, setShowLabels] = useState(true);
  const [showSynonyms, setShowSynonyms] = useState(false);
  const [linkDistance, setLinkDistance] = useState([50]);
  const [nodeSize, setNodeSize] = useState([1]);
  const [layoutType, setLayoutType] = useState<'force' | 'hierarchical'>('force');
  const [highlightNodes, setHighlightNodes] = useState(new Set());
  const [highlightLinks, setHighlightLinks] = useState(new Set());
  const [hoverNode, setHoverNode] = useState<GraphNode | null>(null);
  
  const fgRef = useRef<any>();

  useEffect(() => {
    fetchGraphData();
  }, [showSynonyms]);

  const fetchGraphData = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('/api/ontology/graph', {
        params: { include_synonyms: showSynonyms }
      });
      
      const { nodes, links } = response.data;
      
      // Assign colors and sizes based on hierarchy level and usage
      const processedNodes = nodes.map((node: any) => ({
        ...node,
        id: node.id,
        name: node.display_name || node.name,
        tag: node.slug,
        level: node.hierarchy_level || 0,
        usage: node.usage_count || 0,
        size: Math.max(3, Math.min(15, (node.usage_count || 0) / 10 + 5)),
        color: getNodeColor(node),
        description: node.description,
        verified: node.verified,
        quality_score: node.quality_score,
        child_count: node.child_count || 0,
        descendant_count: node.descendant_count || 0,
        is_synonym: node.is_synonym || false
      }));

      setGraphData({ 
        nodes: processedNodes, 
        links: links 
      });
    } catch (err: any) {
      console.error('Error fetching graph data:', err);
      setError(err.response?.data?.detail || 'Failed to load graph data');
    } finally {
      setLoading(false);
    }
  };

  const getNodeColor = (node: any) => {
    if (node.is_synonym) return '#9CA3AF'; // Gray for synonyms
    if (node.entity_type === 'person') return '#3B82F6'; // Blue for people
    if (node.entity_type === 'organisation') return '#10B981'; // Green for orgs
    if (node.entity_type === 'location') return '#F59E0B'; // Amber for locations
    if (node.hierarchy_level === 0) return '#8B5CF6'; // Purple for root
    if (node.hierarchy_level === 1) return '#EC4899'; // Pink for level 1
    if (node.hierarchy_level === 2) return '#14B8A6'; // Teal for level 2
    return '#6B7280'; // Default gray
  };

  const handleNodeClick = useCallback((node: GraphNode) => {
    setSelectedNode(node);
    
    // Highlight connected nodes
    const connectedNodeIds = new Set();
    const connectedLinkIds = new Set();
    
    graphData.links.forEach(link => {
      if (link.source === node.id || (link.source as any).id === node.id) {
        connectedNodeIds.add(link.target);
        connectedNodeIds.add((link.target as any).id);
        connectedLinkIds.add(link);
      }
      if (link.target === node.id || (link.target as any).id === node.id) {
        connectedNodeIds.add(link.source);
        connectedNodeIds.add((link.source as any).id);
        connectedLinkIds.add(link);
      }
    });
    
    setHighlightNodes(connectedNodeIds);
    setHighlightLinks(connectedLinkIds);
  }, [graphData]);

  const handleNodeHover = useCallback((node: GraphNode | null) => {
    setHoverNode(node);
  }, []);

  const handleZoomIn = () => {
    if (fgRef.current) {
      const currentZoom = fgRef.current.zoom();
      fgRef.current.zoom(currentZoom * 1.2, 300);
    }
  };

  const handleZoomOut = () => {
    if (fgRef.current) {
      const currentZoom = fgRef.current.zoom();
      fgRef.current.zoom(currentZoom * 0.8, 300);
    }
  };

  const handleZoomFit = () => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(400, 50);
    }
  };

  const handleExport = () => {
    if (fgRef.current) {
      const canvas = fgRef.current.canvas();
      if (canvas) {
        const dataURL = canvas.toDataURL('image/png');
        const link = document.createElement('a');
        link.download = 'concept-graph.png';
        link.href = dataURL;
        link.click();
      }
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[600px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      {/* Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-5 w-5" />
            Concept Visualization Graph
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Layout Type */}
            <div className="space-y-2">
              <Label>Layout Type</Label>
              <Select value={layoutType} onValueChange={(value: any) => setLayoutType(value)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="force">Force-Directed</SelectItem>
                  <SelectItem value="hierarchical">Hierarchical</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Display Options */}
            <div className="space-y-2">
              <Label>Display Options</Label>
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-labels"
                  checked={showLabels}
                  onCheckedChange={setShowLabels}
                />
                <Label htmlFor="show-labels">Show Labels</Label>
              </div>
              <div className="flex items-center space-x-2">
                <Switch
                  id="show-synonyms"
                  checked={showSynonyms}
                  onCheckedChange={setShowSynonyms}
                />
                <Label htmlFor="show-synonyms">Include Synonyms</Label>
              </div>
            </div>

            {/* Link Distance */}
            <div className="space-y-2">
              <Label>Link Distance: {linkDistance[0]}</Label>
              <Slider
                value={linkDistance}
                onValueChange={setLinkDistance}
                min={10}
                max={200}
                step={10}
              />
            </div>

            {/* Node Size */}
            <div className="space-y-2">
              <Label>Node Size Multiplier: {nodeSize[0]}x</Label>
              <Slider
                value={nodeSize}
                onValueChange={setNodeSize}
                min={0.5}
                max={3}
                step={0.1}
              />
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 mt-4">
            <Button variant="outline" size="sm" onClick={handleZoomIn}>
              <ZoomIn className="h-4 w-4 mr-1" />
              Zoom In
            </Button>
            <Button variant="outline" size="sm" onClick={handleZoomOut}>
              <ZoomOut className="h-4 w-4 mr-1" />
              Zoom Out
            </Button>
            <Button variant="outline" size="sm" onClick={handleZoomFit}>
              <Maximize2 className="h-4 w-4 mr-1" />
              Fit to View
            </Button>
            <Button variant="outline" size="sm" onClick={fetchGraphData}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
            <Button variant="outline" size="sm" onClick={handleExport}>
              <Download className="h-4 w-4 mr-1" />
              Export PNG
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Graph and Details */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Graph */}
        <Card className="lg:col-span-3">
          <CardContent className="p-0">
            <div className="border rounded-lg" style={{ height: '600px' }}>
                <ForceGraph2D
                ref={fgRef}
                graphData={graphData}
                nodeLabel={showLabels ? 'name' : undefined}
                nodeColor="color"
                nodeRelSize={nodeSize[0]}
                nodeVal={(node: any) => node.size * nodeSize[0]}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.005}
                // Note: linkDistance is set via d3Force('link').distance()
                onNodeClick={handleNodeClick}
                onNodeHover={handleNodeHover}
                nodeCanvasObject={(node: any, ctx, globalScale) => {
                  // Custom node rendering
                  const label = node.name;
                  const fontSize = 12 / globalScale;
                  ctx.font = `${fontSize}px Sans-Serif`;
                  
                  // Draw node
                  ctx.beginPath();
                  ctx.arc(node.x, node.y, node.size * nodeSize[0], 0, 2 * Math.PI);
                  ctx.fillStyle = node === hoverNode || highlightNodes.has(node.id) 
                    ? node.color 
                    : `${node.color}88`;
                  ctx.fill();
                  
                  // Draw label if enabled
                  if (showLabels) {
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    ctx.fillStyle = '#000';
                    ctx.fillText(label, node.x, node.y + node.size * nodeSize[0] + fontSize);
                  }
                }}
                linkCanvasObjectMode={() => 'after'}
                linkCanvasObject={(link: any, ctx) => {
                  const start = link.source;
                  const end = link.target;
                  
                  // Draw link
                  ctx.beginPath();
                  ctx.moveTo(start.x, start.y);
                  ctx.lineTo(end.x, end.y);
                  ctx.strokeStyle = highlightLinks.has(link) ? '#3B82F6' : '#D1D5DB';
                  ctx.lineWidth = highlightLinks.has(link) ? 2 : 1;
                  ctx.stroke();
                }}
              />
            </div>
          </CardContent>
        </Card>

        {/* Selected Node Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">
              <Info className="h-4 w-4 inline mr-2" />
              Node Details
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedNode ? (
              <div className="space-y-3">
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Name</p>
                  <p className="font-medium">{selectedNode.name}</p>
                </div>
                
                {selectedNode.description && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Description</p>
                    <p className="text-sm">{selectedNode.description}</p>
                  </div>
                )}
                
                <div>
                  <p className="text-sm font-medium text-muted-foreground">Statistics</p>
                  <div className="space-y-1 mt-1">
                    <Badge variant="outline">
                      Usage: {selectedNode.usage}
                    </Badge>
                    <Badge variant="outline">
                      Children: {selectedNode.child_count}
                    </Badge>
                    <Badge variant="outline">
                      Descendants: {selectedNode.descendant_count}
                    </Badge>
                  </div>
                </div>
                
                {selectedNode.verified && (
                  <Badge className="bg-green-500">Verified</Badge>
                )}
                
                {selectedNode.quality_score !== undefined && (
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">Quality Score</p>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-500 h-2 rounded-full"
                          style={{ width: `${selectedNode.quality_score * 100}%` }}
                        />
                      </div>
                      <span className="text-sm">
                        {(selectedNode.quality_score * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">
                Click on a node to view details
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Graph Statistics */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Graph Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Nodes</p>
              <p className="text-2xl font-bold">{graphData.nodes.length}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Links</p>
              <p className="text-2xl font-bold">{graphData.links.length}</p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Root Nodes</p>
              <p className="text-2xl font-bold">
                {graphData.nodes.filter(n => n.level === 0).length}
              </p>
            </div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Synonym Nodes</p>
              <p className="text-2xl font-bold">
                {graphData.nodes.filter(n => n.is_synonym).length}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}