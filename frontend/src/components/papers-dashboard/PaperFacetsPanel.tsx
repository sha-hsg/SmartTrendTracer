/**
 * PaperFacetsPanel - Left sidebar with all faceted filters.
 *
 * Renders: Authors, Years, Conferences, Institutions, Processors,
 * Special Filters (flagged, missing data), and Rating filters.
 */
import React from 'react'
import {
  Users,
  Calendar,
  Building2,
  Filter,
  ChevronDown,
  ChevronRight,
  X,
  Loader2,
  Cpu,
  GraduationCap,
  Flag,
  BookOpen,
  BarChart3,
  FilterX,
  Star,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Checkbox } from '@/components/ui/checkbox'
import type { Facets } from './types'

interface PaperFacetsPanelProps {
  facets: Facets | null
  loadingFacets: boolean
  activeFilterCount: number

  // Selected filter values
  selectedAuthors: Set<string>
  selectedYears: Set<number>
  selectedConferences: Set<string>
  selectedAffiliations: Set<string>
  selectedProcessors: Set<string>

  // Special filters
  showFlagged: boolean | null
  showNoProcessor: boolean
  showNoYear: boolean
  showNoConference: boolean
  showNoAffiliation: boolean
  showNoAnnotations: boolean
  showNoMollickSummary: boolean

  // Rating filters
  selectedRating: number | null
  minRating: number | null
  showUnratedOnly: boolean

  // Facet UI state
  expandedFacets: Set<string>

  // Actions
  clearAllFilters: () => void
  toggleFacet: (facetName: string) => void
  toggleFacetValue: (facetType: string, value: string | number) => void
  setSelectedAuthors: (s: Set<string>) => void
  setSelectedYears: (s: Set<number>) => void
  setSelectedConferences: (s: Set<string>) => void
  setSelectedAffiliations: (s: Set<string>) => void
  setSelectedProcessors: (s: Set<string>) => void
  setShowFlagged: (v: boolean | null) => void
  setShowNoProcessor: (v: boolean) => void
  setShowNoYear: (v: boolean) => void
  setShowNoConference: (v: boolean) => void
  setShowNoAffiliation: (v: boolean) => void
  setShowNoAnnotations: (v: boolean) => void
  setShowNoMollickSummary: (v: boolean) => void
  setSelectedRating: (v: number | null) => void
  setMinRating: (v: number | null) => void
  setShowUnratedOnly: (v: boolean) => void
  setCurrentPage: (v: number) => void
}

/** Reusable collapsible facet section with checkbox list */
function FacetSection({
  name,
  icon: Icon,
  label,
  items,
  selectedValues,
  facetType,
  expandedFacets,
  toggleFacet,
  toggleFacetValue,
  onClear,
}: {
  name: string
  icon: React.ElementType
  label: string
  items: Array<{ value: string | number; count: number; label: string }>
  selectedValues: Set<any>
  facetType: string
  expandedFacets: Set<string>
  toggleFacet: (name: string) => void
  toggleFacetValue: (type: string, value: string | number) => void
  onClear: () => void
}) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <button
          onClick={() => toggleFacet(name)}
          className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
        >
          <Icon className="h-4 w-4 text-gray-500 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
          {selectedValues.size > 0 && (
            <Badge variant="secondary" className="text-xs">
              {selectedValues.size}
            </Badge>
          )}
          {expandedFacets.has(name) ? (
            <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
          ) : (
            <ChevronRight className="h-4 w-4 text-gray-400 ml-1" />
          )}
        </button>
        {selectedValues.size > 0 && (
          <button
            onClick={onClear}
            className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            title={`Clear ${label.toLowerCase()} filters`}
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>
      {expandedFacets.has(name) && (
        <div className="space-y-1 max-h-48 overflow-y-auto">
          {items.length > 0 ? (
            items.map((item, index) => (
              <label
                key={`${item.value}-${index}`}
                className="flex items-center space-x-2 px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer rounded"
              >
                <Checkbox
                  checked={selectedValues.has(item.value)}
                  onCheckedChange={() => toggleFacetValue(facetType, item.value)}
                />
                <span className="text-sm text-gray-600 dark:text-gray-400 flex-1 truncate" title={item.label}>
                  {item.label}
                </span>
                <span className="text-xs text-gray-400">({item.count})</span>
              </label>
            ))
          ) : (
            <div className="text-sm text-gray-400 px-2 py-2">No {label.toLowerCase()} found</div>
          )}
        </div>
      )}
    </div>
  )
}

