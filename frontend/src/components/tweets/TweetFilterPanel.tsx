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
  Calendar,
  GitBranch,
  Layers,
  ChevronDown,
  ChevronRight as ChevronRightIcon,
  X,
} from 'lucide-react'
import SemanticConceptSearch from '../concept-management/SemanticConceptSearch'
import { cn } from "@/lib/utils"
import { Concept } from '@/types/concept'
import conceptService from '@/services/conceptService'

interface AuthorFacet {
  username: string
  name?: string
  count: number
}

interface YearFacet {
  year: number
  count: number
}

interface AnnotationFacet {
  status: string
  label: string
  count: number
}

interface ConceptFacet {
  concept_id: string
  id?: string
  slug: string
  display_name: string
  count: number
  aggregate_count?: number
  entity_type?: string
  children?: ConceptFacet[]
  parents?: string[]
}

interface TweetFilterPanelProps {
  facets: {
    authors: AuthorFacet[]
    concepts: ConceptFacet[]
    years: YearFacet[]
    annotation_status: AnnotationFacet[]
  }
  hierarchyFacets: ConceptFacet[]
  selectedAuthors: string[]
  selectedConcepts: string[]
  selectedYears: number[]
  selectedAnnotationStatus: string[]
  showHierarchy: boolean
  showAllConcepts: boolean
  expandedConcepts: Set<string>
  onToggleAuthor: (username: string) => void
  onToggleYear: (year: number) => void
  onToggleConcept: (conceptId: string) => void
  onToggleConceptExpansion: (conceptId: string) => void
  onSetSelectedAuthors: (authors: string[]) => void
  onSetSelectedConcepts: (concepts: string[]) => void
  onSetSelectedYears: (years: number[]) => void
  onSetSelectedAnnotationStatus: (status: string[]) => void
  onSetShowHierarchy: (show: boolean) => void
  onSetShowAllConcepts: (show: boolean) => void
}

const INITIAL_CONCEPTS_LIMIT = 50

