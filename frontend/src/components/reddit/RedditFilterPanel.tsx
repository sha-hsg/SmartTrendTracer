import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { TagBadge } from "@/components/ui/tag-badge"
import {
  Search,
  Filter,
  User,
  X,
  ArrowUp,
  Clock,
  ChevronDown,
  ChevronRight as ChevronRightIcon
} from 'lucide-react'
import { cn } from "@/lib/utils"
import { Concept } from '@/types/concept'
import { RedditFacets } from './types'

interface RedditFilterPanelProps {
  facets: RedditFacets | null
  searchQuery: string
  setSearchQuery: (query: string) => void
  selectedConcept: Concept | null
  setSelectedConcept: (concept: Concept | null) => void
  setConceptSearchOpen: (open: boolean) => void
  selectedSubreddit: string
  handleSubredditFilter: (subreddit: string) => void
  selectedTimeRange: string
  handleTimeRangeFilter: (range: string) => void
  minScore: number | null
  handleScoreFilter: (scoreType: string) => void
  selectedAuthor: string
  handleAuthorFilter: (author: string) => void
  collapsedSections: {[key: string]: boolean}
  toggleSection: (section: string) => void
  activeFiltersCount: number
  clearAllFilters: () => void
}

const RedditFilterPanel: React.FC<RedditFilterPanelProps> = ({
  facets,
  searchQuery,
  setSearchQuery,
  selectedConcept,
  setSelectedConcept,
  setConceptSearchOpen,
  selectedSubreddit,
  handleSubredditFilter,
  selectedTimeRange,
  handleTimeRangeFilter,
  minScore,
  handleScoreFilter,
  selectedAuthor,
  handleAuthorFilter,
  collapsedSections,
  toggleSection,
  activeFiltersCount,
  clearAllFilters
}) => {
  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Filter className="w-5 h-5" />
            Filters
          </CardTitle>
          {activeFiltersCount > 0 && (
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className="text-xs">
                {activeFiltersCount} active
              </Badge>
              <Button
                onClick={clearAllFilters}
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Search Posts</label>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search titles and content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>
        </div>

        {/* Concept Search */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Filter by Concept</label>
          {selectedConcept ? (
            <div className="flex items-center gap-2">
              <TagBadge size="sm">{selectedConcept.display_name}</TagBadge>
              <Button
                onClick={() => setSelectedConcept(null)}
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
              >
                <X className="w-3 h-3" />
              </Button>
            </div>
          ) : (
            <Button
              onClick={() => setConceptSearchOpen(true)}
              variant="outline"
              size="sm"
              className="w-full justify-start"
            >
              <Search className="w-4 h-4 mr-2" />
              Search Concepts...
            </Button>
          )}
        </div>

        {/* Subreddits */}
        {facets?.subreddits && facets.subreddits.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Subreddits</label>
              <Button
                onClick={() => toggleSection('subreddits')}
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
              >
                {collapsedSections['subreddits'] ?
                  <ChevronRightIcon className="w-3 h-3" /> :
                  <ChevronDown className="w-3 h-3" />
                }
              </Button>
            </div>
            {!collapsedSections['subreddits'] && (
              <div className="space-y-1 max-h-40 overflow-y-auto">
                {facets.subreddits.map(subreddit => (
                  <div
                    key={subreddit.name}
                    className={cn(
                      "flex items-center justify-between p-2 rounded cursor-pointer text-sm",
                      selectedSubreddit === subreddit.name
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                    )}
                    onClick={() => handleSubredditFilter(subreddit.name)}
                  >
                    <span>r/{subreddit.name}</span>
                    <Badge variant="secondary" className="text-xs">
                      {subreddit.count}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Time Ranges */}
        {facets?.time_ranges && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Time Range</label>
            <div className="space-y-1">
              {Object.entries(facets.time_ranges).map(([range, count]) => (
                <div
                  key={range}
                  className={cn(
                    "flex items-center justify-between p-2 rounded cursor-pointer text-sm",
                    selectedTimeRange === range
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  )}
                  onClick={() => handleTimeRangeFilter(range)}
                >
                  <span className="flex items-center gap-2">
                    <Clock className="w-3 h-3" />
                    {range === '24h' && 'Last 24 hours'}
                    {range === '7d' && 'Last 7 days'}
                    {range === '30d' && 'Last 30 days'}
                  </span>
                  <Badge variant="secondary" className="text-xs">
                    {count}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Score Ranges */}
        {facets?.score_ranges && (
          <div className="space-y-2">
            <label className="text-sm font-medium">Post Score</label>
            <div className="space-y-1">
              {Object.entries(facets.score_ranges).map(([scoreType, count]) => (
                <div
                  key={scoreType}
                  className={cn(
                    "flex items-center justify-between p-2 rounded cursor-pointer text-sm",
                    (scoreType === 'high_score' && minScore === 100) ||
                    (scoreType === 'medium_score' && minScore === 10) ||
                    (scoreType === 'low_score' && minScore === 0)
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
                  )}
                  onClick={() => handleScoreFilter(scoreType)}
                >
                  <span className="flex items-center gap-2">
                    <ArrowUp className="w-3 h-3" />
                    {scoreType === 'high_score' && '100+ points'}
                    {scoreType === 'medium_score' && '10-99 points'}
                    {scoreType === 'low_score' && '< 10 points'}
                  </span>
                  <Badge variant="secondary" className="text-xs">
                    {count}
                  </Badge>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Authors */}
        {facets?.authors && facets.authors.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium">Top Authors</label>
              <Button
                onClick={() => toggleSection('authors')}
                variant="ghost"
                size="sm"
                className="h-6 w-6 p-0"
              >
                {collapsedSections['authors'] ?
                  <ChevronRightIcon className="w-3 h-3" /> :
                  <ChevronDown className="w-3 h-3" />
                }
              </Button>
            </div>
            {!collapsedSections['authors'] && (
              <div className="space-y-1 max-h-32 overflow-y-auto">
                {facets.authors.slice(0, 10).map(author => (
                  <div
                    key={author.name}
                    className={cn(
                      "flex items-center justify-between p-2 rounded cursor-pointer text-sm",
                      selectedAuthor === author.name
                        ? "bg-primary text-primary-foreground"
                        : "hover:bg-muted"
                    )}
                    onClick={() => handleAuthorFilter(author.name)}
                  >
                    <span className="flex items-center gap-2">
                      <User className="w-3 h-3" />
                      {author.name}
                    </span>
                    <Badge variant="secondary" className="text-xs">
                      {author.count}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default RedditFilterPanel
