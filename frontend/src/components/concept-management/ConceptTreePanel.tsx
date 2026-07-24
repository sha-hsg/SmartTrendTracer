import { useMemo } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  ChevronRight,
  ChevronDown,
  Search,
  RefreshCw,
  Loader2,
} from 'lucide-react'

interface ConceptTreeNode {
  id: string
  slug: string
  name: string
  display_name: string
  description?: string
  parent_id?: string | null
  parents?: string[]
  entity_type?: string
  icon?: string
  color?: string
  created_at?: string
  created_by?: string
  auto_generated?: boolean
  verified?: boolean
  quality_score?: number

  children?: ConceptTreeNode[]
  children_details?: ConceptTreeNode[]
  expanded?: boolean
  usage_stats?: {
    tweet_count: number
    article_count: number
    paper_count: number
    total_count: number
  }
}

interface ConceptTreePanelProps {
  treeData: ConceptTreeNode[]
  selectedConceptId: string | null
  searchQuery: string
  expandedNodes: Set<string>
  loading: boolean
  onSearchChange: (query: string) => void
  onToggleNode: (nodeId: string) => void
  onSelectConcept: (concept: ConceptTreeNode) => void
  onRefresh: () => void
}

export default function ConceptTreePanel({
  treeData,
  selectedConceptId,
  searchQuery,
  expandedNodes,
  loading,
  onSearchChange,
  onToggleNode,
  onSelectConcept,
  onRefresh,
}: ConceptTreePanelProps) {
  const filteredTree = useMemo(() => {
    if (!searchQuery) return treeData

    const filterNodes = (nodes: ConceptTreeNode[]): ConceptTreeNode[] => {
      return nodes.reduce((acc: ConceptTreeNode[], node) => {
        const matchesSearch = node.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                             node.slug.toLowerCase().includes(searchQuery.toLowerCase())

        const children = node.children || node.children_details || []
        const filteredChildren = children.length > 0 ? filterNodes(children) : []

        if (matchesSearch || filteredChildren.length > 0) {
          acc.push({
            ...node,
            children: filteredChildren,
            children_details: filteredChildren,
            expanded: true
          })
        }

        return acc
      }, [])
    }

    return filterNodes(treeData)
  }, [treeData, searchQuery])

  const renderTreeNode = (node: ConceptTreeNode, level: number = 0) => {
    const isExpanded = expandedNodes.has(node.id)
    const children = node.children || node.children_details || []
    const hasChildren = children.length > 0
    const isSelected = selectedConceptId === node.id

    return (
      <div key={node.id}>
        <div
          className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer hover:bg-accent ${
            isSelected ? 'bg-accent' : ''
          }`}
          style={{ paddingLeft: `${level * 20 + 8}px` }}
          onClick={() => onSelectConcept(node)}
        >
          {hasChildren && (
            <button
              className="p-0.5"
              onClick={(e) => {
                e.stopPropagation()
                onToggleNode(node.id)
              }}
            >
              {isExpanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRight className="h-3 w-3" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-4" />}

          {node.entity_type === 'person' && <span>👤</span>}
          {node.entity_type === 'organisation' && <span>🏢</span>}
          {node.entity_type === 'location' && <span>📍</span>}

          <span className="text-sm font-medium">{node.display_name}</span>

          {node.usage_stats && node.usage_stats.total_count > 0 && (
            <Badge variant="outline" className="ml-auto text-xs">
              {node.usage_stats.total_count}
            </Badge>
          )}
        </div>

        {isExpanded && hasChildren && (
          <div>
            {children.map(child => renderTreeNode(child, level + 1))}
          </div>
        )}
      </div>
    )
  }

  return (
    <Card className="lg:col-span-1">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Hierarchy</CardTitle>
          <Button size="sm" variant="ghost" onClick={onRefresh}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search concepts..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-8"
          />
        </div>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[500px]">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-6 w-6 animate-spin" />
            </div>
          ) : (
            <div className="space-y-1">
              {filteredTree.map(node => renderTreeNode(node))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

export type { ConceptTreeNode }