export default function TweetFilterPanel({
  facets,
  hierarchyFacets,
  selectedAuthors,
  selectedConcepts,
  selectedYears,
  selectedAnnotationStatus,
  showHierarchy,
  showAllConcepts,
  expandedConcepts,
  onToggleAuthor,
  onToggleYear,
  onToggleConcept,
  onToggleConceptExpansion,
  onSetSelectedAuthors,
  onSetSelectedConcepts,
  onSetSelectedYears,
  onSetSelectedAnnotationStatus,
  onSetShowHierarchy,
  onSetShowAllConcepts,
}: TweetFilterPanelProps) {

  const displayedConcepts = showHierarchy
    ? hierarchyFacets
    : (showAllConcepts ? facets.concepts : facets.concepts.slice(0, INITIAL_CONCEPTS_LIMIT))

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
              {isExpanded ? (
                <ChevronDown className="h-3 w-3" />
              ) : (
                <ChevronRightIcon className="h-3 w-3" />
              )}
            </button>
          )}
          {!hasChildren && level > 0 && <div className="w-4" />}

          <TagBadge
            variant={isSelected ? "default" : "system"}
            className="flex-1 justify-between cursor-pointer"
            style={{
              backgroundColor: isSelected ? '#93C5FD' : '#DBEAFE',
              color: '#1E40AF'
            }}
          >
            <span className="flex items-center gap-1">
              <span>{conceptService.getConceptIcon(concept as unknown as Concept)}</span>
              <span>{concept.display_name}</span>
            </span>
            <span className="ml-2 text-xs opacity-70">{concept.aggregate_count ?? concept.count}</span>
          </TagBadge>
        </div>

        {hasChildren && isExpanded && (
          <div className="mt-1">
            {concept.children!.map((child, childIndex) => (
              <React.Fragment key={`${concept.concept_id}-child-${child.concept_id}-${childIndex}`}>
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
      {/* Left Sidebar - Authors Filter */}
      <div className="lg:col-span-2">
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="h-4 w-4" />
                Authors
              </CardTitle>
              {selectedAuthors.length > 0 && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onSetSelectedAuthors([])}
                  className="h-7 px-2 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[553px] px-4 pb-4">
              {facets.authors.map(author => (
                <div
                  key={author.username}
                  className={cn(
                    "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                    selectedAuthors.includes(author.username) && "bg-blue-50 dark:bg-blue-950"
                  )}
                  onClick={() => onToggleAuthor(author.username)}
                >
                  <div className="flex items-center gap-2">
                    <Checkbox
                      checked={selectedAuthors.includes(author.username)}
                      onCheckedChange={() => onToggleAuthor(author.username)}
                    />
                    <span className="text-sm font-medium">@{author.username}</span>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {author.count}
                  </Badge>
                </div>
              ))}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Year Navigation */}
        <Card className="mt-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Years
              </CardTitle>
              {selectedYears.length > 0 && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onSetSelectedYears([])}
                  className="h-7 px-2 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-[200px] px-4 pb-4">
              {facets.years.map(year => (
                <div
                  key={year.year}
                  className={cn(
                    "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                    selectedYears.includes(year.year) && "bg-blue-50 dark:bg-blue-950"
                  )}
                  onClick={() => onToggleYear(year.year)}
                >
                  <div className="flex items-center gap-2">
                    <Checkbox
                      checked={selectedYears.includes(year.year)}
                      onCheckedChange={() => onToggleYear(year.year)}
                    />
                    <span className="text-sm font-medium">{year.year}</span>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {year.count}
                  </Badge>
                </div>
              ))}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Annotation Status Filter */}
        <Card className="mt-6">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Annotation Status
              </CardTitle>
              {selectedAnnotationStatus.length > 0 && (
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => onSetSelectedAnnotationStatus([])}
                  className="h-7 px-2 text-xs"
                >
                  <X className="h-3 w-3 mr-1" />
                  Clear
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="px-4 pb-4 space-y-2">
              {facets.annotation_status.map(status => (
                <div
                  key={status.status}
                  className={cn(
                    "flex items-center justify-between py-2 px-3 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer transition-colors",
                    selectedAnnotationStatus.includes(status.status) && "bg-blue-50 dark:bg-blue-950"
                  )}
                  onClick={() => {
                    if (selectedAnnotationStatus.includes(status.status)) {
                      onSetSelectedAnnotationStatus([])
                    } else {
                      onSetSelectedAnnotationStatus([status.status])
                    }
                  }}
                >
                  <div className="flex items-center gap-2">
                    <Checkbox
                      checked={selectedAnnotationStatus.includes(status.status)}
                      onCheckedChange={() => {
                        if (selectedAnnotationStatus.includes(status.status)) {
                          onSetSelectedAnnotationStatus([])
                        } else {
                          onSetSelectedAnnotationStatus([status.status])
                        }
                      }}
                      onClick={(e) => e.stopPropagation()}
                      className="h-4 w-4"
                    />
                    <span className="text-sm font-medium">
                      {status.label}
                    </span>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {status.count}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Right Sidebar - Tags Filter */}
      <div className="lg:col-span-3 order-last lg:order-last">
        <Card>
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
                    onClick={() => onSetSelectedConcepts([])}
                    className="h-7 px-2 text-xs"
                  >
                    <X className="h-3 w-3 mr-1" />
                    Clear
                  </Button>
                )}
                <Button
                  size="sm"
                  variant={showHierarchy ? "default" : "outline"}
                  onClick={() => onSetShowHierarchy(!showHierarchy)}
                  className="h-7 px-2"
                  title={showHierarchy ? "Show flat list" : "Show hierarchy"}
                >
                  {showHierarchy ? <GitBranch className="h-3 w-3" /> : <Layers className="h-3 w-3" />}
                </Button>
              </div>
            </div>
          </CardHeader>

          {/* Semantic Concept Search */}
          <div className="px-4 pt-4 pb-2">
            <SemanticConceptSearch
              onConceptSelect={(conceptId, _displayName) => {
                if (!selectedConcepts.includes(conceptId)) {
                  onSetSelectedConcepts([...selectedConcepts, conceptId])
                }
              }}
              selectedConcepts={selectedConcepts}
              contentTypes={['tweet']}
              placeholder="Search concepts semantically..."
              className="w-full"
            />
          </div>

          <CardContent className="p-0">
            <ScrollArea className="h-[1200px] px-4 pb-4">
              {showHierarchy ? (
                <div className="space-y-1">
                  {hierarchyFacets && hierarchyFacets.map((concept, index) => (
                    <React.Fragment key={`hierarchy-root-${concept.concept_id}-${index}`}>
                      {renderHierarchicalConcept(concept)}
                    </React.Fragment>
                  ))}
                </div>
              ) : (
                <div className="space-y-1">
                  {displayedConcepts.map((concept, index) => (
                    <div
                      key={`${concept.concept_id}-${index}`}
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
                          <span className="text-xs">{conceptService.getConceptIcon(concept as unknown as Concept)}</span>
                          <span>{concept.display_name}</span>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-xs py-0 px-1">
                        {concept.count}
                      </Badge>
                    </div>
                  ))}

                  {/* Show More/Less button */}
                  {!showHierarchy && facets.concepts.length > INITIAL_CONCEPTS_LIMIT && (
                    <div className="mt-3 pt-3 border-t">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onSetShowAllConcepts(!showAllConcepts)}
                        className="w-full justify-center text-xs"
                      >
                        {showAllConcepts ? (
                          <>
                            <ChevronDown className="h-3 w-3 mr-1 rotate-180" />
                            Show Less
                          </>
                        ) : (
                          <>
                            <ChevronDown className="h-3 w-3 mr-1" />
                            Show {facets.concepts.length - INITIAL_CONCEPTS_LIMIT} More Concepts
                          </>
                        )}
                      </Button>
                    </div>
                  )}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </>
  )
}
