import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import {
  ChevronRight,
  ChevronDown,
  Search,
  Tag,
} from 'lucide-react'
import { cn } from "@/lib/utils"
import type { TagConcept } from './types'

interface ConceptTreeProps {
  tree: TagConcept[]
  selectedConceptId: string | null
  expandedNodes: Set<string>
  searchTerm: string
  onSearchChange: (value: string) => void
  onSelectConcept: (conceptId: string) => void
  onToggleNode: (nodeId: string) => void
}

export default function ConceptTree({
  tree,
  selectedConceptId,
  expandedNodes,
  searchTerm,
  onSearchChange,
  onSelectConcept,
  onToggleNode,
}: ConceptTreeProps) {

  const getEntityIcon = (entityType?: string) => {
    switch(entityType) {
      case 'person': return '👤'
      case 'organisation': return '🏢'
      case 'location': return '📍'
      case 'model': return '🤖'
      case 'dataset': return '📊'
      case 'method': return '⚙️'
      default: return null
    }
  }

  const renderTreeNode = (node: TagConcept, level: number = 0, _isLast: boolean = false, parentPath: string = "") => {
    const isExpanded = expandedNodes.has(node.id)
    const hasChildren = node.children && node.children.length > 0
    const matchesSearch = !searchTerm ||
      node.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.tag.toLowerCase().includes(searchTerm.toLowerCase()) ||
      node.synonyms.some(s => s.toLowerCase().includes(searchTerm.toLowerCase()))

    if (!matchesSearch && !hasChildren) return null

    const entityIcon = getEntityIcon(node.entity_type)

    return (
      <div key={node.id} className="relative">
        {/* Tree lines for visual hierarchy */}
        {level > 0 && (
          <div
            className="absolute left-0 top-0 h-full w-px bg-border"
            style={{ left: `${(level - 1) * 24 + 16}px` }}
          />
        )}
        {level > 0 && (
          <div
            className="absolute top-3 h-px bg-border"
            style={{
              left: `${(level - 1) * 24 + 16}px`,
              width: '12px'
            }}
          />
        )}

        <div
          className={cn(
            "flex items-center gap-2 px-2 py-1.5 rounded-md hover:bg-accent cursor-pointer transition-colors relative",
            selectedConceptId === node.id && "bg-accent"
          )}
          style={{ paddingLeft: `${level * 24 + 8}px` }}
          onClick={() => onSelectConcept(node.id)}
        >
          {hasChildren && (
            <button
              className="p-0.5 hover:bg-background rounded z-10"
              onClick={(e) => {
                e.stopPropagation()
                onToggleNode(node.id)
              }}
            >
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
          )}
          {!hasChildren && <div className="w-5" />}

          {entityIcon ? (
            <span className="text-base" title={node.entity_type}>{entityIcon}</span>
          ) : (
            <Tag className="w-4 h-4 text-muted-foreground" />
          )}

          <div className="flex-1 flex items-center gap-2">
            <span className="font-medium">{node.display_name}</span>
            {level === 0 && (
              <Badge variant="default" className="text-xs">
                Root
              </Badge>
            )}
            {node.child_count > 0 && (
              <Badge variant="secondary" className="text-xs">
                {node.child_count} {node.child_count === 1 ? 'child' : 'children'}
              </Badge>
            )}
            {node.synonyms.length > 0 && (
              <Tooltip>
                <TooltipTrigger>
                  <Badge variant="outline" className="text-xs">
                    {node.synonyms.length} synonyms
                  </Badge>
                </TooltipTrigger>
                <TooltipContent>
                  <div className="text-xs">
                    {node.synonyms.join(', ')}
                  </div>
                </TooltipContent>
              </Tooltip>
            )}
          </div>
        </div>

        {isExpanded && hasChildren && (
          <div className="relative">
            {node.children!.map((child, index) =>
              renderTreeNode(
                child,
                level + 1,
                index === node.children!.length - 1,
                `${parentPath}${node.id}/`
              )
            )}
          </div>
        )}
      </div>
    )
  }

  return (
    <Card className="lg:col-span-1">
      <CardHeader>
        <CardTitle className="text-lg">Concept Hierarchy</CardTitle>
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search tags..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-8"
          />
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <ScrollArea className="h-[600px] px-4 pb-4">
          {tree.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Tag className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No tags in ontology</p>
            </div>
          ) : (
            tree.map(node => renderTreeNode(node))
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}
