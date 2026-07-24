import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import { Checkbox } from "@/components/ui/checkbox"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  User,
  Tag,
  X,
  GitBranch,
  Layers,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
} from 'lucide-react'
import { cn } from "@/lib/utils"
import { Concept } from '@/types/concept'
import conceptService from '@/services/conceptService'

interface AuthorFacet {
  name: string
  count: number
}

interface ConceptFacet extends Concept {
  count: number
  children?: ConceptFacet[]
}

interface ArticleFilterPanelProps {
  facets: { authors: AuthorFacet[]; concepts: ConceptFacet[] }
  selectedAuthors: string[]
  selectedConcepts: string[]
  showHierarchy: boolean
  hierarchyFacets: ConceptFacet[]
  expandedConcepts: Set<string>
  onToggleAuthor: (authorName: string) => void
  onClearAuthors: () => void
  onToggleConcept: (conceptId: string) => void
  onClearConcepts: () => void
  onToggleHierarchy: () => void
  onToggleConceptExpansion: (conceptId: string) => void
  onShowAuthorManagement: () => void
}

export default function ArticleFilterPanel({
  facets,
  selectedAuthors,
  selectedConcepts,
  showHierarchy,
  hierarchyFacets,
  expandedConcepts,
  onToggleAuthor,
  onClearAuthors,
  onToggleConcept,
  onClearConcepts,
  onToggleHierarchy,
  onToggleConceptExpansion,
  onShowAuthorManagement,
}: ArticleFilterPanelProps) {
  const displayedConcepts = showHierarchy ? hierarchyFacets : facets.concepts

  const renderHierarchicalConcept = (concept: ConceptFacet, level: number = 0) => {
    const isExpanded = expandedConcepts.has(concept.concept_id)
    const hasChildren = concept.children && concept.children.length > 0
    const isSelected = selectedConcepts.includes(concept.concept_id)

    return (
      <div className="w-full">
        <div
          className={cn(
            "flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
            isSelected && "bg-blue-50 dark:bg-blue-950",
            level > 0 && "ml-4"
          )}
          onClick={() => onToggleConcept(concept.concept_id)}
        >
          {hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation()
                onToggleConceptExpansion(concept.concept_id)
              }}
              className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded"
            >
              {isExpanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRightIcon className="h-3 w-3" />}
            </button>
          )}
          {!hasChildren && <div className="w-4" />}

          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onToggleConcept(concept.concept_id)}
            onClick={(e) => e.stopPropagation()}
            className="h-3 w-3"
          />

          <TagBadge
            variant={isSelected ? "default" : "system"}
            className="flex-1 justify-between cursor-pointer"
            style={{
              backgroundColor: isSelected ? '#93C5FD' : '#DBEAFE',
              color: '#1E40AF'
            }}
          >
            <span className="flex items-center gap-1">
              <span>{conceptService.getConceptIcon(concept)}</span>
              <span>{concept.display_name}</span>
            </span>
            <Badge variant="secondary" className="ml-auto text-xs py-0 px-1">
              {concept.count}
            </Badge>
          </TagBadge>
        </div>

        {hasChildren && isExpanded && (
          <div className="ml-2">
            {concept.children!.map((child, childIndex) => (
              <React.Fragment key={child.concept_id || `child-${level}-${childIndex}`}>
                {renderHierarchicalConcept(child, level + 1)}
              </React.Fragment>
            ))}
          </div>
        )}
      </div>
    )
  }

  return (
    <>
      {/* Authors Filter - Left */}
      <div className="lg:col-span-2">
        <Card className="sticky top-4">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="h-4 w-4" />
                Authors
              </CardTitle>
              <div className="flex gap-1">
                {selectedAuthors.length > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={onClearAuthors}
                    className="h-7 px-2 text-xs"
                  >
                    <X className="h-3 w-3 mr-1" />
                    Clear
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={onShowAuthorManagement}
                  className="h-7 px-2 text-xs"
                  title="Manage Authors"
                >
                  ⚙️
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[600px] px-4 pb-4">
              <div className="space-y-1">
                {facets.authors.map((author, index) => (
                  <div
                    key={`${author.name}-${index}`}
                    className={cn(
                      "flex items-center justify-between py-2 px-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                      selectedAuthors.includes(author.name) && "bg-blue-50 dark:bg-blue-950"
                    )}
                    onClick={() => onToggleAuthor(author.name)}
                  >
                    <div className="flex items-center gap-2">
                      <Checkbox
                        checked={selectedAuthors.includes(author.name)}
                        onCheckedChange={() => onToggleAuthor(author.name)}
                        onClick={(e) => e.stopPropagation()}
                      />
                      <span className="text-sm font-medium">{author.name}</span>
                    </div>
                    <Badge variant="secondary" className="text-xs">
                      {author.count}
                    </Badge>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>
      </div>

      {/* Concepts Filter - Right */}
      <div className="lg:col-span-3 order-last lg:order-last">
        <Card className="sticky top-4">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Concepts
              </CardTitle>
              <div className="flex gap-1">
                {selectedConcepts.length > 0 && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={onClearConcepts}
                    className="h-7 px-2 text-xs"
                  >
                    <X className="h-3 w-3 mr-1" />
                    Clear
                  </Button>
                )}
                <Button
                  size="sm"
                  variant={showHierarchy ? "default" : "outline"}
                  onClick={onToggleHierarchy}
                  className="h-7 px-2"
                  title={showHierarchy ? "Show flat list" : "Show hierarchy"}
                >
                  {showHierarchy ? <GitBranch className="h-3 w-3" /> : <Layers className="h-3 w-3" />}
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[1200px] px-4 pb-4">
              {showHierarchy ? (
                <div className="space-y-1">
                  {hierarchyFacets && hierarchyFacets.map((concept, index) => (
                    <React.Fragment key={concept.concept_id || `hierarchy-${index}`}>
                      {renderHierarchicalConcept(concept)}
                    </React.Fragment>
                  ))}
                </div>
              ) : (
                <div className="space-y-1">
                  {displayedConcepts.map(concept => (
                    <div
                      key={concept.concept_id}
                      className={cn(
                        "flex items-center justify-between py-1 px-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                        selectedConcepts.includes(concept.concept_id) && "bg-blue-50 dark:bg-blue-950"
                      )}
                      onClick={() => onToggleConcept(concept.concept_id)}
                    >
                      <div className="flex items-center gap-2">
                        <Checkbox
                          checked={selectedConcepts.includes(concept.concept_id)}
                          onCheckedChange={() => onToggleConcept(concept.concept_id)}
                          onClick={(e) => e.stopPropagation()}
                          className="h-3 w-3"
                        />
                        <div
                          className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded-md text-xs font-medium"
                          style={{
                            backgroundColor: selectedConcepts.includes(concept.concept_id) ? '#93C5FD' : '#DBEAFE',
                            color: '#1E40AF'
                          }}
                        >
                          <span className="text-xs">{conceptService.getConceptIcon(concept)}</span>
                          <span>{concept.display_name}</span>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs py-0 px-1">
                        {concept.count}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </>
  )
}
