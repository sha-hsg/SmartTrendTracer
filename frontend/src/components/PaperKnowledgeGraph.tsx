import React, { useState, useEffect, useRef, useCallback } from 'react'
import ForceGraph2D from 'react-force-graph-2d'
import axios from 'axios'
import {
  Network,
  FileText,
  Users,
  GitBranch,
  Loader2,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RefreshCw,
  Info,
  X
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Input } from '@/components/ui/input'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

interface GraphNode {
  id: string
  label: string
  type: string
  data: any
  x?: number
  y?: number
  color?: string
  size?: number
}

interface GraphEdge {
  source: string
  target: string
  type: string
  label?: string
  weight?: number
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
  statistics: {
    total_nodes: number
    total_edges: number
    paper_nodes: number
    author_nodes: number
    citation_edges: number
    authorship_edges: number
  }
}

interface PaperKnowledgeGraphProps {
  paperId?: number
  onNodeClick?: (node: any) => void
}

const PaperKnowledgeGraph: React.FC<PaperKnowledgeGraphProps> = ({ 
  paperId, 
  onNodeClick 
}) => {
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [zoom, setZoom] = useState(1)
  const graphRef = useRef<any>()

  const fetchGraphData = async () => {
    setLoading(true)
    setError(null)
    
    try {
      const params = paperId ? { paper_id: paperId } : {}
      const response = await axios.get('http://localhost:8000/api/papers/advanced/knowledge-graph', {
        params
      })
      
      // Process nodes for visualization
      const processedNodes = response.data.nodes.map((node: GraphNode) => ({
        ...node,
        color: getNodeColor(node.type),
        size: getNodeSize(node)
      }))
      
      setGraphData({
        ...response.data,
        nodes: processedNodes
      })
    } catch (err) {
      setError('Failed to load knowledge graph')
      console.error('Error fetching graph:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchGraphData()
  }, [paperId])

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'center':
        return '#ef4444' // red
      case 'paper':
        return '#3b82f6' // blue
      case 'reference':
        return '#10b981' // green
      case 'citation':
        return '#f59e0b' // orange
      case 'related':
        return '#8b5cf6' // purple
      case 'author':
        return '#ec4899' // pink
      default:
        return '#6b7280' // gray
    }
  }

  const getNodeSize = (node: GraphNode) => {
    if (node.type === 'center') return 12
    if (node.type === 'author') return 8 + (node.data?.paper_count || 0)
    return 6 + Math.min(10, (node.data?.citations || 0) / 10)
  }

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node)
    if (onNodeClick) {
      onNodeClick(node)
    }
  }, [onNodeClick])

  const handleZoomIn = () => {
    if (graphRef.current) {
      const newZoom = zoom * 1.2
      setZoom(newZoom)
      graphRef.current.zoom(newZoom)
    }
  }

  const handleZoomOut = () => {
    if (graphRef.current) {
      const newZoom = zoom / 1.2
      setZoom(newZoom)
      graphRef.current.zoom(newZoom)
    }
  }

  const handleCenterGraph = () => {
    if (graphRef.current) {
      graphRef.current.zoomToFit(400)
    }
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </CardContent>
      </Card>
    )
  }

  if (error || !graphData) {
    return (
      <Card>
        <CardContent className="p-6">
          <Alert variant="destructive">
            <AlertDescription>{error || 'No data available'}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-[700px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Network className="h-5 w-5" />
              Paper Knowledge Graph
            </CardTitle>
            <CardDescription>
              Interactive visualization of paper relationships and citations
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomIn}
              title="Zoom in"
            >
              <ZoomIn className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleZoomOut}
              title="Zoom out"
            >
              <ZoomOut className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleCenterGraph}
              title="Center graph"
            >
              <Maximize2 className="h-4 w-4" />
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={fetchGraphData}
              title="Refresh"
            >
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="relative h-[calc(100%-120px)]">
        {/* Statistics Bar */}
        <div className="absolute top-2 left-2 z-10 bg-white/90 backdrop-blur p-2 rounded-lg shadow-sm">
          <div className="flex items-center gap-4 text-xs">
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-blue-500 rounded-full" />
              <span>{graphData.statistics.paper_nodes} Papers</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-pink-500 rounded-full" />
              <span>{graphData.statistics.author_nodes} Authors</span>
            </div>
            <div className="flex items-center gap-1">
              <GitBranch className="h-3 w-3" />
              <span>{graphData.statistics.citation_edges} Citations</span>
            </div>
          </div>
        </div>

        {/* Legend */}
        <div className="absolute bottom-2 left-2 z-10 bg-white/90 backdrop-blur p-2 rounded-lg shadow-sm">
          <div className="text-xs space-y-1">
            <div className="font-semibold mb-1">Node Types:</div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <span>Center Paper</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span>References</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-orange-500 rounded-full" />
              <span>Citations</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-purple-500 rounded-full" />
              <span>Related</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-3 h-3 bg-pink-500 rounded-full" />
              <span>Authors</span>
            </div>
          </div>
        </div>

        {/* Graph */}
        <ForceGraph2D
          ref={graphRef}
          graphData={{
            nodes: graphData.nodes,
            links: graphData.edges
          }}
          nodeId="id"
          nodeLabel="label"
          nodeColor="color"
          nodeRelSize={1}
          nodeVal={(node: any) => node.size || 5}
          linkDirectionalArrowLength={3}
          linkDirectionalArrowRelPos={1}
          linkCurvature={0.25}
          linkColor={() => '#9ca3af'}
          linkWidth={(link: any) => link.weight || 1}
          onNodeClick={handleNodeClick}
          onNodeHover={(node: any) => {
            document.body.style.cursor = node ? 'pointer' : 'default'
          }}
          enableZoomInteraction={true}
          enablePanInteraction={true}
        />

        {/* Node Details Dialog */}
        <Dialog open={!!selectedNode} onOpenChange={() => setSelectedNode(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {selectedNode?.type === 'author' ? 'Author Details' : 'Paper Details'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <span className="text-sm font-medium">Name/Title:</span>
                <p className="text-sm text-gray-700">{selectedNode?.label}</p>
              </div>
              {selectedNode?.data?.full_title && (
                <div>
                  <span className="text-sm font-medium">Full Title:</span>
                  <p className="text-sm text-gray-700">{selectedNode.data.full_title}</p>
                </div>
              )}
              {selectedNode?.data?.year && (
                <div>
                  <span className="text-sm font-medium">Year:</span>
                  <p className="text-sm text-gray-700">{selectedNode.data.year}</p>
                </div>
              )}
              {selectedNode?.data?.citations !== undefined && (
                <div>
                  <span className="text-sm font-medium">Citations:</span>
                  <p className="text-sm text-gray-700">{selectedNode.data.citations}</p>
                </div>
              )}
              {selectedNode?.data?.paper_count && (
                <div>
                  <span className="text-sm font-medium">Papers:</span>
                  <p className="text-sm text-gray-700">{selectedNode.data.paper_count}</p>
                </div>
              )}
              {selectedNode?.data?.arxiv_id && (
                <div>
                  <span className="text-sm font-medium">ArXiv ID:</span>
                  <p className="text-sm text-gray-700">{selectedNode.data.arxiv_id}</p>
                </div>
              )}
              <div className="flex items-center gap-2 mt-4">
                <Badge variant="outline">
                  {selectedNode?.type}
                </Badge>
                {selectedNode?.id?.startsWith('paper_') && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => {
                      const id = selectedNode.id.replace('paper_', '')
                      console.log('View paper', id)
                    }}
                  >
                    View Paper
                  </Button>
                )}
              </div>
            </div>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  )
}

export default PaperKnowledgeGraph