const PaperFacetsPanel: React.FC<PaperFacetsPanelProps> = ({
  facets,
  loadingFacets,
  activeFilterCount,
  selectedAuthors,
  selectedYears,
  selectedConferences,
  selectedAffiliations,
  selectedProcessors,
  showFlagged,
  showNoProcessor,
  showNoYear,
  showNoConference,
  showNoAffiliation,
  showNoAnnotations,
  showNoMollickSummary,
  selectedRating,
  showUnratedOnly,
  expandedFacets,
  clearAllFilters,
  toggleFacet,
  toggleFacetValue,
  setSelectedAuthors,
  setSelectedYears,
  setSelectedConferences,
  setSelectedAffiliations,
  setSelectedProcessors,
  setShowFlagged,
  setShowNoProcessor,
  setShowNoYear,
  setShowNoConference,
  setShowNoAffiliation,
  setShowNoAnnotations,
  setShowNoMollickSummary,
  setSelectedRating,
  setMinRating,
  setShowUnratedOnly,
  setCurrentPage,
}) => {
  const specialFilterCount =
    (showFlagged !== null ? 1 : 0) +
    (showNoProcessor ? 1 : 0) +
    (showNoYear ? 1 : 0) +
    (showNoConference ? 1 : 0) +
    (showNoAffiliation ? 1 : 0) +
    (showNoAnnotations ? 1 : 0)

  return (
    <div className="w-80 bg-white dark:bg-gray-950 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">Filters</h2>
          {activeFilterCount > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={clearAllFilters}
              className="text-blue-600 hover:text-blue-800"
            >
              <FilterX className="h-4 w-4 mr-1" />
              Clear All ({activeFilterCount})
            </Button>
          )}
        </div>

        {loadingFacets ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400 dark:text-gray-500" />
          </div>
        ) : (
          <div className="space-y-4">
            {/* Authors */}
            <FacetSection
              name="authors" icon={Users} label="Authors"
              items={facets?.authors || []}
              selectedValues={selectedAuthors}
              facetType="author"
              expandedFacets={expandedFacets}
              toggleFacet={toggleFacet}
              toggleFacetValue={toggleFacetValue}
              onClear={() => { setSelectedAuthors(new Set()); setCurrentPage(1) }}
            />

            {/* Years */}
            <FacetSection
              name="years" icon={Calendar} label="Years"
              items={facets?.years || []}
              selectedValues={selectedYears}
              facetType="year"
              expandedFacets={expandedFacets}
              toggleFacet={toggleFacet}
              toggleFacetValue={toggleFacetValue}
              onClear={() => { setSelectedYears(new Set()); setCurrentPage(1) }}
            />

            {/* Conferences */}
            <FacetSection
              name="conferences" icon={Building2} label="Conferences"
              items={facets?.conferences || []}
              selectedValues={selectedConferences}
              facetType="conference"
              expandedFacets={expandedFacets}
              toggleFacet={toggleFacet}
              toggleFacetValue={toggleFacetValue}
              onClear={() => { setSelectedConferences(new Set()); setCurrentPage(1) }}
            />

            {/* Institutions */}
            <FacetSection
              name="affiliations" icon={GraduationCap} label="Institutions"
              items={facets?.affiliations || []}
              selectedValues={selectedAffiliations}
              facetType="affiliation"
              expandedFacets={expandedFacets}
              toggleFacet={toggleFacet}
              toggleFacetValue={toggleFacetValue}
              onClear={() => { setSelectedAffiliations(new Set()); setCurrentPage(1) }}
            />

            {/* Processors */}
            <FacetSection
              name="processors" icon={Cpu} label="Processors"
              items={facets?.processors || []}
              selectedValues={selectedProcessors}
              facetType="processor"
              expandedFacets={expandedFacets}
              toggleFacet={toggleFacet}
              toggleFacetValue={toggleFacetValue}
              onClear={() => { setSelectedProcessors(new Set()); setCurrentPage(1) }}
            />

            {/* Special Filters Section */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <button
                  onClick={() => toggleFacet('special')}
                  className="flex items-center gap-2 text-left hover:text-blue-600 transition-colors flex-1"
                >
                  <Filter className="h-4 w-4 text-gray-500 dark:text-gray-400" />
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Special Filters</span>
                  {specialFilterCount > 0 && (
                    <Badge variant="secondary" className="text-xs">
                      {specialFilterCount}
                    </Badge>
                  )}
                  {expandedFacets.has('special') ? (
                    <ChevronDown className="h-4 w-4 text-gray-400 ml-1" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-gray-400 ml-1" />
                  )}
                </button>
                {specialFilterCount > 0 && (
                  <button
                    onClick={() => {
                      setShowFlagged(null)
                      setShowNoProcessor(false)
                      setShowNoYear(false)
                      setShowNoConference(false)
                      setShowNoAffiliation(false)
                      setShowNoAnnotations(false)
                      setCurrentPage(1)
                    }}
                    className="p-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                    title="Clear special filters"
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
              {expandedFacets.has('special') && (
                <div className="space-y-3 px-2">
                  {/* Flagged Papers Filter */}
                  <div className="space-y-2">
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Paper Status</span>
                    <div className="space-y-1">
                      <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer rounded">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            checked={showFlagged === true}
                            onCheckedChange={(checked) => {
                              setShowFlagged(checked ? true : null)
                              setCurrentPage(1)
                            }}
                          />
                          <div className="flex items-center gap-1">
                            <Flag className="h-3 w-3 text-orange-500" />
                            <span className="text-sm text-gray-600 dark:text-gray-400">Flagged</span>
                          </div>
                        </div>
                        <span className="text-xs text-gray-400">({facets?.paper_status?.flagged || 0})</span>
                      </label>
                      <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer rounded">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            checked={showFlagged === false}
                            onCheckedChange={(checked) => {
                              setShowFlagged(checked ? false : null)
                              setCurrentPage(1)
                            }}
                          />
                          <div className="flex items-center gap-1">
                            <Flag className="h-3 w-3 text-gray-300 dark:text-gray-600" />
                            <span className="text-sm text-gray-600 dark:text-gray-400">Not Flagged</span>
                          </div>
                        </div>
                        <span className="text-xs text-gray-400">({facets?.paper_status?.unflagged || 0})</span>
                      </label>
                    </div>
                  </div>

                  <Separator className="my-2" />

                  {/* Missing Data Filters */}
                  <div className="space-y-2">
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Missing Data</span>
                    <div className="space-y-1">
                      {[
                        { checked: showNoProcessor, setter: setShowNoProcessor, icon: Cpu, label: 'Processing', count: facets?.missing_data?.no_processor },
                        { checked: showNoYear, setter: setShowNoYear, icon: Calendar, label: 'Year', count: facets?.missing_data?.no_year },
                        { checked: showNoConference, setter: setShowNoConference, icon: Building2, label: 'Conference', count: facets?.missing_data?.no_conference },
                        { checked: showNoAffiliation, setter: setShowNoAffiliation, icon: GraduationCap, label: 'Affiliation', count: facets?.missing_data?.no_affiliation },
                        { checked: showNoAnnotations, setter: setShowNoAnnotations, icon: BookOpen, label: 'Annotations', count: facets?.missing_data?.no_annotations },
                        { checked: showNoMollickSummary, setter: setShowNoMollickSummary, icon: BarChart3, label: 'Mollick Summary', count: facets?.missing_data?.no_mollick_summary },
                      ].map(({ checked, setter, icon: ItemIcon, label, count }) => (
                        <label key={label} className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={checked}
                              onCheckedChange={(c) => {
                                setter(c as boolean)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-1">
                              <ItemIcon className="h-3 w-3 text-gray-400" />
                              <span className="text-sm text-gray-600 dark:text-gray-400">{label}</span>
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">({count || 0})</span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <Separator className="my-2" />

                  {/* Rating Filter */}
                  <div className="space-y-2">
                    <span className="text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wide">Rating</span>
                    <div className="space-y-1">
                      {[5, 4, 3, 2, 1].map((stars) => (
                        <label key={stars} className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer rounded">
                          <div className="flex items-center space-x-2">
                            <Checkbox
                              checked={selectedRating === stars}
                              onCheckedChange={(checked) => {
                                setSelectedRating(checked ? stars : null)
                                setMinRating(null)
                                setShowUnratedOnly(false)
                                setCurrentPage(1)
                              }}
                            />
                            <div className="flex items-center gap-0.5">
                              {Array.from({ length: 5 }).map((_, i) => (
                                <Star
                                  key={i}
                                  className={`h-3 w-3 ${i < stars ? 'fill-yellow-400 text-yellow-400' : 'text-gray-300 dark:text-gray-600'}`}
                                />
                              ))}
                            </div>
                          </div>
                          <span className="text-xs text-gray-400">
                            ({facets?.rating?.[`${stars}_star${stars !== 1 ? 's' : ''}`] || 0})
                          </span>
                        </label>
                      ))}
                      <label className="flex items-center justify-between space-x-2 px-2 py-1 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer rounded">
                        <div className="flex items-center space-x-2">
                          <Checkbox
                            checked={showUnratedOnly}
                            onCheckedChange={(checked) => {
                              setShowUnratedOnly(checked as boolean)
                              setSelectedRating(null)
                              setMinRating(null)
                              setCurrentPage(1)
                            }}
                          />
                          <span className="text-sm text-gray-600 dark:text-gray-400">Unrated</span>
                        </div>
                        <span className="text-xs text-gray-400">({facets?.rating?.unrated || 0})</span>
                      </label>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default PaperFacetsPanel
