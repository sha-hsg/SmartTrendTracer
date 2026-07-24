import React from 'react'
import {
  Search,
  Tag as TagIcon,
  Hash,
  Loader2,
  X,
  Layers,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Checkbox } from '@/components/ui/checkbox'

interface ConceptsSidebarProps {
  facets: any
  loadingFacets: boolean
  selectedTags: Set<string>
  conceptSearch: string
  showHierarchy: boolean
  setConceptSearch: (v: string) => void
  setShowHierarchy: (v: boolean) => void
  setSelectedTags: (s: Set<string>) => void
  setCurrentPage: (v: number) => void
  toggleFacetValue: (type: string, value: string | number) => void
}

const ConceptsSidebar: React.FC<ConceptsSidebarProps> = ({
  facets,
  loadingFacets,
  selectedTags,
  conceptSearch,
  showHierarchy,
  setConceptSearch,
  setShowHierarchy,
  setSelectedTags,
  setCurrentPage,
  toggleFacetValue,
}) => (
  <div className="w-80 bg-white dark:bg-gray-950 border-l border-gray-200 dark:border-gray-700 overflow-y-auto">
    <div className="p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <TagIcon className="h-5 w-5 text-gray-700 dark:text-gray-300" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Concepts</h2>
        </div>
        <div className="flex items-center gap-1">
          {selectedTags.size > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setSelectedTags(new Set())
                setCurrentPage(1)
              }}
              className="h-7 px-2 text-xs"
            >
              <X className="h-3 w-3 mr-1" />
              Clear
            </Button>
          )}
          <Button
            size="sm"
            variant={showHierarchy ? "default" : "outline"}
            onClick={() => setShowHierarchy(!showHierarchy)}
            className="h-7 px-2"
            title={showHierarchy ? "Show flat list" : "Show hierarchy"}
          >
            {showHierarchy ? <Layers className="h-3 w-3" /> : <Hash className="h-3 w-3" />}
          </Button>
        </div>
      </div>

      {/* Semantic Concept Search */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            type="text"
            placeholder="Search concepts semantically..."
            value={conceptSearch}
            onChange={(e) => setConceptSearch(e.target.value)}
            className="pl-9 pr-3 h-9 text-sm"
          />
        </div>
      </div>

      <div className="space-y-2">
        {loadingFacets ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400 dark:text-gray-500" />
          </div>
        ) : facets && facets.concepts && facets.concepts.length > 0 ? (
          <ScrollArea className="h-[calc(100vh-240px)]">
            <div className="space-y-1 pr-4">
              {facets.concepts
                .filter((concept: any) =>
                  !conceptSearch ||
                  concept.display_name.toLowerCase().includes(conceptSearch.toLowerCase())
                )
                .map((concept: any, index: number) => (
                  <label
                    key={concept.concept_id || concept.id || `${concept.slug}-${index}`}
                    className="flex items-start gap-2 px-3 py-1 hover:bg-blue-50 dark:bg-blue-950 cursor-pointer rounded-lg transition-colors"
                  >
                    <Checkbox
                      checked={selectedTags.has(concept.concept_id || concept.slug)}
                      onCheckedChange={() => toggleFacetValue('tag', concept.concept_id || concept.slug)}
                      className="mt-0.5"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <span className="text-sm text-blue-800 bg-blue-50 dark:bg-blue-950 px-2 py-0.5 rounded break-words"
                          title={concept.display_name}>
                          {concept.display_name}
                        </span>
                        <Badge
                          variant="outline"
                          className="text-xs shrink-0 bg-blue-100 text-blue-700 border-blue-200">
                          {concept.count}
                        </Badge>
                      </div>
                    </div>
                  </label>
                ))}
            </div>
          </ScrollArea>
        ) : (
          <div className="text-sm text-gray-400 text-center py-8">
            No concepts found
          </div>
        )}
      </div>
    </div>
  </div>
)

export default ConceptsSidebar
