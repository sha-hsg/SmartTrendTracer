import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Search,
  Download,
  Grid3x3,
  List,
} from 'lucide-react'
import { Author, MediaType } from './MediaCard'

interface MediaFilterBarProps {
  search: string
  onSearchChange: (value: string) => void
  days: number
  onDaysChange: (value: number) => void
  mediaType: string
  onMediaTypeChange: (value: string) => void
  mediaTypes: MediaType[]
  author: string
  onAuthorChange: (value: string) => void
  authors: Author[]
  sortBy: string
  onSortByChange: (value: string) => void
  viewMode: 'grid' | 'list'
  onViewModeChange: (mode: 'grid' | 'list') => void
  selectedCount: number
  onClearSelection: () => void
  onResetPage: () => void
}

export default function MediaFilterBar({
  search,
  onSearchChange,
  days,
  onDaysChange,
  mediaType,
  onMediaTypeChange,
  mediaTypes,
  author,
  onAuthorChange,
  authors,
  sortBy,
  onSortByChange,
  viewMode,
  onViewModeChange,
  selectedCount,
  onClearSelection,
  onResetPage,
}: MediaFilterBarProps) {
  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        <div className="flex flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
              <Input
                type="text"
                placeholder="Search media..."
                value={search}
                onChange={(e) => {
                  onSearchChange(e.target.value)
                  onResetPage()
                }}
                className="pl-10"
              />
            </div>
          </div>

          {/* Time range */}
          <Select value={days.toString()} onValueChange={(v) => onDaysChange(parseInt(v))}>
            <SelectTrigger className="w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="1">Last 24h</SelectItem>
              <SelectItem value="7">Last 7 days</SelectItem>
              <SelectItem value="30">Last 30 days</SelectItem>
              <SelectItem value="90">Last 90 days</SelectItem>
            </SelectContent>
          </Select>

          {/* Media type filter */}
          <Select value={mediaType} onValueChange={onMediaTypeChange}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All media types" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All types</SelectItem>
              {mediaTypes.map(type => (
                <SelectItem key={type.type} value={type.type}>
                  {type.label} ({type.count})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Author filter */}
          <Select value={author} onValueChange={onAuthorChange}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="All authors" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All authors</SelectItem>
              {authors.map(a => (
                <SelectItem key={a.username} value={a.username}>
                  @{a.username} ({a.media_count})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          {/* Sort */}
          <Select value={sortBy} onValueChange={onSortByChange}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="date_desc">Newest first</SelectItem>
              <SelectItem value="date_asc">Oldest first</SelectItem>
              <SelectItem value="likes_desc">Most liked</SelectItem>
              <SelectItem value="retweets_desc">Most retweeted</SelectItem>
            </SelectContent>
          </Select>

          {/* View mode toggle */}
          <div className="flex gap-1">
            <Button
              size="sm"
              variant={viewMode === 'grid' ? 'default' : 'outline'}
              onClick={() => onViewModeChange('grid')}
            >
              <Grid3x3 className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant={viewMode === 'list' ? 'default' : 'outline'}
              onClick={() => onViewModeChange('list')}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Selected items actions */}
        {selectedCount > 0 && (
          <div className="mt-4 flex items-center justify-between">
            <Badge variant="secondary">
              {selectedCount} item{selectedCount !== 1 ? 's' : ''} selected
            </Badge>
            <div className="flex gap-2">
              <Button size="sm" variant="outline">
                <Download className="h-4 w-4 mr-2" />
                Download Selected
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={onClearSelection}
              >
                Clear Selection
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
